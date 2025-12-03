from datetime import date, timedelta, datetime
from typing import List, Dict, Optional
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Shared.database import Database
from HuizenManager.src.manager import HuizenManager
from Shared.entities import Huis, Leverancier, InhuurContract

class IntelligenceAPI:
    """
    API Layer exposing operational data as tools for the AI Assistant.
    """

    def __init__(self, db_path: str = None):
        # Default to the core DB, but allow overriding (e.g. for mock DB)
        self.db_path = db_path or "database/ryanrent_core.db"
        self.db = Database(self.db_path)
        self.manager = HuizenManager(self.db)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_database_schema(self) -> str:
        """
        Dynamically retrieves the database schema AND data context (counts, distinct values).
        Returns a formatted string suitable for the LLM system prompt.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        schema_lines = ["**DB Schema:**"]
        
        # Columns to sample for distinct values (Enums)
        enum_columns = {
            "huizen": ["status", "woning_type"],
            "klanten": ["type"],
            "boekingen": ["status"],
            "borg_transacties": ["type"]
        }
        
        ignored_tables = ['schema_migrations', 'schema_versions', 'sqlite_sequence']

        for table in tables:
            table_name = table[0]
            if table_name in ignored_tables:
                continue
            
            # Get Row Count
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
            except:
                count = "?"

            # Get Columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            col_names = [col[1] for col in columns]
            
            # Get Distinct Values for specific columns
            enums_str = ""
            if table_name in enum_columns:
                for col in enum_columns[table_name]:
                    if col in col_names:
                        try:
                            cursor.execute(f"SELECT DISTINCT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 3")
                            vals = [str(row[0]) for row in cursor.fetchall()]
                            enums_str += f" [{col}: {', '.join(vals)}]"
                        except:
                            pass

            schema_lines.append(f"- **{table_name}** ({count}): {', '.join(col_names)}{enums_str}")
            
        conn.close()
        return "\n".join(schema_lines)

    def get_houses_near_contract_end(self, days: int = 30) -> List[Dict]:
        """
        Return houses with INHUUR contracts ending within 'days'.
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        
        target_date = date.today() + timedelta(days=days)
        
        query = """
            SELECT 
                h.adres, 
                c.end_date, 
                l.naam as leverancier
            FROM inhuur_contracten c
            JOIN huizen h ON c.property_id = h.id
            JOIN leveranciers l ON c.leverancier_id = l.id
            WHERE c.end_date IS NOT NULL 
            AND c.end_date <= ?
            AND c.end_date >= DATE('now')
            ORDER BY c.end_date ASC
        """
        
        rows = conn.execute(query, (target_date,)).fetchall()
        conn.close()
        return rows

    def get_bookings_without_checkout(self) -> List[Dict]:
        """
        Find bookings where checkout_datum < Today but NO checkout log exists.
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        
        query = """
            SELECT 
                b.id as booking_id,
                h.adres,
                k.naam as client,
                b.checkout_datum
            FROM boekingen b
            JOIN huizen h ON b.huis_id = h.id
            JOIN klanten k ON b.klant_id = k.id
            LEFT JOIN checkouts co ON b.id = co.boeking_id
            WHERE b.checkout_datum < DATE('now')
            AND co.id IS NULL
            AND b.status != 'cancelled'
            ORDER BY b.checkout_datum ASC
        """
        
        rows = conn.execute(query).fetchall()
        conn.close()
        return rows

    def get_upcoming_checkouts(self, days: int = 60) -> List[Dict]:
        """
        Get bookings with checkout dates in the next 'days' days.
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        
        target_date = date.today() + timedelta(days=days)
        
        query = """
            SELECT 
                b.id as booking_id,
                h.adres,
                k.naam as client,
                b.checkin_datum,
                b.checkout_datum,
                b.status
            FROM boekingen b
            JOIN huizen h ON b.huis_id = h.id
            JOIN klanten k ON b.klant_id = k.id
            WHERE b.checkout_datum >= DATE('now')
            AND b.checkout_datum <= ?
            AND b.status != 'cancelled'
            ORDER BY b.checkout_datum ASC
        """
        
        rows = conn.execute(query, (target_date,)).fetchall()
        conn.close()
        return rows

    def get_open_deposits_by_client(self) -> List[Dict]:
        """
        Calculate open deposit balance per client.
        Balance = Received - (Refunded + Deducted)
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        
        # We need to aggregate transactions per booking, then group by client
        query = """
            SELECT 
                k.naam as client,
                COUNT(DISTINCT b.id) as active_deposit_count,
                SUM(CASE WHEN t.type = 'ontvangst' THEN t.bedrag ELSE 0 END) -
                SUM(CASE WHEN t.type IN ('terugbetaling', 'inhouding') THEN t.bedrag ELSE 0 END) as open_balance
            FROM borg_transacties t
            JOIN boekingen b ON t.boeking_id = b.id
            JOIN klanten k ON b.klant_id = k.id
            GROUP BY k.id
            HAVING open_balance > 0
            ORDER BY open_balance DESC
        """
        
        rows = conn.execute(query).fetchall()
        conn.close()
        return rows

    def get_status_overview(self) -> Dict:
        """
        High-level dashboard of the operation.
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        
        stats = {}
        
        # 1. Total Houses
        stats['total_houses'] = conn.execute("SELECT COUNT(*) as c FROM huizen WHERE status='active'").fetchone()['c']
        
        # 2. Current Occupancy (Bookings active today)
        stats['occupied_houses'] = conn.execute("""
            SELECT COUNT(*) as c FROM boekingen 
            WHERE checkin_datum <= DATE('now') 
            AND checkout_datum >= DATE('now')
            AND status != 'cancelled'
        """).fetchone()['c']
        
        # 3. Expiring Contracts (Next 30 days)
        stats['expiring_contracts'] = len(self.get_houses_near_contract_end(30))
        
        # 4. Missing Checkouts
        stats['missing_checkouts'] = len(self.get_bookings_without_checkout())
        
        conn.close()
        return stats

    def get_active_houses(self, limit: int = 50) -> List[Dict]:
        """
        Get a list of active houses with their Object IDs.
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        
        query = """
            SELECT id, object_id, adres, plaats, status 
            FROM huizen 
            WHERE status = 'active' 
            ORDER BY object_id ASC 
            LIMIT ?
        """
        
        rows = conn.execute(query, (limit,)).fetchall()
        conn.close()
        return rows

    def find_house(self, query: str) -> List[Dict]:
        """Find a house by address (partial match)."""
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        rows = conn.execute("SELECT id, object_id, adres FROM huizen WHERE adres LIKE ?", (f"%{query}%",)).fetchall()
        conn.close()
        return rows

    def find_client(self, query: str) -> List[Dict]:
        """Find a client by name (partial match)."""
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        rows = conn.execute("SELECT id, naam FROM klanten WHERE naam LIKE ?", (f"%{query}%",)).fetchall()
        conn.close()
        return rows

        conn.close()
        return rows

    def run_sql_query(self, query: str) -> List[Dict]:
        """
        Run a READ-ONLY SQL query.
        """
        # Safety Check: Only allow SELECT statements
        if not query.strip().upper().startswith("SELECT"):
            return [{"error": "Only SELECT statements are allowed for safety."}]

        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        try:
            rows = conn.execute(query).fetchall()
            return rows
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            conn.close()

    # ==========================================
    # WRITE TOOLS (Mutations)
    # ==========================================

    def add_house(self, adres: str, plaats: str, postcode: str, 
                  woning_type: str, aantal_sk: int, aantal_pers: int) -> Dict:
        """Add a new house."""
        try:
            # Generate next Object ID
            object_id = self.manager.get_next_object_id()
            
            huis = Huis(
                id=None,
                object_id=object_id,
                adres=adres,
                postcode=postcode,
                plaats=plaats,
                woning_type=woning_type,
                oppervlakte=0, # Default
                aantal_sk=aantal_sk,
                aantal_pers=aantal_pers,
                status='active'
            )
            
            huis_id = self.manager.add_huis(huis)
            return {
                "success": True, 
                "message": f"House added successfully! ID: {huis_id}, Object ID: {object_id}",
                "huis_id": huis_id,
                "object_id": object_id
            }
        except Exception as e:
            return {"error": str(e)}

    def add_supplier(self, naam: str, email: str = None, telefoon: str = None, iban: str = None) -> Dict:
        """Add a new supplier/owner."""
        try:
            # Check if exists
            existing = self.manager.get_leverancier_by_name(naam)
            if existing:
                return {"success": True, "message": f"Supplier '{naam}' already exists.", "id": existing.id}

            lev = Leverancier(
                id=None,
                naam=naam,
                email=email,
                telefoonnummer=telefoon,
                iban=iban
            )
            lev_id = self.manager.add_leverancier(lev)
            return {"success": True, "message": f"Supplier added successfully!", "id": lev_id}
        except Exception as e:
            return {"error": str(e)}

    def add_client(self, naam: str, email: str = None) -> Dict:
        """Add a new client."""
        try:
            # Check if exists (simple check via SQL as manager doesn't have get_client_by_name exposed clearly yet)
            # Actually manager.add_klant doesn't check duplicates but let's trust the tool usage or add check
            # For now, just add.
            klant_id = self.manager.add_klant(naam, email=email)
            return {"success": True, "message": f"Client added successfully!", "id": klant_id}
        except Exception as e:
            return {"error": str(e)}

    def add_inhuur_contract(self, house_id: int, supplier_id: int, 
                          start_date: str, rent_price: float, 
                          end_date: str = None) -> Dict:
        """Add an inhuur contract."""
        try:
            d_start = datetime.strptime(start_date, "%Y-%m-%d").date()
            d_end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else None
            
            contract = InhuurContract(
                id=None,
                property_id=house_id,
                leverancier_id=supplier_id,
                start_date=d_start,
                end_date=d_end,
                kale_huur=rent_price,
                servicekosten=0, voorschot_gwe=0, internet_kosten=0, 
                inventaris_kosten=0, afval_kosten=0, schoonmaak_kosten=0,
                totale_huur=rent_price, # Simplified
                borg=0, contract_bestand=None, notities="Created by AI"
            )
            
            c_id = self.manager.add_contract(contract)
            return {"success": True, "message": f"Contract added successfully!", "id": c_id}
        except Exception as e:
            return {"error": str(e)}

    def create_booking(self, huis_id: int, klant_id: int, start_date: str, end_date: str) -> Dict:
        """
        Create a new booking.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Check availability
            overlap = cursor.execute("""
                SELECT id FROM boekingen 
                WHERE huis_id = ? 
                AND status != 'cancelled'
                AND (
                    (checkin_datum <= ? AND checkout_datum >= ?) OR
                    (checkin_datum <= ? AND checkout_datum >= ?) OR
                    (checkin_datum >= ? AND checkout_datum <= ?)
                )
            """, (huis_id, start_date, start_date, end_date, end_date, start_date, end_date)).fetchone()
            
            if overlap:
                return {"error": f"House {huis_id} is already booked for these dates."}

            # 2. Get Active Contract (for price) - Simplified for API
            # Ideally we call Manager logic here, but for now we do a direct insert or simple calc
            # Let's assume we just create the booking record and let the Manager handle financials later
            # Or we can fetch the contract.
            
            # Find active contract
            contract = cursor.execute("""
                SELECT id, kale_huur FROM verhuur_contracten 
                WHERE huis_id = ? AND klant_id = ? 
                ORDER BY start_datum DESC LIMIT 1
            """, (huis_id, klant_id)).fetchone()
            
            contract_id = contract[0] if contract else None
            price = contract[1] if contract else 0 # Placeholder
            
            cursor.execute("""
                INSERT INTO boekingen (contract_id, huis_id, klant_id, checkin_datum, checkout_datum, status, totale_huur_factuur)
                VALUES (?, ?, ?, ?, ?, 'confirmed', ?)
            """, (contract_id, huis_id, klant_id, start_date, end_date, price))
            
            booking_id = cursor.lastrowid
            conn.commit()
            return {"success": True, "booking_id": booking_id, "message": f"Booking created for House {huis_id}"}
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def update_booking(self, booking_id: int, checkin_date: str = None, checkout_date: str = None, status: str = None) -> Dict:
        """
        Update an existing booking.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Verify booking exists
            cursor.execute("SELECT id FROM boekingen WHERE id = ?", (booking_id,))
            if not cursor.fetchone():
                return {"error": f"Booking {booking_id} not found."}

            # 2. Build Update Query
            updates = []
            params = []
            
            if checkin_date:
                updates.append("checkin_datum = ?")
                params.append(checkin_date)
            
            if checkout_date:
                updates.append("checkout_datum = ?")
                params.append(checkout_date)
                
            if status:
                updates.append("status = ?")
                params.append(status)
                
            if not updates:
                return {"error": "No fields to update provided."}
                
            params.append(booking_id)
            
            query = f"UPDATE boekingen SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, tuple(params))
            conn.commit()
            
            return {"success": True, "message": f"Booking {booking_id} updated successfully."}
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def register_checkin(self, booking_id: int, date: str, notes: str = "") -> Dict:
        """
        Register a check-in.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checkins (boeking_id, datum, uitgevoerd_door, sleutelset, notities)
                VALUES (?, ?, 'AI Assistant', 'Standard', ?)
            """, (booking_id, date, notes))
            
            cursor.execute("UPDATE boekingen SET status = 'checked_in' WHERE id = ?", (booking_id,))
            conn.commit()
            return {"success": True, "message": f"Check-in registered for Booking {booking_id}"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def register_checkout(self, booking_id: int, date: str, damage: float = 0, cleaning: float = 0) -> Dict:
        """
        Register a check-out.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checkouts (boeking_id, datum_werkelijk, uitgevoerd_door, schade_geschat, schoonmaak_kosten, notities)
                VALUES (?, ?, 'AI Assistant', ?, ?, 'Processed by AI')
            """, (booking_id, date, damage, cleaning))
            
            cursor.execute("UPDATE boekingen SET status = 'checked_out' WHERE id = ?", (booking_id,))
            conn.commit()
            return {"success": True, "message": f"Check-out registered for Booking {booking_id}. Damage: €{damage}, Cleaning: €{cleaning}"}
        except Exception as e:
            return {"error": str(e)}
        finally:
            conn.close()

    def generate_settlement(self, 
                          client_name: str, 
                          house_address: str, 
                          checkin_date: str, 
                          checkout_date: str, 
                          deposit_held: float, 
                          deposit_returned: float,
                          
                          gwe_voorschot: float,
                          cleaning_voorschot: float,
                          
                          client_email: str = "unknown@example.com",
                          
                          gwe_details: Dict = None,
                          gwe_usage_cost: float = 0.0,
                          
                          damages: List[Dict] = [],
                          cleaning_package: str = "geen",
                          cleaning_costs: float = 0.0,
                          
                          extra_voorschot: Dict = None) -> Dict:
        """
        Generate a PDF settlement (Eindafrekening).
        """
        try:
            # 1. Setup paths for imports
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
            eindafrekening_src = os.path.join(project_root, 'Eindafrekening', 'src')
            
            if eindafrekening_src not in sys.path:
                sys.path.append(eindafrekening_src)
                
            # 2. Import Generation Logic & Entities
            from generate import generate_eindafrekening_from_data
            from Shared.entities import (
                Client, RentalProperty, Period, Deposit, 
                GWEMeterReading, GWERegel, GWETotalen, Cleaning, 
                DamageRegel, DamageTotalen, GWEMeterstanden, ExtraVoorschot
            )
            
            # 3. Lookup House Details from DB
            conn = self._get_connection()
            conn.row_factory = self._dict_factory
            house_row = conn.execute("SELECT object_id, postcode, plaats FROM huizen WHERE adres LIKE ?", (f"%{house_address}%",)).fetchone()
            conn.close()
            
            postal_code = house_row['postcode'] if house_row else ""
            city = house_row['plaats'] if house_row else ""
            object_id = house_row['object_id'] if house_row else ""
            unit = "" # Unit not in DB yet

            # 4. Construct Data Objects
            
            # Dates
            d_in = datetime.strptime(checkin_date, "%Y-%m-%d").date()
            d_out = datetime.strptime(checkout_date, "%Y-%m-%d").date()
            days = (d_out - d_in).days
            
            # Entities
            client_obj = Client(name=client_name, contact_person=client_name, email=client_email)
            object_obj = RentalProperty(
                address=house_address,
                unit=unit,
                postal_code=postal_code,
                city=city,
                object_id=object_id
            )
            period_obj = Period(checkin_date=d_in, checkout_date=d_out, days=days)
            
            # Helper to convert Incl VAT to Ex VAT
            def to_excl(amount):
                return amount / 1.21

            # Damage Processing
            damage_regels = []
            total_damage = 0.0
            for dmg in damages:
                desc = dmg.get('description', 'Onbekende schade')
                amt_incl = float(dmg.get('amount', 0))
                amt_excl = to_excl(amt_incl)
                # We set tarief_excl to the calculated excl amount
                damage_regels.append(DamageRegel(desc, 1, amt_excl, amt_excl))
                total_damage += amt_incl # Keep track of incl total for deposit check
            
            # Note: We don't need to calculate totals here, generate.py will do it.
            # But we provide placeholders.
            damage_totalen = DamageTotalen(totaal_excl=0, btw=0, totaal_incl=0)

            # Deposit
            # We set 'gebruikt' to total_damage so generate.py respects it
            deposit_obj = Deposit(
                voorschot=deposit_held,
                gebruikt=total_damage, 
                terug=max(0, deposit_held - total_damage),
                restschade=max(0, total_damage - deposit_held)
            )
            
            # GWE Construction
            gwe_regels = []
            
            # Meter readings & Consumption Logic
            if gwe_details:
                stroom_begin = float(gwe_details.get('stroom_begin', 0))
                stroom_eind = float(gwe_details.get('stroom_eind', 0))
                stroom_verbruik = stroom_eind - stroom_begin
                
                gas_begin = float(gwe_details.get('gas_begin', 0))
                gas_eind = float(gwe_details.get('gas_eind', 0))
                gas_verbruik = gas_eind - gas_begin
                
                stroom = GWEMeterReading(begin=stroom_begin, eind=stroom_eind, verbruik=stroom_verbruik)
                gas = GWEMeterReading(begin=gas_begin, eind=gas_eind, verbruik=gas_verbruik)
                
                # Create detailed line items with 0 cost (informational)
                if stroom_verbruik > 0:
                    gwe_regels.append(GWERegel(f"Stroom verbruik ({stroom_verbruik:.0f} kWh)", stroom_verbruik, 0, 0))
                if gas_verbruik > 0:
                    gwe_regels.append(GWERegel(f"Gas verbruik ({gas_verbruik:.0f} m3)", gas_verbruik, 0, 0))
                    
            else:
                stroom = GWEMeterReading(0,0,0)
                gas = GWEMeterReading(0,0,0)
                
            # Add the total cost line (converted to Ex VAT)
            if gwe_usage_cost > 0:
                cost_excl = to_excl(gwe_usage_cost)
                gwe_regels.append(GWERegel("Totaal GWE Kosten", 1, cost_excl, cost_excl))
                
            gwe_totalen = GWETotalen(totaal_excl=0, btw=0, totaal_incl=0)
            gwe_meterstanden = GWEMeterstanden(stroom=stroom, gas=gas)
            
            # Cleaning
            # Map package name
            pakket_naam = "Geen pakket"
            inbegrepen = 0
            if cleaning_package == "Basis Schoonmaak":
                pakket_naam = "Basis Schoonmaak"
                inbegrepen = 5
            elif cleaning_package == "Intensief Schoonmaak":
                pakket_naam = "Intensief Schoonmaak"
                inbegrepen = 7

            # Calculate extra hours to match the cost
            # extra_bedrag = extra_uren * 50
            # so extra_uren = extra_bedrag / 50
            extra_uren = 0
            if cleaning_costs > 0:
                extra_uren = cleaning_costs / 50.0

            cleaning_obj = Cleaning(
                pakket_type=cleaning_package, 
                pakket_naam=pakket_naam, 
                inbegrepen_uren=inbegrepen, 
                totaal_uren=inbegrepen + extra_uren, 
                extra_uren=extra_uren, 
                uurtarief=50, 
                extra_bedrag=cleaning_costs, 
                voorschot=cleaning_voorschot
            )
            
            # Extra Voorschot
            extra_voorschot_obj = None
            if extra_voorschot:
                amount = float(extra_voorschot.get('amount', 0))
                used = float(extra_voorschot.get('used', 0))
                desc = extra_voorschot.get('description', 'Extra')
                extra_voorschot_obj = ExtraVoorschot(
                    voorschot=amount,
                    omschrijving=desc,
                    gebruikt=used,
                    terug=max(0, amount - used),
                    restschade=max(0, used - amount)
                )

            # 5. Build Data Dictionary
            data = {
                'client': client_obj,
                'object': object_obj,
                'period': period_obj,
                'deposit': deposit_obj,
                'gwe_meterstanden': gwe_meterstanden,
                'gwe_regels': gwe_regels,
                'gwe_totalen': gwe_totalen,
                'cleaning': cleaning_obj,
                'damage_regels': damage_regels,
                'damage_totalen': damage_totalen,
                'extra_voorschot': extra_voorschot_obj,
                'gwe_voorschot': gwe_voorschot
            }
            
            # 5. Call Generator
            output_dir = os.path.join(project_root, 'Eindafrekening', 'output')
            bundle_dir = os.path.join(project_root, 'Eindafrekening') # Templates are here
            shared_dir = os.path.join(project_root, 'Shared')
            
            result = generate_eindafrekening_from_data(
                data, output_dir, bundle_dir, shared_dir, project_root, 
                save_json=False, auto_open=False
            )
            
            pdf_path = result['onepager']['pdf']
            return {
                "success": True, 
                "message": f"Settlement generated successfully!", 
                "pdf_path": pdf_path,
                "net_result": f"€{deposit_returned:.2f} returned"
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    def get_booking_for_settlement(self, booking_id: int) -> Dict:
        """Fetch all booking data needed for settlement generation."""
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()
        
        query = """
        SELECT 
            b.id as booking_id, b.checkin_datum, b.checkout_datum, b.betaalde_borg,
            b.voorschot_gwe, b.voorschot_schoonmaak, b.schoonmaak_pakket,
            k.naam as client_name, k.contactpersoon, k.email, k.telefoonnummer,
            h.adres as property_address, h.object_id, h.postcode, h.plaats
        FROM boekingen b
        JOIN klanten k ON b.klant_id = k.id
        JOIN huizen h ON b.huis_id = h.id
        WHERE b.id = ?
        """
        
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"Booking {booking_id} not found")
        
        return result
    
    def save_meter_readings(self, booking_id: int, readings: Dict) -> bool:
        """Save GWE meter readings for a booking."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for reading_type, values in readings.items():
            cursor.execute("""
                INSERT INTO meter_readings (booking_id, reading_type, start_value, end_value, tariff)
                VALUES (?, ?, ?, ?, ?)
            """, (booking_id, reading_type, values['start'], values['end'], values['tariff']))
        
        conn.commit()
        conn.close()
        return True
    
    def save_damages(self, booking_id: int, damages: List[Dict]) -> bool:
        """Save damage records for a booking."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        for damage in damages:
            cursor.execute("""
                INSERT INTO damages (booking_id, description, estimated_cost, btw_percentage)
                VALUES (?, ?, ?, ?)
            """, (booking_id, damage['description'], damage['cost'], damage.get('btw_percentage', 21.0)))
        
        conn.commit()
        conn.close()
        return True
    
    def update_booking_settlement_status(self, booking_id: int) -> bool:
        """Mark booking as having settlement generated."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE boekingen
            SET settlement_generated = 1, settlement_generated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (booking_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def update_booking_voorschotten(self, booking_id: int, voorschot_gwe: float, voorschot_schoonmaak: float, schoonmaak_pakket: str) -> bool:
        """Update voorschot amounts and cleaning package for a booking."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE boekingen
            SET voorschot_gwe = ?, voorschot_schoonmaak = ?, schoonmaak_pakket = ?
            WHERE id = ?
        """, (voorschot_gwe, voorschot_schoonmaak, schoonmaak_pakket, booking_id))
        
        conn.commit()
        conn.close()
        return True

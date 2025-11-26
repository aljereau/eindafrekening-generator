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
                          cleaning_cost: float,
                          damage_cost: float,
                          gwe_usage: float = 0.0) -> Dict:
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
                DamageRegel, DamageTotalen, GWEMeterstanden
            )
            
            # 3. Construct Data Objects
            # Dates
            d_in = datetime.strptime(checkin_date, "%Y-%m-%d").date()
            d_out = datetime.strptime(checkout_date, "%Y-%m-%d").date()
            days = (d_out - d_in).days
            
            # Entities
            client_obj = Client(name=client_name, contact_person=client_name, email="unknown@example.com")
            object_obj = RentalProperty(address=house_address)
            period_obj = Period(checkin_date=d_in, checkout_date=d_out, days=days)
            
            deposit_obj = Deposit(
                voorschot=deposit_held,
                gebruikt=deposit_held - deposit_returned,
                terug=deposit_returned,
                restschade=0.0
            )
            
            # GWE (Simplified for AI: assume usage is total cost for now, or 0)
            # In a real scenario, AI should ask for meter readings.
            # For now, we create a dummy entry if usage > 0
            gwe_regels = []
            if gwe_usage > 0:
                gwe_regels.append(GWERegel("Verbruik (Schatting)", 1, gwe_usage, gwe_usage))
                
            gwe_totalen = GWETotalen(totaal_excl=gwe_usage, btw=0, totaal_incl=gwe_usage)
            gwe_meterstanden = GWEMeterstanden(
                stroom=GWEMeterReading(0,0,0), 
                gas=GWEMeterReading(0,0,0)
            )
            
            # Cleaning
            cleaning_obj = Cleaning(
                pakket_type="geen", 
                pakket_naam="Op nacalculatie", 
                inbegrepen_uren=0, 
                totaal_uren=0, 
                extra_uren=0, 
                uurtarief=0, 
                extra_bedrag=cleaning_cost, 
                voorschot=0
            )
            
            # Damage
            damage_regels = []
            if damage_cost > 0:
                damage_regels.append(DamageRegel("Schade (Diverse)", 1, damage_cost, damage_cost))
                
            damage_totalen = DamageTotalen(totaal_excl=damage_cost, btw=0, totaal_incl=damage_cost)
            
            # 4. Build Data Dictionary
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
                'extra_voorschot': None,
                'gwe_voorschot': 0.0 # Assuming included or handled in deposit
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

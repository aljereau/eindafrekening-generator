from datetime import date, datetime
from typing import Optional, List, Tuple
import sqlite3
import sys
import os

# Ensure we can import from Shared if running as script
# (Though typically this is imported by other scripts)
# from Shared.database import Database
# from Shared.entities import Huis, Eigenaar, InhuurContract

# When imported as a module in the project, 'Shared' should be available if project root is in path.
try:
    from Shared.database import Database
    from Shared.entities import Huis, Leverancier, InhuurContract
except ImportError:
    # Fallback for when running tests directly inside the folder without root in path
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from Shared.database import Database
    from Shared.entities import Huis, Leverancier, InhuurContract

class HuizenManager:
    """
    Manager for the Huizeninventaris system.
    Handles CRUD operations for Houses (Huizen), Suppliers (Leveranciers), and Contracts (InhuurContracten).
    """

    def __init__(self, db: Database = None):
        self.db = db or Database()

    # ==========================================
    # 1. HUIZEN (Properties)
    # ==========================================

    def add_huis(self, huis: Huis) -> int:
        """Add a new house to the fleet."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO huizen (
                    object_id, adres, postcode, plaats, 
                    woning_type, oppervlakte, aantal_sk, aantal_pers, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                huis.object_id, huis.adres, huis.postcode, huis.plaats,
                huis.woning_type, huis.oppervlakte, huis.aantal_sk, huis.aantal_pers, huis.status
            ))
            huis_id = cursor.lastrowid
            
            # Log status change
            self._log_status_change(cursor, huis_id, huis.status, "Initial creation")
            
            conn.commit()
            return huis_id
        finally:
            conn.close()

    def get_huis(self, huis_id: int) -> Optional[Huis]:
        """Get house details by ID."""
        conn = self.db._get_connection()
        row = conn.execute("SELECT * FROM huizen WHERE id = ?", (huis_id,)).fetchone()
        conn.close()
        
        if not row:
            return None
            
        return Huis(
            id=row['id'],
            object_id=row['object_id'],
            adres=row['adres'],
            postcode=row['postcode'],
            plaats=row['plaats'],
            woning_type=row['woning_type'],
            oppervlakte=row['oppervlakte'],
            aantal_sk=row['aantal_sk'],
            aantal_pers=row['aantal_pers'],
            status=row['status']
        )

    def update_huis(self, huis: Huis):
        """Update physical house details."""
        conn = self.db._get_connection()
        try:
            conn.execute("""
                UPDATE huizen SET
                    object_id = ?, adres = ?, postcode = ?, plaats = ?,
                    woning_type = ?, oppervlakte = ?, aantal_sk = ?, aantal_pers = ?
                WHERE id = ?
            """, (
                huis.object_id, huis.adres, huis.postcode, huis.plaats,
                huis.woning_type, huis.oppervlakte, huis.aantal_sk, huis.aantal_pers,
                huis.id
            ))
            conn.commit()
        finally:
            conn.close()

    def get_next_object_id(self) -> str:
        """
        Calculate the next available Object ID.
        Finds the highest numeric object_id (ignoring 'A-' prefixes) and increments by 1.
        Returns a 4-digit string (e.g., '0444').
        """
        conn = self.db._get_connection()
        rows = conn.execute("SELECT object_id FROM huizen").fetchall()
        conn.close()

        max_id = 0
        for row in rows:
            obj_id = row['object_id']
            # Ignore archived/prefixed IDs if they don't follow the numeric pattern
            if obj_id and obj_id.isdigit():
                val = int(obj_id)
                if val > max_id:
                    max_id = val
        
        next_id = max_id + 1
        return f"{next_id:04d}"

    # ==========================================
    # 2. LEVERANCIERS (Suppliers/Owners)
    # ==========================================

    def add_leverancier(self, leverancier: Leverancier) -> int:
        """Add a new supplier."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leveranciers (naam, email, telefoonnummer, iban)
                VALUES (?, ?, ?, ?)
            """, (leverancier.naam, leverancier.email, leverancier.telefoonnummer, leverancier.iban))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_leverancier_by_name(self, name: str) -> Optional[Leverancier]:
        """Find supplier by name."""
        conn = self.db._get_connection()
        row = conn.execute("SELECT * FROM leveranciers WHERE naam = ?", (name,)).fetchone()
        conn.close()
        if not row: return None
        return Leverancier(id=row['id'], naam=row['naam'], email=row['email'], telefoonnummer=row['telefoonnummer'], iban=row['iban'])

    # ==========================================
    # 3. INHUUR CONTRACTEN
    # ==========================================

    def add_contract(self, contract: InhuurContract) -> int:
        """Add a new rental contract (inhuur)."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inhuur_contracten (
                    property_id, leverancier_id, start_date, end_date,
                    kale_huur, servicekosten, voorschot_gwe, internet_kosten,
                    inventaris_kosten, afval_kosten, schoonmaak_kosten,
                    totale_huur, borg, contract_bestand, notities
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contract.property_id, contract.leverancier_id, contract.start_date, contract.end_date,
                contract.kale_huur, contract.servicekosten, contract.voorschot_gwe, contract.internet_kosten,
                contract.inventaris_kosten, contract.afval_kosten, contract.schoonmaak_kosten,
                contract.totale_huur, contract.borg, contract.contract_bestand, contract.notities
            ))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_active_contract(self, huis_id: int, query_date: date = None) -> Optional[InhuurContract]:
        """Get the contract active on a specific date (default: today)."""
        if query_date is None:
            query_date = date.today()
            
        conn = self.db._get_connection()
        # Find contract where start_date <= query_date AND (end_date IS NULL OR end_date >= query_date)
        row = conn.execute("""
            SELECT * FROM inhuur_contracten 
            WHERE property_id = ? 
            AND start_date <= ? 
            AND (end_date IS NULL OR end_date >= ?)
            ORDER BY start_date DESC
            LIMIT 1
        """, (huis_id, query_date, query_date)).fetchone()
        conn.close()
        
        if not row:
            return None
            
        return InhuurContract(
            id=row['id'],
            property_id=row['property_id'],
            leverancier_id=row['leverancier_id'],
            start_date=datetime.strptime(row['start_date'], '%Y-%m-%d').date() if isinstance(row['start_date'], str) else row['start_date'],
            end_date=datetime.strptime(row['end_date'], '%Y-%m-%d').date() if row['end_date'] else None,
            kale_huur=row['kale_huur'],
            servicekosten=row['servicekosten'],
            voorschot_gwe=row['voorschot_gwe'],
            internet_kosten=row['internet_kosten'],
            inventaris_kosten=row['inventaris_kosten'],
            afval_kosten=row['afval_kosten'],
            schoonmaak_kosten=row['schoonmaak_kosten'],
            totale_huur=row['totale_huur'],
            borg=row['borg'],
            contract_bestand=row['contract_bestand'],
            notities=row['notities']
        )

    # ==========================================
    # 4. KLANTEN (Clients)
    # ==========================================

    def add_klant(self, naam: str, type: str = 'particulier', 
                  contactpersoon: str = None, email: str = None, 
                  min_marge: float = None, max_marge: float = None) -> int:
        """Add a new client."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO klanten (naam, type, contactpersoon, email, min_marge_pct, max_marge_pct)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (naam, type, contactpersoon, email, min_marge, max_marge))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    # ==========================================
    # 5. PARAMETERS & VERHUUR CONTRACTEN
    # ==========================================

    def add_parameter(self, naam: str, prijs_pp_pw: float, eenheid: str = 'per_persoon_per_week') -> int:
        """Add a new cost parameter."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO parameters (naam, prijs_pp_pw, eenheid)
                VALUES (?, ?, ?)
            """, (naam, prijs_pp_pw, eenheid))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_parameters(self) -> List[dict]:
        """Get all active parameters."""
        conn = self.db._get_connection()
        rows = conn.execute("SELECT * FROM parameters WHERE is_actief = 1").fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def create_verhuur_contract(self, huis_id: int, klant_id: int, start_datum: date, 
                                kale_huur: float, parameter_ids: List[int]) -> int:
        """
        Create a new rental contract and calculate totals based on parameters.
        """
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            
            # 1. Get House Capacity
            huis_row = cursor.execute("SELECT aantal_pers FROM huizen WHERE id = ?", (huis_id,)).fetchone()
            if not huis_row: raise ValueError(f"Huis {huis_id} not found")
            capacity = huis_row['aantal_pers'] or 0
            
            # 2. Create Contract (Draft)
            cursor.execute("""
                INSERT INTO verhuur_contracten (huis_id, klant_id, start_datum, kale_huur)
                VALUES (?, ?, ?, ?)
            """, (huis_id, klant_id, start_datum, kale_huur))
            contract_id = cursor.lastrowid
            
            # 3. Process Parameters & Create Rules
            total_monthly_params = 0.0
            
            for param_id in parameter_ids:
                # Get base parameter
                param = cursor.execute("SELECT * FROM parameters WHERE id = ?", (param_id,)).fetchone()
                if not param: continue
                
                # Check for client override
                override = cursor.execute("""
                    SELECT prijs_pp_pw_override FROM klant_parameters 
                    WHERE klant_id = ? AND parameter_id = ? AND is_actief = 1
                """, (klant_id, param_id)).fetchone()
                
                # Determine final price
                prijs = param['prijs_pp_pw']
                if override and override['prijs_pp_pw_override'] is not None:
                    prijs = override['prijs_pp_pw_override']
                
                # Calculate: Price * Capacity * 4 (weeks/month)
                maand_bedrag = prijs * capacity * 4
                total_monthly_params += maand_bedrag
                
                cursor.execute("""
                    INSERT INTO contract_regels (
                        contract_id, parameter_id, parameter_naam, 
                        prijs_pp_pw, aantal_personen, totaal_maand_bedrag
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    contract_id, param_id, param['naam'], 
                    prijs, capacity, maand_bedrag
                ))
            
            # 4. Update Contract Totals (if we had a column for it, but we can query it)
            # For now, we just commit.
            
            conn.commit()
            return contract_id
        finally:
            conn.close()

    # ==========================================
    # 5. ADVANCED FEATURES (Client Params, Occupancy, Operations)
    # ==========================================

    def add_klant_parameter(self, klant_id: int, parameter_id: int, prijs_override: float = None, is_actief: bool = True):
        """Add or update a client-specific parameter override."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO klant_parameters (klant_id, parameter_id, prijs_pp_pw_override, is_actief)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(klant_id, parameter_id) DO UPDATE SET
                    prijs_pp_pw_override = excluded.prijs_pp_pw_override,
                    is_actief = excluded.is_actief
            """, (klant_id, parameter_id, prijs_override, is_actief))
            conn.commit()
        finally:
            conn.close()

    def add_borg_transactie(self, boeking_id: int, datum: date, trans_type: str, bedrag: float, reden: str = None):
        """Log a deposit transaction (ontvangst, terugbetaling, inhouding)."""
        valid_types = ['ontvangst', 'terugbetaling', 'inhouding']
        if trans_type not in valid_types:
            raise ValueError(f"Invalid transaction type. Must be one of {valid_types}")
            
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO borg_transacties (boeking_id, datum, type, bedrag, reden)
                VALUES (?, ?, ?, ?, ?)
            """, (boeking_id, datum, trans_type, bedrag, reden))
            conn.commit()
        finally:
            conn.close()

    def log_checkin(self, boeking_id: int, datum: date, door: str, sleutels: str, notities: str = None):
        """Log a check-in event."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checkins (boeking_id, datum, uitgevoerd_door, sleutelset, notities)
                VALUES (?, ?, ?, ?, ?)
            """, (boeking_id, datum, door, sleutels, notities))
            
            # Update booking status
            cursor.execute("UPDATE boekingen SET status = 'checked_in' WHERE id = ?", (boeking_id,))
            conn.commit()
        finally:
            conn.close()

    def log_checkout(self, boeking_id: int, datum_werkelijk: date, door: str, schade: float = 0, schoonmaak: float = 0, notities: str = None):
        """Log a check-out event."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checkouts (boeking_id, datum_werkelijk, uitgevoerd_door, schade_geschat, schoonmaak_kosten, notities)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (boeking_id, datum_werkelijk, door, schade, schoonmaak, notities))
            
            # Update booking status
            cursor.execute("UPDATE boekingen SET status = 'checked_out' WHERE id = ?", (boeking_id,))
            conn.commit()
        finally:
            conn.close()

    def _log_status_change(self, cursor, property_id, status, reason):
        cursor.execute("""
            INSERT INTO huizen_status_log (property_id, status, datum_gewijzigd, reden)
            VALUES (?, ?, CURRENT_DATE, ?)
        """, (property_id, status, reason))

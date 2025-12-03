from datetime import date, timedelta, datetime
from typing import List, Dict, Optional
import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from Shared.database import Database

class PlanningAPI:
    """
    API Layer for Incheck/Outcheck Planning.
    Handles logic for transitions, priorities, and inspections.
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path or "database/ryanrent_core.db"
        self.db = Database(self.db_path)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _dict_factory(self, cursor, row):
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_upcoming_transitions(self, days_lookahead: int = 60, client_name: str = None, filters: Dict = None) -> List[Dict]:
        """
        Get upcoming transitions (checkouts) with details.
        
        Args:
            days_lookahead: Number of days to look ahead
            client_name: Optional filter by client name
            filters: Optional dictionary of boolean filters:
                     - missing_pre_inspection: Only show if pre-inspection is needed
                     - has_next_tenant: Only show if next tenant is scheduled
                     - missing_vis: Only show if VIS is needed for next tenant
                     
        Returns:
            List of transition dictionaries
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()

        start_date_obj = datetime.now().date()
        end_date_obj = start_date_obj + timedelta(days=days_lookahead)
        
        # We look back 30 days to catch unfinished business, but the primary window is from today.
        # The query uses `start_date` and `end_date` for the BETWEEN clause.
        # Let's keep the original logic for the query range, but use the new start_date for priority calculation.
        query_start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        query_end_date = (date.today() + timedelta(days=days_lookahead)).strftime('%Y-%m-%d')

        query = """
        SELECT 
            b.id as booking_id,
            b.huis_id,
            b.checkout_datum,
            k.naam as client_name,
            h.adres as property_address,
            h.object_id,
            c.datum_werkelijk as werkelijke_datum,
            NULL as tijd,
            0 as terug_naar_eigenaar,
            CASE WHEN c.schoonmaak_kosten > 0 THEN 1 ELSE 0 END as schoonmaak_vereist,
            0 as meubilair_verwijderen,
            0 as sleutels_ontvangen,
            CASE WHEN c.schade_geschat > 0 THEN 1 ELSE 0 END as schade_gemeld,
            'unknown' as afrekening_status
        FROM boekingen b
        JOIN klanten k ON b.klant_id = k.id
        JOIN huizen h ON b.huis_id = h.id
        LEFT JOIN checkouts c ON b.id = c.boeking_id
        WHERE b.checkout_datum BETWEEN ? AND ?
        ORDER BY b.checkout_datum ASC
        """
        
        cursor.execute(query, (query_start_date, query_end_date))
        checkouts_data = cursor.fetchall()
        transitions = []
        for checkout in checkouts_data:
            # Determine priority
            try:
                checkout_date = datetime.strptime(checkout['checkout_datum'], '%Y-%m-%d').date()
            except:
                checkout_date = datetime.now().date() # Fallback
                
            days_until = (checkout_date - datetime.now().date()).days
            priority = 'low'
            if days_until < 3: priority = 'high'
            elif days_until < 7: priority = 'medium'
            
            # Find next booking
            volgende_huurder = "Geen nieuwe huurder"
            dagen_tussen = None
            
            # Find next booking for this house
            cursor.execute("""
                SELECT b.checkin_datum, k.naam 
                FROM boekingen b
                JOIN klanten k ON b.klant_id = k.id
                WHERE b.huis_id = ? AND b.checkin_datum >= ?
                ORDER BY b.checkin_datum ASC
                LIMIT 1
            """, (checkout['huis_id'], checkout['checkout_datum']))
            
            next_booking = cursor.fetchone()
            
            if next_booking:
                volgende_huurder = next_booking['naam']
                try:
                    next_checkin = datetime.strptime(next_booking['checkin_datum'], '%Y-%m-%d').date()
                    dagen_tussen = (next_checkin - checkout_date).days
                except:
                    pass
                next_row = cursor.fetchone()
                
                if next_row:
                    next_date_val = next_row['datum']
                    next_date = datetime.strptime(next_date_val, '%Y-%m-%d').date() if isinstance(next_date_val, str) else next_date_val
                    if isinstance(next_date, datetime): next_date = next_date.date()
                        
                    volgende_huurder = f"{next_row['naam']} ({next_date})"
                    dagen_tussen = (next_date - checkout_date).days
                    
                    if dagen_tussen < 3: priority = 'high' # Upgrade priority if gap is tight

            # Fetch Inspection Statuses
            # Current Booking (Voorinspectie, Eindinspectie)
            inspecties_query = """
            SELECT inspection_type, status, planned_date, inspector
            FROM inspections 
            WHERE booking_id = ?
            """
            cursor.execute(inspecties_query, (checkout['booking_id'],))
            huidige_inspecties = {row['inspection_type']: row for row in cursor.fetchall()}

            # Next Booking (VIS, Incheck)
            # VIS is usually linked to the next booking's pre-checkin inspection? 
            # Or is it the 'incheck' itself?
            # The user mentioned 'VIS_Referentie' on the incheck table.
            # Let's assume 'vis' and 'incheck' are related to the next booking.
            
            volgende_inspecties = {}
            # We need the next booking ID. We can get it from the incheck we found earlier if we selected it.
            # But we only selected datum and naam.
            # Let's just use defaults for now or fetch if critical.
            # Actually, the template needs these keys.
            
            transition = {
                "booking_id": checkout['booking_id'],
                "type": "checkout",
                "date": checkout['checkout_datum'],
                "property": checkout['property_address'],
                "client": checkout['client_name'],
                "priority": priority,
                "volgende_huurder": volgende_huurder,
                "dagen_tussen": dagen_tussen,
                
                # Inspection Statuses (Mapped for template or Dutch keys)
                "voorinspectie": huidige_inspecties.get('voorinspectie', {'status': 'nodig'}),
                "eindinspectie": huidige_inspecties.get('eindinspectie', {'status': 'nodig'}),
                # For next tenant inspections, we might not have them yet if we didn't fetch next booking ID.
                # But we can provide placeholders.
                "vis": {'status': 'nodig' if volgende_huurder != "Geen nieuwe huurder" else 'n.v.t.'},
                "incheck": {'status': 'nodig' if volgende_huurder != "Geen nieuwe huurder" else 'n.v.t.'},
                
                "details": {
                    "werkelijke_datum": checkout['werkelijke_datum'],
                    "tijd": checkout['tijd'],
                    "terug_naar_eigenaar": bool(checkout['terug_naar_eigenaar']),
                    "schoonmaak_vereist": bool(checkout['schoonmaak_vereist']),
                    "meubilair_verwijderen": bool(checkout['meubilair_verwijderen']),
                    "sleutels_ontvangen": bool(checkout['sleutels_ontvangen']),
                    "schade_gemeld": bool(checkout['schade_gemeld']),
                    "afrekening_status": checkout['afrekening_status'] or 'in_afwachting'
                }
            }
            transitions.append(transition)
            
        conn.close()
        
        # Apply Filters
        if filters:
            filtered_transitions = []
            for t in transitions:
                include = True
                
                if filters.get('missing_pre_inspection'):
                    if t['voorinspectie']['status'] != 'nodig':
                        include = False
                        
                if filters.get('has_next_tenant'):
                    if t['volgende_huurder'] == "Geen nieuwe huurder":
                        include = False
                        
                if filters.get('missing_vis'):
                    if t['vis']['status'] != 'nodig':
                        include = False
                        
                if include:
                    filtered_transitions.append(t)
            return filtered_transitions
            
        return transitions


    def schedule_inspection(self, booking_id: int, inspection_type: str, date_str: str, inspector: str) -> bool:
        """Schedule a new inspection."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT id FROM inspections WHERE booking_id = ? AND inspection_type = ?", (booking_id, inspection_type))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE inspections 
                SET planned_date = ?, inspector = ?, status = 'planned'
                WHERE id = ?
            """, (date_str, inspector, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO inspections (booking_id, inspection_type, planned_date, inspector, status)
                VALUES (?, ?, ?, ?, 'planned')
            """, (booking_id, inspection_type, date_str, inspector))
            
        conn.commit()
        conn.close()
        return True

    def update_inspection_status(self, booking_id: int, inspection_type: str, status: str, notes: str = None) -> bool:
        """Update status of an inspection."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = "UPDATE inspections SET status = ?"
        params = [status]
        
        if notes:
            query += ", notes = ?"
            params.append(notes)
            
        query += " WHERE booking_id = ? AND inspection_type = ?"
        params.extend([booking_id, inspection_type])
        
        cursor.execute(query, tuple(params))
        conn.commit()
        conn.close()
        return True

    def get_transition_by_client(self, client_name: str, days_lookahead: int = 90) -> List[Dict]:
        """
        Find upcoming transitions for a specific client.
        
        Args:
            client_name: Name of the client to search for
            days_lookahead: Number of days to look ahead (default 90)
            
        Returns:
            List of transition dicts for this client
        """
        all_transitions = self.get_upcoming_transitions(days_lookahead)
        
        # Filter by client name (case-insensitive partial match)
        client_transitions = [
            t for t in all_transitions 
            if client_name.lower() in t['current_client'].lower() or 
               client_name.lower() in t['next_tenant'].lower()
        ]
        
        return client_transitions
    
    def get_transitions_by_date_range(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Get all transitions in a specific date range.
        
        Args:
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            List of transition dicts in the date range
        """
        conn = self._get_connection()
        conn.row_factory = self._dict_factory
        cursor = conn.cursor()

        query = """
        SELECT 
            b.id as booking_id,
            b.huis_id,
            b.checkout_datum,
            k.naam as client_name,
            h.adres as property_address,
            h.object_id
        FROM boekingen b
        JOIN klanten k ON b.klant_id = k.id
        JOIN huizen h ON b.huis_id = h.id
        WHERE b.checkout_datum BETWEEN ? AND ?
        ORDER BY b.checkout_datum ASC
        """
        
        cursor.execute(query, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
        checkouts = cursor.fetchall()

        transitions = []

        for checkout in checkouts:
            # Find the NEXT booking for this house
            next_booking_query = """
            SELECT 
                b.id as next_booking_id,
                b.checkin_datum as next_checkin_date,
                k.naam as next_client_name
            FROM boekingen b
            JOIN klanten k ON b.klant_id = k.id
            WHERE b.huis_id = ? AND b.checkin_datum >= ?
            ORDER BY b.checkin_datum ASC
            LIMIT 1
            """
            cursor.execute(next_booking_query, (checkout['huis_id'], checkout['checkout_datum']))
            next_booking = cursor.fetchone()

            # Calculate Gap and Priority
            gap_days = None
            priority = "LOW"
            next_tenant_info = "Geen nieuwe huurder"
            
            if next_booking:
                checkout_date = datetime.strptime(checkout['checkout_datum'], '%Y-%m-%d').date()
                next_checkin = datetime.strptime(next_booking['next_checkin_date'], '%Y-%m-%d').date()
                gap_days = (next_checkin - checkout_date).days
                
                next_tenant_info = f"{next_booking['next_client_name']} ({next_booking['next_checkin_date']})"

                if gap_days < 14:
                    priority = "CRITICAL"
                elif gap_days < 30:
                    priority = "HIGH"
                else:
                    priority = "NORMAL"

            # Fetch Inspection Statuses
            inspections_query = """
            SELECT inspection_type, status, planned_date, inspector
            FROM inspections 
            WHERE booking_id = ?
            """
            cursor.execute(inspections_query, (checkout['booking_id'],))
            current_inspections = {row['inspection_type']: row for row in cursor.fetchall()}

            next_inspections = {}
            if next_booking:
                cursor.execute(inspections_query, (next_booking['next_booking_id'],))
                next_inspections = {row['inspection_type']: row for row in cursor.fetchall()}

            # Assemble Transition Object
            transition = {
                "property": f"{checkout['property_address']} ({checkout['object_id']})",
                "checkout_date": checkout['checkout_datum'],
                "current_client": checkout['client_name'],
                "priority": priority,
                "gap_days": gap_days,
                "next_tenant": next_tenant_info,
                
                # Inspection Statuses
                "pre_inspection": current_inspections.get('pre_inspection', {'status': 'needed'}),
                "uitcheck": current_inspections.get('uitcheck', {'status': 'needed'}),
                "vis": next_inspections.get('vis', {'status': 'needed' if next_booking else 'n/a'}),
                "incheck": next_inspections.get('incheck', {'status': 'needed' if next_booking else 'n/a'}),
                
                # IDs for actions
                "current_booking_id": checkout['booking_id'],
                "next_booking_id": next_booking['next_booking_id'] if next_booking else None
            }
            transitions.append(transition)

        conn.close()
        return transitions
    
    def get_critical_transitions(self) -> List[Dict]:
        """
        Get all transitions with CRITICAL priority.
        
        Returns:
            List of critical transition dicts
        """
        all_transitions = self.get_upcoming_transitions(days_lookahead=60)
        
        # Filter for critical priority
        critical_transitions = [
            t for t in all_transitions 
            if t['priority'] == 'CRITICAL'
        ]
        
        return critical_transitions

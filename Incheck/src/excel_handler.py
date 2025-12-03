import pandas as pd
import sqlite3
import os
from datetime import datetime

class PlanningExcelHandler:
    def __init__(self, db_path):
        self.db_path = db_path

    def _format_date(self, date_val):
        if not date_val: return ''
        if isinstance(date_val, str):
            try:
                # Try parsing YYYY-MM-DD
                return datetime.strptime(date_val, '%Y-%m-%d').strftime('%d-%m-%Y')
            except:
                return date_val
        if hasattr(date_val, 'strftime'):
            return date_val.strftime('%d-%m-%Y')
        return str(date_val)

    def generate_excel(self, transitions, output_path):
        """
        Generates an Excel file from the list of transitions.
        """
        data = []
        for t in transitions:
            # Extract dates safely
            voor_date = t.get('voorinspectie', {}).get('geplande_datum', '')
            eind_date = t.get('eindinspectie', {}).get('geplande_datum', '')
            
            row = {
                'Booking ID': t['booking_id'], # System ID
                'Adres': t['property'],
                'Klant': t['client'],
                'Uitcheck Datum': self._format_date(t['date']),
                'Nieuwe Huurder': t['volgende_huurder'],
                'Voorinspectie Datum': self._format_date(voor_date),
                'Voorinspectie Inspecteur': t.get('voorinspectie', {}).get('inspecteur', ''),
                'Eindinspectie Datum': self._format_date(eind_date),
                'Eindinspectie Inspecteur': t.get('eindinspectie', {}).get('inspecteur', ''),
                'Opmerkingen': '' 
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        df.to_excel(output_path, index=False)
        return output_path

    def process_update(self, file_path):
        """
        Reads an Excel file and updates the database with new inspection dates/inspectors.
        """
        if not os.path.exists(file_path):
            return "Error: File not found."
            
        df = pd.read_excel(file_path)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates_count = 0
        
        for index, row in df.iterrows():
            try:
                booking_id = row.get('Booking ID')
                if pd.isna(booking_id): continue
                booking_id = int(booking_id)
                
                # Update Voorinspectie
                v_date = row.get('Voorinspectie Datum')
                v_insp = row.get('Voorinspectie Inspecteur')
                if pd.notna(v_date):
                    self._update_inspection(cursor, booking_id, 'voorinspectie', v_date, v_insp)
                    updates_count += 1
                    
                # Update Eindinspectie
                e_date = row.get('Eindinspectie Datum')
                e_insp = row.get('Eindinspectie Inspecteur')
                if pd.notna(e_date):
                    self._update_inspection(cursor, booking_id, 'eindinspectie', e_date, e_insp)
                    updates_count += 1
                    
            except Exception as e:
                print(f"Error processing row {index}: {e}")
                
        conn.commit()
        conn.close()
        return f"Successfully processed file. Updated/Verified {updates_count} inspection records."

    def _update_inspection(self, cursor, booking_id, inspectie_type, date_val, inspector):
        # Parse date
        date_str = None
        if hasattr(date_val, 'strftime'):
            date_str = date_val.strftime('%Y-%m-%d')
        elif isinstance(date_val, str):
            # Try parsing common formats
            for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    date_str = datetime.strptime(date_val, fmt).strftime('%Y-%m-%d')
                    break
                except:
                    pass
            if not date_str:
                return # Could not parse date
        else:
            return # Unknown type

        inspector_val = inspector if pd.notna(inspector) else None

        # Check if exists
        cursor.execute("SELECT id FROM inspections WHERE booking_id=? AND inspection_type=?", (booking_id, inspectie_type))
        res = cursor.fetchone()
        
        if res:
            cursor.execute("""
                UPDATE inspections 
                SET planned_date=?, inspector=?, status='planned'
                WHERE id=?
            """, (date_str, inspector_val, res[0]))
        else:
            cursor.execute("""
                INSERT INTO inspections (booking_id, inspection_type, planned_date, inspector, status)
                VALUES (?, ?, ?, ?, 'planned')
            """, (booking_id, inspectie_type, date_str, inspector_val))

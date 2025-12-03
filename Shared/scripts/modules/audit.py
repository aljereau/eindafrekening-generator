import sqlite3
import os
from datetime import datetime, timedelta

class AuditController:
    """
    The Controller: Checks data integrity and flags issues.
    """
    def __init__(self, db_path):
        self.db_path = db_path

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def run_full_audit(self):
        """Runs all checks and returns a summary report."""
        issues = []
        issues.extend(self.check_expired_contracts())
        issues.extend(self.check_missing_safe_codes())
        issues.extend(self.check_missing_financials())
        issues.extend(self.check_duplicate_addresses())
        
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_issues": len(issues),
            "issues": issues
        }

    def check_expired_contracts(self):
        """Finds active contracts that have passed their end date."""
        conn = self.get_conn()
        cursor = conn.cursor()
        issues = []
        
        # Verhuur
        cursor.execute("""
            SELECT h.adres, k.naam, vc.eind_datum 
            FROM verhuur_contracten vc
            JOIN huizen h ON vc.huis_id = h.id
            JOIN klanten k ON vc.klant_id = k.id
            WHERE vc.status = 'active' AND vc.eind_datum < DATE('now')
        """)
        for row in cursor.fetchall():
            issues.append({
                "type": "Expired Contract (Verhuur)",
                "severity": "High",
                "description": f"Contract for {row[0]} (Client: {row[1]}) expired on {row[2]} but is still active."
            })
            
        # Inhuur
        cursor.execute("""
            SELECT h.adres, l.naam, ic.end_date
            FROM inhuur_contracten ic
            JOIN huizen h ON ic.property_id = h.id
            JOIN leveranciers l ON ic.leverancier_id = l.id
            WHERE ic.end_date < DATE('now') -- Assuming no status column on inhuur yet, or implicit active
        """)
        for row in cursor.fetchall():
            issues.append({
                "type": "Expired Contract (Inhuur)",
                "severity": "Medium",
                "description": f"Hiring contract for {row[0]} (Owner: {row[1]}) expired on {row[2]}."
            })
            
        conn.close()
        return issues

    def check_missing_safe_codes(self):
        """Finds active houses without safe codes."""
        conn = self.get_conn()
        cursor = conn.cursor()
        issues = []
        
        cursor.execute("""
            SELECT object_id, adres 
            FROM huizen 
            WHERE status = 'active' AND (kluis_code_1 IS NULL OR kluis_code_1 = '')
        """)
        for row in cursor.fetchall():
            issues.append({
                "type": "Missing Data",
                "severity": "Medium",
                "description": f"House {row[0]} ({row[1]}) is missing Safe Code 1."
            })
            
        conn.close()
        return issues

    def check_missing_financials(self):
        """Finds active houses with no active rental contract."""
        conn = self.get_conn()
        cursor = conn.cursor()
        issues = []
        
        # Houses with no active verhuur contract
        cursor.execute("""
            SELECT h.object_id, h.adres
            FROM huizen h
            LEFT JOIN verhuur_contracten vc ON h.id = vc.huis_id AND vc.status = 'active'
            WHERE h.status = 'active' AND vc.id IS NULL
        """)
        for row in cursor.fetchall():
            issues.append({
                "type": "Missing Revenue",
                "severity": "High",
                "description": f"Active house {row[0]} ({row[1]}) has no active rental contract."
            })
            
        conn.close()
        return issues

    def check_duplicate_addresses(self):
        """Finds potential duplicate addresses."""
        conn = self.get_conn()
        cursor = conn.cursor()
        issues = []
        
        cursor.execute("""
            SELECT adres, COUNT(*) as cnt 
            FROM huizen 
            WHERE status = 'active' 
            GROUP BY adres 
            HAVING cnt > 1
        """)
        for row in cursor.fetchall():
            issues.append({
                "type": "Data Integrity",
                "severity": "Low",
                "description": f"Address '{row[0]}' appears {row[1]} times in active houses."
            })
            
        conn.close()
        return issues

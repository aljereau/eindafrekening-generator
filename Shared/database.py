#!/usr/bin/env python3
"""
Database Module - SQLite operations for Eindafrekening Generator
Handles:
- Schema initialization and migrations
- Eindafrekening storage with versioning
- Core entities: Properties, Clients, Contracts, Bookings
"""

import sqlite3
import json
import os
import sys
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path


class Database:
    """SQLite database manager for RyanRent Core"""

    DEFAULT_DB_PATH = "database/ryanrent_core.db"
    
    def __init__(self, db_path: str = None):
        """
        Initialize database connection
        Args:
            db_path: Path to SQLite database file
        """
        # Determine project root and default DB path
        if getattr(sys, 'frozen', False):
            # Running as compiled app (PyInstaller)
            # sys.executable is .../RyanRent Admin.app/Contents/MacOS/RyanRent Admin
            # We want to go up to the folder CONTAINING the .app
            bundle_dir = os.path.dirname(sys.executable)
            # Go up 3 levels to get out of .app/Contents/MacOS
            project_root = os.path.abspath(os.path.join(bundle_dir, '..', '..', '..'))
        else:
            # Running as script
            # Shared/database.py -> Shared -> Project Root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
        
        # Default path is ALWAYS [ProjectRoot]/database/ryanrent_core.db
        default_db_path = os.path.join(project_root, "database", "ryanrent_core.db")
        
        self.db_path = db_path or default_db_path
        
        # Migrations are in Shared/migrations
        # If frozen, they are bundled in _MEIxxxx/Shared/migrations
        if getattr(sys, 'frozen', False):
             # In PyInstaller --onefile/--onedir, data is in sys._MEIPASS
             base_path = sys._MEIPASS
             self.migrations_dir = os.path.join(base_path, "Shared", "migrations")
        else:
             current_dir = os.path.dirname(os.path.abspath(__file__))
             self.migrations_dir = os.path.join(current_dir, "migrations")

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize/Migrate database
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def _init_database(self):
        """Initialize database and run all migrations"""
        print(f"📊 Checking database schema: {self.db_path}")

        # Get all migration files
        if not os.path.exists(self.migrations_dir):
            print(f"   ⚠️  Migrations dir not found: {self.migrations_dir}")
            return

        migration_files = sorted([
            f for f in os.listdir(self.migrations_dir) 
            if f.endswith('.sql')
        ])

        conn = self._get_connection()
        try:
            # Create migrations table if not exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Apply each migration
            for migration_file in migration_files:
                if not self._is_migration_applied(conn, migration_file):
                    print(f"   Applying migration: {migration_file}...")
                    self._apply_migration(conn, migration_file)
                    print(f"   ✓ Applied {migration_file}")
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"   ❌ Database initialization failed: {e}")
            raise
        finally:
            conn.close()

    def _is_migration_applied(self, conn: sqlite3.Connection, filename: str) -> bool:
        """Check if a migration has already been applied"""
        cursor = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE version = ?", 
            (filename,)
        )
        return cursor.fetchone() is not None

    def _apply_migration(self, conn: sqlite3.Connection, filename: str):
        """Apply a single migration file"""
        file_path = os.path.join(self.migrations_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        conn.executescript(sql)
        conn.execute(
            "INSERT INTO schema_migrations (version) VALUES (?)", 
            (filename,)
        )

    # ==========================================
    # CORE ENTITIES: CLIENTS
    # ==========================================

    def add_client(self, name: str, email: str, **kwargs) -> int:
        """Add a new client"""
        conn = self._get_connection()
        try:
            # Check if exists
            cursor = conn.execute("SELECT id FROM clients WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row['id']

            columns = ['name', 'email'] + list(kwargs.keys())
            placeholders = ['?'] * len(columns)
            values = [name, email] + list(kwargs.values())
            
            sql = f"INSERT INTO clients ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor = conn.execute(sql, values)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_client(self, client_id: int) -> Optional[Dict[str, Any]]:
        """Get client by ID"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ==========================================
    # CORE ENTITIES: PROPERTIES
    # ==========================================

    def add_property(self, address: str, **kwargs) -> int:
        """Add a new property"""
        conn = self._get_connection()
        try:
            # Check if exists
            cursor = conn.execute("SELECT id FROM properties WHERE address = ?", (address,))
            row = cursor.fetchone()
            if row:
                return row['id']

            columns = ['address'] + list(kwargs.keys())
            placeholders = ['?'] * len(columns)
            values = [address] + list(kwargs.values())
            
            sql = f"INSERT INTO properties ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor = conn.execute(sql, values)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_all_properties(self) -> List[Dict[str, Any]]:
        """Get all properties"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM properties ORDER BY address")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """Get raw database connection (public)"""
        return self._get_connection()

    def create_contract(self, property_id: int, client_id: int, start_date: date, 
                       rent_price_excl: float, **kwargs) -> int:
        """Create a new contract"""
        conn = self._get_connection()
        try:
            columns = ['property_id', 'client_id', 'start_date', 'rent_price_excl'] + list(kwargs.keys())
            placeholders = ['?'] * len(columns)
            values = [property_id, client_id, str(start_date), rent_price_excl] + list(kwargs.values())
            
            sql = f"INSERT INTO contracts ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            cursor = conn.execute(sql, values)
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    # ==========================================
    # EINDAFREKENINGEN (Legacy + New)
    # ==========================================

    def check_existing_version(
        self,
        client_name: str,
        checkin_date: date,
        checkout_date: date
    ) -> Optional[Dict[str, Any]]:
        """Check if eindafrekening already exists"""
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT version, version_reason, totaal_eindafrekening, created_at, file_path
                FROM eindafrekeningen
                WHERE client_name = ? AND checkin_date = ? AND checkout_date = ?
                ORDER BY version DESC
            """, (client_name, str(checkin_date), str(checkout_date)))

            versions = [dict(row) for row in cursor.fetchall()]
            if not versions:
                return None

            return {
                'latest_version': versions[0]['version'],
                'version_count': len(versions),
                'first_created': versions[-1]['created_at'],
                'last_updated': versions[0]['created_at'],
                'versions': versions
            }
        finally:
            conn.close()

    def get_next_version(self, client_name: str, checkin_date: date, checkout_date: date) -> Tuple[int, bool]:
        """Get next version number"""
        existing = self.check_existing_version(client_name, checkin_date, checkout_date)
        if existing is None:
            return (1, True)
        return (existing['latest_version'] + 1, False)

    def save_eindafrekening(
        self,
        client_name: str,
        checkin_date: date,
        checkout_date: date,
        version: int,
        version_reason: str,
        data_json: Dict[str, Any],
        object_address: str = "",
        period_days: int = 0,
        borg_terug: float = 0.0,
        gwe_totaal_incl: float = 0.0,
        totaal_eindafrekening: float = 0.0,
        file_path: str = ""
    ) -> int:
        """Save eindafrekening to database"""
        if version > 1 and not version_reason.strip():
            raise ValueError("version_reason is REQUIRED for revisions (version > 1)")

        json_data = json.dumps(data_json, ensure_ascii=False, indent=2)
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO eindafrekeningen (
                    client_name, checkin_date, checkout_date, version, version_reason,
                    data_json, object_address, period_days, borg_terug,
                    gwe_totaal_incl, totaal_eindafrekening, file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_name, str(checkin_date), str(checkout_date), version, version_reason,
                json_data, object_address, period_days, borg_terug,
                gwe_totaal_incl, totaal_eindafrekening, file_path
            ))
            conn.commit()
            print(f"   ✓ Saved to database: ID={cursor.lastrowid}, Version={version}")
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            print(f"   ❌ Database error: {e}")
            raise
        finally:
            conn.close()

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent eindafrekeningen"""
        conn = self._get_connection()
        try:
            # Note: 'latest_eindafrekeningen' is a view created in 001 migration
            cursor = conn.execute("""
                SELECT id, client_name, checkin_date, checkout_date, version, 
                       totaal_eindafrekening, created_at, file_path
                FROM latest_eindafrekeningen
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


# Convenience functions
def init_database(db_path: str = None) -> Database:
    """Initialize and return database instance"""
    return Database(db_path)


if __name__ == "__main__":
    """Test database operations"""
    print("🧪 Testing Database Module")
    print("=" * 60)

    test_db_path = "database/test_core.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = Database(test_db_path)
    
    # Test Core Entities
    print("\n1. Testing Core Entities...")
    client_id = db.add_client("Jansen BV", "info@jansen.nl", type="business")
    print(f"   ✓ Added Client: ID={client_id}")
    
    prop_id = db.add_property("Kalverstraat 1", city="Amsterdam", default_rent_excl=1500)
    print(f"   ✓ Added Property: ID={prop_id}")
    
    contract_id = db.create_contract(prop_id, client_id, date(2024, 1, 1), 1500)
    print(f"   ✓ Created Contract: ID={contract_id}")
    
    print("\n✅ All database tests passed!")

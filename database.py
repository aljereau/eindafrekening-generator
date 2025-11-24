#!/usr/bin/env python3
"""
Database Module - SQLite operations for Eindafrekening Generator

Handles:
- Schema initialization and migrations
- Eindafrekening storage with versioning
- Version detection and increment
- Query operations
"""

import sqlite3
import json
import os
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path


class Database:
    """SQLite database manager for eindafrekeningen"""

    DEFAULT_DB_PATH = "database/eindafrekeningen.db"
    MIGRATIONS_DIR = "migrations"

    def __init__(self, db_path: str = None):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file (default: database/eindafrekeningen.db)
        """
        self.db_path = db_path or self.DEFAULT_DB_PATH

        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database if it doesn't exist
        if not os.path.exists(self.db_path):
            self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn

    def _init_database(self):
        """Initialize database with schema from migration file"""
        print(f"📊 Initializing database: {self.db_path}")

        migration_file = os.path.join(self.MIGRATIONS_DIR, "001_initial_schema.sql")

        if not os.path.exists(migration_file):
            raise FileNotFoundError(f"Migration file not found: {migration_file}")

        with open(migration_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        conn = self._get_connection()
        try:
            conn.executescript(schema_sql)
            conn.commit()
            print(f"   ✓ Database schema initialized")
        except sqlite3.Error as e:
            print(f"   ❌ Schema initialization failed: {e}")
            raise
        finally:
            conn.close()

    def check_existing_version(
        self,
        client_name: str,
        checkin_date: date,
        checkout_date: date
    ) -> Optional[Dict[str, Any]]:
        """
        Check if eindafrekening already exists for client+dates

        Args:
            client_name: Client name
            checkin_date: Check-in date
            checkout_date: Check-out date

        Returns:
            Dictionary with existing version info, or None if not found
            {
                'latest_version': int,
                'version_count': int,
                'first_created': datetime,
                'last_updated': datetime,
                'versions': List[dict]  # All versions
            }
        """
        conn = self._get_connection()
        try:
            # Get all versions
            cursor = conn.execute("""
                SELECT
                    version,
                    version_reason,
                    totaal_eindafrekening,
                    created_at,
                    file_path
                FROM eindafrekeningen
                WHERE client_name = ?
                  AND checkin_date = ?
                  AND checkout_date = ?
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

    def get_next_version(
        self,
        client_name: str,
        checkin_date: date,
        checkout_date: date
    ) -> Tuple[int, bool]:
        """
        Get next version number for eindafrekening

        Args:
            client_name: Client name
            checkin_date: Check-in date
            checkout_date: Check-out date

        Returns:
            Tuple of (version_number, is_new)
            - (1, True) if new eindafrekening
            - (n+1, False) if revision of existing
        """
        existing = self.check_existing_version(client_name, checkin_date, checkout_date)

        if existing is None:
            return (1, True)
        else:
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
        """
        Save eindafrekening to database

        Args:
            client_name: Client name
            checkin_date: Check-in date
            checkout_date: Check-out date
            version: Version number
            version_reason: Reason for this version (REQUIRED for v2+)
            data_json: Complete viewmodel as dictionary
            object_address: Property address
            period_days: Number of days
            borg_terug: Deposit refund amount
            gwe_totaal_incl: GWE total including VAT
            totaal_eindafrekening: Final settlement amount
            file_path: Path to generated output file

        Returns:
            ID of inserted record

        Raises:
            ValueError: If version_reason is empty for v2+
            sqlite3.IntegrityError: If duplicate version exists
        """
        # Validate version reason (required for v2+)
        if version > 1 and not version_reason.strip():
            raise ValueError("version_reason is REQUIRED for revisions (version > 1)")

        # Convert data to JSON string
        json_data = json.dumps(data_json, ensure_ascii=False, indent=2)

        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO eindafrekeningen (
                    client_name,
                    checkin_date,
                    checkout_date,
                    version,
                    version_reason,
                    data_json,
                    object_address,
                    period_days,
                    borg_terug,
                    gwe_totaal_incl,
                    totaal_eindafrekening,
                    file_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                client_name,
                str(checkin_date),
                str(checkout_date),
                version,
                version_reason,
                json_data,
                object_address,
                period_days,
                borg_terug,
                gwe_totaal_incl,
                totaal_eindafrekening,
                file_path
            ))

            conn.commit()
            record_id = cursor.lastrowid

            print(f"   ✓ Saved to database: ID={record_id}, Version={version}")
            return record_id

        except sqlite3.IntegrityError as e:
            print(f"   ❌ Database error: {e}")
            raise
        finally:
            conn.close()

    def get_eindafrekening(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve eindafrekening by ID

        Args:
            record_id: Database record ID

        Returns:
            Dictionary with all fields, or None if not found
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM eindafrekeningen WHERE id = ?
            """, (record_id,))

            row = cursor.fetchone()
            if row:
                result = dict(row)
                # Parse JSON data
                result['data_json'] = json.loads(result['data_json'])
                return result
            return None

        finally:
            conn.close()

    def list_recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List recent eindafrekeningen (latest versions only)

        Args:
            limit: Maximum number of records to return

        Returns:
            List of eindafrekening summaries (no full JSON data)
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT
                    id,
                    client_name,
                    checkin_date,
                    checkout_date,
                    version,
                    version_reason,
                    totaal_eindafrekening,
                    created_at,
                    file_path
                FROM latest_eindafrekeningen
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def get_version_history_summary(self) -> List[Dict[str, Any]]:
        """
        Get summary of all eindafrekeningen with multiple versions

        Returns:
            List of summary records showing version history
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM version_history
            """)

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def search_by_client(self, client_name: str, partial: bool = True) -> List[Dict[str, Any]]:
        """
        Search eindafrekeningen by client name

        Args:
            client_name: Client name to search
            partial: If True, allows partial matches (default: True)

        Returns:
            List of matching eindafrekeningen
        """
        conn = self._get_connection()
        try:
            if partial:
                pattern = f"%{client_name}%"
                cursor = conn.execute("""
                    SELECT
                        id, client_name, checkin_date, checkout_date,
                        version, totaal_eindafrekening, created_at
                    FROM latest_eindafrekeningen
                    WHERE client_name LIKE ?
                    ORDER BY created_at DESC
                """, (pattern,))
            else:
                cursor = conn.execute("""
                    SELECT
                        id, client_name, checkin_date, checkout_date,
                        version, totaal_eindafrekening, created_at
                    FROM latest_eindafrekeningen
                    WHERE client_name = ?
                    ORDER BY created_at DESC
                """, (client_name,))

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()


# Convenience functions
def init_database(db_path: str = None) -> Database:
    """Initialize and return database instance"""
    return Database(db_path)


if __name__ == "__main__":
    """Test database operations"""
    import sys
    from datetime import date

    print("🧪 Testing Database Module")
    print("=" * 60)

    # Use test database
    test_db_path = "database/test_eindafrekeningen.db"

    # Clean up test database if exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print(f"   Cleaned up existing test database")

    # Initialize database
    db = Database(test_db_path)
    print(f"\n✓ Database initialized: {test_db_path}")

    # Test data
    test_data = {
        'client': {'name': 'Test Familie'},
        'period': {'days': 14},
        'financial': {'totals': {'totaal_eindafrekening': 150.50}}
    }

    # Test 1: Save new eindafrekening (v1)
    print("\n1. Testing save_eindafrekening (v1)...")
    version, is_new = db.get_next_version("Test Familie", date(2024, 7, 1), date(2024, 7, 15))
    print(f"   Next version: {version}, Is new: {is_new}")

    record_id = db.save_eindafrekening(
        client_name="Test Familie",
        checkin_date=date(2024, 7, 1),
        checkout_date=date(2024, 7, 15),
        version=version,
        version_reason="Eerste verzending",
        data_json=test_data,
        period_days=14,
        totaal_eindafrekening=150.50
    )
    print(f"   ✓ Saved v1: ID={record_id}")

    # Test 2: Check existing version
    print("\n2. Testing check_existing_version...")
    existing = db.check_existing_version("Test Familie", date(2024, 7, 1), date(2024, 7, 15))
    if existing:
        print(f"   ✓ Found existing: v{existing['latest_version']}, Count: {existing['version_count']}")
    else:
        print(f"   ❌ Should have found existing version!")
        sys.exit(1)

    # Test 3: Save revision (v2)
    print("\n3. Testing save_eindafrekening (v2 - revision)...")
    version, is_new = db.get_next_version("Test Familie", date(2024, 7, 1), date(2024, 7, 15))
    print(f"   Next version: {version}, Is new: {is_new}")

    record_id_v2 = db.save_eindafrekening(
        client_name="Test Familie",
        checkin_date=date(2024, 7, 1),
        checkout_date=date(2024, 7, 15),
        version=version,
        version_reason="Correctie GWE bedrag",
        data_json=test_data,
        period_days=14,
        totaal_eindafrekening=175.80
    )
    print(f"   ✓ Saved v2: ID={record_id_v2}")

    # Test 4: List recent
    print("\n4. Testing list_recent...")
    recent = db.list_recent(limit=10)
    print(f"   ✓ Found {len(recent)} records")
    for r in recent:
        print(f"      - {r['client_name']} v{r['version']}: €{r['totaal_eindafrekening']:.2f}")

    # Test 5: Version history
    print("\n5. Testing get_version_history_summary...")
    history = db.get_version_history_summary()
    print(f"   ✓ Found {len(history)} items with multiple versions")
    for h in history:
        print(f"      - {h['client_name']}: {h['version_count']} versions")

    # Test 6: Search by client
    print("\n6. Testing search_by_client...")
    results = db.search_by_client("Test")
    print(f"   ✓ Found {len(results)} matching records")

    print("\n✅ All database tests passed!")
    print(f"\n📍 Test database location: {os.path.abspath(test_db_path)}")

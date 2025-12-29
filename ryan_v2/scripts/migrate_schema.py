
import sqlite3
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")

def migrate_database():
    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        logger.info("--- Starting Migration ---")
        
        # --- Phase 0: Drop Dependent Views ---
        logger.info("Phase 0: Dropping dependent views...")
        cursor.execute("DROP VIEW IF EXISTS view_latest_pricing")
        
        # --- Phase 1: Standardize Object ID (Add Columns) ---
        logger.info("Phase 1: Adding object_id columns to related tables...")
        
        # Tables to migrate from huis_id/property_id (INT) to object_id (TEXT)
        # Mapping: table_name -> old_id_column
        tables_to_migrate = {
            'boekingen': 'huis_id',
            'verhuur_contracten': 'huis_id',
            'inhuur_contracten': 'property_id',
            'huizen_status_log': 'property_id'
        }
        
        for table, old_col in tables_to_migrate.items():
            # Check if column already exists
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [col['name'] for col in cursor.fetchall()]
            
            if 'object_id' not in columns:
                logger.info(f"Migrating {table}...")
                
                # 1. Add new column using the temp name first to allow for safe copy
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN object_id TEXT")
                
                # 2. Populate it by joining with huizen on the integer ID
                logger.info(f"Populating {table}.object_id from huizen.object_id...")
                
                sql = f"""
                    UPDATE {table} 
                    SET object_id = (
                        SELECT object_id 
                        FROM huizen 
                        WHERE huizen.id = {table}.{old_col}
                    )
                    WHERE object_id IS NULL
                """
                cursor.execute(sql)
                
                # 3. Rename old column to indicate legacy
                if f"{old_col}_old" not in columns:
                    cursor.execute(f"ALTER TABLE {table} RENAME COLUMN {old_col} TO {old_col}_old")
                    logger.info(f"Renamed {old_col} to {old_col}_old in {table}")
            
            else:
                logger.info(f"Table {table} already has object_id column. Skipping addition.")

        conn.commit()
        
        # --- Phase 2: Split Active/Archive ---
        logger.info("Phase 2: Splitting huizen into Active and Archive...")
        
        # 1. Create Archive Table
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='huizen'")
        create_sql = cursor.fetchone()['sql']
        create_archive_sql = create_sql.replace("CREATE TABLE huizen", "CREATE TABLE IF NOT EXISTS huizen_archief")
        if "huizen_archief" not in create_archive_sql:
             create_archive_sql = "CREATE TABLE IF NOT EXISTS huizen_archief AS SELECT * FROM huizen WHERE 0"
        
        cursor.execute(create_archive_sql)
        
        # 2. Copy Archived Data
        logger.info("Copying archived properties (A-%) to huizen_archief...")
        cursor.execute("INSERT OR IGNORE INTO huizen_archief SELECT * FROM huizen WHERE object_id LIKE 'A-%'")
        archive_count = cursor.rowcount
        logger.info(f"Copied {archive_count} rows to archive.")
        
        # 3. Delete from Active
        logger.info("Removing archived properties from huizen...")
        cursor.execute("DELETE FROM huizen WHERE object_id LIKE 'A-%'")
        delete_count = cursor.rowcount
        logger.info(f"Removed {delete_count} rows from active huizen.")
        
        # 4. Create View union
        logger.info("Phase 3: Creating v_alle_huizen view...")
        cursor.execute("DROP VIEW IF EXISTS v_alle_huizen")
        cursor.execute("""
            CREATE VIEW v_alle_huizen AS
            SELECT *, 'active' as source FROM huizen
            UNION ALL
            SELECT *, 'archive' as source FROM huizen_archief
        """)

        # 5. Re-create view_latest_pricing using NEW columns
        logger.info("Phase 4: Recreating view_latest_pricing with updated schema...")
        cursor.execute("""
            CREATE VIEW view_latest_pricing AS
            WITH
                latest_verhuur AS (
                    SELECT *, ROW_NUMBER() OVER (
                            PARTITION BY
                                object_id
                            ORDER BY start_datum DESC
                        ) as rn
                    FROM verhuur_contracten
                    WHERE
                        status = 'active'
                        OR eind_datum IS NULL
                        OR eind_datum >= DATE('now')
                ),
                latest_inhuur AS (
                    SELECT *, ROW_NUMBER() OVER (
                            PARTITION BY
                                object_id
                            ORDER BY start_date DESC
                        ) as rn
                    FROM inhuur_contracten
                    WHERE
                        end_date IS NULL
                        OR end_date >= DATE('now')
                )
            SELECT h.object_id, h.adres, h.plaats,

            -- Verhuur (Out)
            v.kale_huur AS verhuur_prijs,
            v.start_datum AS verhuur_start,
            v.eind_datum AS verhuur_eind,
            k.naam AS klant_naam,

            -- Inhuur (In)
            i.kale_huur AS inhuur_prijs,
            i.start_date AS inhuur_start,
            i.end_date AS inhuur_eind,
            l.naam AS leverancier_naam,

            -- Margin
            (
                IFNULL(v.kale_huur, 0) - IFNULL(i.kale_huur, 0)
            ) AS bruto_marge
            FROM
                huizen h
                LEFT JOIN latest_verhuur v ON h.object_id = v.object_id
                AND v.rn = 1
                LEFT JOIN "relaties" k ON v.klant_id = k.id
                LEFT JOIN latest_inhuur i ON h.object_id = i.object_id
                AND i.rn = 1
                LEFT JOIN leveranciers l ON i.leverancier_id = l.id
        """)

        
        conn.commit()
        logger.info("--- Migration Completed Successfully ---")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

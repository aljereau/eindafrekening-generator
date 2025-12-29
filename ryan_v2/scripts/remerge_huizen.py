
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")

def remerge_huizen():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        logger.info("--- Starting Remerge of huizen and huizen_archief ---")
        
        # 1. Check if huizen_archief exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='huizen_archief'")
        if not cursor.fetchone():
            logger.info("huizen_archief table does not exist. Migration might have already been done.")
            return

        # 2. Merge Data
        logger.info("Inserting archived properties into huizen...")
        cursor.execute("INSERT OR IGNORE INTO huizen SELECT * FROM huizen_archief")
        rows_merged = cursor.rowcount
        logger.info(f"Merged {rows_merged} rows from huizen_archief into huizen.")

        # 3. Drop Archive Table
        logger.info("Dropping huizen_archief table...")
        cursor.execute("DROP TABLE huizen_archief")

        # 4. Drop Union View
        logger.info("Dropping v_alle_huizen view...")
        cursor.execute("DROP VIEW IF EXISTS v_alle_huizen")

        conn.commit()
        logger.info("--- Remerge Completed Successfully ---")

    except Exception as e:
        conn.rollback()
        logger.error(f"Remerge failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    remerge_huizen()


import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")
BAK_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db.bak")

def repair_object_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        logger.info("--- Repairing NULL Object IDs from Backup ---")
        
        # Attach backup database
        cursor.execute(f"ATTACH DATABASE '{BAK_PATH}' AS backup")
        
        tables_to_repair = {
            'verhuur_contracten': 'huis_id_old',
            'inhuur_contracten': 'property_id_old',
            'huizen_status_log': 'property_id_old'
        }

        for table, old_id_col in tables_to_repair.items():
            logger.info(f"Repairing table: {table}")
            
            # Update missing object_ids from backup.huizen
            # Backup huizen has BOTH active and archived houses (it was the state before my split)
            sql = f"""
                UPDATE {table}
                SET object_id = (
                    SELECT b.object_id
                    FROM backup.huizen b
                    WHERE b.id = {table}.{old_id_col}
                )
                WHERE object_id IS NULL
            """
            cursor.execute(sql)
            rows_updated = cursor.rowcount
            logger.info(f"Fixed {rows_updated} rows in {table}.")

        conn.commit()
        logger.info("--- Repair Completed Successfully ---")

    except Exception as e:
        conn.rollback()
        logger.error(f"Repair failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    repair_object_ids()


import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")

def formalize_integrity():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        logger.info("--- Starting Formalization of Relational Integrity (Foreign Keys) ---")
        
        # Phase 0: Drop ALL Views
        logger.info("Dropping all views to avoid dependency errors...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
        views = [row[0] for row in cursor.fetchall()]
        for view in views:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
            
        tables_to_migrate = {
            'boekingen': 'huis_id_old',
            'verhuur_contracten': 'huis_id_old',
            'inhuur_contracten': 'property_id_old',
            'huizen_status_log': 'property_id_old'
        }

        for table, old_id_col in tables_to_migrate.items():
            logger.info(f"Formalizing table: {table}")
            
            # 1. Get current schema info
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            col_defs = []
            col_names = []
            
            for col in columns:
                name = col['name']
                type_ = col['type']
                notnull = "NOT NULL" if col['notnull'] else ""
                dflt = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] is not None else ""
                
                # Skip the old ID column
                if name == old_id_col:
                    continue
                
                # Special handling for object_id to ensure it's NOT NULL and properly typed
                if name == 'object_id':
                    col_defs.append(f"object_id TEXT NOT NULL")
                else:
                    # Special case for 'id' to preserve PRIMARY KEY AUTOINCREMENT
                    if name == 'id':
                        col_defs.append(f"id INTEGER PRIMARY KEY AUTOINCREMENT")
                    else:
                        col_defs.append(f"{name} {type_} {notnull} {dflt}")
                
                col_names.append(name)

            # Add Foreign Key constraint
            # Note: We also need to preserve other Foreign Keys (like klant_id -> relaties)
            # Let's see what other FKs exist
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            fk_list = cursor.fetchall()
            
            for fk in fk_list:
                # table: relaties, from: klant_id, to: id
                if fk['from'] == old_id_col:
                    continue # Skip the one we are replacing
                
                col_defs.append(f"FOREIGN KEY ({fk['from']}) REFERENCES \"{fk['table']}\"({fk['to']})")
            
            # Add the NEW Foreign Key for object_id
            col_defs.append(f"FOREIGN KEY (object_id) REFERENCES huizen(object_id)")

            create_sql = f"CREATE TABLE {table}_new ({', '.join(col_defs)})"
            
            logger.info(f"Creating {table}_new...")
            cursor.execute(f"DROP TABLE IF EXISTS {table}_new")
            cursor.execute(create_sql)
            
            # 2. Copy data
            cols_str = ", ".join(col_names)
            logger.info(f"Copying data to {table}_new...")
            cursor.execute(f"INSERT INTO {table}_new ({cols_str}) SELECT {cols_str} FROM {table}")
            
            # 3. Swap tables
            logger.info(f"Swapping {table} tables...")
            cursor.execute(f"DROP TABLE {table}")
            cursor.execute(f"ALTER TABLE {table}_new RENAME TO {table}")

        conn.commit()
        logger.info("--- Relational Integrity Formalized Successfully ---")

        # Phase 4: Rebuild Views
        logger.info("Rebuilding views...")
        import subprocess
        subprocess.run(["python3", "scripts/rebuild_views.py"], check=True)
        logger.info("Views rebuilt successfully.")

    except Exception as e:
        conn.rollback()
        logger.error(f"Formalization failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    formalize_integrity()

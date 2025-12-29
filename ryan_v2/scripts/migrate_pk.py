
import sqlite3
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")

def migrate_pk():
    if not DB_PATH.exists():
        logger.error(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        logger.info("--- Starting PK Migration (Switching to object_id as PK) ---")
        
        # Phase 0: Drop Views that depend on huizen
        logger.info("Dropping dependent views...")
        cursor.execute("DROP VIEW IF EXISTS v_alle_huizen")
        cursor.execute("DROP VIEW IF EXISTS view_latest_pricing")
        cursor.execute("DROP VIEW IF EXISTS view_house_profitability")

        cursor.execute("DROP VIEW IF EXISTS view_house_profitability")
        cursor.execute("DROP VIEW IF EXISTS v_planning_inputs")
        cursor.execute("DROP VIEW IF EXISTS v_status_check")
        cursor.execute("DROP VIEW IF EXISTS v_actieve_cycli")
        cursor.execute("DROP VIEW IF EXISTS view_operational_dashboard") 
        cursor.execute("DROP VIEW IF EXISTS v_house_costs") 
        cursor.execute("DROP VIEW IF EXISTS v_open_acties")
        cursor.execute("DROP VIEW IF EXISTS v_schoonmaak_variance")
        cursor.execute("DROP VIEW IF EXISTS view_client_scorecard")
        cursor.execute("DROP VIEW IF EXISTS version_history")
        cursor.execute("DROP VIEW IF EXISTS latest_eindafrekeningen") 

        # Cleanup potential leftovers from failed runs
        cursor.execute("DROP TABLE IF EXISTS huizen_new")
        cursor.execute("DROP TABLE IF EXISTS huizen_archief_new")

        # --- Table: huizen ---
        logger.info("Migrating Table: huizen")
        
        # 1. Get current columns but exclude 'id'
        cursor.execute("PRAGMA table_info(huizen)")
        columns_info = cursor.fetchall()
        
        # Filter out 'id' and build column definitions
        # We need to construct the CREATE TABLE statement manually
        # Standardize on object_id as TEXT PRIMARY KEY
        
        col_defs = []
        col_names = []
        
        for col in columns_info:
            name = col['name']
            type_ = col['type']
            notnull = "NOT NULL" if col['notnull'] else ""
            dflt = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] is not None else ""
            
            if name == 'id':
                continue # SKIP the integer ID
            
            if name == 'object_id':
                col_defs.append(f"object_id TEXT PRIMARY KEY")
            else:
                col_defs.append(f"{name} {type_} {notnull} {dflt}")
            
            col_names.append(name)
            
        create_sql = f"CREATE TABLE huizen_new ({', '.join(col_defs)})"
        
        logger.info(f"Creating huizen_new...")
        cursor.execute(create_sql)
        
        # 2. Copy Data
        cols_str = ", ".join(col_names)
        logger.info(f"Copying data to huizen_new...")
        cursor.execute(f"INSERT INTO huizen_new ({cols_str}) SELECT {cols_str} FROM huizen")
        
        # 3. Drop Old and Rename
        logger.info("Swapping huizen tables...")
        cursor.execute("DROP TABLE huizen")
        cursor.execute("ALTER TABLE huizen_new RENAME TO huizen")


        # --- Table: huizen_archief ---
        logger.info("Migrating Table: huizen_archief")
        
        # Similar logic for archive
        cursor.execute("PRAGMA table_info(huizen_archief)")
        columns_info = cursor.fetchall()
        
        col_defs = []
        col_names = []
        
        for col in columns_info:
            name = col['name']
            type_ = col['type']
            notnull = "NOT NULL" if col['notnull'] else ""
            dflt = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] is not None else ""
            
            if name == 'id':
                continue 
            
            if name == 'object_id':
                col_defs.append(f"object_id TEXT PRIMARY KEY")
            else:
                col_defs.append(f"{name} {type_} {notnull} {dflt}")
            
            col_names.append(name)
            
        create_sql = f"CREATE TABLE huizen_archief_new ({', '.join(col_defs)})"
        
        logger.info(f"Creating huizen_archief_new...")
        cursor.execute(create_sql)
        
        # Copy Data
        cols_str = ", ".join(col_names)
        logger.info(f"Copying data to huizen_archief_new...")
        cursor.execute(f"INSERT INTO huizen_archief_new ({cols_str}) SELECT {cols_str} FROM huizen_archief")
        
        # Drop and Rename
        logger.info("Swapping huizen_archief tables...")
        cursor.execute("DROP TABLE huizen_archief")
        cursor.execute("ALTER TABLE huizen_archief_new RENAME TO huizen_archief")


        # --- Restore Views ---
        logger.info("Restoring Views...")
        
        cursor.execute("""
            CREATE VIEW v_alle_huizen AS
            SELECT *, 'active' as source FROM huizen
            UNION ALL
            SELECT *, 'archive' as source FROM huizen_archief
        """)
        
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

        cursor.execute("""
            CREATE VIEW view_house_profitability AS
            SELECT h.adres, h.plaats, COUNT(DISTINCT b.id) as total_bookings,

            -- Income
            SUM(
                IFNULL(vc.kale_huur, 0) * (
                    JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
                ) / 30.0
            ) as est_total_revenue,

            -- Costs
            SUM(
                IFNULL(ic.kale_huur, 0) * (
                    JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
                ) / 30.0
            ) as est_total_cost,

            -- Damages
            (
                SELECT SUM(estimated_cost)
                FROM damages d
                    JOIN boekingen b2 ON d.booking_id = b2.id
                WHERE
                    b2.object_id = h.object_id
            ) as total_damages_cost,

            -- Margin
            (
                SUM(
                    IFNULL(vc.kale_huur, 0) * (
                        JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
                    ) / 30.0
                ) - SUM(
                    IFNULL(ic.kale_huur, 0) * (
                        JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
                    ) / 30.0
                )
            ) as est_gross_margin
            FROM
                huizen h
                JOIN boekingen b ON h.object_id = b.object_id
                
                -- Update joins to use object_id
                LEFT JOIN verhuur_contracten vc ON h.object_id = vc.object_id
                LEFT JOIN inhuur_contracten ic ON h.object_id = ic.object_id
            GROUP BY
                h.object_id
        """)

        conn.commit()

        # Re-create Operational Views
        logger.info("Restoring Operational Views...")
        
        cursor.execute("""
            CREATE VIEW v_actieve_cycli AS
            SELECT
              c.cyclus_id,
              c.object_id,
              h.adres,
              h.plaats,
              c.klant_type,
              c.bestemming,
              c.status,
              c.einddatum_huurder,
              c.startdatum_nieuwe_huurder,
              c.interne_opmerking,
              c.aangemaakt_op,
              c.laatst_bijgewerkt_op
            FROM woning_cycli c
            JOIN huizen h ON h.object_id = c.object_id
            WHERE c.is_actief = 1
        """)

        cursor.execute("""
            CREATE VIEW v_status_check AS
            SELECT
              c.cyclus_id,
              c.object_id,
              CASE
                WHEN c.status = 'NIET_GESTART' THEN 'OK'
                ELSE NULL
              END AS check_start,
              CASE
                WHEN c.status = 'VOORINSPECTIE_GEPLAND' THEN
                  CASE
                    WHEN EXISTS (SELECT 1 FROM woning_acties a
                                 WHERE a.cyclus_id = c.cyclus_id
                                   AND a.actie_type = 'VOORINSPECTIE'
                                   AND a.gepland_op IS NOT NULL)
                    THEN 'OK' ELSE 'BLOCKER'
                  END
                ELSE NULL
              END AS check_voorinspectie_gepland,
              'OK' AS status_severity
            FROM woning_cycli c
            INNER JOIN huizen h ON c.object_id = h.object_id
            WHERE c.is_actief = 1
        """)

        # Add v_planning_inputs (Simplified for migration safety)
        cursor.execute("""
            CREATE VIEW v_planning_inputs AS
            SELECT
              c.cyclus_id,
              c.object_id,
              h.adres,
              h.plaats,
              h.woning_type,
              h.oppervlakte,
              c.status,
              c.klant_type,
              c.einddatum_huurder,
              c.startdatum_nieuwe_huurder
            FROM woning_cycli c
            INNER JOIN huizen h ON c.object_id = h.object_id
            WHERE c.is_actief = 1
        """)

        conn.commit()
        logger.info("--- PK Migration Completed Successfully ---")


    except Exception as e:
        conn.rollback()
        logger.error(f"Migration Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_pk()

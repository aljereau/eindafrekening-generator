
import sqlite3
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = Path("/Users/aljereaumarten/Library/CloudStorage/OneDrive-SharedLibraries-RyanRentB.V/RyanRent - General/01_RyanRent&Co/Aljereau/Eindafrekening Generator/database/ryanrent_mock.db")

def rebuild_views():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        logger.info("--- Rebuilding Dropped Views ---")
        
        # 1. latest_eindafrekeningen (no huizen dependency)
        logger.info("Creating latest_eindafrekeningen...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS latest_eindafrekeningen AS
            SELECT e.*
            FROM eindafrekeningen e
            INNER JOIN (
                SELECT client_name, checkin_date, checkout_date, MAX(version) as max_version
                FROM eindafrekeningen
                GROUP BY client_name, checkin_date, checkout_date
            ) latest
            ON e.client_name = latest.client_name
               AND e.checkin_date = latest.checkin_date
               AND e.checkout_date = latest.checkout_date
               AND e.version = latest.max_version
        """)

        # 2. version_history (no huizen dependency)
        logger.info("Creating version_history...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS version_history AS
            SELECT
                client_name,
                checkin_date,
                checkout_date,
                COUNT(*) as version_count,
                MIN(created_at) as first_created,
                MAX(created_at) as last_updated,
                MAX(version) as current_version
            FROM eindafrekeningen
            GROUP BY client_name, checkin_date, checkout_date
            HAVING COUNT(*) > 1
            ORDER BY last_updated DESC
        """)

        # 3. view_client_scorecard (UPDATED: uses object_id now)
        logger.info("Creating view_client_scorecard...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS view_client_scorecard AS
            SELECT
                k.naam as client_name,
                k.type as client_type,
                COUNT(b.id) as total_bookings,

            -- Financials
            SUM(
                IFNULL(vc.kale_huur, 0) * (
                    JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
                ) / 30.0
            ) as total_revenue_generated,

            -- Risk/Issues
            (
                SELECT COUNT(*)
                FROM damages d
                    JOIN boekingen b2 ON d.booking_id = b2.id
                WHERE
                    b2.klant_id = k.id
            ) as damage_incidents,
            (
                SELECT SUM(estimated_cost)
                FROM damages d
                    JOIN boekingen b2 ON d.booking_id = b2.id
                WHERE
                    b2.klant_id = k.id
            ) as total_damage_cost,

            -- Average Stay
            AVG(
                JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
            ) as avg_stay_days
            FROM
                "relaties" k
                JOIN boekingen b ON k.id = b.klant_id
                LEFT JOIN verhuur_contracten vc ON b.object_id = vc.object_id
                AND b.klant_id = vc.klant_id
            GROUP BY
                k.id
            ORDER BY total_revenue_generated DESC
        """)

        # 4. v_open_acties (already uses object_id)
        logger.info("Creating v_open_acties...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_open_acties AS
            SELECT
              a.actie_id,
              a.cyclus_id,
              c.object_id,
              h.adres,
              h.plaats,
              a.actie_type,
              a.gepland_op,
              a.uitgevoerd_door,
              c.status AS cyclus_status,
              c.startdatum_nieuwe_huurder AS deadline,
              CASE
                WHEN c.startdatum_nieuwe_huurder IS NULL THEN NULL
                ELSE julianday(c.startdatum_nieuwe_huurder) - julianday('now')
              END AS deadline_dagen,
              CASE
                WHEN a.gepland_op IS NULL THEN NULL
                ELSE julianday(a.gepland_op) - julianday('now')
              END AS planning_dagen,
              a.verwachte_schoonmaak_uren,
              a.opmerking,
              c.interne_opmerking AS cyclus_opmerking,
              a.aangemaakt_op
            FROM woning_acties a
            INNER JOIN woning_cycli c ON a.cyclus_id = c.cyclus_id
            INNER JOIN huizen h ON c.object_id = h.object_id
            WHERE c.is_actief = 1
              AND a.gepland_op IS NOT NULL
              AND a.uitgevoerd_op IS NULL
            ORDER BY deadline_dagen ASC NULLS LAST, planning_dagen ASC NULLS LAST
        """)

        # 5. v_schoonmaak_variance (already uses object_id)
        logger.info("Creating v_schoonmaak_variance...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_schoonmaak_variance AS
            SELECT
              a.actie_id,
              a.cyclus_id,
              c.object_id,
              h.adres,
              h.woning_type,
              h.oppervlakte,
              h.aantal_sk AS slaapkamers,
              a.verwachte_schoonmaak_uren,
              a.werkelijke_schoonmaak_uren,
              (a.werkelijke_schoonmaak_uren - a.verwachte_schoonmaak_uren) AS uren_verschil,
              CASE
                WHEN a.verwachte_schoonmaak_uren > 0 THEN
                  ROUND(((a.werkelijke_schoonmaak_uren - a.verwachte_schoonmaak_uren) /
                         a.verwachte_schoonmaak_uren) * 100, 1)
                ELSE NULL
              END AS percentage_verschil,
              CASE
                WHEN a.werkelijke_schoonmaak_uren IS NULL THEN 'GEEN_DATA'
                WHEN a.verwachte_schoonmaak_uren IS NULL THEN 'GEEN_SCHATTING'
                WHEN a.werkelijke_schoonmaak_uren <= a.verwachte_schoonmaak_uren * 0.9 THEN 'ONDER_SCHATTING'
                WHEN a.werkelijke_schoonmaak_uren <= a.verwachte_schoonmaak_uren * 1.1 THEN 'BINNEN_MARGE'
                ELSE 'BOVEN_SCHATTING'
              END AS variance_categorie,
              a.uitgevoerd_door,
              a.uitgevoerd_op,
              a.issues_gevonden,
              a.opmerking
            FROM woning_acties a
            INNER JOIN woning_cycli c ON a.cyclus_id = c.cyclus_id
            INNER JOIN huizen h ON c.object_id = h.object_id
            WHERE a.actie_type = 'SCHOONMAAK'
              AND a.uitgevoerd_op IS NOT NULL
              AND (a.verwachte_schoonmaak_uren IS NOT NULL OR a.werkelijke_schoonmaak_uren IS NOT NULL)
            ORDER BY a.uitgevoerd_op DESC
        """)

        # 6. view_latest_pricing
        logger.info("Creating view_latest_pricing...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS view_latest_pricing AS
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
            v.kale_huur AS verhuur_prijs,
            v.start_datum AS verhuur_start,
            v.eind_datum AS verhuur_eind,
            k.naam AS klant_naam,
            i.kale_huur AS inhuur_prijs,
            i.start_date AS inhuur_start,
            i.end_date AS inhuur_eind,
            l.naam AS leverancier_naam,
            (IFNULL(v.kale_huur, 0) - IFNULL(i.kale_huur, 0)) AS bruto_marge
            FROM
                huizen h
                LEFT JOIN latest_verhuur v ON h.object_id = v.object_id AND v.rn = 1
                LEFT JOIN "relaties" k ON v.klant_id = k.id
                LEFT JOIN latest_inhuur i ON h.object_id = i.object_id AND i.rn = 1
                LEFT JOIN leveranciers l ON i.leverancier_id = l.id
        """)

        # 7. view_house_profitability
        logger.info("Creating view_house_profitability...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS view_house_profitability AS
            SELECT h.adres, h.plaats, COUNT(DISTINCT b.id) as total_bookings,
            SUM(IFNULL(vc.kale_huur, 0) * (JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)) / 30.0) as est_total_revenue,
            SUM(IFNULL(ic.kale_huur, 0) * (JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)) / 30.0) as est_total_cost,
            (SELECT SUM(estimated_cost) FROM damages d JOIN boekingen b2 ON d.booking_id = b2.id WHERE b2.object_id = h.object_id) as total_damages_cost,
            (SUM(IFNULL(vc.kale_huur, 0) * (JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)) / 30.0) - SUM(IFNULL(ic.kale_huur, 0) * (JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)) / 30.0)) as est_gross_margin
            FROM huizen h
            JOIN boekingen b ON h.object_id = b.object_id
            LEFT JOIN verhuur_contracten vc ON h.object_id = vc.object_id
            LEFT JOIN inhuur_contracten ic ON h.object_id = ic.object_id
            GROUP BY h.object_id
        """)

        # 8. Operational Views (v_actieve_cycli, v_status_check, v_planning_inputs)
        logger.info("Creating Operational Views...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_actieve_cycli AS
            SELECT c.*, h.adres, h.plaats FROM woning_cycli c JOIN huizen h ON h.object_id = c.object_id WHERE c.is_actief = 1
        """)
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_status_check AS
            SELECT c.*, CASE WHEN c.status = 'NIET_GESTART' THEN 'OK' ELSE NULL END AS check_start FROM woning_cycli c JOIN huizen h ON c.object_id = h.object_id WHERE c.is_actief = 1
        """)
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_planning_inputs AS
            SELECT c.*, h.adres, h.plaats, h.woning_type FROM woning_cycli c JOIN huizen h ON c.object_id = h.object_id WHERE c.is_actief = 1
        """)

        # 9. Unified View (compatibility)
        logger.info("Creating compatibility view v_alle_huizen...")
        cursor.execute("CREATE VIEW IF NOT EXISTS v_alle_huizen AS SELECT *, status as source FROM huizen")


        conn.commit()
        logger.info("--- All Views Rebuilt Successfully ---")

    except Exception as e:
        conn.rollback()
        logger.error(f"Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    rebuild_views()

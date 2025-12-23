-- ============================================================================
-- RYAN V2: Rename huis_id → object_id for Consistency
-- ============================================================================
-- Purpose: Standardize all property references to use "object_id"
-- Date: 2025-12-22
-- ============================================================================

-- =============================================================================
-- Step 1: Rename column in woning_cycli
-- =============================================================================
-- SQLite requires recreating the table to rename columns

BEGIN TRANSACTION;

-- Create new table with correct column name
CREATE TABLE woning_cycli_new (
  -- Primary Key
  cyclus_id TEXT PRIMARY KEY,

  -- Foreign Keys (renamed: huis_id → object_id)
  object_id TEXT NOT NULL,

  -- Status Management
  is_actief INTEGER NOT NULL DEFAULT 1,

  -- Client & Destination
  klant_type TEXT NOT NULL
    CHECK (klant_type IN ('TRADIRO', 'EXTERN', 'EIGENAAR')),
  bestemming TEXT NOT NULL
    CHECK (bestemming IN ('OPNIEUW_VERHUREN', 'TERUG_NAAR_EIGENAAR')),

  -- Lifecycle Status (11 states)
  status TEXT NOT NULL CHECK (status IN (
    'NIET_GESTART',
    'VOORINSPECTIE_GEPLAND',
    'VOORINSPECTIE_UITGEVOERD',
    'UITCHECK_GEPLAND',
    'UITCHECK_UITGEVOERD',
    'SCHOONMAAK_NODIG',
    'KLAAR_VOOR_INCHECK',
    'INCHECK_GEPLAND',
    'INCHECK_UITGEVOERD',
    'TERUG_NAAR_EIGENAAR',
    'AFGEROND'
  )),

  -- Timeline
  einddatum_huurder TEXT,
  startdatum_nieuwe_huurder TEXT,

  -- Notes
  interne_opmerking TEXT,

  -- Timestamps
  aangemaakt_op TEXT NOT NULL DEFAULT (datetime('now')),
  laatst_bijgewerkt_op TEXT NOT NULL DEFAULT (datetime('now')),

  -- Constraints (updated: huis_id → object_id)
  FOREIGN KEY (object_id) REFERENCES huizen(object_id)
);

-- Copy data from old table
INSERT INTO woning_cycli_new (
  cyclus_id, object_id, is_actief, klant_type, bestemming, status,
  einddatum_huurder, startdatum_nieuwe_huurder, interne_opmerking,
  aangemaakt_op, laatst_bijgewerkt_op
)
SELECT
  cyclus_id, huis_id, is_actief, klant_type, bestemming, status,
  einddatum_huurder, startdatum_nieuwe_huurder, interne_opmerking,
  aangemaakt_op, laatst_bijgewerkt_op
FROM woning_cycli;

-- Drop old table
DROP TABLE woning_cycli;

-- Rename new table
ALTER TABLE woning_cycli_new RENAME TO woning_cycli;

-- Recreate indexes (updated: huis_id → object_id)
CREATE UNIQUE INDEX idx_woning_cycli_active_unique
  ON woning_cycli(object_id)
  WHERE is_actief = 1;

CREATE INDEX idx_woning_cycli_object_id
  ON woning_cycli(object_id);

CREATE INDEX idx_woning_cycli_status
  ON woning_cycli(status)
  WHERE is_actief = 1;

CREATE INDEX idx_woning_cycli_deadline
  ON woning_cycli(startdatum_nieuwe_huurder)
  WHERE is_actief = 1 AND startdatum_nieuwe_huurder IS NOT NULL;

-- Recreate trigger
CREATE TRIGGER trg_woning_cycli_updated
  AFTER UPDATE ON woning_cycli
  FOR EACH ROW
  WHEN OLD.laatst_bijgewerkt_op = NEW.laatst_bijgewerkt_op
BEGIN
  UPDATE woning_cycli
  SET laatst_bijgewerkt_op = datetime('now')
  WHERE cyclus_id = NEW.cyclus_id;
END;

COMMIT;

-- =============================================================================
-- Step 2: Recreate views with updated column name
-- =============================================================================

-- Drop old views
DROP VIEW IF EXISTS v_actieve_cycli;
DROP VIEW IF EXISTS v_open_acties;
DROP VIEW IF EXISTS v_schoonmaak_variance;
DROP VIEW IF EXISTS v_status_check;
DROP VIEW IF EXISTS v_planning_inputs;

-- Recreate v_actieve_cycli (updated: huis_id → object_id)
CREATE VIEW v_actieve_cycli AS
SELECT
  c.cyclus_id,
  c.object_id,
  h.adres,
  h.postcode,
  h.plaats,
  h.woning_type,
  h.aantal_sk AS slaapkamers,
  h.aantal_pers AS capaciteit,
  c.status,
  c.klant_type,
  c.bestemming,
  c.einddatum_huurder,
  c.startdatum_nieuwe_huurder,
  CASE
    WHEN c.startdatum_nieuwe_huurder IS NULL THEN NULL
    ELSE julianday(c.startdatum_nieuwe_huurder) - julianday('now')
  END AS deadline_dagen,
  (SELECT COUNT(*)
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
     AND a.gepland_op IS NOT NULL
     AND a.uitgevoerd_op IS NULL
  ) AS open_acties_count,
  (SELECT COUNT(*)
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
  ) AS totaal_acties,
  c.interne_opmerking,
  c.aangemaakt_op,
  c.laatst_bijgewerkt_op
FROM woning_cycli c
INNER JOIN huizen h ON c.object_id = h.object_id
WHERE c.is_actief = 1
ORDER BY deadline_dagen ASC NULLS LAST, c.laatst_bijgewerkt_op DESC;

-- Recreate v_open_acties (updated: huis_id → object_id)
CREATE VIEW v_open_acties AS
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
ORDER BY deadline_dagen ASC NULLS LAST, planning_dagen ASC NULLS LAST;

-- Recreate v_schoonmaak_variance (updated: huis_id → object_id)
CREATE VIEW v_schoonmaak_variance AS
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
ORDER BY a.uitgevoerd_op DESC;

-- Recreate v_status_check (updated: huis_id → object_id)
CREATE VIEW v_status_check AS
SELECT
  c.cyclus_id,
  c.object_id,
  h.adres,
  c.status,
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
  CASE
    WHEN c.status = 'UITCHECK_UITGEVOERD' THEN
      CASE
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'UITCHECK'
                       AND a.uitgevoerd_op IS NOT NULL
                       AND a.verwachte_schoonmaak_uren IS NOT NULL)
        THEN 'OK' ELSE 'BLOCKER'
      END
    ELSE NULL
  END AS check_uitcheck_uitgevoerd,
  CASE
    WHEN c.status = 'SCHOONMAAK_NODIG' THEN
      CASE
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'UITCHECK'
                       AND a.verwachte_schoonmaak_uren > 0)
        THEN 'OK' ELSE 'BLOCKER'
      END
    ELSE NULL
  END AS check_schoonmaak_nodig,
  CASE
    WHEN c.status = 'KLAAR_VOOR_INCHECK' THEN
      CASE
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'UITCHECK'
                       AND a.verwachte_schoonmaak_uren = 0)
        THEN 'OK'
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'SCHOONMAAK'
                       AND a.werkelijke_schoonmaak_uren IS NOT NULL)
        THEN 'OK'
        ELSE 'BLOCKER'
      END
    ELSE NULL
  END AS check_klaar_voor_incheck,
  CASE
    WHEN c.status = 'INCHECK_UITGEVOERD' THEN
      CASE
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'INCHECK'
                       AND a.uitgevoerd_op IS NOT NULL)
        THEN 'OK' ELSE 'BLOCKER'
      END
    ELSE NULL
  END AS check_incheck_uitgevoerd,
  CASE
    WHEN c.status = 'TERUG_NAAR_EIGENAAR' THEN
      CASE
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'OVERDRACHT_EIGENAAR'
                       AND a.uitgevoerd_op IS NOT NULL)
        THEN 'OK' ELSE 'BLOCKER'
      END
    ELSE NULL
  END AS check_terug_naar_eigenaar,
  CASE
    WHEN c.status = 'AFGEROND' THEN
      CASE
        WHEN c.bestemming = 'OPNIEUW_VERHUREN' THEN
          CASE
            WHEN EXISTS (SELECT 1 FROM woning_acties a
                         WHERE a.cyclus_id = c.cyclus_id
                           AND a.actie_type = 'INCHECK'
                           AND a.uitgevoerd_op IS NOT NULL)
            THEN 'OK' ELSE 'BLOCKER'
          END
        WHEN c.bestemming = 'TERUG_NAAR_EIGENAAR' THEN
          CASE
            WHEN EXISTS (SELECT 1 FROM woning_acties a
                         WHERE a.cyclus_id = c.cyclus_id
                           AND a.actie_type = 'OVERDRACHT_EIGENAAR'
                           AND a.uitgevoerd_op IS NOT NULL)
            THEN 'OK' ELSE 'BLOCKER'
          END
        ELSE 'WARNING'
      END
    ELSE NULL
  END AS check_afgerond,
  CASE
    WHEN (CASE WHEN c.status = 'VOORINSPECTIE_GEPLAND' AND NOT EXISTS (SELECT 1 FROM woning_acties a WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'VOORINSPECTIE' AND a.gepland_op IS NOT NULL) THEN 1 ELSE 0 END +
          CASE WHEN c.status = 'UITCHECK_UITGEVOERD' AND NOT EXISTS (SELECT 1 FROM woning_acties a WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK' AND a.uitgevoerd_op IS NOT NULL AND a.verwachte_schoonmaak_uren IS NOT NULL) THEN 1 ELSE 0 END +
          CASE WHEN c.status = 'SCHOONMAAK_NODIG' AND NOT EXISTS (SELECT 1 FROM woning_acties a WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK' AND a.verwachte_schoonmaak_uren > 0) THEN 1 ELSE 0 END +
          CASE WHEN c.status = 'KLAAR_VOOR_INCHECK' AND NOT (
            EXISTS (SELECT 1 FROM woning_acties a WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK' AND a.verwachte_schoonmaak_uren = 0) OR
            EXISTS (SELECT 1 FROM woning_acties a WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'SCHOONMAAK' AND a.werkelijke_schoonmaak_uren IS NOT NULL)
          ) THEN 1 ELSE 0 END +
          CASE WHEN c.status = 'INCHECK_UITGEVOERD' AND NOT EXISTS (SELECT 1 FROM woning_acties a WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'INCHECK' AND a.uitgevoerd_op IS NOT NULL) THEN 1 ELSE 0 END +
          CASE WHEN c.status = 'TERUG_NAAR_EIGENAAR' AND NOT EXISTS (SELECT 1 FROM woning_acties a WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'OVERDRACHT_EIGENAAR' AND a.uitgevoerd_op IS NOT NULL) THEN 1 ELSE 0 END
         ) > 0 THEN 'BLOCKER'
    ELSE 'OK'
  END AS status_severity,
  c.bestemming,
  c.startdatum_nieuwe_huurder,
  c.laatst_bijgewerkt_op
FROM woning_cycli c
INNER JOIN huizen h ON c.object_id = h.object_id
WHERE c.is_actief = 1
ORDER BY
  CASE status_severity
    WHEN 'BLOCKER' THEN 1
    WHEN 'WARNING' THEN 2
    WHEN 'OK' THEN 3
    ELSE 4
  END,
  c.startdatum_nieuwe_huurder ASC NULLS LAST;

-- Recreate v_planning_inputs (updated: huis_id → object_id)
CREATE VIEW v_planning_inputs AS
SELECT
  c.cyclus_id,
  c.object_id,
  h.adres,
  h.plaats,
  h.woning_type,
  h.oppervlakte,
  h.aantal_sk AS slaapkamers,
  h.aantal_pers AS capaciteit,
  c.status,
  c.klant_type,
  c.bestemming,
  c.einddatum_huurder,
  c.startdatum_nieuwe_huurder,
  CASE
    WHEN c.startdatum_nieuwe_huurder IS NULL THEN NULL
    ELSE julianday(c.startdatum_nieuwe_huurder) - julianday('now')
  END AS deadline_dagen,
  CASE
    WHEN c.startdatum_nieuwe_huurder IS NULL THEN 'ONBEKEND'
    WHEN julianday(c.startdatum_nieuwe_huurder) - julianday('now') <= 2 THEN 'CRITICAL'
    WHEN julianday(c.startdatum_nieuwe_huurder) - julianday('now') <= 5 THEN 'HIGH'
    WHEN julianday(c.startdatum_nieuwe_huurder) - julianday('now') <= 10 THEN 'NORMAL'
    ELSE 'LOW'
  END AS urgency_band,
  (SELECT a.verwachte_schoonmaak_uren
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
     AND a.actie_type = 'UITCHECK'
     AND a.verwachte_schoonmaak_uren IS NOT NULL
   ORDER BY a.uitgevoerd_op DESC, a.aangemaakt_op DESC
   LIMIT 1
  ) AS verwachte_schoonmaak_uren,
  (SELECT COUNT(*)
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
     AND a.gepland_op IS NOT NULL
     AND a.uitgevoerd_op IS NULL
  ) AS open_acties_count,
  (SELECT status_severity
   FROM v_status_check sc
   WHERE sc.cyclus_id = c.cyclus_id
  ) AS status_severity,
  (SELECT a.uitgevoerd_door
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
     AND a.uitgevoerd_door IS NOT NULL
   ORDER BY a.uitgevoerd_op DESC, a.aangemaakt_op DESC
   LIMIT 1
  ) AS laatst_toegewezen_team,
  CASE c.status
    WHEN 'NIET_GESTART' THEN 'VOORINSPECTIE_PLANNEN'
    WHEN 'VOORINSPECTIE_GEPLAND' THEN 'VOORINSPECTIE_UITVOEREN'
    WHEN 'VOORINSPECTIE_UITGEVOERD' THEN 'UITCHECK_PLANNEN'
    WHEN 'UITCHECK_GEPLAND' THEN 'UITCHECK_UITVOEREN'
    WHEN 'UITCHECK_UITGEVOERD' THEN
      CASE
        WHEN (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
              WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
              ORDER BY a.uitgevoerd_op DESC LIMIT 1) > 0
        THEN 'SCHOONMAAK_PLANNEN'
        ELSE 'INCHECK_PLANNEN'
      END
    WHEN 'SCHOONMAAK_NODIG' THEN 'SCHOONMAAK_PLANNEN'
    WHEN 'KLAAR_VOOR_INCHECK' THEN 'INCHECK_PLANNEN'
    WHEN 'INCHECK_GEPLAND' THEN 'INCHECK_UITVOEREN'
    WHEN 'INCHECK_UITGEVOERD' THEN
      CASE c.bestemming
        WHEN 'OPNIEUW_VERHUREN' THEN 'CYCLUS_AFRONDEN'
        WHEN 'TERUG_NAAR_EIGENAAR' THEN 'EIGENAAR_OVERDRACHT_PLANNEN'
        ELSE 'ONBEKEND'
      END
    WHEN 'TERUG_NAAR_EIGENAAR' THEN 'EIGENAAR_OVERDRACHT_UITVOEREN'
    WHEN 'AFGEROND' THEN 'GEEN_ACTIE'
    ELSE 'ONBEKEND'
  END AS volgende_actie,
  c.interne_opmerking,
  c.aangemaakt_op,
  c.laatst_bijgewerkt_op
FROM woning_cycli c
INNER JOIN huizen h ON c.object_id = h.object_id
WHERE c.is_actief = 1
ORDER BY
  CASE
    WHEN julianday(c.startdatum_nieuwe_huurder) - julianday('now') <= 2 THEN 1
    ELSE 2
  END,
  (SELECT CASE WHEN status_severity = 'BLOCKER' THEN 1 ELSE 2 END
   FROM v_status_check sc WHERE sc.cyclus_id = c.cyclus_id),
  deadline_dagen ASC NULLS LAST;

-- =============================================================================
-- Completion
-- =============================================================================

SELECT
  'Column renamed: huis_id → object_id in woning_cycli' AS status,
  'All views updated with new column name' AS views_status,
  datetime('now') AS timestamp;

-- ============================================================================
-- RYAN V2: In-Uit-Check AI Planning Views
-- ============================================================================
-- Purpose: SQL views for status validation, AI planning, and operational dashboards
-- Author: RyanRent Development Team
-- Date: 2025-12-22
-- Database: ryanrent_mock.db
-- Dependencies: schema_inuitcheck.sql must be applied first
-- ============================================================================

-- =============================================================================
-- VIEW 1: v_actieve_cycli (Active Cycles Dashboard)
-- =============================================================================
-- Purpose: All active cycles with property details for operational overview
-- Use: Dashboard display, filtering, quick status checks
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_actieve_cycli AS
SELECT
  -- Cycle identifiers
  c.cyclus_id,
  c.object_id,

  -- Property details (from huizen table)
  h.adres,
  h.postcode,
  h.plaats,
  h.woning_type,
  h.aantal_sk AS slaapkamers,
  h.aantal_pers AS capaciteit,

  -- Cycle status
  c.status,
  c.klant_type,
  c.bestemming,

  -- Timeline
  c.einddatum_huurder,
  c.startdatum_nieuwe_huurder,

  -- Deadline calculation
  CASE
    WHEN c.startdatum_nieuwe_huurder IS NULL THEN NULL
    ELSE julianday(c.startdatum_nieuwe_huurder) - julianday('now')
  END AS deadline_dagen,

  -- Open actions count
  (SELECT COUNT(*)
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
     AND a.gepland_op IS NOT NULL
     AND a.uitgevoerd_op IS NULL
  ) AS open_acties_count,

  -- Total actions count
  (SELECT COUNT(*)
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
  ) AS totaal_acties,

  -- Notes
  c.interne_opmerking,

  -- Timestamps
  c.aangemaakt_op,
  c.laatst_bijgewerkt_op

FROM woning_cycli c
INNER JOIN huizen h ON c.object_id = h.object_id
WHERE c.is_actief = 1
ORDER BY deadline_dagen ASC NULLS LAST, c.laatst_bijgewerkt_op DESC;

-- =============================================================================
-- VIEW 2: v_open_acties (Open Actions)
-- =============================================================================
-- Purpose: All actions that are planned but not yet executed
-- Use: Task management, team assignment, progress tracking
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_open_acties AS
SELECT
  -- Action identifiers
  a.actie_id,
  a.cyclus_id,
  c.object_id,

  -- Property details
  h.adres,
  h.plaats,

  -- Action details
  a.actie_type,
  a.gepland_op,
  a.uitgevoerd_door,

  -- Cycle context
  c.status AS cyclus_status,
  c.startdatum_nieuwe_huurder AS deadline,

  -- Deadline pressure (days until property needs to be ready)
  CASE
    WHEN c.startdatum_nieuwe_huurder IS NULL THEN NULL
    ELSE julianday(c.startdatum_nieuwe_huurder) - julianday('now')
  END AS deadline_dagen,

  -- Planning urgency (days until planned execution)
  CASE
    WHEN a.gepland_op IS NULL THEN NULL
    ELSE julianday(a.gepland_op) - julianday('now')
  END AS planning_dagen,

  -- Expected effort
  a.verwachte_schoonmaak_uren,

  -- Notes
  a.opmerking,
  c.interne_opmerking AS cyclus_opmerking,

  -- Timestamps
  a.aangemaakt_op

FROM woning_acties a
INNER JOIN woning_cycli c ON a.cyclus_id = c.cyclus_id
INNER JOIN huizen h ON c.object_id = h.object_id
WHERE c.is_actief = 1
  AND a.gepland_op IS NOT NULL
  AND a.uitgevoerd_op IS NULL
ORDER BY deadline_dagen ASC NULLS LAST, planning_dagen ASC NULLS LAST;

-- =============================================================================
-- VIEW 3: v_schoonmaak_variance (Cleaning Hours Variance)
-- =============================================================================
-- Purpose: Compare expected vs. actual cleaning hours for learning and improvement
-- Use: Estimation refinement, team performance analysis, budget tracking
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_schoonmaak_variance AS
SELECT
  -- Identifiers
  a.actie_id,
  a.cyclus_id,
  c.object_id,

  -- Property details
  h.adres,
  h.woning_type,
  h.oppervlakte,
  h.aantal_sk AS slaapkamers,

  -- Cleaning hours
  a.verwachte_schoonmaak_uren,
  a.werkelijke_schoonmaak_uren,

  -- Variance calculations
  (a.werkelijke_schoonmaak_uren - a.verwachte_schoonmaak_uren) AS uren_verschil,
  CASE
    WHEN a.verwachte_schoonmaak_uren > 0 THEN
      ROUND(((a.werkelijke_schoonmaak_uren - a.verwachte_schoonmaak_uren) /
             a.verwachte_schoonmaak_uren) * 100, 1)
    ELSE NULL
  END AS percentage_verschil,

  -- Variance category
  CASE
    WHEN a.werkelijke_schoonmaak_uren IS NULL THEN 'GEEN_DATA'
    WHEN a.verwachte_schoonmaak_uren IS NULL THEN 'GEEN_SCHATTING'
    WHEN a.werkelijke_schoonmaak_uren <= a.verwachte_schoonmaak_uren * 0.9 THEN 'ONDER_SCHATTING'
    WHEN a.werkelijke_schoonmaak_uren <= a.verwachte_schoonmaak_uren * 1.1 THEN 'BINNEN_MARGE'
    ELSE 'BOVEN_SCHATTING'
  END AS variance_categorie,

  -- Team & execution
  a.uitgevoerd_door,
  a.uitgevoerd_op,

  -- Context
  a.issues_gevonden,
  a.opmerking

FROM woning_acties a
INNER JOIN woning_cycli c ON a.cyclus_id = c.cyclus_id
INNER JOIN huizen h ON c.object_id = h.object_id
WHERE a.actie_type = 'SCHOONMAAK'
  AND a.uitgevoerd_op IS NOT NULL
  AND (a.verwachte_schoonmaak_uren IS NOT NULL OR a.werkelijke_schoonmaak_uren IS NOT NULL)
ORDER BY a.uitgevoerd_op DESC;

-- =============================================================================
-- VIEW 4: v_status_check (Status Validation)
-- =============================================================================
-- Purpose: Validate cycle status against required actions/data
-- Use: Quality assurance, blocker identification, compliance checking
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_status_check AS
SELECT
  -- Identifiers
  c.cyclus_id,
  c.object_id,
  h.adres,

  -- Current status
  c.status,

  -- Validation checks (status-specific requirements)

  -- Check: VOORINSPECTIE_GEPLAND requires VOORINSPECTIE action with gepland_op
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

  -- Check: UITCHECK_UITGEVOERD requires UITCHECK action with uitgevoerd_op + verwachte_uren
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

  -- Check: SCHOONMAAK_NODIG requires verwachte_schoonmaak_uren > 0
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

  -- Check: KLAAR_VOOR_INCHECK requires either no cleaning needed OR cleaning completed
  CASE
    WHEN c.status = 'KLAAR_VOOR_INCHECK' THEN
      CASE
        -- Option 1: No cleaning needed (verwachte_uren = 0)
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'UITCHECK'
                       AND a.verwachte_schoonmaak_uren = 0)
        THEN 'OK'
        -- Option 2: Cleaning completed (werkelijke_uren filled)
        WHEN EXISTS (SELECT 1 FROM woning_acties a
                     WHERE a.cyclus_id = c.cyclus_id
                       AND a.actie_type = 'SCHOONMAAK'
                       AND a.werkelijke_schoonmaak_uren IS NOT NULL)
        THEN 'OK'
        ELSE 'BLOCKER'
      END
    ELSE NULL
  END AS check_klaar_voor_incheck,

  -- Check: INCHECK_UITGEVOERD requires INCHECK action with uitgevoerd_op
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

  -- Check: TERUG_NAAR_EIGENAAR requires OVERDRACHT_EIGENAAR action
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

  -- Check: AFGEROND requires appropriate completion action based on bestemming
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

  -- Overall status assessment
  CASE
    -- Count blockers across all checks
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

  -- Context
  c.bestemming,
  c.startdatum_nieuwe_huurder,

  -- Timestamps
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

-- =============================================================================
-- VIEW 5: v_planning_inputs (AI Planning Dataset - Enhanced 7-Level Priority)
-- =============================================================================
-- Purpose: Complete dataset for AI planning engine with 7-level priority scoring
-- Use: AI agent query, planning recommendations, team assignment
-- Priority Logic: Gate-based deterministic system (Tradiro → Deadline → Late → Lead Time)
-- Documentation: See database/PRIORITY_RULES.md for full specification
-- =============================================================================

CREATE VIEW IF NOT EXISTS v_planning_inputs AS
SELECT
  -- ===========================================
  -- IDENTIFIERS
  -- ===========================================
  c.cyclus_id,
  c.object_id,
  h.adres,
  h.plaats,

  -- ===========================================
  -- PROPERTY CHARACTERISTICS
  -- ===========================================
  h.woning_type,
  h.oppervlakte,
  h.aantal_sk AS slaapkamers,
  h.aantal_pers AS capaciteit,

  -- ===========================================
  -- CURRENT STATUS
  -- ===========================================
  c.status,
  c.klant_type,
  c.bestemming,

  -- ===========================================
  -- TIMELINE & DEADLINES
  -- ===========================================
  c.einddatum_huurder,
  c.startdatum_nieuwe_huurder,

  -- Effective deadline (with 14-day soft deadline fallback)
  COALESCE(
    c.startdatum_nieuwe_huurder,
    DATE(c.einddatum_huurder, '+14 days')
  ) AS effective_deadline,

  -- Has confirmed move-in date (Gate B)
  CASE
    WHEN c.startdatum_nieuwe_huurder IS NOT NULL THEN 1
    ELSE 0
  END AS has_movein_date,

  -- Days until move-in
  CASE
    WHEN COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')) IS NULL THEN NULL
    ELSE CAST(julianday(COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days'))) - julianday('now') AS INTEGER)
  END AS deadline_dagen,

  -- ===========================================
  -- CLEANING EFFORT ESTIMATION
  -- ===========================================

  -- Expected cleaning hours (with bedroom-based fallback)
  COALESCE(
    (SELECT a.verwachte_schoonmaak_uren
     FROM woning_acties a
     WHERE a.cyclus_id = c.cyclus_id
       AND a.actie_type = 'UITCHECK'
       AND a.verwachte_schoonmaak_uren IS NOT NULL
     ORDER BY a.uitgevoerd_op DESC, a.aangemaakt_op DESC
     LIMIT 1),
    -- Fallback: Estimate from bedroom count
    CASE h.aantal_sk
      WHEN 1 THEN 2.0   -- Studio/1BR = LAAG
      WHEN 2 THEN 3.5   -- 2BR = MIDDEL
      WHEN 3 THEN 5.0   -- 3BR = MIDDEL-HOOG
      ELSE 7.0          -- 4BR+ = HOOG
    END,
    4.0  -- Ultimate fallback
  ) AS verwachte_schoonmaak_uren,

  -- Dirty classification based on hours
  CASE
    WHEN COALESCE(
      (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
       WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
       AND a.verwachte_schoonmaak_uren IS NOT NULL
       ORDER BY a.uitgevoerd_op DESC LIMIT 1),
      CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
      4.0
    ) <= 2.0 THEN 'LAAG'
    WHEN COALESCE(
      (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
       WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
       AND a.verwachte_schoonmaak_uren IS NOT NULL
       ORDER BY a.uitgevoerd_op DESC LIMIT 1),
      CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
      4.0
    ) <= 5.0 THEN 'MIDDEL'
    ELSE 'HOOG'
  END AS dirty_class,

  -- Minimum lead days required (based on dirty_class)
  CASE
    WHEN COALESCE(
      (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
       WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
       AND a.verwachte_schoonmaak_uren IS NOT NULL
       ORDER BY a.uitgevoerd_op DESC LIMIT 1),
      CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
      4.0
    ) <= 2.0 THEN 1  -- LAAG
    WHEN COALESCE(
      (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
       WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
       AND a.verwachte_schoonmaak_uren IS NOT NULL
       ORDER BY a.uitgevoerd_op DESC LIMIT 1),
      CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
      4.0
    ) <= 5.0 THEN 2  -- MIDDEL
    ELSE 3           -- HOOG
  END AS min_lead_days,

  -- ===========================================
  -- PRIORITY CALCULATIONS
  -- ===========================================

  -- Required ready date (move-in date - min_lead_days)
  DATE(
    COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')),
    '-' || (
      CASE
        WHEN COALESCE(
          (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
           WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
           AND a.verwachte_schoonmaak_uren IS NOT NULL
           ORDER BY a.uitgevoerd_op DESC LIMIT 1),
          CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
          4.0
        ) <= 2.0 THEN 1
        WHEN COALESCE(
          (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
           WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
           AND a.verwachte_schoonmaak_uren IS NOT NULL
           ORDER BY a.uitgevoerd_op DESC LIMIT 1),
          CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
          4.0
        ) <= 5.0 THEN 2
        ELSE 3
      END
    ) || ' days'
  ) AS required_ready_date,

  -- Days until required ready date (Gate C calculation)
  CAST(
    julianday(
      DATE(
        COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')),
        '-' || (
          CASE
            WHEN COALESCE(
              (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
               WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
               AND a.verwachte_schoonmaak_uren IS NOT NULL
               ORDER BY a.uitgevoerd_op DESC LIMIT 1),
              CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
              4.0
            ) <= 2.0 THEN 1
            WHEN COALESCE(
              (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
               WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
               AND a.verwachte_schoonmaak_uren IS NOT NULL
               ORDER BY a.uitgevoerd_op DESC LIMIT 1),
              CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
              4.0
            ) <= 5.0 THEN 2
            ELSE 3
          END
        ) || ' days'
      )
    ) - julianday('now')
  AS INTEGER) AS days_until_required_ready,

  -- Critical late flag (Gate C) - Property cannot be ready on time
  CASE
    WHEN CAST(
      julianday(
        DATE(
          COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')),
          '-' || (
            CASE
              WHEN COALESCE(
                (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
                 WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
                 AND a.verwachte_schoonmaak_uren IS NOT NULL
                 ORDER BY a.uitgevoerd_op DESC LIMIT 1),
                CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
                4.0
              ) <= 2.0 THEN 1
              WHEN COALESCE(
                (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
                 WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
                 AND a.verwachte_schoonmaak_uren IS NOT NULL
                 ORDER BY a.uitgevoerd_op DESC LIMIT 1),
                CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
                4.0
              ) <= 5.0 THEN 2
              ELSE 3
            END
          ) || ' days'
        )
      ) - julianday('now')
    AS INTEGER) <= 0 THEN 1
    ELSE 0
  END AS is_critical_late,

  -- Client priority rank (Gate A) - TRADIRO always first
  CASE c.klant_type
    WHEN 'TRADIRO' THEN 1
    WHEN 'EXTERN' THEN 2
    WHEN 'EIGENAAR' THEN 3
    ELSE 4
  END AS client_priority_rank,

  -- Urgency band (simplified for display)
  CASE
    WHEN COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')) IS NULL THEN 'ONBEKEND'
    WHEN CAST(julianday(COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days'))) - julianday('now') AS INTEGER) <= 2 THEN 'CRITICAL'
    WHEN CAST(julianday(COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days'))) - julianday('now') AS INTEGER) <= 5 THEN 'HIGH'
    WHEN CAST(julianday(COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days'))) - julianday('now') AS INTEGER) <= 10 THEN 'NORMAL'
    ELSE 'LOW'
  END AS urgency_band,

  -- ===========================================
  -- WORKLOAD & STATUS
  -- ===========================================

  -- Open actions count
  (SELECT COUNT(*)
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
     AND a.gepland_op IS NOT NULL
     AND a.uitgevoerd_op IS NULL
  ) AS open_acties_count,

  -- Status validation severity
  (SELECT status_severity
   FROM v_status_check sc
   WHERE sc.cyclus_id = c.cyclus_id
  ) AS status_severity,

  -- Status severity rank (for sorting)
  CASE
    WHEN (SELECT status_severity FROM v_status_check sc WHERE sc.cyclus_id = c.cyclus_id) = 'BLOCKER' THEN 1
    WHEN (SELECT status_severity FROM v_status_check sc WHERE sc.cyclus_id = c.cyclus_id) = 'WARNING' THEN 2
    ELSE 3
  END AS status_severity_rank,

  -- ===========================================
  -- TEAM ASSIGNMENT
  -- ===========================================

  -- Last assigned team (for continuity)
  (SELECT a.uitgevoerd_door
   FROM woning_acties a
   WHERE a.cyclus_id = c.cyclus_id
     AND a.uitgevoerd_door IS NOT NULL
   ORDER BY a.uitgevoerd_op DESC, a.aangemaakt_op DESC
   LIMIT 1
  ) AS laatst_toegewezen_team,

  -- ===========================================
  -- NEXT ACTION SUGGESTION
  -- ===========================================

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

  -- ===========================================
  -- PRIORITY EXPLANATION (Human-Readable)
  -- ===========================================

  CASE WHEN c.klant_type = 'TRADIRO' THEN '🏢 Tradiro | ' ELSE '' END ||
  CASE
    WHEN CAST(
      julianday(
        DATE(
          COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')),
          '-' || (
            CASE
              WHEN COALESCE(
                (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
                 WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
                 AND a.verwachte_schoonmaak_uren IS NOT NULL
                 ORDER BY a.uitgevoerd_op DESC LIMIT 1),
                CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
                4.0
              ) <= 2.0 THEN 1
              WHEN COALESCE(
                (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
                 WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
                 AND a.verwachte_schoonmaak_uren IS NOT NULL
                 ORDER BY a.uitgevoerd_op DESC LIMIT 1),
                CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
                4.0
              ) <= 5.0 THEN 2
              ELSE 3
            END
          ) || ' days'
        )
      ) - julianday('now')
    AS INTEGER) <= 0 THEN '🚨 TE LAAT | '
    ELSE ''
  END ||
  'Huurder: ' || CAST(COALESCE(
    CAST(julianday(COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days'))) - julianday('now') AS INTEGER),
    999
  ) AS TEXT) || ' dgn | ' ||
  'Schoonmaak: ' || CAST(ROUND(COALESCE(
    (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
     WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
     AND a.verwachte_schoonmaak_uren IS NOT NULL
     ORDER BY a.uitgevoerd_op DESC LIMIT 1),
    CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
    4.0
  ), 1) AS TEXT) || 'u (' ||
  CASE
    WHEN COALESCE(
      (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
       WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
       AND a.verwachte_schoonmaak_uren IS NOT NULL
       ORDER BY a.uitgevoerd_op DESC LIMIT 1),
      CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
      4.0
    ) <= 2.0 THEN 'LAAG'
    WHEN COALESCE(
      (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
       WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
       AND a.verwachte_schoonmaak_uren IS NOT NULL
       ORDER BY a.uitgevoerd_op DESC LIMIT 1),
      CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
      4.0
    ) <= 5.0 THEN 'MIDDEL'
    ELSE 'HOOG'
  END || ') | Klaar: ' ||
  DATE(
    COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')),
    '-' || (
      CASE
        WHEN COALESCE(
          (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
           WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
           AND a.verwachte_schoonmaak_uren IS NOT NULL
           ORDER BY a.uitgevoerd_op DESC LIMIT 1),
          CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
          4.0
        ) <= 2.0 THEN 1
        WHEN COALESCE(
          (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
           WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
           AND a.verwachte_schoonmaak_uren IS NOT NULL
           ORDER BY a.uitgevoerd_op DESC LIMIT 1),
          CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
          4.0
        ) <= 5.0 THEN 2
        ELSE 3
      END
    ) || ' days'
  ) AS priority_explanation,

  -- ===========================================
  -- METADATA
  -- ===========================================

  c.interne_opmerking,
  c.aangemaakt_op,
  c.laatst_bijgewerkt_op

FROM woning_cycli c
INNER JOIN huizen h ON c.object_id = h.object_id
WHERE c.is_actief = 1

-- ===========================================
-- 7-LEVEL PRIORITY SORT
-- ===========================================
ORDER BY
  -- Level 1: TRADIRO always first (Gate A)
  CASE c.klant_type
    WHEN 'TRADIRO' THEN 1
    WHEN 'EXTERN' THEN 2
    WHEN 'EIGENAAR' THEN 3
    ELSE 4
  END ASC,

  -- Level 2: Confirmed move-in dates first (Gate B)
  CASE WHEN c.startdatum_nieuwe_huurder IS NOT NULL THEN 0 ELSE 1 END ASC,

  -- Level 3: Critical late items first (Gate C)
  CASE
    WHEN CAST(
      julianday(
        DATE(
          COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')),
          '-' || (
            CASE
              WHEN COALESCE(
                (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
                 WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
                 AND a.verwachte_schoonmaak_uren IS NOT NULL
                 ORDER BY a.uitgevoerd_op DESC LIMIT 1),
                CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
                4.0
              ) <= 2.0 THEN 1
              WHEN COALESCE(
                (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
                 WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
                 AND a.verwachte_schoonmaak_uren IS NOT NULL
                 ORDER BY a.uitgevoerd_op DESC LIMIT 1),
                CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
                4.0
              ) <= 5.0 THEN 2
              ELSE 3
            END
          ) || ' days'
        )
      ) - julianday('now')
    AS INTEGER) <= 0 THEN 0
    ELSE 1
  END ASC,

  -- Level 4: Tightest prep window (days until required ready)
  CAST(
    julianday(
      DATE(
        COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days')),
        '-' || (
          CASE
            WHEN COALESCE(
              (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
               WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
               AND a.verwachte_schoonmaak_uren IS NOT NULL
               ORDER BY a.uitgevoerd_op DESC LIMIT 1),
              CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
              4.0
            ) <= 2.0 THEN 1
            WHEN COALESCE(
              (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
               WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
               AND a.verwachte_schoonmaak_uren IS NOT NULL
               ORDER BY a.uitgevoerd_op DESC LIMIT 1),
              CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
              4.0
            ) <= 5.0 THEN 2
            ELSE 3
          END
        ) || ' days'
      )
    ) - julianday('now')
  AS INTEGER) ASC NULLS LAST,

  -- Level 5: Soonest move-in deadline
  julianday(COALESCE(c.startdatum_nieuwe_huurder, DATE(c.einddatum_huurder, '+14 days'))) ASC NULLS LAST,

  -- Level 6: Most cleaning work first
  COALESCE(
    (SELECT a.verwachte_schoonmaak_uren FROM woning_acties a
     WHERE a.cyclus_id = c.cyclus_id AND a.actie_type = 'UITCHECK'
     AND a.verwachte_schoonmaak_uren IS NOT NULL
     ORDER BY a.uitgevoerd_op DESC LIMIT 1),
    CASE h.aantal_sk WHEN 1 THEN 2.0 WHEN 2 THEN 3.5 WHEN 3 THEN 5.0 ELSE 7.0 END,
    4.0
  ) DESC,

  -- Level 7: Blockers first
  CASE
    WHEN (SELECT status_severity FROM v_status_check sc WHERE sc.cyclus_id = c.cyclus_id) = 'BLOCKER' THEN 1
    WHEN (SELECT status_severity FROM v_status_check sc WHERE sc.cyclus_id = c.cyclus_id) = 'WARNING' THEN 2
    ELSE 3
  END ASC;

-- =============================================================================
-- VIEWS METADATA
-- =============================================================================

SELECT
  'Views inuitcheck created successfully' AS status,
  '5 views: v_actieve_cycli, v_open_acties, v_schoonmaak_variance, v_status_check, v_planning_inputs' AS views,
  datetime('now') AS timestamp;

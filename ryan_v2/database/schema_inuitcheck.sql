-- ============================================================================
-- RYAN V2: In-Uit-Check Database Schema
-- ============================================================================
-- Purpose: Property lifecycle management for check-out → cleaning → check-in
-- Author: RyanRent Development Team
-- Date: 2025-12-22
-- Database: ryanrent_mock.db (extends existing schema)
-- ============================================================================

-- =============================================================================
-- TABLE 1: woning_cycli (Property Lifecycles)
-- =============================================================================
-- Purpose: Track one complete cycle per property through checkout→cleaning→checkin
-- Cardinality: 1 house : N cycles (over time), 1 house : 1 active cycle (at any moment)
-- =============================================================================

CREATE TABLE IF NOT EXISTS woning_cycli (
  -- Primary Key
  cyclus_id TEXT PRIMARY KEY,              -- UUID (DB-generated)

  -- Foreign Keys
  huis_id TEXT NOT NULL,                   -- FK to huizen.object_id

  -- Status Management
  is_actief INTEGER NOT NULL DEFAULT 1,    -- 1 = active, 0 = archived
                                            -- Only 1 active cycle per house

  -- Client & Destination
  klant_type TEXT NOT NULL                 -- TRADIRO|EXTERN|EIGENAAR
    CHECK (klant_type IN ('TRADIRO', 'EXTERN', 'EIGENAAR')),
  bestemming TEXT NOT NULL                 -- OPNIEUW_VERHUREN|TERUG_NAAR_EIGENAAR
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
  einddatum_huurder TEXT,                  -- ISO date: YYYY-MM-DD
  startdatum_nieuwe_huurder TEXT,          -- ISO date: YYYY-MM-DD (deadline)

  -- Notes
  interne_opmerking TEXT,

  -- Timestamps
  aangemaakt_op TEXT NOT NULL DEFAULT (datetime('now')),
  laatst_bijgewerkt_op TEXT NOT NULL DEFAULT (datetime('now')),

  -- Constraints
  FOREIGN KEY (huis_id) REFERENCES huizen(object_id)
);

-- =============================================================================
-- INDEXES for woning_cycli
-- =============================================================================

-- Unique constraint: Only 1 active cycle per house
CREATE UNIQUE INDEX IF NOT EXISTS idx_woning_cycli_active_unique
  ON woning_cycli(huis_id)
  WHERE is_actief = 1;

-- Performance: Lookup cycles by house
CREATE INDEX IF NOT EXISTS idx_woning_cycli_huis_id
  ON woning_cycli(huis_id);

-- Performance: Filter by status
CREATE INDEX IF NOT EXISTS idx_woning_cycli_status
  ON woning_cycli(status)
  WHERE is_actief = 1;

-- Performance: Deadline queries
CREATE INDEX IF NOT EXISTS idx_woning_cycli_deadline
  ON woning_cycli(startdatum_nieuwe_huurder)
  WHERE is_actief = 1 AND startdatum_nieuwe_huurder IS NOT NULL;

-- =============================================================================
-- TABLE 2: woning_acties (Property Actions)
-- =============================================================================
-- Purpose: Record factual events that prove cycle status validity (append-only)
-- Cardinality: 1 cycle : N actions (history)
-- =============================================================================

CREATE TABLE IF NOT EXISTS woning_acties (
  -- Primary Key
  actie_id TEXT PRIMARY KEY,               -- UUID

  -- Foreign Keys
  cyclus_id TEXT NOT NULL,                 -- FK to woning_cycli.cyclus_id

  -- Action Type (6 types)
  actie_type TEXT NOT NULL CHECK (actie_type IN (
    'VOORINSPECTIE',
    'UITCHECK',
    'SCHOONMAAK',
    'INCHECK',
    'OVERDRACHT_EIGENAAR',
    'REPARATIE'
  )),

  -- Planning & Execution
  gepland_op TEXT,                         -- ISO datetime: YYYY-MM-DD HH:MM:SS
  uitgevoerd_op TEXT,                      -- ISO datetime: YYYY-MM-DD HH:MM:SS
  uitgevoerd_door TEXT,                    -- Team/person name

  -- Inspection Fields
  fotos_gemaakt TEXT                       -- JA|NEE|ONBEKEND
    CHECK (fotos_gemaakt IS NULL OR fotos_gemaakt IN ('JA', 'NEE', 'ONBEKEND')),
  issues_gevonden TEXT                     -- JA|NEE|ONBEKEND
    CHECK (issues_gevonden IS NULL OR issues_gevonden IN ('JA', 'NEE', 'ONBEKEND')),

  -- Cleaning Hours Tracking
  verwachte_schoonmaak_uren REAL           -- Hours, ≥0 (set during UITCHECK)
    CHECK (verwachte_schoonmaak_uren IS NULL OR verwachte_schoonmaak_uren >= 0),
  werkelijke_schoonmaak_uren REAL          -- Hours, ≥0 (set during SCHOONMAAK)
    CHECK (werkelijke_schoonmaak_uren IS NULL OR werkelijke_schoonmaak_uren >= 0),

  -- Key Management
  sleutels_bevestigd TEXT                  -- JA|NEE|ONBEKEND
    CHECK (sleutels_bevestigd IS NULL OR sleutels_bevestigd IN ('JA', 'NEE', 'ONBEKEND')),
  sleuteloverdracht_methode TEXT           -- PERSOONLIJK|IN_WONING_ACHTERGELATEN|ANDERS
    CHECK (sleuteloverdracht_methode IS NULL OR sleuteloverdracht_methode IN (
      'PERSOONLIJK', 'IN_WONING_ACHTERGELATEN', 'ANDERS'
    )),

  -- Notes
  opmerking TEXT,

  -- Timestamps
  aangemaakt_op TEXT NOT NULL DEFAULT (datetime('now')),
  bijgewerkt_op TEXT NOT NULL DEFAULT (datetime('now')),

  -- Constraints
  FOREIGN KEY (cyclus_id) REFERENCES woning_cycli(cyclus_id)
);

-- =============================================================================
-- INDEXES for woning_acties
-- =============================================================================

-- Performance: Lookup actions by cycle
CREATE INDEX IF NOT EXISTS idx_woning_acties_cyclus_id
  ON woning_acties(cyclus_id);

-- Performance: Filter by action type
CREATE INDEX IF NOT EXISTS idx_woning_acties_type
  ON woning_acties(actie_type);

-- Performance: Find open actions (planned but not executed)
CREATE INDEX IF NOT EXISTS idx_woning_acties_open
  ON woning_acties(gepland_op, uitgevoerd_op)
  WHERE gepland_op IS NOT NULL AND uitgevoerd_op IS NULL;

-- Performance: Execution date queries
CREATE INDEX IF NOT EXISTS idx_woning_acties_uitgevoerd
  ON woning_acties(uitgevoerd_op)
  WHERE uitgevoerd_op IS NOT NULL;

-- =============================================================================
-- TABLE 3: teams (Team Registry)
-- =============================================================================
-- Purpose: Track teams for capacity planning and assignment
-- =============================================================================

CREATE TABLE IF NOT EXISTS teams (
  -- Primary Key
  team_id TEXT PRIMARY KEY,                -- UUID or simple ID

  -- Team Info
  team_naam TEXT NOT NULL,                 -- Display name
  team_type TEXT                           -- INTERN|SCHOONMAAK|CONTRACTOR
    CHECK (team_type IS NULL OR team_type IN ('INTERN', 'SCHOONMAAK', 'CONTRACTOR')),

  -- Capacity
  standaard_capaciteit_uren_per_dag REAL   -- Standard daily hours
    CHECK (standaard_capaciteit_uren_per_dag IS NULL OR
           standaard_capaciteit_uren_per_dag >= 0),

  -- Timestamps
  aangemaakt_op TEXT NOT NULL DEFAULT (datetime('now'))
);

-- =============================================================================
-- INDEXES for teams
-- =============================================================================

-- Performance: Lookup by name
CREATE INDEX IF NOT EXISTS idx_teams_naam
  ON teams(team_naam);

-- =============================================================================
-- TABLE 4: team_beschikbaarheid (Daily Team Availability)
-- =============================================================================
-- Purpose: Track daily team capacity and workload
-- =============================================================================

CREATE TABLE IF NOT EXISTS team_beschikbaarheid (
  -- Primary Key
  id INTEGER PRIMARY KEY AUTOINCREMENT,

  -- Foreign Keys
  team_id TEXT NOT NULL,                   -- FK to teams.team_id

  -- Date & Capacity
  datum TEXT NOT NULL,                     -- ISO date: YYYY-MM-DD
  beschikbare_uren REAL,                   -- Available hours for this date
  ingepland_uren REAL DEFAULT 0,           -- Planned hours for this date

  -- Constraints
  CHECK (beschikbare_uren IS NULL OR beschikbare_uren >= 0),
  CHECK (ingepland_uren >= 0),
  FOREIGN KEY (team_id) REFERENCES teams(team_id),

  -- Unique: One record per team per date
  UNIQUE(team_id, datum)
);

-- =============================================================================
-- INDEXES for team_beschikbaarheid
-- =============================================================================

-- Performance: Lookup availability by team and date
CREATE INDEX IF NOT EXISTS idx_team_beschikbaarheid_team_datum
  ON team_beschikbaarheid(team_id, datum);

-- Performance: Date range queries
CREATE INDEX IF NOT EXISTS idx_team_beschikbaarheid_datum
  ON team_beschikbaarheid(datum);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger: Auto-update laatst_bijgewerkt_op for woning_cycli
CREATE TRIGGER IF NOT EXISTS trg_woning_cycli_updated
  AFTER UPDATE ON woning_cycli
  FOR EACH ROW
  WHEN OLD.laatst_bijgewerkt_op = NEW.laatst_bijgewerkt_op
BEGIN
  UPDATE woning_cycli
  SET laatst_bijgewerkt_op = datetime('now')
  WHERE cyclus_id = NEW.cyclus_id;
END;

-- Trigger: Auto-update bijgewerkt_op for woning_acties
CREATE TRIGGER IF NOT EXISTS trg_woning_acties_updated
  AFTER UPDATE ON woning_acties
  FOR EACH ROW
  WHEN OLD.bijgewerkt_op = NEW.bijgewerkt_op
BEGIN
  UPDATE woning_acties
  SET bijgewerkt_op = datetime('now')
  WHERE actie_id = NEW.actie_id;
END;

-- Trigger: Validate UITCHECK actions have verwachte_schoonmaak_uren when executed
-- Purpose: Enforce data quality for priority system - cleaning hours required for dirty_class calculation
CREATE TRIGGER IF NOT EXISTS trg_validate_uitcheck_hours
  BEFORE INSERT ON woning_acties
  FOR EACH ROW
  WHEN NEW.actie_type = 'UITCHECK' AND NEW.uitgevoerd_op IS NOT NULL AND NEW.verwachte_schoonmaak_uren IS NULL
BEGIN
  SELECT RAISE(ABORT, 'UITCHECK action with uitgevoerd_op requires verwachte_schoonmaak_uren to be set');
END;

-- Trigger: Validate UITCHECK hours on update
CREATE TRIGGER IF NOT EXISTS trg_validate_uitcheck_hours_update
  BEFORE UPDATE ON woning_acties
  FOR EACH ROW
  WHEN NEW.actie_type = 'UITCHECK' AND NEW.uitgevoerd_op IS NOT NULL AND NEW.verwachte_schoonmaak_uren IS NULL
BEGIN
  SELECT RAISE(ABORT, 'UITCHECK action with uitgevoerd_op requires verwachte_schoonmaak_uren to be set');
END;

-- =============================================================================
-- SCHEMA METADATA
-- =============================================================================

-- Track schema version for future migrations
CREATE TABLE IF NOT EXISTS schema_version (
  schema_name TEXT PRIMARY KEY,
  version INTEGER NOT NULL,
  applied_on TEXT NOT NULL DEFAULT (datetime('now'))
);

INSERT OR REPLACE INTO schema_version (schema_name, version)
VALUES ('inuitcheck', 1);

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

SELECT
  'Schema inuitcheck v1 created successfully' AS status,
  datetime('now') AS timestamp;

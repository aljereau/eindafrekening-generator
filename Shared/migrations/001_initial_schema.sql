-- Migration 001: Initial Database Schema
-- RyanRent Eindafrekening Generator V2.0
-- Created: November 2024

-- Set schema version
PRAGMA user_version = 1;

-- Enable Write-Ahead Logging for better concurrency (OneDrive sync)
PRAGMA journal_mode = WAL;

-- Foreign keys enforcement
PRAGMA foreign_keys = ON;

-- Main table: Store eindafrekeningen with full JSON data
CREATE TABLE IF NOT EXISTS eindafrekeningen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Unique identification (composite key)
    client_name TEXT NOT NULL,
    checkin_date DATE NOT NULL,
    checkout_date DATE NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,

    -- Version tracking
    version_reason TEXT NOT NULL,  -- REQUIRED for v2+: "Correctie GWE", "Extra schade", etc.

    -- Complete data storage (JSON format)
    data_json TEXT NOT NULL,  -- Full viewmodel as JSON for reconstruction

    -- Indexed summary fields for fast queries
    object_address TEXT,
    period_days INTEGER,
    borg_terug REAL,
    gwe_totaal_incl REAL,
    totaal_eindafrekening REAL,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_by TEXT DEFAULT 'RyanRent Generator V2.0',
    file_path TEXT,  -- Path to generated HTML/PDF

    -- Constraints
    UNIQUE(client_name, checkin_date, checkout_date, version),
    CHECK(version >= 1),
    CHECK(length(client_name) > 0),
    CHECK(checkin_date < checkout_date)
);

-- Schema metadata table
CREATE TABLE IF NOT EXISTS schema_versions (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT NOT NULL
);

-- Insert initial schema version
INSERT INTO schema_versions (version, description)
VALUES (1, 'Initial schema with eindafrekeningen table');

-- Indexes for fast lookup
CREATE INDEX IF NOT EXISTS idx_client_dates
    ON eindafrekeningen(client_name, checkin_date, checkout_date);

CREATE INDEX IF NOT EXISTS idx_created_desc
    ON eindafrekeningen(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_client_name
    ON eindafrekeningen(client_name);

CREATE INDEX IF NOT EXISTS idx_version
    ON eindafrekeningen(client_name, checkin_date, checkout_date, version DESC);

-- View: Latest versions only (most recent version per client+dates)
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
   AND e.version = latest.max_version;

-- View: Version history summary
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
ORDER BY last_updated DESC;

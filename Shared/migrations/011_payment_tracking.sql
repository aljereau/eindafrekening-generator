-- Migration: 011_payment_tracking.sql
-- Description: Add table for tracking debtor status (payment behavior).

CREATE TABLE IF NOT EXISTS debiteuren_standen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relatie_id INTEGER REFERENCES relaties (id),
    factuur_nummer TEXT,
    factuur_datum DATE,
    verval_datum DATE,
    oorspronkelijk_bedrag REAL,
    openstaand_bedrag REAL,
    dagen_openstaand INTEGER,
    status TEXT, -- 'Open', 'Te Laat', 'Betaald'
    snapshot_datum DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_debiteuren_relatie ON debiteuren_standen (relatie_id);

CREATE INDEX idx_debiteuren_snapshot ON debiteuren_standen (snapshot_datum);
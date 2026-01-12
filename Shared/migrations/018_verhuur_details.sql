-- Migration 018: Add verhuur/inhuur contract details
-- Supports comprehensive property view

-- 1. INHUUR_CONTRACTEN - Add facturatie flag
ALTER TABLE inhuur_contracten ADD COLUMN facturatie TEXT;

-- 2. VERHUUR_CONTRACTEN - Add contract period details
ALTER TABLE verhuur_contracten ADD COLUMN minimum_periode INTEGER;

ALTER TABLE verhuur_contracten ADD COLUMN opgezegd_datum DATE;

ALTER TABLE verhuur_contracten ADD COLUMN datum_incheck DATE;

ALTER TABLE verhuur_contracten ADD COLUMN datum_uitcheck DATE;

ALTER TABLE verhuur_contracten ADD COLUMN huurder_naam TEXT;

ALTER TABLE verhuur_contracten ADD COLUMN mutatie_notities TEXT;

ALTER TABLE verhuur_contracten
ADD COLUMN verhuur_incl_btw REAL DEFAULT 0;

ALTER TABLE verhuur_contracten
ADD COLUMN verhuur_excl_btw REAL DEFAULT 0;

ALTER TABLE verhuur_contracten
ADD COLUMN overige_kosten REAL DEFAULT 0;

ALTER TABLE verhuur_contracten
ADD COLUMN afval_kosten REAL DEFAULT 0;

ALTER TABLE verhuur_contracten ADD COLUMN marge REAL DEFAULT 0;
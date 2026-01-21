-- Migration: 017_add_kale_huur.sql
-- Created: 2026-01-20
-- Description: Add kale_huur column to inhuur_contracten

ALTER TABLE inhuur_contracten ADD COLUMN kale_huur REAL DEFAULT 0;

INSERT OR IGNORE INTO
    schema_migrations (version)
VALUES ('017_add_kale_huur.sql');
-- Migration: 013_add_facturatie_type.sql
-- Created: 2026-01-20
-- Description: Add facturatie_type column to huizen table for admin tracking
--              Values: 'Factuur' (RyanRent makes invoice), 'DS' (Direct Settlement), NULL (not classified)

-- ============================================
-- ADD FACTURATIE_TYPE COLUMN
-- ============================================
-- Note: SQLite doesn't support IF NOT EXISTS for columns,
-- but this migration is tracked in schema_migrations so won't run twice

ALTER TABLE huizen ADD COLUMN facturatie_type TEXT;

-- Record this migration
INSERT OR IGNORE INTO
    schema_migrations (version)
VALUES ('013_add_facturatie_type.sql');
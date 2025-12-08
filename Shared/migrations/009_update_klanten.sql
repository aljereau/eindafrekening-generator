-- Migration: 009_update_klanten.sql
-- Description: Rename klanten to relaties and add columns for suppliers.

-- Rename table
ALTER TABLE klanten RENAME TO relaties;

-- Add columns
ALTER TABLE relaties ADD COLUMN plaats TEXT;

ALTER TABLE relaties ADD COLUMN land TEXT;

ALTER TABLE relaties ADD COLUMN is_klant BOOLEAN DEFAULT 0;

ALTER TABLE relaties ADD COLUMN is_leverancier BOOLEAN DEFAULT 0;

-- Update existing records to be clients by default
UPDATE relaties SET is_klant = 1;
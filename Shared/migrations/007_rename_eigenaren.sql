-- Migration 007: Rename Eigenaren to Leveranciers
-- "Eigenaren" are actually a subset of "Leveranciers" (Suppliers).

-- 1. Rename table
ALTER TABLE eigenaren RENAME TO leveranciers;

-- 2. Update inhuur_contracten column (SQLite doesn't support RENAME COLUMN in all versions easily, but let's try standard syntax)
-- If this fails, we might need to recreate the table, but for now we assume modern SQLite.
ALTER TABLE inhuur_contracten
RENAME COLUMN eigenaar_id TO leverancier_id;
-- Migration: 010_add_postcode_to_relaties.sql
-- Description: Add postcode column to relaties table.

ALTER TABLE relaties ADD COLUMN postcode TEXT;
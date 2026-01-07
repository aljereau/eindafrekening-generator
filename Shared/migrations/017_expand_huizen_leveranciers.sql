-- Migration 017: Expand huizen, leveranciers, and inhuur_contracten
-- Adds property details, owner contact info, and contract terms

-- 1. HUIZEN - Add property details
ALTER TABLE huizen ADD COLUMN tekening TEXT;

ALTER TABLE huizen ADD COLUMN lijst_meters TEXT;

ALTER TABLE huizen ADD COLUMN meter_gas TEXT;

ALTER TABLE huizen ADD COLUMN meter_electra TEXT;

ALTER TABLE huizen ADD COLUMN meter_water TEXT;

-- 2. LEVERANCIERS - Add contact details
ALTER TABLE leveranciers ADD COLUMN contactpersoon TEXT;

ALTER TABLE leveranciers ADD COLUMN adres TEXT;

ALTER TABLE leveranciers ADD COLUMN postcode TEXT;

ALTER TABLE leveranciers ADD COLUMN woonplaats TEXT;

-- 3. INHUUR_CONTRACTEN - Add contract terms
ALTER TABLE inhuur_contracten ADD COLUMN opzegtermijn INTEGER;
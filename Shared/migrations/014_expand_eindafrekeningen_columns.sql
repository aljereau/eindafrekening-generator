-- Migration 014: Expand eindafrekeningen table with Excel columns
-- Adds missing basis fields from Master Template for better tracking and reporting

ALTER TABLE eindafrekeningen ADD COLUMN object_id TEXT;

ALTER TABLE eindafrekeningen ADD COLUMN klant_nr TEXT;

ALTER TABLE eindafrekeningen ADD COLUMN inspecteur TEXT;

ALTER TABLE eindafrekeningen ADD COLUMN folder_link TEXT;

ALTER TABLE eindafrekeningen ADD COLUMN contractnr TEXT;

ALTER TABLE eindafrekeningen ADD COLUMN gwe_beheer_type TEXT;

ALTER TABLE eindafrekeningen
ADD COLUMN voorschot_gwe_incl REAL DEFAULT 0;

ALTER TABLE eindafrekeningen
ADD COLUMN extra_voorschot_omschrijving TEXT;

-- Meter readings
ALTER TABLE eindafrekeningen ADD COLUMN meter_elek_begin REAL;

ALTER TABLE eindafrekeningen ADD COLUMN meter_elek_eind REAL;

ALTER TABLE eindafrekeningen ADD COLUMN meter_gas_begin REAL;

ALTER TABLE eindafrekeningen ADD COLUMN meter_gas_eind REAL;

ALTER TABLE eindafrekeningen ADD COLUMN meter_water_begin REAL;

ALTER TABLE eindafrekeningen ADD COLUMN meter_water_eind REAL;

-- Cleaning details
ALTER TABLE eindafrekeningen
ADD COLUMN schoonmaak_uren_extra REAL DEFAULT 0;

ALTER TABLE eindafrekeningen
ADD COLUMN schoonmaak_uurtarief REAL DEFAULT 0;
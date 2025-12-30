-- Migration 015: Schema Optimization
-- Purpose: Create convenience view for eindafrekeningen and enable FK enforcement
-- Date: 2025-12-29

-- ============================================================================
-- TABLE PURPOSE DOCUMENTATION
-- ============================================================================
--
-- eindafrekeningen: SNAPSHOT table
--   - Stores frozen settlement documents at the moment of generation
--   - Denormalized by design: captures state at generation time
--   - Changes to client/house data should NOT affect historical settlements
--   - Optional booking_id links to boekingen when available
--
-- damages: LIVE TRACKING table
--   - Records damages as they're discovered during tenancy/inspections
--   - Linked to boekingen via booking_id
--   - Used as source data; totals snapshot into eindafrekeningen.data_json
--
-- meter_readings: LIVE TRACKING table
--   - Records meter snapshots at check-in and check-out
--   - Linked to boekingen via booking_id
--   - Used as source data; values snapshot into eindafrekeningen columns
--
-- boekingen: TRANSACTIONAL table
--   - Core booking records linking clients to properties
--   - Properly normalized with FKs to huizen, relaties, verhuur_contracten
-- ============================================================================

-- Create convenience view for querying eindafrekeningen with related data
DROP VIEW IF EXISTS v_eindafrekeningen_extended;

CREATE VIEW v_eindafrekeningen_extended AS
SELECT
    -- Core eindafrekening fields
    e.id,
    e.client_name,
    e.checkin_date,
    e.checkout_date,
    e.version,
    e.version_reason,
    e.object_address,
    e.period_days,
    e.borg_terug,
    e.gwe_totaal_incl,
    e.totaal_eindafrekening,
    e.created_at,
    e.file_path,
    e.schoonmaak_pakket,
    e.schoonmaak_kosten,
    e.schade_totaal_kosten,
    e.extra_voorschot_bedrag,
    e.booking_id,
    e.object_id,
    e.klant_nr,
    e.inspecteur,
    e.gwe_beheer_type,
    e.voorschot_gwe_incl,
    e.meter_elek_begin,
    e.meter_elek_eind,
    e.meter_gas_begin,
    e.meter_gas_eind,
    e.meter_water_begin,
    e.meter_water_eind,
    e.schoonmaak_uren_extra,
    e.schoonmaak_uurtarief,

-- Joined house data (from huizen via object_id)
h.adres AS huis_adres,
h.postcode AS huis_postcode,
h.plaats AS huis_plaats,
h.woning_type AS huis_type,

-- Joined client data (from relaties via klant_nr)
r.naam AS klant_naam_db,
r.email AS klant_email,
r.telefoonnummer AS klant_telefoon,

-- Joined booking data (from boekingen via booking_id)
b.voorschot_gwe AS boeking_voorschot_gwe,
b.voorschot_schoonmaak AS boeking_voorschot_schoonmaak,
b.betaalde_borg AS boeking_betaalde_borg,
b.status AS boeking_status
FROM
    eindafrekeningen e
    LEFT JOIN huizen h ON e.object_id = h.object_id
    LEFT JOIN relaties r ON e.klant_nr = CAST(r.id AS TEXT)
    LEFT JOIN boekingen b ON e.booking_id = b.id;

-- Create index on booking_id for faster joins (if not exists)
CREATE INDEX IF NOT EXISTS idx_eindafrekeningen_booking_id ON eindafrekeningen (booking_id);

CREATE INDEX IF NOT EXISTS idx_eindafrekeningen_object_id ON eindafrekeningen (object_id);

CREATE INDEX IF NOT EXISTS idx_eindafrekeningen_klant_nr ON eindafrekeningen (klant_nr);
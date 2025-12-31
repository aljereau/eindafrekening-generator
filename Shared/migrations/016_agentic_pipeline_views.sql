-- Migration 016: Agentic Pipeline Views
-- Purpose: Create canonical export views for the intent-based query system
-- Date: 2025-12-30

-- ============================================================================
-- NEW VIEWS FOR AGENTIC PIPELINE
-- These views are "export-shaped" - pre-joined and ready for direct export
-- ============================================================================

-- v_bookings_extended: Full booking details with house and client info
DROP VIEW IF EXISTS v_bookings_extended;

CREATE VIEW v_bookings_extended AS
SELECT
    b.id AS booking_id,
    b.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.woning_type,
    b.klant_id,
    r.naam AS klant_naam,
    r.email AS klant_email,
    r.telefoonnummer AS klant_telefoon,
    b.checkin_datum,
    b.checkout_datum,
    julianday(b.checkout_datum) - julianday(b.checkin_datum) AS verblijf_dagen,
    julianday(b.checkout_datum) - julianday('now') AS dagen_tot_checkout,
    julianday(b.checkin_datum) - julianday('now') AS dagen_tot_checkin,
    b.betaalde_borg,
    b.voorschot_gwe,
    b.voorschot_schoonmaak,
    b.schoonmaak_pakket,
    b.totale_huur_factuur,
    b.status,
    b.settlement_generated,
    b.settlement_generated_at,
    -- Contract info
    vc.kale_huur AS verhuur_kale_huur,
    vc.servicekosten AS verhuur_servicekosten,
    ic.kale_huur AS inhuur_kale_huur
FROM
    boekingen b
    JOIN huizen h ON b.object_id = h.object_id
    LEFT JOIN relaties r ON b.klant_id = r.id
    LEFT JOIN verhuur_contracten vc ON b.contract_id = vc.id
    LEFT JOIN inhuur_contracten ic ON h.object_id = ic.object_id
    AND ic.status = 'active';

-- v_contracts_overview: Active contracts with financials
DROP VIEW IF EXISTS v_contracts_overview;

CREATE VIEW v_contracts_overview AS
SELECT
    'verhuur' AS contract_type,
    vc.id AS contract_id,
    vc.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    r.naam AS klant_naam,
    vc.start_datum,
    vc.eind_datum,
    vc.kale_huur,
    vc.servicekosten,
    vc.voorschot_gwe,
    vc.borg,
    vc.status,
    NULL AS inhuur_prijs,
    vc.kale_huur AS revenue_per_month
FROM
    verhuur_contracten vc
    JOIN huizen h ON vc.object_id = h.object_id
    LEFT JOIN relaties r ON vc.klant_id = r.id
WHERE
    vc.status = 'active'
UNION ALL
SELECT
    'inhuur' AS contract_type,
    ic.id AS contract_id,
    ic.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    l.naam AS klant_naam, -- eigenaar
    ic.start_datum,
    ic.eind_datum,
    ic.kale_huur,
    ic.servicekosten,
    ic.voorschot_gwe,
    ic.borg,
    ic.status,
    ic.kale_huur AS inhuur_prijs,
    - ic.kale_huur AS revenue_per_month -- cost, so negative
FROM
    inhuur_contracten ic
    JOIN huizen h ON ic.object_id = h.object_id
    LEFT JOIN leveranciers l ON ic.leverancier_id = l.id
WHERE
    ic.status = 'active';

-- v_inspections_pipeline: Upcoming and overdue inspections
DROP VIEW IF EXISTS v_inspections_pipeline;

CREATE VIEW v_inspections_pipeline AS
SELECT
    i.id AS inspection_id,
    i.booking_id,
    b.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    r.naam AS klant_naam,
    i.inspection_type,
    i.planned_date,
    i.completed_date,
    i.status,
    i.inspector,
    i.notes,
    julianday(i.planned_date) - julianday('now') AS dagen_tot_inspectie,
    CASE
        WHEN i.status = 'completed' THEN 'AFGEROND'
        WHEN julianday(i.planned_date) < julianday('now') THEN 'ACHTERSTALLIG'
        WHEN julianday(i.planned_date) - julianday('now') <= 7 THEN 'DEZE_WEEK'
        ELSE 'GEPLAND'
    END AS urgentie
FROM
    inspections i
    LEFT JOIN boekingen b ON i.booking_id = b.id
    LEFT JOIN huizen h ON b.object_id = h.object_id
    LEFT JOIN relaties r ON b.klant_id = r.id
WHERE
    i.status != 'cancelled'
ORDER BY i.planned_date;

-- v_occupancy_summary: Occupancy stats per house
DROP VIEW IF EXISTS v_occupancy_summary;

CREATE VIEW v_occupancy_summary AS
SELECT
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.status AS huis_status,
    COUNT(DISTINCT b.id) AS totaal_boekingen,
    SUM(
        julianday(b.checkout_datum) - julianday(b.checkin_datum)
    ) AS totaal_verblijf_dagen,
    -- Current occupancy
    (
        SELECT r.naam
        FROM boekingen curr
            JOIN relaties r ON curr.klant_id = r.id
        WHERE
            curr.object_id = h.object_id
            AND DATE('now') BETWEEN curr.checkin_datum AND curr.checkout_datum
        LIMIT 1
    ) AS huidige_huurder,
    (
        SELECT curr.checkout_datum
        FROM boekingen curr
        WHERE
            curr.object_id = h.object_id
            AND DATE('now') BETWEEN curr.checkin_datum AND curr.checkout_datum
        LIMIT 1
    ) AS huidige_checkout,
    -- Next booking
    (
        SELECT MIN(next.checkin_datum)
        FROM boekingen next
        WHERE
            next.object_id = h.object_id
            AND next.checkin_datum > DATE('now')
    ) AS volgende_checkin
FROM huizen h
    LEFT JOIN boekingen b ON h.object_id = b.object_id
GROUP BY
    h.object_id;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_boekingen_dates ON boekingen (checkin_datum, checkout_datum);

CREATE INDEX IF NOT EXISTS idx_inspections_planned ON inspections (planned_date, status);

CREATE INDEX IF NOT EXISTS idx_boekingen_status ON boekingen (status);
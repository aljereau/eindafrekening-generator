-- Migration: 011_add_gwe_leverancier_info.sql
-- Created: 2026-01-12
-- Description: Add meterbeheerder and GWE leverancier to huizen

-- ============================================
-- ADD GWE LEVERANCIER INFO TO HUIZEN
-- ============================================

ALTER TABLE huizen ADD COLUMN meterbeheerder TEXT;
-- e.g., Enexis, Stedin
ALTER TABLE huizen ADD COLUMN gwe_leverancier TEXT;
-- e.g., Vattenfall, Eneco

-- ============================================
-- ADD GWE_TARIEVEN TABLE FOR STANDARD RATES
-- (So we don't have to enter them every time)
-- ============================================

CREATE TABLE IF NOT EXISTS gwe_tarieven (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    leverancier TEXT NOT NULL,
    type TEXT NOT NULL, -- Water, Gas, Elektra
    omschrijving TEXT NOT NULL, -- levering, vastrecht, etc.
    tarief REAL DEFAULT 0,
    btw_pct REAL DEFAULT 0.21,
    eenheid TEXT, -- m³, kWh, dag
    geldig_vanaf DATE,
    geldig_tot DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- SEED: WATER TARIEVEN (fixed, from Calculator)
-- ============================================

INSERT INTO
    gwe_tarieven (
        leverancier,
        type,
        omschrijving,
        tarief,
        btw_pct,
        eenheid
    )
VALUES (
        'PWN',
        'Water',
        'levering',
        1.29,
        0.09,
        'm³'
    ),
    (
        'PWN',
        'Water',
        'vastrecht',
        0.25474,
        0.09,
        'dag'
    ),
    (
        'PWN',
        'Water',
        'Belasting op leidingwater',
        0.45899,
        0.09,
        'm³'
    ),
    (
        'PWN',
        'Water',
        'Precarioheffing',
        0.0923,
        0.09,
        'm³'
    );

-- ============================================
-- UPDATE V_GWE_VERBRUIK_COMPLEET
-- ============================================

DROP VIEW IF EXISTS v_gwe_verbruik_compleet;

CREATE VIEW v_gwe_verbruik_compleet AS
SELECT
    g.id as gwe_id,
    g.type,
    g.omschrijving,
    g.meterstand_begin,
    g.meterstand_eind,
    g.meterstand_eind - g.meterstand_begin as verbruik,
    g.eenheid,
    g.tarief,
    g.btw_pct,
    (
        g.meterstand_eind - g.meterstand_begin
    ) * g.tarief as kosten_excl_btw,
    (
        g.meterstand_eind - g.meterstand_begin
    ) * g.tarief * (1 + g.btw_pct) as kosten_incl_btw,
    b.id as boeking_id,
    b.checkin,
    b.checkout,
    h.object_id,
    h.adres,
    h.meterbeheerder,
    h.gwe_leverancier,
    k.naam as klant_naam,
    k.email as klant_email
FROM
    gwe_verbruik g
    JOIN boekingen b ON g.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;
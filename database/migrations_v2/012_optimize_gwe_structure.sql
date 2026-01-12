-- Migration: 012_optimize_gwe_structure.sql
-- Created: 2026-01-12
-- Description: Move meterstanden to boekingen, auto-calculate in view

-- ============================================
-- ADD METERSTANDEN TO BOEKINGEN (one entry per booking)
-- ============================================

ALTER TABLE boekingen ADD COLUMN elektra_begin REAL;

ALTER TABLE boekingen ADD COLUMN elektra_eind REAL;

ALTER TABLE boekingen ADD COLUMN gas_begin REAL;

ALTER TABLE boekingen ADD COLUMN gas_eind REAL;

ALTER TABLE boekingen ADD COLUMN water_begin REAL;

ALTER TABLE boekingen ADD COLUMN water_eind REAL;

-- ============================================
-- SIMPLIFY GWE_VERBRUIK TABLE
-- Now just needs: type, omschrijving, tarief, eenheid, btw_pct
-- Verbruik/dagen comes from booking
-- ============================================

-- First, let's create a new simpler gwe_regels table
CREATE TABLE IF NOT EXISTS gwe_regels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    type TEXT NOT NULL, -- Water, Gas, Elektra
    omschrijving TEXT NOT NULL, -- levering, vastrecht, enkel tarief, etc.
    tarief REAL DEFAULT 0,
    btw_pct REAL DEFAULT 0.21,
    eenheid TEXT NOT NULL, -- 'm³', 'kWh', 'dag'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES boekingen (id)
);

-- ============================================
-- VIEW: V_GWE_REGELS_COMPLEET
-- Auto-calculates verbruik/dagen based on eenheid
-- ============================================

DROP VIEW IF EXISTS v_gwe_regels_compleet;

CREATE VIEW v_gwe_regels_compleet AS
SELECT
    g.id as gwe_id,
    g.type,
    g.omschrijving,
    g.tarief,
    g.btw_pct,
    g.eenheid,
    -- Auto calculate aantal based on eenheid
    CASE g.eenheid
        WHEN 'dag' THEN julianday(b.checkout) - julianday(b.checkin)
        WHEN 'kWh' THEN b.elektra_eind - b.elektra_begin
        WHEN 'm³' THEN CASE g.type
            WHEN 'Water' THEN b.water_eind - b.water_begin
            WHEN 'Gas' THEN b.gas_eind - b.gas_begin
            ELSE 0
        END
        ELSE 0
    END as aantal,
    -- Calculate costs
    CASE g.eenheid
        WHEN 'dag' THEN (
            julianday(b.checkout) - julianday(b.checkin)
        ) * g.tarief
        WHEN 'kWh' THEN (
            b.elektra_eind - b.elektra_begin
        ) * g.tarief
        WHEN 'm³' THEN CASE g.type
            WHEN 'Water' THEN (b.water_eind - b.water_begin) * g.tarief
            WHEN 'Gas' THEN (b.gas_eind - b.gas_begin) * g.tarief
            ELSE 0
        END
        ELSE 0
    END as kosten_excl_btw,
    -- With BTW
    CASE g.eenheid
        WHEN 'dag' THEN (
            julianday(b.checkout) - julianday(b.checkin)
        ) * g.tarief * (1 + g.btw_pct)
        WHEN 'kWh' THEN (
            b.elektra_eind - b.elektra_begin
        ) * g.tarief * (1 + g.btw_pct)
        WHEN 'm³' THEN CASE g.type
            WHEN 'Water' THEN (b.water_eind - b.water_begin) * g.tarief * (1 + g.btw_pct)
            WHEN 'Gas' THEN (b.gas_eind - b.gas_begin) * g.tarief * (1 + g.btw_pct)
            ELSE 0
        END
        ELSE 0
    END as kosten_incl_btw,
    -- Booking/house/client context
    b.id as boeking_id,
    b.checkin,
    b.checkout,
    julianday(b.checkout) - julianday(b.checkin) as dagen,
    b.elektra_begin,
    b.elektra_eind,
    b.gas_begin,
    b.gas_eind,
    b.water_begin,
    b.water_eind,
    h.object_id,
    h.adres,
    k.naam as klant_naam
FROM
    gwe_regels g
    JOIN boekingen b ON g.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;
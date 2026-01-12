-- Migration: 006_add_context_views.sql
-- Created: 2026-01-12
-- Description: Add human-readable context views for damages, gwe_usage, and schoonmaak

-- ============================================
-- VIEW: V_DAMAGES_COMPLETE
-- Damages with booking, house, and client context
-- ============================================

CREATE VIEW IF NOT EXISTS v_damages_complete AS
SELECT
    -- Damage details
    d.id as damage_id,
    d.omschrijving,
    d.aantal,
    d.tarief,
    d.kosten,
    d.btw_pct,
    d.kosten * (1 + d.btw_pct) as kosten_incl_btw,
    d.datum,
    -- Booking context
    b.id as booking_id,
    b.checkin,
    b.checkout,
    -- House context
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    -- Client context
    k.naam as klant_naam,
    k.email as klant_email,
    k.telefoonnummer as klant_telefoon
FROM
    damages d
    JOIN bookings b ON d.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN houses h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;

-- ============================================
-- VIEW: V_GWE_USAGE_COMPLETE
-- GWE usage with booking, house, and client context
-- ============================================

CREATE VIEW IF NOT EXISTS v_gwe_usage_complete AS
SELECT
    -- GWE details
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
    -- Booking context
    b.id as booking_id,
    b.checkin,
    b.checkout,
    -- House context
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    -- Client context
    k.naam as klant_naam,
    k.email as klant_email
FROM
    gwe_usage g
    JOIN bookings b ON g.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN houses h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;

-- ============================================
-- VIEW: V_SCHOONMAAK_COMPLETE
-- Schoonmaak with booking, house, and client context
-- ============================================

CREATE VIEW IF NOT EXISTS v_schoonmaak_complete AS
SELECT
    -- Schoonmaak details
    s.id as schoonmaak_id,
    s.kosten,
    s.datum,
    s.notities,
    -- Booking context
    b.id as booking_id,
    b.checkin,
    b.checkout,
    ct.schoonmaak_pakket,
    -- House context
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    -- Client context
    k.naam as klant_naam,
    k.email as klant_email
FROM
    schoonmaak s
    JOIN bookings b ON s.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN houses h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;
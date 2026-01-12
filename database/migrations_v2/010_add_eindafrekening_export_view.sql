-- Migration: 010_add_eindafrekening_export_view.sql
-- Created: 2026-01-12
-- Description: Comprehensive view for eindafrekening export with all line types

-- ============================================
-- VIEW: V_EINDAFREKENING_EXPORT
-- Complete export with all line types (Basis, GWE, GWE_Item, Schade, Schoonmaak)
-- ============================================

DROP VIEW IF EXISTS v_eindafrekening_export;

CREATE VIEW v_eindafrekening_export AS

-- Basis row (contract/booking info)
SELECT
    h.adres,
    'Basis' as type,
    k.naam as klant_naam,
    h.object_id,
    k.id as klant_nr,
    b.checkin,
    b.checkout,
    COALESCE(
        b.borg_betaald,
        ct.borg_override,
        h.borg_standaard
    ) as borg,
    ct.gwe_verantwoordelijk as gwe_beheer,
    ct.voorschot_gwe_excl_btw as gwe_maandbedrag,
    ct.voorschot_gwe_btw_pct as gwe_btw_pct,
    ct.voorschot_gwe_excl_btw * (1 + ct.voorschot_gwe_btw_pct) as voorschot_gwe_incl,
    NULL as meterstand_begin,
    NULL as meterstand_eind,
    ct.schoonmaak_pakket,
    NULL as schoon_uren,
    NULL as kosten_type,
    NULL as eenheid,
    NULL as beschrijving,
    NULL as aantal,
    NULL as prijs_stuk,
    NULL as totaal_excl,
    NULL as btw_pct,
    NULL as btw_bedrag,
    NULL as totaal_incl,
    b.id as boeking_id
FROM
    boekingen b
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id
UNION ALL

-- GWE summary row
SELECT
    h.adres,
    'GWE' as type,
    k.naam as klant_naam,
    h.object_id,
    k.id as klant_nr,
    b.checkin,
    b.checkout,
    NULL as borg,
    NULL as gwe_beheer,
    NULL as gwe_maandbedrag,
    NULL as gwe_btw_pct,
    NULL as voorschot_gwe_incl,
    NULL as meterstand_begin,
    NULL as meterstand_eind,
    NULL as schoonmaak_pakket,
    NULL as schoon_uren,
    NULL as kosten_type,
    NULL as eenheid,
    NULL as beschrijving,
    NULL as aantal,
    NULL as prijs_stuk,
    NULL as totaal_excl,
    NULL as btw_pct,
    NULL as btw_bedrag,
    NULL as totaal_incl,
    b.id as boeking_id
FROM
    boekingen b
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id
WHERE
    EXISTS (
        SELECT 1
        FROM gwe_verbruik g
        WHERE
            g.booking_id = b.id
    )
UNION ALL

-- GWE_Item rows
SELECT
    h.adres,
    'GWE_Item' as type,
    k.naam as klant_naam,
    h.object_id,
    k.id as klant_nr,
    b.checkin,
    b.checkout,
    NULL as borg,
    NULL as gwe_beheer,
    NULL as gwe_maandbedrag,
    NULL as gwe_btw_pct,
    NULL as voorschot_gwe_incl,
    g.meterstand_begin,
    g.meterstand_eind,
    NULL as schoonmaak_pakket,
    NULL as schoon_uren,
    g.type as kosten_type,
    g.eenheid,
    g.omschrijving as beschrijving,
    g.meterstand_eind - g.meterstand_begin as aantal,
    g.tarief as prijs_stuk,
    (
        g.meterstand_eind - g.meterstand_begin
    ) * g.tarief as totaal_excl,
    g.btw_pct,
    (
        g.meterstand_eind - g.meterstand_begin
    ) * g.tarief * g.btw_pct as btw_bedrag,
    (
        g.meterstand_eind - g.meterstand_begin
    ) * g.tarief * (1 + g.btw_pct) as totaal_incl,
    b.id as boeking_id
FROM
    gwe_verbruik g
    JOIN boekingen b ON g.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id
UNION ALL

-- Schoonmaak rows
SELECT
    h.adres,
    'Schoonmaak' as type,
    k.naam as klant_naam,
    h.object_id,
    k.id as klant_nr,
    b.checkin,
    b.checkout,
    NULL as borg,
    NULL as gwe_beheer,
    NULL as gwe_maandbedrag,
    NULL as gwe_btw_pct,
    NULL as voorschot_gwe_incl,
    NULL as meterstand_begin,
    NULL as meterstand_eind,
    ct.schoonmaak_pakket,
    NULL as schoon_uren,
    NULL as kosten_type,
    NULL as eenheid,
    s.notities as beschrijving,
    NULL as aantal,
    NULL as prijs_stuk,
    s.kosten as totaal_excl,
    0.21 as btw_pct,
    s.kosten * 0.21 as btw_bedrag,
    s.kosten * 1.21 as totaal_incl,
    b.id as boeking_id
FROM
    schoonmaak s
    JOIN boekingen b ON s.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id
UNION ALL

-- Schade rows
SELECT
    h.adres,
    'Schade' as type,
    k.naam as klant_naam,
    h.object_id,
    k.id as klant_nr,
    b.checkin,
    b.checkout,
    NULL as borg,
    NULL as gwe_beheer,
    NULL as gwe_maandbedrag,
    NULL as gwe_btw_pct,
    NULL as voorschot_gwe_incl,
    NULL as meterstand_begin,
    NULL as meterstand_eind,
    NULL as schoonmaak_pakket,
    NULL as schoon_uren,
    'Overig' as kosten_type,
    NULL as eenheid,
    d.omschrijving as beschrijving,
    d.aantal,
    d.tarief as prijs_stuk,
    d.kosten as totaal_excl,
    d.btw_pct,
    d.kosten * d.btw_pct as btw_bedrag,
    d.kosten * (1 + d.btw_pct) as totaal_incl,
    b.id as boeking_id
FROM
    schades d
    JOIN boekingen b ON d.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;
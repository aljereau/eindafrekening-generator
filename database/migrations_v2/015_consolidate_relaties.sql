-- Migration: 015_consolidate_relaties.sql
-- Created: 2026-01-20
-- Description: Remove redundant klanten/eigenaren tables, create views from relaties

-- ============================================
-- CHECK FOR DATA BEFORE DROPPING (Safety)
-- ============================================
-- klanten and eigenaren should be empty - data is in relaties

-- ============================================
-- CREATE ROLE-BASED VIEWS FROM RELATIES
-- ============================================

DROP VIEW IF EXISTS v_klanten;

CREATE VIEW v_klanten AS
SELECT
    id,
    naam,
    type,
    contactpersoon,
    email,
    telefoonnummer,
    adres,
    postcode,
    plaats,
    land,
    kvk_nummer,
    btw_nummer,
    iban,
    marge_max,
    created_at
FROM relaties
WHERE
    is_klant = 1;

DROP VIEW IF EXISTS v_leveranciers;

CREATE VIEW v_leveranciers AS
SELECT
    id,
    naam,
    type,
    contactpersoon,
    email,
    telefoonnummer,
    adres,
    postcode,
    plaats,
    land,
    kvk_nummer,
    btw_nummer,
    iban,
    created_at
FROM relaties
WHERE
    is_leverancier = 1;

DROP VIEW IF EXISTS v_eigenaren;

CREATE VIEW v_eigenaren AS
SELECT
    id,
    naam,
    type,
    contactpersoon,
    email,
    telefoonnummer,
    adres,
    postcode,
    plaats,
    land,
    kvk_nummer,
    btw_nummer,
    iban,
    created_at
FROM relaties
WHERE
    is_eigenaar = 1;

-- ============================================
-- FIX v_gwe_regels_compleet
-- Change ct.klant_id -> ct.relatie_id, klanten -> relaties
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
    r.naam as klant_naam
FROM
    gwe_regels g
    JOIN boekingen b ON g.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN relaties r ON ct.relatie_id = r.id;

-- ============================================
-- FIX v_inhuur_overview to use relaties instead of eigenaren
-- ============================================

DROP VIEW IF EXISTS v_inhuur_overview;

CREATE VIEW v_inhuur_overview AS
SELECT h.object_id, h.id AS house_id, h.adres, h.postcode, h.plaats, h.woning_type, h.oppervlakte, h.aantal_slaapkamers, h.capaciteit_personen, h.facturatie_type,

-- Owner Details (from relaties)
ic.relatie_id AS eigenaar_id,
e.naam AS eigenaar_naam,
e.email AS eigenaar_email,
e.telefoonnummer AS eigenaar_telefoon,
e.iban AS eigenaar_iban,

-- Inhuur Contract
ic.start_datum AS inhuur_start,
ic.eind_datum AS inhuur_end,
CASE
    WHEN ic.eind_datum IS NULL THEN 'Onbepaalde tijd'
    WHEN ic.eind_datum < DATE('now') THEN 'Verlopen'
    ELSE 'Actief'
END AS contract_status,
ic.minimale_duur_maanden,
ic.opzegtermijn_maanden,

-- Inhuur Financial
ic.inhuur_excl_btw AS inhuur_maand_excl,
ROUND(
    ic.inhuur_excl_btw * (1 + ic.inhuur_btw_pct),
    2
) AS inhuur_maand_incl,
ic.borg AS inhuur_borg,
ic.voorschot_gwe AS inhuur_voorschot_gwe,
ic.vve_kosten,
ic.overige_kosten AS inhuur_overige,
ic.internet_kosten,

-- Verhuur
vc.huur_excl_btw AS verhuur_maand_excl,
ROUND(
    vc.huur_excl_btw * (1 + vc.huur_btw_pct),
    2
) AS verhuur_maand_incl,
vc.voorschot_gwe_excl_btw AS verhuur_voorschot_gwe,

-- Margin
(
    COALESCE(vc.huur_excl_btw, 0) - COALESCE(ic.inhuur_excl_btw, 0)
) AS marge_per_maand,
(
    (
        COALESCE(vc.huur_excl_btw, 0) - COALESCE(ic.inhuur_excl_btw, 0)
    ) * 12
) AS marge_per_jaar,
CASE
    WHEN ic.inhuur_excl_btw > 0 THEN ROUND(
        (
            (
                vc.huur_excl_btw - ic.inhuur_excl_btw
            ) / ic.inhuur_excl_btw * 100
        ),
        2
    )
    ELSE NULL
END AS marge_percentage,
ic.hovk,
ic.rechtsvorm,
ic.contract_link,
ic.notities AS contract_notities
FROM
    huizen h
    LEFT JOIN inhuur_contracten ic ON ic.house_id = h.id
    LEFT JOIN relaties e ON ic.relatie_id = e.id -- Changed from eigenaren to relaties
    LEFT JOIN verhuur_contracten vc ON vc.house_id = h.id
    AND (
        vc.end_date IS NULL
        OR vc.end_date >= DATE('now')
    )
ORDER BY h.object_id;

-- ============================================
-- DROP REDUNDANT TABLES (they are empty)
-- ============================================

DROP TABLE IF EXISTS klanten;

DROP TABLE IF EXISTS eigenaren;

-- Record this migration
INSERT OR IGNORE INTO
    schema_migrations (version)
VALUES (
        '015_consolidate_relaties.sql'
    );
-- Migration: 018_fix_v_sales.sql
-- Created: 2026-01-21
-- Description: Fix v_sales view - correct BTW calc and show latest contracts

-- ============================================
-- FIXED v_sales
-- Changes:
--   1. BTW calculation: kale*1.09 + gwe*1.21 + overige
--   2. Shows LATEST contract (not just active)
--   3. Added PPPW (price per person per week)
-- ============================================
DROP VIEW IF EXISTS v_sales;

CREATE VIEW v_sales AS
WITH
    latest_verhuur AS (
        -- Get most recent verhuur contract per house
        SELECT *, ROW_NUMBER() OVER (
                PARTITION BY
                    house_id
                ORDER BY start_date DESC, id DESC
            ) as rn
        FROM verhuur_contracten
    ),
    latest_inhuur AS (
        -- Get most recent inhuur contract per house
        SELECT *, ROW_NUMBER() OVER (
                PARTITION BY
                    house_id
                ORDER BY start_datum DESC, id DESC
            ) as rn
        FROM inhuur_contracten
    )
SELECT
    -- ========================================
    -- PROPERTY CORE INFO
    -- ========================================
    h.object_id,
    h.id AS house_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.woning_type,
    h.oppervlakte AS oppervlakte_m2,
    h.aantal_slaapkamers,
    h.capaciteit_personen,
    h.active AS huis_actief,
    h.facturatie_type,
    h.kluis_code_1,
    h.kluis_code_2,
    h.meterbeheerder,
    h.gwe_leverancier,
    h.sharepoint_folder,
    h.sharepoint_inhuur,
    h.sharepoint_verhuur,
    h.sharepoint_inhuur_overeenkomsten,
    h.borg_standaard,
    h.voorschot_gwe_standaard,
    h.voorschot_schoonmaak_standaard,

-- ========================================
-- OWNER (EIGENAAR) INFO
-- ========================================
eigenaar.id AS eigenaar_id,
eigenaar.naam AS eigenaar_naam,
eigenaar.type AS eigenaar_type,
eigenaar.contactpersoon AS eigenaar_contactpersoon,
eigenaar.email AS eigenaar_email,
eigenaar.telefoonnummer AS eigenaar_telefoon,
eigenaar.adres AS eigenaar_adres,
eigenaar.postcode AS eigenaar_postcode,
eigenaar.plaats AS eigenaar_plaats,
eigenaar.land AS eigenaar_land,
eigenaar.kvk_nummer AS eigenaar_kvk,
eigenaar.btw_nummer AS eigenaar_btw,
eigenaar.iban AS eigenaar_iban,

-- ========================================
-- INHUUR CONTRACT (latest)
-- ========================================
ic.id AS inhuur_contract_id,
ic.start_datum AS inhuur_start,
ic.eind_datum AS inhuur_eind,
CASE
    WHEN ic.id IS NULL THEN 'Geen inhuur'
    WHEN ic.eind_datum IS NULL THEN 'Onbepaalde tijd'
    WHEN ic.eind_datum < DATE('now') THEN 'Verlopen'
    ELSE 'Actief'
END AS inhuur_status,
ic.minimale_duur_maanden AS inhuur_min_duur,
ic.opzegtermijn_maanden AS inhuur_opzegtermijn,
ic.hovk AS inhuur_hovk,
ic.rechtsvorm AS inhuur_rechtsvorm,
ic.contract_link AS inhuur_contract_link,
ic.notities AS inhuur_notities,

-- Inhuur financials (what RyanRent pays to owner)
ic.kale_huur AS inhuur_kale_huur,
ic.inhuur_excl_btw AS inhuur_totaal_excl_btw,
-- FIXED BTW: kale*1.09 + gwe*1.21
ROUND(
    COALESCE(ic.kale_huur, 0) * 1.09 + COALESCE(ic.voorschot_gwe, 0) * 1.21 + COALESCE(ic.overige_kosten, 0) + COALESCE(ic.vve_kosten, 0) + COALESCE(ic.internet_kosten, 0),
    2
) AS inhuur_totaal_incl_btw,
ic.inhuur_btw_pct AS inhuur_btw_percentage,
ic.borg AS inhuur_borg,
ic.voorschot_gwe AS inhuur_voorschot_gwe,
ic.vve_kosten AS inhuur_vve_kosten,
ic.overige_kosten AS inhuur_overige_kosten,
ic.internet_kosten AS inhuur_internet_kosten,

-- ========================================
-- CURRENT TENANT (HUURDER) INFO
-- ========================================
huurder.id AS huurder_id,
huurder.naam AS huurder_naam,
huurder.type AS huurder_type,
huurder.contactpersoon AS huurder_contactpersoon,
huurder.email AS huurder_email,
huurder.telefoonnummer AS huurder_telefoon,
huurder.adres AS huurder_adres,
huurder.postcode AS huurder_postcode,
huurder.plaats AS huurder_plaats,
huurder.land AS huurder_land,
huurder.kvk_nummer AS huurder_kvk,
huurder.btw_nummer AS huurder_btw,
huurder.iban AS huurder_iban,
huurder.marge_max AS huurder_marge_max,

-- ========================================
-- VERHUUR CONTRACT (latest)
-- ========================================
vc.id AS verhuur_contract_id,
vc.start_date AS verhuur_start,
vc.end_date AS verhuur_eind,
vc.contract_duur_maanden AS verhuur_duur_maanden,
vc.contract_type AS verhuur_contract_type,
CASE
    WHEN vc.id IS NULL THEN 'Leegstand'
    WHEN vc.end_date IS NULL THEN 'Onbepaalde tijd'
    WHEN vc.end_date < DATE('now') THEN 'Verlopen'
    ELSE 'Actief'
END AS verhuur_status,

-- Verhuur financials (what RyanRent charges tenant)
vc.kale_huur AS verhuur_kale_huur,
vc.huur_excl_btw AS verhuur_totaal_excl_btw,
-- FIXED BTW: kale*1.09 + gwe*1.21
ROUND(
    COALESCE(vc.kale_huur, 0) * 1.09 + COALESCE(vc.voorschot_gwe_excl_btw, 0) * 1.21 + COALESCE(vc.overige_kosten, 0),
    2
) AS verhuur_totaal_incl_btw,
vc.huur_btw_pct AS verhuur_btw_percentage,
vc.voorschot_gwe_excl_btw AS verhuur_voorschot_gwe,
vc.voorschot_gwe_btw_pct AS verhuur_gwe_btw_percentage,
vc.overige_kosten AS verhuur_overige_kosten,
vc.eindschoonmaak_kosten AS verhuur_eindschoonmaak,
COALESCE(
    vc.borg_override,
    h.borg_standaard
) AS verhuur_borg,
vc.gwe_verantwoordelijk,

-- Package inclusions
vc.incl_stoffering,
vc.incl_meubilering,
vc.incl_internet,
vc.incl_schoonmaak_kwartaal,
vc.incl_bedlinnen,
vc.incl_tuinonderhoud,
vc.incl_eindschoonmaak,
vc.incl_afvalverwerking,
vc.schoonmaak_pakket,

-- ========================================
-- MARGIN ANALYSIS
-- ========================================
COALESCE(vc.huur_excl_btw, 0) - COALESCE(ic.inhuur_excl_btw, 0) AS marge_maand_excl_btw,
(
    COALESCE(vc.huur_excl_btw, 0) - COALESCE(ic.inhuur_excl_btw, 0)
) * 12 AS marge_jaar_excl_btw,
CASE
    WHEN COALESCE(ic.inhuur_excl_btw, 0) > 0 THEN ROUND(
        (
            (
                COALESCE(vc.huur_excl_btw, 0) - ic.inhuur_excl_btw
            ) / ic.inhuur_excl_btw
        ) * 100,
        2
    )
    ELSE NULL
END AS marge_percentage,

-- ========================================
-- PPPW (Price Per Person Per Week)
-- ========================================
CASE
    WHEN COALESCE(h.capaciteit_personen, 0) > 0 THEN ROUND(
        COALESCE(vc.huur_excl_btw, 0) / h.capaciteit_personen / 4.33,
        2
    )
    ELSE NULL
END AS verhuur_pppw,
CASE
    WHEN COALESCE(h.capaciteit_personen, 0) > 0 THEN ROUND(
        COALESCE(ic.inhuur_excl_btw, 0) / h.capaciteit_personen / 4.33,
        2
    )
    ELSE NULL
END AS inhuur_pppw,

-- ========================================
-- AVAILABILITY STATUS
-- ========================================
CASE
    WHEN h.active = 0 THEN 'Inactief'
    WHEN vc.id IS NULL THEN 'Beschikbaar'
    WHEN vc.end_date IS NULL THEN 'Verhuurd (onbepaald)'
    WHEN vc.end_date < DATE('now') THEN 'Beschikbaar'
    WHEN vc.end_date <= DATE('now', '+60 days') THEN 'Binnenkort beschikbaar'
    ELSE 'Verhuurd'
END AS beschikbaarheid_status,

-- Days until available
CASE
    WHEN vc.end_date IS NOT NULL
    AND vc.end_date > DATE('now') THEN CAST(
        julianday(vc.end_date) - julianday('now') AS INTEGER
    )
    ELSE 0
END AS dagen_tot_beschikbaar
FROM huizen h

-- Join LATEST inhuur (most recent contract)
LEFT JOIN latest_inhuur ic ON ic.house_id = h.id AND ic.rn = 1

-- Join owner details
LEFT JOIN relaties eigenaar ON ic.relatie_id = eigenaar.id

-- Join LATEST verhuur (most recent contract)
LEFT JOIN latest_verhuur vc ON vc.house_id = h.id AND vc.rn = 1

-- Join tenant details
LEFT JOIN relaties huurder ON vc.relatie_id = huurder.id
ORDER BY h.object_id;

-- Record this migration
INSERT OR IGNORE INTO
    schema_migrations (version)
VALUES ('018_fix_v_sales.sql');
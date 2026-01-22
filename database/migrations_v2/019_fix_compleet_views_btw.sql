-- Migration: 019_fix_compleet_views_btw.sql
-- Created: 2026-01-21
-- Description: Add totaal_incl_btw to v_verhuur_compleet and v_inhuur_compleet
--              BTW: huur=9%, gwe=21%

-- ============================================
-- v_verhuur_compleet - add totaal_incl_btw
-- ============================================
DROP VIEW IF EXISTS v_verhuur_compleet;

CREATE VIEW v_verhuur_compleet AS
SELECT
    v.id as verhuur_id,
    h.id as huis_id,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.woning_type,
    h.capaciteit_personen,
    h.aantal_slaapkamers,
    r.id as huurder_id,
    r.naam as huurder_naam,
    r.telefoonnummer as huurder_telefoon,
    r.email as huurder_email,
    v.contract_type,
    v.contract_duur_maanden,
    v.start_date as start_datum,
    v.end_date as eind_datum,
    -- Kale huur
    v.kale_huur,
    v.huur_btw_pct,
    ROUND(
        v.kale_huur * (
            1 + COALESCE(v.huur_btw_pct, 0.09)
        ),
        2
    ) as kale_huur_incl_btw,
    -- GWE
    v.voorschot_gwe_excl_btw,
    v.voorschot_gwe_btw_pct,
    ROUND(
        v.voorschot_gwe_excl_btw * (
            1 + COALESCE(v.voorschot_gwe_btw_pct, 0.21)
        ),
        2
    ) as voorschot_gwe_incl_btw,
    -- Overige
    v.overige_kosten,
    -- Totals
    v.huur_excl_btw as totaal_excl_btw,
    -- CORRECT BTW: kale*1.09 + gwe*1.21 + overige
    ROUND(
        COALESCE(v.kale_huur, 0) * (
            1 + COALESCE(v.huur_btw_pct, 0.09)
        ) + COALESCE(v.voorschot_gwe_excl_btw, 0) * (
            1 + COALESCE(v.voorschot_gwe_btw_pct, 0.21)
        ) + COALESCE(v.overige_kosten, 0),
        2
    ) as totaal_incl_btw,
    -- Other fields
    v.borg_override,
    COALESCE(
        v.borg_override,
        h.borg_standaard
    ) as borg,
    v.gwe_verantwoordelijk,
    v.schoonmaak_pakket,
    v.incl_stoffering,
    v.incl_meubilering,
    v.incl_internet,
    v.incl_eindschoonmaak
FROM
    verhuur_contracten v
    JOIN huizen h ON v.house_id = h.id
    JOIN relaties r ON v.relatie_id = r.id;

-- ============================================
-- v_inhuur_compleet - add totaal_incl_btw
-- ============================================
DROP VIEW IF EXISTS v_inhuur_compleet;

CREATE VIEW v_inhuur_compleet AS
SELECT
    ic.id as inhuur_id,
    h.id as huis_id,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.woning_type,
    h.capaciteit_personen,
    h.aantal_slaapkamers,
    r.id as eigenaar_id,
    r.naam as eigenaar_naam,
    r.telefoonnummer as eigenaar_telefoon,
    r.email as eigenaar_email,
    ic.start_datum,
    ic.eind_datum,
    ic.minimale_duur_maanden,
    ic.opzegtermijn_maanden,
    -- Kale huur
    ic.kale_huur,
    ic.inhuur_btw_pct,
    ROUND(
        ic.kale_huur * (
            1 + COALESCE(ic.inhuur_btw_pct, 0.09)
        ),
        2
    ) as kale_huur_incl_btw,
    -- GWE
    ic.voorschot_gwe,
    ROUND(ic.voorschot_gwe * 1.21, 2) as voorschot_gwe_incl_btw,
    -- Other costs
    ic.vve_kosten,
    ic.overige_kosten,
    ic.internet_kosten,
    -- Totals
    ic.inhuur_excl_btw as totaal_excl_btw,
    -- CORRECT BTW: kale*1.09 + gwe*1.21 + other costs
    ROUND(
        COALESCE(ic.kale_huur, 0) * (
            1 + COALESCE(ic.inhuur_btw_pct, 0.09)
        ) + COALESCE(ic.voorschot_gwe, 0) * 1.21 + COALESCE(ic.vve_kosten, 0) + COALESCE(ic.overige_kosten, 0) + COALESCE(ic.internet_kosten, 0),
        2
    ) as totaal_incl_btw,
    -- Borg
    ic.borg,
    ic.notities
FROM
    inhuur_contracten ic
    JOIN huizen h ON ic.house_id = h.id
    JOIN relaties r ON ic.relatie_id = r.id;

-- Record migration
INSERT OR IGNORE INTO
    schema_migrations (version)
VALUES (
        '019_fix_compleet_views_btw.sql'
    );
-- Migration: 009_add_huizen_details_and_vve.sql
-- Created: 2026-01-12
-- Description: Add more columns to huizen and vve_kosten to inhuur_contracten

-- ============================================
-- ADD COLUMNS TO HUIZEN
-- ============================================

ALTER TABLE huizen ADD COLUMN woning_type TEXT;

ALTER TABLE huizen ADD COLUMN oppervlakte REAL;

ALTER TABLE huizen ADD COLUMN kluis_code_1 TEXT;

ALTER TABLE huizen ADD COLUMN kluis_code_2 TEXT;

-- ============================================
-- ADD VVE_KOSTEN TO INHUUR_CONTRACTEN
-- (Extra costs on top of kale huur)
-- ============================================

ALTER TABLE inhuur_contracten ADD COLUMN vve_kosten REAL DEFAULT 0;

-- ============================================
-- UPDATE V_INHUUR_COMPLEET TO SHOW VVE_KOSTEN
-- ============================================

DROP VIEW IF EXISTS v_inhuur_compleet;

CREATE VIEW v_inhuur_compleet AS
SELECT
    ic.id as inhuur_id,
    h.id as huis_id,
    h.object_id,
    h.adres,
    h.woning_type,
    h.oppervlakte,
    h.capaciteit_personen,
    h.aantal_slaapkamers,
    h.kluis_code_1,
    h.kluis_code_2,
    l.id as eigenaar_id,
    l.naam as eigenaar_naam,
    l.telefoonnummer as eigenaar_telefoon,
    l.email as eigenaar_email,
    ic.start_datum,
    ic.eind_datum,
    ic.minimale_duur_maanden,
    ic.opzegtermijn_maanden,
    ic.hovk,
    ic.rechtsvorm,
    ic.notities,
    -- Kosten breakdown
    ic.inhuur_excl_btw as kale_huur,
    ic.vve_kosten,
    ic.inhuur_excl_btw + ic.vve_kosten as totaal_inhuur_excl_btw,
    ic.inhuur_btw_pct,
    (
        ic.inhuur_excl_btw + ic.vve_kosten
    ) * (1 + ic.inhuur_btw_pct) as totaal_inhuur_incl_btw,
    ic.borg,
    -- Per week berekening
    CASE
        WHEN COALESCE(
            (
                SELECT value
                FROM configuratie
                WHERE
                    key = 'weken_per_maand'
            ),
            4.33
        ) > 0 THEN (
            ic.inhuur_excl_btw + ic.vve_kosten
        ) / COALESCE(
            (
                SELECT value
                FROM configuratie
                WHERE
                    key = 'weken_per_maand'
            ),
            4.33
        )
        ELSE 0
    END as inhuur_per_week
FROM
    inhuur_contracten ic
    JOIN huizen h ON ic.house_id = h.id
    JOIN leveranciers l ON ic.eigenaar_id = l.id;
-- Migration: 016_add_portfolio_views.sql
-- Created: 2026-01-20
-- Updated: House-centric view with owner and client columns

-- ============================================
-- v_huizen_compleet
-- Full house list with owner and current tenant info
-- Sort by eigenaar, klant, adres, etc.
-- ============================================
DROP VIEW IF EXISTS v_huizen_compleet;

CREATE VIEW v_huizen_compleet AS
SELECT
    -- House Info
    h.object_id, h.adres, h.postcode, h.plaats, h.woning_type, h.oppervlakte, h.aantal_slaapkamers, h.capaciteit_personen, h.facturatie_type,

-- Owner (Eigenaar) Info
owner.id AS eigenaar_id,
owner.naam AS eigenaar_naam,
owner.email AS eigenaar_email,
owner.telefoonnummer AS eigenaar_telefoon,

-- Inhuur Contract (RyanRent pays to owner)
ic.inhuur_excl_btw AS inhuur_maand_excl,
ROUND(
    ic.inhuur_excl_btw * (
        1 + COALESCE(ic.inhuur_btw_pct, 0.09)
    ),
    2
) AS inhuur_maand_incl,
ic.borg AS inhuur_borg,
ic.start_datum AS inhuur_start,
ic.eind_datum AS inhuur_eind,
CASE
    WHEN ic.eind_datum IS NULL THEN 'Actief'
    WHEN ic.eind_datum < DATE('now') THEN 'Verlopen'
    ELSE 'Actief'
END AS inhuur_status,

-- Current Tenant (Klant) Info
tenant.id AS klant_id,
tenant.naam AS klant_naam,
tenant.email AS klant_email,
tenant.telefoonnummer AS klant_telefoon,

-- Verhuur Contract (Client pays to RyanRent)
vc.huur_excl_btw AS verhuur_maand_excl,
ROUND(
    vc.huur_excl_btw * (
        1 + COALESCE(vc.huur_btw_pct, 0.09)
    ),
    2
) AS verhuur_maand_incl,
vc.voorschot_gwe_excl_btw AS verhuur_voorschot_gwe,
h.borg_standaard AS verhuur_borg,
vc.start_date AS verhuur_start,
vc.end_date AS verhuur_eind,
CASE
    WHEN vc.end_date IS NULL THEN 'Actief'
    WHEN vc.end_date < DATE('now') THEN 'Verlopen'
    ELSE 'Actief'
END AS verhuur_status,

-- Margin Calculation
(
    COALESCE(vc.huur_excl_btw, 0) - COALESCE(ic.inhuur_excl_btw, 0)
) AS marge_maand,
(
    COALESCE(vc.huur_excl_btw, 0) - COALESCE(ic.inhuur_excl_btw, 0)
) * 12 AS marge_jaar,
CASE
    WHEN ic.inhuur_excl_btw > 0 THEN ROUND(
        (
            (
                vc.huur_excl_btw - ic.inhuur_excl_btw
            ) / ic.inhuur_excl_btw * 100
        ),
        1
    )
    ELSE NULL
END AS marge_pct
FROM huizen h

-- Join owner via inhuur contract
LEFT JOIN inhuur_contracten ic ON ic.house_id = h.id
LEFT JOIN relaties owner ON ic.relatie_id = owner.id

-- Join current tenant via verhuur contract (active only)
LEFT JOIN verhuur_contracten vc ON vc.house_id = h.id
AND (
    vc.end_date IS NULL
    OR vc.end_date >= DATE('now')
)
LEFT JOIN relaties tenant ON vc.relatie_id = tenant.id
ORDER BY h.object_id;

-- Record migration
INSERT OR IGNORE INTO
    schema_migrations (version)
VALUES ('016_add_portfolio_views.sql');
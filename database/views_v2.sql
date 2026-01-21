-- ============================================================================
-- Views for ryanrent_v2.db schema
-- ============================================================================

-- Drop old views that don't match v2 schema
DROP VIEW IF EXISTS v_contracts_overview;

DROP VIEW IF EXISTS v_facturen_februari_2026;

DROP VIEW IF EXISTS v_inhuur_overview;

-- ============================================================================
-- v_contracts_overview (v2 schema)
-- ============================================================================
CREATE VIEW v_contracts_overview AS
SELECT
    'verhuur' AS contract_type,
    vc.id AS contract_id,
    h.object_id,
    h.id AS house_id,
    h.adres,
    h.postcode,
    h.plaats,
    vc.relatie_id AS klant_id,
    r.naam AS klant_naam,
    vc.start_date,
    vc.end_date,
    vc.huur_excl_btw,
    vc.voorschot_gwe_excl_btw AS voorschot_gwe,
    h.borg_standaard AS borg,
    h.facturatie_type,
    CASE
        WHEN vc.end_date IS NULL
        OR vc.end_date >= DATE('now') THEN 1
        ELSE 0
    END AS is_active
FROM
    verhuur_contracten vc
    JOIN huizen h ON vc.house_id = h.id
    LEFT JOIN relaties r ON vc.relatie_id = r.id;

-- ============================================================================
-- v_facturen_februari_2026 (v2 schema)
-- Show all active properties with facturatie_type tag
-- ============================================================================
CREATE VIEW v_facturen_februari_2026 AS
SELECT
    h.object_id,
    h.id AS house_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.facturatie_type, -- Tag: 'Factuur', 'DS', or NULL
    vc.relatie_id AS klant_id,
    r.naam AS klant_naam,
    vc.huur_excl_btw,
    vc.voorschot_gwe_excl_btw AS voorschot_gwe,
    vc.start_date,
    vc.end_date,
    ROUND(
        vc.huur_excl_btw * (1 + vc.huur_btw_pct),
        2
    ) AS huur_incl_btw,
    '2026-02-01' AS factuur_periode_start,
    '2026-02-28' AS factuur_periode_eind
FROM
    huizen h
    LEFT JOIN verhuur_contracten vc ON vc.house_id = h.id
    LEFT JOIN relaties r ON vc.relatie_id = r.id
WHERE
    -- Active contracts
    (
        vc.end_date IS NULL
        OR vc.end_date >= '2026-02-01'
    )
    AND vc.start_date <= '2026-02-28'
ORDER BY h.facturatie_type NULLS LAST, h.object_id;

-- ============================================================================
-- v_inhuur_overview (v2 schema)
-- Comprehensive view of properties with owner/contract details
-- ============================================================================
CREATE VIEW v_inhuur_overview AS
SELECT
    -- Property Details
    h.object_id, h.id AS house_id, h.adres, h.postcode, h.plaats, h.woning_type, h.oppervlakte, h.aantal_slaapkamers, h.capaciteit_personen, h.facturatie_type,

-- Owner Details (from eigenaren via relatie_id)
ic.relatie_id AS eigenaar_id,
e.naam AS eigenaar_naam,
e.email AS eigenaar_email,
e.telefoonnummer AS eigenaar_telefoon,
e.iban AS eigenaar_iban,

-- Inhuur Contract Information
ic.start_datum AS inhuur_start,
ic.eind_datum AS inhuur_end,
CASE
    WHEN ic.eind_datum IS NULL THEN 'Onbepaalde tijd'
    WHEN ic.eind_datum < DATE('now') THEN 'Verlopen'
    ELSE 'Actief'
END AS contract_status,
ic.minimale_duur_maanden,
ic.opzegtermijn_maanden,

-- Inhuur Financial (what RyanRent pays to owner)
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

-- Verhuur (what RyanRent charges tenants)
vc.huur_excl_btw AS verhuur_maand_excl,
ROUND(
    vc.huur_excl_btw * (1 + vc.huur_btw_pct),
    2
) AS verhuur_maand_incl,
vc.voorschot_gwe_excl_btw AS verhuur_voorschot_gwe,

-- Margin calculation
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

-- Contract metadata
ic.hovk,
ic.rechtsvorm,
ic.contract_link,
ic.notities AS contract_notities
FROM
    huizen h
    LEFT JOIN inhuur_contracten ic ON ic.house_id = h.id
    LEFT JOIN eigenaren e ON ic.relatie_id = e.id
    LEFT JOIN verhuur_contracten vc ON vc.house_id = h.id
    AND (
        vc.end_date IS NULL
        OR vc.end_date >= DATE('now')
    )
ORDER BY h.object_id;
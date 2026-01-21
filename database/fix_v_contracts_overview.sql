-- Fix v_contracts_overview to use correct column names for both tables
DROP VIEW IF EXISTS v_contracts_overview;

CREATE VIEW v_contracts_overview AS
SELECT
    'verhuur' AS contract_type,
    vc.id AS contract_id,
    vc.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    r.id AS klant_id,
    r.naam AS klant_naam,
    vc.start_datum AS start_date,
    vc.eind_datum AS end_date,
    vc.kale_huur,
    vc.servicekosten,
    vc.voorschot_gwe,
    vc.overige_kosten,
    vc.kale_huur AS kale_verhuurprijs,
    vc.verhuur_excl_btw,
    vc.borg,
    CASE
        WHEN vc.status = 'active'
        AND vc.verhuur_excl_btw > 0 THEN 1
        ELSE 0
    END AS is_active,
    NULL AS inhuur_prijs,
    vc.verhuur_excl_btw AS revenue_per_month
FROM
    verhuur_contracten vc
    JOIN huizen h ON vc.object_id = h.object_id
    LEFT JOIN relaties r ON vc.klant_id = r.id
UNION ALL
SELECT
    'inhuur' AS contract_type,
    ic.id AS contract_id,
    ic.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    l.id AS klant_id,
    l.naam AS klant_naam, -- eigenaar
    ic.start_date,
    ic.end_date,
    ic.kale_huur,
    ic.servicekosten,
    ic.voorschot_gwe,
    0 AS overige_kosten,
    ic.kale_inhuurprijs AS kale_verhuurprijs,
    ic.inhuur_prijs_excl_btw AS verhuur_excl_btw,
    ic.borg,
    CASE
        WHEN ic.inhuur_prijs_excl_btw > 0 THEN 1
        ELSE 0
    END AS is_active,
    ic.inhuur_prijs_excl_btw AS inhuur_prijs,
    - ic.inhuur_prijs_excl_btw AS revenue_per_month -- cost, so negative
FROM
    inhuur_contracten ic
    JOIN huizen h ON ic.object_id = h.object_id
    LEFT JOIN leveranciers l ON ic.leverancier_id = l.id;
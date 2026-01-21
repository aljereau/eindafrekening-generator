-- ============================================================================
-- v_inhuur_overview (FIXED)
-- Comprehensive view of rental properties with owner and contract details
-- ============================================================================

DROP VIEW IF EXISTS v_inhuur_overview;

CREATE VIEW v_inhuur_overview AS
SELECT
    -- Property Details
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.woning_type,
    h.oppervlakte,
    h.aantal_sk as slaapkamers,
    h.aantal_pers as max_personen,
    h.status as property_status,
    h.facturatie_type,

-- Owner Details (leverancier = eigenaar in this context)
ic.leverancier_id as eigenaar_id,
r.naam as eigenaar_naam,
r.email as eigenaar_email,
r.telefoonnummer as eigenaar_telefoon,
r.iban as eigenaar_iban,
r.contactpersoon as eigenaar_contactpersoon,

-- Contract Information
ic.start_date as contract_start,
ic.end_date as contract_end,
CASE
    WHEN ic.end_date IS NULL THEN 'Onbepaalde tijd'
    WHEN ic.end_date < DATE('now') THEN 'Verlopen'
    ELSE 'Actief'
END as contract_status,
CAST(
    JULIANDAY(
        COALESCE(ic.end_date, DATE('now'))
    ) - JULIANDAY(ic.start_date) AS INTEGER
) / 365.25 as contract_jaren,
ic.opzegtermijn as opzegtermijn_maanden,

-- Financial Details (what RyanRent pays to owner)
ic.inhuur_prijs_excl_btw as inhuur_maand_excl,
ic.inhuur_prijs_incl_btw as inhuur_maand_incl,
ic.kale_inhuurprijs,
ic.kale_huur,
ic.servicekosten,
ic.voorschot_gwe as inhuur_voorschot_gwe,
ic.afval_kosten,
ic.totale_huur,
ic.borg as inhuur_borg,
ic.inhuur_prijs_excl_btw * 12 as inhuur_jaar_excl,
ic.inhuur_prijs_incl_btw * 12 as inhuur_jaar_incl,

-- Additional property costs
h.voorschot_gwe as property_voorschot_gwe,
h.borg as property_borg,
h.vve_kosten,
h.kosten_gem_heffingen_standaard as gem_heffingen,
h.kosten_operationeel_standaard as operationeel,

-- Verhuur pricing (what RyanRent charges to tenants)
vc.verhuur_excl_btw as verhuur_maand_excl,
(vc.verhuur_excl_btw * 1.21) as verhuur_maand_incl,
vc.kale_verhuurprijs,
vc.voorschot_gwe as verhuur_voorschot_gwe,
vc.overige_kosten as verhuur_overige_kosten,

-- Margin calculation
(
    COALESCE(vc.verhuur_excl_btw, 0) - COALESCE(ic.inhuur_prijs_excl_btw, 0)
) as marge_per_maand,
(
    (
        COALESCE(vc.verhuur_excl_btw, 0) - COALESCE(ic.inhuur_prijs_excl_btw, 0)
    ) * 12
) as marge_per_jaar,
CASE
    WHEN ic.inhuur_prijs_excl_btw > 0 THEN ROUND(
        (
            (
                vc.verhuur_excl_btw - ic.inhuur_prijs_excl_btw
            ) / ic.inhuur_prijs_excl_btw * 100
        ),
        2
    )
    ELSE NULL
END as marge_percentage,

-- Contract metadata
ic.contract_bestand,
ic.notities as contract_notities,
ic.facturatie as inhuur_facturatie_type,
ic.aangemaakt_op as contract_aangemaakt,
ic.gewijzigd_op as contract_gewijzigd,
h.aangemaakt_op as property_aangemaakt
FROM
    huizen h
    LEFT JOIN inhuur_contracten ic ON h.object_id = ic.object_id
    LEFT JOIN leveranciers r ON ic.leverancier_id = r.id
    LEFT JOIN v_contracts_overview vc ON h.object_id = vc.object_id
    AND vc.is_active = 1
WHERE
    h.status = 'active'
ORDER BY h.object_id;
-- ============================================================================
-- v_facturen_februari_2026
-- View for generating February 2026 invoices (shows ALL properties with facturatie_type tag)
-- ============================================================================

DROP VIEW IF EXISTS v_facturen_februari_2026;

CREATE VIEW v_facturen_februari_2026 AS
SELECT
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.facturatie_type, -- Tag: 'Factuur', 'DS', or empty
    vc.klant_id,
    vc.klant_naam,
    vc.verhuur_excl_btw,
    vc.kale_verhuurprijs,
    vc.voorschot_gwe,
    vc.overige_kosten,
    vc.start_date,
    vc.end_date,
    vc.is_active,
    -- Calculate monthly invoice amount
    (
        COALESCE(vc.verhuur_excl_btw, 0) * 1.21
    ) as maand_bedrag_incl_btw,
    -- Invoice period
    '2026-02-01' as factuur_periode_start,
    '2026-02-28' as factuur_periode_eind
FROM
    huizen h
    LEFT JOIN v_contracts_overview vc ON h.object_id = vc.object_id
WHERE
    -- Active properties
    h.status = 'active'
    -- Active contracts in February 2026
    AND vc.is_active = 1
    AND vc.verhuur_excl_btw > 0
ORDER BY h.facturatie_type, h.object_id;
-- Migration: 008_move_capaciteit_to_huizen.sql
-- Created: 2026-01-12
-- Description: Move capaciteit_personen from verhuur_contracten to huizen (source of truth)

-- ============================================
-- ADD COLUMNS TO HUIZEN
-- ============================================

ALTER TABLE huizen ADD COLUMN capaciteit_personen INTEGER;

ALTER TABLE huizen ADD COLUMN aantal_slaapkamers INTEGER;

-- ============================================
-- UPDATE VIEWS TO PULL CAPACITEIT FROM HUIZEN
-- ============================================

-- Drop and recreate v_boekingen_compleet
DROP VIEW IF EXISTS v_boekingen_compleet;

CREATE VIEW v_boekingen_compleet AS
SELECT
    b.id as boeking_id,
    b.checkin,
    b.checkout,
    julianday(b.checkout) - julianday(b.checkin) as dagen,
    b.status,
    k.id as klant_id,
    k.naam as klant_naam,
    k.email as klant_email,
    h.id as huis_id,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    h.capaciteit_personen, -- ← Now from huizen
    h.aantal_slaapkamers, -- ← Now from huizen
    COALESCE(
        b.borg_betaald,
        ct.borg_override,
        h.borg_standaard
    ) as borg,
    COALESCE(
        b.voorschot_gwe_betaald,
        ct.voorschot_gwe_excl_btw * (1 + ct.voorschot_gwe_btw_pct),
        h.voorschot_gwe_standaard
    ) as voorschot_gwe,
    COALESCE(
        b.voorschot_schoonmaak_betaald,
        h.voorschot_schoonmaak_standaard
    ) as voorschot_schoonmaak,
    ct.gwe_verantwoordelijk,
    ct.schoonmaak_pakket,
    ct.incl_eindschoonmaak,
    ct.huur_excl_btw,
    ct.voorschot_gwe_excl_btw
FROM
    boekingen b
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN klanten k ON ct.klant_id = k.id
    JOIN huizen h ON ct.house_id = h.id;

-- Recreate v_eindafrekening (depends on v_boekingen_compleet)
DROP VIEW IF EXISTS v_eindafrekening;

CREATE VIEW v_eindafrekening AS
SELECT
    bc.*,
    COALESCE(
        (
            SELECT SUM(kosten * (1 + btw_pct))
            FROM schades
            WHERE
                booking_id = bc.boeking_id
        ),
        0
    ) as totaal_schades_incl,
    COALESCE(
        (
            SELECT SUM(
                    (
                        meterstand_eind - meterstand_begin
                    ) * tarief * (1 + btw_pct)
                )
            FROM gwe_verbruik
            WHERE
                booking_id = bc.boeking_id
        ),
        0
    ) as totaal_gwe_incl,
    COALESCE(
        (
            SELECT SUM(kosten)
            FROM schoonmaak
            WHERE
                booking_id = bc.boeking_id
        ),
        0
    ) as totaal_schoonmaak
FROM v_boekingen_compleet bc;

-- Note: verhuur_contracten.capaciteit_personen can be removed in a future migration
-- For now, we keep it for backwards compatibility but views use huizen.capaciteit_personen
-- Migration: 007_rename_to_dutch.sql
-- Created: 2026-01-12
-- Description: Rename tables and views to Dutch for consistency

-- ============================================
-- RENAME TABLES TO DUTCH
-- ============================================

-- houses → huizen
ALTER TABLE houses RENAME TO huizen;

-- bookings → boekingen
ALTER TABLE bookings RENAME TO boekingen;

-- damages → schades
ALTER TABLE damages RENAME TO schades;

-- gwe_usage → gwe_verbruik
ALTER TABLE gwe_usage RENAME TO gwe_verbruik;

-- ============================================
-- RECREATE VIEWS WITH DUTCH NAMES
-- ============================================

-- Drop old views
DROP VIEW IF EXISTS v_booking_complete;

DROP VIEW IF EXISTS v_eindafrekening;

DROP VIEW IF EXISTS v_damages_complete;

DROP VIEW IF EXISTS v_gwe_usage_complete;

DROP VIEW IF EXISTS v_schoonmaak_complete;

DROP VIEW IF EXISTS v_inhuur_complete;

-- v_boekingen_compleet (was v_booking_complete)
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
    ct.capaciteit_personen,
    ct.huur_excl_btw,
    ct.voorschot_gwe_excl_btw
FROM
    boekingen b
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN klanten k ON ct.klant_id = k.id
    JOIN huizen h ON ct.house_id = h.id;

-- v_eindafrekening (updated with new table names)
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

-- v_schades_compleet (was v_damages_complete)
CREATE VIEW v_schades_compleet AS
SELECT
    d.id as schade_id,
    d.omschrijving,
    d.aantal,
    d.tarief,
    d.kosten,
    d.btw_pct,
    d.kosten * (1 + d.btw_pct) as kosten_incl_btw,
    d.datum,
    b.id as boeking_id,
    b.checkin,
    b.checkout,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    k.naam as klant_naam,
    k.email as klant_email,
    k.telefoonnummer as klant_telefoon
FROM
    schades d
    JOIN boekingen b ON d.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;

-- v_gwe_verbruik_compleet (was v_gwe_usage_complete)
CREATE VIEW v_gwe_verbruik_compleet AS
SELECT
    g.id as gwe_id,
    g.type,
    g.omschrijving,
    g.meterstand_begin,
    g.meterstand_eind,
    g.meterstand_eind - g.meterstand_begin as verbruik,
    g.eenheid,
    g.tarief,
    g.btw_pct,
    (
        g.meterstand_eind - g.meterstand_begin
    ) * g.tarief as kosten_excl_btw,
    (
        g.meterstand_eind - g.meterstand_begin
    ) * g.tarief * (1 + g.btw_pct) as kosten_incl_btw,
    b.id as boeking_id,
    b.checkin,
    b.checkout,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    k.naam as klant_naam,
    k.email as klant_email
FROM
    gwe_verbruik g
    JOIN boekingen b ON g.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;

-- v_schoonmaak_compleet (updated with new table names)
CREATE VIEW v_schoonmaak_compleet AS
SELECT
    s.id as schoonmaak_id,
    s.kosten,
    s.datum,
    s.notities,
    b.id as boeking_id,
    b.checkin,
    b.checkout,
    ct.schoonmaak_pakket,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    k.naam as klant_naam,
    k.email as klant_email
FROM
    schoonmaak s
    JOIN boekingen b ON s.booking_id = b.id
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN huizen h ON ct.house_id = h.id
    JOIN klanten k ON ct.klant_id = k.id;

-- v_inhuur_compleet (updated with new table names)
CREATE VIEW v_inhuur_compleet AS
SELECT
    ic.id as inhuur_id,
    h.id as huis_id,
    h.object_id,
    h.adres,
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
    ic.inhuur_excl_btw,
    ic.inhuur_btw_pct,
    ic.borg,
    ic.inhuur_excl_btw * (1 + ic.inhuur_btw_pct) as inhuur_incl_btw,
    CASE
        WHEN COALESCE(
            (
                SELECT value
                FROM configuratie
                WHERE
                    key = 'weken_per_maand'
            ),
            4.33
        ) > 0 THEN ic.inhuur_excl_btw / COALESCE(
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
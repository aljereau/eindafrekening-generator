-- Migration: 005_add_inhuur_contracten.sql
-- Created: 2026-01-12
-- Description: Add inhuur_contracten table for house-owner (leverancier) relationships

-- ============================================
-- TABLE: INHUUR_CONTRACTEN
-- Links houses to their owners (leveranciers)
-- ============================================

CREATE TABLE IF NOT EXISTS inhuur_contracten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    house_id INTEGER NOT NULL,
    eigenaar_id INTEGER NOT NULL,  -- FK to leveranciers (owner)

-- Pricing
inhuur_excl_btw REAL DEFAULT 0, -- Monthly rent excl VAT
inhuur_btw_pct REAL DEFAULT 0.09, -- VAT percentage (9% or 21%)
borg REAL DEFAULT 0, -- Deposit (kale inhuurprijs borg)

-- Contract Period
start_datum DATE,
eind_datum DATE,
minimale_duur_maanden INTEGER, -- Minimum contract duration
opzegtermijn_maanden INTEGER DEFAULT 1,

-- Contract Details
hovk TEXT,                             -- HOVK reference
    rechtsvorm TEXT,                       -- Legal form of owner
    contract_link TEXT,                    -- Link to contract document
    notities TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (house_id) REFERENCES houses(id),
    FOREIGN KEY (eigenaar_id) REFERENCES leveranciers(id)
);

-- ============================================
-- VIEW: V_INHUUR_COMPLETE
-- Calculated fields + pulled in data
-- ============================================

CREATE VIEW IF NOT EXISTS v_inhuur_complete AS
SELECT
    ic.id as inhuur_id,
    -- House info
    h.id as house_id,
    h.object_id,
    h.adres,
    -- Eigenaar (pulled from leveranciers)
    l.id as eigenaar_id,
    l.naam as eigenaar_naam,
    l.telefoonnummer as eigenaar_telefoon,
    l.email as eigenaar_email,
    -- Contract terms
    ic.start_datum,
    ic.eind_datum,
    ic.minimale_duur_maanden,
    ic.opzegtermijn_maanden,
    ic.hovk,
    ic.rechtsvorm,
    ic.notities,
    -- Pricing (stored)
    ic.inhuur_excl_btw,
    ic.inhuur_btw_pct,
    ic.borg,
    -- Pricing (calculated)
    ic.inhuur_excl_btw * (1 + ic.inhuur_btw_pct) as inhuur_incl_btw,
    -- Per persoon per week (needs house capacity, use config for weken_per_maand)
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
    JOIN houses h ON ic.house_id = h.id
    JOIN leveranciers l ON ic.eigenaar_id = l.id;
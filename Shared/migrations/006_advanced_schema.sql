-- Migration 006: Advanced Schema
-- Adds Margins, Client Parameters, Real Occupancy, Deposit Tracking, and Operations.

-- ==========================================
-- 1. KLANTEN (Margins)
-- ==========================================
-- SQLite doesn't support adding multiple columns in one statement easily in all versions,
-- but separate statements work fine.
ALTER TABLE klanten ADD COLUMN min_marge_pct REAL;

ALTER TABLE klanten ADD COLUMN max_marge_pct REAL;

-- ==========================================
-- 2. KLANT PARAMETERS (Client Specific Overrides)
-- ==========================================
CREATE TABLE IF NOT EXISTS klant_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    klant_id INTEGER NOT NULL,
    parameter_id INTEGER NOT NULL,

-- Override settings
prijs_pp_pw_override REAL,          -- NULL = use master price
    is_actief BOOLEAN DEFAULT 1,        -- per client toggle

    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (klant_id) REFERENCES klanten(id),
    FOREIGN KEY (parameter_id) REFERENCES parameters(id),

    UNIQUE(klant_id, parameter_id)
);

-- ==========================================
-- 3. PERSONEN (Real Occupants)
-- ==========================================
CREATE TABLE IF NOT EXISTS personen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voornaam TEXT,
    achternaam TEXT,
    extern_referentienummer TEXT, -- e.g. Tradiro ID
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 4. VERBLIJVEN (Stays)
-- Links a person to a booking for a specific period
-- ==========================================
CREATE TABLE IF NOT EXISTS verblijven (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    boeking_id INTEGER NOT NULL,
    persoon_id INTEGER NOT NULL,
    start_datum DATE NOT NULL,
    eind_datum DATE NOT NULL,
    FOREIGN KEY (boeking_id) REFERENCES boekingen (id),
    FOREIGN KEY (persoon_id) REFERENCES personen (id)
);

-- ==========================================
-- 5. BORGBEHEER (Deposit Transactions)
-- ==========================================
CREATE TABLE IF NOT EXISTS borg_transacties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    boeking_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    type TEXT NOT NULL, -- 'ontvangst', 'terugbetaling', 'inhouding'
    bedrag REAL NOT NULL,
    reden TEXT,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (boeking_id) REFERENCES boekingen (id)
);

-- ==========================================
-- 6. OPERATIONS (Check-in / Check-out)
-- ==========================================
CREATE TABLE IF NOT EXISTS checkins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    boeking_id INTEGER NOT NULL,
    datum DATE NOT NULL,
    uitgevoerd_door TEXT,
    sleutelset TEXT,
    notities TEXT,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (boeking_id) REFERENCES boekingen (id)
);

CREATE TABLE IF NOT EXISTS checkouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    boeking_id INTEGER NOT NULL,
    datum_gepland DATE,
    datum_werkelijk DATE,
    uitgevoerd_door TEXT,
    schade_geschat REAL,
    schoonmaak_kosten REAL,
    notities TEXT,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (boeking_id) REFERENCES boekingen (id)
);
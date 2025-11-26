-- Migration 003: Huizeninventaris Schema
-- Clean Dutch schema for managing the fleet (Huizen, Eigenaren, InhuurContracten)

-- 1. HUIZEN (Properties)
CREATE TABLE IF NOT EXISTS huizen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL UNIQUE, -- The key identifier (e.g. "0011")
    adres TEXT NOT NULL,
    postcode TEXT,
    plaats TEXT,
    woning_type TEXT,
    oppervlakte REAL,
    aantal_sk INTEGER, -- Aantal slaapkamers
    aantal_pers INTEGER, -- Capaciteit
    status TEXT DEFAULT 'active', -- active, archived, maintenance
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. EIGENAREN (Owners)
CREATE TABLE IF NOT EXISTS eigenaren (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    email TEXT,
    telefoonnummer TEXT,
    iban TEXT,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. INHUUR_CONTRACTEN (Contracts with Owners)


CREATE TABLE IF NOT EXISTS inhuur_contracten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    eigenaar_id INTEGER,
    
    start_date DATE,
    end_date DATE,

-- Financials (Dutch)

kale_huur REAL DEFAULT 0,
    servicekosten REAL DEFAULT 0,
    voorschot_gwe REAL DEFAULT 0,
    internet_kosten REAL DEFAULT 0,
    inventaris_kosten REAL DEFAULT 0,
    afval_kosten REAL DEFAULT 0,
    schoonmaak_kosten REAL DEFAULT 0,
    
    totale_huur REAL DEFAULT 0,
    borg REAL DEFAULT 0,
    
    contract_bestand TEXT,
    notities TEXT,
    
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (property_id) REFERENCES huizen(id),
    FOREIGN KEY (eigenaar_id) REFERENCES eigenaren(id)
);

-- 4. HUIZEN_STATUS_LOG
CREATE TABLE IF NOT EXISTS huizen_status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    datum_gewijzigd DATE DEFAULT CURRENT_DATE,
    reden TEXT,
    FOREIGN KEY (property_id) REFERENCES huizen (id)
);

-- 5. INDEXES
CREATE INDEX IF NOT EXISTS idx_huizen_object_id ON huizen (object_id);

CREATE INDEX IF NOT EXISTS idx_contracten_dates ON inhuur_contracten (property_id, start_date);
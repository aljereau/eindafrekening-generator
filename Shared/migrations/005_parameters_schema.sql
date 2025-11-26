-- Migration 005: Parameters & Contract Logic
-- Adds dynamic cost parameters and links them to contracts.

-- ==========================================
-- 1. PARAMETERS (Master List)
-- e.g. "Internet", "Tuinonderhoud"
-- ==========================================
CREATE TABLE IF NOT EXISTS parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    prijs_pp_pw REAL NOT NULL, -- Price per person per week
    eenheid TEXT DEFAULT 'per_persoon_per_week',
    beschrijving TEXT,
    is_actief BOOLEAN DEFAULT 1,
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==========================================
-- 2. CONTRACT REGELS (Contract Lines)
-- Links a specific contract to a parameter, freezing the calculation.
-- ==========================================
CREATE TABLE IF NOT EXISTS contract_regels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    parameter_id INTEGER, -- Link to master (optional, for reference)

-- Snapshot of values at creation time
parameter_naam TEXT NOT NULL,
prijs_pp_pw REAL NOT NULL,
aantal_personen INTEGER NOT NULL, -- Capacity of house at creation

-- Calculated total for this line
-- Formula: prijs_pp_pw * aantal_personen * 4.33 (or 4? User said 4)
-- We will store the monthly result here.
totaal_maand_bedrag REAL NOT NULL,
    
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES verhuur_contracten(id),
    FOREIGN KEY (parameter_id) REFERENCES parameters(id)
);

-- ==========================================
-- 3. UPDATE VERHUUR CONTRACTEN
-- We need to ensure verhuur_contracten has 'operationele_kosten'
-- Since SQLite ALTER TABLE is limited, we add columns if they don't exist.
-- ==========================================
-- ALTER TABLE verhuur_contracten ADD COLUMN operationele_kosten REAL DEFAULT 0;
-- ALTER TABLE verhuur_contracten ADD COLUMN totaal_maand_bedrag REAL DEFAULT 0;
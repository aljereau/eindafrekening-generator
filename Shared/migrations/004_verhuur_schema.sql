-- Migration 004: Verhuur Schema (Contracten & Boekingen)
-- Restores the client-side rental logic, now referencing the 'huizen' table.

-- ==========================================
-- 1. VERHUUR CONTRACTEN (Rental Contracts - Outgoing)
-- Links a Client (Klant) to a House (Huis) for a specific duration and price
-- ==========================================
CREATE TABLE IF NOT EXISTS verhuur_contracten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    huis_id INTEGER NOT NULL,
    klant_id INTEGER NOT NULL,

-- Duration
start_datum DATE NOT NULL,
eind_datum DATE, -- NULL means indefinite

-- Financial Terms (Income for RyanRent)
kale_huur REAL NOT NULL,
servicekosten REAL DEFAULT 0,
borg REAL DEFAULT 0,

-- Included Services (Booleans 0/1)
inclusief_gwe BOOLEAN DEFAULT 0,
inclusief_internet BOOLEAN DEFAULT 1,
inclusief_schoonmaak BOOLEAN DEFAULT 0,

-- Contract Generation Details
betalingstermijn INTEGER DEFAULT 14, -- Days
    opzegtermijn INTEGER DEFAULT 1, -- Months
    huisregels TEXT,
    sleutels_aantal INTEGER DEFAULT 2,
    
    status TEXT DEFAULT 'active', -- active, terminated, draft
    notities TEXT,
    
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (huis_id) REFERENCES huizen(id),
    FOREIGN KEY (klant_id) REFERENCES klanten(id)
);

-- ==========================================
-- 2. BOEKINGEN (Bookings / Stays)
-- Specific instances of a stay, often linked to a contract
-- This links the "Eindafrekening" to the core system
-- ==========================================

CREATE TABLE IF NOT EXISTS boekingen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER, -- Optional, could be ad-hoc
    huis_id INTEGER NOT NULL,
    klant_id INTEGER NOT NULL,
    
    checkin_datum DATE NOT NULL,
    checkout_datum DATE NOT NULL,

-- Financials specific to this stay
totale_huur_factuur REAL,
    betaalde_borg REAL,
    
    status TEXT DEFAULT 'confirmed', -- confirmed, checked_in, checked_out, cancelled
    
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (contract_id) REFERENCES verhuur_contracten(id),
    FOREIGN KEY (huis_id) REFERENCES huizen(id),
    FOREIGN KEY (klant_id) REFERENCES klanten(id)
);

-- ==========================================
-- 3. LINK EINDAFREKENINGEN TO BOEKINGEN
-- Add boeking_id to existing table
-- ==========================================
-- Note: This might fail if column already exists from previous migrations.
-- ALTER TABLE eindafrekeningen
-- ADD COLUMN boeking_id INTEGER REFERENCES boekingen (id);
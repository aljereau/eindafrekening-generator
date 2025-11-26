-- Migration: 002_core_schema.sql
-- Description: Add Clients entity (Dutch: Klanten).

-- ==========================================
-- 1. KLANTEN (Clients)
-- ==========================================
CREATE TABLE IF NOT EXISTS klanten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    type TEXT DEFAULT 'particulier', -- particulier, zakelijk, bureau

-- Contact Info
contactpersoon TEXT,
email TEXT,
telefoonnummer TEXT,
adres TEXT,

-- Financial Info
kvk_nummer TEXT,
    btw_nummer TEXT,
    iban TEXT,
    
    aangemaakt_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    gewijzigd_op TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
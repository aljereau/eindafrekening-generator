-- Migration: Add eindafrekening support to database
-- Date: 2024-12-02

-- Add columns to boekingen table
-- ALTER TABLE boekingen ADD COLUMN voorschot_gwe REAL DEFAULT 0;

-- ALTER TABLE boekingen ADD COLUMN voorschot_schoonmaak REAL DEFAULT 0;

-- ALTER TABLE boekingen ADD COLUMN schoonmaak_pakket TEXT;

ALTER TABLE boekingen
ADD COLUMN settlement_generated BOOLEAN DEFAULT 0;

ALTER TABLE boekingen ADD COLUMN settlement_generated_at TIMESTAMP;

-- Create meter_readings table
CREATE TABLE IF NOT EXISTS meter_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    reading_type TEXT NOT NULL, -- 'electricity', 'gas', 'water'
    start_value REAL NOT NULL,
    end_value REAL NOT NULL,
    tariff REAL NOT NULL, -- €/unit
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES boekingen (id)
);

CREATE INDEX idx_meter_readings_booking ON meter_readings (booking_id);

-- Create damages table
CREATE TABLE IF NOT EXISTS damages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    estimated_cost REAL NOT NULL,
    btw_percentage REAL DEFAULT 21.0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES boekingen (id)
);

CREATE INDEX idx_damages_booking ON damages (booking_id);
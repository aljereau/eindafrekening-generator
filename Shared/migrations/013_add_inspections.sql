-- Migration: Add inspections table for Incheck/Outcheck planning
-- Date: 2024-12-02

CREATE TABLE IF NOT EXISTS inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    inspection_type TEXT NOT NULL, -- 'pre_inspection', 'uitcheck', 'vis', 'incheck'
    planned_date DATE,
    inspector TEXT,
    status TEXT DEFAULT 'planned', -- 'planned', 'completed', 'cancelled'
    report_link TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES boekingen (id)
);

CREATE INDEX idx_inspections_booking ON inspections (booking_id);

CREATE INDEX idx_inspections_date ON inspections (planned_date);
CREATE TABLE IF NOT EXISTS uitcheck_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    actual_date DATE,
    actual_time TIME,
    returning_to_owner BOOLEAN DEFAULT 0,
    cleaning_required BOOLEAN DEFAULT 0,
    furniture_removal BOOLEAN DEFAULT 0,
    keys_collected BOOLEAN DEFAULT 0,
    damage_reported BOOLEAN DEFAULT 0,
    settlement_status TEXT DEFAULT 'pending', -- pending, in_progress, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES boekingen (id)
);

CREATE INDEX IF NOT EXISTS idx_uitcheck_details_booking ON uitcheck_details (booking_id);
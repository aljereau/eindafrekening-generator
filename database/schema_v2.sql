-- RyanRent Database v2
-- Clean architecture with proper relationships
-- Created: 2026-01-12

-- ============================================
-- 1. CLIENTS (Klanten)
-- ============================================
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    email TEXT,
    telefoon TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. HOUSES (Huizen) - Source of defaults
-- ============================================
CREATE TABLE IF NOT EXISTS houses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT UNIQUE NOT NULL, -- e.g., "0135"
    adres TEXT NOT NULL,
    postcode TEXT,
    plaats TEXT,
    -- Standaard waarden (defaults)
    borg_standaard REAL DEFAULT 0,
    voorschot_gwe_standaard REAL DEFAULT 0,
    voorschot_schoonmaak_standaard REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 3. VERHUUR_CONTRACTEN (Rental contracts)
-- Links client to house with terms
-- ============================================
CREATE TABLE IF NOT EXISTS verhuur_contracten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    house_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    -- Who handles GWE: "client" or "ryanrent"
    gwe_verantwoordelijk TEXT DEFAULT 'ryanrent',
    -- Cleaning terms
    schoonmaak_vooraf INTEGER DEFAULT 0, -- 0=no, 1=yes
    -- Override waarden (NULL = use house default)
    borg_override REAL,
    voorschot_gwe_override REAL,
    voorschot_schoonmaak_override REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id),
    FOREIGN KEY (house_id) REFERENCES houses (id)
);

-- ============================================
-- 4. BOOKINGS (Actual rental execution)
-- ============================================
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    checkin DATE NOT NULL,
    checkout DATE NOT NULL,
    -- Actual paid amounts (NULL = use contract/house default)
    borg_betaald REAL,
    voorschot_gwe_betaald REAL,
    voorschot_schoonmaak_betaald REAL,
    status TEXT DEFAULT 'active', -- active, completed, cancelled
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES verhuur_contracten (id)
);

-- ============================================
-- 5. DAMAGES (Schade-gerelateerde kosten)
-- ============================================
CREATE TABLE IF NOT EXISTS damages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    omschrijving TEXT NOT NULL,
    aantal REAL DEFAULT 1,
    tarief REAL DEFAULT 0, -- Rate per unit (excl VAT)
    kosten REAL DEFAULT 0, -- Total (aantal × tarief)
    btw_pct REAL DEFAULT 0.21, -- VAT percentage
    datum DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings (id)
);

-- ============================================
-- 6. GWE_USAGE (Verbruik per booking)
-- ============================================
CREATE TABLE IF NOT EXISTS gwe_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    type TEXT NOT NULL, -- "Water", "Gas", "Elektra"
    omschrijving TEXT,
    verbruik REAL DEFAULT 0,
    eenheid TEXT, -- "m³", "kWh", "dag"
    tarief REAL DEFAULT 0, -- Rate (excl VAT)
    btw_pct REAL DEFAULT 0.21,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings (id)
);

-- ============================================
-- 7. SCHOONMAAK (Cleaning per booking)
-- ============================================
CREATE TABLE IF NOT EXISTS schoonmaak (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    kosten REAL DEFAULT 0,
    datum DATE,
    notities TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings (id)
);

-- ============================================
-- VIEW: Get booking with all defaults resolved
-- ============================================
CREATE VIEW IF NOT EXISTS v_booking_complete AS
SELECT
    b.id as booking_id,
    b.checkin,
    b.checkout,
    julianday(b.checkout) - julianday(b.checkin) as dagen,
    b.status,
    -- Client info
    c.id as client_id,
    c.naam as client_naam,
    c.email as client_email,
    -- House info
    h.id as house_id,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    -- Resolved values (booking → contract → house defaults)
    COALESCE(
        b.borg_betaald,
        ct.borg_override,
        h.borg_standaard
    ) as borg,
    COALESCE(
        b.voorschot_gwe_betaald,
        ct.voorschot_gwe_override,
        h.voorschot_gwe_standaard
    ) as voorschot_gwe,
    COALESCE(
        b.voorschot_schoonmaak_betaald,
        ct.voorschot_schoonmaak_override,
        h.voorschot_schoonmaak_standaard
    ) as voorschot_schoonmaak,
    -- Contract terms
    ct.gwe_verantwoordelijk,
    ct.schoonmaak_vooraf
FROM
    bookings b
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN clients c ON ct.client_id = c.id
    JOIN houses h ON ct.house_id = h.id;

-- ============================================
-- VIEW: Get eindafrekening data
-- ============================================
CREATE VIEW IF NOT EXISTS v_eindafrekening AS
SELECT
    bc.*,
    -- Damage totals
    COALESCE(
        (
            SELECT SUM(kosten * (1 + btw_pct))
            FROM damages
            WHERE
                booking_id = bc.booking_id
        ),
        0
    ) as total_damages_incl,
    -- GWE totals
    COALESCE(
        (
            SELECT SUM(
                    verbruik * tarief * (1 + btw_pct)
                )
            FROM gwe_usage
            WHERE
                booking_id = bc.booking_id
        ),
        0
    ) as total_gwe_incl,
    -- Schoonmaak totals
    COALESCE(
        (
            SELECT SUM(kosten)
            FROM schoonmaak
            WHERE
                booking_id = bc.booking_id
        ),
        0
    ) as total_schoonmaak
FROM v_booking_complete bc;
-- RyanRent Database v2 - Complete Schema
-- Migration: 001_create_all.sql
-- Created: 2026-01-12
-- Description: Definitive base schema for all tables and views

-- ============================================
-- TABLES
-- ============================================

-- KLANTEN (Customers)
CREATE TABLE IF NOT EXISTS klanten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    type TEXT DEFAULT 'particulier',
    contactpersoon TEXT,
    email TEXT,
    telefoonnummer TEXT,
    adres TEXT,
    postcode TEXT,
    plaats TEXT,
    land TEXT,
    kvk_nummer TEXT,
    btw_nummer TEXT,
    iban TEXT,
    marge_max REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- LEVERANCIERS (Suppliers)
CREATE TABLE IF NOT EXISTS leveranciers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    type TEXT DEFAULT 'particulier',
    contactpersoon TEXT,
    email TEXT,
    telefoonnummer TEXT,
    adres TEXT,
    postcode TEXT,
    plaats TEXT,
    land TEXT,
    kvk_nummer TEXT,
    btw_nummer TEXT,
    iban TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- HOUSES (Properties with defaults)
CREATE TABLE IF NOT EXISTS houses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT UNIQUE NOT NULL,
    adres TEXT NOT NULL,
    postcode TEXT,
    plaats TEXT,
    borg_standaard REAL DEFAULT 0,
    voorschot_gwe_standaard REAL DEFAULT 0,
    voorschot_schoonmaak_standaard REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- CONFIGURATIE (Business settings)
CREATE TABLE IF NOT EXISTS configuratie (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value REAL,
    omschrijving TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- INVENTARIS (Products)
CREATE TABLE IF NOT EXISTS inventaris (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    inkoop_prijs REAL DEFAULT 0,
    type TEXT,
    leverancier TEXT,
    marge_override REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- DIENSTEN (Services)
CREATE TABLE IF NOT EXISTS diensten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    naam TEXT NOT NULL,
    tarief REAL DEFAULT 0,
    eenheid TEXT DEFAULT 'uur',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- VERHUUR_CONTRACTEN (Rental contracts)
CREATE TABLE IF NOT EXISTS verhuur_contracten (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    klant_id INTEGER NOT NULL,
    house_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    contract_duur_maanden INTEGER,
    capaciteit_personen INTEGER,
    huur_excl_btw REAL DEFAULT 0,
    huur_btw_pct REAL DEFAULT 0.09,
    voorschot_gwe_excl_btw REAL DEFAULT 0,
    voorschot_gwe_btw_pct REAL DEFAULT 0.21,
    borg_override REAL,
    incl_stoffering INTEGER DEFAULT 0,
    incl_meubilering INTEGER DEFAULT 0,
    incl_internet INTEGER DEFAULT 0,
    incl_schoonmaak_kwartaal INTEGER DEFAULT 0,
    incl_bedlinnen INTEGER DEFAULT 0,
    incl_tuinonderhoud INTEGER DEFAULT 0,
    incl_eindschoonmaak INTEGER DEFAULT 0,
    incl_afvalverwerking INTEGER DEFAULT 0,
    schoonmaak_pakket TEXT,
    gwe_verantwoordelijk TEXT DEFAULT 'ryanrent',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (klant_id) REFERENCES klanten (id),
    FOREIGN KEY (house_id) REFERENCES houses (id)
);

-- BOOKINGS (Rental execution)
CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    checkin DATE NOT NULL,
    checkout DATE NOT NULL,
    borg_betaald REAL,
    voorschot_gwe_betaald REAL,
    voorschot_schoonmaak_betaald REAL,
    status TEXT DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES verhuur_contracten (id)
);

-- DAMAGES (Damage costs per booking)
CREATE TABLE IF NOT EXISTS damages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    omschrijving TEXT NOT NULL,
    aantal REAL DEFAULT 1,
    tarief REAL DEFAULT 0,
    kosten REAL DEFAULT 0,
    btw_pct REAL DEFAULT 0.21,
    datum DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings (id)
);

-- GWE_USAGE (Meter readings per booking)
CREATE TABLE IF NOT EXISTS gwe_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    omschrijving TEXT,
    meterstand_begin REAL DEFAULT 0,
    meterstand_eind REAL DEFAULT 0,
    eenheid TEXT,
    tarief REAL DEFAULT 0,
    btw_pct REAL DEFAULT 0.21,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings (id)
);

-- SCHOONMAAK (Cleaning costs per booking)
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
-- VIEWS
-- ============================================

-- V_INVENTARIS_PRIJZEN (Products with calculated prices)
CREATE VIEW IF NOT EXISTS v_inventaris_prijzen AS
SELECT
    i.id,
    i.naam,
    i.inkoop_prijs,
    i.type,
    i.leverancier,
    COALESCE(i.marge_override, c.value) as marge,
    i.inkoop_prijs / (
        1 - COALESCE(i.marge_override, c.value)
    ) as verkoop_prijs
FROM inventaris i
    CROSS JOIN configuratie c
WHERE
    c.key = 'marge_inventaris_standaard';

-- V_BOOKING_COMPLETE (Booking with all details resolved)
CREATE VIEW IF NOT EXISTS v_booking_complete AS
SELECT
    b.id as booking_id,
    b.checkin,
    b.checkout,
    julianday(b.checkout) - julianday(b.checkin) as dagen,
    b.status,
    k.id as klant_id,
    k.naam as klant_naam,
    k.email as klant_email,
    h.id as house_id,
    h.object_id,
    h.adres,
    h.postcode,
    h.plaats,
    COALESCE(
        b.borg_betaald,
        ct.borg_override,
        h.borg_standaard
    ) as borg,
    COALESCE(
        b.voorschot_gwe_betaald,
        ct.voorschot_gwe_excl_btw * (1 + ct.voorschot_gwe_btw_pct),
        h.voorschot_gwe_standaard
    ) as voorschot_gwe,
    COALESCE(
        b.voorschot_schoonmaak_betaald,
        h.voorschot_schoonmaak_standaard
    ) as voorschot_schoonmaak,
    ct.gwe_verantwoordelijk,
    ct.schoonmaak_pakket,
    ct.incl_eindschoonmaak,
    ct.capaciteit_personen,
    ct.huur_excl_btw,
    ct.voorschot_gwe_excl_btw
FROM
    bookings b
    JOIN verhuur_contracten ct ON b.contract_id = ct.id
    JOIN klanten k ON ct.klant_id = k.id
    JOIN houses h ON ct.house_id = h.id;

-- V_EINDAFREKENING (Complete settlement data)
CREATE VIEW IF NOT EXISTS v_eindafrekening AS
SELECT
    bc.*,
    COALESCE(
        (
            SELECT SUM(kosten * (1 + btw_pct))
            FROM damages
            WHERE
                booking_id = bc.booking_id
        ),
        0
    ) as total_damages_incl,
    COALESCE(
        (
            SELECT SUM(
                    (
                        meterstand_eind - meterstand_begin
                    ) * tarief * (1 + btw_pct)
                )
            FROM gwe_usage
            WHERE
                booking_id = bc.booking_id
        ),
        0
    ) as total_gwe_incl,
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

-- ============================================
-- SEED DATA: CONFIGURATIE
-- ============================================

INSERT OR IGNORE INTO
    configuratie (key, value, omschrijving)
VALUES (
        'marge_inventaris_standaard',
        0.30,
        '30% marge op producten'
    ),
    (
        'marge_diensten_standaard',
        0.30,
        '30% marge op diensten'
    ),
    (
        'marge_tradiro_max',
        0.08,
        'Max 8% marge Tradiro'
    ),
    (
        'marge_min_verhuur',
        0.15,
        'Min 15% marge verhuur'
    ),
    (
        'marge_target_verhuur',
        0.25,
        'Target 25% marge verhuur'
    ),
    (
        'marge_max_andere_klanten',
        0.40,
        'Max 40% andere klanten'
    ),
    (
        'meubilering_pppw',
        15.00,
        'Meubilering €/persoon/week'
    ),
    (
        'stoffering_pppw',
        10.00,
        'Stoffering €/persoon/week'
    ),
    (
        'internet_pppw',
        5.00,
        'Internet €/persoon/week'
    ),
    (
        'bedlinnen_pppw',
        3.00,
        'Bedlinnen €/persoon/week'
    ),
    (
        'tuinonderhoud_pppw',
        2.50,
        'Tuinonderhoud €/persoon/week'
    ),
    (
        'afvalverwerking_pppw',
        2.00,
        'Afvalverwerking €/persoon/week'
    ),
    (
        'schoonmaak_basis',
        250.00,
        'Basis schoonmaakpakket'
    ),
    (
        'schoonmaak_intensief',
        375.00,
        'Intensief schoonmaakpakket'
    ),
    (
        'schoonmaak_kwartaal_pppw',
        5.00,
        'Schoonmaak kwartaal €/persoon/week'
    ),
    (
        'weken_per_maand',
        4.33,
        'Weken per maand'
    );

-- ============================================
-- SEED DATA: DIENSTEN
-- ============================================

INSERT OR IGNORE INTO
    diensten (naam, tarief, eenheid)
VALUES (
        'Arbeid Schoonmaak P/U',
        35.00,
        'uur'
    ),
    (
        'Arbeid Technish P/U',
        45.00,
        'uur'
    ),
    (
        'Afval verwerk',
        215.00,
        'keer'
    ),
    (
        'Reiskosten per km',
        0.28,
        'km'
    );

-- ============================================
-- SEED DATA: INVENTARIS (64 products)
-- ============================================

INSERT OR IGNORE INTO
    inventaris (
        naam,
        inkoop_prijs,
        type,
        leverancier
    )
VALUES (
        'Wasmachine',
        210.0,
        'huishoudelijke apparaten',
        'Strijbosch B.V.'
    ),
    (
        'Stofzuiger',
        59.0,
        'huishoudelijke apparaten',
        'Strijbosch B.V.'
    ),
    (
        'TV',
        210.0,
        'huishoudelijke apparaten',
        'Strijbosch B.V.'
    ),
    (
        'Combi Koelkast',
        295.0,
        'huishoudelijke apparaten',
        'Strijbosch B.V.'
    ),
    (
        'Combi Magnetron',
        115.0,
        'huishoudelijke apparaten',
        'Strijbosch B.V.'
    ),
    (
        'Waterkoker',
        19.0,
        'huishoudelijke apparaten',
        'Strijbosch B.V.'
    ),
    (
        'Tafel Koelkast',
        190.0,
        'huishoudelijke apparaten',
        'Strijbosch B.V.'
    ),
    (
        'Box spring',
        78.75,
        'Meubels',
        'Matex'
    ),
    (
        'Matras',
        70.75,
        'Meubels',
        'Matex'
    ),
    (
        'KleidingKast 1P',
        48.76,
        'Meubels',
        'Ikea'
    ),
    (
        'Nachtkasje',
        37.0,
        'Meubels',
        ''
    ),
    (
        'Eetkamertafel',
        41.31,
        'Meubels',
        ''
    ),
    (
        'Eetkamerstoel',
        44.5,
        'Meubels',
        ''
    ),
    (
        'TV meubel',
        62.75,
        'Meubels',
        ''
    ),
    (
        'Salontafel',
        16.52,
        'Meubels',
        'Ikea'
    ),
    (
        'Bank',
        106.0,
        'Meubels',
        'OpenGuard'
    ),
    (
        'Fauteuil',
        65.0,
        'Meubels',
        ''
    ),
    (
        'Dekbedovertrek en kussensloop',
        9.08,
        'Slaapkamer',
        'Ikea'
    ),
    (
        'Hoeslaken',
        5.78,
        'Slaapkamer',
        'Ikea'
    ),
    (
        'Dekbed',
        10.74,
        'Slaapkamer',
        'Ikea'
    ),
    (
        'Kussen',
        5.78,
        'Slaapkamer',
        'Ikea'
    ),
    (
        'Kleerhanger 10st',
        1.64,
        'Slaapkamer',
        'Ikea'
    ),
    (
        'Stekkerdoos 2st',
        4.95,
        'Slaapkamer',
        'Ikea'
    ),
    (
        'Staand droogrek',
        5.36,
        'Slaapkamer',
        'Ikea'
    ),
    (
        'Pannenset 3st',
        9.91,
        'Keukenset',
        'Ikea'
    ),
    (
        'Koekenpan 2st',
        12.39,
        'Keukenset',
        'Ikea'
    ),
    (
        'Onderzetter set',
        1.64,
        'Keukenset',
        'Ikea'
    ),
    (
        'Snijplank 2st',
        0.82,
        'Keukenset',
        'Ikea'
    ),
    (
        'Messenset 3st',
        4.95,
        'Keukenset',
        'Ikea'
    ),
    (
        'Vergiet',
        1.23,
        'Keukenset',
        'Ikea'
    ),
    (
        'Keukengerei 3st',
        1.64,
        'Keukenset',
        'Ikea'
    ),
    (
        'Oven-/serveerschaal',
        5.78,
        'Keukenset',
        'Ikea'
    ),
    (
        'Kleine stoffer en blik',
        1.89,
        'Keukenset',
        'Ikea'
    ),
    (
        'Afwasborstel',
        0.82,
        'Keukenset',
        'Ikea'
    ),
    (
        'Afdruipmat',
        2.06,
        'Keukenset',
        'Ikea'
    ),
    (
        'Theedoek 4st',
        2.47,
        'Keukenset',
        'Ikea'
    ),
    (
        'Glas 45 cl set 6 st',
        4.95,
        'Keukenset',
        'Ikea'
    ),
    (
        'Beker 1st',
        1.64,
        'Keukenset',
        'Ikea'
    ),
    (
        'Bestekbak',
        0.62,
        'Keukenset',
        'Ikea'
    ),
    (
        'Bestek 4p',
        3.71,
        'Keukenset',
        'Ikea'
    ),
    (
        'Servies 4 pers',
        12.39,
        'Keukenset',
        'Ikea'
    ),
    (
        'Toiletborstel',
        0.64,
        'Anderen + SNF',
        'Ikea'
    ),
    (
        'DoucheGordijn',
        3.3,
        'Anderen + SNF',
        'Ikea'
    ),
    (
        'DoucheGordijn Stang',
        4.12,
        'Anderen + SNF',
        'Ikea'
    ),
    (
        'Afvalemmer',
        7.4,
        'Anderen + SNF',
        'Action'
    ),
    (
        'Mopset',
        8.26,
        'Anderen + SNF',
        'Action'
    ),
    (
        'Vervangingsmop',
        2.47,
        'Anderen + SNF',
        'Action'
    ),
    (
        'Keylocker',
        29.03,
        'Anderen + SNF',
        ''
    ),
    (
        'Brandblusser',
        70.0,
        'Anderen + SNF',
        ''
    ),
    (
        'Blusdeken',
        9.95,
        'Anderen + SNF',
        ''
    ),
    (
        'Rookmelder + magneet',
        7.7,
        'Anderen + SNF',
        'Action'
    ),
    (
        'CO2 + magneet',
        15.67,
        'Anderen + SNF',
        'Action'
    ),
    (
        'Gordijnen x1 inl stang',
        48.73,
        'Anderen + SNF',
        'Ikea'
    ),
    (
        'Sleutels per stuk',
        17.5,
        'TD inventaris + diensten',
        ''
    ),
    (
        'WC bril',
        29.66,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Doucheset',
        134.0,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Afdekplaat electra',
        1.29,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Doucheslang',
        19.99,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Deurhendels',
        10.0,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Kamerdeur',
        123.21,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Raamuitzetter',
        19.99,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Lichtschakelaar',
        3.79,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Lampen',
        3.95,
        'TD inventaris + diensten',
        ''
    ),
    (
        'Plafondlamp',
        5.78,
        'TD inventaris + diensten',
        ''
    );
-- RyanRent Property Status Dashboard Schema
-- Generated from Incheck/PropertyStatusDash.md

-- 1. properties
CREATE TABLE properties (
    property_id VARCHAR(50) PRIMARY KEY,
    address VARCHAR(255) NOT NULL UNIQUE,
    property_code VARCHAR(50), -- e.g., "HUIS-135"
    owner_id VARCHAR(50),
    property_type VARCHAR(50), -- RR Eigendom, Klant Eigendom
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for properties
CREATE INDEX idx_properties_address ON properties (address);

CREATE INDEX idx_properties_code ON properties (property_code);

-- 2. clients
CREATE TABLE clients (
    client_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    client_type VARCHAR(50), -- Bureau, Direct, Eigenaar
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for clients
CREATE INDEX idx_clients_name ON clients (name);

-- 3. inspectors
CREATE TABLE inspectors (
    inspector_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. uitchecks
CREATE TABLE uitchecks (
    uitcheck_id VARCHAR(50) PRIMARY KEY,  -- UC-2025-001
    property_id VARCHAR(50) NOT NULL REFERENCES properties(property_id),
    client_id VARCHAR(50) REFERENCES clients(client_id),

-- Dates
scheduled_date DATE NOT NULL,
scheduled_time TIME,
actual_date DATE,
actual_time TIME,
pre_inspection_date DATE,

-- Assignment
inspector_id VARCHAR(50) REFERENCES inspectors (inspector_id),
pre_inspector_id VARCHAR(50) REFERENCES inspectors (inspector_id),

-- Status
status VARCHAR(50) NOT NULL, -- Gepland, Bezig, Voltooid, Geannuleerd
priority VARCHAR(50), -- Kritisch, Hoog, Normaal, Laag

-- Operational details
returning_to_owner BOOLEAN DEFAULT FALSE,
furniture_removal BOOLEAN DEFAULT FALSE,
keys_collected BOOLEAN DEFAULT FALSE,
damage_reported BOOLEAN DEFAULT FALSE,

-- Cleaning
cleaning_required VARCHAR(100), -- RR Schoonmaak, Park Schoonmaak, etc.
cleaning_paid_by VARCHAR(50), -- Huurder, RR, Eigenaar
cleaning_cost DECIMAL(10, 2),

-- Financial
settlement_status VARCHAR(50), -- Niet Gestart, In Afwachting, Bezig, Voltooid
settlement_amount DECIMAL(10, 2),

-- Notes
notes TEXT,

-- Metadata
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for uitchecks
CREATE INDEX idx_uitchecks_property ON uitchecks (property_id);

CREATE INDEX idx_uitchecks_scheduled_date ON uitchecks (scheduled_date);

CREATE INDEX idx_uitchecks_status ON uitchecks (status);

CREATE INDEX idx_uitchecks_priority ON uitchecks (priority);

CREATE INDEX idx_uitchecks_inspector ON uitchecks (inspector_id);

-- 5. inchecks
CREATE TABLE inchecks (
    incheck_id VARCHAR(50) PRIMARY KEY,  -- IC-2025-001
    property_id VARCHAR(50) NOT NULL REFERENCES properties(property_id),
    linked_uitcheck_id VARCHAR(50) REFERENCES uitchecks(uitcheck_id),

-- New tenant info
new_tenant_name VARCHAR(255),
new_tenant_company_id VARCHAR(50) REFERENCES clients (client_id),

-- Dates
planned_date DATE NOT NULL,
actual_date DATE,
vis_date DATE, -- Voor-incheck inspectie

-- Assignment
inspector_id VARCHAR(50) REFERENCES inspectors (inspector_id),
vis_inspector_id VARCHAR(50) REFERENCES inspectors (inspector_id),

-- Status
status VARCHAR(50) NOT NULL, -- Gepland, VIS Gedaan, Voltooid, Geannuleerd
vis_approved BOOLEAN, -- Did new tenant approve during VIS?

-- Reference
vis_reference TEXT, notes TEXT,

-- Metadata
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for inchecks
CREATE INDEX idx_inchecks_property ON inchecks (property_id);

CREATE INDEX idx_inchecks_linked_uitcheck ON inchecks (linked_uitcheck_id);

CREATE INDEX idx_inchecks_planned_date ON inchecks (planned_date);

CREATE INDEX idx_inchecks_status ON inchecks (status);

CREATE INDEX idx_inchecks_company ON inchecks (new_tenant_company_id);

-- 6. bookings (Optional)
CREATE TABLE bookings (
    booking_id VARCHAR(50) PRIMARY KEY,
    property_id VARCHAR(50) NOT NULL REFERENCES properties (property_id),
    client_id VARCHAR(50) REFERENCES clients (client_id),
    tenant_name VARCHAR(255),
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(50), -- Active, Ending, Ended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for bookings
CREATE INDEX idx_bookings_property ON bookings (property_id);

CREATE INDEX idx_bookings_dates ON bookings (start_date, end_date);

CREATE INDEX idx_bookings_status ON bookings (status);

-- 7. property_status_view
CREATE VIEW property_status_view AS
SELECT
    -- Property info
    p.property_id, p.address, p.property_code,

-- Uitcheck info
u.uitcheck_id,
u.scheduled_date as uitcheck_scheduled,
u.actual_date as uitcheck_actual,
u.pre_inspection_date,
u.status as uitcheck_status,
u.priority as uitcheck_priority,
u.returning_to_owner,
ui.name as uitcheck_inspector,

-- Incheck info
i.incheck_id,
i.planned_date as incheck_planned,
i.actual_date as incheck_actual,
i.vis_date,
i.vis_approved,
i.new_tenant_name,
i.status as incheck_status,
ii.name as incheck_inspector,
c.name as new_tenant_company,

-- Client info
cl.name as current_client,

-- Calculated fields
CASE
    WHEN i.planned_date IS NOT NULL THEN i.planned_date - CURRENT_DATE
    ELSE NULL
END as days_until_incheck,
CASE
    WHEN u.scheduled_date IS NOT NULL THEN u.scheduled_date - CURRENT_DATE
    ELSE NULL
END as days_until_uitcheck,

-- Priority calculation (business logic)
CASE
        -- Kritisch: Incheck within 7 days AND missing critical steps
        WHEN i.planned_date IS NOT NULL 
            AND i.planned_date - CURRENT_DATE <= 7
            AND (u.pre_inspection_date IS NULL OR i.vis_date IS NULL)
        THEN 'KRITISCH'

-- Hoog: Incheck within 14 days
WHEN i.planned_date IS NOT NULL
AND i.planned_date - CURRENT_DATE <= 14 THEN 'HOOG'

-- Normaal: Incheck within 30 days
WHEN i.planned_date IS NOT NULL
AND i.planned_date - CURRENT_DATE <= 30 THEN 'NORMAAL'

-- Laag: No new tenant or distant incheck
ELSE 'LAAG' END as calculated_priority,

-- Status completeness score (0-100)
(
    CASE
        WHEN u.uitcheck_id IS NOT NULL THEN 20
        ELSE 0
    END + CASE
        WHEN u.pre_inspection_date IS NOT NULL THEN 20
        ELSE 0
    END + CASE
        WHEN u.actual_date IS NOT NULL THEN 20
        ELSE 0
    END + CASE
        WHEN i.vis_date IS NOT NULL THEN 20
        ELSE 0
    END + CASE
        WHEN i.actual_date IS NOT NULL THEN 20
        ELSE 0
    END
) as completeness_score
FROM
    properties p
    LEFT JOIN uitchecks u ON p.property_id = u.property_id
    AND u.scheduled_date >= CURRENT_DATE - 7 -- Only recent/upcoming
    AND u.scheduled_date <= CURRENT_DATE + 30
    AND u.status != 'Voltooid'
    LEFT JOIN inchecks i ON u.uitcheck_id = i.linked_uitcheck_id
    LEFT JOIN inspectors ui ON u.inspector_id = ui.inspector_id
    LEFT JOIN inspectors ii ON i.inspector_id = ii.inspector_id
    LEFT JOIN clients cl ON u.client_id = cl.client_id
    LEFT JOIN clients c ON i.new_tenant_company_id = c.client_id
WHERE
    u.uitcheck_id IS NOT NULL -- Only properties with active uitchecks
ORDER BY
    calculated_priority DESC,
    days_until_incheck ASC;
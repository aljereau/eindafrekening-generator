-- 1. House Profitability (Historical & Projected)
-- Aggregates financial performance per house
DROP VIEW IF EXISTS view_house_profitability;

CREATE VIEW view_house_profitability AS
SELECT h.adres, h.plaats, COUNT(DISTINCT b.id) as total_bookings,

-- Income
SUM(
    IFNULL(vc.kale_huur, 0) * (
        JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
    ) / 30.0
) as est_total_revenue,

-- Costs
SUM(
    IFNULL(ic.kale_huur, 0) * (
        JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
    ) / 30.0
) as est_total_cost,

-- Damages
(
    SELECT SUM(estimated_cost)
    FROM damages d
        JOIN boekingen b2 ON d.booking_id = b2.id
    WHERE
        b2.huis_id = h.id
) as total_damages_cost,

-- Margin
(
    SUM(
        IFNULL(vc.kale_huur, 0) * (
            JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
        ) / 30.0
    ) - SUM(
        IFNULL(ic.kale_huur, 0) * (
            JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
        ) / 30.0
    )
) as est_gross_margin
FROM
    huizen h
    JOIN boekingen b ON h.id = b.huis_id
    -- Join contracts active at time of booking (Simplified: using latest for now as history is limited, 
    -- but ideally we join on date ranges. For this demo, we use the view_latest_pricing logic or just latest contracts)
    LEFT JOIN verhuur_contracten vc ON h.id = vc.huis_id
    LEFT JOIN inhuur_contracten ic ON h.id = ic.property_id
GROUP BY
    h.id;

-- 2. Client Scorecard
-- Who are the best/worst clients?
DROP VIEW IF EXISTS view_client_scorecard;

CREATE VIEW view_client_scorecard AS
SELECT
    k.naam as client_name,
    k.type as client_type,
    COUNT(b.id) as total_bookings,

-- Financials
SUM(
    IFNULL(vc.kale_huur, 0) * (
        JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
    ) / 30.0
) as total_revenue_generated,

-- Risk/Issues
(
    SELECT COUNT(*)
    FROM damages d
        JOIN boekingen b2 ON d.booking_id = b2.id
    WHERE
        b2.klant_id = k.id
) as damage_incidents,
(
    SELECT SUM(estimated_cost)
    FROM damages d
        JOIN boekingen b2 ON d.booking_id = b2.id
    WHERE
        b2.klant_id = k.id
) as total_damage_cost,

-- Average Stay
AVG(
    JULIANDAY(b.checkout_datum) - JULIANDAY(b.checkin_datum)
) as avg_stay_days
FROM
    klanten k
    JOIN boekingen b ON k.id = b.klant_id
    LEFT JOIN verhuur_contracten vc ON b.huis_id = vc.huis_id
    AND b.klant_id = vc.klant_id
GROUP BY
    k.id
ORDER BY total_revenue_generated DESC;

-- 3. Operational Dashboard
-- What is happening right now?
DROP VIEW IF EXISTS view_operational_dashboard;

CREATE VIEW view_operational_dashboard AS
SELECT
    h.adres,
    CASE
        WHEN b.id IS NOT NULL THEN 'Occupied'
        ELSE 'Vacant'
    END as status,
    k.naam as current_tenant,
    b.checkout_datum as next_checkout,

-- Days until action needed
CAST(
    JULIANDAY(b.checkout_datum) - JULIANDAY('now') AS INTEGER
) as days_remaining
FROM
    huizen h
    LEFT JOIN boekingen b ON h.id = b.huis_id
    AND b.checkin_datum <= DATE('now')
    AND b.checkout_datum >= DATE('now')
    LEFT JOIN klanten k ON b.klant_id = k.id
ORDER BY days_remaining ASC;
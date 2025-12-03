DROP VIEW IF EXISTS view_latest_pricing;

CREATE VIEW view_latest_pricing AS
WITH
    latest_verhuur AS (
        SELECT *, ROW_NUMBER() OVER (
                PARTITION BY
                    huis_id
                ORDER BY start_datum DESC
            ) as rn
        FROM verhuur_contracten
            -- Consider active if status is active OR it's a future/current contract based on date
        WHERE
            status = 'active'
            OR eind_datum IS NULL
            OR eind_datum >= DATE('now')
    ),
    latest_inhuur AS (
        SELECT *, ROW_NUMBER() OVER (
                PARTITION BY
                    property_id
                ORDER BY start_date DESC
            ) as rn
        FROM inhuur_contracten
            -- Consider active if no end date or end date is in future
        WHERE
            end_date IS NULL
            OR end_date >= DATE('now')
    )
SELECT h.id AS huis_id, h.object_id, h.adres, h.plaats,

-- Verhuur (Out)
v.kale_huur AS verhuur_prijs,
v.start_datum AS verhuur_start,
v.eind_datum AS verhuur_eind,
k.naam AS klant_naam,

-- Inhuur (In)
i.kale_huur AS inhuur_prijs,
i.start_date AS inhuur_start,
i.end_date AS inhuur_eind,
l.naam AS leverancier_naam,

-- Margin Calculation (Optional but useful)
(
    IFNULL(v.kale_huur, 0) - IFNULL(i.kale_huur, 0)
) AS bruto_marge
FROM
    huizen h
    LEFT JOIN latest_verhuur v ON h.id = v.huis_id
    AND v.rn = 1
    LEFT JOIN klanten k ON v.klant_id = k.id
    LEFT JOIN latest_inhuur i ON h.id = i.property_id
    AND i.rn = 1
    LEFT JOIN leveranciers l ON i.leverancier_id = l.id;
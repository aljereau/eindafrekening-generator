-- RyanRent Operationele Planning DB (SQLite)
-- Doel: woningen (master) -> cycli (lifecycle) -> acties (proof + planning)
-- Opmerking: huizen/masterdata komt uit jullie bestaande "huizen" tabel.
-- In deze schema neem ik 'huizen' minimal op als referentie. Vervang/alias naar jullie echte tabel.

PRAGMA foreign_keys = ON;

-- =========================================================
-- 1) Enumeraties / keuzelijsten (optioneel maar handig)
-- =========================================================
-- In SQLite zijn enums niet native. We gebruiken CHECK constraints op tekstvelden.
-- Als je later liever echte lijst-tabellen wil, kan dat ook.

-- =========================================================
-- 2) Huizen (masterdata)
-- =========================================================
-- Als jullie al een 'huizen' tabel hebben: gebruik die en verwijder deze.
CREATE TABLE IF NOT EXISTS huizen (
  huis_id            TEXT PRIMARY KEY,  -- kan UUID of interne key zijn
  adres_weergave     TEXT NOT NULL,      -- "Akkerweg 12, Nunspeet"
  plaats             TEXT,
  actief             INTEGER NOT NULL DEFAULT 1 CHECK (actief IN (0,1)),
  aangemaakt_op      TEXT NOT NULL DEFAULT (datetime('now')),
  bijgewerkt_op      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_huizen_adres ON huizen(adres_weergave);

-- =========================================================
-- 3) Woning cycli (1 rij per proces-cyclus)
-- =========================================================
CREATE TABLE IF NOT EXISTS woning_cycli (
  cyclus_id                TEXT PRIMARY KEY,  -- UUID
  huis_id                  TEXT NOT NULL,
  is_actief                INTEGER NOT NULL DEFAULT 1 CHECK (is_actief IN (0,1)),

  klant_type               TEXT NOT NULL CHECK (klant_type IN ('TRADIRO','EXTERN','EIGENAAR')),
  bestemming               TEXT NOT NULL CHECK (bestemming IN ('OPNIEUW_VERHUREN','TERUG_NAAR_EIGENAAR')),

  status                   TEXT NOT NULL CHECK (status IN (
                            'NIET_GESTART',
                            'VOORINSPECTIE_GEPLAND',
                            'VOORINSPECTIE_UITGEVOERD',
                            'UITCHECK_GEPLAND',
                            'UITCHECK_UITGEVOERD',
                            'SCHOONMAAK_NODIG',
                            'KLAAR_VOOR_INCHECK',
                            'INCHECK_GEPLAND',
                            'INCHECK_UITGEVOERD',
                            'TERUG_NAAR_EIGENAAR',
                            'AFGEROND'
                          )),

  einddatum_huurder         TEXT, -- ISO date
  startdatum_nieuwe_huurder TEXT, -- ISO date

  interne_opmerking         TEXT,

  aangemaakt_op             TEXT NOT NULL DEFAULT (datetime('now')),
  laatst_bijgewerkt_op      TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY (huis_id) REFERENCES huizen(huis_id)
);

CREATE INDEX IF NOT EXISTS idx_cycli_huis_actief ON woning_cycli(huis_id, is_actief);
CREATE INDEX IF NOT EXISTS idx_cycli_status ON woning_cycli(status);

-- (Belangrijk) Unieke actieve cyclus per huis.
-- SQLite ondersteunt partial indexes: perfect hiervoor.
CREATE UNIQUE INDEX IF NOT EXISTS ux_cycli_1_actief_per_huis
ON woning_cycli(huis_id)
WHERE is_actief = 1;

-- =========================================================
-- 4) Acties (meerdere rijen per cyclus)
-- =========================================================
CREATE TABLE IF NOT EXISTS woning_acties (
  actie_id                  TEXT PRIMARY KEY,   -- UUID
  cyclus_id                 TEXT NOT NULL,

  actie_type                TEXT NOT NULL CHECK (actie_type IN (
                            'VOORINSPECTIE',
                            'UITCHECK',
                            'SCHOONMAAK',
                            'INCHECK',
                            'OVERDRACHT_EIGENAAR',
                            'REPARATIE'
                          )),

  gepland_op                TEXT,   -- datetime ISO
  uitgevoerd_op             TEXT,   -- datetime ISO
  uitgevoerd_door           TEXT,   -- naam/team/leverancier

  fotos_gemaakt             TEXT CHECK (fotos_gemaakt IN ('JA','NEE','ONBEKEND')),
  issues_gevonden           TEXT CHECK (issues_gevonden IN ('JA','NEE','ONBEKEND')),

  verwachte_schoonmaak_uren REAL CHECK (verwachte_schoonmaak_uren IS NULL OR verwachte_schoonmaak_uren >= 0),
  werkelijke_schoonmaak_uren REAL CHECK (werkelijke_schoonmaak_uren IS NULL OR werkelijke_schoonmaak_uren >= 0),

  sleutels_bevestigd        TEXT CHECK (sleutels_bevestigd IN ('JA','NEE','ONBEKEND')),
  sleuteloverdracht_methode TEXT CHECK (sleuteloverdracht_methode IN ('PERSOONLIJK','IN_WONING_ACHTERGELATEN','ANDERS') OR sleuteloverdracht_methode IS NULL),

  opmerking                 TEXT,

  aangemaakt_op             TEXT NOT NULL DEFAULT (datetime('now')),
  bijgewerkt_op             TEXT NOT NULL DEFAULT (datetime('now')),

  FOREIGN KEY (cyclus_id) REFERENCES woning_cycli(cyclus_id)
);

CREATE INDEX IF NOT EXISTS idx_acties_cyclus ON woning_acties(cyclus_id);
CREATE INDEX IF NOT EXISTS idx_acties_type ON woning_acties(actie_type);
CREATE INDEX IF NOT EXISTS idx_acties_open ON woning_acties(uitgevoerd_op);

-- =========================================================
-- 5) Views: wat de dashboard/AI meestal wil lezen
-- =========================================================

-- 5.1 Actieve cycli overzicht
CREATE VIEW IF NOT EXISTS v_actieve_cycli AS
SELECT
  c.cyclus_id,
  c.huis_id,
  h.adres_weergave,
  h.plaats,
  c.klant_type,
  c.bestemming,
  c.status,
  c.einddatum_huurder,
  c.startdatum_nieuwe_huurder,
  c.interne_opmerking,
  c.aangemaakt_op,
  c.laatst_bijgewerkt_op
FROM woning_cycli c
JOIN huizen h ON h.huis_id = c.huis_id
WHERE c.is_actief = 1;

-- 5.2 Laatste actie per type per cyclus (handig voor checks)
-- Dit pakt de meest recente uitgevoerde actie per type.
CREATE VIEW IF NOT EXISTS v_laatste_actie_per_type AS
SELECT
  a.cyclus_id,
  a.actie_type,
  a.actie_id,
  MAX(COALESCE(a.uitgevoerd_op, a.gepland_op, a.aangemaakt_op)) AS laatst_moment
FROM woning_acties a
GROUP BY a.cyclus_id, a.actie_type;

-- 5.3 Openstaande acties (gepland maar niet uitgevoerd)
CREATE VIEW IF NOT EXISTS v_open_acties AS
SELECT
  c.cyclus_id,
  h.adres_weergave,
  a.actie_id,
  a.actie_type,
  a.gepland_op,
  a.uitgevoerd_door,
  c.status,
  c.startdatum_nieuwe_huurder
FROM woning_acties a
JOIN woning_cycli c ON c.cyclus_id = a.cyclus_id
JOIN huizen h ON h.huis_id = c.huis_id
WHERE c.is_actief = 1
  AND a.gepland_op IS NOT NULL
  AND a.uitgevoerd_op IS NULL;

-- 5.4 Schoonmaak variance (verwacht vs werkelijk) per cyclus
CREATE VIEW IF NOT EXISTS v_schoonmaak_variance AS
SELECT
  c.cyclus_id,
  h.adres_weergave,
  -- verwacht komt van de UITCHECK actie
  (SELECT MAX(verwachte_schoonmaak_uren)
   FROM woning_acties a1
   WHERE a1.cyclus_id = c.cyclus_id AND a1.actie_type = 'UITCHECK') AS verwacht_uren,
  -- werkelijk komt van de SCHOONMAAK actie
  (SELECT MAX(werkelijke_schoonmaak_uren)
   FROM woning_acties a2
   WHERE a2.cyclus_id = c.cyclus_id AND a2.actie_type = 'SCHOONMAAK') AS werkelijk_uren
FROM woning_cycli c
JOIN huizen h ON h.huis_id = c.huis_id
WHERE c.is_actief = 1;
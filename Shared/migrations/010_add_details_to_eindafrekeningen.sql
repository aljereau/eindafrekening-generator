-- Add detailed columns to eindafrekeningen table for analytics
ALTER TABLE eindafrekeningen ADD COLUMN schoonmaak_pakket TEXT;

ALTER TABLE eindafrekeningen
ADD COLUMN schoonmaak_kosten REAL DEFAULT 0;

ALTER TABLE eindafrekeningen
ADD COLUMN schade_totaal_kosten REAL DEFAULT 0;

ALTER TABLE eindafrekeningen
ADD COLUMN extra_voorschot_bedrag REAL DEFAULT 0;
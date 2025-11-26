-- Migration 008: Remove Person and Stay tables
-- User clarified they do not track individual occupants, only contracts with institutions.

DROP TABLE IF EXISTS verblijven;

DROP TABLE IF EXISTS personen;
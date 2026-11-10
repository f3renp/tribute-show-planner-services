-- Tables owned by the catalogue service. IF NOT EXISTS makes this safe to
-- run on every startup: existing tables and their data are left alone.
-- The shows and setlist_items tables live in the shows service's own
-- database (ADR-6).

CREATE TABLE IF NOT EXISTS outfits (
    id             INTEGER PRIMARY KEY,
    name           TEXT    NOT NULL UNIQUE,
    change_seconds INTEGER NOT NULL CHECK (change_seconds >= 0)
);

CREATE TABLE IF NOT EXISTS songs (
    id               INTEGER PRIMARY KEY,
    title            TEXT    NOT NULL,
    album            TEXT    NOT NULL,
    year             INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
    energy           INTEGER NOT NULL CHECK (energy BETWEEN 1 AND 5),
    kind             TEXT    NOT NULL CHECK (kind IN ('dance', 'ballad')),
    outfit_id        INTEGER NOT NULL REFERENCES outfits (id),
    active           INTEGER NOT NULL DEFAULT 1,
    UNIQUE (title, album)
);

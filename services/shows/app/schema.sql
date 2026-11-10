-- Tables owned by the shows service. IF NOT EXISTS makes this safe to run
-- on every startup: existing tables and their data are left alone.
-- The songs and outfits tables live in the catalogue service's own
-- database (ADR-6).

CREATE TABLE IF NOT EXISTS shows (
    id          INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    venue       TEXT    NOT NULL,
    show_date   TEXT    NOT NULL,
    max_minutes INTEGER NOT NULL CHECK (max_minutes > 0)
);

-- song_id has no REFERENCES to songs: songs are in another service's
-- database, so the show builder only stores the ID and asks the catalogue
-- API for song details (ADR-3).
CREATE TABLE IF NOT EXISTS setlist_items (
    id            INTEGER PRIMARY KEY,
    show_id       INTEGER NOT NULL REFERENCES shows (id) ON DELETE CASCADE,
    position      INTEGER NOT NULL,
    item_type     TEXT    NOT NULL CHECK (item_type IN ('song', 'break')),
    song_id       INTEGER,
    break_label   TEXT,
    break_seconds INTEGER,
    UNIQUE (show_id, position)
);

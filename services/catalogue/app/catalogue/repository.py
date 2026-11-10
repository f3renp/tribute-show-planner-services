"""SQL for the catalogue tables. Only this file reads or writes songs and outfits."""
import db

# Songs ------------------------------------------------------------------


def list_songs():
    """All songs with their outfit name, active songs first."""
    return db.fetch_all(
        """
        SELECT songs.id, title, album, year, duration_seconds, energy, kind,
               outfit_id, active, outfits.name AS outfit_name
        FROM songs
        JOIN outfits ON outfits.id = songs.outfit_id
        ORDER BY active DESC, title
        """
    )


def get_song(song_id):
    """One song as a dict, or None if the id does not exist."""
    return db.fetch_one("SELECT * FROM songs WHERE id = ?", (song_id,))


def get_songs_with_outfits(song_ids):
    """The songs with these ids, each with its outfit name and change time."""
    if not song_ids:
        return []
    # One "?" per id, e.g. "?, ?, ?" for three ids.
    placeholders = ", ".join("?" for _ in song_ids)
    return db.fetch_all(
        f"""
        SELECT songs.id, title, album, year, duration_seconds, energy, kind,
               outfit_id, active, outfits.name AS outfit_name,
               outfits.change_seconds AS outfit_change_seconds
        FROM songs
        JOIN outfits ON outfits.id = songs.outfit_id
        WHERE songs.id IN ({placeholders})
        """,
        tuple(song_ids),
    )


def find_song_by_title_and_album(title, album):
    """The song with this title and album, or None."""
    return db.fetch_one(
        "SELECT * FROM songs WHERE title = ? AND album = ?", (title, album)
    )


def insert_song(song):
    """Save a new song and return its id. song uses the column names as keys."""
    return db.execute(
        """
        INSERT INTO songs (title, album, year, duration_seconds, energy, kind, outfit_id)
        VALUES (:title, :album, :year, :duration_seconds, :energy, :kind, :outfit_id)
        """,
        song,
    )


def update_song(song_id, song):
    """Overwrite the details of an existing song."""
    db.execute(
        """
        UPDATE songs
        SET title = :title, album = :album, year = :year,
            duration_seconds = :duration_seconds, energy = :energy,
            kind = :kind, outfit_id = :outfit_id
        WHERE id = :id
        """,
        dict(song, id=song_id),
    )


def set_song_active(song_id, active):
    """Mark a song as active (True) or retired (False)."""
    db.execute(
        "UPDATE songs SET active = ? WHERE id = ?", (int(active), song_id)
    )


# Outfits ----------------------------------------------------------------


def list_outfits():
    """All outfits, sorted by name."""
    return db.fetch_all("SELECT * FROM outfits ORDER BY name")


def get_outfit(outfit_id):
    """One outfit as a dict, or None if the id does not exist."""
    return db.fetch_one("SELECT * FROM outfits WHERE id = ?", (outfit_id,))


def find_outfit_by_name(name):
    """The outfit with this name, or None."""
    return db.fetch_one("SELECT * FROM outfits WHERE name = ?", (name,))


def insert_outfit(outfit):
    """Save a new outfit and return its id."""
    return db.execute(
        "INSERT INTO outfits (name, change_seconds) VALUES (:name, :change_seconds)",
        outfit,
    )

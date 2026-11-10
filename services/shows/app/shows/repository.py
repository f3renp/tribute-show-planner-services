"""SQL for the show builder tables. Only this file reads or writes shows and
setlist_items. It never touches songs or outfits: song details come from
the catalogue service through shows.catalogue_client."""
import db

# Shows ------------------------------------------------------------------


def list_shows():
    """All shows, the soonest date first."""
    return db.fetch_all("SELECT * FROM shows ORDER BY show_date, name")


def get_show(show_id):
    """One show as a dict, or None if the id does not exist."""
    return db.fetch_one("SELECT * FROM shows WHERE id = ?", (show_id,))


def insert_show(show):
    """Save a new show and return its id."""
    return db.execute(
        """
        INSERT INTO shows (name, venue, show_date, max_minutes)
        VALUES (:name, :venue, :show_date, :max_minutes)
        """,
        show,
    )


# Setlist items ----------------------------------------------------------


def list_items(show_id):
    """The setlist of a show, in running order."""
    return db.fetch_all(
        "SELECT * FROM setlist_items WHERE show_id = ? ORDER BY position",
        (show_id,),
    )


def next_position(show_id):
    """The position after the last item: 1 for an empty setlist."""
    row = db.fetch_one(
        """
        SELECT COALESCE(MAX(position), 0) + 1 AS position
        FROM setlist_items WHERE show_id = ?
        """,
        (show_id,),
    )
    return row["position"]


def insert_song_item(show_id, position, song_id):
    """Add a song to the setlist at this position and return the item id."""
    return db.execute(
        """
        INSERT INTO setlist_items (show_id, position, item_type, song_id)
        VALUES (?, ?, 'song', ?)
        """,
        (show_id, position, song_id),
    )


def insert_break_item(show_id, position, label, seconds):
    """Add a break to the setlist at this position and return the item id."""
    return db.execute(
        """
        INSERT INTO setlist_items
            (show_id, position, item_type, break_label, break_seconds)
        VALUES (?, ?, 'break', ?, ?)
        """,
        (show_id, position, label, seconds),
    )


def delete_item(show_id, item_id):
    """Remove one item from a show's setlist."""
    db.execute(
        "DELETE FROM setlist_items WHERE id = ? AND show_id = ?",
        (item_id, show_id),
    )


def save_order(show_id, item_ids):
    """Renumber the setlist so item_ids[0] is position 1, item_ids[1] is 2...

    All updates run on one connection and are committed together, so the
    setlist is never left half reordered.
    """
    connection = db.get_connection()
    try:
        # UNIQUE (show_id, position) would fail if two items briefly shared
        # a position. Moving every item to a negative position first means
        # the new positions 1, 2, 3... are always free.
        connection.execute(
            "UPDATE setlist_items SET position = -position WHERE show_id = ?",
            (show_id,),
        )
        for position, item_id in enumerate(item_ids, start=1):
            connection.execute(
                "UPDATE setlist_items SET position = ? WHERE id = ? AND show_id = ?",
                (position, item_id, show_id),
            )
        connection.commit()
    finally:
        connection.close()

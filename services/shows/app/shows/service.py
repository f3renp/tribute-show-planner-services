"""Show builder rules: validating shows and breaks, and editing setlists.

validate_show, validate_break and move_in_order take plain values and
return plain values, with no database or Flask, so they can be unit
tested on their own. The functions below them save through the
repository. Song details only ever come from the catalogue service, over
HTTP through shows.catalogue_client.
"""
from datetime import date

from shows import catalogue_client, repository
from shows.rules import format_duration

# A show longer than 4 hours is a typo.
MAX_SHOW_MINUTES = 4 * 60

# A break longer than 30 minutes is an interval, not a break in the set.
MAX_BREAK_SECONDS = 30 * 60

DIRECTIONS = ("up", "down")


def parse_whole_number(text):
    """Turn "90" into 90. Return None if the text is not a whole number."""
    try:
        return int(text.strip())
    except ValueError:
        return None


def validate_show(form):
    """Check a submitted show form and return (show, errors).

    form is a dict of strings, as it arrives from an HTML form. show_date
    must be YYYY-MM-DD, which is what <input type="date"> sends.
    """
    errors = []

    name = form.get("name", "").strip()
    if not name:
        errors.append("Name is required.")

    venue = form.get("venue", "").strip()
    if not venue:
        errors.append("Venue is required.")

    show_date = form.get("show_date", "").strip()
    try:
        date.fromisoformat(show_date)
    except ValueError:
        errors.append("Date must look like 2026-10-31.")

    max_minutes = parse_whole_number(form.get("max_minutes", ""))
    if max_minutes is None or not 1 <= max_minutes <= MAX_SHOW_MINUTES:
        errors.append(f"Length must be between 1 and {MAX_SHOW_MINUTES} minutes.")

    show = {
        "name": name,
        "venue": venue,
        "show_date": show_date,
        "max_minutes": max_minutes,
    }
    return show, errors


def validate_break(form):
    """Check a submitted break form and return (label, seconds, errors)."""
    errors = []

    label = form.get("break_label", "").strip()
    if not label:
        errors.append("Break label is required.")

    seconds = parse_whole_number(form.get("break_seconds", ""))
    if seconds is None or not 1 <= seconds <= MAX_BREAK_SECONDS:
        errors.append(f"Break must be between 1 and {MAX_BREAK_SECONDS} seconds.")

    return label, seconds, errors


def move_in_order(item_ids, item_id, direction):
    """Return a new list with item_id moved one place "up" or "down".

    The first item cannot move up and the last cannot move down: the
    order comes back unchanged. So does an item_id that is not in the list.
    """
    if direction not in DIRECTIONS:
        raise ValueError(f"Direction must be one of {DIRECTIONS}.")
    new_order = list(item_ids)
    if item_id not in new_order:
        return new_order
    index = new_order.index(item_id)
    other = index - 1 if direction == "up" else index + 1
    if 0 <= other < len(new_order):
        new_order[index], new_order[other] = new_order[other], new_order[index]
    return new_order


# Reading: setlists joined with song details from the catalogue ----------


def get_setlist(show_id):
    """The show's items in order. Each song item gets a "song" key with the
    catalogue's details for it, fetched in one HTTP call through the seam."""
    items = repository.list_items(show_id)
    song_ids = [item["song_id"] for item in items if item["item_type"] == "song"]
    songs = catalogue_client.get_songs_by_ids(song_ids)
    for item in items:
        item["song"] = songs.get(item["song_id"])
    return items


def songs_to_choose():
    """Active catalogue songs, for the "add a song" picker."""
    return catalogue_client.list_active_songs()


# Saving: these use the database through the repository ------------------


def create_show(form):
    """Validate a show form and save it. Return (show_id, errors).

    show_id is None when there are errors.
    """
    show, errors = validate_show(form)
    if errors:
        return None, errors
    return repository.insert_show(show), []


def add_song_to_setlist(show_id, song_id):
    """Append a song to the end of a show's setlist. Return the errors."""
    if song_id is None:
        return ["Choose a song."]
    song = catalogue_client.get_songs_by_ids([song_id]).get(song_id)
    if song is None:
        return ["That song is not in the catalogue."]
    if not song["active"]:
        return ["That song is retired."]
    repository.insert_song_item(show_id, repository.next_position(show_id), song_id)
    return []


def add_break_to_setlist(show_id, form):
    """Validate a break form and append it to the setlist. Return the errors."""
    label, seconds, errors = validate_break(form)
    if not errors:
        position = repository.next_position(show_id)
        repository.insert_break_item(show_id, position, label, seconds)
    return errors


def remove_item(show_id, item_id):
    """Delete an item and close the gap it leaves in the positions."""
    remaining = [
        item["id"] for item in repository.list_items(show_id) if item["id"] != item_id
    ]
    repository.delete_item(show_id, item_id)
    repository.save_order(show_id, remaining)


def move_item(show_id, item_id, direction):
    """Move an item one place up or down in its show's setlist."""
    item_ids = [item["id"] for item in repository.list_items(show_id)]
    repository.save_order(show_id, move_in_order(item_ids, item_id, direction))

"""Demo catalogue: outfits and songs added at startup if the catalogue is empty.

Everything is saved through catalogue.service, so the demo data passes the
same validation as songs typed into the form. Only metadata is stored:
no lyrics, audio or cover art. Durations are approximate album lengths.
"""
from catalogue import repository, service

# (name, change_seconds)
DEMO_OUTFITS = [
    ("Jackson 5 retro", 60),
    ("Tuxedo", 90),
    ("Sequin jacket", 120),
    ("Red leather jacket", 150),
    ("Buckle outfit", 120),
    ("White suit and fedora", 180),
    ("Military jacket", 150),
]

# (title, album, year, duration, energy, kind, outfit name)
DEMO_SONGS = [
    ("I Want You Back", "Diana Ross Presents the Jackson 5", 1969, "2:58", 4, "dance", "Jackson 5 retro"),
    ("Ben", "Ben", 1972, "2:44", 1, "ballad", "Jackson 5 retro"),
    ("Don't Stop 'Til You Get Enough", "Off the Wall", 1979, "6:05", 5, "dance", "Tuxedo"),
    ("Rock with You", "Off the Wall", 1979, "3:40", 3, "dance", "Tuxedo"),
    ("She's Out of My Life", "Off the Wall", 1979, "3:38", 1, "ballad", "Tuxedo"),
    ("Wanna Be Startin' Somethin'", "Thriller", 1982, "6:03", 5, "dance", "Sequin jacket"),
    ("Billie Jean", "Thriller", 1982, "4:54", 4, "dance", "Sequin jacket"),
    ("Human Nature", "Thriller", 1982, "4:06", 2, "ballad", "Sequin jacket"),
    ("Beat It", "Thriller", 1982, "4:18", 5, "dance", "Red leather jacket"),
    ("Thriller", "Thriller", 1982, "5:57", 5, "dance", "Red leather jacket"),
    ("Bad", "Bad", 1987, "4:07", 4, "dance", "Buckle outfit"),
    ("The Way You Make Me Feel", "Bad", 1987, "4:58", 4, "dance", "Buckle outfit"),
    ("Man in the Mirror", "Bad", 1987, "5:19", 3, "ballad", "Buckle outfit"),
    ("Smooth Criminal", "Bad", 1987, "4:17", 5, "dance", "White suit and fedora"),
    ("Black or White", "Dangerous", 1991, "4:15", 4, "dance", "Military jacket"),
    ("Remember the Time", "Dangerous", 1991, "4:00", 3, "dance", "Military jacket"),
    ("Heal the World", "Dangerous", 1991, "6:25", 1, "ballad", "Military jacket"),
    ("They Don't Care About Us", "HIStory", 1995, "4:44", 4, "dance", "Military jacket"),
    ("Earth Song", "HIStory", 1995, "6:46", 2, "ballad", "Military jacket"),
    ("You Are Not Alone", "HIStory", 1995, "5:45", 1, "ballad", "Military jacket"),
]

# (title, album) of demo songs that start retired, to show that feature.
RETIRED_DEMO_SONGS = [("Ben", "Ben")]


def catalogue_is_empty():
    """True if there are no outfits and no songs yet."""
    return not repository.list_outfits() and not repository.list_songs()


def add_demo_outfits():
    """Save every demo outfit through the catalogue service."""
    for name, change_seconds in DEMO_OUTFITS:
        errors = service.add_outfit({"name": name, "change_seconds": str(change_seconds)})
        if errors:
            raise ValueError(f"Demo outfit {name!r} is invalid: {errors}")


def add_demo_songs():
    """Save every demo song, filling in the form the same way a user would."""
    for title, album, year, duration, energy, kind, outfit_name in DEMO_SONGS:
        outfit_id = repository.find_outfit_by_name(outfit_name)["id"]
        form = {
            "title": title,
            "album": album,
            "year": str(year),
            "duration": duration,
            "energy": str(energy),
            "kind": kind,
            "outfit_id": str(outfit_id),
        }
        errors = service.add_song(form)
        if errors:
            raise ValueError(f"Demo song {title!r} is invalid: {errors}")


def retire_demo_songs():
    """Retire the demo songs listed in RETIRED_DEMO_SONGS."""
    for title, album in RETIRED_DEMO_SONGS:
        song = repository.find_song_by_title_and_album(title, album)
        service.retire_song(song["id"])


def seed_demo_catalogue():
    """Fill an empty catalogue with the demo data. Return True if it did.

    A catalogue that already has an outfit or a song is left alone, so
    restarting the app never adds the demo data twice or mixes it with
    real data.
    """
    if not catalogue_is_empty():
        return False
    add_demo_outfits()
    add_demo_songs()
    retire_demo_songs()
    return True

"""Setlist checks: each one reports what is wrong with a show's order.

Every check takes the items from service.get_setlist (in order, each song
item with a "song" dict from the catalogue, or None if the id is missing)
and returns a list of problem messages. An empty list means no problems.
No database and no Flask here, so each check can be tested on its own.
"""

# Energy 4 or 5 counts as a high-energy song.
HIGH_ENERGY = 4

# A third high-energy song in a row wears out the performer and the crowd.
MAX_HIGH_ENERGY_IN_A_ROW = 2


def format_duration(seconds):
    """Turn 294 seconds into "4:54"."""
    return f"{seconds // 60}:{seconds % 60:02d}"


def setlist_seconds(items):
    """Total length of the setlist: every song plus every break.

    A song whose details are missing adds nothing, because its length is
    unknown. The retired and missing song check reports it instead.
    """
    total = 0
    for item in items:
        if item["item_type"] == "break":
            total += item["break_seconds"]
        elif item["song"] is not None:
            total += item["song"]["duration_seconds"]
    return total


def is_over_limit(total_seconds, max_minutes):
    """True if the running time is longer than the show's limit.
    Exactly at the limit is fine."""
    return total_seconds > max_minutes * 60


def check_running_time(items, max_minutes):
    """Report it when the setlist is longer than the show's limit."""
    total = setlist_seconds(items)
    if not is_over_limit(total, max_minutes):
        return []
    over = format_duration(total - max_minutes * 60)
    return [
        f"Running time is {format_duration(total)}, "
        f"{over} over the {max_minutes}-minute limit."
    ]


def check_outfit_changes(items):
    """Report each outfit change that the breaks before it are too short for.

    When two songs in a row use different outfits, the breaks between
    them must add up to at least the new outfit's change_seconds.
    """
    problems = []
    previous_song = None
    break_seconds = 0
    for item in items:
        if item["item_type"] == "break":
            break_seconds += item["break_seconds"]
            continue
        song = item["song"]
        if song is None:
            continue
        if previous_song is not None and song["outfit_id"] != previous_song["outfit_id"]:
            needed = song["outfit_change_seconds"]
            if break_seconds < needed:
                problems.append(
                    f"Position {item['position']}: changing into "
                    f"{song['outfit_name']} for \"{song['title']}\" takes "
                    f"{needed} s, but the break before it is only "
                    f"{break_seconds} s."
                )
        previous_song = song
        break_seconds = 0
    return problems


def is_high_energy(song):
    """True for songs with energy 4 or 5."""
    return song["energy"] >= HIGH_ENERGY


def check_energy_pacing(items):
    """Report each run of more than two high-energy songs in a row.

    A break gives the performer a rest, so it ends the run. The run is
    reported once, at the song that makes it too long.
    """
    problems = []
    run = 0
    for item in items:
        if item["item_type"] == "break":
            run = 0
            continue
        song = item["song"]
        if song is None:
            continue
        if not is_high_energy(song):
            run = 0
            continue
        run += 1
        if run == MAX_HIGH_ENERGY_IN_A_ROW + 1:
            problems.append(
                f"Position {item['position']}: \"{song['title']}\" makes "
                f"{run} high-energy songs in a row without a rest."
            )
    return problems


def check_ballads_in_a_row(items):
    """Report each ballad that comes straight after another ballad.

    A break between them separates the two ballads, so it is fine.
    """
    problems = []
    previous_was_ballad = False
    for item in items:
        if item["item_type"] == "break":
            previous_was_ballad = False
            continue
        song = item["song"]
        if song is None:
            continue
        is_ballad = song["kind"] == "ballad"
        if is_ballad and previous_was_ballad:
            problems.append(
                f"Position {item['position']}: \"{song['title']}\" is a "
                f"second ballad in a row."
            )
        previous_was_ballad = is_ballad
    return problems


def check_opener_and_closer(items):
    """Report it when the first or last song is not high energy.

    Breaks and songs whose details are missing are left out, so the
    opener is the first known song and the closer the last one. With a
    single song it is both, and it is reported only once.
    """
    songs = [
        item for item in items if item["item_type"] == "song" and item["song"] is not None
    ]
    if not songs:
        return []
    problems = []
    opener = songs[0]
    closer = songs[-1]
    if not is_high_energy(opener["song"]):
        problems.append(
            f"The opener \"{opener['song']['title']}\" has energy "
            f"{opener['song']['energy']}; open with energy {HIGH_ENERGY} or more."
        )
    if closer is not opener and not is_high_energy(closer["song"]):
        problems.append(
            f"The closer \"{closer['song']['title']}\" has energy "
            f"{closer['song']['energy']}; close with energy {HIGH_ENERGY} or more."
        )
    return problems


def check_retired_and_repeated_songs(items):
    """Report retired songs, songs missing from the catalogue, and songs
    that appear more than once."""
    problems = []
    first_position = {}
    for item in items:
        if item["item_type"] != "song":
            continue
        position = item["position"]
        song = item["song"]
        if song is None:
            problems.append(
                f"Position {position}: song {item['song_id']} is no longer "
                f"in the catalogue."
            )
        elif not song["active"]:
            problems.append(f"Position {position}: \"{song['title']}\" is retired.")
        song_id = item["song_id"]
        if song_id in first_position:
            problems.append(
                f"Position {position}: the same song is already at position "
                f"{first_position[song_id]}."
            )
        else:
            first_position[song_id] = position
    return problems


def check_setlist(items, max_minutes):
    """Run every check and return all their problems in one list."""
    return (
        check_running_time(items, max_minutes)
        + check_outfit_changes(items)
        + check_energy_pacing(items)
        + check_ballads_in_a_row(items)
        + check_opener_and_closer(items)
        + check_retired_and_repeated_songs(items)
    )

"""Unit tests for the setlist checks in shows/rules.py: no database, no Flask."""
from shows.rules import (
    check_ballads_in_a_row,
    check_energy_pacing,
    check_opener_and_closer,
    check_outfit_changes,
    check_retired_and_repeated_songs,
    check_running_time,
    check_setlist,
    format_duration,
    is_high_energy,
    is_over_limit,
    setlist_seconds,
)


def song_item(
    position,
    title,
    duration=240,
    outfit_id=1,
    change_seconds=0,
    energy=4,
    kind="dance",
    active=1,
    song_id=None,
):
    """A song item shaped like the ones service.get_setlist returns.

    song_id defaults to the position, so every song is different unless
    a test passes the same song_id twice.
    """
    if song_id is None:
        song_id = position
    return {
        "position": position,
        "item_type": "song",
        "song_id": song_id,
        "song": {
            "id": song_id,
            "title": title,
            "duration_seconds": duration,
            "outfit_id": outfit_id,
            "outfit_name": f"Outfit {outfit_id}",
            "outfit_change_seconds": change_seconds,
            "energy": energy,
            "kind": kind,
            "active": active,
        },
    }


def break_item(position, seconds):
    """A break item shaped like the ones service.get_setlist returns."""
    return {
        "position": position,
        "item_type": "break",
        "song_id": None,
        "song": None,
        "break_label": "Break",
        "break_seconds": seconds,
    }


def missing_song_item(position):
    """A song item whose id is no longer in the catalogue."""
    return {"position": position, "item_type": "song", "song_id": 99, "song": None}


# Running time -----------------------------------------------------------


def test_format_duration():
    assert format_duration(294) == "4:54"
    assert format_duration(5) == "0:05"


def test_setlist_seconds_adds_songs_and_breaks():
    items = [song_item(1, "Thriller", duration=300), break_item(2, 60)]
    assert setlist_seconds(items) == 360


def test_setlist_seconds_skips_missing_songs():
    items = [song_item(1, "Thriller", duration=300), missing_song_item(2)]
    assert setlist_seconds(items) == 300


def test_empty_setlist_is_within_any_limit():
    assert check_running_time([], 1) == []


def test_running_time_exactly_at_limit_is_fine():
    items = [song_item(1, "Bad", duration=300), song_item(2, "Thriller", duration=300)]
    assert check_running_time(items, 10) == []


def test_running_time_over_limit_is_reported():
    items = [song_item(1, "Bad", duration=300), song_item(2, "Thriller", duration=330)]
    problems = check_running_time(items, 10)
    assert problems == ["Running time is 10:30, 0:30 over the 10-minute limit."]


def test_breaks_count_towards_running_time():
    items = [song_item(1, "Bad", duration=540), break_item(2, 120)]
    assert len(check_running_time(items, 10)) == 1


def test_is_over_limit_only_above_the_limit():
    assert is_over_limit(599, 10) is False
    assert is_over_limit(600, 10) is False
    assert is_over_limit(601, 10) is True


# Outfit changes ---------------------------------------------------------


def test_same_outfit_needs_no_break():
    items = [
        song_item(1, "Bad", outfit_id=1, change_seconds=90),
        song_item(2, "Smooth Criminal", outfit_id=1, change_seconds=90),
    ]
    assert check_outfit_changes(items) == []


def test_outfit_change_without_break_is_reported():
    items = [
        song_item(1, "Bad", outfit_id=1),
        song_item(2, "Thriller", outfit_id=2, change_seconds=90),
    ]
    problems = check_outfit_changes(items)
    assert len(problems) == 1
    assert "Position 2" in problems[0]
    assert "Thriller" in problems[0]


def test_outfit_change_with_long_enough_break_is_fine():
    items = [
        song_item(1, "Bad", outfit_id=1),
        break_item(2, 90),
        song_item(3, "Thriller", outfit_id=2, change_seconds=90),
    ]
    assert check_outfit_changes(items) == []


def test_outfit_change_with_short_break_is_reported():
    items = [
        song_item(1, "Bad", outfit_id=1),
        break_item(2, 60),
        song_item(3, "Thriller", outfit_id=2, change_seconds=90),
    ]
    assert len(check_outfit_changes(items)) == 1


def test_breaks_in_a_row_add_up():
    items = [
        song_item(1, "Bad", outfit_id=1),
        break_item(2, 45),
        break_item(3, 45),
        song_item(4, "Thriller", outfit_id=2, change_seconds=90),
    ]
    assert check_outfit_changes(items) == []


def test_break_only_counts_before_the_next_song():
    # The long break comes before "Bad", so the change after it is not covered.
    items = [
        break_item(1, 300),
        song_item(2, "Bad", outfit_id=1),
        song_item(3, "Thriller", outfit_id=2, change_seconds=90),
    ]
    assert len(check_outfit_changes(items)) == 1


def test_first_song_needs_no_change_time():
    items = [song_item(1, "Thriller", outfit_id=2, change_seconds=90)]
    assert check_outfit_changes(items) == []


def test_missing_song_is_skipped_in_outfit_check():
    items = [
        song_item(1, "Bad", outfit_id=1),
        missing_song_item(2),
        song_item(3, "Smooth Criminal", outfit_id=1),
    ]
    assert check_outfit_changes(items) == []


# Energy pacing ----------------------------------------------------------


def test_is_high_energy_starts_at_four():
    assert is_high_energy({"energy": 4})
    assert is_high_energy({"energy": 5})
    assert not is_high_energy({"energy": 3})


def test_two_high_energy_songs_in_a_row_are_fine():
    items = [song_item(1, "Bad", energy=5), song_item(2, "Thriller", energy=4)]
    assert check_energy_pacing(items) == []


def test_third_high_energy_song_in_a_row_is_reported():
    items = [
        song_item(1, "Bad", energy=5),
        song_item(2, "Thriller", energy=4),
        song_item(3, "Beat It", energy=5),
    ]
    problems = check_energy_pacing(items)
    assert len(problems) == 1
    assert "Position 3" in problems[0]


def test_long_run_is_reported_once():
    items = [song_item(position, f"Song {position}", energy=5) for position in range(1, 6)]
    assert len(check_energy_pacing(items)) == 1


def test_calm_song_ends_the_run():
    items = [
        song_item(1, "Bad", energy=5),
        song_item(2, "Thriller", energy=4),
        song_item(3, "Human Nature", energy=2),
        song_item(4, "Beat It", energy=5),
    ]
    assert check_energy_pacing(items) == []


def test_break_ends_the_run():
    items = [
        song_item(1, "Bad", energy=5),
        song_item(2, "Thriller", energy=4),
        break_item(3, 60),
        song_item(4, "Beat It", energy=5),
    ]
    assert check_energy_pacing(items) == []


# Ballads in a row -------------------------------------------------------


def test_two_ballads_in_a_row_are_reported():
    items = [
        song_item(1, "Human Nature", kind="ballad"),
        song_item(2, "Heal the World", kind="ballad"),
    ]
    problems = check_ballads_in_a_row(items)
    assert len(problems) == 1
    assert "Heal the World" in problems[0]


def test_three_ballads_in_a_row_give_two_problems():
    items = [song_item(position, f"Ballad {position}", kind="ballad") for position in (1, 2, 3)]
    assert len(check_ballads_in_a_row(items)) == 2


def test_dance_song_between_ballads_is_fine():
    items = [
        song_item(1, "Human Nature", kind="ballad"),
        song_item(2, "Bad", kind="dance"),
        song_item(3, "Heal the World", kind="ballad"),
    ]
    assert check_ballads_in_a_row(items) == []


def test_break_between_ballads_is_fine():
    items = [
        song_item(1, "Human Nature", kind="ballad"),
        break_item(2, 60),
        song_item(3, "Heal the World", kind="ballad"),
    ]
    assert check_ballads_in_a_row(items) == []


# Opener and closer ------------------------------------------------------


def test_high_energy_opener_and_closer_are_fine():
    items = [
        song_item(1, "Wanna Be Startin' Somethin'", energy=5),
        song_item(2, "Human Nature", energy=2),
        song_item(3, "Billie Jean", energy=4),
    ]
    assert check_opener_and_closer(items) == []


def test_calm_opener_is_reported():
    items = [song_item(1, "Human Nature", energy=2), song_item(2, "Bad", energy=5)]
    problems = check_opener_and_closer(items)
    assert len(problems) == 1
    assert problems[0].startswith("The opener")


def test_calm_closer_is_reported():
    items = [song_item(1, "Bad", energy=5), song_item(2, "Human Nature", energy=2)]
    problems = check_opener_and_closer(items)
    assert len(problems) == 1
    assert problems[0].startswith("The closer")


def test_breaks_are_not_opener_or_closer():
    items = [
        break_item(1, 60),
        song_item(2, "Bad", energy=5),
        song_item(3, "Thriller", energy=5),
        break_item(4, 60),
    ]
    assert check_opener_and_closer(items) == []


def test_single_calm_song_is_reported_once():
    items = [song_item(1, "Human Nature", energy=2)]
    assert len(check_opener_and_closer(items)) == 1


def test_setlist_without_songs_has_no_opener_problem():
    assert check_opener_and_closer([break_item(1, 60)]) == []


# Retired and repeated songs ---------------------------------------------


def test_active_different_songs_are_fine():
    items = [song_item(1, "Bad"), song_item(2, "Thriller")]
    assert check_retired_and_repeated_songs(items) == []


def test_retired_song_is_reported():
    items = [song_item(1, "Bad"), song_item(2, "Dangerous", active=0)]
    problems = check_retired_and_repeated_songs(items)
    assert problems == ['Position 2: "Dangerous" is retired.']


def test_missing_song_is_reported():
    problems = check_retired_and_repeated_songs([missing_song_item(1)])
    assert problems == ["Position 1: song 99 is no longer in the catalogue."]


def test_same_song_twice_is_reported_with_first_position():
    items = [
        song_item(1, "Bad", song_id=7),
        song_item(2, "Thriller"),
        song_item(3, "Bad", song_id=7),
    ]
    problems = check_retired_and_repeated_songs(items)
    assert problems == ["Position 3: the same song is already at position 1."]


def test_breaks_are_ignored_by_song_check():
    assert check_retired_and_repeated_songs([break_item(1, 60)]) == []


def test_missing_song_does_not_end_an_energy_run():
    items = [
        song_item(1, "Bad", energy=5),
        missing_song_item(2),
        song_item(3, "Thriller", energy=4),
        song_item(4, "Beat It", energy=5),
    ]
    assert len(check_energy_pacing(items)) == 1


def test_missing_song_does_not_separate_ballads():
    items = [
        song_item(1, "Human Nature", kind="ballad"),
        missing_song_item(2),
        song_item(3, "Heal the World", kind="ballad"),
    ]
    assert len(check_ballads_in_a_row(items)) == 1


# All checks together ----------------------------------------------------


def test_good_setlist_has_no_problems():
    items = [
        song_item(1, "Wanna Be Startin' Somethin'", energy=5, outfit_id=1),
        song_item(2, "Human Nature", energy=2, kind="ballad", outfit_id=1),
        break_item(3, 90),
        song_item(4, "Thriller", energy=4, outfit_id=2, change_seconds=90),
    ]
    assert check_setlist(items, 20) == []


def test_check_setlist_collects_problems_from_several_checks():
    items = [
        song_item(1, "Human Nature", energy=2, kind="ballad", duration=400),
        song_item(2, "Heal the World", energy=2, kind="ballad", outfit_id=2, change_seconds=60),
        song_item(3, "Human Nature", energy=2, kind="ballad", song_id=1, active=0),
    ]
    problems = check_setlist(items, 1)
    assert any(problem.startswith("Running time") for problem in problems)
    assert any("changing into" in problem for problem in problems)
    assert any("second ballad" in problem for problem in problems)
    assert any(problem.startswith("The opener") for problem in problems)
    assert any("is retired" in problem for problem in problems)
    assert any("already at position" in problem for problem in problems)

"""Unit tests for the pure catalogue functions: no database, no Flask."""
import pytest

from catalogue.service import (
    format_duration,
    parse_duration,
    parse_whole_number,
    read_duration,
    song_to_form,
    validate_outfit,
    validate_song,
)


def valid_song_form():
    """A song form that passes every check. Tests change one field at a time."""
    return {
        "title": "Billie Jean",
        "album": "Thriller",
        "year": "1982",
        "duration": "4:54",
        "energy": "4",
        "kind": "dance",
        "outfit_id": "1",
    }


# Duration parsing -------------------------------------------------------


@pytest.mark.parametrize(
    "text, seconds",
    [("4:54", 294), ("0:30", 30), ("10:00", 600), (" 12:05 ", 725)],
)
def test_parse_duration_turns_m_ss_into_seconds(text, seconds):
    assert parse_duration(text) == seconds


@pytest.mark.parametrize(
    "text",
    ["", "454", "4:5", "4:60", "4:54:00", "a:bc", "-1:30", "4:5a", "4.54"],
)
def test_parse_duration_rejects_bad_formats(text):
    with pytest.raises(ValueError):
        parse_duration(text)


@pytest.mark.parametrize(
    "seconds, text",
    [(294, "4:54"), (65, "1:05"), (30, "0:30"), (600, "10:00")],
)
def test_format_duration_turns_seconds_into_m_ss(seconds, text):
    assert format_duration(seconds) == text


def test_format_then_parse_gives_back_the_same_seconds():
    for seconds in range(30, 1201):
        assert parse_duration(format_duration(seconds)) == seconds


def test_read_duration_accepts_the_limits():
    assert read_duration("0:30") == (30, None)
    assert read_duration("20:00") == (1200, None)


@pytest.mark.parametrize("text", ["0:29", "20:01"])
def test_read_duration_rejects_durations_outside_the_limits(text):
    seconds, error = read_duration(text)
    assert seconds is None
    assert "between 0:30 and 20:00" in error


def test_read_duration_returns_the_format_error_as_text():
    seconds, error = read_duration("4:5")
    assert seconds is None
    assert "two digits" in error


# Whole numbers ----------------------------------------------------------


@pytest.mark.parametrize("text, number", [("5", 5), (" 7 ", 7), ("-3", -3)])
def test_parse_whole_number_reads_integers(text, number):
    assert parse_whole_number(text) == number


@pytest.mark.parametrize("text", ["", "abc", "4.5"])
def test_parse_whole_number_returns_none_for_non_integers(text):
    assert parse_whole_number(text) is None


# Song validation --------------------------------------------------------


def test_valid_song_has_no_errors_and_typed_values():
    song, errors = validate_song(valid_song_form())
    assert errors == []
    assert song == {
        "title": "Billie Jean",
        "album": "Thriller",
        "year": 1982,
        "duration_seconds": 294,
        "energy": 4,
        "kind": "dance",
        "outfit_id": 1,
    }


def test_validate_song_strips_spaces_from_text():
    form = dict(valid_song_form(), title="  Billie Jean  ", album=" Thriller ")
    song, errors = validate_song(form)
    assert errors == []
    assert song["title"] == "Billie Jean"
    assert song["album"] == "Thriller"


def test_empty_form_reports_every_problem_at_once():
    song, errors = validate_song({})
    assert len(errors) == 7


@pytest.mark.parametrize(
    "field, value",
    [
        ("title", "   "),
        ("album", ""),
        ("year", "1963"),
        ("year", "2015"),
        ("year", "nineteen"),
        ("duration", "0:10"),
        ("duration", "4.54"),
        ("energy", "0"),
        ("energy", "6"),
        ("kind", "rock"),
        ("outfit_id", ""),
    ],
)
def test_one_bad_field_gives_exactly_one_error(field, value):
    form = dict(valid_song_form(), **{field: value})
    song, errors = validate_song(form)
    assert len(errors) == 1


@pytest.mark.parametrize(
    "field, value",
    [("year", "1964"), ("year", "2014"), ("energy", "1"), ("energy", "5"),
     ("kind", "ballad")],
)
def test_values_at_the_limits_are_accepted(field, value):
    form = dict(valid_song_form(), **{field: value})
    song, errors = validate_song(form)
    assert errors == []


def test_song_to_form_fills_a_form_that_validates_to_the_same_song():
    song, errors = validate_song(valid_song_form())
    assert validate_song(song_to_form(song)) == (song, [])


# Outfit validation ------------------------------------------------------


def test_valid_outfit_has_no_errors():
    outfit, errors = validate_outfit({"name": " Red jacket ", "change_seconds": "90"})
    assert errors == []
    assert outfit == {"name": "Red jacket", "change_seconds": 90}


def test_outfit_change_time_limits_are_accepted():
    assert validate_outfit({"name": "A", "change_seconds": "0"})[1] == []
    assert validate_outfit({"name": "A", "change_seconds": "600"})[1] == []


@pytest.mark.parametrize(
    "form",
    [
        {"name": "", "change_seconds": "90"},
        {"name": "Red jacket", "change_seconds": "-1"},
        {"name": "Red jacket", "change_seconds": "601"},
        {"name": "Red jacket", "change_seconds": "ninety"},
    ],
)
def test_bad_outfit_gives_one_error(form):
    outfit, errors = validate_outfit(form)
    assert len(errors) == 1

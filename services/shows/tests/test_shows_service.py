"""Tests for shows/service.py.

The first tests cover the pure functions (validate_show, validate_break,
move_in_order). The rest use the database fixture from conftest.py and
the catalogue fixture, a fake catalogue service the tests add songs to, so
no test calls the real catalogue over HTTP.
"""
import pytest

from shows import repository, service


def valid_show_form():
    """A show form that passes every check."""
    return {
        "name": "Halloween night",
        "venue": "Teatro Real",
        "show_date": "2026-10-31",
        "max_minutes": "90",
    }


# Show and break validation ----------------------------------------------


def test_valid_show_has_no_errors_and_typed_values():
    show, errors = service.validate_show(valid_show_form())
    assert errors == []
    assert show["max_minutes"] == 90


def test_empty_show_form_reports_every_problem_at_once():
    show, errors = service.validate_show({})
    assert len(errors) == 4


@pytest.mark.parametrize(
    "field, value",
    [
        ("name", " "),
        ("venue", ""),
        ("show_date", "31/10/2026"),
        ("show_date", "2026-02-30"),
        ("max_minutes", "0"),
        ("max_minutes", "241"),
        ("max_minutes", "ninety"),
    ],
)
def test_one_bad_show_field_gives_exactly_one_error(field, value):
    form = dict(valid_show_form(), **{field: value})
    show, errors = service.validate_show(form)
    assert len(errors) == 1


def test_valid_break():
    form = {"break_label": " Costume change ", "break_seconds": "120"}
    assert service.validate_break(form) == ("Costume change", 120, [])


@pytest.mark.parametrize(
    "form",
    [
        {"break_label": "", "break_seconds": "120"},
        {"break_label": "Rest", "break_seconds": "0"},
        {"break_label": "Rest", "break_seconds": "1801"},
        {"break_label": "Rest", "break_seconds": "two"},
    ],
)
def test_bad_break_gives_one_error(form):
    label, seconds, errors = service.validate_break(form)
    assert len(errors) == 1


# Reordering -------------------------------------------------------------


def test_move_up_swaps_with_the_item_before():
    assert service.move_in_order([10, 20, 30], 30, "up") == [10, 30, 20]


def test_move_down_swaps_with_the_item_after():
    assert service.move_in_order([10, 20, 30], 10, "down") == [20, 10, 30]


def test_first_item_cannot_move_up_and_last_cannot_move_down():
    assert service.move_in_order([10, 20, 30], 10, "up") == [10, 20, 30]
    assert service.move_in_order([10, 20, 30], 30, "down") == [10, 20, 30]


def test_unknown_item_leaves_the_order_unchanged():
    assert service.move_in_order([10, 20], 99, "up") == [10, 20]


def test_move_in_order_does_not_change_the_list_it_is_given():
    item_ids = [10, 20, 30]
    service.move_in_order(item_ids, 30, "up")
    assert item_ids == [10, 20, 30]


def test_unknown_direction_raises():
    with pytest.raises(ValueError):
        service.move_in_order([10, 20], 10, "sideways")


# Saving and reading setlists (temporary database) -----------------------


def add_song(catalogue, title):
    """Add a song to the fake catalogue, shaped like GET /api/songs returns
    it. Return the song id."""
    song_id = len(catalogue) + 1
    catalogue[song_id] = {
        "id": song_id,
        "title": title,
        "album": "Thriller",
        "year": 1982,
        "duration_seconds": 294,
        "energy": 4,
        "kind": "dance",
        "outfit_id": 1,
        "active": 1,
        "outfit_name": "Red jacket",
        "outfit_change_seconds": 90,
    }
    return song_id


def create_show():
    """Save a valid show and return its id."""
    show_id, errors = service.create_show(valid_show_form())
    assert errors == []
    return show_id


def item_labels(show_id):
    """The setlist as short labels in order, e.g. ["Billie Jean", "break: Rest"]."""
    labels = []
    for item in service.get_setlist(show_id):
        if item["item_type"] == "song":
            labels.append(item["song"]["title"])
        else:
            labels.append("break: " + item["break_label"])
    return labels


@pytest.mark.usefixtures("database")
def test_create_show_saves_it(catalogue):
    show_id = create_show()
    assert repository.get_show(show_id)["venue"] == "Teatro Real"


@pytest.mark.usefixtures("database")
def test_create_show_with_errors_saves_nothing(catalogue):
    show_id, errors = service.create_show(dict(valid_show_form(), name=""))
    assert show_id is None
    assert errors == ["Name is required."]
    assert repository.list_shows() == []


@pytest.mark.usefixtures("database")
def test_songs_and_breaks_are_added_at_the_end_in_order(catalogue):
    show_id = create_show()
    assert service.add_song_to_setlist(show_id, add_song(catalogue, "Billie Jean")) == []
    form = {"break_label": "Rest", "break_seconds": "60"}
    assert service.add_break_to_setlist(show_id, form) == []
    assert service.add_song_to_setlist(show_id, add_song(catalogue, "Beat It")) == []
    assert item_labels(show_id) == ["Billie Jean", "break: Rest", "Beat It"]
    positions = [item["position"] for item in repository.list_items(show_id)]
    assert positions == [1, 2, 3]


@pytest.mark.usefixtures("database")
def test_get_setlist_attaches_the_catalogue_details(catalogue):
    show_id = create_show()
    service.add_song_to_setlist(show_id, add_song(catalogue, "Billie Jean"))
    song = service.get_setlist(show_id)[0]["song"]
    assert song["duration_seconds"] == 294
    assert song["outfit_change_seconds"] == 90


@pytest.mark.usefixtures("database")
def test_add_song_to_setlist_refuses_no_song_missing_song_and_retired_song(catalogue):
    show_id = create_show()
    song_id = add_song(catalogue, "Billie Jean")
    catalogue[song_id]["active"] = 0
    assert service.add_song_to_setlist(show_id, None) == ["Choose a song."]
    assert service.add_song_to_setlist(show_id, 99) == [
        "That song is not in the catalogue."
    ]
    assert service.add_song_to_setlist(show_id, song_id) == ["That song is retired."]
    assert repository.list_items(show_id) == []


@pytest.mark.usefixtures("database")
def test_bad_break_is_not_saved(catalogue):
    show_id = create_show()
    errors = service.add_break_to_setlist(show_id, {"break_label": "", "break_seconds": "60"})
    assert errors == ["Break label is required."]
    assert repository.list_items(show_id) == []


@pytest.mark.usefixtures("database")
def test_retired_song_stays_in_an_existing_setlist(catalogue):
    show_id = create_show()
    song_id = add_song(catalogue, "Billie Jean")
    service.add_song_to_setlist(show_id, song_id)
    catalogue[song_id]["active"] = 0
    setlist = service.get_setlist(show_id)
    assert setlist[0]["song"]["active"] == 0


@pytest.mark.usefixtures("database")
def test_move_item_saves_the_new_order(catalogue):
    show_id = create_show()
    for title in ["Billie Jean", "Beat It", "Thriller"]:
        service.add_song_to_setlist(show_id, add_song(catalogue, title))
    last_item_id = repository.list_items(show_id)[2]["id"]
    service.move_item(show_id, last_item_id, "up")
    assert item_labels(show_id) == ["Billie Jean", "Thriller", "Beat It"]


@pytest.mark.usefixtures("database")
def test_remove_item_closes_the_gap_in_positions(catalogue):
    show_id = create_show()
    for title in ["Billie Jean", "Beat It", "Thriller"]:
        service.add_song_to_setlist(show_id, add_song(catalogue, title))
    middle_item_id = repository.list_items(show_id)[1]["id"]
    service.remove_item(show_id, middle_item_id)
    assert item_labels(show_id) == ["Billie Jean", "Thriller"]
    positions = [item["position"] for item in repository.list_items(show_id)]
    assert positions == [1, 2]

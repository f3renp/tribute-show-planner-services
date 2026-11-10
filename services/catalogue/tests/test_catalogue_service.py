"""Tests for the catalogue functions that save and read through SQLite.

Each test starts with an empty temporary database (the database fixture
in conftest.py).
"""
import pytest

from catalogue import repository, service

# Every test in this file runs with the database fixture.
pytestmark = pytest.mark.usefixtures("database")


def add_outfit(name="Red jacket", change_seconds="90"):
    """Save an outfit and return its id."""
    assert service.add_outfit({"name": name, "change_seconds": change_seconds}) == []
    return repository.find_outfit_by_name(name)["id"]


def song_form(outfit_id, title="Billie Jean", album="Thriller"):
    """A valid song form for the given outfit."""
    return {
        "title": title,
        "album": album,
        "year": "1982",
        "duration": "4:54",
        "energy": "4",
        "kind": "dance",
        "outfit_id": str(outfit_id),
    }


def add_song(outfit_id, title="Billie Jean", album="Thriller"):
    """Save a song and return its id."""
    assert service.add_song(song_form(outfit_id, title, album)) == []
    return repository.find_song_by_title_and_album(title, album)["id"]


# Outfits ----------------------------------------------------------------


def test_add_outfit_saves_it():
    outfit_id = add_outfit("Red jacket", "90")
    assert repository.get_outfit(outfit_id)["change_seconds"] == 90


def test_add_outfit_rejects_a_duplicate_name():
    add_outfit("Red jacket")
    errors = service.add_outfit({"name": "Red jacket", "change_seconds": "30"})
    assert errors == ["An outfit with this name already exists."]
    assert len(repository.list_outfits()) == 1


def test_add_outfit_with_a_bad_form_saves_nothing():
    errors = service.add_outfit({"name": "", "change_seconds": "90"})
    assert errors == ["Name is required."]
    assert repository.list_outfits() == []


# Adding and editing songs -----------------------------------------------


def test_add_song_saves_typed_values():
    song_id = add_song(add_outfit())
    song = repository.get_song(song_id)
    assert song["title"] == "Billie Jean"
    assert song["duration_seconds"] == 294
    assert song["active"] == 1


def test_add_song_with_a_bad_form_saves_nothing():
    form = dict(song_form(add_outfit()), energy="9")
    assert service.add_song(form) == ["Energy must be between 1 and 5."]
    assert repository.list_songs() == []


def test_add_song_rejects_an_outfit_that_does_not_exist():
    errors = service.add_song(song_form(outfit_id=99))
    assert errors == ["That outfit does not exist."]


def test_add_song_rejects_the_same_title_and_album():
    outfit_id = add_outfit()
    add_song(outfit_id)
    errors = service.add_song(song_form(outfit_id))
    assert errors == ["This title and album is already in the catalogue."]


def test_same_title_on_another_album_is_allowed():
    outfit_id = add_outfit()
    add_song(outfit_id, "Billie Jean", "Thriller")
    add_song(outfit_id, "Billie Jean", "HIStory")
    assert len(repository.list_songs()) == 2


def test_edit_song_saves_the_changes():
    outfit_id = add_outfit()
    song_id = add_song(outfit_id)
    form = dict(song_form(outfit_id), duration="5:10")
    assert service.edit_song(song_id, form) == []
    assert repository.get_song(song_id)["duration_seconds"] == 310


def test_edit_song_is_not_a_duplicate_of_itself():
    outfit_id = add_outfit()
    song_id = add_song(outfit_id)
    assert service.edit_song(song_id, song_form(outfit_id)) == []


def test_edit_song_rejects_taking_another_songs_title_and_album():
    outfit_id = add_outfit()
    add_song(outfit_id, "Billie Jean", "Thriller")
    song_id = add_song(outfit_id, "Beat It", "Thriller")
    errors = service.edit_song(song_id, song_form(outfit_id, "Billie Jean", "Thriller"))
    assert errors == ["This title and album is already in the catalogue."]
    assert repository.get_song(song_id)["title"] == "Beat It"


# Retiring and the functions the show builder uses -----------------------


def test_retired_song_is_kept_but_not_active():
    outfit_id = add_outfit()
    song_id = add_song(outfit_id)
    service.retire_song(song_id)
    assert repository.get_song(song_id)["active"] == 0
    assert service.list_active_songs() == []


def test_reactivated_song_is_active_again():
    song_id = add_song(add_outfit())
    service.retire_song(song_id)
    service.reactivate_song(song_id)
    assert [song["id"] for song in service.list_active_songs()] == [song_id]


def test_get_songs_by_ids_includes_the_outfit_change_time():
    song_id = add_song(add_outfit("Red jacket", "90"))
    songs = service.get_songs_by_ids([song_id])
    assert songs[song_id]["outfit_name"] == "Red jacket"
    assert songs[song_id]["outfit_change_seconds"] == 90


def test_get_songs_by_ids_leaves_out_ids_that_do_not_exist():
    song_id = add_song(add_outfit())
    assert list(service.get_songs_by_ids([song_id, 99])) == [song_id]


def test_get_songs_by_ids_with_no_ids_is_empty():
    assert service.get_songs_by_ids([]) == {}

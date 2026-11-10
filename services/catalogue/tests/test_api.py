"""Tests for /health and the JSON endpoints the shows service calls.

create_app() seeds the demo catalogue into the temporary database, so the
demo songs are there to ask for.
"""
import pytest

import main
from catalogue import repository

pytestmark = pytest.mark.usefixtures("database")


@pytest.fixture
def client():
    return main.create_app().test_client()


def song_id(title, album):
    return repository.find_song_by_title_and_album(title, album)["id"]


def test_health_says_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_songs_by_ids_returns_the_details_the_show_builder_needs(client):
    billie_jean = song_id("Billie Jean", "Thriller")
    response = client.get(f"/api/songs?ids={billie_jean}")
    assert response.status_code == 200
    [song] = response.get_json()
    assert song["id"] == billie_jean
    assert song["duration_seconds"] == 294
    assert song["outfit_name"] == "Sequin jacket"
    assert song["outfit_change_seconds"] == 120


def test_songs_by_ids_leaves_out_unknown_ids(client):
    billie_jean = song_id("Billie Jean", "Thriller")
    response = client.get(f"/api/songs?ids={billie_jean},9999")
    assert [song["id"] for song in response.get_json()] == [billie_jean]


def test_songs_by_ids_with_no_ids_is_empty(client):
    assert client.get("/api/songs").get_json() == []


def test_songs_by_ids_rejects_ids_that_are_not_numbers(client):
    assert client.get("/api/songs?ids=1,two").status_code == 400


def test_active_songs_leave_out_retired_ones(client):
    titles = [song["title"] for song in client.get("/api/songs/active").get_json()]
    assert "Billie Jean" in titles
    assert "Ben" not in titles

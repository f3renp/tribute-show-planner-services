"""Tests for seed.py, each on an empty temporary database."""
import pytest

import seed
from catalogue import repository, service

pytestmark = pytest.mark.usefixtures("database")


def test_empty_catalogue_gets_every_demo_outfit_and_song():
    assert seed.seed_demo_catalogue() is True
    assert len(repository.list_outfits()) == len(seed.DEMO_OUTFITS)
    assert len(repository.list_songs()) == len(seed.DEMO_SONGS)


def test_demo_songs_keep_their_outfit_and_duration():
    seed.seed_demo_catalogue()
    song = repository.find_song_by_title_and_album("Smooth Criminal", "Bad")
    assert song["duration_seconds"] == 4 * 60 + 17
    outfit = repository.get_outfit(song["outfit_id"])
    assert outfit["name"] == "White suit and fedora"


def test_listed_demo_songs_start_retired():
    seed.seed_demo_catalogue()
    active_titles = [song["title"] for song in service.list_active_songs()]
    assert "Ben" not in active_titles
    assert len(active_titles) == len(seed.DEMO_SONGS) - len(seed.RETIRED_DEMO_SONGS)


def test_seeding_twice_adds_nothing_the_second_time():
    seed.seed_demo_catalogue()
    assert seed.seed_demo_catalogue() is False
    assert len(repository.list_songs()) == len(seed.DEMO_SONGS)


def test_catalogue_with_one_outfit_is_not_seeded():
    service.add_outfit({"name": "My own outfit", "change_seconds": "60"})
    assert seed.seed_demo_catalogue() is False
    assert len(repository.list_outfits()) == 1
    assert repository.list_songs() == []

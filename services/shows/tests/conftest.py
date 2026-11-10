"""Shared test setup. pytest loads this file before the tests in tests/."""
import pytest

import config
import db
from shows import catalogue_client


@pytest.fixture
def database(tmp_path, monkeypatch):
    """Point the service at a new, empty SQLite file for one test.

    tmp_path is a fresh folder pytest creates for each test, and monkeypatch
    puts config.DATABASE_PATH back when the test ends, so tests never touch
    data/shows.db or each other's data.
    """
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "test.db"))
    db.init_db()


@pytest.fixture
def catalogue(monkeypatch):
    """A fake catalogue service: a dict {song_id: song} the test fills in.

    The two catalogue_client functions are replaced so they read this dict
    instead of calling the catalogue over HTTP. They return the same shapes
    as the real API, so the show builder code under test does not know the
    difference.
    """
    songs = {}

    def get_songs_by_ids(song_ids):
        return {song_id: dict(songs[song_id]) for song_id in song_ids if song_id in songs}

    def list_active_songs():
        return [dict(song) for song in songs.values() if song["active"]]

    monkeypatch.setattr(catalogue_client, "get_songs_by_ids", get_songs_by_ids)
    monkeypatch.setattr(catalogue_client, "list_active_songs", list_active_songs)
    return songs

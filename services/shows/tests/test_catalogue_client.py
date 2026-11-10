"""Tests for shows/catalogue_client.py and /health.

urlopen is replaced by a fake that records the URL it was asked for and
answers with a fixed JSON body, so no test needs the catalogue running.
"""
import io
import json

import pytest

import config
import main
from shows import catalogue_client


@pytest.fixture
def fake_catalogue_api(monkeypatch):
    """Make urlopen answer with calls["body"] and record each URL in calls["urls"]."""
    calls = {"urls": [], "body": []}

    def fake_urlopen(url, timeout):
        calls["urls"].append(url)
        return io.BytesIO(json.dumps(calls["body"]).encode())

    monkeypatch.setattr(catalogue_client, "urlopen", fake_urlopen)
    monkeypatch.setattr(config, "CATALOGUE_URL", "http://catalogue:8000/")
    return calls


def test_songs_by_ids_asks_once_and_keys_the_result_by_id(fake_catalogue_api):
    fake_catalogue_api["body"] = [{"id": 7, "title": "Bad"}, {"id": 3, "title": "Ben"}]
    songs = catalogue_client.get_songs_by_ids([7, 3, 7])
    assert songs == {7: {"id": 7, "title": "Bad"}, 3: {"id": 3, "title": "Ben"}}
    assert fake_catalogue_api["urls"] == ["http://catalogue:8000/api/songs?ids=3%2C7"]


def test_songs_by_ids_with_no_ids_makes_no_request(fake_catalogue_api):
    assert catalogue_client.get_songs_by_ids([]) == {}
    assert fake_catalogue_api["urls"] == []


def test_active_songs_come_from_the_active_endpoint(fake_catalogue_api):
    fake_catalogue_api["body"] = [{"id": 1, "title": "Bad", "active": 1}]
    assert catalogue_client.list_active_songs() == [{"id": 1, "title": "Bad", "active": 1}]
    assert fake_catalogue_api["urls"] == ["http://catalogue:8000/api/songs/active"]


@pytest.mark.usefixtures("database")
def test_health_says_ok():
    response = main.create_app().test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}

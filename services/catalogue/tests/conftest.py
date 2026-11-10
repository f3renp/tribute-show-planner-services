"""Shared test setup. pytest loads this file before the tests in tests/."""
import pytest

import config
import db


@pytest.fixture
def database(tmp_path, monkeypatch):
    """Point the service at a new, empty SQLite file for one test.

    tmp_path is a fresh folder pytest creates for each test, and monkeypatch
    puts config.DATABASE_PATH back when the test ends, so tests never touch
    data/catalogue.db or each other's data.
    """
    monkeypatch.setattr(config, "DATABASE_PATH", str(tmp_path / "test.db"))
    db.init_db()

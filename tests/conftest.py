"""Shared pytest fixtures for the test suite."""

import pytest

from backend.core import db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    yield

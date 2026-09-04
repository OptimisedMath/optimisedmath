import pytest

from backend.core import db
from tests.support.fixture_curriculum import build_fixture_curriculum


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "users.db")
    db.init_db()
    yield


@pytest.fixture
def fixture_curriculum():
    return build_fixture_curriculum()

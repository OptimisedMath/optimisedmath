import pytest

import backend.config as config
from backend.curriculum_loader import TopicDict
from backend.models import ChapterFrontier
from backend.play_mode import AdminPlayMode, StudentPlayMode, resolve_play_mode


def _chapter_topics() -> list[TopicDict]:
    return [
        {"topic_id": 10, "name": "Topic A", "max_level": 3, "radio_only": False},
        {"topic_id": 20, "name": "Topic B", "max_level": 5, "radio_only": False},
        {"topic_id": 30, "name": "Topic C", "max_level": 2, "radio_only": False},
    ]


def _stored_frontier() -> ChapterFrontier:
    return ChapterFrontier(frontier_topic_id=20, frontier_level=2)


@pytest.mark.parametrize(
    ("username", "expected_admin"),
    [
        ("student", False),
        ("", False),
        (None, False),
        ("Antoni", True),
        ("Antonio", True),
        ("Tony", True),
    ],
)
def test_resolve_play_mode_identity(username, expected_admin):
    mode = resolve_play_mode(username)
    assert mode.is_admin is expected_admin
    if expected_admin:
        assert isinstance(mode, AdminPlayMode)
    else:
        assert isinstance(mode, StudentPlayMode)


@pytest.mark.parametrize(
    ("mode_factory", "expected_topic", "expected_level"),
    [
        (StudentPlayMode, 20, 2),
        (AdminPlayMode, 30, 2),
    ],
)
def test_effective_frontier(mode_factory, expected_topic, expected_level):
    chapter_topics = _chapter_topics()
    stored = _stored_frontier()
    mode = mode_factory()

    frontier = mode.resolve_frontier(chapter_topics, stored)

    assert frontier.frontier_topic_id == expected_topic
    assert frontier.frontier_level == expected_level


@pytest.mark.parametrize(
    ("mode_factory", "persists_profile", "reveals_correct_answer"),
    [
        (StudentPlayMode, True, False),
        (AdminPlayMode, False, True),
    ],
)
def test_persistence_and_reveal_flags(
    mode_factory, persists_profile, reveals_correct_answer
):
    mode = mode_factory()
    assert mode.persists_profile is persists_profile
    assert mode.reveals_correct_answer is reveals_correct_answer


def test_resolve_play_mode_uses_config_admin_usernames():
    admin_name = next(iter(config.ADMIN_USERNAMES))
    assert resolve_play_mode(admin_name).is_admin is True

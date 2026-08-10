"""Table-driven tests for play mode resolution (student vs admin adapters)."""

import pytest

import backend.config as config
from backend.curriculum_loader import TopicDict
from backend.models import ChapterFrontier
from backend.play_mode import AdminPlayMode, StudentPlayMode, resolve_play_mode
from backend.unlock import Frontier


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

    frontier = mode.effective_frontier(chapter_topics, stored)

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


@pytest.mark.parametrize(
    ("mode_factory", "expected_topic", "expected_level"),
    [
        (StudentPlayMode, 20, 2),
        (AdminPlayMode, 10, 1),
    ],
)
def test_implicit_chapter_landing(mode_factory, expected_topic, expected_level):
    chapter_topics = _chapter_topics()
    stored = _stored_frontier()
    mode = mode_factory()

    topic_id, level = mode.implicit_chapter_landing(chapter_topics, stored)

    assert (topic_id, level) == (expected_topic, expected_level)


@pytest.mark.parametrize(
    ("mode_factory", "target_topic", "expected_level"),
    [
        (StudentPlayMode, 10, 1),
        (StudentPlayMode, 20, 2),
        (StudentPlayMode, 30, 2),
        (AdminPlayMode, 10, 1),
        (AdminPlayMode, 20, 1),
        (AdminPlayMode, 30, 1),
    ],
)
def test_implicit_topic_landing(mode_factory, target_topic, expected_level):
    chapter_topics = _chapter_topics()
    stored = _stored_frontier()
    mode = mode_factory()

    level = mode.implicit_topic_landing(chapter_topics, target_topic, stored)

    assert level == expected_level


def test_resolve_play_mode_uses_config_admin_usernames():
    admin_name = next(iter(config.ADMIN_USERNAMES))
    assert resolve_play_mode(admin_name).is_admin is True


@pytest.mark.parametrize(
    ("mode_factory", "expected_completed", "expected_total"),
    [
        (StudentPlayMode, 1, 3),
        (AdminPlayMode, 3, 3),
    ],
)
def test_chapter_progress_counts(mode_factory, expected_completed, expected_total):
    chapter_topics = _chapter_topics()
    frontier = Frontier(frontier_topic_id=20, frontier_level=2)
    mode = mode_factory()

    completed, total = mode.chapter_progress_counts(chapter_topics, frontier)

    assert (completed, total) == (expected_completed, expected_total)


@pytest.mark.parametrize(
    ("mode_factory", "selected_level", "expected_completed"),
    [
        (StudentPlayMode, 1, 0),
        (StudentPlayMode, 3, 2),
        (AdminPlayMode, 1, 5),
        (AdminPlayMode, 3, 5),
    ],
)
def test_topic_progress_counts(mode_factory, selected_level, expected_completed):
    mode = mode_factory()

    completed, total = mode.topic_progress_counts(5, selected_level)

    assert (completed, total) == (expected_completed, 5)


@pytest.mark.parametrize(
    ("mode_factory", "has_frontier_record", "selected_topic_id", "expected"),
    [
        (StudentPlayMode, True, 10, True),
        (StudentPlayMode, True, 20, False),
        (StudentPlayMode, False, 10, False),
        (StudentPlayMode, True, None, False),
        (AdminPlayMode, True, 10, False),
    ],
)
def test_has_next_unlocked_topic(
    mode_factory, has_frontier_record, selected_topic_id, expected
):
    frontier = Frontier(frontier_topic_id=20, frontier_level=2)
    mode = mode_factory()

    result = mode.has_next_unlocked_topic(
        frontier, has_frontier_record, selected_topic_id
    )

    assert result is expected

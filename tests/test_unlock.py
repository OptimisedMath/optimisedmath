"""Unit tests for the Unlock module (frontier read/write rules)."""

import pytest

from backend.models import ChapterProgress
from backend.unlock import (
    AdvanceResult,
    UnlockFrontier,
    accessible_topics,
    advance_on_mastery,
    can_access,
    first_topic_id,
    get_frontier,
    level_limit,
)


def _topics(*topic_ids: int) -> list[dict]:
    return [
        {"topic_id": tid, "name": f"T{tid}", "max_level": 3, "text_mode_disabled": False}
        for tid in topic_ids
    ]


def test_first_topic_id_uses_curriculum_order_not_numeric_min():
    chapter_topics = _topics(50, 10, 30)

    assert first_topic_id(chapter_topics) == 50
    assert first_topic_id(chapter_topics) != min(t["topic_id"] for t in chapter_topics)


def test_get_frontier_defaults_when_progress_missing():
    chapter_topics = _topics(10, 20)
    frontier = get_frontier(None, chapter_topics)

    assert frontier == UnlockFrontier(unlocked_topic_id=10, unlocked_level=1)


def test_get_frontier_reads_progress():
    progress = ChapterProgress(unlocked_topic_id=20, unlocked_level=2)
    frontier = get_frontier(progress, _topics(10, 20))

    assert frontier == UnlockFrontier(unlocked_topic_id=20, unlocked_level=2)


@pytest.mark.parametrize(
    ("topic_id", "level", "expected"),
    [
        (10, 1, True),
        (10, 2, True),
        (10, 3, False),
        (20, 1, False),
    ],
)
def test_can_access_frontier_topic_and_level(topic_id, level, expected):
    frontier = UnlockFrontier(unlocked_topic_id=10, unlocked_level=2)

    assert can_access(topic_id, level, frontier) is expected


def test_can_access_allows_replaying_completed_topic():
    frontier = UnlockFrontier(unlocked_topic_id=20, unlocked_level=2)

    assert can_access(10, 3, frontier) is True


def test_can_access_admin_bypass():
    frontier = UnlockFrontier(unlocked_topic_id=10, unlocked_level=1)

    assert can_access(99, 99, frontier, admin_mode=True) is True


def test_level_limit_at_frontier_topic():
    frontier = UnlockFrontier(unlocked_topic_id=10, unlocked_level=2)

    assert level_limit(10, 5, frontier) == 2


def test_level_limit_on_completed_topic():
    frontier = UnlockFrontier(unlocked_topic_id=20, unlocked_level=1)

    assert level_limit(10, 5, frontier) == 5


def test_level_limit_admin():
    frontier = UnlockFrontier(unlocked_topic_id=10, unlocked_level=1)

    assert level_limit(10, 5, frontier, admin_mode=True) == 5


def test_accessible_topics_filters_to_frontier():
    chapter_topics = _topics(10, 20, 30)
    frontier = UnlockFrontier(unlocked_topic_id=20, unlocked_level=2)

    visible = accessible_topics(chapter_topics, frontier)

    assert [t["topic_id"] for t in visible] == [10, 20]


def test_accessible_topics_admin_sees_all():
    chapter_topics = _topics(10, 20, 30)
    frontier = UnlockFrontier(unlocked_topic_id=10, unlocked_level=1)

    visible = accessible_topics(chapter_topics, frontier, admin_mode=True)

    assert len(visible) == 3


def test_advance_on_mastery_unlocks_next_level():
    result = advance_on_mastery(1, 3, (20, 30))

    assert result == AdvanceResult(
        level_unlocked=True,
        new_unlocked_level=2,
        new_selected_level=2,
    )


def test_advance_on_mastery_completes_topic_and_advances():
    result = advance_on_mastery(3, 3, (20, 30))

    assert result == AdvanceResult(
        topic_completed=True,
        unlock_topic_id=20,
        new_unlocked_level=1,
    )


def test_advance_on_mastery_completes_last_topic_without_next():
    result = advance_on_mastery(3, 3, ())

    assert result == AdvanceResult(topic_completed=True)

"""Unit tests for the Unlock module (Frontier read/write rules)."""

import pytest

from backend.models import ChapterFrontier
from backend.unlock import (
    AdvanceResult,
    Frontier,
    FrontierZone,
    accessible_topics,
    advance_on_mastery,
    can_access,
    chapter_max_frontier,
    classify_frontier_zone,
    effective_frontier,
    first_topic_id,
    get_frontier,
    level_limit,
)


def _topics(*topic_ids: int) -> list[dict]:
    return [
        {"topic_id": tid, "name": f"T{tid}", "max_level": 3, "radio_only": False}
        for tid in topic_ids
    ]


def test_first_topic_id_uses_curriculum_order_not_numeric_min():
    chapter_topics = _topics(50, 10, 30)

    assert first_topic_id(chapter_topics) == 50
    assert first_topic_id(chapter_topics) != min(t["topic_id"] for t in chapter_topics)


def test_get_frontier_defaults_when_progress_missing():
    chapter_topics = _topics(10, 20)
    frontier = get_frontier(None, chapter_topics)

    assert frontier == Frontier(frontier_topic_id=10, frontier_level=1)


def test_get_frontier_reads_progress():
    progress = ChapterFrontier(frontier_topic_id=20, frontier_level=2)
    frontier = get_frontier(progress, _topics(10, 20))

    assert frontier == Frontier(frontier_topic_id=20, frontier_level=2)


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
    frontier = Frontier(frontier_topic_id=10, frontier_level=2)

    assert can_access(topic_id, level, frontier) is expected


def test_can_access_allows_replaying_completed_topic():
    frontier = Frontier(frontier_topic_id=20, frontier_level=2)

    assert can_access(10, 3, frontier) is True


def test_effective_frontier_returns_chapter_max_for_admin():
    chapter_topics = _topics(10, 20, 30)
    stored = ChapterFrontier(frontier_topic_id=10, frontier_level=1)

    effective = effective_frontier(
        chapter_topics, stored, admin_mode=True
    )

    assert effective == chapter_max_frontier(chapter_topics)
    assert effective.frontier_topic_id == 30
    assert effective.frontier_level == 3


def test_effective_frontier_returns_stored_for_student():
    chapter_topics = _topics(10, 20)
    stored = ChapterFrontier(frontier_topic_id=20, frontier_level=2)

    effective = effective_frontier(
        chapter_topics, stored, admin_mode=False
    )

    assert effective == get_frontier(stored, chapter_topics)


def test_can_access_with_effective_admin_frontier():
    chapter_topics = _topics(10, 20, 30)
    stored = ChapterFrontier(frontier_topic_id=10, frontier_level=1)
    effective = effective_frontier(
        chapter_topics, stored, admin_mode=True
    )

    assert can_access(30, 3, effective) is True
    assert can_access(99, 99, effective) is False


def test_level_limit_at_frontier_topic():
    frontier = Frontier(frontier_topic_id=10, frontier_level=2)

    assert level_limit(10, 5, frontier) == 2


def test_level_limit_on_completed_topic():
    frontier = Frontier(frontier_topic_id=20, frontier_level=1)

    assert level_limit(10, 5, frontier) == 5


def test_level_limit_with_effective_admin_frontier():
    chapter_topics = _topics(10, 20, 30)
    stored = ChapterFrontier(frontier_topic_id=10, frontier_level=1)
    effective = effective_frontier(
        chapter_topics, stored, admin_mode=True
    )

    assert level_limit(10, 5, effective) == 5
    assert level_limit(30, 3, effective) == 3


def test_accessible_topics_filters_to_frontier():
    chapter_topics = _topics(10, 20, 30)
    frontier = Frontier(frontier_topic_id=20, frontier_level=2)

    visible = accessible_topics(chapter_topics, frontier)

    assert [t["topic_id"] for t in visible] == [10, 20]


def test_accessible_topics_with_effective_admin_frontier():
    chapter_topics = _topics(10, 20, 30)
    stored = ChapterFrontier(frontier_topic_id=10, frontier_level=1)
    effective = effective_frontier(
        chapter_topics, stored, admin_mode=True
    )

    visible = accessible_topics(chapter_topics, effective)

    assert len(visible) == 3


def test_advance_on_mastery_unlocks_next_level():
    result = advance_on_mastery(1, 3, (20, 30))

    assert result == AdvanceResult(
        level_unlocked=True,
        new_frontier_level=2,
        new_selected_level=2,
    )


def test_advance_on_mastery_completes_topic_and_advances():
    result = advance_on_mastery(3, 3, (20, 30))

    assert result == AdvanceResult(
        topic_completed=True,
        unlock_topic_id=20,
        new_frontier_level=1,
    )


def test_advance_on_mastery_completes_last_topic_without_next():
    result = advance_on_mastery(3, 3, ())

    assert result == AdvanceResult(topic_completed=True)


@pytest.mark.parametrize(
    ("topic_id", "level", "frontier_topic_id", "frontier_level", "expected"),
    [
        (20, 1, 10, 2, FrontierZone.BEYOND),
        (10, 3, 10, 2, FrontierZone.BEYOND),
        (10, 2, 10, 2, FrontierZone.AT),
        (10, 1, 10, 2, FrontierZone.BEHIND),
        (10, 3, 20, 2, FrontierZone.BEHIND),
    ],
)
def test_classify_frontier_zone(
    topic_id, level, frontier_topic_id, frontier_level, expected
):
    frontier = Frontier(
        frontier_topic_id=frontier_topic_id,
        frontier_level=frontier_level,
    )

    assert (
        classify_frontier_zone(topic_id, level, frontier) == expected
    )

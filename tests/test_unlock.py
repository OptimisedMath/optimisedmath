"""Unit tests for the Unlock module (UnlockedProgress read/write rules)."""

import pytest

from backend.models import ChapterProgress
from backend.unlock import (
    AdvanceResult,
    UnlockedProgress,
    accessible_topics,
    advance_on_mastery,
    can_access,
    first_topic_id,
    get_unlocked_progress,
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


def test_get_unlocked_progress_defaults_when_progress_missing():
    chapter_topics = _topics(10, 20)
    unlocked_progress = get_unlocked_progress(None, chapter_topics)

    assert unlocked_progress == UnlockedProgress(unlocked_topic_id=10, unlocked_level=1)


def test_get_unlocked_progress_reads_progress():
    progress = ChapterProgress(unlocked_topic_id=20, unlocked_level=2)
    unlocked_progress = get_unlocked_progress(progress, _topics(10, 20))

    assert unlocked_progress == UnlockedProgress(unlocked_topic_id=20, unlocked_level=2)


@pytest.mark.parametrize(
    ("topic_id", "level", "expected"),
    [
        (10, 1, True),
        (10, 2, True),
        (10, 3, False),
        (20, 1, False),
    ],
)
def test_can_access_unlocked_progress_topic_and_level(topic_id, level, expected):
    unlocked_progress = UnlockedProgress(unlocked_topic_id=10, unlocked_level=2)

    assert can_access(topic_id, level, unlocked_progress) is expected


def test_can_access_allows_replaying_completed_topic():
    unlocked_progress = UnlockedProgress(unlocked_topic_id=20, unlocked_level=2)

    assert can_access(10, 3, unlocked_progress) is True


def test_can_access_admin_bypass():
    unlocked_progress = UnlockedProgress(unlocked_topic_id=10, unlocked_level=1)

    assert can_access(99, 99, unlocked_progress, admin_mode=True) is True


def test_level_limit_at_unlocked_progress_topic():
    unlocked_progress = UnlockedProgress(unlocked_topic_id=10, unlocked_level=2)

    assert level_limit(10, 5, unlocked_progress) == 2


def test_level_limit_on_completed_topic():
    unlocked_progress = UnlockedProgress(unlocked_topic_id=20, unlocked_level=1)

    assert level_limit(10, 5, unlocked_progress) == 5


def test_level_limit_admin():
    unlocked_progress = UnlockedProgress(unlocked_topic_id=10, unlocked_level=1)

    assert level_limit(10, 5, unlocked_progress, admin_mode=True) == 5


def test_accessible_topics_filters_to_unlocked_progress():
    chapter_topics = _topics(10, 20, 30)
    unlocked_progress = UnlockedProgress(unlocked_topic_id=20, unlocked_level=2)

    visible = accessible_topics(chapter_topics, unlocked_progress)

    assert [t["topic_id"] for t in visible] == [10, 20]


def test_accessible_topics_admin_sees_all():
    chapter_topics = _topics(10, 20, 30)
    unlocked_progress = UnlockedProgress(unlocked_topic_id=10, unlocked_level=1)

    visible = accessible_topics(chapter_topics, unlocked_progress, admin_mode=True)

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

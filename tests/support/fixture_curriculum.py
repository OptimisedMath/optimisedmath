"""In-memory Curriculum adapter for tests — synthetic Chapters and Topics."""

from __future__ import annotations

from backend.curriculum import Curriculum
from backend.curriculum_loader import LevelConfig, TopicDict, TopicMeta

# Stable synthetic ids — assertions must not chase real Polish content.
CHAPTER_ALPHA = 100
CHAPTER_BETA = 200

TOPIC_MULTI = 101  # Chapter Alpha: levels 1–2 published, level 3 unpublished
TOPIC_RADIO = 102  # Chapter Alpha: radio-only, single published level
TOPIC_SINGLE = 201  # Chapter Beta: exactly one published level


def build_fixture_curriculum() -> Curriculum:
    """Build a fixture Curriculum covering behaviours later tickets need."""
    topics_alpha: tuple[TopicDict, ...] = (
        {
            "topic_id": TOPIC_MULTI,
            "name": "Multi Level Topic",
            "max_level": 2,
            "radio_only": False,
        },
        {
            "topic_id": TOPIC_RADIO,
            "name": "Radio Only Topic",
            "max_level": 1,
            "radio_only": True,
        },
    )
    topics_beta: tuple[TopicDict, ...] = (
        {
            "topic_id": TOPIC_SINGLE,
            "name": "Single Level Topic",
            "max_level": 1,
            "radio_only": False,
        },
    )
    topics_by_id: dict[int, dict[int, TopicMeta]] = {
        CHAPTER_ALPHA: {
            TOPIC_MULTI: {
                "name": "Multi Level Topic",
                "max_level": 2,
                "radio_only": False,
            },
            TOPIC_RADIO: {
                "name": "Radio Only Topic",
                "max_level": 1,
                "radio_only": True,
            },
        },
        CHAPTER_BETA: {
            TOPIC_SINGLE: {
                "name": "Single Level Topic",
                "max_level": 1,
                "radio_only": False,
            },
        },
    }
    level_configs: dict[tuple[int, int, int], LevelConfig] = {
        (CHAPTER_ALPHA, TOPIC_MULTI, 1): LevelConfig(
            level=1,
            name="Multi L1",
            function="fixture_multi_1",
            traps={},
            published=True,
        ),
        (CHAPTER_ALPHA, TOPIC_MULTI, 2): LevelConfig(
            level=2,
            name="Multi L2",
            function="fixture_multi_2",
            traps={},
            published=True,
        ),
        (CHAPTER_ALPHA, TOPIC_MULTI, 3): LevelConfig(
            level=3,
            name="Multi L3 unpublished",
            function="fixture_multi_3",
            traps={},
            published=False,
        ),
        (CHAPTER_ALPHA, TOPIC_RADIO, 1): LevelConfig(
            level=1,
            name="Radio L1",
            function="fixture_radio_1",
            traps={},
            published=True,
        ),
        (CHAPTER_BETA, TOPIC_SINGLE, 1): LevelConfig(
            level=1,
            name="Single L1",
            function="fixture_single_1",
            traps={},
            published=True,
        ),
    }
    return Curriculum(
        _chapter_ids=(CHAPTER_ALPHA, CHAPTER_BETA),
        _chapter_names={
            CHAPTER_ALPHA: "Chapter Alpha",
            CHAPTER_BETA: "Chapter Beta",
        },
        _topics={
            CHAPTER_ALPHA: topics_alpha,
            CHAPTER_BETA: topics_beta,
        },
        _topics_by_id=topics_by_id,
        _level_configs=level_configs,
        _keyboard_types={
            CHAPTER_ALPHA: "fraction",
            CHAPTER_BETA: "default",
        },
    )

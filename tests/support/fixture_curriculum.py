"""In-memory Curriculum adapter for tests — synthetic Chapters and Topics."""

from __future__ import annotations

from backend.curriculum import Curriculum
from backend.curriculum_loader import (
    ChapterBundle,
    ChapterSummary,
    CurriculumStore,
    LevelConfig,
    TopicDict,
)

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

    bundle_alpha = ChapterBundle(
        chapter_id=CHAPTER_ALPHA,
        chapter_name="Chapter Alpha",
        keyboard_type="fraction",
        raw={},
        topics_meta=topics_alpha,
        topics_by_id={topic["topic_id"]: topic for topic in topics_alpha},
        level_configs={
            (TOPIC_MULTI, 1): LevelConfig(
                level=1,
                name="Multi L1",
                function="fixture_multi_1",
                traps={},
                published=True,
            ),
            (TOPIC_MULTI, 2): LevelConfig(
                level=2,
                name="Multi L2",
                function="fixture_multi_2",
                traps={},
                published=True,
            ),
            (TOPIC_MULTI, 3): LevelConfig(
                level=3,
                name="Multi L3 unpublished",
                function="fixture_multi_3",
                traps={},
                published=False,
            ),
            (TOPIC_RADIO, 1): LevelConfig(
                level=1,
                name="Radio L1",
                function="fixture_radio_1",
                traps={},
                published=True,
            ),
        },
        topic_name_by_id={
            TOPIC_MULTI: "Multi Level Topic",
            TOPIC_RADIO: "Radio Only Topic",
        },
    )
    bundle_beta = ChapterBundle(
        chapter_id=CHAPTER_BETA,
        chapter_name="Chapter Beta",
        keyboard_type="default",
        raw={},
        topics_meta=topics_beta,
        topics_by_id={topic["topic_id"]: topic for topic in topics_beta},
        level_configs={
            (TOPIC_SINGLE, 1): LevelConfig(
                level=1,
                name="Single L1",
                function="fixture_single_1",
                traps={},
                published=True,
            ),
        },
        topic_name_by_id={TOPIC_SINGLE: "Single Level Topic"},
    )

    bundles = (bundle_alpha, bundle_beta)
    store = CurriculumStore(
        bundles=bundles,
        curriculum={bundle.chapter_id: list(bundle.topics_meta) for bundle in bundles},
        chapters=[
            ChapterSummary(chapter_id=bundle.chapter_id, name=bundle.chapter_name)
            for bundle in bundles
        ],
        bundles_by_chapter_id={bundle.chapter_id: bundle for bundle in bundles},
        chapter_id_by_name={
            bundle.chapter_name: bundle.chapter_id for bundle in bundles
        },
        chapter_name_by_id={
            bundle.chapter_id: bundle.chapter_name for bundle in bundles
        },
    )
    return Curriculum(_store=store)

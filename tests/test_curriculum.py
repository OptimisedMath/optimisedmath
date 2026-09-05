"""Tests for the Curriculum read model, provider, and /curriculum tracer."""

from __future__ import annotations

import asyncio

import pytest

from backend.curriculum import (
    Curriculum,
    get_curriculum_response,
    resolve_curriculum,
    set_curriculum,
)
from backend.main import curriculum_index
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    CHAPTER_BETA,
    TOPIC_MULTI,
    TOPIC_RADIO,
    TOPIC_SINGLE,
)


@pytest.fixture(autouse=True)
def _clear_curriculum_override():
    set_curriculum(None)
    yield
    set_curriculum(None)


def test_curriculum_is_immutable(fixture_curriculum: Curriculum):
    with pytest.raises(AttributeError):
        fixture_curriculum._store = None  # type: ignore[misc]


def test_fixture_curriculum_has_required_shape(fixture_curriculum: Curriculum):
    assert fixture_curriculum.chapter_ids() == (CHAPTER_ALPHA, CHAPTER_BETA)
    assert fixture_curriculum.has_chapter(CHAPTER_ALPHA)
    assert not fixture_curriculum.has_chapter(999)

    chapters = fixture_curriculum.chapters()
    assert [(c.chapter_id, c.name) for c in chapters] == [
        (CHAPTER_ALPHA, "Chapter Alpha"),
        (CHAPTER_BETA, "Chapter Beta"),
    ]

    alpha_topics = fixture_curriculum.topics(CHAPTER_ALPHA)
    assert [t["topic_id"] for t in alpha_topics] == [TOPIC_MULTI, TOPIC_RADIO]
    radio = fixture_curriculum.topic_by_id(CHAPTER_ALPHA, TOPIC_RADIO)
    assert radio is not None
    assert radio["radio_only"] is True
    assert radio["max_level"] == 1
    assert radio["topic_id"] == TOPIC_RADIO

    multi = fixture_curriculum.topic_by_id(CHAPTER_ALPHA, TOPIC_MULTI)
    assert multi is not None
    assert multi["max_level"] == 2

    single = fixture_curriculum.topic_by_id(CHAPTER_BETA, TOPIC_SINGLE)
    assert single is not None
    assert single["max_level"] == 1

    unpublished = fixture_curriculum.level_config(CHAPTER_ALPHA, TOPIC_MULTI, 3)
    assert unpublished is not None
    assert unpublished.published is False

    assert fixture_curriculum.chapter_name(CHAPTER_ALPHA) == "Chapter Alpha"
    assert (
        fixture_curriculum.topic_name(CHAPTER_ALPHA, TOPIC_MULTI) == "Multi Level Topic"
    )
    assert fixture_curriculum.keyboard_type(CHAPTER_ALPHA) == "fraction"
    assert fixture_curriculum.keyboard_type(999) == "default"


def test_provider_override_returns_fixture(fixture_curriculum: Curriculum):
    set_curriculum(fixture_curriculum)
    assert resolve_curriculum() is fixture_curriculum


def test_provider_default_is_yaml_backed():
    set_curriculum(None)
    curriculum = resolve_curriculum()
    # Real Polish chapters from backend/data/
    assert curriculum.has_chapter(10)
    assert curriculum.has_chapter(20)
    assert curriculum.chapter_name(10) == "Ułamki Zwykłe"


def test_curriculum_index_uses_fixture_not_yaml(fixture_curriculum: Curriculum):
    set_curriculum(fixture_curriculum)
    response = asyncio.run(curriculum_index())

    assert [c.chapter_id for c in response.chapters] == [CHAPTER_ALPHA, CHAPTER_BETA]
    assert response.chapters[0].name == "Chapter Alpha"
    assert response.chapters[0].topics[0].topic_id == TOPIC_MULTI
    assert response.chapters[0].topics[1].radio_only is True
    assert response.chapters[1].topics[0].topic_id == TOPIC_SINGLE
    # Must not surface real YAML chapter names
    assert all(c.name != "Ułamki Zwykłe" for c in response.chapters)


def test_get_curriculum_response_takes_curriculum(fixture_curriculum: Curriculum):
    response = get_curriculum_response(fixture_curriculum)
    assert len(response.chapters) == 2
    assert response.chapters[0].topics[0].name == "Multi Level Topic"


def test_topic_by_id_missing_topic_returns_none(fixture_curriculum: Curriculum):
    assert fixture_curriculum.topic_by_id(CHAPTER_ALPHA, 999) is None
    assert fixture_curriculum.topic_by_id(999, TOPIC_MULTI) is None


def test_clamp_level_caps_to_topic_max(fixture_curriculum: Curriculum):
    assert fixture_curriculum.clamp_level(99, CHAPTER_ALPHA, TOPIC_MULTI) == 2


def test_clamp_level_null_topic_caps_to_one(fixture_curriculum: Curriculum):
    assert fixture_curriculum.clamp_level(99, CHAPTER_ALPHA, None) == 1


def test_clamp_level_null_level_defaults_to_one(fixture_curriculum: Curriculum):
    assert fixture_curriculum.clamp_level(None, CHAPTER_ALPHA, TOPIC_MULTI) == 1

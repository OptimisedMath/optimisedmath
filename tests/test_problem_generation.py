"""Problem generation against a fixture Curriculum — no backend/data/ reads."""

import pytest

import backend.config as config
import backend.problem_generation as problem_generation
from backend.problem_generation import ProblemGenerationError, generate_level_problem
from tests.support.fixture_curriculum import (
    CHAPTER_ALPHA,
    TOPIC_MULTI,
)


def _fake_multi_1():
    return {
        "question": r"\text{fixture q}",
        "correct": "1",
        "options": ["1", "2", "3", "4"],
        "options_map": {"1": "correct", "2": "t1", "3": "t2", "4": "t3"},
    }


def test_generate_level_problem_uses_fixture_curriculum_and_fake_generator(
    fixture_curriculum, monkeypatch
):
    """A Problem can be generated from the fixture without reading backend/data/."""
    monkeypatch.setitem(
        problem_generation.FUNCTION_REGISTRY, "fixture_multi_1", _fake_multi_1
    )

    problem = generate_level_problem(
        fixture_curriculum, CHAPTER_ALPHA, TOPIC_MULTI, 1
    )

    assert problem["question"] == r"\text{fixture q}"
    assert problem["correct"] == "1"
    assert problem["level"] == 1
    assert problem["level_name"] == "Multi L1"
    assert problem["keyboard_type"] == "fraction"
    assert "problem_id" in problem


def test_unpublished_level_raises_same_error(fixture_curriculum):
    """Fixture unpublished Level surfaces the same 'Level is not available' message."""
    with pytest.raises(
        ProblemGenerationError,
        match=(
            "Level 3 is not available for topic 'Multi Level Topic' "
            f"in chapter {CHAPTER_ALPHA}"
        ),
    ):
        generate_level_problem(fixture_curriculum, CHAPTER_ALPHA, TOPIC_MULTI, 3)


def test_always_failing_generator_surfaces_same_error(
    fixture_curriculum, monkeypatch
):
    """A generator that never returns a problem keeps the prior error message."""

    def always_fail():
        return None

    monkeypatch.setitem(
        problem_generation.FUNCTION_REGISTRY, "fixture_multi_1", always_fail
    )
    monkeypatch.setattr(config, "MAX_RETRIES_GENERATE", 3)

    with pytest.raises(
        ProblemGenerationError,
        match=(
            "Failed to generate valid problem for always_fail "
            "after 3 attempts"
        ),
    ):
        generate_level_problem(fixture_curriculum, CHAPTER_ALPHA, TOPIC_MULTI, 1)

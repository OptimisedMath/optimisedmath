"""Ułamki Zwykłe, Mnożenie przez liczbę (Topic 80) — #363.

`multiplies_the_denominator_too` computes the right wrong answer by multiplying
both the numerator and the denominator — exactly what simplification undoes.
Rendering it simplified collapses it back onto a fraction already on screen, so
a Student who made that mistake cannot find their own answer among the options.
#363 also gave the Trap to Level 2, which had none for expanding instead of
cancelling. These tests assert on what a Student meets: the option string
served, never on how the generator computed it.
"""

import re

import pytest

import backend.chapters.ulamki_zwykle.topic_80_mnozenie_liczba as topic
import backend.config as config
from backend.core.utils import FILLER_SLUG
from backend.curriculum import curriculum_from_yaml
from backend.problem_generation import generate_level_problem

CHAPTER_ID = 10
TOPIC_ID = 80
SLUG = "multiplies_the_denominator_too"
ROLLS = 300
CURRICULUM_ROLLS = 50

# Each Level with a reader for its operands as (whole, n, d, k). Level 3 feeds
# the deconstruction contract, so it names them whole1/n1/d1/n2 instead.
LEVELS = [
    (topic.frac_mult_num_1, lambda p: (0, p["n"], p["d"], p["k"])),
    (topic.frac_mult_num_2, lambda p: (0, p["n"], p["d"], p["k"])),
    (topic.frac_mult_num_3, lambda p: (p["whole1"], p["n1"], p["d1"], p["n2"])),
]
GENERATORS = [generator for generator, _ in LEVELS]
LEVEL_IDS = [generator.__name__ for generator in GENERATORS]


def _question_fractions(question: str) -> set[str]:
    """Every `\\frac{a}{b}` the question prints, a mixed number's own part included."""
    return set(re.findall(r"\\frac\{\d+\}\{\d+\}", question))


def _trap_draws(generator) -> list[tuple[dict, str]]:
    """Every (Problem, option string served under SLUG) pair across ROLLS rolls.

    Rejected draws, and draws whose slots the Trap did not reach, are dropped.
    """
    draws = []
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        for value, slug in problem["options_map"].items():
            if slug == SLUG:
                draws.append((problem, value))
    return draws


@pytest.fixture(scope="module")
def curriculum():
    return curriculum_from_yaml()


@pytest.mark.parametrize("generator", GENERATORS, ids=LEVEL_IDS)
def test_multiplies_the_denominator_too_is_never_a_fraction_from_the_question(
    generator,
):
    """The option's string never matches a fraction printed in the question.

    One that did would read as the question handed back, not as a wrong answer.
    """
    draws = _trap_draws(generator)
    assert draws, f"{generator.__name__} never served {SLUG} in {ROLLS} rolls"

    for problem, value in draws:
        assert value not in _question_fractions(problem["question"])


@pytest.mark.parametrize("generator,operands", LEVELS, ids=LEVEL_IDS)
def test_multiplies_the_denominator_too_renders_the_improper_unsimplified_form(
    generator, operands
):
    """The Trap is the un-simplified fraction built from the Problem's own operands.

    Simplifying it is what collapses it back onto the question's own fraction.
    """
    draws = _trap_draws(generator)
    assert draws, f"{generator.__name__} never served {SLUG} in {ROLLS} rolls"

    for problem, value in draws:
        whole, n, d, k = operands(problem["parameters"])
        assert value == rf"\frac{{{(whole * d + n) * k}}}{{{d * k}}}"


@pytest.mark.parametrize("level", [1, 2, 3])
def test_every_served_slug_has_its_own_prose_through_the_real_curriculum(
    curriculum, level
):
    """Every slug a Level serves gets its own prose through the real curriculum.

    None of it is the generic wrong-answer message the loader falls back to.
    """
    for _ in range(CURRICULUM_ROLLS):
        problem = generate_level_problem(curriculum, CHAPTER_ID, TOPIC_ID, level)
        for slug in problem["options_map"].values():
            if slug in ("correct", FILLER_SLUG):
                continue
            assert problem["messages"][slug] != config.DEFAULT_WRONG_MESSAGE

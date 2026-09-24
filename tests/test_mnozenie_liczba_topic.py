"""Ułamki Zwykłe, Mnożenie przez liczbę (Topic 80) — #363.

`multiplies_the_denominator_too` computes the right wrong answer by multiplying
both the numerator and the denominator — exactly what simplification undoes.
Rendering it simplified collapses it back onto a fraction already on screen, so
a Student who made that mistake cannot find their own answer among the options.
These tests assert on what a Student meets: the option string served, never on
how the generator computed it.
"""

import re

import pytest

import backend.chapters.ulamki_zwykle.topic_80_mnozenie_liczba as topic
import backend.config as config
from backend.curriculum import curriculum_from_yaml
from backend.problem_generation import generate_level_problem

CHAPTER_ID = 10
TOPIC_ID = 80
SLUG = "multiplies_the_denominator_too"
ROLLS = 300


def _question_fractions(question: str) -> set[str]:
    """Every `\\frac{a}{b}` printed in the question, plus bare mixed-number pieces."""
    return set(re.findall(r"\\frac\{\d+\}\{\d+\}", question))


@pytest.fixture(scope="module")
def curriculum():
    return curriculum_from_yaml()


@pytest.mark.parametrize(
    "generator",
    [topic.frac_mult_num_1, topic.frac_mult_num_2, topic.frac_mult_num_3],
)
def test_multiplies_the_denominator_too_is_never_a_fraction_from_the_question(
    generator,
):
    """The option's string must never match a fraction printed in the question —
    otherwise it reads as the question handed back, not a wrong answer."""
    seen = False
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        for value, slug in problem["options_map"].items():
            if slug == SLUG:
                seen = True
                assert value not in _question_fractions(problem["question"])
    assert seen, f"{generator.__name__} never emitted {SLUG} in {ROLLS} rolls"


@pytest.mark.parametrize(
    "generator",
    [topic.frac_mult_num_1, topic.frac_mult_num_3],
)
def test_multiplies_the_denominator_too_renders_the_improper_unsimplified_form(
    generator,
):
    """Levels 1 and 3: the Trap is the un-simplified fraction built from the
    Problem's own operands, not the simplified value simplification undoes it to."""
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        for value, slug in problem["options_map"].items():
            if slug == SLUG:
                params = problem["parameters"]
                n = params.get("n1", params.get("n"))
                d = params.get("d1", params.get("d"))
                w = params.get("whole1", 0)
                k = params.get("n2", params.get("k"))
                num = (w * d + n) * k
                den = d * k
                assert value == rf"\frac{{{num}}}{{{den}}}"


def test_level_2_gains_the_trap_it_never_had():
    """Level 2 (Skracanie na krzyż z liczbą) previously had no Trap for expanding
    instead of cancelling; it must now serve one, un-simplified."""
    seen = False
    for _ in range(ROLLS):
        problem = topic.frac_mult_num_2()
        if problem is None:
            continue
        for value, slug in problem["options_map"].items():
            if slug == SLUG:
                seen = True
                n, d, k = (
                    problem["parameters"]["n"],
                    problem["parameters"]["d"],
                    problem["parameters"]["k"],
                )
                assert value == rf"\frac{{{n * k}}}{{{d * k}}}"
                assert value not in _question_fractions(problem["question"])
    assert seen


@pytest.mark.parametrize("level", [1, 2, 3])
def test_every_served_slug_has_its_own_prose_through_the_real_curriculum(
    curriculum, level
):
    """Loading through the real curriculum attaches prose to every slug a Level
    serves, and none of it is the generic wrong-answer message."""
    for _ in range(50):
        problem = generate_level_problem(curriculum, CHAPTER_ID, TOPIC_ID, level)
        for slug in problem["options_map"].values():
            if slug in ("correct", "filler"):
                continue
            message = problem["messages"][slug]
            assert message != config.DEFAULT_WRONG_MESSAGE

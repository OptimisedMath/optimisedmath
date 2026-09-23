"""Neither `Kolejność wykonywania działań` Topic may serve a whole number written
as a fraction over one.

A Student practising `Kolejność wykonywania działań` was shown `\\frac{1}{1}` for a
question or option wherever a whole-number operand or result appeared — the
question, the correct answer, and Traps alike (#318). The two Chapters carried the
same sum twice, hand-written as LaTeX and separately derived as an ASCII
`expression`; only the derived copy's renderer ever printed a bare integer.
ADR-0017 inverts the direction so both are one string, closing every place the
`\\frac{n}{1}` form could reappear.

Scoped to the twelve Kolejność generators, not the whole registry: `dec_to_frac_1`
in a different Topic deliberately offers `\\frac{n}{1}` as a Trap for a Student who
uses one fewer place than a decimal needs, and that Trap is untouched by this issue.

Rolled many times per generator, in the shape `test_no_negative_answers.py` uses: no
single call reveals every template a generator can draw.
"""

import re

import pytest

from backend.problem_generation import FUNCTION_REGISTRY
from tests.support.kolejnosc import KOLEJNOSC_GENERATORS

ROLLS = 400

_FRACTION_OVER_ONE_RE = re.compile(r"\\frac\{-?\d+\}\{1\}")


@pytest.mark.parametrize("name", KOLEJNOSC_GENERATORS)
def test_generator_never_serves_a_fraction_over_one(name):
    """No question or option written by a Kolejność generator reads `\\frac{n}{1}`."""
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        assert not _FRACTION_OVER_ONE_RE.search(
            problem["question"]
        ), f"{name} emitted a fraction-over-one question {problem['question']!r}"
        for option in problem["options"]:
            assert not _FRACTION_OVER_ONE_RE.search(option), (
                f"{name} emitted a fraction-over-one option {option!r} for "
                f"{problem['question']!r}"
            )

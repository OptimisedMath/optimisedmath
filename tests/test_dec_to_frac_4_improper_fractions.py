"""`dec_to_frac_4` must convert fractions greater than one, not only proper ones.

Widening the numerator range to draw numerators up to twice the denominator
(#276) means every option string has to thread the whole part through, or the
three Trap formulas stop being the specific mistakes their slugs and Polish
prose name the moment a draw rolls an improper numerator. A bare read of the
old code — proper fractions only, whole part always zero — would miss that.
"""

import re

from backend.chapters.ulamki_dziesietne.topic_10_zamiana import dec_to_frac_4

ROLLS = 500

# `1,(3)` — whole part, comma, one repeating digit in brackets. The leading zero
# is optional here because only the leading-zero Trap is allowed to carry one.
PERIOD_RE = re.compile(r"(?P<whole>\d+),(?P<leading_zero>0)?\((?P<digit>\d)\)")
# `1,3` — the same reading with the brackets dropped.
NO_BRACKETS_RE = re.compile(r"(?P<whole>\d+),(?P<digit>\d)")


def _draws() -> list[dict]:
    """Every Problem the generator emits across ROLLS rolls, rejections dropped."""
    rolls = (dec_to_frac_4() for _ in range(ROLLS))
    return [problem for problem in rolls if problem is not None]


def _traps_by_slug(problem: dict) -> dict[str, str]:
    """The Problem's Trap answers keyed by slug, the inverse of `options_map`."""
    return {slug: value for value, slug in problem["options_map"].items()}


def _whole_part(problem: dict) -> int:
    """The whole part the Problem's own parameters imply, computed independently."""
    return problem["parameters"]["n"] // problem["parameters"]["d"]


def test_draws_both_proper_and_improper_numerators():
    """Both sides of the widened range are reachable, not just the old proper draws."""
    numerators = [(p["parameters"]["n"], p["parameters"]["d"]) for p in _draws()]

    assert any(n < d for n, d in numerators), f"no proper draw in {ROLLS} rolls"
    assert any(n > d for n, d in numerators), f"no improper draw in {ROLLS} rolls"


def test_numerators_never_exceed_twice_the_denominator():
    """The widened range stops at 2d, so the whole part never runs past one."""
    for problem in _draws():
        n, d = problem["parameters"]["n"], problem["parameters"]["d"]
        assert n <= 2 * d, f"numerator {n} exceeds twice the denominator {d}"


def test_a_numerator_equal_to_the_denominator_is_never_emitted():
    """`n == d` divides exactly, leaving no period for the Level to ask about."""
    for problem in _draws():
        n, d = problem["parameters"]["n"], problem["parameters"]["d"]
        assert n != d, "a numerator equal to the denominator has no period"


def test_correct_answer_carries_the_whole_part_with_a_single_digit_period():
    """The correct answer reads `w,(digit)` — whole part in, no padding zero."""
    for problem in _draws():
        match = PERIOD_RE.fullmatch(problem["correct"])
        assert match, f"unexpected correct format {problem['correct']!r}"
        assert (
            match["leading_zero"] is None
        ), "correct answer must not have a leading zero"
        assert int(match["whole"]) == _whole_part(problem)


def test_traps_thread_the_whole_part_on_improper_draws():
    """Each Trap keeps the whole part, so it stays the one mistake its slug names."""
    improper = [p for p in _draws() if p["parameters"]["n"] > p["parameters"]["d"]]
    assert improper, f"no improper draw seen in {ROLLS} rolls"

    for problem in improper:
        w = _whole_part(problem)
        period_digit = int(PERIOD_RE.fullmatch(problem["correct"])["digit"])
        traps = _traps_by_slug(problem)

        omits = NO_BRACKETS_RE.fullmatch(traps["omits_the_period_brackets"])
        assert omits, traps["omits_the_period_brackets"]
        assert int(omits["whole"]) == w
        assert int(omits["digit"]) == period_digit

        leading_zero = PERIOD_RE.fullmatch(
            traps["adds_a_leading_zero_before_the_period"]
        )
        assert leading_zero, traps["adds_a_leading_zero_before_the_period"]
        assert leading_zero["leading_zero"] == "0"
        assert int(leading_zero["whole"]) == w
        assert int(leading_zero["digit"]) == period_digit

        wrong_digit = PERIOD_RE.fullmatch(traps["gets_the_period_digit_wrong"])
        assert wrong_digit, traps["gets_the_period_digit_wrong"]
        assert int(wrong_digit["whole"]) == w
        assert int(wrong_digit["digit"]) == period_digit + 1

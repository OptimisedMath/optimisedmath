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

CORRECT_RE = re.compile(r"^(\d+),(0)?\((\d)\)$")
NO_BRACKETS_RE = re.compile(r"^(\d+),(\d)$")


def test_draws_both_proper_and_improper_numerators():
    proper = improper = False
    for _ in range(ROLLS):
        problem = dec_to_frac_4()
        if problem is None:
            continue
        n, d = problem["parameters"]["n"], problem["parameters"]["d"]
        proper = proper or n < d
        improper = improper or n > d
        if proper and improper:
            break

    assert proper, f"no proper draw in {ROLLS} rolls"
    assert improper, f"no improper draw in {ROLLS} rolls"


def test_numerators_never_exceed_twice_the_denominator():
    for _ in range(ROLLS):
        problem = dec_to_frac_4()
        if problem is None:
            continue
        n, d = problem["parameters"]["n"], problem["parameters"]["d"]
        assert n != d, "a numerator equal to the denominator has no period"
        assert n <= 2 * d, f"numerator {n} exceeds twice the denominator {d}"


def test_correct_answer_carries_the_whole_part_with_a_single_digit_period():
    for _ in range(ROLLS):
        problem = dec_to_frac_4()
        if problem is None:
            continue
        n, d = problem["parameters"]["n"], problem["parameters"]["d"]
        w = n // d

        match = CORRECT_RE.fullmatch(problem["correct"])
        assert match, f"unexpected correct format {problem['correct']!r}"
        assert match.group(2) is None, "correct answer must not have a leading zero"
        assert int(match.group(1)) == w


def test_traps_thread_the_whole_part_on_improper_draws():
    seen_improper = False
    for _ in range(ROLLS):
        problem = dec_to_frac_4()
        if problem is None:
            continue
        n, d = problem["parameters"]["n"], problem["parameters"]["d"]
        if n < d:
            continue
        seen_improper = True
        w = n // d

        correct_match = CORRECT_RE.fullmatch(problem["correct"])
        period_digit = int(correct_match.group(3))
        by_slug = {slug: value for value, slug in problem["options_map"].items()}

        omits = NO_BRACKETS_RE.fullmatch(by_slug["omits_the_period_brackets"])
        assert omits, by_slug["omits_the_period_brackets"]
        assert int(omits.group(1)) == w
        assert int(omits.group(2)) == period_digit

        leading_zero = CORRECT_RE.fullmatch(
            by_slug["adds_a_leading_zero_before_the_period"]
        )
        assert leading_zero, by_slug["adds_a_leading_zero_before_the_period"]
        assert leading_zero.group(2) == "0"
        assert int(leading_zero.group(1)) == w
        assert int(leading_zero.group(3)) == period_digit

        wrong_digit = CORRECT_RE.fullmatch(by_slug["gets_the_period_digit_wrong"])
        assert wrong_digit, by_slug["gets_the_period_digit_wrong"]
        assert int(wrong_digit.group(1)) == w
        assert int(wrong_digit.group(3)) == period_digit + 1

    assert seen_improper, f"no improper draw seen in {ROLLS} rolls"

"""`frac_imp_2`'s `puts_the_quotient_in_the_numerator` Trap must be reachable (#361).

The Trap it replaces, `swaps_the_remainder_and_the_denominator`, was built from the
denominator, the remainder and the whole part in the wrong argument positions, and
the shared formatting helper folded the result into a number no route through the
Problem produced. The new Trap is the mistake of dividing correctly and then writing
the quotient and the remainder in the wrong places.

A generator draws its numbers at random, so no single call proves the guarantee —
the same sweep shape as `test_trap_slugs.py`. Running the generator many times does.
"""

from backend.core.utils import format_answers
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500


def _draws() -> list[dict]:
    """Every Problem `frac_imp_2` emits across ROLLS rolls, rejections dropped."""
    generator = FUNCTION_REGISTRY["frac_imp_2"]
    rolls = (generator() for _ in range(ROLLS))
    return [problem for problem in rolls if problem is not None]


def test_trap_swaps_the_quotient_and_the_remainder():
    """The Trap's option is the mixed number formed from the Problem's own quotient
    and remainder, written the wrong way round, and it is never the correct answer.
    """
    problems = _draws()
    assert problems, f"frac_imp_2 emitted no Problem in {ROLLS} rolls"

    swapped_seen = 0
    for problem in problems:
        w, n, d = (
            problem["parameters"]["w"],
            problem["parameters"]["n"],
            problem["parameters"]["d"],
        )
        correct = problem["correct"]
        expected_trap, _ = format_answers(w, d, n)

        if w == n:
            # Dividing correctly and swapping the two results lands on the
            # correct answer itself — the slot must go empty, not collide.
            assert expected_trap == correct
            assert "puts_the_quotient_in_the_numerator" not in problem[
                "options_map"
            ].values()
            continue

        assert expected_trap != correct, (
            f"frac_imp_2 offered the correct answer {correct!r} as "
            "puts_the_quotient_in_the_numerator"
        )

        label = problem["options_map"].get(expected_trap)
        if label == "gives_only_the_whole_part":
            # w divides evenly into d, so the swapped mixed number reduces to a
            # bare whole number that happens to also be w — ADR-0008's earlier-
            # declared Trap keeps the slot, and this draw's slot goes to a Filler.
            continue

        swapped_seen += 1
        assert label == "puts_the_quotient_in_the_numerator", (
            f"frac_imp_2 did not offer {expected_trap!r} as "
            f"puts_the_quotient_in_the_numerator for {w} and {n}/{d}"
        )

    assert swapped_seen, f"frac_imp_2 drew no w != n Problem in {ROLLS} rolls"


def test_a_problem_whose_whole_part_equals_its_remainder_is_still_served():
    """Skipping the colliding Trap must not discard the draw and re-roll it (#361)."""
    equal_draws = [
        problem
        for problem in _draws()
        if problem["parameters"]["w"] == problem["parameters"]["n"]
    ]
    assert equal_draws, f"frac_imp_2 drew no w == n Problem in {ROLLS} rolls"

    for problem in equal_draws:
        assert len(problem["options"]) == len(set(problem["options"])) == 4

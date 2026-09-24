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

TRAP_SLUG = "puts_the_quotient_in_the_numerator"


def _draws() -> list[dict]:
    """Every Problem `frac_imp_2` emits across ROLLS rolls, rejections dropped."""
    generator = FUNCTION_REGISTRY["frac_imp_2"]
    rolls = (generator() for _ in range(ROLLS))
    return [problem for problem in rolls if problem is not None]


def test_frac_imp_2_trap_puts_the_quotient_in_the_numerator():
    """The Trap is the draw's own quotient and remainder, written the wrong way round."""
    problems = _draws()
    assert problems, f"frac_imp_2 emitted no Problem in {ROLLS} rolls"

    offered = 0
    for problem in problems:
        parameters = problem["parameters"]
        w, n, d = parameters["w"], parameters["n"], parameters["d"]
        if w == n:
            continue  # The swap lands on the correct answer — its own test below.

        expected_trap, _ = format_answers(w, d, n)
        assert expected_trap != problem["correct"], (
            f"frac_imp_2 offered the correct answer {problem['correct']!r} as "
            f"{TRAP_SLUG}"
        )

        label = problem["options_map"].get(expected_trap)
        if label == "gives_only_the_whole_part":
            # d divides w, so the swapped mixed number reduces to the bare whole
            # number w — ADR-0008's earlier-declared Trap keeps the slot, and
            # this draw's slot goes to a Filler.
            continue

        offered += 1
        assert label == TRAP_SLUG, (
            f"frac_imp_2 did not offer {expected_trap!r} as {TRAP_SLUG} "
            f"for {w} and {n}/{d}"
        )

    assert offered, f"frac_imp_2 drew no w != n Problem in {ROLLS} rolls"


def test_frac_imp_2_w_equals_n_collision_falls_back_to_filler():
    """At w == n the swap is the correct answer, so the Trap loses its slot (#361).

    Losing the slot must leave the draw served with four distinct options, not
    discard it and re-roll.
    """
    equal_draws = [
        problem
        for problem in _draws()
        if problem["parameters"]["w"] == problem["parameters"]["n"]
    ]
    assert equal_draws, f"frac_imp_2 drew no w == n Problem in {ROLLS} rolls"

    for problem in equal_draws:
        parameters = problem["parameters"]
        w, n, d = parameters["w"], parameters["n"], parameters["d"]
        expected_trap, _ = format_answers(w, d, n)

        assert expected_trap == problem["correct"]
        assert TRAP_SLUG not in problem["options_map"].values()
        assert len(problem["options"]) == len(set(problem["options"])) == 4

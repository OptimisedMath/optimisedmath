"""No decimal-addition option may carry more decimal places than its operands.

`dec_add_1` used to build its operands as `whole + d/10` in binary float and pass
the sum straight to `fmt_dec`, so a Student was sometimes shown a 17-digit binary-
float artefact (e.g. `2,5999999999999996`) as one of the four options — and it was
the correct one. The fix computes in exact `Decimal` arithmetic; this test asserts
the Student-visible guarantee rather than the arithmetic used to reach it.

A generator picks its template with `random.choice`, so no single call proves the
guarantee — the same sweep shape as `test_problem_parameters.py` and
`test_trap_slugs.py`. Running each generator many times does.

Scoped to `dec_add_1` only: its sibling generators in the same Topic (`dec_add_2`,
`dec_add_3`) already build correct/Trap/Filler values through `round()`, which
never exhibited this artefact (audited separately), and `dec_add_2`'s
`applies_the_multiplication_point_rule` Trap *deliberately* emits an answer with a
different, larger number of decimal places — the guarantee below does not hold
for it.
"""

import re

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500

_NUMBER_RE = re.compile(r"\d+,\d+|\d+")


def _decimal_places(token: str) -> int:
    return len(token.split(",")[1]) if "," in token else 0


def _operand_places(q_str: str) -> int:
    """Max decimal places among the numbers embedded in the rendered question."""
    return max(_decimal_places(token) for token in _NUMBER_RE.findall(q_str))


def test_dec_add_1_emits_no_option_with_more_decimal_places_than_the_operands():
    name = "dec_add_1"
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue

        operand_places = _operand_places(problem["question"])

        for option in problem["options"]:
            assert _decimal_places(option) <= operand_places, (
                f"{name} emitted option {option!r} with more decimal places than "
                f"its operands (max {operand_places}) in {problem['question']!r}"
            )

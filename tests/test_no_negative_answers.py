"""No Level may set a negative number as the answer a Student is asked to reach.

Negative numbers are outside what klasy 4-8 practise in these Chapters, but two
`Kolejność wykonywania działań` Boss templates could roll one anyway: `dec_order_6`
drew `a · (b + c)² − d` with an `a` so small that 131 of its 135 operand
combinations came out negative, and `dec_order_5`'s `(a + b)² − c` went negative on
half its draws (#242). Their Ułamki Zwykłe counterparts already discarded such a
roll, so the defect was one generator disagreeing with its sibling.

Traps are deliberately exempt — a Student who multiplies before squaring may well
land on a negative number, and hiding that would remove the Trap.
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 400


@pytest.mark.parametrize("name", sorted(FUNCTION_REGISTRY))
def test_generator_never_emits_a_negative_correct_answer(name):
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        correct = problem["correct"]
        assert not correct.lstrip().startswith("-"), (
            f"{name} emitted a negative answer {correct!r} for "
            f"{problem['question']!r}"
        )

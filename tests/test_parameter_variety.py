# Every generator must actually randomise the numbers it declares as `parameters`.
#
# `test_trap_slugs.py` proves each declared Trap is reachable and
# `test_problem_parameters.py` proves every Problem carries `parameters` — neither
# notices a generator that emits the *same* numbers every roll. `frac_div_frac_2`
# and `frac_mult_2` both seeded their rejection-sampling loop with a pair that
# already satisfied the loop condition, so the body never ran and a whole Level
# shipped one fixed numerator pair (#226).
#
# So: sweep every generator, and require each integer parameter to take more than
# one value across the rolls. A parameter that is fixed by the Level's *shape*
# rather than by a bug is listed in `STRUCTURALLY_CONSTANT` with the reason.
import collections

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 300

# (generator, parameter) pairs whose single value is the Level's design, not a
# frozen roll: dividing by / multiplying by a whole number pins that operand to
# `whole = 0, d = 1`, and each `frac_pow` Level teaches one fixed exponent.
STRUCTURALLY_CONSTANT = {
    "frac_div_num_3": {"whole2", "d2"},
    "frac_mult_3": {"whole1"},
    "frac_mult_num_3": {"whole2", "d2"},
    "frac_pow_1": {"p"},
    "frac_pow_2": {"p"},
}


@pytest.mark.parametrize("name", sorted(FUNCTION_REGISTRY))
def test_generator_varies_its_integer_parameters(name):
    generator = FUNCTION_REGISTRY[name]
    exempt = STRUCTURALLY_CONSTANT.get(name, set())

    seen = collections.defaultdict(set)
    emitted = 0
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        emitted += 1
        for key, value in problem["parameters"].items():
            if isinstance(value, int) and not isinstance(value, bool):
                seen[key].add(value)

    if not emitted:
        pytest.skip(f"{name} emitted no Problem in {ROLLS} rolls")

    frozen = sorted(
        key for key, values in seen.items() if len(values) == 1 and key not in exempt
    )
    assert not frozen, (
        f"{name} never varied {frozen} across {emitted} Problems "
        f"(values: { {k: sorted(seen[k]) for k in frozen} })"
    )

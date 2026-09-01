"""Every generator in the curriculum must supply non-empty `parameters`.

A generator picks its template with `random.choice`, so no single call proves every
branch supplies `parameters` — the same sweep shape as `test_trap_slugs.py`. Running
each generator many times does: over enough rolls every template fires, and every
emitted Problem must carry a non-empty `parameters` dict.

One sweep over the whole curriculum, not one per chapter — `build_problem_dict` makes
`parameters` a required argument, so this is the guarantee's only test.
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500


@pytest.mark.parametrize("name", sorted(FUNCTION_REGISTRY))
def test_generator_always_supplies_non_empty_parameters(name):
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        assert problem.get(
            "parameters"
        ), f"{name} emitted a Problem with no `parameters`"

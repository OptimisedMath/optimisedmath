"""Every Ułamki zwykłe generator must supply `parameters` to `build_problem_dict`.

A generator picks its template with `random.choice`, so no single call proves every
branch supplies `parameters` — the same sweep shape as `test_trap_slugs.py`. Running
each generator many times does: over enough rolls every template fires, and every
emitted Problem must carry a non-empty `parameters` dict.

Scoped to `backend/chapters/ulamki_zwykle/` — the other chapter migrates on its own
ticket and is untouched here.
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500

CHAPTER_MODULE_PREFIX = "backend.chapters.ulamki_zwykle"

CHAPTER_GENERATOR_NAMES = sorted(
    name
    for name, func in FUNCTION_REGISTRY.items()
    if func.__module__.startswith(CHAPTER_MODULE_PREFIX)
)


def test_chapter_has_generators_to_sweep():
    assert CHAPTER_GENERATOR_NAMES


@pytest.mark.parametrize("name", CHAPTER_GENERATOR_NAMES)
def test_generator_always_supplies_parameters(name):
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        assert problem.get(
            "parameters"
        ), f"{name} emitted a Problem with no `parameters`"

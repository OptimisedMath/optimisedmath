"""Every generator in ulamki_dziesietne must supply `parameters` to build_problem_dict.

A generator picks its template at random, so no static read can prove the guarantee —
the same sweep pattern as `tests/test_trap_slugs.py` runs each generator many times
and asserts every emitted Problem carries a non-empty `parameters`. Scoped to this
chapter only; the other chapter (`ulamki_zwykle`) migrates in its own ticket.
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

CHAPTER_MODULE_PREFIX = "backend.chapters.ulamki_dziesietne"

# High enough that the rarest branch fires with overwhelming probability.
ROLLS = 500

CHAPTER_GENERATOR_NAMES = sorted(
    name
    for name, func in FUNCTION_REGISTRY.items()
    if func.__module__.startswith(CHAPTER_MODULE_PREFIX)
)


def test_chapter_has_generators_to_sweep():
    """Guards against the filter silently matching nothing."""
    assert CHAPTER_GENERATOR_NAMES


@pytest.mark.parametrize("name", CHAPTER_GENERATOR_NAMES)
def test_generator_supplies_non_empty_parameters(name):
    generator = FUNCTION_REGISTRY[name]
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        assert problem.get(
            "parameters"
        ), f"{name} emitted a Problem without non-empty parameters"

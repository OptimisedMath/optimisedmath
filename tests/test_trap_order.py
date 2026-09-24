"""No Problem lists a slip before a Trap whose Level entry references a Misconception.

ADR-0008 owns the rule and why: a template's Traps are ordered believed rules first,
then slips, because when only three of them fit a Problem's slots the Misconception
Traps are the ones worth the slot.

`build_problem_dict` fills those slots in declaration order, so `options_map`'s
insertion order *is* the order a Problem offers — this sweep reads it there rather
than re-deriving it from a generator's source. Whether a slug carries a Misconception
comes from the Level's curriculum entry (`LevelConfig.trap_misconceptions`), not a
hand-kept list, so a Level that gains or loses one stays honest automatically.

Same sweep shape as `test_trap_slugs.py`: a generator picks its template and its
numbers at random, so no single call proves the guarantee. Running each generator
many times does.
"""

import pytest

from backend.core.utils import FILLER_SLUG
from backend.curriculum_loader import load_curriculum_store
from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 500


def _misconception_slugs(name: str) -> set[str]:
    """Every Trap slug the generator's Level(s) mark with a Misconception."""
    store = load_curriculum_store()
    slugs: set[str] = set()
    for bundle in store.bundles:
        for level_config in bundle.level_configs.values():
            if level_config.function == name:
                slugs |= set(level_config.trap_misconceptions)
    return slugs


@pytest.mark.parametrize("name", sorted(FUNCTION_REGISTRY))
def test_generator_never_serves_a_slip_before_a_misconception_trap(name):
    generator = FUNCTION_REGISTRY[name]
    misconception_slugs = _misconception_slugs(name)
    if not misconception_slugs:
        pytest.skip(f"{name}'s Level declares no Trap with a Misconception")

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue

        served = [
            slug
            for slug in problem["options_map"].values()
            if slug not in ("correct", FILLER_SLUG)
        ]

        slip_already_served = None
        for slug in served:
            if slug not in misconception_slugs:
                slip_already_served = slug
                continue
            assert slip_already_served is None, (
                f"{name} served slip {slip_already_served!r} before Misconception "
                f"Trap {slug!r} in {problem['question']!r}"
            )

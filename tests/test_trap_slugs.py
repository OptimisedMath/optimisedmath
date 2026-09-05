"""Every generator's @declares_traps declaration must match what its body emits.

A generator picks its template with `random.choice`, so no single call reveals the
whole vocabulary and no static read of the source can prove the declaration honest.
Running each generator many times does: over enough rolls every template fires, and
the union of the slugs actually emitted must equal the declared set exactly.

Both directions are failures worth catching. A declared slug no template emits is a
Level carrying prose no Student can ever reach — the loader forces an entry for it,
so it is authored effort spent on a dead option. An emitted slug that was never
declared slips past the loader's validation entirely and falls back to the generic
wrong-answer message, silently losing the targeted feedback the Trap exists for.
"""

import pytest

from backend.core.utils import FILLER_SLUG, declared_trap_slugs
from backend.problem_generation import FUNCTION_REGISTRY

# High enough that the rarest branch (1 template in 4, further gated by a retry loop
# that rerolls on option collisions) fires with overwhelming probability.
ROLLS = 500


def _emitted_slugs(generator) -> set[str]:
    """The union of Trap slugs seen across many calls, Fillers and `correct` excluded."""
    seen: set[str] = set()
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        for label in problem["options_map"].values():
            if label not in ("correct", FILLER_SLUG):
                seen.add(label)
    return seen


@pytest.mark.parametrize("name", sorted(FUNCTION_REGISTRY))
def test_generator_emits_exactly_the_trap_slugs_it_declares(name):
    generator = FUNCTION_REGISTRY[name]
    declared = declared_trap_slugs(generator)
    emitted = _emitted_slugs(generator)

    assert declared, f"{name} declares no Trap slugs — add @declares_traps"

    undeclared = sorted(emitted - declared)
    assert (
        not undeclared
    ), f"{name} emits Trap slugs it does not declare: {', '.join(undeclared)}"

    unreachable = sorted(declared - emitted)
    assert not unreachable, (
        f"{name} declares Trap slugs no template emitted in {ROLLS} rolls: "
        f"{', '.join(unreachable)}"
    )


@pytest.mark.parametrize("name", sorted(FUNCTION_REGISTRY))
def test_filler_is_never_declared_as_a_trap_slug(name):
    """A Filler is radio-button padding, not an anticipated wrong rule."""
    assert FILLER_SLUG not in declared_trap_slugs(FUNCTION_REGISTRY[name])

"""No option Ułamki Zwykłe or Ułamki Dziesiętne serve is ever negative.

ADR-0007 owns the rule and why it reversed the Trap exemption this sweep used to
grant: a Student working these Chapters has not met negative numbers, so no option
— correct answer, Trap or Filler — may be one, and `build_problem_dict` skips any
that would be unless a call passes `allow_negative_options` (#266). No call in
these two Chapters does, and this sweep is what catches one opting in by mistake,
so it checks every option a generator here can emit, not only the correct answer.

Chapter membership comes from the generator's own module, not a hand-kept list, so
a new generator dropped into either Chapter is covered automatically.
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 400

_NEGATIVE_FREE_MODULE_PREFIXES = (
    "backend.chapters.ulamki_zwykle.",
    "backend.chapters.ulamki_dziesietne.",
)

_NEGATIVE_FREE_GENERATORS = sorted(
    name
    for name, generator in FUNCTION_REGISTRY.items()
    if generator.__module__.startswith(_NEGATIVE_FREE_MODULE_PREFIXES)
)


@pytest.mark.parametrize("name", _NEGATIVE_FREE_GENERATORS)
def test_generator_never_offers_a_negative_option(name):
    generator = FUNCTION_REGISTRY[name]

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        for option in problem["options_map"]:
            assert not option.lstrip().startswith("-"), (
                f"{name} offered the negative option {option!r} for "
                f"{problem['question']!r}"
            )

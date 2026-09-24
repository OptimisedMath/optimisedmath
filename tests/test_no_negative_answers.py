"""No option Ułamki Zwykłe or Ułamki Dziesiętne serve is ever negative.

Negative numbers come after fractions and decimals in the curriculum, so a Student
working these two Chapters has no rule that produces one — not for the correct
answer, a Trap, or a Filler (ADR-0007).

This sweep used to check the correct answer only and exempt Traps outright —
"a Student who multiplies before squaring may well land on a negative number, and
hiding that would remove the Trap." That reasoning assumed the Student could reach
a negative number by a rule they actually apply. They cannot: on the `Kolejność
działań` Boss Level both wrong-order Traps were negative on every draw, so a
Student in Radio mode could discard two of four options without doing any
arithmetic (#266). `build_problem_dict` now skips a Trap or Filler that would be
negative unless a call opts in with `allow_negative_options` — no call in these
two Chapters does — so this sweep checks every option a generator here can emit,
not only the correct answer. Chapter membership comes from the generator's own
module, not a hand-kept list, so a new generator dropped into either Chapter is
covered automatically.
"""

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

ROLLS = 400

_NEGATIVE_FREE_CHAPTER_MODULES = ("ulamki_zwykle", "ulamki_dziesietne")


def _chapter_module(generator) -> str:
    """The Chapter directory a generator is defined in, e.g. `ulamki_zwykle`."""
    return generator.__module__.split(".")[2]


_NAMES = sorted(
    name
    for name, generator in FUNCTION_REGISTRY.items()
    if _chapter_module(generator) in _NEGATIVE_FREE_CHAPTER_MODULES
)


@pytest.mark.parametrize("name", _NAMES)
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

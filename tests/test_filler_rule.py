"""ADR-0009: build_problem_dict invents every Filler itself; a generator's own
`fillers=` survives only where the shared rule cannot work.

Two properties this frees up, that no per-generator test can check on its own:
a static one (no new hand-written `fillers=` slips in unnoticed) and a dynamic
one (every generator that is padded at all actually reaches four distinct
options now that a collision or a skipped Trap no longer discards the Problem).
"""

import ast
from pathlib import Path

import pytest

from backend.problem_generation import FUNCTION_REGISTRY

CHAPTERS_DIR = Path(__file__).resolve().parent.parent / "backend" / "chapters"

# Comparison Levels draw their options from {<, >, =}: two or three symbols are
# the whole Problem, so `build_problem_dict` never pads one to four.
COMPARISON_GENERATORS = frozenset(
    {
        "frac_comp_1",
        "frac_comp_2",
        "frac_comp_3",
        "dec_compare_1",
        "dec_compare_2",
        "dec_compare_3",
        "dec_compare_4",
    }
)

# ADR-0009's declared exemptions: the generators whose own `fillers=` the shared
# rule cannot replace — the comparison symbols have no number to move, and
# `dec_to_frac_4` writes repeating decimals like `0,(3)`, a form the rule cannot
# parse. None of them needs the hatch today; grow this set only by editing it here.
FILLERS_EXEMPT_GENERATORS = COMPARISON_GENERATORS | {"dec_to_frac_4"}


def _functions_passing_fillers(source: str, path: Path) -> set[str]:
    """Every function name whose body passes a `fillers=` keyword argument."""
    tree = ast.parse(source, filename=str(path))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(call, ast.Call)
            and any(kw.arg == "fillers" for kw in call.keywords)
            for call in ast.walk(node)
        )
    }


_CHAPTER_FILES = sorted(CHAPTERS_DIR.rglob("topic_*.py"))


@pytest.mark.parametrize(
    "path",
    _CHAPTER_FILES,
    ids=[str(p.relative_to(CHAPTERS_DIR)) for p in _CHAPTER_FILES],
)
def test_only_the_pinned_exemptions_pass_fillers(path):
    """No chapter file hand-writes `fillers=` outside ADR-0009's exemptions."""
    offenders = (
        _functions_passing_fillers(path.read_text(encoding="utf-8"), path)
        - FILLERS_EXEMPT_GENERATORS
    )
    assert not offenders, (
        f"{path.relative_to(CHAPTERS_DIR)} passes fillers= from "
        f"{sorted(offenders)}, outside the pinned exemption set"
    )


ROLLS = 300


@pytest.mark.parametrize("name", sorted(set(FUNCTION_REGISTRY) - COMPARISON_GENERATORS))
def test_padded_generator_serves_four_distinct_options(name):
    """Every generator outside the comparison Levels fills all four slots, on every roll."""
    generator = FUNCTION_REGISTRY[name]
    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue
        options = problem["options"]
        assert len(options) == 4, f"{name} served {len(options)} options: {options}"
        assert len(set(options)) == 4, f"{name} served a repeated option: {options}"

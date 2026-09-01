"""Every walkthrough a Trap can reach must build from what its generator emits.

The only place that can see all three factors at once: a Level's generator, the Traps
it emits, and the walkthrough contract of the Misconception those Traps reference. A
generator's `parameters` only exist after a call and a generator picks its template
with `random.choice`, so no load-time check and no single roll can prove the contract
holds — the same sweep shape as `test_trap_slugs.py` and `test_problem_parameters.py`,
with the walkthrough registry as a third factor.

Two failures are caught. A missing required key means a Student who hits that
Misconception twice gets no Deconstruction where the curriculum promised one
(`submission.py` now skips rather than raises, so the loss is silent — this is where it
becomes loud). A final Step whose answer is not the Problem's own means a walkthrough
that runs, reads plausibly, and lands the Student on the wrong number; that assertion
runs only where the walkthrough declares `answers_the_problem`, since the expansion
walkthrough deliberately ends on a numerator rather than a whole fraction.
"""

import pytest

from backend import deconstruction
from backend.curriculum_loader import load_curriculum_store
from backend.problem_generation import FUNCTION_REGISTRY

# Matched to the existing sweeps rather than trimmed: two of the fraction generators
# return None on most rolls because of a coprimality guard, so a smaller count would
# give exactly the Levels this sweep exists for the thinnest cover.
ROLLS = 500


def _combinations() -> list[tuple[str, int, int, str, str, str]]:
    """Every (chapter, topic, level, generator, trap, misconception) with a walkthrough."""
    combinations = []
    for bundle in load_curriculum_store().bundles:
        for (topic_id, level), level_config in bundle.level_configs.items():
            for trap_slug, slug in level_config.trap_misconceptions.items():
                if deconstruction.has_walkthrough(slug):
                    combinations.append(
                        (
                            bundle.chapter_name,
                            topic_id,
                            level,
                            level_config.function,
                            trap_slug,
                            slug,
                        )
                    )
    return combinations


COMBINATIONS = _combinations()


def test_the_sweep_covers_something():
    """A store that silently loaded nothing would make every case below vacuous."""
    assert COMBINATIONS


@pytest.mark.parametrize(
    ("chapter_name", "topic_id", "level", "function", "trap_slug", "misconception"),
    COMBINATIONS,
    ids=[
        f"{function}-{trap_slug}-{misconception}"
        for _, _, _, function, trap_slug, misconception in COMBINATIONS
    ],
)
def test_walkthrough_builds_from_what_the_generator_emits(
    chapter_name, topic_id, level, function, trap_slug, misconception
):
    generator = FUNCTION_REGISTRY[function]
    declaration = deconstruction.declaration(misconception)
    where = (
        f"{chapter_name} / topic {topic_id} level {level} ({function}), "
        f"Trap '{trap_slug}' -> '{misconception}'"
    )

    for _ in range(ROLLS):
        problem = generator()
        if problem is None:
            continue

        try:
            steps = deconstruction.build_steps(misconception, problem["parameters"])
        except deconstruction.DeconstructionContractError as error:
            pytest.fail(f"{where}: {error} (parameters: {problem['parameters']})")

        assert steps, f"{where}: walkthrough built no Steps"

        if declaration.answers_the_problem:
            assert steps[-1].answer == problem["correct"], (
                f"{where}: the final Step answers {steps[-1].answer!r} but the "
                f"Problem's answer is {problem['correct']!r} "
                f"(parameters: {problem['parameters']})"
            )

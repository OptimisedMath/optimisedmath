"""Registry-wide figure contracts every scene-drawn generator inherits (#356).

test-seams.md names P2 (a figure's labels cannot disagree with the Problem's
answer and Traps) and P3 (a figure is legible) as generator-seam and
renderer-seam properties respectively, each also carrying a registry-wide
floor — the same shape as `test_trap_slugs.py`, `test_no_negative_answers.py`,
`test_parameter_variety.py` and `test_problem_variety.py`.

A scene-drawn Problem is identified by the artefact its renderer produced, not
by its name or Chapter: `Scene.to_svg()` marks its root `<svg>` with
`role="img"`; `generate_universal_number_line`, which builds its SVG by hand,
never does. Sweeping on that marker means a future Geometria generator
inherits both contracts without a new test being written for it.
"""

import random
import re

import pytest

from backend.core.scene import Scene
from backend.problem_generation import FUNCTION_REGISTRY
from tests.support.svg_labels import figure_labels

ROLLS = 300

#: A printed label's leading number, in Polish comma notation — `12`, `12,5`.
#: A label that withholds its value (`x`, `h`, a vertex letter, a Greek
#: letter) has no leading digit and does not match; P1 owns those (#356).
_NUMERIC_LABEL = re.compile(r"^-?\d+(?:,\d+)?")


def _is_scene_drawn(generator) -> bool:
    """Whether `generator`'s figure carries the scene renderer's `role="img"`
    marker. Retried a few times because a generator can return `None` on a
    draw its own constraints reject; every Problem a scene-drawn generator
    does emit carries the same marker, so one success settles it."""
    for _ in range(10):
        problem = generator()
        if problem is not None:
            return 'role="img"' in (problem["image_html"] or "")
    return False


SCENE_GENERATORS = sorted(
    name for name, fn in FUNCTION_REGISTRY.items() if _is_scene_drawn(fn)
)

NUMBER_LINE_GENERATORS = {name for name in FUNCTION_REGISTRY if "number_line" in name}

# #350 (Topic 130 labels cross the figure's lines) already measured this: the
# placement pass's early exit stops searching once a label clears every other
# label, even when a figure stroke still runs through its box (#356's own
# sweep below reproduces the same shape — Level 2 clean, the other three
# Levels not). Fixing placement is #350's job, not this ticket's — a change
# there touches every figure the app can draw — so these three are named
# here rather than silently skipped, each carrying the issue that owns them.
# `strict=True` so the marker cannot quietly outlive the fix: once #350 lands,
# whichever of these turns clean starts failing this suite until its entry is
# removed.
_KNOWN_LABEL_STROKE_COLLISIONS = {
    "geo_triangle_area_1": "#350: the height's label crosses a slant side",
    "geo_triangle_area_3": "#350: a side's label crosses the dashed height",
    "geo_triangle_area_4": "#350: the known dimension's label crosses a slant side",
}


def _label_value(label: str) -> float | None:
    """The leading number a printed label carries, or None for a symbol that
    withholds a value rather than printing one."""
    match = _NUMERIC_LABEL.match(label)
    if match is None:
        return None
    return float(match.group().replace(",", "."))


def _parameter_values(parameters: dict) -> set[float]:
    """Every numeric value a Problem's `parameters` carries.

    Excludes `bool` — an `int` subclass in Python — so a parameter such as the
    reverse rung's `height_unknown: True` can never stand in for a printed `1`
    that has nothing to do with it (#356).
    """
    return {
        float(value)
        for value in parameters.values()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def test_number_line_generators_are_not_scene_drawn():
    """Sanity check for the artefact-based split: the number-line renderer
    writes its SVG by hand and never emits `role="img"` (#356)."""
    assert NUMBER_LINE_GENERATORS, "expected at least one number-line generator"
    assert not NUMBER_LINE_GENERATORS & set(SCENE_GENERATORS)


class TestP2Floor:
    """P2's floor (test-seams.md, #356): every numeric label a scene-drawn
    figure prints is a value the Problem's own `parameters` carries. Not the
    P2 test itself — `TestForwardRungPoolPinning` in test_geometria_topic.py
    carries that, exhaustively, per Level — this is the registry-wide floor
    every present and future scene-drawn generator inherits without a new
    test being written for it."""

    @pytest.mark.parametrize("name", SCENE_GENERATORS)
    def test_every_numeric_label_is_a_problem_parameter(self, name):
        """Every number a figure prints traces back to `parameters`, or it's a
        withheld-value symbol P1 owns."""
        generator = FUNCTION_REGISTRY[name]
        random.seed(0)
        rolled = 0
        for _ in range(ROLLS):
            problem = generator()
            if problem is None:
                continue
            rolled += 1
            allowed = _parameter_values(problem["parameters"])
            for label in figure_labels(problem["image_html"]):
                value = _label_value(label)
                if value is None:
                    continue
                assert value in allowed, (
                    f"{name} printed {label!r}, not a value in "
                    f"{problem['parameters']!r}"
                )
        assert rolled, f"{name} never returned a Problem in {ROLLS} rolls"


def _render_contexts(generator, monkeypatch, rolls):
    """The `Ctx` each of `rolls` draws of `generator` rendered against.

    Reads what `Scene.to_svg()` already recorded rather than recomputing the
    placement pass — the tautology class #349 rules out.
    """
    captured = []
    original_to_svg = Scene.to_svg

    def recording_to_svg(self, *args, **kwargs):
        svg = original_to_svg(self, *args, **kwargs)
        captured.append(self.render_context())
        return svg

    monkeypatch.setattr(Scene, "to_svg", recording_to_svg)
    random.seed(0)
    for _ in range(rolls):
        generator()
    return captured


def _p3_params():
    """`SCENE_GENERATORS`, each wrapped in an xfail marker where #350 already
    found the defect this sweep looks for."""
    for name in SCENE_GENERATORS:
        reason = _KNOWN_LABEL_STROKE_COLLISIONS.get(name)
        marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
        yield pytest.param(name, marks=marks, id=name)


class TestP3Legibility:
    """P3 (test-seams.md, #356): no label is drawn with a residual stroke
    collision — read off `Ctx.placed`, the render context's own record of
    what `place_labels` settled on, never recomputed here.

    Deliberately red on arrival for the Levels #350 already found: this sweep
    is the registry-wide floor every scene-drawn generator inherits, #350 is
    where the placement fix for these specific figures belongs.
    """

    @pytest.mark.parametrize("name", list(_p3_params()))
    def test_no_label_is_drawn_with_a_residual_collision(self, name, monkeypatch):
        """No placed label crosses a figure stroke, per the render context's
        own record — three Levels xfail against #350's known defect."""
        generator = FUNCTION_REGISTRY[name]
        contexts = _render_contexts(generator, monkeypatch, ROLLS)
        assert contexts, f"{name} never rendered a Scene in {ROLLS} rolls"
        for ctx in contexts:
            for placement in ctx.placed:
                assert placement.collisions == 0, (
                    f"{name} drew a label at {placement.box} crossing "
                    f"{placement.collisions} figure stroke(s)"
                )

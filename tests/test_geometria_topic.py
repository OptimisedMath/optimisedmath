"""Tests for the Geometria vertical slice — Topic 130, Pole trójkąta (#214)."""

import math
import re

import pytest

import backend.chapters.geometria.topic_130_pole_trojkata as topic
from backend.core.scene import EdgeLabel, Outline, Scene, Triangle
from backend.curriculum import curriculum_from_yaml
from backend.curriculum_loader import CurriculumLoadError, _validate_expected_units
from backend.problem_generation import generate_level_problem
from backend.session import _is_safe_svg_fragment

CHAPTER_ID = 30
TOPIC_ID = 130
GENERATORS = [
    topic.geo_triangle_area_1,
    topic.geo_triangle_area_2,
    topic.geo_triangle_area_3,
    topic.geo_triangle_area_4,
]


@pytest.fixture(scope="module")
def curriculum():
    return curriculum_from_yaml()


class TestSceneInvariant:
    def test_a_label_reads_its_number_off_the_figure(self):
        """The to-scale invariant: the number that places the vertex and the number
        that prints are the same number, so they cannot disagree."""
        figure = Triangle.base_height(base=14, height=12, apex_frac=5 / 14)
        assert figure.edge_length("AB") == pytest.approx(14)

    def test_a_derived_side_prints_as_the_whole_number_it_is(self):
        """The pools exist to make this true — a printed `13,00` would be a tell."""
        figure = Triangle.base_height(base=14, height=12, apex_frac=5 / 14)
        svg = Scene(figure, [Outline(), EdgeLabel("CA", "cm")]).to_svg()
        assert ">13 cm<" in svg

    def test_the_altitude_foot_falls_outside_on_the_obtuse_rung(self):
        """Level 3 exists for exactly this case, so the pool must actually produce it."""
        for base, height, offset, _, _ in topic.OBTUSE:
            assert offset > 0
            figure = Triangle.base_height(base, height, apex_frac=-offset / base)
            assert figure.p("C")[0] < 0


class TestGenerators:
    @pytest.mark.parametrize("generator", GENERATORS, ids=lambda g: g.__name__)
    def test_every_svg_survives_the_session_gate(self, generator):
        """`_is_safe_svg_fragment` is a denylist, so new primitives must pass it."""
        for _ in range(20):
            problem = generator()
            if problem is None:
                continue
            assert _is_safe_svg_fragment(problem["image_html"])

    @pytest.mark.parametrize("generator", GENERATORS, ids=lambda g: g.__name__)
    def test_every_option_is_a_bare_number(self, generator):
        """#213: the Unit is appended by the client, so it can never discriminate."""
        for _ in range(20):
            problem = generator()
            if problem is None:
                continue
            for option in problem["options"]:
                assert re.fullmatch(r"\d+", option), option

    @pytest.mark.parametrize("generator", GENERATORS[:3], ids=lambda g: g.__name__)
    def test_a_forward_rung_labels_a_length_that_is_neither_base_nor_height(
        self, generator
    ):
        """Without a distractor length, two of the three Traps cannot fire (#237)."""
        problem = generator()
        assert problem is not None
        parameters = problem["parameters"]
        extra = set(parameters) - {"base", "height", "unit"}
        assert extra

    def test_the_reverse_rung_withholds_one_dimension_and_varies_which(self):
        """Fixing which dimension is unknown makes the rung solvable without the figure."""
        withheld = set()
        for _ in range(40):
            problem = topic.geo_triangle_area_4()
            if problem is None:
                continue
            assert ">x<" in problem["image_html"]
            withheld.add(problem["parameters"]["height_unknown"])
        assert withheld == {True, False}

    def test_the_reverse_rung_answers_in_a_length(self):
        """That is what puts both dimensions in the Topic without an `m²` rung."""
        problem = topic.geo_triangle_area_4()
        assert problem["expected_unit"] in topic.LENGTH_UNITS


class TestLevels:
    @pytest.mark.parametrize("level", [1, 2, 3, 4])
    def test_every_level_serves_a_problem_with_a_declared_unit(self, curriculum, level):
        declared = curriculum.level_config(CHAPTER_ID, TOPIC_ID, level).expected_units
        for _ in range(10):
            problem = generate_level_problem(curriculum, CHAPTER_ID, TOPIC_ID, level)
            assert problem["expected_unit"] in declared

    @pytest.mark.parametrize("level", [1, 2, 3, 4])
    def test_the_unit_varies_within_a_level(self, curriculum, level):
        """A fixed Unit trains `cm²` as the shape of an area answer rather than as a
        reading of the figure — the reflex `confuses_length_and_area_units` detects."""
        seen = {
            generate_level_problem(curriculum, CHAPTER_ID, TOPIC_ID, level)[
                "expected_unit"
            ]
            for _ in range(40)
        }
        assert len(seen) > 1

    def test_the_chapter_asks_for_a_text_keyboard(self, curriculum):
        """`default` sets inputMode=numeric, which puts `c` and `m` out of reach."""
        assert curriculum.keyboard_type(CHAPTER_ID) == "text"


class TestExpectedUnitsValidation:
    def _level(self, **overrides):
        entry = {"level": 1, "name": "L", "function": "nonexistent_generator"}
        entry.update(overrides)
        return entry

    def test_a_unit_outside_the_table_fails_at_load_time(self):
        """The whole reason the declaration is in YAML: a typo is caught on boot."""
        with pytest.raises(CurriculumLoadError, match="not in the Units table"):
            _validate_expected_units(
                "F.yaml", "C", "T", self._level(expected_units=["cm3"])
            )

    def test_an_empty_declaration_fails(self):
        with pytest.raises(CurriculumLoadError, match="non-empty list"):
            _validate_expected_units("F.yaml", "C", "T", self._level(expected_units=[]))

    def test_a_level_and_its_generator_must_declare_the_same_units(self):
        """Two lists that could drift, checked against each other exactly as
        `declares_traps` is."""
        entry = self._level(
            function="geo_triangle_area_1", expected_units=["cm²", "m²"]
        )
        with pytest.raises(CurriculumLoadError, match="does not match"):
            _validate_expected_units("Geometria.yaml", "Geometria", "Pole", entry)


class TestNewChapterOnAnExistingProfile:
    def test_a_profile_saved_before_a_chapter_existed_gains_its_frontier(self):
        """#214: `load_profile` replaces the Frontier map with what the DB stored, so
        a Chapter added afterwards had no record and the first Submission in it
        raised `KeyError` on the Chapter id."""
        from backend.core import db
        from backend.models import ChapterFrontier, SessionState
        from backend.session_state import load_profile

        stale = SessionState(
            username="wraca",
            selected_chapter_id=10,
            selected_topic_id=10,
            selected_level=1,
            chapter_frontiers={
                10: ChapterFrontier(frontier_topic_id=10, frontier_level=1)
            },
        )
        db.save_user("wraca", stale)

        state = SessionState()
        load_profile(state, "wraca", curriculum_from_yaml())

        assert CHAPTER_ID in state.chapter_frontiers

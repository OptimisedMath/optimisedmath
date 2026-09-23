"""Tests for the Geometria vertical slice — Topic 130, Pole trójkąta (#214)."""

import itertools
import random
import re

import pytest

import backend.chapters.geometria.topic_130_pole_trojkata as topic
from backend.core.scene import Altitude, Centre, EdgeLabel, Outline, Radius, Scene, Triangle
from backend.core.scene.geometry import circle
from backend.core.scene.render import Box, _overlap
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

    def test_an_unknown_height_is_named_h(self):
        """#293: the height is always `h`, never one of the edge letters."""
        figure = Triangle.base_height(base=14, height=12, apex_frac=5 / 14)
        altitude = Altitude(apex="C", base="AB", unknown=True)
        svg = Scene(figure, [Outline(), altitude]).to_svg()
        assert ">h<" in svg

    def test_a_known_height_prints_only_its_number(self):
        """A known height stays exactly as it was before #293 — no symbol clutter."""
        figure = Triangle.base_height(base=14, height=12, apex_frac=5 / 14)
        svg = Scene(
            figure, [Outline(), Altitude(apex="C", base="AB", unit_label="cm")]
        ).to_svg()
        assert ">12 cm<" in svg
        assert ">h<" not in svg

    def test_unknown_edges_are_named_a_b_c_in_figure_order(self):
        """#293: each unknown edge claims the next letter, in the order its
        EdgeLabel is drawn."""
        figure = Triangle.base_height(base=14, height=12, apex_frac=5 / 14)
        ab = EdgeLabel("AB", "cm", unknown=True)
        bc = EdgeLabel("BC", "cm", unknown=True)
        ca = EdgeLabel("CA", "cm", unknown=True)
        svg = Scene(figure, [Outline(), ab, bc, ca]).to_svg()
        assert (ab.unknown_text, bc.unknown_text, ca.unknown_text) == ("a", "b", "c")
        for letter in "abc":
            assert f">{letter}<" in svg

    def test_an_unknown_symbol_is_drawn_in_italic(self):
        """#293: the unknown opts out of the figure's upright sans stack."""
        figure = Triangle.base_height(base=14, height=12, apex_frac=5 / 14)
        svg = Scene(figure, [Outline(), EdgeLabel("AB", "cm", unknown=True)]).to_svg()
        assert 'font-style="italic"' in svg

    def test_a_known_label_stays_upright(self):
        """Numbers and Units never pick up the unknown's italic treatment."""
        figure = Triangle.base_height(base=14, height=12, apex_frac=5 / 14)
        svg = Scene(figure, [Outline(), EdgeLabel("AB", "cm")]).to_svg()
        assert 'font-style="italic"' not in svg

    def test_a_circles_centre_defaults_to_s(self):
        """#325: `S` is Polish material's centre letter — never `O`, which a Student
        has been taught means *obwód*."""
        svg = Scene(circle(radius=5), [Centre()]).to_svg()
        assert ">S<" in svg
        assert ">O<" not in svg

    def test_a_circles_centre_prints_an_override_label(self):
        """#325: the default stays overridable, for a future figure with two circles."""
        svg = Scene(circle(radius=5), [Centre(label="S1")]).to_svg()
        assert ">S1<" in svg
        assert ">S<" not in svg

    def test_an_unknown_radius_prints_r(self):
        """#325: an unknown radius is named `r`, the letter for promień — never `x`."""
        radius = Radius(unknown=True)
        svg = Scene(circle(radius=5), [radius]).to_svg()
        assert ">r<" in svg
        assert ">x<" not in svg
        assert radius.unknown_text == "r"

    def test_an_unknown_diameter_prints_d(self):
        """#325: an unknown diameter is named `d`, read off the annotation rather
        than retyped by the generator."""
        radius = Radius(diameter=True, unknown=True)
        svg = Scene(circle(radius=5), [radius]).to_svg()
        assert ">d<" in svg
        assert radius.unknown_text == "d"

    def test_an_unknown_radius_symbol_is_drawn_in_italic(self):
        """#325 follows #293's convention: the unknown opts out of the upright sans stack."""
        svg = Scene(circle(radius=5), [Radius(unknown=True)]).to_svg()
        assert 'font-style="italic"' in svg

    def test_a_known_radius_and_diameter_print_their_number_upright(self):
        """#325: a known value keeps printing its number and Unit, unchanged."""
        svg = Scene(
            circle(radius=5),
            [Radius(unit_label="cm"), Radius(diameter=True, at=100, unit_label="cm")],
        ).to_svg()
        assert ">5 cm<" in svg
        assert ">10 cm<" in svg
        assert 'font-style="italic"' not in svg

    def test_no_two_placed_labels_ever_overlap(self, monkeypatch):
        """#289: sweeps every figure every generator in this Topic can draw, across
        many seeds, and asserts pairwise disjointness of the placed label boxes —
        the fault that let `24 dm` print on top of `25 dm` must not come back."""
        captured: list[list[Box]] = []
        original_to_svg = Scene.to_svg

        def recording_to_svg(self, *args, **kwargs):
            svg = original_to_svg(self, *args, **kwargs)
            captured.append(self.label_boxes())
            return svg

        monkeypatch.setattr(Scene, "to_svg", recording_to_svg)

        random.seed(0)
        for generator in GENERATORS:
            for _ in range(80):
                generator()

        assert captured
        for boxes in captured:
            for a, b in itertools.combinations(boxes, 2):
                assert not _overlap(a, b), f"{a} overlaps {b}"

    def test_the_drawn_glyphs_of_the_289_figure_do_not_touch(self):
        """#289's actual fault: the box the renderer reserved was narrower than the
        bold glyphs it drew, so `label_boxes()` read clear while `26 dm` printed on
        `24 dm`. Measuring the drawn text independently is the only way to see it."""
        figure = Triangle.base_height(base=17, height=24, apex_frac=7 / 17)
        svg = Scene(
            figure,
            [
                Outline(),
                EdgeLabel("AB", "dm"),
                EdgeLabel("BC", "dm"),
                EdgeLabel("CA", "dm"),
                Altitude(apex="C", base="AB", unit_label="dm"),
            ],
        ).to_svg()

        glyphs = []
        for x, y, size, text in re.findall(
            r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*font-size="([\d.]+)"[^>]*>([^<]*)<',
            svg,
        ):
            x, y, size = float(x), float(y), float(size)
            # How wide a weight-600 system-ui character draws, per unit font size.
            half_w, half_h = 0.34 * size * len(text), 0.58 * size
            glyphs.append((text, (x - half_w, y - half_h, x + half_w, y + half_h)))

        assert len(glyphs) == 4
        for (a, box_a), (b, box_b) in itertools.combinations(glyphs, 2):
            assert not _overlap(box_a, box_b), f"{a} overlaps {b}"


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

    @pytest.mark.parametrize("generator", GENERATORS[1:3], ids=lambda g: g.__name__)
    def test_a_forward_rung_labels_a_length_that_is_neither_base_nor_height(
        self, generator
    ):
        """Without a distractor length, two of the three Traps cannot fire (#237).

        Levels 2 and 3 keep their sides for exactly this reason; Level 1 does not
        (#294), covered separately below.
        """
        problem = generator()
        assert problem is not None
        parameters = problem["parameters"]
        extra = set(parameters) - {"base", "height", "unit"}
        assert extra

    def test_level_1_labels_only_base_and_height(self):
        """#294: the slant sides are gone, so the figure prints exactly the two
        lengths the formula needs — both of them, or the Problem is unsolvable."""
        for _ in range(20):
            problem = topic.geo_triangle_area_1()
            assert problem is not None
            parameters = problem["parameters"]
            unit = parameters["unit"]
            printed = set(
                re.findall(r"<text[^>]*>([^<]*)</text>", problem["image_html"])
            )
            assert printed - {"A", "B", "C"} == {
                f"{parameters['base']} {unit}",
                f"{parameters['height']} {unit}",
            }

    def test_level_1_magnitudes_are_small_enough_to_multiply_mentally(self):
        """#294: dropping the slant sides frees the pool from the Pythagorean-triple
        constraint that used to force base/height into 13-14-15 territory."""
        for _ in range(20):
            problem = topic.geo_triangle_area_1()
            assert problem is not None
            parameters = problem["parameters"]
            assert parameters["base"] <= 12
            assert parameters["height"] <= 12

    def test_level_1_no_longer_emits_the_perimeter_or_side_as_height_traps(self):
        """#294: neither Trap has a visible side to compute its distractor from."""
        for _ in range(40):
            problem = topic.geo_triangle_area_1()
            assert problem is not None
            slugs = set(problem["options_map"].values())
            assert topic.TRAP_PERIMETER not in slugs
            assert topic.TRAP_SIDE_AS_HEIGHT not in slugs

    @pytest.mark.parametrize("generator", GENERATORS[1:3], ids=lambda g: g.__name__)
    def test_levels_2_and_3_still_emit_the_perimeter_and_side_as_height_traps(
        self, generator
    ):
        """#294: these Traps move off Level 1 but stay put where a side is visible."""
        seen: set[str] = set()
        for _ in range(40):
            problem = generator()
            assert problem is not None
            seen |= set(problem["options_map"].values())
        assert topic.TRAP_PERIMETER in seen
        assert topic.TRAP_SIDE_AS_HEIGHT in seen

    def test_the_reverse_rung_withholds_one_dimension_and_varies_which(self):
        """Fixing which dimension is unknown makes the rung solvable without the figure."""
        withheld = set()
        for _ in range(40):
            problem = topic.geo_triangle_area_4()
            if problem is None:
                continue
            height_unknown = problem["parameters"]["height_unknown"]
            symbol = "h" if height_unknown else "a"
            assert f">{symbol}<" in problem["image_html"]
            withheld.add(height_unknown)
        assert withheld == {True, False}

    def test_the_reverse_rung_names_the_same_symbol_in_prose_and_figure(self):
        """#293: the figure and the question text must never name different letters."""
        for _ in range(40):
            problem = topic.geo_triangle_area_4()
            if problem is None:
                continue
            symbol = "h" if problem["parameters"]["height_unknown"] else "a"
            assert rf"\text{{. Oblicz }} {symbol} " in problem["question"]
            assert f">{symbol}<" in problem["image_html"]

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

    @pytest.mark.parametrize("level", [1, 2, 3])
    def test_an_area_level_offers_the_exponent_key(self, curriculum, level):
        """Levels 1-3 expect a squared Unit, so the phone needs a way to type `²` (#292)."""
        problem = generate_level_problem(curriculum, CHAPTER_ID, TOPIC_ID, level)
        assert problem["exponent_key"] is True

    def test_the_reverse_rung_withholds_the_exponent_key(self, curriculum):
        """Level 4 expects a length Unit — no squared Unit is possible there (#292)."""
        problem = generate_level_problem(curriculum, CHAPTER_ID, TOPIC_ID, 4)
        assert problem["exponent_key"] is False


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

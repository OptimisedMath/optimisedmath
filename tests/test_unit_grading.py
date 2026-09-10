"""Tests for the unit-bearing answer contract — ADR-0005 as amended by #237."""

import pytest

import backend.config as config
from backend.answer_grading import grade
from backend.core.units import convert, normalize_unit, split_answer


def _area_problem(**overrides):
    problem = {
        "problem_id": "test-problem",
        "question": r"\text{Oblicz pole trójkąta.}",
        "correct": "84",
        "expected_unit": "cm²",
        "options": ["84", "168", "42"],
        "options_map": {
            "84": "correct",
            "168": "treats_the_triangle_area_as_base_times_height",
            "42": "computes_the_perimeter_instead_of_the_area",
        },
        "messages": {
            "treats_the_triangle_area_as_base_times_height": "Podziel przez 2.",
            "computes_the_perimeter_instead_of_the_area": "To obwód.",
            "filler": "Niepoprawna odpowiedź.",
        },
        "grading_policy": "standard",
    }
    problem.update(overrides)
    return problem


class TestSplitAndNormalize:
    def test_square_marker_is_part_of_the_unit_token(self):
        """`m2` splits as one Unit, not as `m` after a stray digit `2`."""
        assert split_answer("0,0024 m2") == ("0,0024", "m2")

    def test_answer_without_a_trailing_word_reports_no_unit(self):
        """A bare number is *no Unit given*, distinct from an unreadable one."""
        assert split_answer("24") == ("24", None)

    def test_unrecognised_trailing_word_is_returned_not_discarded(self):
        """A non-Unit word survives the split, so the grader can say so."""
        assert split_answer("24 kotów") == ("24", "kotów")

    @pytest.mark.parametrize("typed", ["cm2", "cm^2", "CM²", " cm ² "])
    def test_phone_typable_forms_normalize_to_the_catalogue_unit(self, typed):
        """A phone keyboard has no `²`, so demanding one would penalize the device."""
        assert normalize_unit(typed) == "cm²"

    def test_conversion_across_dimensions_is_impossible(self):
        """No factor exists between `cm` and `cm²` — this is what makes a wrong
        dimension short-circuit conversion instead of converting to right."""
        assert convert(24, "cm", "cm²") is None


class TestUnitGrading:
    @pytest.mark.parametrize("typed", ["84 cm²", "84 cm2", "84 CM^2", "84cm2"])
    def test_expected_unit_in_any_typable_form_is_correct(self, typed):
        assert grade(typed, _area_problem(), is_input_mode=True)["is_correct"]

    def test_correct_conversion_is_correct(self):
        """`0,0084 m²` is Correct for `84 cm²`: converting is more work, not less."""
        assert grade("0,0084 m²", _area_problem(), is_input_mode=True)["is_correct"]

    def test_conversion_resolves_correct_exactly_not_approximately(self):
        """Factors are integers, so the comparison is exact — 8400 mm² is 84 cm²."""
        assert grade("8400 mm²", _area_problem(), is_input_mode=True)["is_correct"]

    def test_a_missing_unit_is_wrong_not_a_soft_error(self):
        """Here the Unit is part of the answer, so omitting it is penalized."""
        result = grade("84", _area_problem(), is_input_mode=True)
        assert result["answer_outcome"] == "wrong"
        assert result["lock_answer"] is True
        assert result["feedback_msg"] == config.MISSING_UNIT_MESSAGE

    def test_an_unrecognised_unit_is_wrong_with_its_own_prose(self):
        result = grade("84 kotów", _area_problem(), is_input_mode=True)
        assert result["answer_outcome"] == "wrong"
        assert result["feedback_msg"] == config.UNKNOWN_UNIT_MESSAGE

    def test_a_malformed_number_is_still_a_soft_error(self):
        """Only the Unit half of the answer is exempt from Soft Errors."""
        result = grade("osiem", _area_problem(), is_input_mode=True)
        assert result["answer_outcome"] == "syntax_error"
        assert result["lock_answer"] is False

    def test_wrong_dimension_synthesizes_the_length_versus_area_trap(self):
        """The grader raises this Trap itself; no generator authors it."""
        result = grade("84 cm", _area_problem(), is_input_mode=True)
        assert result["answer_outcome"] == "trap"
        assert result["trap_slug"] == config.UNIT_DIMENSION_TRAP_SLUG
        assert result["misconception_slug"] == "confuses_length_and_area_units"

    def test_wrong_scale_synthesizes_the_conversion_trap(self):
        result = grade("84 mm²", _area_problem(), is_input_mode=True)
        assert result["answer_outcome"] == "trap"
        assert result["misconception_slug"] == "converts_units_incorrectly"

    def test_the_number_decides_which_trap_fires_not_the_unit(self):
        """#229: a Unit Trap fires only on the expected number, so an answer whose
        number matches an authored Trap *is* that Trap."""
        result = grade("168 cm", _area_problem(), is_input_mode=True)
        assert result["trap_slug"] == "treats_the_triangle_area_as_base_times_height"

    def test_a_trap_number_typed_in_another_unit_still_names_its_own_rule(self):
        """Conversion applies to Trap matching too, not only to Correct — otherwise
        `1,68 dm²` would fall through to the generic wrong-answer message."""
        result = grade("1,68 dm²", _area_problem(), is_input_mode=True)
        assert result["trap_slug"] == "treats_the_triangle_area_as_base_times_height"

    def test_an_unmatched_wrong_number_is_plain_wrong(self):
        result = grade("50 cm²", _area_problem(), is_input_mode=True)
        assert result["answer_outcome"] == "wrong"
        assert "trap_slug" not in result

    def test_radio_mode_never_sees_a_unit(self):
        """Options are bare numbers, so the Unit can never be the discriminator."""
        assert grade("84", _area_problem(), is_input_mode=False)["is_correct"]

    def test_a_problem_without_an_expected_unit_grades_unchanged(self):
        """The other 95 generators are untouched by any of this."""
        problem = _area_problem()
        del problem["expected_unit"]
        assert grade("84", problem, is_input_mode=True)["is_correct"]

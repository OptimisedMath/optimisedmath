# tests/test_core_logic.py
import random
import re

import pytest
from fractions import Fraction

from backend.core.utils import (
    build_problem_dict,
    clean_mobile_input,
    clean_latex,
    check_text_answer,
    fmt_dec,
    format_answers,
    format_fraction_answer,
    parse_to_fraction,
)


class TestMobileSanitizer:
    """Tests the middleware that cleans messy mobile keyboard inputs."""

    @pytest.mark.parametrize(
        "user_input, expected",
        [
            ("1,5", "1,5"),
            ("1.5", "1,5"),
            ("0.52", "0,52"),
            ("1-1/2", "1 1/2"),
            ("1.1/2", "1 1/2"),
            ("  3/4  ", "3/4"),
            ("1   1/2", "1 1/2"),
            ("", ""),
            (None, ""),
        ],
    )
    def test_clean_mobile_input(self, user_input, expected):
        assert clean_mobile_input(user_input) == expected


class TestLatexCleaner:
    @pytest.mark.parametrize(
        "latex_in, expected",
        [
            ("$\\displaystyle 1\\frac{1}{2}$", "1 1/2"),
            ("\\frac{3}{4}", "3/4"),
            ("$\\displaystyle \\frac{10}{20}$", "10/20"),
            ("2\\frac{1}{3}", "2 1/3"),
            ("\\dfrac{3}{4}", "3/4"),
            ("$3 + \\displaystyle\\frac{1}{2}$", "3 + 1/2"),
            (r"-\frac{5}{3}", "-5/3"),
        ],
    )
    def test_clean_latex(self, latex_in, expected):
        assert clean_latex(latex_in) == expected


class TestEvaluationLogic:
    @pytest.mark.parametrize(
        "correct_latex, user_text, is_match",
        [
            ("3/4", "3/4", True),
            ("3/4", "3 / 4", True),
            ("1 \\frac{1}{2}", "1 1/2", True),
            ("0,5", "0,5", True),
            ("0,52", "0,52", True),
            ("3/4", "1/2", False),
            ("1 \\frac{1}{2}", "11/2", False),
        ],
    )
    def test_check_text_answer(self, correct_latex, user_text, is_match):
        assert check_text_answer(correct_latex, user_text) is is_match


class TestFormatters:
    @pytest.mark.parametrize(
        "val, expected",
        [
            (1.5, "1,5"),
            (2.0, "2"),
            (0.5200, "0,52"),
            (0.0, "0"),
            (0.25, "0,25"),
        ],
    )
    def test_fmt_dec(self, val, expected):
        assert fmt_dec(val) == expected


class TestFormatFractionAnswer:
    @pytest.mark.parametrize(
        "num, den, simplify, expected",
        [
            (9, 3, False, r"\frac{9}{3}"),
            (9, 3, True, "3"),
            (6, 4, False, r"\frac{6}{4}"),
            (6, 4, True, r"1\frac{1}{2}"),
            (3, 1, False, "3"),
        ],
    )
    def test_format_fraction_answer(self, num, den, simplify, expected):
        assert format_fraction_answer(num, den, simplify=simplify) == expected

    def test_format_fraction_answer_mixed_unsimplified(self):
        assert format_fraction_answer(2, 3, 1, simplify=False) == r"1\frac{2}{3}"


class TestFormatAnswers:
    @pytest.mark.parametrize(
        "num, den, whole, expected_canonical, expected_unsimplified",
        [
            (1, 4, 2, r"2\frac{1}{4}", r"\frac{9}{4}"),
            (6, 4, 0, r"1\frac{1}{2}", r"\frac{6}{4}"),
            (3, 1, 0, "3", "3"),
            (2, 3, 0, r"\frac{2}{3}", r"\frac{2}{3}"),
        ],
    )
    def test_format_answers_positive(
        self, num, den, whole, expected_canonical, expected_unsimplified
    ):
        c_str, u_str = format_answers(num, den, whole)
        assert c_str == expected_canonical
        assert u_str == expected_unsimplified

    @pytest.mark.parametrize(
        "num, den, whole, expected_canonical",
        [
            (-5, 3, 0, r"-1\frac{2}{3}"),
            (2, 3, -1, r"-\frac{1}{3}"),
            (-1, 3, 0, r"-\frac{1}{3}"),
        ],
    )
    def test_format_answers_negative(self, num, den, whole, expected_canonical):
        c_str, u_str = format_answers(num, den, whole)
        assert c_str == expected_canonical
        assert parse_to_fraction(u_str) == parse_to_fraction(c_str)


class TestParseToFraction:
    @pytest.mark.parametrize(
        "val_str, expected",
        [
            (r"1\frac{1}{2}", Fraction(3, 2)),
            ("1 1/2", Fraction(3, 2)),
            ("0,5", Fraction(1, 2)),
            ("2/4", Fraction(1, 2)),
            ("-1 1/2", Fraction(-3, 2)),
            ("1,1/2", Fraction(3, 2)),
            ("", None),
            ("not-a-number", None),
        ],
    )
    def test_parse_to_fraction(self, val_str, expected):
        assert parse_to_fraction(val_str) == expected


class TestBuildProblemDict:
    def test_duplicate_trap_strings_are_padded_not_dropped(self):
        """Two Traps with identical strings emit the Problem; the earlier keeps its label."""
        problem = build_problem_dict(
            "q", "1/2", traps={"a": "3/4", "b": "3/4"}, parameters={}
        )
        assert problem is not None
        assert problem["options_map"]["3/4"] == "a"
        assert len(problem["options"]) == 4

    def test_trap_equal_to_correct_is_labelled_correct(self):
        problem = build_problem_dict(
            "q", "1/2", traps={"a": "1/2", "b": "3/4"}, parameters={}
        )
        assert problem["options_map"]["1/2"] == "correct"
        assert len(problem["options"]) == 4

    def test_trap_equal_in_value_but_not_string_is_kept(self):
        problem = build_problem_dict(
            "q", r"\frac{4}{5}", traps={"a": r"\frac{12}{15}"}, parameters={}
        )
        assert problem["options_map"][r"\frac{12}{15}"] == "a"

    def test_more_than_three_traps_only_first_three_offered(self):
        problem = build_problem_dict(
            "q",
            "1",
            traps={"a": "2", "b": "3", "c": "4", "d": "5"},
            parameters={},
        )
        assert set(problem["options"]) == {"1", "2", "3", "4"}
        assert "5" not in problem["options"]

    def test_none_trap_frees_slot_for_next_declared_trap(self):
        problem = build_problem_dict(
            "q",
            "1",
            traps={"a": None, "b": "2", "c": "3", "d": "4"},
            parameters={},
        )
        assert set(problem["options"]) == {"1", "2", "3", "4"}

    def test_negative_trap_skipped_by_default(self):
        problem = build_problem_dict(
            "q", "1", traps={"a": "-2", "b": "3"}, parameters={}
        )
        assert "-2" not in problem["options"]
        assert "3" in problem["options"]

    def test_negative_trap_kept_when_allowed(self):
        problem = build_problem_dict(
            "q",
            "1",
            traps={"a": "-2"},
            parameters={},
            allow_negative_options=True,
        )
        assert "-2" in problem["options"]

    def test_comparison_symbol_ordering(self):
        problem = build_problem_dict(
            "q", "<", traps={"a": ">", "b": "="}, parameters={}
        )
        assert problem is not None
        assert problem["options"] == ["<", "=", ">"]

    def test_comparison_problems_are_never_padded(self):
        problem = build_problem_dict("q", "<", traps={"a": ">"}, parameters={})
        assert len(problem["options"]) == 2

    def test_no_improper_unsimplified_keys(self):
        problem = build_problem_dict("q", "1/2", traps={"a": "2/3"}, parameters={})
        assert problem is not None
        assert "improper" not in problem
        assert "unsimplified" not in problem

    def test_parameters_included(self):
        problem = build_problem_dict(
            "q", "1/2", parameters={"n": 1, "d": 2.5, "op": "+"}
        )
        assert problem is not None
        assert problem["parameters"] == {"n": 1, "d": 2.5, "op": "+"}

    def test_parameters_is_required(self):
        with pytest.raises(TypeError):
            build_problem_dict("q", "1/2")

    def test_empty_slots_are_padded_with_fillers(self):
        problem = build_problem_dict("q", "1/2", parameters={})
        assert len(problem["options"]) == 4
        labels = list(problem["options_map"].values())
        assert labels.count("filler") == 3

    def test_fillers_differ_in_value_from_every_option(self, monkeypatch):
        monkeypatch.setattr(random, "choice", lambda seq: seq[0])
        problem = build_problem_dict(
            "q", "1/2", traps={"a": "3/4"}, parameters={}
        )
        values = {
            parse_to_fraction(v) or v for v in problem["options"]
        }
        assert len(values) == len(problem["options"])
        for label in problem["options_map"].values():
            assert label in {"correct", "a", "filler"}

    def test_filler_keeps_mixed_shape(self, monkeypatch):
        monkeypatch.setattr(random, "choice", lambda seq: seq[0])
        problem = build_problem_dict(
            "q", r"2\frac{1}{5}", parameters={}
        )
        for value, label in problem["options_map"].items():
            if label != "filler":
                continue
            assert re.fullmatch(r"\d+\\frac\{\d+\}\{\d+\}", value)

    def test_filler_keeps_decimal_places(self, monkeypatch):
        monkeypatch.setattr(random, "choice", lambda seq: seq[0])
        problem = build_problem_dict("q", "8,2", parameters={})
        for value, label in problem["options_map"].items():
            if label != "filler":
                continue
            assert re.fullmatch(r"-?\d+,\d$", value)

    def test_no_filler_is_negative_by_default(self):
        problem = build_problem_dict("q", "1", parameters={})
        for value in problem["options"]:
            assert not value.startswith("-")

    def test_notation_exception_gives_correct_answer_company(self, monkeypatch):
        """`frac_add_1`-shaped case: correct is a whole number, Trap a fraction.

        Without the exception both Fillers would be fractions, leaving the correct
        answer the only whole number on screen.
        """
        monkeypatch.setattr(random, "choice", lambda seq: seq[0])
        problem = build_problem_dict(
            "q", "1", traps={"adds_the_denominators": r"\frac{1}{2}"}, parameters={}
        )
        whole_numbers = [v for v in problem["options"] if re.fullmatch(r"-?\d+", v)]
        assert len(whole_numbers) >= 2

    def test_explicit_fillers_replace_the_rule(self):
        problem = build_problem_dict(
            "q", "1", fillers=["0,(3)"], parameters={}
        )
        assert "0,(3)" in problem["options"]
        assert len(problem["options"]) == 2

    def test_explicit_none_filler_is_skipped(self):
        problem = build_problem_dict("q", "1", fillers=[None, "2"], parameters={})
        assert problem["options"] == sorted(problem["options"]) or set(
            problem["options"]
        ) == {"1", "2"}

    def test_never_returns_none(self):
        problem = build_problem_dict(
            "q", "1", traps={"a": "1", "b": "1", "c": "1"}, parameters={}
        )
        assert problem is not None

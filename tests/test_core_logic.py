# tests/test_core_logic.py
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
    def test_duplicate_options_returns_none(self):
        assert build_problem_dict("q", "1/2", traps={"a": "1/2", "b": "3/4"}) is None

    def test_comparison_symbol_ordering(self):
        problem = build_problem_dict("q", "<", traps={"a": ">", "b": "="})
        assert problem is not None
        assert problem["options"] == ["<", "=", ">"]

    def test_no_improper_unsimplified_keys(self):
        problem = build_problem_dict("q", "1/2", traps={"a": "2/3"})
        assert problem is not None
        assert "improper" not in problem
        assert "unsimplified" not in problem

    def test_parameters_included_when_provided(self):
        problem = build_problem_dict(
            "q", "1/2", parameters={"n": 1, "d": 2.5, "op": "+"}
        )
        assert problem is not None
        assert problem["parameters"] == {"n": 1, "d": 2.5, "op": "+"}

    def test_parameters_absent_when_not_provided(self):
        problem = build_problem_dict("q", "1/2")
        assert problem is not None
        assert "parameters" not in problem

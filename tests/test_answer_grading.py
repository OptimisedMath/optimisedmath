"""Tests for backend.answer_grading and problem_generation registry helpers."""

import pytest

from backend.answer_grading import grade
from backend.problem_generation import (
    GeneratorRegistryError,
    _register_generator,
    problem_fingerprint,
)


def _sample_problem(**overrides):
    base = {
        "problem_id": "test-problem",
        "question": r"\text{Oblicz: } \frac{1}{2} + \frac{1}{2}",
        "correct": "1",
        "options": ["1", r"\frac{2}{4}", "2"],
        "options_map": {
            "1": "correct",
            r"\frac{2}{4}": "t1",
            "2": "t2",
        },
        "messages": {
            "t1": "Trap one",
            "t2": "Trap two",
        },
        "grading_policy": "standard",
    }
    base.update(overrides)
    return base


def _exact_match_only_problem():
    """An `exact_match_only` problem whose options hold no Trap a value-equal answer matches."""
    return _sample_problem(
        correct=r"\frac{1}{2}",
        options=["1", "2"],
        options_map={
            "1": "correct",
            "2": "t2",
        },
        grading_policy="exact_match_only",
    )


class TestProblemFingerprint:
    def test_same_content_same_fingerprint(self):
        first = _sample_problem()
        second = _sample_problem(problem_id="different-id")
        assert problem_fingerprint(first) == problem_fingerprint(second)

    def test_different_correct_answer_different_fingerprint(self):
        first = _sample_problem()
        second = _sample_problem(correct="2")
        assert problem_fingerprint(first) != problem_fingerprint(second)

    def test_different_fillers_same_fingerprint(self):
        """Two servings of one question share a fingerprint despite different Fillers (ADR-0009)."""
        first = _sample_problem(options=["1", r"\frac{2}{4}", "2"])
        second = _sample_problem(options=["1", "5", "9"])
        assert problem_fingerprint(first) == problem_fingerprint(second)


class TestRegistryCollision:
    def test_register_generator_rejects_duplicate_names(self):
        registry: dict[str, object] = {}
        sources: dict[str, str] = {}

        _register_generator(registry, sources, "frac_test", lambda: None, "mod.a")
        with pytest.raises(GeneratorRegistryError, match="Duplicate generator"):
            _register_generator(registry, sources, "frac_test", lambda: None, "mod.b")


class TestMultipleChoiceGrading:
    def test_correct_answer(self):
        result = grade("1", _sample_problem(), input_mode="radio")
        assert result["is_correct"] is True
        assert result["lock_answer"] is True
        assert result["answer_outcome"] == "correct"

    def test_trap_answer(self):
        result = grade(r"\frac{2}{4}", _sample_problem(), input_mode="radio")
        assert "is_correct" not in result
        assert result["answer_outcome"] == "trap"
        assert result["trap_slug"] == "t1"
        assert result["feedback_msg"] == "Trap one"

    def test_unanticipated_answer_not_in_options_map(self):
        """An option absent from options_map is unanticipated: Wrong, not Filler."""
        result = grade("not-an-option", _sample_problem(), input_mode="radio")
        assert result["answer_outcome"] == "wrong"
        assert "trap_slug" not in result


class TestTextGrading:
    def test_exact_text_match(self):
        result = grade("1", _sample_problem(), input_mode="typing")
        assert result["is_correct"] is True
        assert result["answer_outcome"] == "correct"

    def test_syntax_error(self):
        result = grade("abc", _sample_problem(), input_mode="typing")
        assert result["answer_outcome"] == "syntax_error"
        assert result["lock_answer"] is False

    def test_equivalent_unsimplified(self):
        problem = _sample_problem(correct=r"\frac{1}{2}")
        result = grade("2/4", problem, input_mode="typing")
        assert result["answer_outcome"] == "unsimplified"
        assert result["lock_answer"] is False

    def test_equivalent_accepted_policy(self):
        problem = _sample_problem(
            correct=r"\frac{1}{2}",
            grading_policy="equivalent_accepted",
        )
        result = grade("2/4", problem, input_mode="typing")
        assert result["is_correct"] is True
        assert result["answer_outcome"] == "correct"

    def test_exact_match_only_policy(self):
        """Value-equal in the wrong form is Wrong with the generic message, never a Soft Error (#312)."""
        result = grade("2/4", _exact_match_only_problem(), input_mode="typing")
        assert result["answer_outcome"] == "wrong"
        assert result["lock_answer"] is True
        assert result["feedback_type"] == "warning"
        assert result["feedback_msg"] == "Niepoprawna odpowiedź, spróbuj ponownie."

    def test_exact_match_only_notation_check_still_runs_first(self):
        """A decimal where a common fraction was asked stays a Soft Error under exact_match_only."""
        result = grade("0,5", _exact_match_only_problem(), input_mode="typing")
        assert result["answer_outcome"] == "format_mismatch"
        assert result["lock_answer"] is False
        assert result["feedback_type"] == "info"

    def test_exact_match_equivalent_trap_shows_trap_message(self):
        problem = _sample_problem(
            correct=r"\frac{3}{7}",
            options=[r"\frac{3}{7}", r"\frac{9}{21}", "1"],
            options_map={
                r"\frac{3}{7}": "correct",
                r"\frac{9}{21}": "t1",
                "1": "t2",
            },
            messages={
                "t1": "Partially simplified trap",
                "t2": "Trap two",
            },
            grading_policy="exact_match_only",
        )
        result = grade("9/21", problem, input_mode="typing")
        assert result["answer_outcome"] == "trap"
        assert result["trap_slug"] == "t1"
        assert result["feedback_msg"] == "Partially simplified trap"
        assert "is_correct" not in result

    def test_text_trap_match(self):
        problem = _sample_problem(correct="1")
        result = grade("2", problem, input_mode="typing")
        assert result["answer_outcome"] == "trap"
        assert result["trap_slug"] == "t2"

    def test_missing_options_map_does_not_crash(self):
        problem = _sample_problem()
        del problem["options_map"]
        result = grade("9", problem, input_mode="typing")
        assert result["answer_outcome"] == "wrong"


class TestFormatMismatch:
    @pytest.mark.parametrize(
        "user_text, correct_latex, expected_substring",
        [
            ("1/2", "0,5", "ułamków dziesiętnych"),
            ("0,5", r"\frac{1}{2}", "ułamka zwykłego"),
        ],
    )
    def test_format_mismatch_messages(
        self, user_text, correct_latex, expected_substring
    ):
        problem = _sample_problem(
            correct=correct_latex,
            grading_policy="equivalent_accepted",
        )
        result = grade(user_text, problem, input_mode="typing")
        assert result["answer_outcome"] == "format_mismatch"
        assert expected_substring in result["feedback_msg"]

    def test_no_mismatch_for_matching_formats(self):
        problem = _sample_problem(
            correct=r"\frac{1}{2}",
            grading_policy="equivalent_accepted",
        )
        result = grade("1/2", problem, input_mode="typing")
        assert result.get("answer_outcome") != "format_mismatch"
        assert result["is_correct"] is True

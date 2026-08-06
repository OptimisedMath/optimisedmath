"""Tests for backend.engine grading and registry helpers."""

import pytest

import backend.engine as engine
from backend.engine import (
    GeneratorRegistryError,
    ProblemGenerationError,
    _register_generator,
    evaluate_answer,
    generate_level_problem,
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
            "2": "w1",
        },
        "messages": {
            "t1": "Trap one",
            "w1": "Wrong one",
        },
        "grading_policy": "standard",
    }
    base.update(overrides)
    return base


class TestProblemFingerprint:
    def test_same_content_same_fingerprint(self):
        first = _sample_problem()
        second = _sample_problem(problem_id="different-id")
        assert problem_fingerprint(first) == problem_fingerprint(second)

    def test_different_correct_answer_different_fingerprint(self):
        first = _sample_problem()
        second = _sample_problem(correct="2")
        assert problem_fingerprint(first) != problem_fingerprint(second)


class TestRegistryCollision:
    def test_register_generator_rejects_duplicate_names(self):
        registry: dict[str, object] = {}
        sources: dict[str, str] = {}

        _register_generator(registry, sources, "frac_test", lambda: None, "mod.a")
        with pytest.raises(GeneratorRegistryError, match="Duplicate generator"):
            _register_generator(registry, sources, "frac_test", lambda: None, "mod.b")


class TestMultipleChoiceGrading:
    def test_correct_answer(self):
        result = evaluate_answer("1", _sample_problem(), is_input_mode=False)
        assert result["is_correct"] is True
        assert result["lock_answer"] is True

    def test_trap_answer(self):
        result = evaluate_answer(
            r"\frac{2}{4}", _sample_problem(), is_input_mode=False
        )
        assert "is_correct" not in result
        assert result["trap_id"] == "t1"
        assert result["feedback_msg"] == "Trap one"

    def test_wrong_answer(self):
        result = evaluate_answer("2", _sample_problem(), is_input_mode=False)
        assert result["trap_id"] == "w1"
        assert result["feedback_msg"] == "Wrong one"


class TestTextGrading:
    def test_exact_text_match(self):
        result = evaluate_answer("1", _sample_problem(), is_input_mode=True)
        assert result["is_correct"] is True

    def test_syntax_error(self):
        result = evaluate_answer("abc", _sample_problem(), is_input_mode=True)
        assert result["trap_id"] == "syntax_error"
        assert result["lock_answer"] is False

    def test_equivalent_unsimplified(self):
        problem = _sample_problem(correct=r"\frac{1}{2}")
        result = evaluate_answer("2/4", problem, is_input_mode=True)
        assert result["trap_id"] == "unsimplified"
        assert result["lock_answer"] is False

    def test_equivalent_accepted_policy(self):
        problem = _sample_problem(
            correct=r"\frac{1}{2}",
            grading_policy="equivalent_accepted",
        )
        result = evaluate_answer("2/4", problem, is_input_mode=True)
        assert result["is_correct"] is True

    def test_exact_match_only_policy(self):
        problem = _sample_problem(
            correct=r"\frac{1}{2}",
            options=["1", "2"],
            options_map={
                "1": "correct",
                "2": "w1",
            },
            grading_policy="exact_match_only",
        )
        result = evaluate_answer("2/4", problem, is_input_mode=True)
        assert result["trap_id"] == "exact_match_violation"
        assert result["lock_answer"] is True

    def test_exact_match_equivalent_trap_shows_trap_message(self):
        problem = _sample_problem(
            correct=r"\frac{3}{7}",
            options=[r"\frac{3}{7}", r"\frac{9}{21}", "1"],
            options_map={
                r"\frac{3}{7}": "correct",
                r"\frac{9}{21}": "t1",
                "1": "w1",
            },
            messages={
                "t1": "Partially simplified trap",
                "w1": "Wrong one",
            },
            grading_policy="exact_match_only",
        )
        result = evaluate_answer("9/21", problem, is_input_mode=True)
        assert result["trap_id"] == "t1"
        assert result["feedback_msg"] == "Partially simplified trap"
        assert "is_correct" not in result

    def test_text_trap_match(self):
        problem = _sample_problem(correct="1")
        result = evaluate_answer("2", problem, is_input_mode=True)
        assert result["trap_id"] == "w1"

    def test_missing_options_map_does_not_crash(self):
        problem = _sample_problem()
        del problem["options_map"]
        result = evaluate_answer("9", problem, is_input_mode=True)
        assert result["trap_id"] == "w1"


class TestFormatMismatch:
    @pytest.mark.parametrize(
        "user_text, correct_latex, expected_substring",
        [
            ("1/2", "0,5", "ułamków dziesiętnych"),
            ("0,5", r"\frac{1}{2}", "ułamka zwykłego"),
        ],
    )
    def test_format_mismatch_messages(self, user_text, correct_latex, expected_substring):
        problem = _sample_problem(
            correct=correct_latex,
            grading_policy="equivalent_accepted",
        )
        result = evaluate_answer(user_text, problem, is_input_mode=True)
        assert result["trap_id"] == "format_mismatch"
        assert expected_substring in result["feedback_msg"]

    def test_no_mismatch_for_matching_formats(self):
        problem = _sample_problem(
            correct=r"\frac{1}{2}",
            grading_policy="equivalent_accepted",
        )
        result = evaluate_answer("1/2", problem, is_input_mode=True)
        assert result.get("trap_id") != "format_mismatch"
        assert result["is_correct"] is True


class TestGenerateLevelProblem:
    def test_generates_real_fraction_problem(self):
        problem = generate_level_problem(10, 10, 1)
        assert problem["question"]
        assert problem["correct"]
        assert problem["problem_id"]
        assert "error" not in problem

    def test_missing_chapter_raises(self):
        with pytest.raises(ProblemGenerationError, match="Missing curriculum"):
            generate_level_problem(999, 10, 1)

    def test_missing_topic_raises(self):
        with pytest.raises(ProblemGenerationError, match="Topic id"):
            generate_level_problem(10, 99999, 1)

    def test_missing_level_raises(self):
        with pytest.raises(ProblemGenerationError, match="Level 999"):
            generate_level_problem(10, 10, 999)

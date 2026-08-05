"""Facade for problem generation and answer grading modules."""

from backend.answer_grading import EvalResult, evaluate_answer, grade
from backend.curriculum_loader import get_chapters, get_curriculum
from backend.problem_generation import (
    FUNCTION_REGISTRY,
    GeneratorRegistryError,
    ProblemGenerationError,
    generate_level_problem,
    generate_problem,
    get_curriculum_response,
    problem_fingerprint,
)
from backend.problem_generation import (
    _register_generator,
)

__all__ = [
    "EvalResult",
    "FUNCTION_REGISTRY",
    "GeneratorRegistryError",
    "ProblemGenerationError",
    "_register_generator",
    "evaluate_answer",
    "generate_level_problem",
    "generate_problem",
    "get_chapters",
    "get_curriculum",
    "get_curriculum_response",
    "grade",
    "problem_fingerprint",
]

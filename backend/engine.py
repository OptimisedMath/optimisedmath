"""Problem generation, generator registry, and answer grading."""

import hashlib
import importlib
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from backend.core.utils import check_text_answer, parse_to_fraction
from backend.curriculum_loader import (
    get_curriculum,
    get_level_config,
    get_macro_keyboard_type,
    get_macro_topics_ordered,
    get_topic_map,
    set_function_registry,
)
from backend.models import CurriculumResponse, CurriculumTopic
import backend.config as config

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)

class GeneratorRegistryError(Exception):
    """Raised when generator registration fails."""


class ProblemGenerationError(Exception):
    """Raised when a level problem cannot be generated."""


GeneratorFunc = Callable[[], dict[str, Any] | None]


def _is_generator(name: str, value: object, module_name: str) -> bool:
    return (
        callable(value)
        and not name.startswith("_")
        and getattr(value, "__module__", None) == module_name
    )


def _register_generator(
    registry: dict[str, GeneratorFunc],
    sources: dict[str, str],
    name: str,
    func: GeneratorFunc,
    module_path: str,
) -> None:
    if name in registry:
        raise GeneratorRegistryError(
            f"Duplicate generator '{name}' in {module_path} "
            f"(already registered from {sources[name]})"
        )
    registry[name] = func
    sources[name] = module_path


def _load_generator_registry(macro_topics_dir: Path) -> dict[str, GeneratorFunc]:
    registry: dict[str, GeneratorFunc] = {}
    sources: dict[str, str] = {}

    for file_path in macro_topics_dir.rglob("micro_*.py"):
        module_path = ".".join(
            file_path.relative_to(BASE_DIR.parent).with_suffix("").parts
        )
        module = importlib.import_module(module_path)

        for name, value in module.__dict__.items():
            if _is_generator(name, value, module.__name__):
                _register_generator(registry, sources, name, value, module_path)

    return registry


# --- THE AUTOLOADER ---
FUNCTION_REGISTRY = _load_generator_registry(BASE_DIR / "macro_topics")
set_function_registry(FUNCTION_REGISTRY)


def get_curriculum_response() -> CurriculumResponse:
    """Return curriculum metadata formatted for the API."""
    curriculum = get_curriculum()
    return CurriculumResponse(
        macro_topics=get_macro_topics_ordered(),
        micro_topics={
            macro_topic: [CurriculumTopic(**topic) for topic in topic_list]
            for macro_topic, topic_list in curriculum.items()
        },
    )


def problem_fingerprint(problem: dict) -> str:
    """Stable identity for a generated problem instance (excludes problem_id)."""
    options = "|".join(sorted(str(opt) for opt in problem.get("options", [])))
    payload = f"{problem.get('question', '')}|{problem.get('correct', '')}|{options}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_level_problem(macro_topic: str, micro_topic: str, level: int) -> dict[str, Any]:
    """Generate a problem for a curriculum level."""
    topic_map = get_topic_map(macro_topic)
    if not topic_map:
        raise ProblemGenerationError(f"Missing curriculum file for: {macro_topic}")

    known_names = {meta["name"] for meta in topic_map.values()}
    if micro_topic not in known_names:
        raise ProblemGenerationError(
            f"Micro topic '{micro_topic}' not found in '{macro_topic}'"
        )

    level_config = get_level_config(macro_topic, micro_topic, level)
    if level_config is None or not level_config.published:
        raise ProblemGenerationError(
            f"Level {level} is not available for '{micro_topic}' in '{macro_topic}'"
        )

    func_name = level_config.function
    problem_func = FUNCTION_REGISTRY.get(func_name)
    if not problem_func:
        raise ProblemGenerationError(f"Function {func_name} not found")

    try:
        problem_dict = generate_problem(problem_func)
    except RuntimeError as exc:
        raise ProblemGenerationError(str(exc)) from exc

    problem_dict["level"] = int(level)
    problem_dict["level_name"] = level_config.name
    problem_dict["problem_id"] = str(uuid.uuid4())

    default_msg = config.DEFAULT_WRONG_MESSAGE
    traps = level_config.traps
    yaml_messages = {
        "t1": traps.get("t1") or default_msg,
        "t2": traps.get("t2") or default_msg,
        "t3": traps.get("t3") or default_msg,
    }
    gen_messages = problem_dict.pop("messages", {})
    problem_dict["messages"] = {**yaml_messages, **gen_messages}
    problem_dict["level_display"] = f"{level_config.name} (Lvl {level})"
    problem_dict["keyboard_type"] = get_macro_keyboard_type(macro_topic)
    return problem_dict


def generate_problem(topic_function: GeneratorFunc) -> dict[str, Any]:
    """Generate a problem using the given topic function, with retry logic for valid problems.

    Args:
        topic_function: A callable that generates a problem dict

    Raises:
        RuntimeError: If problem generation fails after max retries
    """
    for attempt in range(config.MAX_RETRIES_GENERATE):
        try:
            problem = topic_function()
            if problem is not None:
                return problem
        except Exception:
            logger.exception(
                "Problem generator %s failed on attempt %s",
                topic_function.__name__,
                attempt + 1,
            )
            continue

    raise RuntimeError(
        f"Failed to generate valid problem for {topic_function.__name__} "
        f"after {config.MAX_RETRIES_GENERATE} attempts"
    )


def check_format_mismatch(user_text, correct_latex):
    """Intercepts answers that are mathematically correct but use the wrong notation system."""
    user_str = str(user_text)
    if "/" in user_str and "," in correct_latex:
        return "Wynik poprawny matematycznie, ale to jest zadanie z ułamków dziesiętnych! Zapisz odpowiedź używając przecinka, a nie ułamka zwykłego."
    if ("," in user_str or "." in user_str) and "\\frac" in correct_latex:
        return "Wynik poprawny matematycznie, ale w tym zadaniu powinieneś użyć ułamka zwykłego, a nie dziesiętnego!"
    return None


def evaluate_answer(user_input, problem, is_text_mode=False):
    """Grade a submission against a generated problem.

    Handles multiple-choice (options_map), open-text (parse + grading_policy),
    trap/wrong feedback, and format-mismatch warnings.

    Returns:
        Dict with keys like is_correct, lock_answer, feedback_type,
        feedback_msg, trap_id (subset depends on outcome).
    """
    options_map = problem.get("options_map", {})

    # --- 1. MULTIPLE CHOICE MODE ---
    if not is_text_mode and "options" in problem and len(problem["options"]) > 0:
        is_correct = options_map.get(user_input) == "correct"
        if is_correct:
            return {"is_correct": True, "lock_answer": True}
        else:
            msg_key = options_map.get(user_input, "w1")
            msg_text = problem.get("messages", {}).get(
                msg_key, "Niepoprawna odpowiedź, spróbuj ponownie."
            )

            return {
                "lock_answer": True,
                "feedback_type": "warning",
                "feedback_msg": msg_text,
                "trap_id": msg_key,
            }

    # --- 2. TEXT INPUT MODE ---
    policy = problem.get("grading_policy", "standard")

    if check_text_answer(problem["correct"], user_input):
        return {"is_correct": True, "lock_answer": True}

    student_val = parse_to_fraction(str(user_input))
    correct_val = parse_to_fraction(problem["correct"])

    if student_val is None:
        return {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "Niepoprawny zapis matematyczny.",
            "trap_id": "syntax_error",
        }

    if student_val == correct_val:
        format_warning = check_format_mismatch(user_input, problem["correct"])
        if format_warning:
            return {
                "lock_answer": False,
                "feedback_type": "info",
                "feedback_msg": format_warning,
                "trap_id": "format_mismatch",
            }

        if policy == "exact_match_only":
            return {
                "lock_answer": True,
                "feedback_type": "warning",
                "feedback_msg": "W tym zadaniu wartość matematyczna to nie wszystko. Musisz zapisać ułamek w dokładnie takiej postaci, o jaką prosi polecenie!",
                "trap_id": "exact_match_violation",
            }
        elif policy == "equivalent_accepted":
            return {"is_correct": True, "lock_answer": True}
        else:
            return {
                "lock_answer": False,
                "feedback_type": "info",
                "feedback_msg": "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!",
                "trap_id": "unsimplified",
            }

    # --- 3. TEXT MODE TRAP SCANNER ---
    for opt_str, opt_type in options_map.items():
        if opt_type in ["t1", "t2", "t3", "w1", "w2"]:
            opt_val = parse_to_fraction(opt_str)
            if check_text_answer(opt_str, user_input) or (
                opt_val is not None and student_val == opt_val
            ):
                msg_text = problem.get("messages", {}).get(
                    opt_type, "Niepoprawna odpowiedź, spróbuj ponownie."
                )
                return {
                    "lock_answer": True,
                    "feedback_type": "warning",
                    "feedback_msg": msg_text,
                    "trap_id": opt_type,
                }

    msg_text = problem.get("messages", {}).get(
        "w1", "Niepoprawna odpowiedź, spróbuj ponownie."
    )
    return {
        "lock_answer": True,
        "feedback_type": "warning",
        "feedback_msg": msg_text,
        "trap_id": "w1",
    }

import importlib
import logging
import uuid
from pathlib import Path
from typing import TypedDict

from backend.core.utils import check_text_answer, parse_to_fraction
from backend.curriculum_loader import (
    MicroTopicDict,
    get_curriculum,
    get_macro_yaml,
    get_macro_topics_ordered,
    set_function_registry,
)
from backend.models import CurriculumResponse, CurriculumTopic
import backend.config as config

BASE_DIR = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)

# --- THE AUTOLOADER ---
FUNCTION_REGISTRY: dict[str, object] = {}
macro_path = Path(__file__).parent / "macro_topics"
for file_path in macro_path.rglob("*.py"):
    if file_path.name.startswith("__"):
        continue
    module_path = ".".join(
        file_path.relative_to(Path(__file__).parent.parent).with_suffix("").parts
    )
    module = importlib.import_module(module_path)

    for k, v in module.__dict__.items():
        if callable(v) and not k.startswith("_") and (
            k.startswith("frac_") or k.startswith("dec_")
        ):
            FUNCTION_REGISTRY[k] = v

set_function_registry(FUNCTION_REGISTRY)


class TopicMeta(TypedDict):
    name: str
    max_level: int
    text_mode_disabled: bool


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


def build_topic_map(
    curriculum: dict[str, list[MicroTopicDict]], macro_topic: str
) -> dict[int, TopicMeta]:
    topic_map: dict[int, TopicMeta] = {}
    for topic in curriculum.get(macro_topic, []):
        order = topic["micro_topic_order"]
        topic_map[int(order)] = {
            "name": topic["name"],
            "max_level": int(topic["max_level"]),
            "text_mode_disabled": topic.get("text_mode_disabled", False),
        }
    return topic_map


def get_micro_topic_name(
    curriculum: dict[str, list[MicroTopicDict]],
    macro_topic: str,
    micro_topic_order: int,
) -> str | None:
    for topic in curriculum.get(macro_topic, []):
        if topic["micro_topic_order"] == micro_topic_order:
            return topic["name"]
    return None


def get_problem_from_db(macro_topic, micro_topic, level) -> dict | None:
    data = get_macro_yaml(macro_topic)
    if not data:
        return {"error": f"Missing database file for: {macro_topic}"}

    topic_entry = next(
        (t for t in data.get("micro_topics", []) if t["name"] == micro_topic),
        None,
    )
    if topic_entry is None:
        return None

    level_entry = next(
        (lvl for lvl in topic_entry.get("levels", []) if lvl["level"] == int(level)),
        None,
    )
    if level_entry is None or not level_entry.get("published", True):
        return None

    func_name = level_entry["function"]
    problem_func = FUNCTION_REGISTRY.get(func_name)

    if not problem_func:
        return {"error": f"Function {func_name} not found"}

    try:
        problem_dict = generate_problem(problem_func)
        problem_dict["level"] = int(level)
        problem_dict["level_name"] = level_entry["name"]
        problem_dict["problem_id"] = str(uuid.uuid4())
    except RuntimeError as e:
        return {"error": str(e)}

    DEFAULT_MSG = config.DEFAULT_WRONG_MESSAGE
    traps = level_entry.get("traps", {})
    problem_dict["messages"] = {
        "t1": traps.get("t1") or DEFAULT_MSG,
        "t2": traps.get("t2") or DEFAULT_MSG,
        "t3": traps.get("t3") or DEFAULT_MSG,
    }
    problem_dict["level_display"] = f"{level_entry['name']} (Lvl {level})"
    problem_dict["keyboard_type"] = data.get("keyboard_type", "default")
    return problem_dict


def generate_problem(topic_function):
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

    # --- 1. MULTIPLE CHOICE MODE ---
    if not is_text_mode and "options" in problem and len(problem["options"]) > 0:
        is_correct = problem["options_map"].get(user_input) == "correct"
        if is_correct:
            return {"is_correct": True, "lock_answer": True}
        else:
            msg_key = problem["options_map"].get(user_input, "w1")
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
    for opt_str, opt_type in problem["options_map"].items():
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

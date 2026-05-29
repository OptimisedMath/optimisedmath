import functools
import yaml
import importlib
from pathlib import Path
from backend.core.utils import check_text_answer, parse_to_fraction
import backend.config as config
import uuid

BASE_DIR = Path(__file__).resolve().parent

# --- THE AUTOLOADER ---
FUNCTION_REGISTRY = {}
macro_path = Path(__file__).parent / "macro_topics"
for file_path in macro_path.rglob("*.py"):
    if file_path.name.startswith("__"):
        continue
    module_path = ".".join(file_path.relative_to(Path(__file__).parent.parent).parts)[:-3]
    module = importlib.import_module(module_path)

    # Safely store functions in a specific dictionary instead of global memory
    for k, v in module.__dict__.items():
        if callable(v) and not k.startswith("_"):
            FUNCTION_REGISTRY[k] = v


@functools.lru_cache(maxsize=None)
def get_curriculum() -> dict:
    curriculum_dict = {}
    data_dir = BASE_DIR / "data"

    if not data_dir.exists():
        return curriculum_dict

    # 1. Dynamically scan for every YAML file in the data folder
    for file_path in sorted(data_dir.glob("*.yaml")):
        try:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            macro_topic = data["macro_topic"]
            topics = []

            # 2. Build topic list from YAML, filtering unpublished levels
            for topic in data.get("topics", []):
                published_levels = [
                    lvl["level"]
                    for lvl in topic.get("levels", [])
                    if lvl.get("published", True)
                ]
                if published_levels:
                    topics.append({
                        "Topic_Order": topic["order"],
                        "Micro_Topic": topic["name"],
                        "Level": max(published_levels),
                        "text_mode_disabled": topic.get("text_mode_disabled", False),
                    })

            if topics:
                curriculum_dict[macro_topic] = topics

        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")

    return curriculum_dict


@functools.lru_cache(maxsize=None)
def load_topic_yaml(macro_topic: str) -> dict:
    """Helper function to load and cache the YAML once per topic."""
    safe_filename = macro_topic.replace(" ", "_") + ".yaml"
    yaml_path = BASE_DIR / "data" / safe_filename
    if not yaml_path.exists():
        return {}
    with open(yaml_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_problem_from_db(macro_topic, micro_topic, level) -> dict | None:
    data = load_topic_yaml(macro_topic)
    if not data:
        return {"error": f"Missing database file for: {macro_topic}"}

    # Find the matching micro-topic
    topic_entry = next(
        (t for t in data.get("topics", []) if t["name"] == micro_topic),
        None,
    )
    if topic_entry is None:
        return None

    # Find the matching level
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

    # Pull trap messages, falling back to default for missing keys
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
        except Exception as e:
            # Log individual generation errors but continue retrying
            continue
    
    raise RuntimeError(
        f"Failed to generate valid problem for {topic_function.__name__} after {config.MAX_RETRIES_GENERATE} attempts"
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
            # The option clicked resolves to 't1', 't2', 'w1', etc.
            msg_key = problem["options_map"].get(user_input, "w1")
            msg_text = problem.get("messages", {}).get(
                msg_key, "Niepoprawna odpowiedź, spróbuj ponownie."
            )

            return {
                "lock_answer": True,
                "feedback_type": "warning",
                "feedback_msg": msg_text,
                "trap_id": msg_key  # <-- INJECTED FOR TELEMETRY
            }

    # --- 2. TEXT INPUT MODE ---
    policy = problem.get("grading_policy", "standard")

    # Exact Match Check
    if check_text_answer(problem["correct"], user_input):
        return {"is_correct": True, "lock_answer": True}

    # Mathematical Evaluation
    student_val = parse_to_fraction(str(user_input))
    correct_val = parse_to_fraction(problem["correct"])

    if student_val is None:
        # SHIFT: Gibberish math format is a soft error (Blue)
        return {
            "lock_answer": False,
            "feedback_type": "info",
            "feedback_msg": "Niepoprawny zapis matematyczny.",
            "trap_id": "syntax_error"  # <-- INJECTED FOR TELEMETRY
        }

    if student_val == correct_val:
        format_warning = check_format_mismatch(user_input, problem["correct"])
        if format_warning:
            # SHIFT: Wrong notation system is a soft error (Blue)
            return {
                "lock_answer": False,
                "feedback_type": "info",
                "feedback_msg": format_warning,
                "trap_id": "format_mismatch"  # <-- INJECTED FOR TELEMETRY
            }

        if policy == "exact_match_only":
            return {
                "lock_answer": True,
                "feedback_type": "warning",
                "feedback_msg": "W tym zadaniu wartość matematyczna to nie wszystko. Musisz zapisać ułamek w dokładnie takiej postaci, o jaką prosi polecenie!",
                "trap_id": "exact_match_violation"  # <-- INJECTED FOR TELEMETRY
            }
        elif policy == "equivalent_accepted":
            return {"is_correct": True, "lock_answer": True}
        else:
            # SHIFT: Unsimplified fraction is a soft error (Blue)
            return {
                "lock_answer": False,
                "feedback_type": "info",
                "feedback_msg": "Wynik jest poprawny matematycznie, ale zapisz go w najprostszej postaci (bez zbędnych zer lub skrócony)!",
                "trap_id": "unsimplified"  # <-- INJECTED FOR TELEMETRY
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
                # Hard Trap (Yellow)
                return {
                    "lock_answer": True,
                    "feedback_type": "warning",
                    "feedback_msg": msg_text,
                    "trap_id": opt_type  # <-- INJECTED FOR TELEMETRY
                }

    # If math is entirely wrong and misses all explicit traps
    msg_text = problem.get("messages", {}).get(
        "w1", "Niepoprawna odpowiedź, spróbuj ponownie."
    )
    # Hard Error (Yellow)
    return {
        "lock_answer": True, 
        "feedback_type": "warning", 
        "feedback_msg": msg_text,
        "trap_id": "w1"  # <-- INJECTED FOR TELEMETRY
    }

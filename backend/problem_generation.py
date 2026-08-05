"""Problem generation, generator registry, and curriculum API helpers."""

import hashlib
import importlib
import logging
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

import backend.config as config
from backend.core.utils import ProblemDict
from backend.curriculum_loader import (
    get_chapter_keyboard_type,
    get_chapters,
    get_curriculum,
    get_level_config,
    get_topic_name,
    get_topics_by_id,
    set_function_registry,
)
from backend.models import ChapterSummary, CurriculumResponse, TopicSummary

BASE_DIR = Path(__file__).resolve().parent.parent
CHAPTERS_DIR = BASE_DIR / "backend" / "chapters"
logger = logging.getLogger(__name__)

GeneratorFunc = Callable[[], ProblemDict | None]


class GeneratorRegistryError(Exception):
    """Raised when generator registration fails."""


class ProblemGenerationError(Exception):
    """Raised when a level problem cannot be generated."""


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


def _load_generator_registry(chapters_dir: Path) -> dict[str, GeneratorFunc]:
    registry: dict[str, GeneratorFunc] = {}
    sources: dict[str, str] = {}

    for file_path in chapters_dir.rglob("topic_*.py"):
        module_path = ".".join(
            file_path.relative_to(BASE_DIR).with_suffix("").parts
        )
        module = importlib.import_module(module_path)

        for name, value in module.__dict__.items():
            if _is_generator(name, value, module.__name__):
                _register_generator(registry, sources, name, value, module_path)

    return registry


FUNCTION_REGISTRY: dict[str, GeneratorFunc] = _load_generator_registry(CHAPTERS_DIR)
set_function_registry(FUNCTION_REGISTRY)


def get_curriculum_response() -> CurriculumResponse:
    """Return curriculum metadata formatted for the API."""
    curriculum = get_curriculum()
    chapters: list[ChapterSummary] = []
    for chapter in get_chapters():
        topic_list = curriculum.get(chapter.chapter_id, [])
        chapters.append(
            ChapterSummary(
                chapter_id=chapter.chapter_id,
                name=chapter.name,
                topics=[TopicSummary(**topic_entry) for topic_entry in topic_list],
            )
        )
    return CurriculumResponse(chapters=chapters)


def generate_problem(generator_func: GeneratorFunc) -> ProblemDict:
    """Generate a problem using the given generator function, with retry logic.

    Raises:
        RuntimeError: If problem generation fails after max retries
    """
    for attempt in range(config.MAX_RETRIES_GENERATE):
        try:
            problem = generator_func()
            if problem is not None:
                return problem
        except Exception:
            logger.exception(
                "Problem generator %s failed on attempt %s",
                generator_func.__name__,
                attempt + 1,
            )
            continue

    raise RuntimeError(
        f"Failed to generate valid problem for {generator_func.__name__} "
        f"after {config.MAX_RETRIES_GENERATE} attempts"
    )


def generate_level_problem(chapter_id: int, topic_id: int, level: int) -> ProblemDict:
    """Generate a problem for a curriculum level."""
    topics_by_id = get_topics_by_id(chapter_id)
    if not topics_by_id:
        raise ProblemGenerationError(f"Missing curriculum for chapter id: {chapter_id}")

    if topic_id not in topics_by_id:
        topic_name = get_topic_name(chapter_id, topic_id)
        raise ProblemGenerationError(
            f"Topic id {topic_id} ({topic_name!r}) not found in chapter {chapter_id}"
        )

    level_config = get_level_config(chapter_id, topic_id, level)
    if level_config is None or not level_config.published:
        topic_name = get_topic_name(chapter_id, topic_id) or str(topic_id)
        raise ProblemGenerationError(
            f"Level {level} is not available for topic '{topic_name}' in chapter {chapter_id}"
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
    problem_dict["messages"] = yaml_messages | gen_messages
    problem_dict["level_display"] = f"{level_config.name} (Lvl {level})"
    problem_dict["keyboard_type"] = get_chapter_keyboard_type(chapter_id)
    return problem_dict


def problem_fingerprint(problem: ProblemDict) -> str:
    """Stable identity for a generated problem instance (excludes problem_id)."""
    options = "|".join(sorted(str(opt) for opt in problem.get("options", [])))
    payload = f"{problem.get('question', '')}|{problem.get('correct', '')}|{options}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

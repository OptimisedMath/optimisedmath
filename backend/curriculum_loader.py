"""Load, validate, and cache curriculum YAML files."""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, TypedDict

import yaml

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

REQUIRED_ROOT_KEYS = ("macro_topic", "micro_topics", "keyboard_type")


class CurriculumLoadError(Exception):
    """Raised when curriculum YAML fails validation."""


class MicroTopicDict(TypedDict):
    """Navigation metadata for one micro-topic derived from curriculum YAML."""

    micro_topic_order: int
    name: str
    max_level: int
    text_mode_disabled: bool


@dataclass(frozen=True)
class MacroTopicBundle:
    """Cached parsed YAML plus derived navigation metadata for one macro topic."""

    macro_topic: str
    order: int
    keyboard_type: str
    raw: dict[str, Any]
    micro_topics_meta: list[MicroTopicDict]


_function_registry: dict[str, Callable[..., Any]] | None = None


def set_function_registry(registry: dict[str, Callable[..., Any]]) -> None:
    """Provide generator registry for function-name validation."""
    global _function_registry
    _function_registry = registry
    _load_curriculum_store.cache_clear()


def _expected_filename(macro_topic: str) -> str:
    return macro_topic.replace(" ", "_") + ".yaml"


def _derive_micro_topics_meta(data: dict[str, Any]) -> list[MicroTopicDict]:
    micro_topics: list[MicroTopicDict] = []
    for topic in data.get("micro_topics", []):
        published_levels = [
            lvl["level"]
            for lvl in topic.get("levels", [])
            if lvl.get("published", True)
        ]
        if published_levels:
            micro_topics.append(
                {
                    "micro_topic_order": int(topic["order"]),
                    "name": topic["name"],
                    "max_level": max(published_levels),
                    "text_mode_disabled": topic.get("text_mode_disabled", False),
                }
            )
    return micro_topics


def _validate_micro_topics(
    file_name: str, macro_topic: str, data: dict[str, Any]
) -> None:
    micro_topics = data.get("micro_topics")
    if not isinstance(micro_topics, list):
        raise CurriculumLoadError(
            f"{file_name}: 'micro_topics' must be a list for macro '{macro_topic}'"
        )

    seen_orders: set[int] = set()
    for topic in micro_topics:
        if not isinstance(topic, dict):
            raise CurriculumLoadError(
                f"{file_name}: each micro topic must be a mapping in '{macro_topic}'"
            )

        for key in ("order", "name", "levels"):
            if key not in topic:
                raise CurriculumLoadError(
                    f"{file_name}: micro topic in '{macro_topic}' missing '{key}'"
                )

        order = int(topic["order"])
        if order in seen_orders:
            raise CurriculumLoadError(
                f"{file_name}: duplicate micro topic order {order} in '{macro_topic}'"
            )
        seen_orders.add(order)

        levels = topic.get("levels", [])
        if not isinstance(levels, list) or not levels:
            raise CurriculumLoadError(
                f"{file_name}: micro topic '{topic['name']}' in '{macro_topic}' "
                "must have at least one level"
            )

        has_published = False
        for level in levels:
            if not isinstance(level, dict):
                raise CurriculumLoadError(
                    f"{file_name}: invalid level entry in '{macro_topic}'"
                )
            for key in ("level", "name", "function"):
                if key not in level:
                    raise CurriculumLoadError(
                        f"{file_name}: level in '{macro_topic}' / '{topic['name']}' "
                        f"missing '{key}'"
                    )
            if level.get("published", True):
                has_published = True
                func_name = level["function"]
                if _function_registry is not None and func_name not in _function_registry:
                    raise CurriculumLoadError(
                        f"{file_name}: function '{func_name}' not found in "
                        f"FUNCTION_REGISTRY ({macro_topic} / {topic['name']})"
                    )

        if not has_published:
            logger.warning(
                "%s: micro topic '%s' in '%s' has no published levels",
                file_name,
                topic["name"],
                macro_topic,
            )


def _validate_file(file_path: Path, data: Any) -> MacroTopicBundle:
    file_name = file_path.name

    if not isinstance(data, dict):
        raise CurriculumLoadError(f"{file_name}: root must be a mapping")

    for key in REQUIRED_ROOT_KEYS:
        if key not in data:
            raise CurriculumLoadError(f"{file_name}: missing required key '{key}'")

    macro_topic = data["macro_topic"]
    if not isinstance(macro_topic, str) or not macro_topic.strip():
        raise CurriculumLoadError(f"{file_name}: 'macro_topic' must be a non-empty string")

    expected_name = _expected_filename(macro_topic)
    if file_name != expected_name:
        raise CurriculumLoadError(
            f"{file_name}: filename must be '{expected_name}' for macro '{macro_topic}'"
        )

    order = int(data.get("order", 999))
    if data.get("order") is None:
        logger.warning(
            "%s: missing macro 'order'; defaulting to %s for '%s'",
            file_name,
            order,
            macro_topic,
        )

    _validate_micro_topics(file_name, macro_topic, data)
    micro_topics_meta = _derive_micro_topics_meta(data)

    if not micro_topics_meta:
        raise CurriculumLoadError(
            f"{file_name}: macro '{macro_topic}' has no published micro topics"
        )

    return MacroTopicBundle(
        macro_topic=macro_topic,
        order=order,
        keyboard_type=str(data.get("keyboard_type", "default")),
        raw=data,
        micro_topics_meta=micro_topics_meta,
    )


@functools.lru_cache(maxsize=1)
def _load_curriculum_store() -> tuple[MacroTopicBundle, ...]:
    if not DATA_DIR.exists():
        return ()

    bundles: list[MacroTopicBundle] = []
    seen_macros: set[str] = set()

    for file_path in sorted(DATA_DIR.glob("*.yaml")):
        try:
            with open(file_path, encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except Exception as exc:
            raise CurriculumLoadError(
                f"Failed to parse {file_path.name}: {exc}"
            ) from exc

        bundle = _validate_file(file_path, data)
        if bundle.macro_topic in seen_macros:
            raise CurriculumLoadError(
                f"Duplicate macro_topic '{bundle.macro_topic}' in {file_path.name}"
            )
        seen_macros.add(bundle.macro_topic)
        bundles.append(bundle)

    bundles.sort(key=lambda b: (b.order, b.macro_topic))
    return tuple(bundles)


def get_macro_topics_ordered() -> list[str]:
    """Return macro topic names sorted by YAML `order`."""
    return [bundle.macro_topic for bundle in _load_curriculum_store()]


def get_curriculum() -> dict[str, list[MicroTopicDict]]:
    """Return navigation metadata keyed by macro topic (insertion order = macro order)."""
    return {
        bundle.macro_topic: list(bundle.micro_topics_meta)
        for bundle in _load_curriculum_store()
    }


def get_macro_yaml(macro_topic: str) -> dict[str, Any]:
    """Return full parsed YAML for one macro topic."""
    for bundle in _load_curriculum_store():
        if bundle.macro_topic == macro_topic:
            return bundle.raw
    return {}

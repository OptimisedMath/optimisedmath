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

# --- Exceptions & types ---


class CurriculumLoadError(Exception):
    """Raised when curriculum YAML fails validation."""


class TopicDict(TypedDict):
    """Navigation metadata for one topic derived from curriculum YAML."""

    topic_id: int
    name: str
    max_level: int
    radio_only: bool


class TopicMeta(TypedDict):
    """Navigation metadata for one topic within a chapter."""

    name: str
    max_level: int
    radio_only: bool


@dataclass(frozen=True)
class LevelConfig:
    """Precomputed level metadata for problem generation."""

    level: int
    name: str
    function: str
    traps: dict[str, str]
    published: bool


@dataclass(frozen=True)
class ChapterBundle:
    """Cached parsed YAML plus derived navigation metadata for one chapter."""

    chapter_id: int
    chapter_name: str
    keyboard_type: str
    raw: dict[str, Any]
    topics_meta: tuple[TopicDict, ...]
    topics_by_id: dict[int, TopicMeta]
    level_configs: dict[tuple[int, int], LevelConfig]
    topic_name_by_id: dict[int, str]


@dataclass(frozen=True)
class ChapterSummary:
    """Chapter id and display name for API responses."""

    chapter_id: int
    name: str


@dataclass(frozen=True)
class CurriculumStore:
    """Fully loaded curriculum with precomputed lookup indexes."""

    bundles: tuple[ChapterBundle, ...]
    curriculum: dict[int, list[TopicDict]]
    chapters: list[ChapterSummary]
    bundles_by_chapter_id: dict[int, ChapterBundle]
    chapter_id_by_name: dict[str, int]
    chapter_name_by_id: dict[int, str]


_EMPTY_STORE = CurriculumStore(
    bundles=(),
    curriculum={},
    chapters=[],
    bundles_by_chapter_id={},
    chapter_id_by_name={},
    chapter_name_by_id={},
)

# --- Generator registry hook ---

_function_registry: dict[str, Callable[..., Any]] | None = None


def set_function_registry(registry: dict[str, Callable[..., Any]]) -> None:
    """Provide generator registry for function-name validation."""
    global _function_registry
    _function_registry = registry
    _load_store.cache_clear()


# --- Derivation helpers ---


def _expected_filename(chapter_name: str) -> str:
    return chapter_name.replace(" ", "_") + ".yaml"


def _derive_topics_meta(data: dict[str, Any]) -> list[TopicDict]:
    chapter_topics: list[TopicDict] = []
    for topic_entry in data.get("topics", []):
        published_levels = [
            lvl["level"]
            for lvl in topic_entry.get("levels", [])
            if lvl.get("published", True)
        ]
        if published_levels:
            chapter_topics.append(
                {
                    "topic_id": int(topic_entry["id"]),
                    "name": topic_entry["name"],
                    "max_level": max(published_levels),
                    "radio_only": topic_entry.get(
                        "radio_only", topic_entry.get("text_mode_disabled", False)
                    ),
                }
            )
    return chapter_topics


def _derive_topics_by_id(topics_meta: list[TopicDict]) -> dict[int, TopicMeta]:
    return {
        int(topic_entry["topic_id"]): {
            "name": topic_entry["name"],
            "max_level": int(topic_entry["max_level"]),
            "radio_only": bool(topic_entry.get("radio_only", False)),
        }
        for topic_entry in topics_meta
    }


def _derive_level_configs(data: dict[str, Any]) -> dict[tuple[int, int], LevelConfig]:
    configs: dict[tuple[int, int], LevelConfig] = {}
    for topic_entry in data.get("topics", []):
        topic_id = int(topic_entry["id"])
        for level_entry in topic_entry.get("levels", []):
            configs[(topic_id, int(level_entry["level"]))] = LevelConfig(
                level=int(level_entry["level"]),
                name=str(level_entry["name"]),
                function=str(level_entry["function"]),
                traps={
                    str(key): str(value)
                    for key, value in level_entry.get("traps", {}).items()
                },
                published=bool(level_entry.get("published", True)),
            )
    return configs


def _derive_topic_name_by_id(topics_meta: list[TopicDict]) -> dict[int, str]:
    return {int(topic_entry["topic_id"]): topic_entry["name"] for topic_entry in topics_meta}


# --- Validation ---


def _validate_topics(
    file_name: str, chapter_name: str, data: dict[str, Any]
) -> None:
    chapter_topics = data.get("topics")
    if not isinstance(chapter_topics, list):
        raise CurriculumLoadError(
            f"{file_name}: 'topics' must be a list for chapter '{chapter_name}'"
        )

    seen_topic_ids: set[int] = set()
    for topic_entry in chapter_topics:
        if not isinstance(topic_entry, dict):
            raise CurriculumLoadError(
                f"{file_name}: each topic must be a mapping in '{chapter_name}'"
            )

        for key in ("id", "name", "levels"):
            if key not in topic_entry:
                raise CurriculumLoadError(
                    f"{file_name}: topic in '{chapter_name}' missing '{key}'"
                )

        topic_id = int(topic_entry["id"])
        if topic_id in seen_topic_ids:
            raise CurriculumLoadError(
                f"{file_name}: duplicate topic id {topic_id} in '{chapter_name}'"
            )
        seen_topic_ids.add(topic_id)

        levels = topic_entry.get("levels", [])
        if not isinstance(levels, list) or not levels:
            raise CurriculumLoadError(
                f"{file_name}: topic '{topic_entry['name']}' in '{chapter_name}' "
                "must have at least one level"
            )

        has_published = False
        for level_entry in levels:
            if not isinstance(level_entry, dict):
                raise CurriculumLoadError(
                    f"{file_name}: invalid level entry in '{chapter_name}'"
                )
            for key in ("level", "name", "function"):
                if key not in level_entry:
                    raise CurriculumLoadError(
                        f"{file_name}: level in '{chapter_name}' / '{topic_entry['name']}' "
                        f"missing '{key}'"
                    )
            if level_entry.get("published", True):
                has_published = True
                func_name = level_entry["function"]
                if _function_registry is not None and func_name not in _function_registry:
                    raise CurriculumLoadError(
                        f"{file_name}: function '{func_name}' not found in "
                        f"FUNCTION_REGISTRY ({chapter_name} / {topic_entry['name']})"
                    )

        if not has_published:
            logger.warning(
                "%s: topic '%s' in '%s' has no published levels",
                file_name,
                topic_entry["name"],
                chapter_name,
            )


def _validate_file(file_path: Path, data: Any) -> ChapterBundle:
    file_name = file_path.name

    if not isinstance(data, dict):
        raise CurriculumLoadError(f"{file_name}: root must be a mapping")

    for key in ("chapter", "topics", "keyboard_type"):
        if key not in data:
            raise CurriculumLoadError(f"{file_name}: missing required key '{key}'")

    chapter_name = data["chapter"]
    if not isinstance(chapter_name, str) or not chapter_name.strip():
        raise CurriculumLoadError(f"{file_name}: 'chapter' must be a non-empty string")

    expected_name = _expected_filename(chapter_name)
    if file_name != expected_name:
        raise CurriculumLoadError(
            f"{file_name}: filename must be '{expected_name}' for chapter '{chapter_name}'"
        )

    chapter_id = int(data.get("id", 999))
    if data.get("id") is None:
        logger.warning(
            "%s: missing chapter 'id'; defaulting to %s for '%s'",
            file_name,
            chapter_id,
            chapter_name,
        )

    _validate_topics(file_name, chapter_name, data)
    topics_meta = _derive_topics_meta(data)

    if not topics_meta:
        raise CurriculumLoadError(
            f"{file_name}: chapter '{chapter_name}' has no published topics"
        )

    return ChapterBundle(
        chapter_id=chapter_id,
        chapter_name=chapter_name,
        keyboard_type=str(data.get("keyboard_type", "default")),
        raw=data,
        topics_meta=tuple(topics_meta),
        topics_by_id=_derive_topics_by_id(topics_meta),
        level_configs=_derive_level_configs(data),
        topic_name_by_id=_derive_topic_name_by_id(topics_meta),
    )


# --- Loading & cache ---


def _build_store(bundles: list[ChapterBundle]) -> CurriculumStore:
    bundles.sort(key=lambda bundle: (bundle.chapter_id, bundle.chapter_name))
    bundle_tuple = tuple(bundles)
    chapter_id_by_name = {bundle.chapter_name: bundle.chapter_id for bundle in bundle_tuple}
    chapter_name_by_id = {bundle.chapter_id: bundle.chapter_name for bundle in bundle_tuple}
    return CurriculumStore(
        bundles=bundle_tuple,
        curriculum={
            bundle.chapter_id: list(bundle.topics_meta) for bundle in bundle_tuple
        },
        chapters=[
            ChapterSummary(chapter_id=bundle.chapter_id, name=bundle.chapter_name)
            for bundle in bundle_tuple
        ],
        bundles_by_chapter_id={bundle.chapter_id: bundle for bundle in bundle_tuple},
        chapter_id_by_name=chapter_id_by_name,
        chapter_name_by_id=chapter_name_by_id,
    )


@functools.lru_cache(maxsize=32)
def _load_store(data_dir: Path) -> CurriculumStore:
    if not data_dir.exists():
        return _EMPTY_STORE

    bundles: list[ChapterBundle] = []
    seen_chapter_ids: set[int] = set()
    seen_chapter_names: set[str] = set()

    for file_path in sorted(data_dir.glob("*.yaml")):
        try:
            with open(file_path, encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except Exception as exc:
            raise CurriculumLoadError(
                f"Failed to parse {file_path.name}: {exc}"
            ) from exc

        bundle = _validate_file(file_path, data)
        if bundle.chapter_id in seen_chapter_ids:
            raise CurriculumLoadError(
                f"Duplicate chapter id '{bundle.chapter_id}' in {file_path.name}"
            )
        if bundle.chapter_name in seen_chapter_names:
            raise CurriculumLoadError(
                f"Duplicate chapter name '{bundle.chapter_name}' in {file_path.name}"
            )
        seen_chapter_ids.add(bundle.chapter_id)
        seen_chapter_names.add(bundle.chapter_name)
        bundles.append(bundle)

    return _build_store(bundles)


# --- Public API ---


def load_curriculum_store() -> CurriculumStore:
    """Return the fully loaded, cached curriculum store for `DATA_DIR`.

    The lru_cache is keyed on the data directory, so tests that monkeypatch
    `DATA_DIR` to a fresh `tmp_path` get an uncached load without needing to
    clear the cache themselves.
    """
    return _load_store(DATA_DIR)

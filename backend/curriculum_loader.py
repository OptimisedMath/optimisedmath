"""Load, validate, and cache curriculum YAML files."""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, TypedDict

import yaml

from backend.core.utils import FILLER_SLUG, declared_trap_slugs

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# The Misconception catalogue lives beside the Chapter files but is not a Chapter.
MISCONCEPTIONS_FILE = "misconceptions.yaml"

# --- Exceptions & types ---


class CurriculumLoadError(Exception):
    """Raised when curriculum YAML fails validation."""


class TopicDict(TypedDict):
    """Navigation metadata for one topic derived from curriculum YAML."""

    topic_id: int
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
    trap_misconceptions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ChapterBundle:
    """Cached parsed YAML plus derived navigation metadata for one chapter."""

    chapter_id: int
    chapter_name: str
    keyboard_type: str
    raw: dict[str, Any]
    topics_meta: tuple[TopicDict, ...]
    topics_by_id: dict[int, TopicDict]
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
    chapters: list[ChapterSummary]
    bundles_by_chapter_id: dict[int, ChapterBundle]
    chapter_name_by_id: dict[int, str]
    misconception_names: dict[str, str] = field(default_factory=dict)


_EMPTY_STORE = CurriculumStore(
    bundles=(),
    chapters=[],
    bundles_by_chapter_id={},
    chapter_name_by_id={},
)

# --- Generator registry hook ---

_function_registry: dict[str, Callable[..., Any]] | None = None


def set_function_registry(registry: dict[str, Callable[..., Any]]) -> None:
    """Provide generator registry for function-name validation."""
    global _function_registry
    _function_registry = registry
    _load_store.cache_clear()


# --- Deconstruction walkthrough registry hook ---

_deconstruction_registry: dict[str, Callable[..., Any]] | None = None


def set_deconstruction_registry(registry: dict[str, Callable[..., Any]]) -> None:
    """Provide walkthrough registry for `deconstruction:` name validation."""
    global _deconstruction_registry
    _deconstruction_registry = registry
    _load_store.cache_clear()


# --- Derivation helpers ---


_ASCII_TRANSLITERATION = str.maketrans(
    "ąĄćĆęĘłŁńŃóÓśŚźŹżŻ",
    "aAcCeElLnNoOsSzZzZ",
)


def _expected_filename(chapter_name: str) -> str:
    # Data filenames must stay pure ASCII: they round-trip through zip files
    # shared across platforms, and Windows' built-in "Extract All" ignores a
    # zip's UTF-8 filename flag and always decodes names with the legacy OEM
    # codepage, corrupting any non-ASCII characters on extraction.
    ascii_name = chapter_name.translate(_ASCII_TRANSLITERATION)
    return ascii_name.replace(" ", "_") + ".yaml"


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


def _derive_topics_by_id(topics_meta: list[TopicDict]) -> dict[int, TopicDict]:
    return {int(topic_entry["topic_id"]): topic_entry for topic_entry in topics_meta}


def _derive_trap_prose(level_entry: dict[str, Any]) -> dict[str, str]:
    """Per-Level trap sentences, keyed by trap slug. The Student-facing first hit."""
    return {
        str(key): str(entry["explanation"])
        for key, entry in level_entry.get("traps", {}).items()
    }


def _derive_trap_misconceptions(level_entry: dict[str, Any]) -> dict[str, str]:
    """Trap slug -> Misconception id. Absent for a Trap swept to `Wrong`."""
    return {
        str(key): str(entry["misconception"])
        for key, entry in level_entry.get("traps", {}).items()
        if entry.get("misconception")
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
                traps=_derive_trap_prose(level_entry),
                trap_misconceptions=_derive_trap_misconceptions(level_entry),
                published=bool(level_entry.get("published", True)),
            )
    return configs


def _derive_topic_name_by_id(topics_meta: list[TopicDict]) -> dict[int, str]:
    return {
        int(topic_entry["topic_id"]): topic_entry["name"] for topic_entry in topics_meta
    }


# --- Validation ---


def _validate_trap_slugs(
    file_name: str, chapter_name: str, topic_name: str, level_entry: dict[str, Any]
) -> None:
    """Assert a Level's Trap slugs match exactly what its generator declares.

    Both directions matter: a YAML slug the generator cannot emit is prose no Student
    will ever see, and an emitted slug with no YAML entry falls back to the generic
    wrong-answer message, silently losing the targeted feedback a Trap exists for.
    """
    if _function_registry is None:
        return

    generator = _function_registry.get(str(level_entry["function"]))
    if generator is None:
        return

    declared = declared_trap_slugs(generator)
    authored = {str(slug) for slug in level_entry.get("traps", {})}
    where = f"{file_name}: {chapter_name} / {topic_name} / level {level_entry['level']}"

    if FILLER_SLUG in authored:
        raise CurriculumLoadError(
            f"{where}: '{FILLER_SLUG}' is not a Trap slug — a Filler carries no prose"
        )

    unauthored = sorted(declared - authored)
    if unauthored:
        raise CurriculumLoadError(
            f"{where}: generator emits Trap slugs with no 'traps' entry: "
            f"{', '.join(unauthored)}"
        )

    unreachable = sorted(authored - declared)
    if unreachable:
        raise CurriculumLoadError(
            f"{where}: 'traps' entries no template can emit: {', '.join(unreachable)}"
        )


def _validate_topics(file_name: str, chapter_name: str, data: dict[str, Any]) -> None:
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
                if (
                    _function_registry is not None
                    and func_name not in _function_registry
                ):
                    raise CurriculumLoadError(
                        f"{file_name}: function '{func_name}' not found in "
                        f"FUNCTION_REGISTRY ({chapter_name} / {topic_entry['name']})"
                    )
                _validate_trap_slugs(
                    file_name, chapter_name, topic_entry["name"], level_entry
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


def _build_store(
    bundles: list[ChapterBundle], catalogue: dict[str, Any] | None = None
) -> CurriculumStore:
    bundles.sort(key=lambda bundle: (bundle.chapter_id, bundle.chapter_name))
    bundle_tuple = tuple(bundles)
    chapter_name_by_id = {
        bundle.chapter_id: bundle.chapter_name for bundle in bundle_tuple
    }
    misconception_names = {
        slug: str(entry["name"]) for slug, entry in (catalogue or {}).items()
    }
    return CurriculumStore(
        bundles=bundle_tuple,
        chapters=[
            ChapterSummary(chapter_id=bundle.chapter_id, name=bundle.chapter_name)
            for bundle in bundle_tuple
        ],
        bundles_by_chapter_id={bundle.chapter_id: bundle for bundle in bundle_tuple},
        chapter_name_by_id=chapter_name_by_id,
        misconception_names=misconception_names,
    )


def _load_misconception_catalogue(data_dir: Path) -> dict[str, Any]:
    """Parse `misconceptions.yaml` — the global, named catalogue of wrong rules."""
    catalogue_path = data_dir / MISCONCEPTIONS_FILE
    if not catalogue_path.exists():
        return {}

    try:
        with open(catalogue_path, encoding="utf-8") as handle:
            catalogue = yaml.safe_load(handle)
    except Exception as exc:
        raise CurriculumLoadError(
            f"Failed to parse {MISCONCEPTIONS_FILE}: {exc}"
        ) from exc

    if not isinstance(catalogue, dict):
        raise CurriculumLoadError(f"{MISCONCEPTIONS_FILE}: must be a mapping")

    for entry_id, entry in catalogue.items():
        if not isinstance(entry, dict):
            raise CurriculumLoadError(
                f"{MISCONCEPTIONS_FILE}: '{entry_id}' must be a mapping"
            )
        for key in ("name", "explanation"):
            if not entry.get(key):
                raise CurriculumLoadError(
                    f"{MISCONCEPTIONS_FILE}: '{entry_id}' missing '{key}'"
                )

        deconstruction = entry.get("deconstruction")
        if (
            deconstruction is not None
            and _deconstruction_registry is not None
            and deconstruction not in _deconstruction_registry
        ):
            raise CurriculumLoadError(
                f"{MISCONCEPTIONS_FILE}: '{entry_id}' deconstruction "
                f"'{deconstruction}' not found in the walkthrough registry"
            )

    return catalogue


def _validate_misconceptions(data_dir: Path, bundles: list[ChapterBundle]) -> None:
    """Assert Chapter Traps and the catalogue agree in both directions."""
    catalogue = _load_misconception_catalogue(data_dir)
    if not catalogue:
        return

    referenced: set[str] = set()
    for bundle in bundles:
        for (topic_id, level), level_config in bundle.level_configs.items():
            for slug, misconception_id in level_config.trap_misconceptions.items():
                if misconception_id not in catalogue:
                    raise CurriculumLoadError(
                        f"{bundle.chapter_name} topic {topic_id} level {level} "
                        f"trap '{slug}': unknown misconception '{misconception_id}'"
                    )
                referenced.add(misconception_id)

    orphans = sorted(set(catalogue) - referenced)
    if orphans:
        raise CurriculumLoadError(
            f"{MISCONCEPTIONS_FILE}: no Trap references {', '.join(orphans)}"
        )


@functools.lru_cache(maxsize=32)
def _load_store(data_dir: Path) -> CurriculumStore:
    if not data_dir.exists():
        return _EMPTY_STORE

    bundles: list[ChapterBundle] = []
    seen_chapter_ids: set[int] = set()
    seen_chapter_names: set[str] = set()

    for file_path in sorted(data_dir.glob("*.yaml")):
        if file_path.name == MISCONCEPTIONS_FILE:
            continue
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

    _validate_misconceptions(data_dir, bundles)
    return _build_store(bundles, _load_misconception_catalogue(data_dir))


# --- Public API ---


def load_curriculum_store() -> CurriculumStore:
    """Return the fully loaded, cached curriculum store for `DATA_DIR`.

    The lru_cache is keyed on the data directory, so tests that monkeypatch
    `DATA_DIR` to a fresh `tmp_path` get an uncached load without needing to
    clear the cache themselves.
    """
    return _load_store(DATA_DIR)

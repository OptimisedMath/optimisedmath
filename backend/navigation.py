"""Curriculum navigation rules and UI-ready navigation state for API responses."""

from __future__ import annotations

import backend.state_manager as state_manager
from backend.curriculum_loader import MicroTopicDict
from backend.models import (
    GameState,
    NavigationMicroTopicOption,
    NavigationProgress,
    NavigationView,
    SessionNavigateRequest,
)

# --- Private helpers ---


def _get_topics(curriculum: dict[str, list[MicroTopicDict]], macro: str) -> list[MicroTopicDict]:
    return curriculum.get(macro, [])


def _find_topic(topics: list[MicroTopicDict], micro_topic_order: int) -> MicroTopicDict | None:
    for topic in topics:
        if int(topic["micro_topic_order"]) == micro_topic_order:
            return topic
    return None


def _first_topic_order(topics: list[MicroTopicDict]) -> int:
    if topics:
        return int(topics[0]["micro_topic_order"])
    return 1


def _get_unlocked(state: GameState, macro: str, topics: list[MicroTopicDict]) -> tuple[int, int]:
    progress = state.macro_progress.get(macro)
    first_order = _first_topic_order(topics)
    unlocked_order = progress.unlocked_micro_topic_order if progress else first_order
    unlocked_level = progress.unlocked_level if progress else 1
    return unlocked_order, unlocked_level


def _clamp_level(level: int | None, topic: MicroTopicDict | None) -> int:
    """Return level capped to the micro-topic's max_level (defensive for stale saves)."""
    effective = level if level is not None else 1
    max_level = int(topic["max_level"]) if topic else 1
    return min(effective, max_level)


def clamp_selected_level(
    state: GameState, curriculum: dict[str, list[MicroTopicDict]]
) -> None:
    """Clamp session selected_level to the current micro-topic's max_level."""
    macro = state.selected_macro
    if not macro:
        return
    topics = _get_topics(curriculum, macro)
    if not topics:
        return
    first_topic = topics[0]
    micro_order = state.selected_micro_topic_order or _first_topic_order(topics)
    topic = _find_topic(topics, micro_order) or first_topic
    state.selected_level = _clamp_level(state.selected_level, topic)

# --- Dropdown builders ---


def get_topic_options(
    topics: list[MicroTopicDict], unlocked_order: int, admin_mode: bool
) -> list[MicroTopicDict]:
    """Return micro-topics available in dropdowns, filtered by unlock progress."""
    if admin_mode:
        available = topics
    else:
        available = [t for t in topics if int(t["micro_topic_order"]) <= unlocked_order]
    if available:
        return available
    return topics[:1]


def get_level_limit(
    selected_topic: MicroTopicDict | None,
    unlocked_order: int,
    unlocked_level: int,
    admin_mode: bool,
) -> int:
    """Return the highest selectable level for the current unlock state."""
    if not selected_topic:
        return 1
    order = int(selected_topic["micro_topic_order"])
    max_level = int(selected_topic["max_level"])
    if admin_mode or order < unlocked_order:
        return max_level
    return min(unlocked_level, max_level)


def get_level_options(level_limit: int) -> list[int]:
    return list(range(1, max(level_limit, 1) + 1))

# --- Navigation resolution ---


def resolve_macro_change(
    state: GameState, curriculum: dict[str, list[MicroTopicDict]], next_macro: str
) -> tuple[str, int, int]:
    """Pick default micro-topic and level when switching macro topic."""
    next_topics = _get_topics(curriculum, next_macro)
    next_macro_progress = state.macro_progress.get(next_macro)
    next_micro_order = (
        next_macro_progress.unlocked_micro_topic_order
        if next_macro_progress
        else _first_topic_order(next_topics)
    )
    next_topic = _find_topic(next_topics, next_micro_order) or (next_topics[0] if next_topics else None)
    next_level = _clamp_level(
        next_macro_progress.unlocked_level if next_macro_progress else 1,
        next_topic,
    )
    return next_macro, next_micro_order, next_level


def resolve_topic_change(
    state: GameState,
    curriculum: dict[str, list[MicroTopicDict]],
    macro: str,
    next_micro_order: int,
) -> tuple[int, int]:
    """Pick default level when switching micro-topic within a macro."""
    topics = _get_topics(curriculum, macro)
    unlocked_order, unlocked_level = _get_unlocked(state, macro, topics)
    next_topic = _find_topic(topics, next_micro_order)
    if next_micro_order < unlocked_order:
        next_level = 1
    else:
        next_level = _clamp_level(unlocked_level, next_topic)
    return next_micro_order, next_level


def resolve_navigate_request(
    state: GameState,
    curriculum: dict[str, list[MicroTopicDict]],
    request: SessionNavigateRequest,
) -> tuple[str, int, int]:
    """Resolve partial navigation intents into a full macro/order/level target."""
    if (
        request.selected_macro is not None
        and request.selected_macro != state.selected_macro
    ):
        return resolve_macro_change(state, curriculum, request.selected_macro)

    macro = request.selected_macro or state.selected_macro
    if not macro:
        macro_topics = list(curriculum.keys())
        macro = macro_topics[0] if macro_topics else ""

    if request.selected_micro_topic_order is not None:
        micro_order, level = resolve_topic_change(
            state, curriculum, macro, int(request.selected_micro_topic_order)
        )
        if request.selected_level is not None:
            level = int(request.selected_level)
        return macro, micro_order, level

    if request.selected_level is not None:
        micro_order = state.selected_micro_topic_order or state_manager.StateManager._get_first_micro_topic_order(
            curriculum, macro
        )
        return macro, int(micro_order), int(request.selected_level)

    micro_order = state.selected_micro_topic_order or state_manager.StateManager._get_first_micro_topic_order(
        curriculum, macro
    )
    return macro, int(micro_order), int(state.selected_level)

# --- API view builder ---


def build_navigation_view(
    state: GameState, curriculum: dict[str, list[MicroTopicDict]]
) -> NavigationView:
    """Build dropdown options, progress counts, and level limits for the frontend."""
    macro_topics = list(curriculum.keys())
    selected_macro = state.selected_macro or (macro_topics[0] if macro_topics else "")
    topics = _get_topics(curriculum, selected_macro)
    first_topic = topics[0] if topics else None
    first_order = _first_topic_order(topics)

    selected_micro_order = state.selected_micro_topic_order or first_order
    selected_topic = _find_topic(topics, selected_micro_order) or first_topic
    selected_level = _clamp_level(state.selected_level, selected_topic)

    unlocked_order, unlocked_level = _get_unlocked(state, selected_macro, topics)
    admin_mode = state.admin_mode

    available_topics = get_topic_options(topics, unlocked_order, admin_mode)
    available_micro = [
        NavigationMicroTopicOption(
            micro_topic_order=int(t["micro_topic_order"]),
            name=str(t["name"]),
        )
        for t in available_topics
    ]

    level_limit = get_level_limit(selected_topic, unlocked_order, unlocked_level, admin_mode)
    available_levels = get_level_options(level_limit)

    has_next = (
        selected_macro in state.macro_progress
        and state.selected_micro_topic_order is not None
        and state.macro_progress[selected_macro].unlocked_micro_topic_order
        > (state.selected_micro_topic_order or 0)
    )

    text_mode_disabled = bool(selected_topic and selected_topic.get("text_mode_disabled"))

    macro_progress: NavigationProgress | None = None
    if selected_macro and topics:
        completed = sum(
            1 for t in topics if int(t["micro_topic_order"]) < unlocked_order
        )
        total = len(topics)
        macro_progress = NavigationProgress(
            completed=completed,
            total=total,
            percentage=(completed / total * 100) if total > 0 else 0.0,
        )

    micro_progress: NavigationProgress | None = None
    if selected_topic:
        max_level = int(selected_topic["max_level"])
        completed_levels = selected_level - 1
        micro_progress = NavigationProgress(
            completed=completed_levels,
            total=max_level,
            percentage=(completed_levels / max_level * 100) if max_level > 0 else 0.0,
        )

    return NavigationView(
        macro_topics=macro_topics,
        current_topic_name=str(selected_topic["name"]) if selected_topic else None,
        available_micro_topics=available_micro,
        available_levels=available_levels,
        has_next_unlocked_topic=has_next,
        text_mode_disabled=text_mode_disabled,
        macro_progress=macro_progress,
        micro_progress=micro_progress,
    )

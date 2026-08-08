"""Read-only navigation view builder for API responses — never mutates session state."""

from __future__ import annotations

from backend.curriculum_loader import TopicDict, get_chapters
from backend.models import (
    SessionState,
    NavigationChapterOption,
    NavigationProgress,
    NavigationTopicOption,
    NavigationView,
)
from backend.navigation_resolution import (
    clamp_level,
    find_topic_by_id,
    get_level_options,
    topics_for_chapter,
)
from backend.play_mode import PlayMode
from backend.unlock import (
    accessible_topics,
    first_topic_id,
    level_limit,
)


def build_navigation_view(
    state: SessionState,
    curriculum: dict[int, list[TopicDict]],
    play_mode: PlayMode,
) -> NavigationView:
    """Build dropdown options, progress counts, and level limits for the frontend."""
    chapter_summaries = get_chapters()
    available_chapters = [
        NavigationChapterOption(chapter_id=chapter.chapter_id, name=chapter.name)
        for chapter in chapter_summaries
    ]

    selected_chapter_id = state.selected_chapter_id or (
        chapter_summaries[0].chapter_id if chapter_summaries else 0
    )
    chapter_topics = topics_for_chapter(curriculum, selected_chapter_id)
    first_topic_entry = chapter_topics[0] if chapter_topics else None
    default_topic_id = first_topic_id(chapter_topics)

    selected_topic_id = state.selected_topic_id or default_topic_id
    active_topic_entry = (
        find_topic_by_id(chapter_topics, selected_topic_id) or first_topic_entry
    )
    selected_level = clamp_level(state.selected_level, active_topic_entry)

    admin_mode = play_mode.is_admin
    frontier = play_mode.effective_frontier(
        chapter_topics,
        state.chapter_frontiers.get(selected_chapter_id),
    )

    available_topic_entries = accessible_topics(chapter_topics, frontier)
    available_topics_view = [
        NavigationTopicOption(
            topic_id=int(topic_entry["topic_id"]),
            name=str(topic_entry["name"]),
        )
        for topic_entry in available_topic_entries
    ]

    level_limit_value = 1
    if active_topic_entry:
        level_limit_value = level_limit(
            int(active_topic_entry["topic_id"]),
            int(active_topic_entry["max_level"]),
            frontier,
        )
    available_levels = get_level_options(level_limit_value)

    if admin_mode:
        has_next = False
    else:
        has_next = (
            selected_chapter_id in state.chapter_frontiers
            and state.selected_topic_id is not None
            and state.chapter_frontiers[selected_chapter_id].frontier_topic_id
            > (state.selected_topic_id or 0)
        )

    radio_only = bool(
        active_topic_entry and active_topic_entry.get("radio_only")
    )

    chapter_completion_view: NavigationProgress | None = None
    if selected_chapter_id and chapter_topics:
        total = len(chapter_topics)
        if admin_mode:
            chapter_completion_view = NavigationProgress(
                completed=total,
                total=total,
                percentage=100.0,
            )
        else:
            completed = sum(
                1
                for topic_entry in chapter_topics
                if int(topic_entry["topic_id"]) < frontier.frontier_topic_id
            )
            chapter_completion_view = NavigationProgress(
                completed=completed,
                total=total,
                percentage=(completed / total * 100) if total > 0 else 0.0,
            )

    topic_completion_view: NavigationProgress | None = None
    if active_topic_entry:
        max_level = int(active_topic_entry["max_level"])
        if admin_mode:
            topic_completion_view = NavigationProgress(
                completed=max_level,
                total=max_level,
                percentage=100.0,
            )
        else:
            completed_levels = selected_level - 1
            topic_completion_view = NavigationProgress(
                completed=completed_levels,
                total=max_level,
                percentage=(completed_levels / max_level * 100) if max_level > 0 else 0.0,
            )

    return NavigationView(
        available_chapters=available_chapters,
        current_topic_name=str(active_topic_entry["name"]) if active_topic_entry else None,
        available_topics=available_topics_view,
        available_levels=available_levels,
        has_next_unlocked_topic=has_next,
        radio_only=radio_only,
        chapter_completion=chapter_completion_view,
        topic_completion=topic_completion_view,
    )

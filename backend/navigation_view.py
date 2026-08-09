"""Read-only navigation view builder for API responses — never mutates session state."""

from __future__ import annotations

from backend.models import (
    NavigationChapterOption,
    NavigationTopicOption,
    NavigationView,
)
from backend.navigation_snapshot import NavigationSnapshot


def build_navigation_view(snapshot: NavigationSnapshot) -> NavigationView:
    """Map a navigation snapshot to the API NavigationView DTO."""
    ctx = snapshot.current
    available_chapters = [
        NavigationChapterOption(chapter_id=chapter.chapter_id, name=chapter.name)
        for chapter in snapshot.chapters()
    ]

    available_topics_view = [
        NavigationTopicOption(
            topic_id=int(topic_entry["topic_id"]),
            name=str(topic_entry["name"]),
        )
        for topic_entry in ctx.accessible_topics
    ]

    available_levels = (
        ctx.level_options_for(
            snapshot.selected_topic_id,
            int(snapshot.active_topic["max_level"]),
        )
        if snapshot.active_topic
        else [1]
    )

    radio_only = bool(
        snapshot.active_topic and snapshot.active_topic.get("radio_only")
    )

    return NavigationView(
        available_chapters=available_chapters,
        current_topic_name=(
            str(snapshot.active_topic["name"]) if snapshot.active_topic else None
        ),
        available_topics=available_topics_view,
        available_levels=available_levels,
        has_next_unlocked_topic=ctx.has_next_unlocked_topic(snapshot.selected_topic_id),
        radio_only=radio_only,
        chapter_completion=ctx.chapter_progress(),
        topic_completion=ctx.topic_progress(
            snapshot.selected_topic_id, snapshot.selected_level
        ),
    )

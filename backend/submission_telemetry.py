"""Telemetry adapter — sanitize problem state and persist submission logs."""

from __future__ import annotations

import json
import time

from backend.answer_grading import EvalResult
from backend.core import db
from backend.core.utils import ProblemDict
from backend.curriculum_loader import TopicMeta, get_chapter_name_by_id
from backend.models import SessionState

_TELEMETRY_STRIP_KEYS = frozenset(
    {
        "image_html",
        "messages",
        "options",
        "options_map",
        "level",
        "level_name",
        "level_display",
        "problem_id",
    }
)


def sanitize_problem_for_telemetry(problem: ProblemDict) -> str:
    """Return JSON-safe problem state with internal/UI fields removed."""
    clean = {k: v for k, v in problem.items() if k not in _TELEMETRY_STRIP_KEYS}
    return json.dumps(clean)


def log_submission_telemetry(
    state: SessionState,
    problem: ProblemDict,
    user_input: str,
    is_input_mode: bool,
    eval_result: EvalResult,
    topics_by_id: dict[int, TopicMeta],
) -> None:
    """Persist one submission attempt with sanitized problem state."""
    username = state.username
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id
    if username is None or chapter_id is None or topic_id is None:
        raise RuntimeError("Session missing required context for telemetry")

    time_spent = None
    if state.problem_start_time is not None:
        time_spent = int(time.time() - state.problem_start_time)

    chapter_name = get_chapter_name_by_id(chapter_id) or str(chapter_id)
    topic_name = topics_by_id[topic_id]["name"]

    db.log_telemetry(
        session_id=state.session_id,
        username=username,
        chapter_name=chapter_name,
        topic_name=topic_name,
        level_number=state.selected_level,
        is_input_mode=is_input_mode,
        is_correct=eval_result.get("is_correct", False),
        user_input=user_input,
        trap_id=eval_result.get("trap_id"),
        time_spent_seconds=time_spent,
        equation_state=sanitize_problem_for_telemetry(problem),
    )

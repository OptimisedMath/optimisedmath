"""Own the Submission cycle choreography end-to-end.

One Submission cycle is the Problem lifecycle within a Session: served →
Submission → Feedback → Next problem (see ``CONTEXT.md``). This module
consolidates orchestration currently spread across ``session.begin_problem``,
and (formerly) ``session_state.reset_submission_cycle`` / ``session_state.navigate_to``.

Responsibilities:

- **Cycle reset** — clear streak, feedback, and problem fields when Navigation
  or Next problem starts a fresh cycle.
- **Begin problem** — apply state mutations for a newly generated problem and
  persist.
- **Post-Topic-completion Navigation** — after Topic completion, land the
  Session on the next unlocked Topic at level 1 when Next problem unlocks one.
- **Chapter-end fallback** — when Topic completion leaves no next unlocked
  Topic, return the already-completed Problem without regenerating.

Call from ``session.py`` use-case functions; do not import ``session`` from
here. ``submission.py`` remains the owner of one graded Submission (grade →
telemetry → progression → persist).
"""

import time

import backend.config as config
import backend.navigation as navigation
from backend.core.utils import ProblemDict
from backend.curriculum import Curriculum
from backend.models import SessionNavigateRequest, SessionState
from backend.play_mode import PlayMode, resolve_play_mode
from backend.problem_generation import (
    generate_level_problem,
    problem_fingerprint,
)
import backend.session_state as session_state


class ProblemServeError(Exception):
    """Problem serving failed when no candidate could be selected."""


class NoActiveProblemError(Exception):
    """Next problem requested at chapter end with no active problem on the Session."""


class TopicNotFoundError(Exception):
    """Selected topic is missing from the curriculum."""


def _navigate_after_topic_completion(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode | None = None,
) -> bool:
    """Navigate to the next Topic after Topic completion when Next problem unlocks one.

    Routes the target through the consolidated navigation resolver
    (``navigation.resolve_navigation_target``) — the same validate-and-resolve
    path toolbar Navigation uses — so Reachable/Locked determination cannot
    diverge between manual Navigation and post-completion auto-navigation.

    Returns True when Navigation moved the Session to the Frontier topic at level 1.
    """
    chapter_id = state.selected_chapter_id
    if chapter_id is None:
        return False

    mode = play_mode if play_mode is not None else resolve_play_mode(state.username)
    snapshot = navigation.build_navigation_snapshot(state, curriculum, mode)
    ctx = snapshot.chapter_context(chapter_id)
    if not ctx.has_next_unlocked_topic(state.selected_topic_id):
        return False

    next_topic_id = ctx.effective_frontier.frontier_topic_id
    request = SessionNavigateRequest(
        session_id=state.session_id,
        selected_chapter_id=chapter_id,
        selected_topic_id=next_topic_id,
        selected_level=1,
    )
    try:
        target_chapter_id, target_topic_id, target_level = (
            navigation.resolve_navigation_target(state, curriculum, request, snapshot)
        )
    except navigation.NavigationResolutionError:
        return False

    navigate_to(
        state,
        chapter_id=target_chapter_id,
        topic_id=target_topic_id,
        level=target_level,
        curriculum=curriculum,
        play_mode=mode,
    )
    return True


def reset_submission_cycle(
    state: SessionState, curriculum: Curriculum | None = None
) -> None:
    """Clear the current problem state when navigating or loading the next problem."""
    session_state._clear_submission_cycle_fields(state, curriculum)


def navigate_to(
    state: SessionState,
    chapter_id: int | None = None,
    topic_id: int | None = None,
    level: int | None = None,
    curriculum: Curriculum | None = None,
    play_mode: PlayMode | None = None,
) -> None:
    """Navigate to a different chapter/topic/level, resetting submission cycle and syncing."""
    if chapter_id is not None:
        state.selected_chapter_id = chapter_id
    if topic_id is not None:
        state.selected_topic_id = topic_id
    if level is not None:
        state.selected_level = level
    reset_submission_cycle(state, curriculum)
    session_state.sync_to_db(state, play_mode)


def begin_problem(
    state: SessionState,
    problem: ProblemDict,
    curriculum: Curriculum,
    *,
    recent_fingerprints: list[str] | None = None,
    play_mode: PlayMode | None = None,
) -> None:
    """Apply state mutations for a newly generated problem and persist."""
    state.current_input_mode = session_state.resolve_input_mode(state, curriculum)
    if recent_fingerprints is not None:
        state.recent_problem_fingerprints = recent_fingerprints[
            -config.MAX_RETRIES_DUPLICATE_CHECK :
        ]
    state.problem_answered = False
    state.feedback_type = None
    state.feedback_msg = ""
    state.level_completed = False
    state.problem_start_time = time.time()
    state.current_problem = problem
    session_state.sync_to_db(state, play_mode)


def serve_next_problem(
    state: SessionState,
    curriculum: Curriculum,
    chapter_id: int,
    topic_id: int,
    play_mode: PlayMode | None = None,
) -> ProblemDict:
    """Generate the next problem at the selection, dedupe recent instances, and begin it."""
    level = state.selected_level
    recent_fingerprints = list(state.recent_problem_fingerprints)
    problem: ProblemDict | None = None

    for _ in range(config.MAX_RETRIES_DUPLICATE_CHECK):
        candidate = generate_level_problem(curriculum, chapter_id, topic_id, level)
        fingerprint = problem_fingerprint(candidate)
        if fingerprint not in recent_fingerprints:
            problem = candidate
            recent_fingerprints.append(fingerprint)
            break
        problem = candidate

    if problem is None:
        raise ProblemServeError(
            f"Could not generate problem for "
            f"chapter {chapter_id}/topic {topic_id}/level {level}"
        )

    begin_problem(
        state,
        problem,
        curriculum,
        recent_fingerprints=recent_fingerprints,
        play_mode=play_mode,
    )
    return problem


def resolve_next_problem(
    state: SessionState,
    curriculum: Curriculum,
    chapter_id: int,
    topic_id: int,
    play_mode: PlayMode | None = None,
) -> ProblemDict:
    """Serve the next problem, handling post-Topic-completion Navigation and chapter-end fallback.

    Raises:
        NoActiveProblemError: At chapter end with no active problem, or missing selection
            after post-Topic Navigation.
        TopicNotFoundError: Selected topic is missing from the curriculum.
    """
    if state.problem_answered and state.topic_completed:
        if not _navigate_after_topic_completion(state, curriculum, play_mode):
            problem = state.current_problem
            if problem is None:
                raise NoActiveProblemError("No active problem in this session")
            return problem
        next_chapter_id = state.selected_chapter_id
        next_topic_id = state.selected_topic_id
        if next_chapter_id is None or next_topic_id is None:
            raise NoActiveProblemError("Session has no chapter/topic selected")
        chapter_id = next_chapter_id
        topic_id = next_topic_id

    if curriculum.topic(chapter_id, topic_id) is None:
        raise TopicNotFoundError(f"Topic id {topic_id} not found in curriculum")

    return serve_next_problem(
        state,
        curriculum,
        chapter_id,
        topic_id,
        play_mode=play_mode,
    )

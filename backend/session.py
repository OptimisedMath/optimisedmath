"""Session use-cases — gameplay route logic behind the HTTP seam."""

from __future__ import annotations

import time
from typing import Any

import backend.config as config
import backend.navigation as navigation
import backend.session_state as session_state
import backend.submission as submission
import backend.submission_cycle as submission_cycle
from backend.curriculum import Curriculum, resolve_curriculum
from backend.play_mode import PlayMode, resolve_play_mode
from backend.core import db
from backend.core.utils import ProblemDict, clean_latex, clean_mobile_input
from backend.problem_generation import ProblemGenerationError
from backend.progression import streak_meter_for
from backend.models import (
    AutoSolveRequest,
    SessionResponse,
    SessionState,
    ProblemResponse,
    ProblemSubmissionRequest,
    SessionNavigateRequest,
    SessionResetRequest,
    SessionStartRequest,
    SubmissionResponse,
)

# --- Session storage (in-memory cache; SQLite fallback on miss) ---

ACTIVE_SESSIONS: dict[str, SessionState] = {}


# --- Domain errors (mapped to HTTP by main.py) ---


class SessionError(Exception):
    """Base error for session use-case failures."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class SessionNotFoundError(SessionError):
    def __init__(self, detail: str = "Session not found") -> None:
        super().__init__(detail, status_code=404)


class ForbiddenError(SessionError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=403)


class ConflictError(SessionError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=409)


class InternalError(SessionError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=500)


# --- Session lookup ---


def get_session(session_id: str) -> SessionState:
    """Retrieve a session from memory, falling back to SQLite if not found."""
    if session_id in ACTIVE_SESSIONS:
        return ACTIVE_SESSIONS[session_id]
    stored = db.load_session(session_id)
    if stored:
        ACTIVE_SESSIONS[session_id] = stored
        return stored
    raise SessionNotFoundError()


# --- Response building ---


def _is_safe_svg_fragment(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered.startswith("<svg") or not lowered.endswith("</svg>"):
        return False
    blocked_tokens = ["<script", "javascript:", " onload=", " onclick=", " onerror="]
    return not any(token in lowered for token in blocked_tokens)


def public_problem(
    problem: ProblemDict, state: SessionState, play_mode: PlayMode
) -> dict[str, Any]:
    """Return only fields needed by the visual layer."""
    public_keys = {
        "problem_id",
        "question",
        "image_html",
        "level",
        "level_name",
        "level_display",
        "keyboard_type",
    }
    public = {key: problem.get(key) for key in public_keys if key in problem}
    image_html = public.get("image_html")
    if image_html and not _is_safe_svg_fragment(str(image_html)):
        public["image_html"] = None
    public["answer_options"] = list(problem.get("options", []))
    public["input_mode"] = state.current_input_mode
    if state.problem_answered:
        public["correct_answer"] = problem.get("correct")
    elif play_mode.reveals_correct_answer:
        correct = problem.get("correct")
        if correct is not None:
            if state.current_input_mode == "input":
                public["correct_answer"] = clean_latex(correct)
            else:
                public["correct_answer"] = correct
    return public


def respond(
    state: SessionState,
    curriculum: Curriculum,
    play_mode: PlayMode | None = None,
) -> SessionResponse:
    """Build the client SessionResponse by selecting fields from persisted state."""
    mode = play_mode if play_mode is not None else resolve_play_mode(state.username)
    current_problem = (
        public_problem(state.current_problem, state, mode)
        if state.current_problem
        else None
    )
    can_submit = bool(current_problem and not state.problem_answered)
    can_next_problem = bool(state.problem_answered)
    snapshot = navigation.build_navigation_snapshot(state, curriculum, mode)
    navigation_view = navigation.build_navigation_view(snapshot)
    return SessionResponse.from_state(
        state,
        current_problem=current_problem,
        can_submit=can_submit,
        can_next_problem=can_next_problem,
        streak_meter=streak_meter_for(state),
        admin_mode=mode.is_admin,
        navigation=navigation_view,
    )


# --- Session use-cases ---


def _resolve_navigation_target_or_raise(
    state: SessionState,
    request: SessionNavigateRequest,
    snapshot: navigation.NavigationSnapshot,
) -> tuple[int, int, int]:
    """Resolve a navigation intent, mapping resolver errors to session-layer errors."""
    try:
        return navigation.resolve_navigation_target(state, request, snapshot)
    except navigation.NavigationLockedError as exc:
        raise ForbiddenError(str(exc)) from exc
    except navigation.NavigationResolutionError as exc:
        raise SessionError(str(exc)) from exc


def start_session(request: SessionStartRequest) -> SessionResponse:
    """Create a session, load user progress, and return SessionResponse with navigation."""
    play_mode = resolve_play_mode(request.username)
    curriculum = resolve_curriculum()

    if not curriculum.chapter_ids():
        raise InternalError("No curriculum data available")

    state = SessionState()
    session_state.init_defaults(state, curriculum)
    session_state.load_profile(state, request.username, curriculum)
    navigation.clamp_selected_level(state, curriculum)

    if (
        request.selected_chapter_id is not None
        and request.selected_chapter_id != state.selected_chapter_id
    ):
        snapshot = navigation.build_navigation_snapshot(
            state, curriculum, play_mode
        )
        override_request = SessionNavigateRequest(
            session_id=state.session_id,
            selected_chapter_id=request.selected_chapter_id,
        )
        chapter_id, topic_id, level = _resolve_navigation_target_or_raise(
            state, override_request, snapshot
        )
        submission_cycle.navigate_to(
            state,
            chapter_id=chapter_id,
            topic_id=topic_id,
            level=level,
            curriculum=curriculum,
            play_mode=play_mode,
        )

    ACTIVE_SESSIONS[state.session_id] = state
    session_state.sync_to_db(
        state, session_state.build_db_write_plan(state, play_mode)
    )
    state.problem_start_time = time.time()

    return respond(state, curriculum, play_mode)


def navigate_session(request: SessionNavigateRequest) -> SessionResponse:
    """Change chapter, topic, or level with unlock validation."""
    state = get_session(request.session_id)
    play_mode = resolve_play_mode(state.username)
    curriculum = resolve_curriculum()
    snapshot = navigation.build_navigation_snapshot(
        state, curriculum, play_mode
    )

    chapter_id, topic_id, selected_level = _resolve_navigation_target_or_raise(
        state, request, snapshot
    )

    submission_cycle.navigate_to(
        state,
        chapter_id=chapter_id,
        topic_id=topic_id,
        level=selected_level,
        curriculum=curriculum,
        play_mode=play_mode,
    )

    return respond(state, curriculum, play_mode)


def reset_session(request: SessionResetRequest) -> SessionResponse:
    """Hard-reset session progress and return a fresh SessionResponse."""
    state = get_session(request.session_id)
    play_mode = resolve_play_mode(state.username)
    curriculum = resolve_curriculum()
    session_state.hard_reset(state, curriculum, play_mode)
    return respond(state, curriculum, play_mode)


def next_problem(session_id: str) -> ProblemResponse:
    """Generate the next problem, dedupe recent instances, and update input mode."""
    state = get_session(session_id)
    play_mode = resolve_play_mode(state.username)
    curriculum = resolve_curriculum()
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id

    if chapter_id is None or topic_id is None:
        raise SessionError("Session has no chapter/topic selected")

    if not curriculum.has_chapter(chapter_id):
        raise SessionError(
            f"Chapter id {chapter_id} not found in curriculum"
        )

    try:
        problem = submission_cycle.resolve_next_problem(
            state,
            curriculum,
            chapter_id,
            topic_id,
            play_mode=play_mode,
        )
    except submission_cycle.NoActiveProblemError as exc:
        raise SessionError(str(exc)) from exc
    except submission_cycle.TopicNotFoundError as exc:
        raise SessionError(str(exc)) from exc
    except (ProblemGenerationError, submission_cycle.ProblemServeError) as exc:
        raise InternalError(str(exc)) from exc

    return ProblemResponse(
        problem=public_problem(problem, state, play_mode),
        state=respond(state, curriculum, play_mode),
    )


def _submit_active_problem(
    session_id: str,
    *,
    problem_id: str | None,
    user_input: str,
    is_input_mode: bool,
    require_admin: bool = False,
) -> SubmissionResponse:
    """Shared submission path — grade, apply outcome, and return updated state."""
    state = get_session(session_id)
    play_mode = resolve_play_mode(state.username)

    if require_admin and not config.ENABLE_DEV_TOOLS and not play_mode.is_admin:
        raise SessionNotFoundError("Development tools are disabled")

    if not state.current_problem:
        raise SessionError("No active problem in this session")

    if state.problem_answered:
        raise ConflictError("Current problem has already been answered")

    problem = state.current_problem

    if problem_id and problem_id != problem.get("problem_id"):
        raise ConflictError("Submitted problem_id does not match the active problem")

    curriculum = resolve_curriculum()
    chapter_id = state.selected_chapter_id

    if chapter_id is None or not curriculum.has_chapter(chapter_id):
        raise SessionError(f"Chapter id {chapter_id} not found")

    eval_result = submission.process_submission(
        state, problem, user_input, is_input_mode, curriculum, play_mode
    )

    return SubmissionResponse(
        state=respond(state, curriculum, play_mode),
        is_correct=eval_result.get("is_correct", False),
        feedback=state.feedback_msg,
    )


def submit_problem(request: ProblemSubmissionRequest) -> SubmissionResponse:
    """Grade an answer, update streak and XP, and persist session state."""
    user_input = (
        clean_mobile_input(request.user_input)
        if request.is_input_mode
        else request.user_input
    )
    return _submit_active_problem(
        request.session_id,
        problem_id=request.problem_id,
        user_input=user_input,
        is_input_mode=request.is_input_mode,
    )


def auto_solve_problem(request: AutoSolveRequest) -> SubmissionResponse:
    """Submit the correct answer for admin or dev testing."""
    state = get_session(request.session_id)
    is_input_mode = state.current_input_mode == "input"
    problem = state.current_problem
    user_input = ""
    if problem is not None:
        user_input = (
            clean_latex(problem["correct"]) if is_input_mode else problem["correct"]
        )
    return _submit_active_problem(
        request.session_id,
        problem_id=request.problem_id,
        user_input=user_input,
        is_input_mode=is_input_mode,
        require_admin=True,
    )

"""Session use-cases — gameplay route logic behind the HTTP seam."""

from __future__ import annotations

import time
from typing import Any

import backend.config as config
import backend.navigation_resolution as navigation_resolution
import backend.navigation_view as navigation_view
import backend.session_state as session_state
import backend.unlock as unlock
from backend.core import db
from backend.core.utils import ProblemDict, clean_latex, clean_mobile_input
from backend.answer_grading import EvalResult
from backend.curriculum_loader import TopicDict, get_chapters, get_curriculum, get_topics_by_id
from backend.problem_generation import (
    ProblemGenerationError,
    generate_level_problem,
    problem_fingerprint,
)
from backend.models import (
    AutoSolveRequest,
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


def public_problem(problem: ProblemDict, state: SessionState) -> dict[str, Any]:
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
    elif config.is_admin_user(state.username):
        correct = problem.get("correct")
        if correct is not None:
            if state.current_input_mode == "input":
                public["correct_answer"] = clean_latex(correct)
            else:
                public["correct_answer"] = correct
    return public


def respond(state: SessionState, curriculum: dict[int, list[TopicDict]]) -> SessionState:
    """Build an API-safe SessionState with navigation attached."""
    response = state.for_response(public_problem)
    response.navigation = navigation_view.build_navigation_view(response, curriculum)
    return response


# --- Problem lifecycle ---


def begin_problem(
    state: SessionState,
    problem: ProblemDict,
    topics_by_id: dict[int, Any],
    *,
    recent_fingerprints: list[str] | None = None,
) -> None:
    """Apply state mutations for a newly generated problem and persist."""
    state.current_input_mode = session_state.resolve_input_mode(
        state, topics_by_id
    )
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
    session_state.sync_to_db(state)


# --- Navigation guards ---


def _validate_unlocked_navigation(
    state: SessionState,
    chapter_id: int,
    topic_id: int,
    selected_level: int,
    chapter_topics: list[TopicDict],
) -> None:
    """Reject navigation to locked topics or levels."""
    admin_mode = config.is_admin_user(state.username)
    frontier = unlock.effective_frontier(
        chapter_topics,
        state.chapter_progress.get(chapter_id),
        admin_mode=admin_mode,
    )
    if unlock.can_access(topic_id, selected_level, frontier):
        return

    if topic_id > frontier.unlocked_topic_id:
        raise ForbiddenError("Topic is locked")

    raise ForbiddenError("Level is locked")


# --- Session use-cases ---


def start_session(request: SessionStartRequest) -> SessionState:
    """Create a session, load user progress, and return SessionState with navigation."""
    curriculum = get_curriculum()
    chapter_ids = [chapter.chapter_id for chapter in get_chapters()]

    if not chapter_ids:
        raise InternalError("No curriculum data available")

    if request.selected_chapter_id is not None and request.selected_chapter_id not in curriculum:
        raise SessionError(
            f"Chapter id {request.selected_chapter_id} not found in curriculum"
        )

    state = SessionState()
    session_state.init_defaults(state, chapter_ids, curriculum)
    session_state.load_profile(
        state, request.username, chapter_ids, curriculum
    )
    navigation_resolution.clamp_selected_level(state, curriculum)

    if request.selected_chapter_id is not None:
        prev_chapter_id = state.selected_chapter_id
        state.selected_chapter_id = request.selected_chapter_id
        if request.selected_chapter_id != prev_chapter_id:
            _, topic_id, level = navigation_resolution.resolve_chapter_change(
                state, curriculum, request.selected_chapter_id
            )
            state.selected_topic_id = topic_id
            state.selected_level = level

    ACTIVE_SESSIONS[state.session_id] = state
    session_state.sync_to_db(state)
    state.problem_start_time = time.time()

    return respond(state, curriculum)


def navigate_session(request: SessionNavigateRequest) -> SessionState:
    """Change chapter, topic, or level with unlock validation."""
    state = get_session(request.session_id)
    curriculum = get_curriculum()
    chapter_id, topic_id, selected_level = navigation_resolution.resolve_navigate_request(
        state, curriculum, request
    )

    if chapter_id not in curriculum:
        raise SessionError(
            f"Chapter id {chapter_id} not found in curriculum"
        )

    chapter_topics = curriculum[chapter_id]
    if not chapter_topics:
        raise SessionError(
            f"Chapter id {chapter_id} has no available topics"
        )

    available_topic_ids = [int(topic_entry["topic_id"]) for topic_entry in chapter_topics]
    if topic_id not in available_topic_ids:
        raise SessionError(
            f"Topic id {topic_id} not found in curriculum"
        )

    topics_by_id = get_topics_by_id(chapter_id)
    selected_topic_meta = topics_by_id[topic_id]
    max_level = int(selected_topic_meta["max_level"])

    if selected_level < 1 or selected_level > max_level:
        raise SessionError(
            f"Level {selected_level} is not available for topic id {topic_id}"
        )

    _validate_unlocked_navigation(
        state, chapter_id, topic_id, selected_level, chapter_topics
    )

    session_state.navigate_to(
        state,
        chapter_id=chapter_id,
        topic_id=topic_id,
        level=selected_level,
        topics_by_id=topics_by_id,
    )

    return respond(state, curriculum)


def reset_session(request: SessionResetRequest) -> SessionState:
    """Hard-reset session progress and return a fresh SessionState."""
    state = get_session(request.session_id)
    curriculum = get_curriculum()
    chapter_ids = [chapter.chapter_id for chapter in get_chapters()]
    session_state.hard_reset(state, chapter_ids, curriculum)
    return respond(state, curriculum)


def next_problem(session_id: str) -> ProblemResponse:
    """Generate the next problem, dedupe recent instances, and update input mode."""
    state = get_session(session_id)
    curriculum = get_curriculum()
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id

    if chapter_id is None or topic_id is None:
        raise SessionError("Session has no chapter/topic selected")

    if chapter_id not in curriculum:
        raise SessionError(
            f"Chapter id {chapter_id} not found in curriculum"
        )

    topics_by_id = get_topics_by_id(chapter_id)
    if topic_id not in topics_by_id:
        raise SessionError(
            f"Topic id {topic_id} not found in curriculum"
        )

    level = state.selected_level
    recent_fingerprints = list(state.recent_problem_fingerprints)
    problem = None

    for _ in range(config.MAX_RETRIES_DUPLICATE_CHECK):
        try:
            candidate = generate_level_problem(chapter_id, topic_id, level)
        except ProblemGenerationError as exc:
            raise InternalError(str(exc)) from exc

        fingerprint = problem_fingerprint(candidate)
        if fingerprint not in recent_fingerprints:
            problem = candidate
            recent_fingerprints.append(fingerprint)
            break
        problem = candidate

    if problem is None:
        raise InternalError(
            f"Could not generate problem for "
            f"chapter {chapter_id}/topic {topic_id}/level {level}"
        )

    begin_problem(
        state, problem, topics_by_id, recent_fingerprints=recent_fingerprints
    )

    return ProblemResponse(
        problem=public_problem(problem, state),
        state=respond(state, curriculum),
    )


def submit_problem(request: ProblemSubmissionRequest) -> SubmissionResponse:
    """Grade an answer, update streak and XP, and persist session state."""
    state = get_session(request.session_id)

    if not state.current_problem:
        raise SessionError("No active problem in this session")

    if state.problem_answered:
        raise ConflictError("Current problem has already been answered")

    problem = state.current_problem

    if request.problem_id and request.problem_id != problem.get("problem_id"):
        raise ConflictError("Submitted problem_id does not match the active problem")

    curriculum = get_curriculum()
    chapter_id = state.selected_chapter_id

    if chapter_id is None or chapter_id not in curriculum:
        raise SessionError(f"Chapter id {chapter_id} not found")

    topics_by_id = get_topics_by_id(chapter_id)
    user_input = (
        clean_mobile_input(request.user_input)
        if request.is_input_mode
        else request.user_input
    )

    eval_result = _process_submission(
        state, problem, user_input, request.is_input_mode, topics_by_id
    )

    return SubmissionResponse(
        state=respond(state, curriculum),
        is_correct=eval_result.get("is_correct", False),
        feedback=state.feedback_msg,
    )


def auto_solve_problem(request: AutoSolveRequest) -> SubmissionResponse:
    """Submit the correct answer for admin or dev testing."""
    state = get_session(request.session_id)

    if not config.ENABLE_DEV_TOOLS and not config.is_admin_user(state.username):
        raise SessionNotFoundError("Development tools are disabled")

    if not state.current_problem:
        raise SessionError("No active problem in this session")

    if state.problem_answered:
        raise ConflictError("Current problem has already been answered")

    problem = state.current_problem

    if request.problem_id and request.problem_id != problem.get("problem_id"):
        raise ConflictError("Submitted problem_id does not match the active problem")

    is_input_mode = state.current_input_mode == "input"
    user_input = (
        clean_latex(problem["correct"]) if is_input_mode else problem["correct"]
    )

    curriculum = get_curriculum()
    chapter_id = state.selected_chapter_id

    if chapter_id is None or chapter_id not in curriculum:
        raise SessionError(f"Chapter id {chapter_id} not found")

    topics_by_id = get_topics_by_id(chapter_id)

    eval_result = _process_submission(
        state, problem, user_input, is_input_mode, topics_by_id
    )

    return SubmissionResponse(
        state=respond(state, curriculum),
        is_correct=eval_result.get("is_correct", False),
        feedback=state.feedback_msg,
    )


def _process_submission(
    state: SessionState,
    problem: ProblemDict,
    user_input: str,
    is_input_mode: bool,
    topics_by_id: dict[int, Any],
) -> EvalResult:
    try:
        return session_state.process_submission(
            state, problem, user_input, is_input_mode, topics_by_id
        )
    except Exception as exc:
        print(f"Error in process_submission: {exc}")
        raise InternalError(f"Error processing submission: {exc}") from exc

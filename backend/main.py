"""FastAPI backend for the Optimized Math Learning app."""

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import backend.config as config
import backend.engine as engine
import backend.navigation as navigation
import backend.state_manager as state_manager
import backend.unlock as unlock
from backend.core import db
from backend.core.utils import ProblemDict, clean_latex, clean_mobile_input
from backend.curriculum_loader import TopicDict, TopicMeta, get_chapters, get_topics_by_id
from backend.models import (
    AutoSolveRequest,
    CurriculumResponse,
    GameState,
    ProblemResponse,
    ProblemSubmissionRequest,
    SessionNavigateRequest,
    SessionResetRequest,
    SessionStartRequest,
    SubmissionResponse,
)

# --- Session storage ---

ACTIVE_SESSIONS: dict[str, GameState] = {}

# --- Request helpers ---


def _get_session(session_id: str) -> GameState:
    """Retrieve a session from memory, falling back to SQLite if not found."""
    if session_id in ACTIVE_SESSIONS:
        return ACTIVE_SESSIONS[session_id]
    stored = db.load_session(session_id)
    if stored:
        ACTIVE_SESSIONS[session_id] = stored
        return stored
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
    )


def _is_safe_svg_fragment(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered.startswith("<svg") or not lowered.endswith("</svg>"):
        return False
    blocked_tokens = ["<script", "javascript:", " onload=", " onclick=", " onerror="]
    return not any(token in lowered for token in blocked_tokens)


def _public_problem(problem: ProblemDict, state: GameState) -> dict[str, Any]:
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
    return public


def _respond(state: GameState, curriculum: dict[int, list[TopicDict]]) -> GameState:
    """Build an API-safe GameState with navigation attached."""
    response = state.for_response(_public_problem)
    response.navigation = navigation.build_navigation_view(response, curriculum)
    return response


def _validate_unlocked_navigation(
    state: GameState,
    chapter_id: int,
    topic_id: int,
    selected_level: int,
    chapter_topics: list[TopicDict],
) -> None:
    """Reject navigation to locked topics or levels unless admin."""
    admin_mode = config.is_admin_user(state.username)
    frontier = unlock.get_frontier(
        state.chapter_progress.get(chapter_id), chapter_topics
    )
    if unlock.can_access(
        topic_id, selected_level, frontier, admin_mode=admin_mode
    ):
        return

    if topic_id > frontier.unlocked_topic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Topic is locked",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Level is locked",
    )


# --- App lifecycle ---


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    print("🚀 Math Learning API started")
    db.init_db()
    yield
    print("🛑 Math Learning API shutting down")


app = FastAPI(
    title="Optimized Math Learning API",
    description="Backend API for the optimized math learning application",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- System endpoints ---


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok", "service": "math-learning-api"}


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Return API metadata and documentation link."""
    return {
        "message": "Optimized Math Learning API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/curriculum", response_model=CurriculumResponse, tags=["Curriculum"])
async def curriculum_index() -> CurriculumResponse:
    """Return available chapters and their topic metadata."""
    return engine.get_curriculum_response()


# --- Session endpoints ---


@app.post("/session/start", response_model=GameState, tags=["Session"])
async def session_start(request: SessionStartRequest) -> GameState:
    """Create a session, load user progress, and return GameState with navigation."""
    curriculum = engine.get_curriculum()
    chapter_ids = [chapter.chapter_id for chapter in get_chapters()]

    if not chapter_ids:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No curriculum data available",
        )

    if request.selected_chapter_id is not None and request.selected_chapter_id not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chapter id {request.selected_chapter_id} not found in curriculum",
        )

    state = GameState()
    state_manager.StateManager.init_defaults(state, chapter_ids, curriculum)
    state_manager.StateManager.load_profile(
        state, request.username, chapter_ids, curriculum
    )
    navigation.clamp_selected_level(state, curriculum)

    if request.selected_chapter_id is not None:
        prev_chapter_id = state.selected_chapter_id
        state.selected_chapter_id = request.selected_chapter_id
        if request.selected_chapter_id != prev_chapter_id:
            _, topic_id, level = navigation.resolve_chapter_change(
                state, curriculum, request.selected_chapter_id
            )
            state.selected_topic_id = topic_id
            state.selected_level = level

    ACTIVE_SESSIONS[state.session_id] = state
    state_manager.StateManager.sync_to_db(state)
    state.problem_start_time = time.time()

    return _respond(state, curriculum)


@app.post("/session/navigate", response_model=GameState, tags=["Session"])
async def session_navigate(request: SessionNavigateRequest) -> GameState:
    """Change chapter, topic, or level with unlock validation."""
    state = _get_session(request.session_id)
    curriculum = engine.get_curriculum()
    chapter_id, topic_id, selected_level = navigation.resolve_navigate_request(
        state, curriculum, request
    )

    if chapter_id not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chapter id {chapter_id} not found in curriculum",
        )

    chapter_topics = curriculum[chapter_id]
    if not chapter_topics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chapter id {chapter_id} has no available topics",
        )

    available_topic_ids = [int(topic_entry["topic_id"]) for topic_entry in chapter_topics]
    if topic_id not in available_topic_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic id {topic_id} not found in curriculum",
        )

    topics_by_id = get_topics_by_id(chapter_id)
    selected_topic_meta = topics_by_id[topic_id]
    max_level = int(selected_topic_meta["max_level"])

    if selected_level < 1 or selected_level > max_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Level {selected_level} is not available for topic id {topic_id}"
            ),
        )

    _validate_unlocked_navigation(
        state, chapter_id, topic_id, selected_level, chapter_topics
    )

    state_manager.StateManager.navigate_to(
        state,
        chapter_id=chapter_id,
        topic_id=topic_id,
        level=selected_level,
        topics_by_id=topics_by_id,
    )

    return _respond(state, curriculum)


@app.post("/session/reset", response_model=GameState, tags=["Session"])
async def session_reset(request: SessionResetRequest) -> GameState:
    """Hard-reset session progress and return a fresh GameState."""
    state = _get_session(request.session_id)
    curriculum = engine.get_curriculum()
    chapter_ids = [chapter.chapter_id for chapter in get_chapters()]
    state_manager.StateManager.hard_reset(state, chapter_ids, curriculum)
    return _respond(state, curriculum)


# --- Problem endpoints ---


@app.get("/problem/next", response_model=ProblemResponse, tags=["Problem"])
async def problem_next(session_id: str) -> ProblemResponse:
    """Generate the next problem, dedupe recent instances, and update input mode."""
    state = _get_session(session_id)
    curriculum = engine.get_curriculum()
    chapter_id = state.selected_chapter_id
    topic_id = state.selected_topic_id

    if chapter_id is None or topic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no chapter/topic selected",
        )

    if chapter_id not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chapter id {chapter_id} not found in curriculum",
        )

    topics_by_id = get_topics_by_id(chapter_id)
    if topic_id not in topics_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic id {topic_id} not found in curriculum",
        )

    state.current_input_mode = state_manager.StateManager._resolve_input_mode(
        state, topics_by_id
    )

    level = state.selected_level
    recent_fingerprints = list(state.recent_problem_fingerprints)
    problem = None

    for _ in range(config.MAX_RETRIES_DUPLICATE_CHECK):
        try:
            candidate = engine.generate_level_problem(chapter_id, topic_id, level)
        except engine.ProblemGenerationError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

        fingerprint = engine.problem_fingerprint(candidate)
        if fingerprint not in recent_fingerprints:
            problem = candidate
            recent_fingerprints.append(fingerprint)
            break
        problem = candidate

    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Could not generate problem for "
                f"chapter {chapter_id}/topic {topic_id}/level {level}"
            ),
        )

    state.recent_problem_fingerprints = recent_fingerprints[
        -config.MAX_RETRIES_DUPLICATE_CHECK :
    ]

    state.problem_answered = False
    state.feedback_type = None
    state.feedback_msg = ""
    state.show_celebration = False
    state.problem_start_time = time.time()
    state.current_problem = problem

    state_manager.StateManager.sync_to_db(state)

    return ProblemResponse(
        problem=_public_problem(problem, state),
        state=_respond(state, curriculum),
    )


@app.post("/problem/submit", response_model=SubmissionResponse, tags=["Problem"])
async def problem_submit(request: ProblemSubmissionRequest) -> SubmissionResponse:
    """Grade an answer, update streak and XP, and persist session state."""
    state = _get_session(request.session_id)

    if not state.current_problem:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active problem in this session",
        )

    if state.problem_answered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current problem has already been answered",
        )

    problem = state.current_problem

    if request.problem_id and request.problem_id != problem.get("problem_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Submitted problem_id does not match the active problem",
        )

    curriculum = engine.get_curriculum()
    chapter_id = state.selected_chapter_id

    if chapter_id is None or chapter_id not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chapter id {chapter_id} not found",
        )

    topics_by_id = get_topics_by_id(chapter_id)
    user_input = (
        clean_mobile_input(request.user_input)
        if request.is_text_mode
        else request.user_input
    )

    try:
        eval_result = state_manager.StateManager.process_submission(
            state, problem, user_input, request.is_text_mode, topics_by_id
        )
    except Exception as e:
        print(f"Error in process_submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing submission: {str(e)}",
        )

    return SubmissionResponse(
        state=_respond(state, curriculum),
        is_correct=eval_result.get("is_correct", False),
        feedback=state.feedback_msg,
    )


@app.post("/problem/auto-solve", response_model=SubmissionResponse, tags=["Problem"])
async def problem_auto_solve(request: AutoSolveRequest) -> SubmissionResponse:
    """Submit the correct answer for admin or dev testing."""
    state = _get_session(request.session_id)

    if not config.ENABLE_DEV_TOOLS and not config.is_admin_user(state.username):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Development tools are disabled",
        )

    if not state.current_problem:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active problem in this session",
        )

    if state.problem_answered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Current problem has already been answered",
        )

    problem = state.current_problem

    if request.problem_id and request.problem_id != problem.get("problem_id"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Submitted problem_id does not match the active problem",
        )

    is_text_mode = state.current_input_mode == "text"
    user_input = (
        clean_latex(problem["correct"]) if is_text_mode else problem["correct"]
    )

    curriculum = engine.get_curriculum()
    chapter_id = state.selected_chapter_id

    if chapter_id is None or chapter_id not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chapter id {chapter_id} not found",
        )

    topics_by_id = get_topics_by_id(chapter_id)

    try:
        eval_result = state_manager.StateManager.process_submission(
            state, problem, user_input, is_text_mode, topics_by_id
        )
    except Exception as e:
        print(f"Error in auto-solve process_submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing auto-solve: {str(e)}",
        )

    return SubmissionResponse(
        state=_respond(state, curriculum),
        is_correct=eval_result.get("is_correct", False),
        feedback=state.feedback_msg,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

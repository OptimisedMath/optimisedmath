"""FastAPI backend for the Optimized Math Learning app."""

import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import backend.config as config
import backend.engine as engine
import backend.navigation as navigation
import backend.state_manager as state_manager
from backend.core import db
from backend.core.utils import clean_latex, clean_mobile_input
from backend.curriculum_loader import (
    MicroTopicDict,
    get_micro_topic_name,
    get_topic_map,
)
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

ACTIVE_SESSIONS: Dict[str, GameState] = {}

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


def _public_problem(problem: Dict[str, Any], state: GameState) -> Dict[str, Any]:
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


def _respond(state: GameState, curriculum: dict[str, list[MicroTopicDict]]) -> GameState:
    """Build an API-safe GameState with navigation attached."""
    response = state.for_response(_public_problem)
    response.navigation = navigation.build_navigation_view(response, curriculum)
    return response


def _validate_unlocked_navigation(
    state: GameState,
    macro_topic: str,
    micro_topic_order: int,
    selected_level: int,
    topic_map: dict,
) -> None:
    """Reject navigation to locked micro-topics or levels unless admin."""
    if config.is_admin_user(state.username):
        return

    progress = state.progress.get(macro_topic)
    first_order = min(topic_map) if topic_map else 1
    unlocked_order = progress.unlocked_micro_topic_order if progress else first_order
    unlocked_level = progress.unlocked_level if progress else 1

    if micro_topic_order > unlocked_order:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Topic is locked",
        )

    if micro_topic_order == unlocked_order and selected_level > unlocked_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Level is locked",
        )


# --- App lifecycle ---


@asynccontextmanager
async def lifespan(app: FastAPI):
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
async def health_check():
    """Return service health status."""
    return {"status": "ok", "service": "math-learning-api"}


@app.get("/", tags=["System"])
async def root():
    """Return API metadata and documentation link."""
    return {
        "message": "Optimized Math Learning API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/curriculum", response_model=CurriculumResponse, tags=["Curriculum"])
async def curriculum_index():
    """Return available macro topics and their micro-topic metadata."""
    return engine.get_curriculum_response()


# --- Session endpoints ---


@app.post("/session/start", response_model=GameState, tags=["Session"])
async def session_start(request: SessionStartRequest):
    """Create a session, load user progress, and return GameState with navigation."""
    curriculum = engine.get_curriculum()
    macro_topics = list(curriculum.keys())

    if not macro_topics:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No curriculum data available",
        )

    if request.selected_macro and request.selected_macro not in macro_topics:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{request.selected_macro}' not found in curriculum",
        )

    state = GameState()
    state_manager.StateManager.init_defaults(state, macro_topics, curriculum)
    state_manager.StateManager.load_profile(
        state, request.username, macro_topics, curriculum
    )

    if request.selected_macro:
        prev_macro = state.selected_macro
        state.selected_macro = request.selected_macro
        if request.selected_macro != prev_macro:
            macro_progress = state.progress.get(request.selected_macro)
            first_order = state_manager.StateManager._get_first_micro_topic_order(
                curriculum, request.selected_macro
            )
            state.selected_micro_topic_order = (
                macro_progress.unlocked_micro_topic_order
                if macro_progress
                else first_order
            )
            state.selected_level = (
                macro_progress.unlocked_level if macro_progress else 1
            )

    ACTIVE_SESSIONS[state.session_id] = state
    state_manager.StateManager.sync_to_db(state)
    state.problem_start_time = time.time()

    return _respond(state, curriculum)


@app.post("/session/navigate", response_model=GameState, tags=["Session"])
async def session_navigate(request: SessionNavigateRequest):
    """Change macro topic, micro-topic, or level with unlock validation."""
    state = _get_session(request.session_id)
    curriculum = engine.get_curriculum()
    macro_topic, micro_topic_order, selected_level = navigation.resolve_navigate_request(
        state, curriculum, request
    )

    if not macro_topic or macro_topic not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{macro_topic}' not found in curriculum",
        )

    topic_list = curriculum[macro_topic]
    if not topic_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{macro_topic}' has no available topics",
        )

    available_orders = [int(t["micro_topic_order"]) for t in topic_list]
    if micro_topic_order not in available_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Micro-topic order {micro_topic_order} not found in curriculum",
        )

    topic_map = get_topic_map(macro_topic)
    selected_topic = topic_map[micro_topic_order]
    max_level = int(selected_topic["max_level"])

    if selected_level < 1 or selected_level > max_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Level {selected_level} is not available for micro-topic "
                f"order {micro_topic_order}"
            ),
        )

    _validate_unlocked_navigation(
        state, macro_topic, micro_topic_order, selected_level, topic_map
    )

    state_manager.StateManager.navigate_to(
        state,
        macro=macro_topic,
        micro_topic_order=micro_topic_order,
        level=selected_level,
        topic_map=topic_map,
    )

    return _respond(state, curriculum)


@app.post("/session/reset", response_model=GameState, tags=["Session"])
async def session_reset(request: SessionResetRequest):
    """Hard-reset session progress and return a fresh GameState."""
    state = _get_session(request.session_id)
    curriculum = engine.get_curriculum()
    macro_topics = list(curriculum.keys())
    state_manager.StateManager.hard_reset(state, macro_topics, curriculum)
    return _respond(state, curriculum)


# --- Problem endpoints ---


@app.get("/problem/next", response_model=ProblemResponse, tags=["Problem"])
async def problem_next(session_id: str):
    """Generate the next problem, dedupe recent instances, and update input mode."""
    state = _get_session(session_id)
    curriculum = engine.get_curriculum()
    macro_topic = state.selected_macro
    micro_topic_order = state.selected_micro_topic_order

    if not macro_topic or micro_topic_order is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no macro/micro-topic selected",
        )

    if macro_topic not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{macro_topic}' not found in curriculum",
        )

    micro_topic = get_micro_topic_name(macro_topic, micro_topic_order)
    if not micro_topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Micro-topic order {micro_topic_order} not found in curriculum",
        )

    topic_map = get_topic_map(macro_topic)
    state.current_input_mode = state_manager.StateManager._resolve_input_mode(
        state, topic_map
    )

    level = state.selected_level
    recent_fingerprints = list(state.recent_problem_fingerprints)
    problem = None

    for _ in range(config.MAX_RETRIES_DUPLICATE_CHECK):
        try:
            candidate = engine.generate_level_problem(macro_topic, micro_topic, level)
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
                f"{macro_topic}/{micro_topic}/{level}"
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

    return {"problem": _public_problem(problem, state), "state": _respond(state, curriculum)}


@app.post("/problem/submit", response_model=SubmissionResponse, tags=["Problem"])
async def problem_submit(request: ProblemSubmissionRequest):
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
    macro_topic = state.selected_macro

    if macro_topic not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{macro_topic}' not found",
        )

    topic_map = get_topic_map(macro_topic)
    user_input = (
        clean_mobile_input(request.user_input)
        if request.is_text_mode
        else request.user_input
    )

    try:
        eval_result = state_manager.StateManager.process_submission(
            state, problem, user_input, request.is_text_mode, topic_map
        )
    except Exception as e:
        print(f"Error in process_submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing submission: {str(e)}",
        )

    return {
        "state": _respond(state, curriculum),
        "is_correct": eval_result.get("is_correct", False),
        "feedback": state.feedback_msg,
    }


@app.post("/problem/auto-solve", response_model=SubmissionResponse, tags=["Problem"])
async def problem_auto_solve(request: AutoSolveRequest):
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
    macro_topic = state.selected_macro

    if macro_topic not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{macro_topic}' not found",
        )

    topic_map = get_topic_map(macro_topic)

    try:
        eval_result = state_manager.StateManager.process_submission(
            state, problem, user_input, is_text_mode, topic_map
        )
    except Exception as e:
        print(f"Error in auto-solve process_submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing auto-solve: {str(e)}",
        )

    return {
        "state": _respond(state, curriculum),
        "is_correct": eval_result.get("is_correct", False),
        "feedback": state.feedback_msg,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

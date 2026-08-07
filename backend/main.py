"""FastAPI backend for the Optimized Math Learning app."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import backend.session_state as session_state
from backend.core import db
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
from backend.problem_generation import get_curriculum_response
from backend.session import (
    ACTIVE_SESSIONS,
    SessionError,
    auto_solve_problem,
    navigate_session,
    next_problem,
    public_problem as _public_problem,
    reset_session,
    start_session,
    submit_problem,
)

# Re-exported for tests that seed in-memory sessions.
__all__ = ["ACTIVE_SESSIONS", "app"]


def _map_session_error(exc: SessionError) -> HTTPException:
    """Map domain errors from the session use-case layer to HTTP responses."""
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


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
    return get_curriculum_response()


# --- Session endpoints ---


@app.post("/session/start", response_model=GameState, tags=["Session"])
async def session_start(request: SessionStartRequest) -> GameState:
    """Create a session, load user progress, and return GameState with navigation."""
    try:
        return start_session(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post("/session/navigate", response_model=GameState, tags=["Session"])
async def session_navigate(request: SessionNavigateRequest) -> GameState:
    """Change chapter, topic, or level with unlock validation."""
    try:
        return navigate_session(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post("/session/reset", response_model=GameState, tags=["Session"])
async def session_reset(request: SessionResetRequest) -> GameState:
    """Hard-reset session progress and return a fresh GameState."""
    try:
        return reset_session(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


# --- Problem endpoints ---


@app.get("/problem/next", response_model=ProblemResponse, tags=["Problem"])
async def problem_next(session_id: str) -> ProblemResponse:
    """Generate the next problem, dedupe recent instances, and update input mode."""
    try:
        return next_problem(session_id)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post("/problem/submit", response_model=SubmissionResponse, tags=["Problem"])
async def problem_submit(request: ProblemSubmissionRequest) -> SubmissionResponse:
    """Grade an answer, update streak and XP, and persist session state."""
    try:
        return submit_problem(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post("/problem/auto-solve", response_model=SubmissionResponse, tags=["Problem"])
async def problem_auto_solve(request: AutoSolveRequest) -> SubmissionResponse:
    """Submit the correct answer for admin or dev testing."""
    try:
        return auto_solve_problem(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

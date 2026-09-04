"""FastAPI backend for the Optimized Math Learning app."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import backend.session_state as session_state
from backend.core import db
from backend.models import (
    AutoSolveRequest,
    CurriculumResponse,
    DeconstructionAbandonRequest,
    DeconstructionStepResponse,
    DeconstructionSubmissionRequest,
    DeconstructionSubmissionResponse,
    SessionResponse,
    ProblemResponse,
    ProblemSubmissionRequest,
    SessionNavigateRequest,
    SessionResetRequest,
    SessionStartRequest,
    SubmissionResponse,
)
from backend.curriculum import get_curriculum_response, resolve_curriculum
from backend.session import (
    ACTIVE_SESSIONS,
    SessionError,
    abandon_deconstruction,
    auto_solve_problem,
    get_deconstruction_step,
    navigate_session,
    next_problem,
    reset_session,
    start_session,
    submit_deconstruction_step,
    submit_problem,
)

# Re-exported for tests that seed in-memory sessions.
__all__ = ["ACTIVE_SESSIONS", "app"]


def _map_session_error(exc: SessionError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


# --- App lifecycle ---


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
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
    return {"status": "ok", "service": "math-learning-api"}


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    return {
        "message": "Optimized Math Learning API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/curriculum", response_model=CurriculumResponse, tags=["Curriculum"])
async def curriculum_index() -> CurriculumResponse:
    return get_curriculum_response(resolve_curriculum())


# --- Session endpoints ---


@app.post("/session/start", response_model=SessionResponse, tags=["Session"])
async def session_start(request: SessionStartRequest) -> SessionResponse:
    try:
        return start_session(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post("/session/navigate", response_model=SessionResponse, tags=["Session"])
async def session_navigate(request: SessionNavigateRequest) -> SessionResponse:
    try:
        return navigate_session(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post("/session/reset", response_model=SessionResponse, tags=["Session"])
async def session_reset(request: SessionResetRequest) -> SessionResponse:
    try:
        return reset_session(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


# --- Problem endpoints ---


@app.get("/problem/next", response_model=ProblemResponse, tags=["Problem"])
async def problem_next(session_id: str) -> ProblemResponse:
    try:
        return next_problem(session_id)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post("/problem/submit", response_model=SubmissionResponse, tags=["Problem"])
async def problem_submit(request: ProblemSubmissionRequest) -> SubmissionResponse:
    try:
        return submit_problem(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post(
    "/problem/auto-solve",
    response_model=SubmissionResponse,
    tags=["Problem", "Dev tools"],
)
async def problem_auto_solve(request: AutoSolveRequest) -> SubmissionResponse:
    try:
        return auto_solve_problem(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


# --- Deconstruction endpoints ---


@app.get(
    "/deconstruction/next",
    response_model=DeconstructionStepResponse,
    tags=["Deconstruction"],
)
async def deconstruction_next(session_id: str) -> DeconstructionStepResponse:
    try:
        return get_deconstruction_step(session_id)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post(
    "/deconstruction/submit",
    response_model=DeconstructionSubmissionResponse,
    tags=["Deconstruction"],
)
async def deconstruction_submit(
    request: DeconstructionSubmissionRequest,
) -> DeconstructionSubmissionResponse:
    try:
        return submit_deconstruction_step(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


@app.post(
    "/deconstruction/abandon",
    response_model=SessionResponse,
    tags=["Deconstruction"],
)
async def deconstruction_abandon(
    request: DeconstructionAbandonRequest,
) -> SessionResponse:
    try:
        return abandon_deconstruction(request)
    except SessionError as exc:
        raise _map_session_error(exc) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

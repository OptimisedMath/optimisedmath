"""FastAPI backend for the Optimized Math Learning app."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Optional, Any
import uuid
import time
import config
import engine
import state_manager


# ============================================================================
# Pydantic Models
# ============================================================================

class TopicProgress(BaseModel):
    """Represents progress for a single macro topic."""
    unlocked_order: int = Field(default=1, description="The highest topic order unlocked")
    unlocked_level: int = Field(default=1, description="The highest level unlocked for the current topic")


class GameState(BaseModel):
    """Mirrors the current state structure from state_manager.py."""
    
    # Core identifiers
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique session identifier")
    username: Optional[str] = Field(default=None, description="Logged-in username")
    
    # XP and streaks
    xp: int = Field(default=0, ge=0, description="Total experience points")
    streak: int = Field(default=0, ge=0, description="Current correct answer streak")
    flawless_eligible: bool = Field(default=True, description="Whether user is eligible for flawless bonus")
    
    # Navigation and selection
    selected_macro: Optional[str] = Field(default=None, description="Currently selected macro topic")
    selected_topic_order: Optional[int] = Field(default=None, description="Currently selected topic order")
    selected_level: int = Field(default=1, ge=1, description="Currently selected difficulty level")
    
    # Problem and input state
    problem_answered: bool = Field(default=False, description="Whether current problem has been answered")
    current_input_mode: str = Field(default="radio", description="Input mode for current problem (radio/text)")
    topic_completed: bool = Field(default=False, description="Whether current topic is completed")
    
    # Feedback
    feedback_type: Optional[str] = Field(default=None, description="Type of feedback (correct/incorrect)")
    feedback_msg: str = Field(default="", description="Feedback message for user")
    show_balloons: bool = Field(default=False, description="Whether to show celebration balloons")
    
    # Progress tracking
    progress: Dict[str, TopicProgress] = Field(
        default_factory=dict,
        description="Progress dictionary mapping macro_topic -> TopicProgress"
    )
    
    # Optional current problem (not persisted)
    current_problem: Optional[Dict[str, Any]] = Field(default=None, description="Current problem being worked on")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "student123",
                "xp": 1500,
                "streak": 3,
                "flawless_eligible": True,
                "selected_macro": "ulamki zwykle",
                "selected_topic_order": 2,
                "selected_level": 2,
                "problem_answered": False,
                "current_input_mode": "radio",
                "topic_completed": False,
                "feedback_type": None,
                "feedback_msg": "",
                "show_balloons": False,
                "progress": {
                    "ulamki zwykle": {
                        "unlocked_order": 3,
                        "unlocked_level": 2
                    },
                    "ulamki dziesietne": {
                        "unlocked_order": 1,
                        "unlocked_level": 1
                    }
                }
            }
        }
    )


# ============================================================================
# Request Models for API Endpoints
# ============================================================================

class SessionStartRequest(BaseModel):
    """Request model for POST /session/start"""
    username: str = Field(description="Username to start session for")
    selected_macro: Optional[str] = Field(default=None, description="Initial macro topic to select (optional)")


class ProblemSubmissionRequest(BaseModel):
    """Request model for POST /problem/submit"""
    session_id: str = Field(description="Session ID for the submission")
    user_input: str = Field(description="User's answer to the problem")
    is_text_mode: bool = Field(default=False, description="Whether the answer was in text mode")


# ============================================================================
# Response Models
# ============================================================================

class ProblemResponse(BaseModel):
    """Response model for problem data"""
    problem: Dict[str, Any] = Field(description="The problem details")
    state: GameState = Field(description="Current game state")


class SubmissionResponse(BaseModel):
    """Response model for problem submission"""
    state: GameState = Field(description="Updated game state after submission")
    is_correct: bool = Field(description="Whether the answer was correct")
    feedback: str = Field(description="Feedback message")


# ============================================================================
# In-Memory Session Storage (for development)
# ============================================================================
# In production, this should be persisted in a database
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}


def _dict_to_gamestate(state_dict: Dict[str, Any]) -> GameState:
    """Convert a state dictionary to a GameState Pydantic model."""
    # Ensure progress items are TopicProgress objects
    progress = {}
    for macro, prog_data in state_dict.get("progress", {}).items():
        if isinstance(prog_data, dict):
            progress[macro] = TopicProgress(**prog_data)
        else:
            progress[macro] = prog_data
    
    state_dict["progress"] = progress
    return GameState(**state_dict)


def _gamestate_to_dict(game_state: GameState) -> Dict[str, Any]:
    """Convert a GameState Pydantic model to a dictionary."""
    return game_state.model_dump()


# ============================================================================
# Lifespan Context Manager
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    print("🚀 Math Learning API started")
    yield
    # Shutdown
    print("🛑 Math Learning API shutting down")


# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title="Optimized Math Learning API",
    description="Backend API for the optimized math learning application",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# CORS Middleware Configuration
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React development server
        "http://localhost:8000",      # Local testing
        "https://localhost:3000",     # HTTPS variant
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Allow all headers
)


# ============================================================================
# HEALTH CHECK & ROOT ENDPOINTS
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """Check if the API is running."""
    return {"status": "ok", "service": "math-learning-api"}


@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "message": "Optimized Math Learning API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# ============================================================================
# SESSION ENDPOINTS
# ============================================================================

@app.post("/session/start", response_model=GameState, tags=["Session"])
async def session_start(request: SessionStartRequest):
    """Initialize a new game session for a user.
    
    - Loads user profile from database or creates new one
    - Returns initialized GameState
    """
    # Get curriculum and macro topics for initialization
    curriculum = engine.get_curriculum()
    macro_topics = list(curriculum.keys())
    
    if not macro_topics:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No curriculum data available"
        )
    
    # Create or load state
    state = {}
    state_manager.StateManager.init_defaults(state, macro_topics, curriculum)
    state_manager.StateManager.load_profile(state, request.username, macro_topics, curriculum)
    
    # Override selected_macro if provided
    if request.selected_macro and request.selected_macro in macro_topics:
        state["selected_macro"] = request.selected_macro
        first_order = state_manager.StateManager._get_first_topic_order(curriculum, request.selected_macro)
        state["selected_topic_order"] = first_order
    
    # Store session in memory
    ACTIVE_SESSIONS[state["session_id"]] = state
    
    # Record problem start time for telemetry
    state["problem_start_time"] = time.time()
    
    return _dict_to_gamestate(state)


# ============================================================================
# PROBLEM ENDPOINTS
# ============================================================================

@app.get("/problem/next", response_model=ProblemResponse, tags=["Problem"])
async def problem_next(session_id: str):
    """Get the next problem for the current session.
    
    - Uses current selected_macro, selected_topic_order, and selected_level
    - Generates a new problem and returns it with current state
    """
    # Retrieve session
    if session_id not in ACTIVE_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    state = ACTIVE_SESSIONS[session_id]
    
    # Get curriculum to find the micro topic name
    curriculum = engine.get_curriculum()
    macro_topic = state.get("selected_macro")
    topic_order = state.get("selected_topic_order")
    
    if not macro_topic or not topic_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has no macro/topic selected"
        )
    
    if macro_topic not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{macro_topic}' not found in curriculum"
        )
    
    # Find the micro topic by Topic_Order
    topic_list = curriculum[macro_topic]
    micro_topic = None
    
    for topic in topic_list:
        if topic.get("Topic_Order") == topic_order:
            micro_topic = topic.get("Micro_Topic")
            break
    
    if not micro_topic:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic order {topic_order} not found in curriculum"
        )
    
    # Generate the problem
    level = state.get("selected_level", 1)
    problem = engine.get_problem_from_db(macro_topic, micro_topic, level)
    
    if not problem:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not generate problem for {macro_topic}/{micro_topic}/{level}"
        )
    
    if "error" in problem:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=problem["error"]
        )
    
    # Reset problem state and record start time
    state["problem_answered"] = False
    state["feedback_type"] = None
    state["feedback_msg"] = ""
    state["show_balloons"] = False
    state["problem_start_time"] = time.time()
    state["current_problem"] = problem
    
    return {
        "problem": problem,
        "state": _dict_to_gamestate(state)
    }


# ============================================================================
# SUBMISSION ENDPOINTS
# ============================================================================

@app.post("/problem/submit", response_model=SubmissionResponse, tags=["Problem"])
async def problem_submit(request: ProblemSubmissionRequest):
    """Submit an answer to the current problem.
    
    - Evaluates the answer using engine.evaluate_answer
    - Updates state using StateManager.process_submission
    - Handles XP, streaks, flawless bonuses, and progression
    - Returns updated GameState
    """
    # Retrieve session
    if request.session_id not in ACTIVE_SESSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    state = ACTIVE_SESSIONS[request.session_id]
    
    # Get the current problem
    if not state.get("current_problem"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active problem in this session"
        )
    
    problem = state["current_problem"]
    
    # Get curriculum for topic mapping
    curriculum = engine.get_curriculum()
    macro_topic = state.get("selected_macro")
    
    if macro_topic not in curriculum:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Macro topic '{macro_topic}' not found"
        )
    
    # Build topic_map for process_submission
    # topic_map should map Topic_Order -> {name, max_level}
    topic_list = curriculum[macro_topic]
    topic_map = {}
    for topic in topic_list:
        order = topic.get("Topic_Order")
        name = topic.get("Micro_Topic")
        max_level = topic.get("Level", 1)
        if order and name:
            topic_map[order] = {"name": name, "max_level": int(max_level)}
    
    # Process the submission
    state_manager.StateManager.process_submission(
        state,
        problem,
        request.user_input,
        request.is_text_mode,
        topic_map
    )
    
    # Evaluate to get is_correct
    eval_result = engine.evaluate_answer(request.user_input, problem, request.is_text_mode)
    is_correct = eval_result.get("is_correct", False)
    feedback = state.get("feedback_msg", "")
    
    return {
        "state": _dict_to_gamestate(state),
        "is_correct": is_correct,
        "feedback": feedback
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

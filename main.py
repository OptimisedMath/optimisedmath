"""FastAPI backend for the Optimized Math Learning app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
import uuid


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

    class Config:
        """Pydantic config for JSON serialization."""
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "student123",
                "xp": 1500,
                "streak": 3,
                "flawless_eligible": True,
                "selected_macro": "ulamki_zwykle",
                "selected_topic_order": 2,
                "selected_level": 2,
                "problem_answered": False,
                "current_input_mode": "radio",
                "topic_completed": False,
                "feedback_type": None,
                "feedback_msg": "",
                "show_balloons": False,
                "progress": {
                    "ulamki_zwykle": {
                        "unlocked_order": 3,
                        "unlocked_level": 2
                    },
                    "ulamki_dziesietne": {
                        "unlocked_order": 1,
                        "unlocked_level": 1
                    }
                }
            }
        }


# ============================================================================
# FastAPI App Initialization
# ============================================================================

app = FastAPI(
    title="Optimized Math Learning API",
    description="Backend API for the optimized math learning application",
    version="1.0.0"
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
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],              # Allow all headers
)


# ============================================================================
# Health Check Endpoint
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

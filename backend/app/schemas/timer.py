"""Timer schemas for request/response."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.game.phases import GamePhase


class TimerState(BaseModel):
    """Timer state schema."""
    
    game_id: str
    phase: GamePhase
    duration_seconds: int
    remaining_seconds: int
    end_time: datetime
    is_paused: bool = False


class TimerStartRequest(BaseModel):
    """Request to start a phase timer."""
    
    phase: GamePhase
    duration_seconds: int = Field(ge=1, description="Duration in seconds")


class TimerResponse(BaseModel):
    """Timer response schema."""
    
    game_id: str
    phase: GamePhase
    remaining_seconds: int
    end_time: datetime
    is_paused: bool


class TimerTickEvent(BaseModel):
    """WebSocket timer tick event."""
    
    event: str = "timer:tick"
    data: TimerResponse


class TimerPhaseChangeEvent(BaseModel):
    """WebSocket phase change event."""
    
    event: str = "timer:phase_change"
    data: dict

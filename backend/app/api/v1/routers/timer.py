"""Timer router for REST API endpoints."""
from fastapi import APIRouter, HTTPException
from app.schemas.timer import TimerStartRequest, TimerResponse, TimerState
from app.services.timer_service import timer_service
from app.core.logger import logger

router = APIRouter(prefix="/games/{game_id}/timer", tags=["timer"])


@router.get("/", response_model=TimerResponse)
async def get_timer_status(game_id: str):
    """Get current timer status for a game."""
    timer_state = await timer_service.get_timer_state(game_id)
    
    if not timer_state:
        raise HTTPException(status_code=404, detail="Timer not found for this game")
    
    return TimerResponse(
        game_id=timer_state.game_id,
        phase=timer_state.phase,
        remaining_seconds=timer_state.remaining_seconds,
        end_time=timer_state.end_time,
        is_paused=timer_state.is_paused,
    )


@router.post("/start", response_model=TimerResponse)
async def start_timer(game_id: str, request: TimerStartRequest):
    """Start a phase timer (host/system only)."""
    try:
        timer_state = await timer_service.start_phase_timer(
            game_id=game_id,
            phase=request.phase,
            duration_seconds=request.duration_seconds,
        )
        
        return TimerResponse(
            game_id=timer_state.game_id,
            phase=timer_state.phase,
            remaining_seconds=timer_state.remaining_seconds,
            end_time=timer_state.end_time,
            is_paused=timer_state.is_paused,
        )
    except Exception as e:
        logger.error(f"Error starting timer for game {game_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pause")
async def pause_timer(game_id: str):
    """Pause the current timer."""
    success = await timer_service.pause_timer(game_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Timer not found or already paused")
    
    return {"message": "Timer paused", "game_id": game_id}


@router.post("/resume")
async def resume_timer(game_id: str):
    """Resume the paused timer."""
    success = await timer_service.resume_timer(game_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Timer not found or not paused")
    
    return {"message": "Timer resumed", "game_id": game_id}


@router.post("/stop")
async def stop_timer(game_id: str):
    """Stop the timer completely."""
    await timer_service.stop_timer(game_id)
    return {"message": "Timer stopped", "game_id": game_id}

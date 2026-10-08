"""Timer service with background countdown task."""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.schemas.timer import TimerState, TimerResponse
from app.game.phases import GamePhase
from app.repositories.timer_repository import timer_repository
from app.core.websocket import ws_manager
from app.core.logger import logger


class TimerService:
    """Service for managing game phase timers."""
    
    def __init__(self):
        # Active timer tasks: game_id -> asyncio.Task
        self._active_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_phase_timer(
        self, 
        game_id: str, 
        phase: GamePhase, 
        duration_seconds: int
    ) -> TimerState:
        """Start a new phase timer."""
        # Cancel existing timer if any
        await self.stop_timer(game_id)
        
        # Create timer state
        end_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
        timer_state = TimerState(
            game_id=game_id,
            phase=phase,
            duration_seconds=duration_seconds,
            remaining_seconds=duration_seconds,
            end_time=end_time,
            is_paused=False,
        )
        
        # Save to repository
        await timer_repository.save_timer_state(timer_state)
        
        # Start background tick task
        task = asyncio.create_task(self._tick_loop(game_id))
        self._active_tasks[game_id] = task
        
        logger.info(f"Timer started for game {game_id}, phase {phase}, duration {duration_seconds}s")
        
        # Broadcast timer started event
        await ws_manager.broadcast_to_game(game_id, {
            "event": "timer:started",
            "data": {
                "game_id": game_id,
                "phase": phase,
                "duration_seconds": duration_seconds,
                "end_time": end_time.isoformat(),
            }
        })
        
        return timer_state
    
    async def _tick_loop(self, game_id: str):
        """Background task that ticks every second."""
        try:
            while True:
                await asyncio.sleep(1)
                
                # Get current timer state
                timer_state = await timer_repository.get_timer_state(game_id)
                if not timer_state:
                    logger.warning(f"Timer state not found for game {game_id}, stopping tick")
                    break
                
                # Skip if paused
                if timer_state.is_paused:
                    continue
                
                # Decrement remaining seconds
                timer_state.remaining_seconds -= 1
                await timer_repository.update_remaining_seconds(
                    game_id, 
                    timer_state.remaining_seconds
                )
                
                # Broadcast tick event
                await ws_manager.broadcast_to_game(game_id, {
                    "event": "timer:tick",
                    "data": {
                        "game_id": game_id,
                        "phase": timer_state.phase,
                        "remaining_seconds": timer_state.remaining_seconds,
                        "end_time": timer_state.end_time.isoformat(),
                    }
                })
                
                # Check if timer expired
                if timer_state.remaining_seconds <= 0:
                    logger.info(f"Timer expired for game {game_id}, phase {timer_state.phase}")
                    await self._handle_timer_expired(game_id, timer_state.phase)
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"Timer task cancelled for game {game_id}")
        except Exception as e:
            logger.error(f"Error in timer tick loop for game {game_id}: {e}")
    
    async def _handle_timer_expired(self, game_id: str, current_phase: GamePhase):
        """Handle timer expiration and trigger phase transition."""
        from app.game.engine import game_engine
        
        # Determine next phase
        next_phase = self._get_next_phase(current_phase)
        
        # Broadcast timer finished event
        await ws_manager.broadcast_to_game(game_id, {
            "event": "timer:finished",
            "data": {
                "game_id": game_id,
                "completed_phase": current_phase,
                "next_phase": next_phase,
            }
        })
        
        # Trigger phase transition in GameEngine
        await game_engine.transition_phase(game_id, next_phase)
        
        # Clean up timer state
        await timer_repository.delete_timer_state(game_id)
        if game_id in self._active_tasks:
            del self._active_tasks[game_id]
    
    def _get_next_phase(self, current_phase: GamePhase) -> GamePhase:
        """Determine next phase based on current phase."""
        phase_flow = {
            GamePhase.PREPARING: GamePhase.ROLE_PREPARE,
            GamePhase.ROLE_PREPARE: GamePhase.NIGHT,
            GamePhase.NIGHT: GamePhase.MORNING,
            GamePhase.MORNING: GamePhase.DISCUSSION,
            GamePhase.DISCUSSION: GamePhase.VOTING,
            GamePhase.VOTING: GamePhase.EXECUTION,
            GamePhase.EXECUTION: GamePhase.NIGHT,  # Loop back or check win condition
        }
        return phase_flow.get(current_phase, GamePhase.END)
    
    async def pause_timer(self, game_id: str) -> bool:
        """Pause the timer."""
        success = await timer_repository.set_paused(game_id, True)
        if success:
            await ws_manager.broadcast_to_game(game_id, {
                "event": "timer:paused",
                "data": {"game_id": game_id}
            })
            logger.info(f"Timer paused for game {game_id}")
        return success
    
    async def resume_timer(self, game_id: str) -> bool:
        """Resume the timer."""
        success = await timer_repository.set_paused(game_id, False)
        if success:
            await ws_manager.broadcast_to_game(game_id, {
                "event": "timer:resumed",
                "data": {"game_id": game_id}
            })
            logger.info(f"Timer resumed for game {game_id}")
        return success
    
    async def stop_timer(self, game_id: str):
        """Stop and cancel the timer."""
        if game_id in self._active_tasks:
            self._active_tasks[game_id].cancel()
            try:
                await self._active_tasks[game_id]
            except asyncio.CancelledError:
                pass
            del self._active_tasks[game_id]
            logger.info(f"Timer stopped for game {game_id}")
    
    async def get_timer_state(self, game_id: str) -> Optional[TimerState]:
        """Get current timer state."""
        return await timer_repository.get_timer_state(game_id)


# Global timer service instance
timer_service = TimerService()

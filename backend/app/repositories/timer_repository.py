"""Timer repository for database operations."""
from typing import Optional
from datetime import datetime
from app.models.timer import TimerModel
from app.schemas.timer import TimerState
from app.core.logger import logger


class TimerRepository:
    """Repository for timer state persistence."""
    
    def __init__(self):
        # In-memory storage for now (will use actual DB later)
        self._storage: dict[str, TimerState] = {}
    
    async def save_timer_state(self, timer_state: TimerState) -> TimerState:
        """Save or update timer state."""
        self._storage[timer_state.game_id] = timer_state
        logger.info(f"Timer state saved for game {timer_state.game_id}")
        return timer_state
    
    async def get_timer_state(self, game_id: str) -> Optional[TimerState]:
        """Get timer state by game_id."""
        return self._storage.get(game_id)
    
    async def delete_timer_state(self, game_id: str) -> bool:
        """Delete timer state."""
        if game_id in self._storage:
            del self._storage[game_id]
            logger.info(f"Timer state deleted for game {game_id}")
            return True
        return False
    
    async def update_remaining_seconds(self, game_id: str, remaining_seconds: int) -> bool:
        """Update remaining seconds for a timer."""
        if game_id in self._storage:
            self._storage[game_id].remaining_seconds = remaining_seconds
            return True
        return False
    
    async def set_paused(self, game_id: str, is_paused: bool) -> bool:
        """Set pause state for a timer."""
        if game_id in self._storage:
            self._storage[game_id].is_paused = is_paused
            logger.info(f"Timer for game {game_id} paused={is_paused}")
            return True
        return False


# Global timer repository instance
timer_repository = TimerRepository()

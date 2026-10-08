"""Game Engine - sole state mutator for game state."""
from typing import Optional
from uuid import UUID
from app.game.phases import GamePhase
from app.core.logger import logger
from app.core.websocket import ws_manager


class GameEngine:
    """
    Central game state manager.
    All game state mutations must go through this engine.
    """
    
    def __init__(self):
        # In-memory game states (will be persisted to DB via repository)
        self.game_states: dict[str, dict] = {}
    
    def create_game(self, game_id: str) -> dict:
        """Initialize a new game state."""
        state = {
            "game_id": game_id,
            "phase": GamePhase.LOBBY,
            "players": [],
            "is_active": False,
        }
        self.game_states[game_id] = state
        logger.info(f"Game {game_id} created in phase {GamePhase.LOBBY}")
        return state
    
    def get_game_state(self, game_id: str) -> Optional[dict]:
        """Get current game state."""
        return self.game_states.get(game_id)
    
    async def transition_phase(self, game_id: str, new_phase: GamePhase):
        """
        Transition game to a new phase.
        This is called by TimerService when phase timer expires.
        """
        if game_id not in self.game_states:
            logger.error(f"Game {game_id} not found")
            return
        
        old_phase = self.game_states[game_id]["phase"]
        self.game_states[game_id]["phase"] = new_phase
        
        logger.info(f"Game {game_id} transitioned: {old_phase} -> {new_phase}")
        
        # Broadcast phase change to all players
        await ws_manager.broadcast_to_game(game_id, {
            "event": "phase:changed",
            "data": {
                "game_id": game_id,
                "old_phase": old_phase,
                "new_phase": new_phase,
            }
        })
    
    def start_game(self, game_id: str):
        """Start the game."""
        if game_id not in self.game_states:
            logger.error(f"Game {game_id} not found")
            return
        
        self.game_states[game_id]["is_active"] = True
        self.game_states[game_id]["phase"] = GamePhase.PREPARING
        logger.info(f"Game {game_id} started")


# Global game engine instance
game_engine = GameEngine()

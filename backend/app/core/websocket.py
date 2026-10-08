"""WebSocket connection manager."""
from typing import Dict, Set
from fastapi import WebSocket
from app.core.logger import logger


class ConnectionManager:
    """Manages WebSocket connections and broadcasting."""
    
    def __init__(self):
        # game_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str):
        """Connect a client to a game room."""
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()
        self.active_connections[game_id].add(websocket)
        logger.info(f"Client connected to game {game_id}")
    
    def disconnect(self, websocket: WebSocket, game_id: str):
        """Disconnect a client from a game room."""
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
        logger.info(f"Client disconnected from game {game_id}")
    
    async def broadcast_to_game(self, game_id: str, message: dict):
        """Broadcast a message to all clients in a game room."""
        if game_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[game_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection, game_id)
    
    async def send_to_client(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")


# Global WebSocket manager instance
ws_manager = ConnectionManager()

"""FastAPI main application."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.websocket import ws_manager
from app.core.logger import logger
from app.api.v1.routers import timer

app = FastAPI(
    title="Lycan Game API",
    description="Backend API for Lycan Werewolf game",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(timer.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Lycan Game API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for game communication."""
    await ws_manager.connect(websocket, game_id)
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Echo back for now (will be handled by specific handlers)
            logger.info(f"Received from game {game_id}: {data}")
            
            # Handle different event types
            event = data.get("event")
            if event:
                logger.info(f"Event {event} received from game {game_id}")
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, game_id)
        logger.info(f"Client disconnected from game {game_id}")
    except Exception as e:
        logger.error(f"WebSocket error for game {game_id}: {e}")
        ws_manager.disconnect(websocket, game_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

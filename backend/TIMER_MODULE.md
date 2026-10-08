# Timer Module Documentation

## Overview
Modul Timer untuk mengatur phase game (Day/Night/Voting) dengan broadcast realtime ke player lewat WebSocket.

## Architecture
Mengikuti pattern: **Router -> Service -> Repository -> Database**

```
Timer Request → Router → Service (background task) → Repository → DB
                   ↓
              WebSocket Broadcast → All Players
```

## Struktur File

```
backend/app/
├── api/v1/routers/timer.py       # REST endpoints
├── services/timer_service.py     # Business logic & background task
├── repositories/timer_repository.py  # Data persistence
├── models/timer.py               # Database model
├── schemas/timer.py              # Request/Response schemas
└── game/
    ├── engine.py                 # GameEngine (state mutator)
    └── phases.py                 # GamePhase enum
```

## State yang Disimpan

```python
{
    "game_id": "uuid",
    "phase": "DAY" | "NIGHT" | "VOTING" | ...,
    "duration_seconds": 60,
    "remaining_seconds": 45,
    "end_time": "2026-08-29T12:00:00Z",
    "is_paused": false
}
```

## REST API Endpoints

Base URL: `/api/v1/games/{game_id}/timer`

### GET `/`
Get status timer aktif.

**Response:**
```json
{
  "game_id": "game-123",
  "phase": "DAY",
  "remaining_seconds": 45,
  "end_time": "2026-08-29T12:00:00Z",
  "is_paused": false
}
```

### POST `/start`
Mulai phase timer (host/system).

**Request:**
```json
{
  "phase": "DAY",
  "duration_seconds": 60
}
```

**Response:** Timer state

### POST `/pause`
Pause timer.

### POST `/resume`
Resume timer yang di-pause.

### POST `/stop`
Stop timer sepenuhnya.

## WebSocket Events

Connect ke: `ws://localhost:8000/ws/{game_id}`

### Server → Client Events

#### `timer:started`
Timer dimulai untuk phase baru.
```json
{
  "event": "timer:started",
  "data": {
    "game_id": "game-123",
    "phase": "DAY",
    "duration_seconds": 60,
    "end_time": "2026-08-29T12:00:00Z"
  }
}
```

#### `timer:tick`
Broadcast setiap 1 detik.
```json
{
  "event": "timer:tick",
  "data": {
    "game_id": "game-123",
    "phase": "DAY",
    "remaining_seconds": 45,
    "end_time": "2026-08-29T12:00:00Z"
  }
}
```

#### `timer:finished`
Timer habis, phase selesai.
```json
{
  "event": "timer:finished",
  "data": {
    "game_id": "game-123",
    "completed_phase": "DAY",
    "next_phase": "NIGHT"
  }
}
```

#### `timer:paused`
Timer di-pause.
```json
{
  "event": "timer:paused",
  "data": {
    "game_id": "game-123"
  }
}
```

#### `timer:resumed`
Timer dilanjutkan.
```json
{
  "event": "timer:resumed",
  "data": {
    "game_id": "game-123"
  }
}
```

#### `phase:changed`
Phase berganti (triggered by GameEngine).
```json
{
  "event": "phase:changed",
  "data": {
    "game_id": "game-123",
    "old_phase": "DAY",
    "new_phase": "NIGHT"
  }
}
```

## Game Phase Flow

```
PREPARING → ROLE_PREPARE → NIGHT → MORNING → DISCUSSION → VOTING → EXECUTION
                                      ↑                                  ↓
                                      └──────────────────────────────────┘
```

## Usage Example

### 1. Start Server
```bash
cd backend
pip install -r requirements.txt
python -m app.main
# atau
uvicorn app.main:app --reload
```

### 2. Start Timer (REST)
```bash
curl -X POST http://localhost:8000/api/v1/games/game-123/timer/start \
  -H "Content-Type: application/json" \
  -d '{
    "phase": "DAY",
    "duration_seconds": 60
  }'
```

### 3. Connect via WebSocket (JavaScript)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/game-123');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.event === 'timer:tick') {
    console.log(`Time remaining: ${message.data.remaining_seconds}s`);
  }
  
  if (message.event === 'timer:finished') {
    console.log(`Phase ${message.data.completed_phase} finished!`);
  }
  
  if (message.event === 'phase:changed') {
    console.log(`New phase: ${message.data.new_phase}`);
  }
};
```

## Key Components

### TimerService (`timer_service.py`)
- `start_phase_timer()`: Start timer baru
- `_tick_loop()`: Background task tick setiap 1 detik
- `_handle_timer_expired()`: Trigger phase transition
- `pause_timer()` / `resume_timer()`: Control timer
- `stop_timer()`: Cancel timer

### GameEngine (`engine.py`)
- Sole state mutator untuk game state
- `transition_phase()`: Ganti phase dan broadcast event
- `create_game()`: Initialize game baru
- `get_game_state()`: Get current state

### ConnectionManager (`websocket.py`)
- `connect()` / `disconnect()`: Manage WebSocket connections
- `broadcast_to_game()`: Kirim message ke semua player di room
- `send_to_client()`: Kirim ke client spesifik

## Integration dengan GameEngine

Ketika timer habis:
1. `TimerService._tick_loop()` deteksi `remaining_seconds == 0`
2. Call `_handle_timer_expired()`
3. Broadcast `timer:finished` event
4. Call `GameEngine.transition_phase()` untuk ganti phase
5. GameEngine broadcast `phase:changed` event
6. Cleanup timer state

## Next Steps

- [ ] Integrasi dengan PostgreSQL (saat ini masih in-memory)
- [ ] Tambah authentication/authorization
- [ ] Handle reconnection (restore timer state)
- [ ] Variable timer duration per phase type
- [ ] Win condition check di GameEngine
- [ ] Integration dengan Voting module
- [ ] Integration dengan Role Engine

## Testing

```bash
# Start server
uvicorn app.main:app --reload

# Test REST endpoints
curl http://localhost:8000/health

# Test WebSocket (gunakan wscat)
npm install -g wscat
wscat -c ws://localhost:8000/ws/test-game
```

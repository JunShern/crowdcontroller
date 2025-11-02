# Crowd Controller

A real-time crowd-controlled gaming system where audience members vote on game actions via a web interface, with the most popular command executed every second.

## Architecture

```
Audience (Web UI) → Backend Server → Controller → Game
     └─────────────────────────┴─────────→ Visualizer
```

### Components

**1. Backend Server** (`backend/main.py`)
- FastAPI + WebSocket server
- Receives commands from audience members
- Broadcasts all commands to connected clients
- Hosts web interface at `/static/index.html`

**2. Web Interface** (`backend/static/index.html`)
- NES-style game controller UI
- Sends commands via WebSocket: MOVE_UP/DOWN/LEFT/RIGHT, ATTACK, WATER, PROPOSE
- Mobile-friendly with touch support, haptic feedback, and wake lock

**3. Controller** (`controller/crowd_aggregator.py`)
- Connects to backend as WebSocket client
- Collects all incoming commands in 1-second windows
- Executes the most-voted command using PyAutoGUI (keyboard/mouse control)
- Broadcasts real-time stats to visualization dashboard

**4. Visualizer** (`controller/visualizer.html`)
- Real-time vote counts with animated bars
- Countdown timer to next command execution
- Command history log
- Accessible at `http://localhost:8080` when controller is running

## Data Flow

1. **Audience votes**: Multiple users send commands from web UI
2. **Server broadcasts**: All commands forwarded to controller
3. **Aggregation**: Controller counts votes in 1-second windows
4. **Execution**: Top command sent to game via PyAutoGUI
5. **Visualization**: Live stats displayed on dashboard

## Setup

```bash
# Start backend server (cloud/Railway)
cd backend
python main.py

# Start controller (local machine with game running)
cd controller
python crowd_aggregator.py
# Visit http://localhost:8080 for visualization

# Share backend URL with audience
# e.g., https://your-backend.railway.app
```

## Supported Commands

- **Movement**: MOVE_UP (W), MOVE_DOWN (S), MOVE_LEFT (A), MOVE_RIGHT (D)
- **Actions**:
  - ATTACK (press '1' + left-click)
  - WATER (press '2' + left-click)
  - PROPOSE (press '3' + right-click)

## Configuration

`controller/crowd_aggregator.py`:
- `AGGREGATION_WINDOW = 1.0` - Voting window duration (seconds)
- `WEB_PORT = 8080` - Visualization server port
- `WEBSOCKET_URI` - Backend WebSocket URL

---

Built with FastAPI, WebSockets, PyAutoGUI, and NES.css

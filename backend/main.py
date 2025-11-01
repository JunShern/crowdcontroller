from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from collections import defaultdict
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS: if you don't use cookies/auth, keep credentials False and wildcard origins OK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # <- set False unless you actually need cookies/auth
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve ./backend/static
STATIC_DIR = (Path(__file__).parent / "static").resolve()
logger.info(f"Serving static from: {STATIC_DIR}")
if not STATIC_DIR.exists():
    # Fail fast with a clear error if static files didn't make it into the image
    raise RuntimeError(f"Static directory not found at {STATIC_DIR}")

# Serve /static/*
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve index.html at "/"
@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return index_path.read_text(encoding="utf-8")

# Diagnostics page
@app.get("/websocket_test", response_class=HTMLResponse)
async def get_websocket_test():
    page = STATIC_DIR / "websocket_test.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="websocket_test.html not found")
    return page.read_text(encoding="utf-8")

connections = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection attempt")
    await websocket.accept()
    logger.info("WebSocket connection accepted")
    connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received command: {data}")
            await broadcast(json.dumps({"command": data}))
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connections.discard(websocket)

async def broadcast(message: str):
    logger.info(f"Broadcasting: {message}")
    dead = []
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            dead.append(ws)
    for ws in dead:
        connections.discard(ws)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

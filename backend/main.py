from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from collections import defaultdict
import logging
import os
import json  # Add json import

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine the absolute path to the static directory
current_dir = os.path.dirname(os.path.abspath(__file__))
static_directory = os.path.join(current_dir, "static")

# Ensure the static directory exists
os.makedirs(static_directory, exist_ok=True)

# Serve static files under /static path
app.mount("/static", StaticFiles(directory=static_directory), name="static")

# Serve index.html at the root
@app.get("/", response_class=HTMLResponse)
async def get_index():
    with open(os.path.join(static_directory, "index.html"), "r") as f:
        return f.read()

# Serve websocket_test.html for diagnostics
@app.get("/websocket_test", response_class=HTMLResponse)
async def get_websocket_test():
    with open(os.path.join(static_directory, "websocket_test.html"), "r") as f:
        return f.read()

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
        connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        connections.discard(websocket)

async def broadcast(message: str):
    logger.info(f"Broadcasting: {message}")
    disconnected = set()
    for connection in connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Error sending to client: {str(e)}")
            disconnected.add(connection)
    
    # Remove disconnected clients
    for connection in disconnected:
        connections.discard(connection)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

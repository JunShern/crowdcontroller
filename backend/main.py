from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn
from collections import defaultdict

app = FastAPI()

# Serve frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

connections = set()
commands_count = defaultdict(int)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            commands_count[data] += 1  # Aggregate commands
            await broadcast(str(commands_count))  # Broadcast update
    except WebSocketDisconnect:
        connections.remove(websocket)

async def broadcast(message: str):
    for connection in connections:
        try:
            await connection.send_text(message)
        except:
            connections.remove(connection)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

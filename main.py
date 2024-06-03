# main.py
 
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketState
from typing import List
import uuid
 
app = FastAPI()
 
# Define the origins that should be allowed to make requests to your API
origins = [
    "*",  # Adjust if using live server extension in VS Code
    # Add the domain of your frontend application here if it is deployed somewhere
]
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow these origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
rooms = {}
 
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
 
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
 
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
 
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            if connection.application_state == WebSocketState.CONNECTED:
                await connection.send_text(message)
 
manager = ConnectionManager()
 
@app.post("/create_room")
async def create_room():
    room_code = str(uuid.uuid4())[:8]
    rooms[room_code] = manager
    return JSONResponse(content={"room_code": room_code})
 
@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    if room_code in rooms:
        manager = rooms[room_code]
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await manager.broadcast(data)
        except WebSocketDisconnect:
            manager.disconnect(websocket)
    else:
        await websocket.close()
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
 
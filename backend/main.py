from typing import List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import redis.asyncio as redis

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.redis = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        messages = await self.get_messages()
        for message in messages:
            try:
                await websocket.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(websocket)
                break

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except WebSocketDisconnect:
            self.disconnect(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                self.disconnect(connection)

    async def save_message(self, message: str):
        if self.redis:
            await self.redis.rpush("chat_messages", message)

    async def get_messages(self) -> List[str]:
        if self.redis:
            messages = await self.redis.lrange("chat_messages", 0, -1)
            return [msg.decode('utf-8') for msg in messages]
        return []

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    manager.redis = await redis.from_url("redis://localhost")

@app.on_event("shutdown")
async def shutdown_event():
    await manager.redis.close()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    try:
        while True:
            data = await websocket.receive_text()
            message = {"time": current_time, "clientId": client_id, "message": data}
            message_json = json.dumps(message)
            await manager.broadcast(message_json)
            await manager.save_message(message_json)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        message = {"time": current_time, "clientId": client_id, "message": "Offline"}
        await manager.broadcast(json.dumps(message))

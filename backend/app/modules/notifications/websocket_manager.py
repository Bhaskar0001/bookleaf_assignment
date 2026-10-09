from typing import Dict, List, Any, Optional
import json
import uuid
from fastapi import WebSocket
from starlette.websockets import WebSocketState
from app.core.logging import logger


class ConnectionManager:
    def __init__(self):
        # Maps user_id -> List[WebSocket]
        self.active_user_connections: Dict[uuid.UUID, List[WebSocket]] = {}
        # List of all active admin WebSockets
        self.active_admin_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, user_id: uuid.UUID, role: str):
        if websocket.client_state == WebSocketState.CONNECTING:
            await websocket.accept()
        if user_id not in self.active_user_connections:
            self.active_user_connections[user_id] = []
        self.active_user_connections[user_id].append(websocket)

        if role == "ADMIN":
            self.active_admin_connections.append(websocket)
        logger.info(f"WebSocket client connected: user={user_id}, role={role}")

    def disconnect(self, websocket: WebSocket, user_id: uuid.UUID, role: str):
        if user_id in self.active_user_connections:
            if websocket in self.active_user_connections[user_id]:
                self.active_user_connections[user_id].remove(websocket)
            if not self.active_user_connections[user_id]:
                del self.active_user_connections[user_id]

        if role == "ADMIN" and websocket in self.active_admin_connections:
            self.active_admin_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected: user={user_id}")

    async def broadcast_to_user(self, user_id: uuid.UUID, message: Dict[str, Any]):
        if user_id in self.active_user_connections:
            payload = json.dumps(message)
            dead_sockets = []
            for ws in self.active_user_connections[user_id]:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.active_user_connections[user_id].remove(ws)

    async def broadcast_to_admins(self, message: Dict[str, Any]):
        payload = json.dumps(message)
        dead_sockets = []
        for ws in self.active_admin_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead_sockets.append(ws)
        for ws in dead_sockets:
            if ws in self.active_admin_connections:
                self.active_admin_connections.remove(ws)

    async def broadcast_event(
        self,
        event_name: str,
        ticket_id: str,
        author_user_id: Optional[uuid.UUID],
        payload: Dict[str, Any],
    ):
        """
        Broadcasts event to admins and to the author who owns the ticket.
        """
        msg = {
            "event": event_name,
            "ticket_id": ticket_id,
            "payload": payload,
        }
        # Admins see all updates
        await self.broadcast_to_admins(msg)
        # Author sees updates for their own tickets
        if author_user_id:
            await self.broadcast_to_user(author_user_id, msg)


manager = ConnectionManager()

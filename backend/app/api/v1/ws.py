from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.modules.notifications.websocket_manager import manager
from app.api.dependencies import get_ws_user
from app.db.models import User
from app.core.logging import logger

router = APIRouter(tags=["Real-time"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: User = Depends(get_ws_user),
):
    if not user:
        return

    await manager.connect(websocket, user.id, user.role)
    try:
        while True:
            # Keep alive and listen for client heartbeats
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id, user.role)
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
        manager.disconnect(websocket, user.id, user.role)

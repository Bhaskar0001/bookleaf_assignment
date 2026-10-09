import json
import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.notifications.websocket_manager import manager
from app.db.session import AsyncSessionLocal
from app.core.security import decode_access_token
from app.db.models import User
from app.core.logging import logger

router = APIRouter(tags=["Real-time"])


async def authenticate_token(token: str, db: AsyncSession) -> Optional[User]:
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        user_uuid = uuid.UUID(user_id_str)
        query = (
            select(User)
            .options(selectinload(User.author_profile))
            .where(User.id == user_uuid, User.is_active == True)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    except Exception:
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    await websocket.accept()
    user = None

    async with AsyncSessionLocal() as db:
        # 1. Check query parameter token (legacy/fallback)
        if token:
            user = await authenticate_token(token, db)
        else:
            # 2. Secure handshake: Wait for initial authentication JSON payload
            try:
                auth_data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                parsed = json.loads(auth_data)
                candidate_token = parsed.get("token")
                if candidate_token:
                    user = await authenticate_token(candidate_token, db)
            except Exception as e:
                logger.warning(f"WebSocket auth handshake timed out or failed: {e}")

        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return

        await manager.connect(websocket, user.id, user.role)
        try:
            # Acknowledge connection
            await websocket.send_json({"event": "connected", "userId": str(user.id), "role": user.role})
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            manager.disconnect(websocket, user.id, user.role)
        except Exception as e:
            logger.warning(f"WebSocket session error: {e}")
            manager.disconnect(websocket, user.id, user.role)

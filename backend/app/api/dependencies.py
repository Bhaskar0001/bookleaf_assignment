from typing import Optional, Annotated
import uuid
from fastapi import Depends, Header, WebSocket, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.security import decode_access_token
from app.core.errors import UnauthorizedException, ForbiddenException
from app.db.models import User, Author


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization:
        raise UnauthorizedException("Authorization header missing", code="AUTH_HEADER_MISSING")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedException("Invalid authorization scheme. Use 'Bearer <token>'", code="AUTH_INVALID_SCHEME")

    token = parts[1]
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload missing subject", code="AUTH_INVALID_PAYLOAD")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user ID in token", code="AUTH_INVALID_USER_ID")

    from sqlalchemy.orm import selectinload
    query = (
        select(User)
        .options(selectinload(User.author_profile))
        .where(User.id == user_uuid, User.is_active == True)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException("User not found or inactive", code="AUTH_USER_NOT_FOUND")

    return user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "ADMIN":
        raise ForbiddenException("Administrator role required for this action", code="ADMIN_ROLE_REQUIRED")
    return current_user


async def require_author(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Author:
    if current_user.role != "AUTHOR":
        raise ForbiddenException("Author role required for this endpoint", code="AUTHOR_ROLE_REQUIRED")

    result = await db.execute(select(Author).where(Author.user_id == current_user.id))
    author = result.scalar_one_or_none()
    if not author:
        raise ForbiddenException("Author profile not found for authenticated user", code="AUTHOR_PROFILE_NOT_FOUND")

    return author


async def get_ws_user(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not token:
        await websocket.close(code=4001, reason="Authentication token missing")
        return None
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            await websocket.close(code=4002, reason="Invalid token payload")
            return None
        user_uuid = uuid.UUID(user_id_str)
        query = (
            select(User)
            .options(selectinload(User.author_profile))
            .where(User.id == user_uuid, User.is_active == True)
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            await websocket.close(code=4003, reason="User not found")
            return None
        return user
    except Exception:
        await websocket.close(code=4004, reason="Authentication failed")
        return None

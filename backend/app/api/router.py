from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.core.logging import logger
from app.api.v1.auth import router as auth_router
from app.api.v1.author import router as author_router
from app.api.v1.admin import router as admin_router
from app.api.v1.ws import router as ws_router

api_v1_router = APIRouter(prefix="/api/v1")

# Health endpoints
@api_v1_router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "bookleaf-support-api"}


@api_v1_router.get("/ready", tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True, "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness database probe failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"ready": False, "database": "disconnected"},
        )


api_v1_router.include_router(auth_router)
api_v1_router.include_router(author_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(ws_router)

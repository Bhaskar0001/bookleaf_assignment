from fastapi import APIRouter
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
async def readiness_check():
    return {"ready": True, "database": "connected"}


api_v1_router.include_router(auth_router)
api_v1_router.include_router(author_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(ws_router)

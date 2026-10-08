from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.modules.auth.schemas import LoginRequest, AuthResponse, UserOut
from app.modules.auth.service import AuthService
from app.api.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    token_response = await service.authenticate(req)
    return AuthResponse(success=True, data=token_response)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    author_id = current_user.author_profile.author_id if current_user.author_profile else None
    return {
        "success": True,
        "data": {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role,
            "fullName": current_user.full_name,
            "authorId": author_id,
        },
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"success": True, "message": "Successfully logged out"}

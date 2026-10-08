from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.models import User, Author
from app.core.security import verify_password, create_access_token
from app.core.errors import UnauthorizedException
from app.modules.auth.schemas import LoginRequest, TokenResponse, UserOut


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(self, req: LoginRequest) -> TokenResponse:
        query = (
            select(User)
            .where(User.email == req.email.lower(), User.is_active == True)
            .options(selectinload(User.author_profile))
        )
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password", code="AUTH_INVALID_CREDENTIALS")

        author_id = user.author_profile.author_id if user.author_profile else None

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "full_name": user.full_name,
            "author_id": author_id,
        }
        token = create_access_token(token_data)

        user_out = UserOut(
            id=user.id,
            email=user.email,
            role=user.role,
            full_name=user.full_name,
            is_active=user.is_active,
            author_id=author_id,
        )

        return TokenResponse(
            access_token=token,
            user=user_out,
        )

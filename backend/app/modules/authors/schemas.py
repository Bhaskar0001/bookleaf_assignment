from typing import Optional
from decimal import Decimal
import uuid
from pydantic import BaseModel


class AuthorProfileOut(BaseModel):
    id: uuid.UUID
    author_id: str
    pen_name: str
    phone: Optional[str] = None
    email: str
    total_books: int
    published_books: int
    books_in_production: int
    total_royalties_earned: Decimal
    total_royalties_paid: Decimal
    total_royalties_pending: Decimal
    open_tickets: int

    class Config:
        from_attributes = True


class AuthorProfileResponse(BaseModel):
    success: bool = True
    data: AuthorProfileOut

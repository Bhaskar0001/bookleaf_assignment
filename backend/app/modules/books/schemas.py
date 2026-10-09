from typing import Optional, List, Any
from decimal import Decimal
from datetime import date, datetime
import uuid
from pydantic import BaseModel


class BookOut(BaseModel):
    id: uuid.UUID
    book_id: str
    author_id: uuid.UUID
    title: str
    isbn: Optional[str] = None
    genre: Optional[str] = None
    publication_date: Optional[date] = None
    status: str
    mrp: Optional[Decimal] = None
    author_royalty_per_copy: Optional[Decimal] = None
    copies_sold: int
    royalty_earned: Decimal
    royalty_paid: Decimal
    royalty_pending: Decimal
    last_royalty_payout_date: Optional[date] = None
    print_partner: Optional[str] = None
    available_on: List[str] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookListResponse(BaseModel):
    success: bool = True
    data: List[BookOut]


class BookDetailResponse(BaseModel):
    success: bool = True
    data: BookOut

from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Book


class BookRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_books_by_author(self, author_id: uuid.UUID) -> List[Book]:
        query = select(Book).where(Book.author_id == author_id).order_by(Book.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_book_by_id_and_author(self, book_identifier: str, author_id: uuid.UUID) -> Optional[Book]:
        # Support both UUID and custom book_id (e.g., BK001)
        query = select(Book).where(Book.author_id == author_id)
        try:
            val_uuid = uuid.UUID(book_identifier)
            query = query.where(Book.id == val_uuid)
        except ValueError:
            query = query.where(Book.book_id == book_identifier)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_book_by_id(self, book_identifier: str) -> Optional[Book]:
        query = select(Book)
        try:
            val_uuid = uuid.UUID(book_identifier)
            query = query.where(Book.id == val_uuid)
        except ValueError:
            query = query.where(Book.book_id == book_identifier)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

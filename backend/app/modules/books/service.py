from typing import List
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.books.repository import BookRepository
from app.db.models import Book
from app.core.errors import NotFoundException, ForbiddenException


class BookService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = BookRepository(db)

    async def get_my_books(self, author_id: uuid.UUID) -> List[Book]:
        return await self.repository.get_books_by_author(author_id)

    async def get_my_book_detail(self, book_identifier: str, author_id: uuid.UUID) -> Book:
        book = await self.repository.get_book_by_id_and_author(book_identifier, author_id)
        if not book:
            # Check if book exists at all to return precise error code
            existing = await self.repository.get_book_by_id(book_identifier)
            if existing:
                raise ForbiddenException(
                    "The requested book is not available for this account.",
                    code="BOOK_NOT_ACCESSIBLE",
                )
            raise NotFoundException("Book not found", code="BOOK_NOT_FOUND")
        return book

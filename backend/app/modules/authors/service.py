from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.models import Author, Book, Ticket, User
from app.modules.authors.schemas import AuthorProfileOut


class AuthorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_author_dashboard_profile(self, author: Author, user: User) -> AuthorProfileOut:
        # 1. Book counts
        book_counts = await self.db.execute(
            select(
                func.count(Book.id).label("total"),
                func.count(Book.id).filter(Book.status == "PUBLISHED").label("published"),
                func.count(Book.id).filter(Book.status == "IN_PRODUCTION").label("in_production"),
            ).where(Book.author_id == author.id)
        )
        counts = book_counts.first()
        total_books = counts.total or 0
        published_books = counts.published or 0
        in_production = counts.in_production or 0

        # 2. Open tickets count
        ticket_count_res = await self.db.execute(
            select(func.count(Ticket.id)).where(
                Ticket.author_id == author.id,
                Ticket.status.in_(["OPEN", "IN_PROGRESS"]),
            )
        )
        open_tickets = ticket_count_res.scalar() or 0

        return AuthorProfileOut(
            id=author.id,
            author_id=author.author_id,
            pen_name=author.pen_name,
            phone=author.phone,
            email=user.email,
            total_books=total_books,
            published_books=published_books,
            books_in_production=in_production,
            total_royalties_earned=author.total_royalties_earned,
            total_royalties_paid=author.total_royalties_paid,
            total_royalties_pending=author.total_royalties_pending,
            open_tickets=open_tickets,
        )

import sys
import os
import json
from decimal import Decimal
from datetime import date
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.db.session import SessionLocal
from app.db.models import User, Author, Book, Ticket, TicketMessage, TicketInternalNote, TicketEvent, SupportAssistRun, TicketRelationship
from app.core.security import get_password_hash

ADMIN_EMAIL = "admin@bookleaf.com"
ADMIN_PASSWORD = "Admin@BookLeaf2026!"
DEFAULT_AUTHOR_PASSWORD = "Author@BookLeaf2026!"


def find_sample_data_file() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "data" / "bookleaf_sample_data.json",
        Path(__file__).resolve().parent.parent.parent / "bookleaf_sample_data.json",
        Path("bookleaf_sample_data.json"),
        Path("backend/data/bookleaf_sample_data.json"),
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find bookleaf_sample_data.json in any expected locations.")


def parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val))
    except Exception:
        return None


def parse_decimal(val):
    if val is None:
        return None
    return Decimal(str(val))


def seed_database(reset: bool = False):
    """
    Seeds the BookLeaf database with the supplied 10 authors and 18 books.
    By default (reset=False), performs a strictly idempotent upsert that preserves existing
    tickets, messages, and production records.
    If reset=True (via --reset CLI flag), clears records for disposable test environments.
    """
    json_path = find_sample_data_file()
    print(f"Loading sample data from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    authors_data = data.get("authors", [])
    print(f"Found {len(authors_data)} authors in sample data.")

    with SessionLocal() as session:
        if reset:
            print("Reset flag detected: clearing all ticket and sample entities...")
            session.execute(delete(TicketRelationship))
            session.execute(delete(TicketEvent))
            session.execute(delete(TicketInternalNote))
            session.execute(delete(TicketMessage))
            session.execute(delete(SupportAssistRun))
            session.execute(delete(Ticket))
            session.execute(delete(Book))
            session.execute(delete(Author))
            session.execute(delete(User).where(User.role != "ADMIN"))
            session.flush()

        print("Executing idempotent upsert seed...")

        # 1. Seed or update Admin User
        admin_user = session.execute(select(User).where(User.email == ADMIN_EMAIL)).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                role="ADMIN",
                full_name="Operations Admin",
                is_active=True,
            )
            session.add(admin_user)
            session.flush()
            print(f"Created Admin user: {ADMIN_EMAIL}")
        else:
            admin_user.password_hash = get_password_hash(ADMIN_PASSWORD)
            admin_user.full_name = "Operations Admin"

        # 2. Seed authors and books from sample JSON idempotently
        for a_data in authors_data:
            author_id = a_data["author_id"]
            name = a_data["name"]
            email = a_data["email"]
            phone = a_data.get("phone")
            city = a_data.get("city")
            joined_date = parse_date(a_data.get("joined_date"))

            # Calculate royalty totals from books
            total_earned = Decimal("0.00")
            total_paid = Decimal("0.00")
            total_pending = Decimal("0.00")
            for b in a_data.get("books", []):
                total_earned += parse_decimal(b.get("total_royalty_earned")) or Decimal("0.00")
                total_paid += parse_decimal(b.get("royalty_paid")) or Decimal("0.00")
                total_pending += parse_decimal(b.get("royalty_pending")) or Decimal("0.00")

            # Check existing author user
            user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user:
                user = User(
                    email=email,
                    password_hash=get_password_hash(DEFAULT_AUTHOR_PASSWORD),
                    role="AUTHOR",
                    full_name=name,
                    is_active=True,
                )
                session.add(user)
                session.flush()
            else:
                user.full_name = name

            # Check existing Author profile
            author = session.execute(select(Author).where(Author.author_id == author_id)).scalar_one_or_none()
            if not author:
                author = Author(
                    user_id=user.id,
                    author_id=author_id,
                    pen_name=name,
                    phone=phone,
                    city=city,
                    joined_date=joined_date,
                    total_royalties_earned=total_earned,
                    total_royalties_paid=total_paid,
                    total_royalties_pending=total_pending,
                )
                session.add(author)
                session.flush()
            else:
                author.pen_name = name
                author.phone = phone
                author.city = city
                author.joined_date = joined_date
                author.total_royalties_earned = total_earned
                author.total_royalties_paid = total_paid
                author.total_royalties_pending = total_pending

            # Seed or update Books
            for b_data in a_data.get("books", []):
                book_id_code = b_data["book_id"]
                book = session.execute(select(Book).where(Book.book_id == book_id_code)).scalar_one_or_none()
                if not book:
                    book = Book(
                        book_id=book_id_code,
                        author_id=author.id,
                        title=b_data["title"],
                        isbn=b_data.get("isbn"),
                        genre=b_data.get("genre"),
                        publication_date=parse_date(b_data.get("publication_date")),
                        status=b_data.get("status", "In Production"),
                        mrp=parse_decimal(b_data.get("mrp")),
                        author_royalty_per_copy=parse_decimal(b_data.get("author_royalty_per_copy")),
                        copies_sold=int(b_data.get("total_copies_sold", 0)),
                        royalty_earned=parse_decimal(b_data.get("total_royalty_earned")) or Decimal("0.00"),
                        royalty_paid=parse_decimal(b_data.get("royalty_paid")) or Decimal("0.00"),
                        royalty_pending=parse_decimal(b_data.get("royalty_pending")) or Decimal("0.00"),
                        last_royalty_payout_date=parse_date(b_data.get("last_royalty_payout_date")),
                        print_partner=b_data.get("print_partner"),
                        available_on=b_data.get("available_on", []),
                    )
                    session.add(book)
                else:
                    book.title = b_data["title"]
                    book.isbn = b_data.get("isbn")
                    book.genre = b_data.get("genre")
                    book.status = b_data.get("status", book.status)
                    book.mrp = parse_decimal(b_data.get("mrp"))
                    book.author_royalty_per_copy = parse_decimal(b_data.get("author_royalty_per_copy"))
                    book.copies_sold = int(b_data.get("total_copies_sold", book.copies_sold))
                    book.royalty_earned = parse_decimal(b_data.get("total_royalty_earned")) or Decimal("0.00")
                    book.royalty_paid = parse_decimal(b_data.get("royalty_paid")) or Decimal("0.00")
                    book.royalty_pending = parse_decimal(b_data.get("royalty_pending")) or Decimal("0.00")
                    book.last_royalty_payout_date = parse_date(b_data.get("last_royalty_payout_date"))
                    book.print_partner = b_data.get("print_partner")
                    book.available_on = b_data.get("available_on", [])

        session.commit()

        # Verification count
        final_authors = session.execute(select(Author)).scalars().all()
        final_books = session.execute(select(Book)).scalars().all()
        print(f"Seed complete! Verified Authors: {len(final_authors)}, Verified Books: {len(final_books)}")
        assert len(final_authors) == 10, f"Expected 10 authors, got {len(final_authors)}"
        assert len(final_books) == 18, f"Expected 18 books, got {len(final_books)}"
        print("Idempotent seed verification passed successfully using bookleaf_sample_data.json!")


if __name__ == "__main__":
    should_reset = "--reset" in sys.argv or os.getenv("FORCE_RESET", "").lower() in ("true", "1")
    seed_database(reset=should_reset)

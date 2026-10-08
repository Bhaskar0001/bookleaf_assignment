import sys
import os
from decimal import Decimal
from datetime import date

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from sqlalchemy import select
from app.db.session import sync_engine
from app.db.models import User, Author, Book
from app.core.security import get_password_hash

ADMIN_EMAIL = "admin@bookleaf.com"
ADMIN_PASSWORD = "Admin@BookLeaf2026!"
DEFAULT_AUTHOR_PASSWORD = "Author@BookLeaf2026!"

AUTHORS_DATA = [
    {
        "author_id": "AUTH001",
        "email": "priya.sharma@bookleaf.com",
        "full_name": "Priya Sharma",
        "pen_name": "Priya Sharma",
        "phone": "+91 98765 43210",
        "books": [
            {
                "book_id": "BK001",
                "title": "Whispers of the Ganges",
                "isbn": "978-93-91234-01-2",
                "genre": "Literary Fiction",
                "publication_date": date(2023, 4, 15),
                "status": "PUBLISHED",
                "mrp": Decimal("399.00"),
                "copies_sold": 1420,
                "royalty_earned": Decimal("28400.00"),
                "royalty_paid": Decimal("20000.00"),
                "royalty_pending": Decimal("8400.00"),
                "print_partner": "Replika Press",
                "available_on": ["Amazon", "Flipkart", "BookLeaf Store"],
            },
            {
                "book_id": "BK002",
                "title": "The Saffron Diaries",
                "isbn": "978-93-91234-02-9",
                "genre": "Historical Fiction",
                "publication_date": date(2023, 11, 20),
                "status": "PUBLISHED",
                "mrp": Decimal("450.00"),
                "copies_sold": 860,
                "royalty_earned": Decimal("19350.00"),
                "royalty_paid": Decimal("15000.00"),
                "royalty_pending": Decimal("4350.00"),
                "print_partner": "Thomson Press",
                "available_on": ["Amazon", "Flipkart"],
            },
            {
                "book_id": "BK003",
                "title": "Echoes from the Valley",
                "isbn": None,
                "genre": "Poetry",
                "publication_date": None,
                "status": "IN_PRODUCTION",
                "mrp": None,
                "copies_sold": 0,
                "royalty_earned": Decimal("0.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("0.00"),
                "print_partner": "Replika Press",
                "available_on": [],
            },
        ],
    },
    {
        "author_id": "AUTH002",
        "email": "rohit.verma@bookleaf.com",
        "full_name": "Rohit Verma",
        "pen_name": "Rohit Verma",
        "phone": "+91 98765 43211",
        "books": [
            {
                "book_id": "BK004",
                "title": "Code & Karma",
                "isbn": "978-93-91234-04-3",
                "genre": "Philosophy & Tech",
                "publication_date": date(2022, 9, 10),
                "status": "PUBLISHED",
                "mrp": Decimal("499.00"),
                "copies_sold": 2150,
                "royalty_earned": Decimal("53750.00"),
                "royalty_paid": Decimal("40000.00"),
                "royalty_pending": Decimal("13750.00"),
                "print_partner": "Manipal Technologies",
                "available_on": ["Amazon", "Flipkart", "Kindle"],
            },
            {
                "book_id": "BK005",
                "title": "Silicon Monks",
                "isbn": "978-93-91234-05-0",
                "genre": "Business Memoir",
                "publication_date": date(2023, 6, 18),
                "status": "PUBLISHED",
                "mrp": Decimal("550.00"),
                "copies_sold": 310,
                "royalty_earned": Decimal("8525.00"),
                "royalty_paid": Decimal("8525.00"),
                "royalty_pending": Decimal("0.00"),
                "print_partner": "Manipal Technologies",
                "available_on": ["Amazon"],
            },
            {
                "book_id": "BK006",
                "title": "Algorithms of Peace",
                "isbn": None,
                "genre": "Self-Help",
                "publication_date": None,
                "status": "IN_PRODUCTION",
                "mrp": None,
                "copies_sold": 0,
                "royalty_earned": Decimal("0.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("0.00"),
                "print_partner": None,
                "available_on": [],
            },
        ],
    },
    {
        "author_id": "AUTH003",
        "email": "ananya.iyer@bookleaf.com",
        "full_name": "Ananya Iyer",
        "pen_name": "Ananya Iyer",
        "phone": "+91 98765 43212",
        "books": [
            {
                "book_id": "BK007",
                "title": "Flavors of Malabar",
                "isbn": "978-93-91234-07-4",
                "genre": "Culinary & Culture",
                "publication_date": date(2023, 2, 14),
                "status": "PUBLISHED",
                "mrp": Decimal("699.00"),
                "copies_sold": 940,
                "royalty_earned": Decimal("32853.00"),
                "royalty_paid": Decimal("30000.00"),
                "royalty_pending": Decimal("2853.00"),
                "print_partner": "Thomson Press",
                "available_on": ["Amazon", "Crossword"],
            },
            {
                "book_id": "BK008",
                "title": "Temple Tales",
                "isbn": "978-93-91234-08-1",
                "genre": "Mythology",
                "publication_date": date(2024, 1, 10),
                "status": "PUBLISHED",
                "mrp": Decimal("350.00"),
                "copies_sold": 120,
                "royalty_earned": Decimal("2100.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("2100.00"),
                "print_partner": "Thomson Press",
                "available_on": ["Amazon", "Flipkart"],
            },
        ],
    },
    {
        "author_id": "AUTH004",
        "email": "vikram.malhotra@bookleaf.com",
        "full_name": "Vikram Malhotra",
        "pen_name": "Vikram Malhotra",
        "phone": "+91 98765 43213",
        "books": [
            {
                "book_id": "BK009",
                "title": "Bazaar Economics",
                "isbn": "978-93-91234-09-8",
                "genre": "Economics",
                "publication_date": date(2022, 11, 5),
                "status": "PUBLISHED",
                "mrp": Decimal("499.00"),
                "copies_sold": 530,
                "royalty_earned": Decimal("13223.50"),
                "royalty_paid": Decimal("10000.00"),
                "royalty_pending": Decimal("3223.50"),
                "print_partner": "Replika Press",
                "available_on": ["Amazon", "Barnes & Noble"],
            },
            {
                "book_id": "BK010",
                "title": "The Rupee Paradox",
                "isbn": None,
                "genre": "Finance",
                "publication_date": None,
                "status": "IN_PRODUCTION",
                "mrp": None,
                "copies_sold": 0,
                "royalty_earned": Decimal("0.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("0.00"),
                "print_partner": "Replika Press",
                "available_on": [],
            },
        ],
    },
    {
        "author_id": "AUTH005",
        "email": "sneha.patel@bookleaf.com",
        "full_name": "Sneha Patel",
        "pen_name": "Sneha Patel",
        "phone": "+91 98765 43214",
        "books": [
            {
                "book_id": "BK011",
                "title": "Wings of Cotton",
                "isbn": "978-93-91234-11-1",
                "genre": "Historical Drama",
                "publication_date": date(2023, 7, 19),
                "status": "PUBLISHED",
                "mrp": Decimal("420.00"),
                "copies_sold": 410,
                "royalty_earned": Decimal("8610.00"),
                "royalty_paid": Decimal("8610.00"),
                "royalty_pending": Decimal("0.00"),
                "print_partner": "Thomson Press",
                "available_on": ["Amazon", "Flipkart"],
            },
            {
                "book_id": "BK012",
                "title": "Loom of Destiny",
                "isbn": "978-93-91234-12-8",
                "genre": "Contemporary Fiction",
                "publication_date": date(2024, 3, 1),
                "status": "PUBLISHED",
                "mrp": Decimal("390.00"),
                "copies_sold": 75,
                "royalty_earned": Decimal("1462.50"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("1462.50"),
                "print_partner": "Thomson Press",
                "available_on": ["Amazon"],
            },
        ],
    },
    {
        "author_id": "AUTH006",
        "email": "amitav.roy@bookleaf.com",
        "full_name": "Amitav Roy",
        "pen_name": "Amitav Roy",
        "phone": "+91 98765 43215",
        "books": [
            {
                "book_id": "BK013",
                "title": "Shadows Over Sundarbans",
                "isbn": "978-93-91234-13-5",
                "genre": "Thriller",
                "publication_date": date(2023, 5, 25),
                "status": "PUBLISHED",
                "mrp": Decimal("450.00"),
                "copies_sold": 1850,
                "royalty_earned": Decimal("41625.00"),
                "royalty_paid": Decimal("35000.00"),
                "royalty_pending": Decimal("6625.00"),
                "print_partner": "Manipal Technologies",
                "available_on": ["Amazon", "Flipkart", "Kindle"],
            },
            {
                "book_id": "BK014",
                "title": "Tides of the Hooghly",
                "isbn": None,
                "genre": "Mystery",
                "publication_date": None,
                "status": "IN_PRODUCTION",
                "mrp": None,
                "copies_sold": 0,
                "royalty_earned": Decimal("0.00"),
                "royalty_paid": Decimal("0.00"),
                "royalty_pending": Decimal("0.00"),
                "print_partner": None,
                "available_on": [],
            },
        ],
    },
    {
        "author_id": "AUTH007",
        "email": "kavita.nair@bookleaf.com",
        "full_name": "Kavita Nair",
        "pen_name": "Kavita Nair",
        "phone": "+91 98765 43216",
        "books": [
            {
                "book_id": "BK015",
                "title": "Monsoon Rhythms",
                "isbn": "978-93-91234-15-9",
                "genre": "Poetry",
                "publication_date": date(2023, 8, 12),
                "status": "PUBLISHED",
                "mrp": Decimal("299.00"),
                "copies_sold": 240,
                "royalty_earned": Decimal("3588.00"),
                "royalty_paid": Decimal("3000.00"),
                "royalty_pending": Decimal("588.00"),
                "print_partner": "Replika Press",
                "available_on": ["Amazon"],
            },
        ],
    },
    {
        "author_id": "AUTH008",
        "email": "devendra.joshi@bookleaf.com",
        "full_name": "Devendra Joshi",
        "pen_name": "Devendra Joshi",
        "phone": "+91 98765 43217",
        "books": [
            {
                "book_id": "BK016",
                "title": "Himalayan Solitude",
                "isbn": "978-93-91234-16-6",
                "genre": "Travel Memoir",
                "publication_date": date(2023, 10, 30),
                "status": "PUBLISHED",
                "mrp": Decimal("499.00"),
                "copies_sold": 620,
                "royalty_earned": Decimal("15469.00"),
                "royalty_paid": Decimal("12000.00"),
                "royalty_pending": Decimal("3469.00"),
                "print_partner": "Replika Press",
                "available_on": ["Amazon", "Flipkart"],
            },
        ],
    },
    {
        "author_id": "AUTH009",
        "email": "meera.sen@bookleaf.com",
        "full_name": "Meera Sen",
        "pen_name": "Meera Sen",
        "phone": "+91 98765 43218",
        "books": [
            {
                "book_id": "BK017",
                "title": "Canvas of Calcutta",
                "isbn": "978-93-91234-17-3",
                "genre": "Art & Biography",
                "publication_date": date(2024, 2, 20),
                "status": "PUBLISHED",
                "mrp": Decimal("799.00"),
                "copies_sold": 480,
                "royalty_earned": Decimal("19176.00"),
                "royalty_paid": Decimal("15000.00"),
                "royalty_pending": Decimal("4176.00"),
                "print_partner": "Thomson Press",
                "available_on": ["Amazon", "Crossword", "Flipkart"],
            },
        ],
    },
    {
        "author_id": "AUTH010",
        "email": "arjun.kapoor@bookleaf.com",
        "full_name": "Arjun Kapoor",
        "pen_name": "Arjun Kapoor",
        "phone": "+91 98765 43219",
        "books": [
            {
                "book_id": "BK018",
                "title": "Gully to Glory",
                "isbn": "978-93-91234-18-0",
                "genre": "Sports Biography",
                "publication_date": date(2022, 12, 1),
                "status": "PUBLISHED",
                "mrp": Decimal("399.00"),
                "copies_sold": 3100,
                "royalty_earned": Decimal("61845.00"),
                "royalty_paid": Decimal("50000.00"),
                "royalty_pending": Decimal("11845.00"),
                "print_partner": "Manipal Technologies",
                "available_on": ["Amazon", "Flipkart", "Kindle", "Crossword"],
            },
        ],
    },
]


def seed_database():
    with Session(sync_engine) as session:
        print("Starting idempotent seed...")

        # 1. Ensure Admin User exists
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
            print(f"Admin user already exists: {ADMIN_EMAIL}")

        # 2. Seed Authors and Books
        authors_count = 0
        books_count = 0

        for a_data in AUTHORS_DATA:
            user = session.execute(select(User).where(User.email == a_data["email"])).scalar_one_or_none()
            if not user:
                user = User(
                    email=a_data["email"],
                    password_hash=get_password_hash(DEFAULT_AUTHOR_PASSWORD),
                    role="AUTHOR",
                    full_name=a_data["full_name"],
                    is_active=True,
                )
                session.add(user)
                session.flush()

            author = session.execute(select(Author).where(Author.author_id == a_data["author_id"])).scalar_one_or_none()
            
            # Calculate aggregate royalties
            total_earned = sum((b["royalty_earned"] for b in a_data["books"]), Decimal("0.00"))
            total_paid = sum((b["royalty_paid"] for b in a_data["books"]), Decimal("0.00"))
            total_pending = sum((b["royalty_pending"] for b in a_data["books"]), Decimal("0.00"))

            if not author:
                author = Author(
                    user_id=user.id,
                    author_id=a_data["author_id"],
                    pen_name=a_data["pen_name"],
                    phone=a_data["phone"],
                    total_royalties_earned=total_earned,
                    total_royalties_paid=total_paid,
                    total_royalties_pending=total_pending,
                )
                session.add(author)
                session.flush()
                authors_count += 1
            else:
                author.total_royalties_earned = total_earned
                author.total_royalties_paid = total_paid
                author.total_royalties_pending = total_pending

            # Seed books for author
            for b_data in a_data["books"]:
                book = session.execute(select(Book).where(Book.book_id == b_data["book_id"])).scalar_one_or_none()
                if not book:
                    book = Book(
                        book_id=b_data["book_id"],
                        author_id=author.id,
                        title=b_data["title"],
                        isbn=b_data["isbn"],
                        genre=b_data["genre"],
                        publication_date=b_data["publication_date"],
                        status=b_data["status"],
                        mrp=b_data["mrp"],
                        copies_sold=b_data["copies_sold"],
                        royalty_earned=b_data["royalty_earned"],
                        royalty_paid=b_data["royalty_paid"],
                        royalty_pending=b_data["royalty_pending"],
                        print_partner=b_data["print_partner"],
                        available_on=b_data["available_on"],
                    )
                    session.add(book)
                    books_count += 1
                else:
                    # Update book fields idempotently
                    book.title = b_data["title"]
                    book.isbn = b_data["isbn"]
                    book.status = b_data["status"]
                    book.mrp = b_data["mrp"]
                    book.copies_sold = b_data["copies_sold"]
                    book.royalty_earned = b_data["royalty_earned"]
                    book.royalty_paid = b_data["royalty_paid"]
                    book.royalty_pending = b_data["royalty_pending"]
                    book.print_partner = b_data["print_partner"]
                    book.available_on = b_data["available_on"]

        session.commit()

        # Verification count
        final_authors = session.execute(select(Author)).scalars().all()
        final_books = session.execute(select(Book)).scalars().all()
        print(f"Seed complete! Verified Authors: {len(final_authors)}, Verified Books: {len(final_books)}")
        assert len(final_authors) == 10, f"Expected 10 authors, got {len(final_authors)}"
        assert len(final_books) == 18, f"Expected 18 books, got {len(final_books)}"
        print("Idempotent seed verification passed successfully!")


if __name__ == "__main__":
    seed_database()

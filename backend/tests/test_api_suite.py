import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from scripts.seed import seed_database

# Ensure database is seeded before running tests
seed_database()


@pytest.mark.asyncio
async def test_health_and_readiness():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

        ready_res = await client.get("/api/v1/ready")
        assert ready_res.status_code == 200
        assert ready_res.json()["ready"] is True


@pytest.mark.asyncio
async def test_auth_login_author_and_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Author Priya login
        author_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "priya.sharma@bookleaf.com", "password": "Author@BookLeaf2026!"},
        )
        assert author_res.status_code == 200
        data = author_res.json()["data"]
        assert data["user"]["role"] == "AUTHOR"
        assert data["user"]["author_id"] == "AUTH001"
        assert "access_token" in data

        # Admin login
        admin_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bookleaf.com", "password": "Admin@BookLeaf2026!"},
        )
        assert admin_res.status_code == 200
        admin_data = admin_res.json()["data"]
        assert admin_data["user"]["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_author_books_and_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Login as Author 1 (Priya Sharma - AUTH001)
        res1 = await client.post(
            "/api/v1/auth/login",
            json={"email": "priya.sharma@bookleaf.com", "password": "Author@BookLeaf2026!"},
        )
        token1 = res1.json()["data"]["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Check Priya's books: she has 3 books (BK001, BK002, BK003)
        books_res = await client.get("/api/v1/author/books", headers=headers1)
        assert books_res.status_code == 200
        priya_books = books_res.json()["data"]
        assert len(priya_books) == 3
        book_ids = [b["book_id"] for b in priya_books]
        assert "BK001" in book_ids
        assert "BK002" in book_ids

        # 2. Login as Author 2 (Rohit Verma - AUTH002)
        res2 = await client.post(
            "/api/v1/auth/login",
            json={"email": "rohit.verma@bookleaf.com", "password": "Author@BookLeaf2026!"},
        )
        token2 = res2.json()["data"]["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Check Rohit's books
        rohit_books_res = await client.get("/api/v1/author/books", headers=headers2)
        assert rohit_books_res.status_code == 200
        rohit_books = rohit_books_res.json()["data"]
        assert len(rohit_books) == 3
        assert "BK004" in [b["book_id"] for b in rohit_books]

        # 3. IDOR Attack Test: Rohit attempts to access Priya's book (BK001) directly
        idor_res = await client.get("/api/v1/author/books/BK001", headers=headers2)
        # MUST BE 403 Forbidden!
        assert idor_res.status_code == 403
        assert idor_res.json()["error"]["code"] == "BOOK_NOT_ACCESSIBLE"


@pytest.mark.asyncio
async def test_ticket_creation_and_event_timeline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Priya creates a support ticket
        res1 = await client.post(
            "/api/v1/auth/login",
            json={"email": "priya.sharma@bookleaf.com", "password": "Author@BookLeaf2026!"},
        )
        headers1 = {"Authorization": f"Bearer {res1.json()['data']['access_token']}"}

        ticket_payload = {
            "bookId": "BK001",
            "subject": "Royalty for Whispers of the Ganges is pending",
            "description": "I see pending royalty of INR 8400 for Whispers of the Ganges. When will this be disbursed?",
        }
        create_res = await client.post("/api/v1/author/tickets", json=ticket_payload, headers=headers1)
        assert create_res.status_code == 201
        t_data = create_res.json()["data"]
        ticket_number = t_data["ticketNumber"]
        assert ticket_number.startswith("BL-")
        assert t_data["status"] == "OPEN"

        # Check author timeline
        timeline_res = await client.get("/api/v1/author/timeline", headers=headers1)
        assert timeline_res.status_code == 200
        events = timeline_res.json()["data"]
        assert any(e["event_type"] == "TICKET_CREATED" for e in events)


@pytest.mark.asyncio
async def test_admin_workspace_and_internal_note_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Login Priya (Author) and Admin
        a_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "priya.sharma@bookleaf.com", "password": "Author@BookLeaf2026!"},
        )
        author_token = a_res.json()["data"]["access_token"]
        author_headers = {"Authorization": f"Bearer {author_token}"}

        adm_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bookleaf.com", "password": "Admin@BookLeaf2026!"},
        )
        admin_token = adm_res.json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Create ticket by Priya
        ticket_res = await client.post(
            "/api/v1/author/tickets",
            json={"subject": "Cover print defect test", "description": "Front cover printing alignment issue."},
            headers=author_headers,
        )
        ticket_number = ticket_res.json()["data"]["ticketNumber"]

        # Admin adds internal note
        note_res = await client.post(
            f"/api/v1/admin/tickets/{ticket_number}/internal-notes",
            json={"note": "Confidential internal note: Contacted Replika Press regarding print run batch."},
            headers=admin_headers,
        )
        assert note_res.status_code == 200

        # Verify: Admin CAN see the internal note in workspace
        adm_workspace_res = await client.get(f"/api/v1/admin/tickets/{ticket_number}", headers=admin_headers)
        assert adm_workspace_res.status_code == 200
        assert len(adm_workspace_res.json()["data"]["internalNotes"]) >= 1

        # CRITICAL TEST: Author CANNOT see internal notes!
        author_view_res = await client.get(f"/api/v1/author/tickets/{ticket_number}", headers=author_headers)
        assert author_view_res.status_code == 200
        assert "internalNotes" not in author_view_res.json()["data"]

        # Author timeline must NEVER contain INTERNAL_NOTE_ADDED
        author_tl_res = await client.get("/api/v1/author/timeline", headers=author_headers)
        assert all(e["event_type"] != "INTERNAL_NOTE_ADDED" for e in author_tl_res.json()["data"])


@pytest.mark.asyncio
async def test_duplicate_ticket_detection_and_linking():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Priya creates first ticket
        a_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "priya.sharma@bookleaf.com", "password": "Author@BookLeaf2026!"},
        )
        author_headers = {"Authorization": f"Bearer {a_res.json()['data']['access_token']}"}

        adm_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@bookleaf.com", "password": "Admin@BookLeaf2026!"},
        )
        admin_headers = {"Authorization": f"Bearer {adm_res.json()['data']['access_token']}"}

        t1_res = await client.post(
            "/api/v1/author/tickets",
            json={
                "bookId": "BK002",
                "subject": "Royalty for The Saffron Diaries has not arrived",
                "description": "Waiting for pending royalty of INR 4350 for The Saffron Diaries.",
            },
            headers=author_headers,
        )
        t1_num = t1_res.json()["data"]["ticketNumber"]

        # Priya creates second similar ticket for same book
        t2_res = await client.post(
            "/api/v1/author/tickets",
            json={
                "bookId": "BK002",
                "subject": "Still waiting for The Saffron Diaries royalty payout",
                "description": "Any update on the royalty payment for The Saffron Diaries? Still haven't received it.",
            },
            headers=author_headers,
        )
        t2_num = t2_res.json()["data"]["ticketNumber"]

        # Check duplicate relationships API from admin
        dup_res = await client.get(f"/api/v1/admin/tickets/{t2_num}/relationships", headers=admin_headers)
        assert dup_res.status_code == 200
        candidates = dup_res.json()["data"]["candidates"]
        cand_nums = [c.get("ticketNumber") or c.get("ticket_number") for c in candidates]
        assert t1_num in cand_nums
        target_cand = next(c for c in candidates if (c.get("ticketNumber") or c.get("ticket_number")) == t1_num)
        assert target_cand["similarity"] >= 0.50
        assert target_cand["signals"]["same_author"] is True
        assert target_cand["signals"]["same_book"] is True

        # Admin links duplicate
        link_res = await client.post(
            f"/api/v1/admin/tickets/{t2_num}/link-duplicate",
            json={"target_ticket_id": t1_num},
            headers=admin_headers,
        )
        assert link_res.status_code == 200
        assert "Linked" in link_res.json()["message"]

        # Prevent duplicate link twice (unique constraint)
        rel_twice_res = await client.post(
            f"/api/v1/admin/tickets/{t2_num}/link-duplicate",
            json={"target_ticket_id": t1_num},
            headers=admin_headers,
        )
        assert rel_twice_res.status_code == 409
        assert rel_twice_res.json()["error"]["code"] == "DUPLICATE_RELATION_EXISTS"

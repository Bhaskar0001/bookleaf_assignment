# BookLeaf Author Support & Communication Portal

A production-grade, modular monolithic internal support and operations platform for **BookLeaf Publishing**.

The platform enables authors to access their publication catalog, inspect royalty breakdowns, submit structured support requests, and interact via a two-way communication timeline. For publishing operations teams, it provides a unified single-screen ticket workspace, table-first queue with multi-dimensional filtering, deterministic duplicate detection and linking, privileged internal notes, and AI-assisted response drafting strictly bound to verified BookLeaf publishing guidelines.

> 📖 **Cloning on a new machine?** Follow the step-by-step [Clone & Setup Guide](CLONE_SETUP_GUIDE.md) for prerequisite installation, database setup, environment configuration, and running with or without Docker.

---

## Key Differentiating Features

1. **Author Communication Timeline (`ticket_events` Backbone)**:
   - The operational history is never assembled as an afterthought or reconstructed by replaying disparate tables.
   - Every state change, assignment, author message, admin response, duplicate link, or status transition mutates current state and appends an immutable event to `ticket_events` within the **same atomic database transaction**.
   - Powers both the Author Timeline and the Admin Audit Trail.

2. **Deterministic Duplicate Detection (Zero LLM Dependency)**:
   - Evaluates incoming tickets against existing author issues using scoped text normalization, Jaccard token similarity, character trigrams, and domain heuristics.
   - Outputs explainable candidate matches with score breakdowns (`same_author`, `same_book`, `subject_similarity`, `description_similarity`).
   - Human-in-the-loop: Operations administrators review and explicitly confirm or dismiss duplicate candidates. Tickets are never silently deleted or merged.

3. **Strict Author Data Isolation & Privileged Internal Notes**:
   - Author identity is derived strictly from the verified JWT principal (`user_id -> author_id`). Client-provided `authorId` parameters are never trusted.
   - Resource-level authorization prevents authors from viewing or mutating other authors' books, tickets, or timelines.
   - Internal notes live in an isolated table (`ticket_internal_notes`) and are filtered out at the SQL query/DTO layer from all author endpoints.

4. **Resilient AI Provider Boundary**:
   - Support assistance (classification, priority assignment, and response drafting) is placed behind a strict provider abstraction (`AIProvider`).
   - Draft generation is strictly grounded in BookLeaf operational policies and never invents payment dates or refunds.
   - If the AI provider is unconfigured or unreachable, ticket operations and core workflows continue running smoothly with deterministic rule fallbacks.

5. **Clean Enterprise UI (No AI Gimmicks)**:
   - Crisp light theme, white cards, subtle borders, high legibility, compact metric cards, and responsive tables.
   - Zero AI badges, robot graphics, glowing gradients, chatbot widgets, or fake dashboards.

---

## Tech Stack

- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL 16+
- **Frontend**: React 18, TypeScript, Vite, Lucide Icons
- **Real-Time**: FastAPI WebSockets
- **Caching & Queue**: Redis, Celery
- **AI Assist**: Google Gemini API via server-side `AIProvider` abstraction with deterministic local fallback
- **Testing**: Pytest, Pytest-Asyncio, HTTPX

---

## Seed Dataset (10 Authors, 18 Books)

The system seeds the exact authoritative dataset of 10 authors and 18 books:
- Published books with active sales & pending royalties.
- Books still in production (`status = 'IN_PRODUCTION'`, `isbn = null`, `mrp = null`, `publication_date = null`).
- Zero royalty payouts (`royalty_earned = 0.00`, `royalty_paid = 0.00`).
- Various print partners (`Replika Press`, `Thomson Press`, `Manipal Technologies`) and distribution platforms (`Amazon`, `Flipkart`, `Kindle`, `Crossword`).

### Pre-Configured Test Accounts

| Role | Account Name | Email | Password |
| :--- | :--- | :--- | :--- |
| **Admin** | Operations Admin | `admin@bookleaf.com` | `Admin@BookLeaf2026!` |
| **Author** | Priya Sharma (`AUTH001`) | `priya.sharma@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Rohit Verma (`AUTH002`) | `rohit.verma@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Ananya Iyer (`AUTH003`) | `ananya.iyer@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Vikram Malhotra (`AUTH004`) | `vikram.malhotra@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Sneha Patel (`AUTH005`) | `sneha.patel@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Amitav Roy (`AUTH006`) | `amitav.roy@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Kavita Nair (`AUTH007`) | `kavita.nair@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Devendra Joshi (`AUTH008`) | `devendra.joshi@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Meera Sen (`AUTH009`) | `meera.sen@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Arjun Kapoor (`AUTH010`) | `arjun.kapoor@bookleaf.com` | `Author@BookLeaf2026!` |

---

## Local Development Setup

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- PostgreSQL running locally or in Docker

### 2. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows
.venv\Scripts\activate
# On Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Run idempotent seed
python scripts/seed.py

# Start API server
uvicorn app.main:app --reload --port 8000
```
Interactive OpenAPI documentation will be available at: `http://localhost:8000/docs`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
The React portal will be accessible at: `http://localhost:5173`

---

## Running Automated Tests

Run the full automated test suite verifying health, authentication, IDOR author isolation, event creation, internal notes privacy, and duplicate detection:
```bash
# From workspace root
backend\.venv\Scripts\pytest backend\tests -v
```

---

## Docker Deployment

To launch the complete platform using Docker Compose:
```bash
docker-compose up --build
```
- Frontend UI: `http://localhost:3000`
- FastAPI Documentation: `http://localhost:8000/docs`

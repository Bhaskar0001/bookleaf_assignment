# BookLeaf Author Support Portal — Clone & Setup Guide

This guide provides instructions for setting up the **BookLeaf Author Support & Communication Portal** on a new machine after cloning from GitHub.

---

## 1. System Prerequisites

Ensure the following tools are installed on your host system:
- **Git** (`git --version`)
- **Python 3.12+** (`python --version`)
- **Node.js 18+ & npm** (`node --version`, `npm --version`)
- **PostgreSQL 16+** (`psql --version`)
- **Redis** *(Optional for Celery worker; system gracefully falls back to async background jobs if Redis is not running)*

---

## 2. Quick Setup with Docker Compose (Recommended)

If Docker and Docker Compose are installed:

```bash
# 1. Clone the repository
git clone https://github.com/Bhaskar0001/bookleaf_assignment.git
cd bookleaf_assignment

# 2. Copy the environment file
cp .env.example .env

# 3. Build and launch all services (PostgreSQL, Redis, Backend, Worker, Frontend)
docker-compose up --build
```

The portal will be accessible at:
- **Frontend UI**: [http://localhost:3000](http://localhost:3000) (or port configured in compose)
- **FastAPI API & OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 3. Manual Local Setup (Step-by-Step)

### Step 3.1: Clone and Configure Environment

```bash
git clone https://github.com/Bhaskar0001/bookleaf_assignment.git
cd bookleaf_assignment

# Copy the sample environment configuration
cp .env.example .env
```

Review `.env` and verify your PostgreSQL port and credentials:
```ini
APP_ENV=development
LOG_LEVEL=INFO
PORT=8000

# Set your PostgreSQL connection string:
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/bookleaf_db
DATABASE_SYNC_URL=postgresql://postgres:postgres@localhost:5432/bookleaf_db

# Security & Secrets:
JWT_SECRET=supersecret_jwt_key_bookleaf_production_2026_xyz123!
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# AI Provider (Optional: local deterministic fallback is active if key is empty):
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# CORS:
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
```

---

### Step 3.2: Database Preparation

Make sure PostgreSQL is running, then create the database:

```sql
-- In PostgreSQL terminal (psql):
CREATE DATABASE bookleaf_db;
\c bookleaf_db;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

---

### Step 3.3: Backend Setup

```bash
# Navigate to the backend directory
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install all backend dependencies
pip install -r requirements.txt

# Run database migrations to create all 11 tables
alembic upgrade head

# Run idempotent seed script (Seeds 10 authors, 18 books, and admin)
python scripts/seed.py

# Start the FastAPI backend server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Step 3.4: Frontend Setup

Open a new terminal window:

```bash
# Navigate to the frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

Open your browser to: **[http://127.0.0.1:5173](http://127.0.0.1:5173)**.

---

### Step 3.5: (Optional) Celery Worker

If Redis is running and you want to run Celery in a dedicated terminal:

```bash
cd backend
# With virtual environment activated:
celery -A app.workers.celery_app worker --loglevel=info
```
*(If Celery is not started, background AI tasks run via non-blocking asyncio background runners without interruptions.)*

---

## 4. Running the Test Suite

To verify the installation:

```bash
cd backend
# With .venv activated:
pytest tests -v
```

All 6 test suites will run and pass:
1. `test_health_and_readiness`
2. `test_auth_login_author_and_admin`
3. `test_author_books_and_isolation` (Row-level IDOR check)
4. `test_ticket_creation_and_event_timeline` (Atomic `ticket_events`)
5. `test_admin_workspace_and_internal_note_isolation` (Confidentiality)
6. `test_duplicate_ticket_detection_and_linking` (Deterministic signals)

---

## 5. Seeded Credentials for Testing

Use the **One-Click Demo Account Switcher** in the UI or manually log in with these credentials:

| Role | Name / Identifier | Email | Password |
| :--- | :--- | :--- | :--- |
| **Admin** | Operations Desk | `admin@bookleaf.com` | `Admin@BookLeaf2026!` |
| **Author** | Priya Sharma (`AUTH001`) | `priya.sharma@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Rohit Verma (`AUTH002`) | `rohit.verma@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Ananya Iyer (`AUTH003`) | `ananya.iyer@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Vikram Malhotra (`AUTH004`) | `vikram.malhotra@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Sneha Patel (`AUTH005`) | `sneha.patel@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Amitav Ghosh (`AUTH006`) | `amitav.ghosh@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Kavita Krishnan (`AUTH007`) | `kavita.krishnan@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Devdutt Pattanaik (`AUTH008`) | `devdutt.pattanaik@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Arundhati Roy (`AUTH009`) | `arundhati.roy@bookleaf.com` | `Author@BookLeaf2026!` |
| **Author** | Chetan Bhagat (`AUTH010`) | `chetan.bhagat@bookleaf.com` | `Author@BookLeaf2026!` |

---

## 6. What Stays Out of Git (`.gitignore`)

The repository is configured to strictly exclude:
- `pgdata/` — Local PostgreSQL database clusters and binary data files.
- `.env` — Local environment secrets and passwords.
- `.venv/` — Local Python virtual environments.
- `node_modules/` & `dist/` — Node packages and compiled bundles.
- `__pycache__/` & `.pytest_cache/` — Python cache and test artifacts.

All required configuration templates (`.env.example`), migration histories (`alembic/`), and seed scripts are versioned in Git.

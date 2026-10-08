# Architecture & System Design

## 1. System Overview

The BookLeaf Author Support & Communication Portal is designed as a **Modular Monolith** rather than distributed microservices to avoid unnecessary network latency, distributed transaction complexity, and DevOps overhead.

```
┌────────────────────────────────────────────────────────┐
│               React + TypeScript Client                │
│       Author Portal (Dashboard, Catalog, Timeline)     │
│       Admin Workspace (Queue, Single-Screen Desk)      │
└───────────────────────────┬────────────────────────────┘
                            │ REST / WebSocket
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Monolith                     │
│  ┌────────────┬─────────────┬─────────────┬──────────┐ │
│  │   Auth     │   Authors   │    Books    │  Tickets │ │
│  ├────────────┼─────────────┼─────────────┼──────────┤ │
│  │  Timeline  │Relationship │SupportAssist│ Admin    │ │
│  └────────────┴─────────────┴─────────────┴──────────┘ │
└─────────────┬───────────────────────────┬──────────────┘
              │                           │
              ▼                           ▼
   PostgreSQL 16+                   Redis + Celery
   - Current State                  - Background triage
   - Append-only ticket_events      - Transient cache
   - ticket_relationships           - Rate limits
```

---

## 2. The `ticket_events` Backbone

Unlike systems that attempt to construct communication history from message tables and log files after the fact:
- Current state tables (`tickets`, `ticket_messages`, `ticket_internal_notes`) allow sub-millisecond querying, indexing, and sorting for operational queues.
- `ticket_events` is an immutable, append-only ledger of every meaningful business event:
  - `TICKET_CREATED`
  - `MESSAGE_ADDED`
  - `STATUS_CHANGED`
  - `CATEGORY_CHANGED`
  - `PRIORITY_CHANGED`
  - `ASSIGNED`
  - `INTERNAL_NOTE_ADDED`
  - `DUPLICATE_DETECTED`
  - `DUPLICATE_LINKED`
  - `DUPLICATE_UNLINKED`
  - `RESPONSE_SENT`
  - `RESOLVED`
  - `CLOSED`
- **Transactional Invariance**: Every state mutation and its corresponding event insertion execute inside the same database transaction.
- **Real-Time Coupling**: WebSockets emit notifications only after the transaction successfully commits.

---

## 3. Deterministic Duplicate Detection Pipeline

Duplicate detection runs completely independently of external AI services:

```
Incoming Ticket
      │
      ▼
Scoped by Author ID & Book ID / General Account
      │
      ▼
Retrieve Active or Recently Resolved Tickets
      │
      ▼
Text Normalization (lowercase, punctuation strip, stop-word removal)
      │
      ▼
Token Jaccard Similarity (60%) + Character Trigrams (40%)
      │
      ▼
Multi-Signal Evaluation (same_author, same_book, status weights, recency decay)
      │
      ▼
Ranked Candidate Matches (> 0.40 score threshold)
      │
      ▼
Admin Human Confirmation (Link Duplicate / Dismiss)
```

The system suggests candidates; only a human operator can confirm links. Both tickets preserve their distinct message threads and timelines.

---

## 4. AI Provider Boundary & Safety Guardrails

- `AIProvider` is an abstract interface isolating business logic from external SDKs.
- `GeminiProvider` connects to Google Gemini models using server-side keys.
- `MockFallbackProvider` guarantees 100% platform availability if external APIs fail.
- **Safety Policy**: Response drafting strictly loads verified BookLeaf publishing policies (royalties, ISBN, printing, distribution) and is explicitly constrained from inventing payment dates or financial promises.

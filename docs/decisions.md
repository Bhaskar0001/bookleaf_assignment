# Architectural Decisions (ADR)

## 1. Modular Monolith vs Microservices
- **Decision**: Build BookLeaf as a clean modular monolith in Python/FastAPI with explicit domain boundaries.
- **Rationale**: The product domain is coherent and deeply relational. Splitting into independent microservices would introduce distributed transactions, cross-service auth overhead, latency, and operational fragility without business justification.

## 2. PostgreSQL as the Authoritative Store
- **Decision**: Store both current state and the append-only `ticket_events` log in PostgreSQL.
- **Rationale**: Guarantees atomic ACID transactions when modifying ticket state and inserting audit events. Relational foreign keys prevent orphan records.

## 3. Append-Only `ticket_events` instead of Full Event Sourcing
- **Decision**: Maintain current-state tables (`tickets`) alongside an immutable `ticket_events` history.
- **Rationale**: Full event sourcing requires replaying streams or managing complex projections for basic administrative queues. Current state + append-only events delivers fast queries and complete historical auditability.

## 4. Deterministic Duplicate Detection vs LLM Embeddings
- **Decision**: Use text normalization, character trigrams, and Jaccard token similarity for duplicate detection.
- **Rationale**: Deterministic algorithms are 100% explainable, cost-free, have zero external downtime risk, and execute in under 10 milliseconds.

## 5. Assistive AI Provider Boundary
- **Decision**: Isolate Google Gemini behind an `AIProvider` interface with automatic local fallback.
- **Rationale**: Prevents vendor lock-in and protects core publishing operations from third-party API outages or rate limits.

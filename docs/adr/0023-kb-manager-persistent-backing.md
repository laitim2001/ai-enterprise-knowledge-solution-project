# ADR-0023: KB Manager + users_repo persistent backing — Postgres via psycopg

**Date**: 2026-05-10
**Status**: Accepted
**Approver**: Chris (Tech Lead / architecture decision owner — AskUserQuestion 2026-05-10 selected "Postgres via psycopg")

## Context

`backend/kb_management/storage.py` defines a `KBStorageBackend` Protocol with a single implementation, `InMemoryKBBackend` ("Process-local KB store. W1 development only — not durable across restart"). `backend/api/auth/users_repo.py` similarly holds registered users in process memory. The Protocol docstring already anticipates a swappable backend ("W2 D1 will add an Azure AI Search-backed implementation that satisfies the same Protocol"); architecture.md v6 §3.4 multi-KB notes and session-start.md §3 C02 status both flag "CO18 persistent backing — Beta hardening W17+".

Operational consequence today: every backend restart wipes all KBs and all registered users. During W17's own browser-smoke work the KB had to be re-`POST /kb`'d after each `uvicorn` restart. For Beta, registered users vanishing on a deploy is a non-starter.

The decision is *which* persistent backend. `audit-W15-d5-vs-spec.md` §7 pre-reserved an ADR slot ("0023 KB Manager persistent backing W17+"). Candidates considered: stdlib `sqlite3`, `aiosqlite`, Postgres (`psycopg` / `asyncpg`), Azure Cosmos DB, or "defer Tier 2 + add a dev seed script".

## Decision

**Use PostgreSQL via `psycopg` (psycopg 3, `psycopg[binary]`), reusing the docker-compose `postgres` service with a dedicated `ekp` database, behind the existing `KBStorageBackend` Protocol (+ an analogous Postgres path in `users_repo`). The in-memory backend is preserved as the no-`DATABASE_URL` fallback (local / CI).**

Concretely:

1. **Dependency**: add `psycopg[binary]` to `backend/pyproject.toml`. (`psycopg` 3 supports async natively — `AsyncConnection` / `AsyncConnectionPool` — matching CLAUDE.md §3.1 "async by default".) `sqlalchemy` is already installed transitively but **not** used here — a 2-table schema does not warrant an ORM or a migration framework (Alembic would be another dep); raw parameterised SQL via `psycopg` is the surgical choice per Karpathy §1.2.
2. **Infrastructure**: `infrastructure/docker-compose.yml` `postgres` service initialises a dedicated `ekp` database (separate from the Langfuse DB on the same instance — via a small `docker-entrypoint-initdb.d` script or a `POSTGRES_MULTIPLE_DATABASES` pattern). `docs/setup.md §4.2` table + `.env` template updated.
3. **Config**: `backend/storage/settings.py` gains `database_url: str = ""` (`postgresql://...`). Empty → in-memory fallback (local dev / CI keep the W1 behaviour with zero infra). `.env.example` adds a commented `DATABASE_URL=`.
4. **`PostgresKBBackend`** (`backend/kb_management/postgres_backend.py`, NEW) — implements the full `KBStorageBackend` Protocol (`create` / `list_all` / `get` / `delete` / `update_config` / `update_metadata`); `CREATE TABLE IF NOT EXISTS knowledge_bases (kb_id TEXT PRIMARY KEY, name TEXT, description TEXT, config JSONB, total_documents INT, total_chunks INT, total_screenshots INT, failed_documents JSONB, last_indexed_at TIMESTAMPTZ, storage_size_mb DOUBLE PRECISION)` on first connect; `KbStatus` ⇄ row mapping; raises the existing `KBNotFoundError` / `KBAlreadyExistsError`.
5. **users_repo Postgres path** — same public interface; `CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE, display_name TEXT, password_hash TEXT, email_verified BOOLEAN, verification_code TEXT, verification_expires_at TIMESTAMPTZ, created_at TIMESTAMPTZ)`.
6. **Wiring**: a `make_kb_backend(settings)` factory (mirroring `make_reranker(settings)`) returns `PostgresKBBackend` when `settings.database_url` is set, else `InMemoryKBBackend`; the FastAPI lifespan opens/closes the connection pool; `get_kb_service()` + the users-repo factory consume it. **No route or service call-site changes** — the Protocol contract holds (this is the swap point the Protocol was designed for).

This is an **H1 storage-layout change** (new durable storage backend) **and an H2 new-dependency** (`psycopg[binary]`) — hence this ADR. It does **not** change the multi-KB index-naming convention (ADR-0005 / ADR-0018), the Azure AI Search index schema, or the blob path convention — only where KB *metadata* and *user records* live.

## Alternatives Considered

- **stdlib `sqlite3` (zero new dep)** — sync; would need `asyncio.to_thread` wrappers; file-based; zero infra. Was the AI recommendation for footprint. **Rejected by the approver in favour of Postgres** — Postgres is already running in docker-compose (Langfuse), is production-grade, supports concurrent writers properly, and matches where a real Beta deploy would land (Azure Database for PostgreSQL) without a later SQLite→Postgres migration.
- **`aiosqlite` (small async SQLite driver)** — cleanest async SQLite; but still a new dep with the same "migrate to Postgres later" debt; rejected for the same reason as stdlib sqlite3.
- **Azure Cosmos DB** — managed, scales; but overkill for ≤ a few dozen KBs + a Beta-cohort user list, adds an Azure dependency that ties into the Track A cred blocker, and the document model is a poor fit for the relational `KbStatus`/`users` shapes. Tier 2 multi-tenancy could revisit.
- **SQLAlchemy ORM (+ Alembic migrations)** — `sqlalchemy` is already installed (transitive), but a 2-table schema doesn't justify an ORM layer + a migration framework dep; raw `psycopg` SQL with `CREATE TABLE IF NOT EXISTS` is simpler and sufficient for Tier 1. Tier 2 can adopt ORM/migrations if the schema grows.
- **Defer to Tier 2 + add `scripts/seed_dev_kb.py`** — the "do nothing" option; keeps the restart-wipes-everything problem; the seed script helps dev but doesn't help Beta. Rejected — the approver chose to do the persistence now.

## Consequences

- **Positive**: KBs + registered users survive restarts/deploys (closes CO18); production-shaped storage (Beta deploy → Azure Database for PostgreSQL drop-in via `DATABASE_URL`); the Protocol-based swap means no churn in routes/services; in-memory fallback keeps local dev + CI zero-infra; raw-SQL DAL is small and auditable.
- **Negative**: new dependency `psycopg[binary]` (vector for an R8 corp-proxy block — see Risks); two new modules + a docker-compose init script; backend tests gain a Postgres-path branch (mitigated by a skip-if-no-`DATABASE_URL` marker matching the existing Azure-dependent test skip pattern); a `DATABASE_URL` env var is now part of the deploy contract; the dev workflow gains a `docker compose up` step if you want persistence locally (still optional — empty `DATABASE_URL` = in-memory).
- **Neutral**: schema is intentionally minimal (JSONB for `config` + `failed_documents` rather than normalised child tables — Tier 1 read/write patterns are key-by-`kb_id` / list-all, no relational queries); migration tooling (Alembic) deferred Tier 2; the Azure AI Search index / blob conventions are untouched.

## Implementation Deliverables

Tracked in `docs/01-planning/W17-beta-hardening/{plan,checklist}.md` **F1** (+ **F0.2** for this ADR). Status appended at W17 closeout.

- [ ] F0.2 — this ADR landed `Accepted`; README index updated
- [ ] F1.1 — `psycopg[binary]` added to `pyproject.toml`; `uv.lock` regenerated
- [ ] F1.2 — docker-compose `ekp` database init; `setup.md §4.2` updated
- [ ] F1.3 — `settings.database_url`; `.env.example` `DATABASE_URL=`; empty → in-memory fallback
- [ ] F1.4 — `PostgresKBBackend` satisfies `KBStorageBackend` Protocol; `CREATE TABLE IF NOT EXISTS`; `KbStatus` ⇄ row; existing exception classes
- [ ] F1.5 — `users_repo` Postgres path; `users` table; in-memory fallback preserved
- [ ] F1.6 — `make_kb_backend(settings)` factory + users-repo factory; lifespan pool; no route/service call-site change
- [ ] F1.7 — `backend/tests/test_kb_postgres_backend.py` + users-repo Postgres-path tests (skip-if-no-DB); in-memory path tests pass; total ≥ 593 + new
- [ ] F1.8 — `architecture.md` §3.4 + `COMPONENT_CATALOG.md` C02 status note (in-memory → Postgres-backed); CO18 → CLOSED

## References

- `backend/kb_management/storage.py` — `KBStorageBackend` Protocol + `InMemoryKBBackend` (the swap point this ADR uses)
- `backend/kb_management/service.py` — `KBService` (backend injected — no call-site change)
- `backend/api/auth/users_repo.py` — analogous user-store persistence
- `architecture.md` v6 §3.4 — multi-KB + storage backend swap point
- ADR-0005 / ADR-0018 — multi-KB index-naming convention (unchanged by this ADR)
- `docs/02-architecture/audit-W15-d5-vs-spec.md` §7 — pre-reserved ADR slot "0023 KB Manager persistent backing W17+"
- `docs/01-planning/W17-beta-hardening/plan.md` §2 F1
- session-start.md §11 carry-over `CO18`
- `infrastructure/docker-compose.yml`, `docs/setup.md` §4.2

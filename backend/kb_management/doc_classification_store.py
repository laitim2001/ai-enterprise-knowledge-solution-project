"""Per-document security-classification storage (W90 P2.3 / ADR-0066 DG1).

Stores a doc's classification (`internal` / `restricted`) keyed by ``(kb_id, doc_id)``.
Mirrors `doc_profile_store.py` / `doc_config_store.py`: a Postgres table when
``settings.database_url`` is set, else a process-local in-memory dict. ``psycopg`` is
imported lazily inside the Postgres impl so an unset ``DATABASE_URL`` never touches it.

Classification is a THIRD per-doc concern, distinct from the content-format profile
(`doc_profile_store`, a system-detected fact) and the retrieval-tuning `DocConfig`
(`doc_config_store`, user-tunable knobs) — it's a security control, so it lives in its
OWN store rather than folding into either. Only the EXCEPTIONS are persisted: a doc with
no row defaults to `internal` (the index stamp default), so the store records only docs
that have been tagged `restricted` (or explicitly reverted to `internal`).

`_run_ingest_pipeline` reads this store at ingest/reindex/backfill to re-stamp every
emitted chunk's `classification` (so a restricted doc survives re-ingest); the
`PATCH /kb/{kb_id}/docs/{doc_id}/classification` admin endpoint writes it + merge-restamps
the live index in one shot (no re-ingest). ``doc_id`` is a free-form key (docs live only
in the search index, no documents table), same as the sibling stores.

Schema (Postgres):
    document_classifications(kb_id TEXT, doc_id TEXT, classification TEXT,
                             PRIMARY KEY(kb_id, doc_id))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import psycopg
    from psycopg.rows import DictRow

    from storage.settings import Settings


class DocClassificationStore(Protocol):
    """Per-document classification CRUD interface. Implementations must be async-safe."""

    async def get(self, kb_id: str, doc_id: str) -> str | None:
        """Return the stored classification for ``(kb_id, doc_id)`` or ``None``.

        ``None`` = no row = default `internal` (the caller / ingest stamp applies the
        default, so the store never has to materialise it).
        """
        ...

    async def upsert(self, kb_id: str, doc_id: str, classification: str) -> str:
        """Insert or replace the per-doc classification; returns the stored value."""
        ...

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        """Delete the per-doc classification (revert to default); ``True`` if a row existed.

        Idempotent — deleting an absent classification is not an error.
        """
        ...

    async def list_for_kb(self, kb_id: str) -> dict[str, str]:
        """Return ``{doc_id: classification}`` for every tagged doc under ``kb_id``."""
        ...


class InMemoryDocClassificationStore:
    """Process-local per-doc classification store — local dev / CI default.

    Satisfies the `DocClassificationStore` Protocol. Backed by a nested dict
    ``{kb_id: {doc_id: classification}}``. Lost on restart (same trade-off as the
    in-memory KB / doc-config / doc-profile backends before Postgres persistence).
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, str]] = {}

    async def get(self, kb_id: str, doc_id: str) -> str | None:
        return self._store.get(kb_id, {}).get(doc_id)

    async def upsert(self, kb_id: str, doc_id: str, classification: str) -> str:
        self._store.setdefault(kb_id, {})[doc_id] = classification
        return classification

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        kb = self._store.get(kb_id)
        if kb is None or doc_id not in kb:
            return False
        del kb[doc_id]
        if not kb:  # drop the empty kb bucket
            del self._store[kb_id]
        return True

    async def list_for_kb(self, kb_id: str) -> dict[str, str]:
        # Copy so callers can't mutate the live store.
        return dict(self._store.get(kb_id, {}))


_TABLE = "document_classifications"

_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    kb_id          TEXT NOT NULL,
    doc_id         TEXT NOT NULL,
    classification TEXT NOT NULL,
    PRIMARY KEY (kb_id, doc_id)
)
"""


class PostgresDocClassificationStore:
    """Per-doc classification CRUD backed by a Postgres table — satisfies the Protocol.

    Connection-per-op via psycopg 3 async (same rationale as `PostgresDocProfileStore`:
    classification ops are infrequent + off the query hot path; ingest reads one row).
    ``CREATE TABLE IF NOT EXISTS`` runs on every connect — idempotent, microseconds
    when present.
    """

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def _connect(self) -> psycopg.AsyncConnection[DictRow]:
        import psycopg
        from psycopg.rows import dict_row

        conn = await psycopg.AsyncConnection.connect(
            self._dsn,
            autocommit=True,
            row_factory=dict_row,
        )
        async with conn.cursor() as cur:
            await cur.execute(_CREATE_TABLE)
        return conn

    async def get(self, kb_id: str, doc_id: str) -> str | None:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"SELECT classification FROM {_TABLE} WHERE kb_id = %s AND doc_id = %s",
                (kb_id, doc_id),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return str(row["classification"])

    async def upsert(self, kb_id: str, doc_id: str, classification: str) -> str:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"""
                INSERT INTO {_TABLE} (kb_id, doc_id, classification)
                VALUES (%s, %s, %s)
                ON CONFLICT (kb_id, doc_id) DO UPDATE SET classification = EXCLUDED.classification
                """,
                (kb_id, doc_id, classification),
            )
        return classification

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"DELETE FROM {_TABLE} WHERE kb_id = %s AND doc_id = %s",
                (kb_id, doc_id),
            )
            return cur.rowcount > 0

    async def list_for_kb(self, kb_id: str) -> dict[str, str]:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"SELECT doc_id, classification FROM {_TABLE} WHERE kb_id = %s ORDER BY doc_id",
                (kb_id,),
            )
            rows = await cur.fetchall()
        return {r["doc_id"]: str(r["classification"]) for r in rows}


def make_doc_classification_store(settings: Settings) -> DocClassificationStore:
    """Return a Postgres-backed store when ``database_url`` is set, else in-memory.

    Mirrors `make_doc_profile_store` — lazy psycopg import inside the Postgres branch
    so an unset ``DATABASE_URL`` never touches the driver.
    """
    if settings.database_url:
        return PostgresDocClassificationStore(settings.database_url)
    return InMemoryDocClassificationStore()

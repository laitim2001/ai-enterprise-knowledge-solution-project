"""Per-document config storage (W57 / ADR-0050 — platform P2a / Gap A).

Stores the per-DOCUMENT `DocConfig` overlay keyed by ``(kb_id, doc_id)``. Kept in
a DEDICATED store (not folded into the `KBStorageBackend` KB-CRUD Protocol) so the
per-doc config concern stays isolated and the KB record schema is untouched.

Mirrors the `kb_management.factory.make_kb_backend` shape (ADR-0023): a Postgres
table when ``settings.database_url`` is set, else a process-local in-memory dict
(local dev / CI unchanged). ``psycopg`` is imported lazily inside the Postgres impl
so an unset ``DATABASE_URL`` never touches it.

``doc_id`` is a FREE-FORM key in the MVP — there is no documents persistence table
(documents live only in the search index), so the store does NOT enforce a foreign
key against existing docs. Orphan rows (config for a deleted doc) are surfaced by
``list_for_kb`` + the P2b UI, not blocked here (logged as W57 plan R2).

Schema (Postgres):
    document_configs(kb_id TEXT, doc_id TEXT, config JSONB, PRIMARY KEY(kb_id, doc_id))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from api.schemas.doc_config import DocConfig

if TYPE_CHECKING:
    import psycopg
    from psycopg.rows import DictRow

    from storage.settings import Settings


class DocConfigStore(Protocol):
    """Per-document config CRUD interface. Implementations must be async-safe."""

    async def get(self, kb_id: str, doc_id: str) -> DocConfig | None:
        """Return the stored `DocConfig` for ``(kb_id, doc_id)`` or ``None`` if absent.

        ``None`` is the inherit sentinel the resolver expects (no per-doc overlay →
        falls through to the per-KB config).
        """
        ...

    async def upsert(self, kb_id: str, doc_id: str, config: DocConfig) -> DocConfig:
        """Insert or replace the per-doc config; returns the stored config."""
        ...

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        """Delete the per-doc config; returns ``True`` if a row existed (else ``False``).

        Idempotent — deleting an absent config is not an error (the route maps both
        to 204).
        """
        ...

    async def list_for_kb(self, kb_id: str) -> dict[str, DocConfig]:
        """Return ``{doc_id: DocConfig}`` for every per-doc config under ``kb_id``."""
        ...


class InMemoryDocConfigStore:
    """Process-local per-doc config store — W1-style local dev / CI default.

    Satisfies the `DocConfigStore` Protocol. Backed by a nested dict
    ``{kb_id: {doc_id: DocConfig}}``. Lost on restart (same trade-off as the
    in-memory KB backend before ADR-0023 Postgres persistence).
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, DocConfig]] = {}

    async def get(self, kb_id: str, doc_id: str) -> DocConfig | None:
        return self._store.get(kb_id, {}).get(doc_id)

    async def upsert(self, kb_id: str, doc_id: str, config: DocConfig) -> DocConfig:
        self._store.setdefault(kb_id, {})[doc_id] = config
        return config

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        kb = self._store.get(kb_id)
        if kb is None or doc_id not in kb:
            return False
        del kb[doc_id]
        if not kb:  # drop the empty kb bucket
            del self._store[kb_id]
        return True

    async def list_for_kb(self, kb_id: str) -> dict[str, DocConfig]:
        # Copy so callers can't mutate the live store.
        return dict(self._store.get(kb_id, {}))


_TABLE = "document_configs"

_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    kb_id   TEXT NOT NULL,
    doc_id  TEXT NOT NULL,
    config  JSONB NOT NULL,
    PRIMARY KEY (kb_id, doc_id)
)
"""


class PostgresDocConfigStore:
    """Per-doc config CRUD backed by a Postgres table — satisfies `DocConfigStore`.

    Connection-per-op via psycopg 3 async (same rationale as `PostgresKBBackend`:
    per-doc config ops are infrequent + off the query hot path). ``CREATE TABLE IF
    NOT EXISTS`` runs on every connect — idempotent, microseconds when present.
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

    async def get(self, kb_id: str, doc_id: str) -> DocConfig | None:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"SELECT config FROM {_TABLE} WHERE kb_id = %s AND doc_id = %s",
                (kb_id, doc_id),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return DocConfig(**row["config"])

    async def upsert(self, kb_id: str, doc_id: str, config: DocConfig) -> DocConfig:
        from psycopg.types.json import Jsonb

        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"""
                INSERT INTO {_TABLE} (kb_id, doc_id, config)
                VALUES (%s, %s, %s)
                ON CONFLICT (kb_id, doc_id) DO UPDATE SET config = EXCLUDED.config
                """,
                (kb_id, doc_id, Jsonb(config.model_dump())),
            )
        return config

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"DELETE FROM {_TABLE} WHERE kb_id = %s AND doc_id = %s",
                (kb_id, doc_id),
            )
            return cur.rowcount > 0

    async def list_for_kb(self, kb_id: str) -> dict[str, DocConfig]:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"SELECT doc_id, config FROM {_TABLE} WHERE kb_id = %s ORDER BY doc_id",
                (kb_id,),
            )
            rows = await cur.fetchall()
        return {r["doc_id"]: DocConfig(**r["config"]) for r in rows}


def make_doc_config_store(settings: Settings) -> DocConfigStore:
    """Return a Postgres-backed store when ``database_url`` is set, else in-memory.

    Mirrors `kb_management.factory.make_kb_backend` — lazy psycopg import inside the
    Postgres branch so an unset ``DATABASE_URL`` never touches the driver.
    """
    if settings.database_url:
        return PostgresDocConfigStore(settings.database_url)
    return InMemoryDocConfigStore()

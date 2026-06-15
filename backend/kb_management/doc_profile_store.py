"""Per-document profile storage (W76 / ADR-0056 層 A 段③ 前置 — read surface).

Stores the W72 profiler result (serialised as `DocProfileInfo`) keyed by
``(kb_id, doc_id)``. Mirrors `doc_config_store.py` (ADR-0050): a Postgres table when
``settings.database_url`` is set, else a process-local in-memory dict. ``psycopg`` is
imported lazily inside the Postgres impl so an unset ``DATABASE_URL`` never touches it.

A profile is a READ-ONLY system-detected fact (img density / structural signals →
classification), distinct from the user-tunable `DocConfig` override — so it lives in
its OWN store rather than folding into `document_configs`. ``doc_id`` is a free-form
key (no documents persistence table — docs live only in the search index), same as
`doc_config_store`; orphan rows are surfaced by the read path, not blocked here.

Schema (Postgres):
    document_profiles(kb_id TEXT, doc_id TEXT, profile JSONB, PRIMARY KEY(kb_id, doc_id))
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from api.schemas.doc_profile import DocProfileInfo

if TYPE_CHECKING:
    import psycopg
    from psycopg.rows import DictRow

    from storage.settings import Settings


class DocProfileStore(Protocol):
    """Per-document profile CRUD interface. Implementations must be async-safe."""

    async def get(self, kb_id: str, doc_id: str) -> DocProfileInfo | None:
        """Return the stored `DocProfileInfo` for ``(kb_id, doc_id)`` or ``None``.

        ``None`` = not profiled (the read API surfaces it as ``null`` → UI「未分析」).
        """
        ...

    async def upsert(self, kb_id: str, doc_id: str, profile: DocProfileInfo) -> DocProfileInfo:
        """Insert or replace the per-doc profile; returns the stored profile."""
        ...

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        """Delete the per-doc profile; returns ``True`` if a row existed (else ``False``).

        Idempotent — deleting an absent profile is not an error.
        """
        ...

    async def list_for_kb(self, kb_id: str) -> dict[str, DocProfileInfo]:
        """Return ``{doc_id: DocProfileInfo}`` for every profiled doc under ``kb_id``."""
        ...


class InMemoryDocProfileStore:
    """Process-local per-doc profile store — local dev / CI default.

    Satisfies the `DocProfileStore` Protocol. Backed by a nested dict
    ``{kb_id: {doc_id: DocProfileInfo}}``. Lost on restart (same trade-off as the
    in-memory KB / doc-config backends before ADR-0023 Postgres persistence).
    """

    def __init__(self) -> None:
        self._store: dict[str, dict[str, DocProfileInfo]] = {}

    async def get(self, kb_id: str, doc_id: str) -> DocProfileInfo | None:
        return self._store.get(kb_id, {}).get(doc_id)

    async def upsert(self, kb_id: str, doc_id: str, profile: DocProfileInfo) -> DocProfileInfo:
        self._store.setdefault(kb_id, {})[doc_id] = profile
        return profile

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        kb = self._store.get(kb_id)
        if kb is None or doc_id not in kb:
            return False
        del kb[doc_id]
        if not kb:  # drop the empty kb bucket
            del self._store[kb_id]
        return True

    async def list_for_kb(self, kb_id: str) -> dict[str, DocProfileInfo]:
        # Copy so callers can't mutate the live store.
        return dict(self._store.get(kb_id, {}))


_TABLE = "document_profiles"

_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    kb_id    TEXT NOT NULL,
    doc_id   TEXT NOT NULL,
    profile  JSONB NOT NULL,
    PRIMARY KEY (kb_id, doc_id)
)
"""


class PostgresDocProfileStore:
    """Per-doc profile CRUD backed by a Postgres table — satisfies `DocProfileStore`.

    Connection-per-op via psycopg 3 async (same rationale as `PostgresDocConfigStore`:
    profile ops are infrequent + off the query hot path). ``CREATE TABLE IF NOT EXISTS``
    runs on every connect — idempotent, microseconds when present.
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

    async def get(self, kb_id: str, doc_id: str) -> DocProfileInfo | None:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"SELECT profile FROM {_TABLE} WHERE kb_id = %s AND doc_id = %s",
                (kb_id, doc_id),
            )
            row = await cur.fetchone()
        if row is None:
            return None
        return DocProfileInfo(**row["profile"])

    async def upsert(self, kb_id: str, doc_id: str, profile: DocProfileInfo) -> DocProfileInfo:
        from psycopg.types.json import Jsonb

        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"""
                INSERT INTO {_TABLE} (kb_id, doc_id, profile)
                VALUES (%s, %s, %s)
                ON CONFLICT (kb_id, doc_id) DO UPDATE SET profile = EXCLUDED.profile
                """,
                (kb_id, doc_id, Jsonb(profile.model_dump())),
            )
        return profile

    async def delete(self, kb_id: str, doc_id: str) -> bool:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"DELETE FROM {_TABLE} WHERE kb_id = %s AND doc_id = %s",
                (kb_id, doc_id),
            )
            return cur.rowcount > 0

    async def list_for_kb(self, kb_id: str) -> dict[str, DocProfileInfo]:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"SELECT doc_id, profile FROM {_TABLE} WHERE kb_id = %s ORDER BY doc_id",
                (kb_id,),
            )
            rows = await cur.fetchall()
        return {r["doc_id"]: DocProfileInfo(**r["profile"]) for r in rows}


def make_doc_profile_store(settings: Settings) -> DocProfileStore:
    """Return a Postgres-backed store when ``database_url`` is set, else in-memory.

    Mirrors `make_doc_config_store` — lazy psycopg import inside the Postgres branch
    so an unset ``DATABASE_URL`` never touches the driver.
    """
    if settings.database_url:
        return PostgresDocProfileStore(settings.database_url)
    return InMemoryDocProfileStore()

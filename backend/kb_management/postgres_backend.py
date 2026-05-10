"""Postgres-backed KB storage (per ADR-0023 — closes CO18 in-memory restart-wipe).

Satisfies the `KBStorageBackend` Protocol. Connection-per-op via psycopg 3 async
— Tier 1 KB CRUD ops (create / list / get / delete / update) are infrequent and
off the query hot path, so a connection pool is not warranted (deviation from
plan §F1.6 "lifespan pool" — connection-per-op is simpler and pool-free; logged
in W17 plan §7 changelog). `CREATE TABLE IF NOT EXISTS` runs on every connect:
idempotent, microseconds when the table already exists, and race-free vs a lazy
one-time init flag.

Wired only when `settings.database_url` is set — see `kb_management.factory.
make_kb_backend`, which lazily imports this module so an unset `DATABASE_URL`
never touches `psycopg`.

Schema (in the `ekp` database per ADR-0023, or whatever DB the DSN points at):
    knowledge_bases(kb_id PK / name / description / config JSONB /
                    total_documents / total_chunks / total_screenshots /
                    failed_documents JSONB / last_indexed_at TIMESTAMPTZ /
                    storage_size_mb DOUBLE PRECISION)
JSONB columns hold the Pydantic-dumped `KbConfig` and `list[FailureRecord]`
(datetimes serialized via `model_dump(mode="json")`, reconstructed by Pydantic).
"""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from api.schemas.kb import FailureRecord, KbConfig, KbStatus
from kb_management.storage import KBAlreadyExistsError, KBNotFoundError

_TABLE = "knowledge_bases"

_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    kb_id              TEXT PRIMARY KEY,
    name               TEXT NOT NULL,
    description        TEXT NOT NULL DEFAULT '',
    config             JSONB NOT NULL,
    total_documents    INTEGER NOT NULL DEFAULT 0,
    total_chunks       INTEGER NOT NULL DEFAULT 0,
    total_screenshots  INTEGER NOT NULL DEFAULT 0,
    failed_documents   JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_indexed_at    TIMESTAMPTZ NOT NULL,
    storage_size_mb    DOUBLE PRECISION NOT NULL DEFAULT 0
)
"""

_COLS = (
    "kb_id, name, description, config, total_documents, total_chunks, "
    "total_screenshots, failed_documents, last_indexed_at, storage_size_mb"
)


def _row_to_kb(row: dict) -> KbStatus:
    return KbStatus(
        kb_id=row["kb_id"],
        name=row["name"],
        description=row["description"],
        config=KbConfig(**row["config"]),
        total_documents=row["total_documents"],
        total_chunks=row["total_chunks"],
        total_screenshots=row["total_screenshots"],
        failed_documents=[FailureRecord(**d) for d in row["failed_documents"]],
        last_indexed_at=row["last_indexed_at"],
        storage_size_mb=row["storage_size_mb"],
    )


def _kb_params(kb: KbStatus) -> tuple:
    return (
        kb.kb_id,
        kb.name,
        kb.description,
        Jsonb(kb.config.model_dump()),
        kb.total_documents,
        kb.total_chunks,
        kb.total_screenshots,
        Jsonb([fr.model_dump(mode="json") for fr in kb.failed_documents]),
        kb.last_indexed_at,
        kb.storage_size_mb,
    )


class PostgresKBBackend:
    """KB CRUD backed by a Postgres table — satisfies the `KBStorageBackend` Protocol."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def _connect(self) -> psycopg.AsyncConnection:
        conn = await psycopg.AsyncConnection.connect(
            self._dsn, autocommit=True, row_factory=dict_row,
        )
        async with conn.cursor() as cur:
            await cur.execute(_CREATE_TABLE)
        return conn

    async def create(self, kb: KbStatus) -> KbStatus:
        async with await self._connect() as conn, conn.cursor() as cur:
            try:
                await cur.execute(
                    f"INSERT INTO {_TABLE} ({_COLS}) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    _kb_params(kb),
                )
            except psycopg.errors.UniqueViolation as exc:
                raise KBAlreadyExistsError(f"KB '{kb.kb_id}' already exists") from exc
        return kb

    async def list_all(self) -> list[KbStatus]:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(f"SELECT {_COLS} FROM {_TABLE} ORDER BY kb_id")
            rows = await cur.fetchall()
        return [_row_to_kb(r) for r in rows]

    async def get(self, kb_id: str) -> KbStatus:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(f"SELECT {_COLS} FROM {_TABLE} WHERE kb_id = %s", (kb_id,))
            row = await cur.fetchone()
        if row is None:
            raise KBNotFoundError(f"KB '{kb_id}' not found")
        return _row_to_kb(row)

    async def delete(self, kb_id: str) -> None:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(f"DELETE FROM {_TABLE} WHERE kb_id = %s", (kb_id,))
            if cur.rowcount == 0:
                raise KBNotFoundError(f"KB '{kb_id}' not found")

    async def update_config(self, kb_id: str, config: KbConfig) -> KbStatus:
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"UPDATE {_TABLE} SET config = %s WHERE kb_id = %s RETURNING {_COLS}",
                (Jsonb(config.model_dump()), kb_id),
            )
            row = await cur.fetchone()
        if row is None:
            raise KBNotFoundError(f"KB '{kb_id}' not found")
        return _row_to_kb(row)

    async def update_metadata(
        self, kb_id: str, name: str | None = None, description: str | None = None,
    ) -> KbStatus:
        if name is None and description is None:
            return await self.get(kb_id)  # no-op — return current state (404 if missing)
        sets: list[str] = []
        params: list[object] = []
        if name is not None:
            sets.append("name = %s")
            params.append(name)
        if description is not None:
            sets.append("description = %s")
            params.append(description)
        params.append(kb_id)
        async with await self._connect() as conn, conn.cursor() as cur:
            await cur.execute(
                f"UPDATE {_TABLE} SET {', '.join(sets)} WHERE kb_id = %s RETURNING {_COLS}",
                tuple(params),
            )
            row = await cur.fetchone()
        if row is None:
            raise KBNotFoundError(f"KB '{kb_id}' not found")
        return _row_to_kb(row)

"""Postgres-backed conversation + message store (per ADR-0031 Option B + ADR-0023 pattern).

Satisfies the `ConversationStore` async Protocol. Sync `psycopg` connection-per-op
under the hood — wrapped in `anyio.to_thread.run_sync` so async route handlers
can `await` without blocking the event loop. Same trade as `PostgresUsersStore` /
`PostgresKBBackend`: low-traffic Tier 1 conversation ops don't justify a pool;
`CREATE TABLE IF NOT EXISTS` runs on every connect (idempotent, microseconds when
the tables already exist).

Imported only when `Settings.database_url` is set — see
`conversations.store.make_conversation_store`, which lazily imports this module so
an unset `DATABASE_URL` never touches `psycopg`.

Schema (in the `ekp` database per ADR-0023):
    conversations(
        id PK / user_id (logical FK — no DB-level FK to users(oid) so the in-memory
                         + Postgres test fixtures don't need to spin up users first) /
        title / kb_id (nullable) / created_at / updated_at / message_count)
    messages(
        id PK /
        conversation_id FK→conversations(id) ON DELETE CASCADE /
        role ('user' | 'assistant') /
        content /
        citations JSONB (nullable — null for user turns; carries the W3 Citation list
                         verbatim for assistant turns) /
        created_at)
"""

from __future__ import annotations

import json
from typing import Any

import anyio
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Json

from api.schemas.conversation import Conversation, Message, _utcnow
from api.schemas.query import Citation
from conversations.store import ConversationNotFoundError

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS conversations (
    id            TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL,
    title         TEXT NOT NULL,
    kb_id         TEXT,
    created_at    TIMESTAMPTZ NOT NULL,
    updated_at    TIMESTAMPTZ NOT NULL,
    message_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS conversations_user_updated_idx
    ON conversations (user_id, updated_at DESC);
CREATE TABLE IF NOT EXISTS messages (
    id              TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT NOT NULL,
    citations       JSONB,
    created_at      TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_conv_created_idx
    ON messages (conversation_id, created_at);
"""

_CONV_COLS = "id, user_id, title, kb_id, created_at, updated_at, message_count"
_MSG_COLS = "id, conversation_id, role, content, citations, created_at"


def _row_to_conversation(row: dict[str, Any]) -> Conversation:
    return Conversation(
        id=row["id"],
        user_id=row["user_id"],
        title=row["title"],
        kb_id=row["kb_id"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        message_count=row["message_count"],
    )


def _row_to_message(row: dict[str, Any]) -> Message:
    raw_citations = row["citations"]
    citations: list[Citation] | None
    if raw_citations is None:
        citations = None
    elif isinstance(raw_citations, str):
        # psycopg dict_row returns JSONB as already-decoded list/dict typically;
        # defend against the string-encoded path just in case.
        citations = [Citation.model_validate(c) for c in json.loads(raw_citations)]
    else:
        citations = [Citation.model_validate(c) for c in raw_citations]
    return Message(
        id=row["id"],
        conversation_id=row["conversation_id"],
        role=row["role"],
        content=row["content"],
        citations=citations,
        created_at=row["created_at"],
    )


def _citations_to_jsonb(citations: list[Citation] | None) -> Json | None:
    if citations is None:
        return None
    return Json([c.model_dump(mode="json") for c in citations])


class PostgresConversationStore:
    """Conversations + messages backed by Postgres tables — satisfies the
    `ConversationStore` async Protocol via `anyio.to_thread.run_sync`."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect_sync(self) -> Any:
        conn = psycopg.connect(self._dsn, autocommit=True, row_factory=dict_row)
        conn.execute(_CREATE_TABLES)
        return conn

    async def reset(self) -> None:
        def _do() -> None:
            with self._connect_sync() as conn:
                conn.execute("TRUNCATE TABLE messages, conversations")

        await anyio.to_thread.run_sync(_do)

    async def create(self, conversation: Conversation) -> Conversation:
        def _do() -> None:
            with self._connect_sync() as conn, conn.cursor() as cur:
                try:
                    cur.execute(
                        f"INSERT INTO conversations ({_CONV_COLS}) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (
                            conversation.id,
                            conversation.user_id,
                            conversation.title,
                            conversation.kb_id,
                            conversation.created_at,
                            conversation.updated_at,
                            conversation.message_count,
                        ),
                    )
                except psycopg.errors.UniqueViolation as exc:
                    raise ValueError(
                        f"conversation_id_already_exists: {conversation.id}"
                    ) from exc

        await anyio.to_thread.run_sync(_do)
        return conversation

    async def list_for_user(
        self, user_id: str, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[Conversation], int]:
        def _do() -> tuple[list[Conversation], int]:
            with self._connect_sync() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) AS n FROM conversations WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
                total = int(row["n"]) if row else 0
                cur.execute(
                    f"SELECT {_CONV_COLS} FROM conversations "
                    "WHERE user_id = %s ORDER BY updated_at DESC LIMIT %s OFFSET %s",
                    (user_id, limit, offset),
                )
                items = [_row_to_conversation(r) for r in cur.fetchall()]
            return items, total

        return await anyio.to_thread.run_sync(_do)

    async def get(self, conversation_id: str, user_id: str) -> Conversation:
        def _do() -> Conversation:
            with self._connect_sync() as conn, conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_CONV_COLS} FROM conversations "
                    "WHERE id = %s AND user_id = %s",
                    (conversation_id, user_id),
                )
                row = cur.fetchone()
            if row is None:
                raise ConversationNotFoundError(conversation_id)
            return _row_to_conversation(row)

        return await anyio.to_thread.run_sync(_do)

    async def list_messages(
        self, conversation_id: str, user_id: str
    ) -> list[Message]:
        # Verify ownership first (raises ConversationNotFoundError if not owned).
        await self.get(conversation_id, user_id)

        def _do() -> list[Message]:
            with self._connect_sync() as conn, conn.cursor() as cur:
                cur.execute(
                    f"SELECT {_MSG_COLS} FROM messages "
                    "WHERE conversation_id = %s ORDER BY created_at ASC, id ASC",
                    (conversation_id,),
                )
                return [_row_to_message(r) for r in cur.fetchall()]

        return await anyio.to_thread.run_sync(_do)

    async def update(
        self,
        conversation_id: str,
        user_id: str,
        *,
        title: str,
        kb_id: str | None,
    ) -> Conversation:
        # Verify ownership + return canonical record.
        existing = await self.get(conversation_id, user_id)
        new_updated_at = _utcnow()

        def _do() -> None:
            with self._connect_sync() as conn, conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET title = %s, kb_id = %s, updated_at = %s "
                    "WHERE id = %s AND user_id = %s",
                    (title, kb_id, new_updated_at, conversation_id, user_id),
                )

        await anyio.to_thread.run_sync(_do)
        return existing.model_copy(
            update={"title": title, "kb_id": kb_id, "updated_at": new_updated_at}
        )

    async def delete(self, conversation_id: str, user_id: str) -> None:
        def _do() -> int:
            with self._connect_sync() as conn, conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM conversations WHERE id = %s AND user_id = %s",
                    (conversation_id, user_id),
                )
                # psycopg's `cur.rowcount` is `int` but its `.pyi` returns `Any`
                # against mypy strict — explicit `int(...)` keeps the return type.
                return int(cur.rowcount)

        rowcount = await anyio.to_thread.run_sync(_do)
        if rowcount == 0:
            raise ConversationNotFoundError(conversation_id)

    async def append_message(
        self, conversation_id: str, user_id: str, message: Message
    ) -> Message:
        # Verify ownership; if missing, ConversationNotFoundError bubbles up.
        await self.get(conversation_id, user_id)
        bumped_at = _utcnow()

        def _do() -> None:
            with self._connect_sync() as conn, conn.cursor() as cur:
                cur.execute(
                    f"INSERT INTO messages ({_MSG_COLS}) VALUES (%s, %s, %s, %s, %s, %s)",
                    (
                        message.id,
                        message.conversation_id,
                        message.role,
                        message.content,
                        _citations_to_jsonb(message.citations),
                        message.created_at,
                    ),
                )
                cur.execute(
                    "UPDATE conversations SET message_count = message_count + 1, "
                    "updated_at = %s WHERE id = %s AND user_id = %s",
                    (bumped_at, conversation_id, user_id),
                )

        await anyio.to_thread.run_sync(_do)
        return message


__all__ = ["PostgresConversationStore"]

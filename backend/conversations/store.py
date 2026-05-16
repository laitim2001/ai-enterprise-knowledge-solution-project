"""Conversation + Message persistence backends — Protocol + in-memory impl + factory.

W20 F3.2 per ADR-0031 Option B + ADR-0023 backing pattern. Mirrors
`api.auth.users_store` (Protocol + in-memory + factory in one file) — simpler than
`kb_management/` (which splits storage/postgres/factory/service across 4 files) since
the conversation surface is a pure CRUD pass-through (no `KBService`-style business
logic).

Two impls:
  - `InMemoryConversationStore` — process-local dict (local dev / CI; default when
    `DATABASE_URL` is unset)
  - `PostgresConversationStore` (in `postgres_store.py`) — durable, picked when
    `Settings.database_url` is set. Lazily imported inside `make_conversation_store`
    so an unset `DATABASE_URL` never touches `psycopg` (R8 corp-proxy precedent —
    keeps the in-memory path working even if `pip install psycopg[binary]` is blocked).

Async interface (route handlers under `/conversations` are async) — same shape as
`KBStorageBackend`, distinct from the sync `UsersStore` (which is consumed by sync
threadpool dependencies).
"""

from __future__ import annotations

from asyncio import Lock
from typing import Protocol

from api.schemas.conversation import Conversation, Message
from storage.settings import Settings


class ConversationNotFoundError(Exception):
    """Raised by `get` / `update` / `delete` / `append_message` when the conversation
    doesn't exist OR isn't owned by the caller (the route layer translates → 404)."""


class ConversationStore(Protocol):
    """Persistence primitives for conversations + messages. Implementations must be
    async-safe (single-process locking is enough for Tier 1)."""

    async def reset(self) -> None:
        """Test fixture helper — wipe both tables."""
        ...

    async def create(self, conversation: Conversation) -> Conversation:
        """Insert a new conversation (zero messages)."""
        ...

    async def list_for_user(
        self, user_id: str, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[Conversation], int]:
        """List user's conversations descending by `updated_at`; returns (items, total)."""
        ...

    async def get(self, conversation_id: str, user_id: str) -> Conversation:
        """Get one conversation. Raises `ConversationNotFoundError` on miss / cross-user."""
        ...

    async def list_messages(self, conversation_id: str, user_id: str) -> list[Message]:
        """Get all messages for a conversation, chronological. Caller must already
        have verified ownership via `get`."""
        ...

    async def update(
        self,
        conversation_id: str,
        user_id: str,
        *,
        title: str,
        kb_id: str | None,
    ) -> Conversation:
        """Set title + kb_id (both required — the caller pre-computes from the
        existing record so the store stays a thin SET-everything UPDATE). The
        route layer (`PATCH /conversations/{id}`) handles "partial" semantics via
        `body.model_fields_set` + a get-then-update sequence."""
        ...

    async def delete(self, conversation_id: str, user_id: str) -> None:
        """Hard delete the conversation + its messages (CASCADE)."""
        ...

    async def append_message(
        self, conversation_id: str, user_id: str, message: Message
    ) -> Message:
        """Append a new message; bumps `updated_at` + `message_count` on the parent."""
        ...


# --------------------------------------------------------------------------- #
# In-memory impl (default when DATABASE_URL unset)
# --------------------------------------------------------------------------- #


class InMemoryConversationStore:
    """Process-local conversation store — not durable across restart. Single-process
    Tier 1 dev / CI scope. Uses `asyncio.Lock` (not RLock) for async-safety."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}  # key = conversation id
        self._messages: dict[str, list[Message]] = {}  # key = conversation id
        self._lock = Lock()

    async def reset(self) -> None:
        async with self._lock:
            self._conversations.clear()
            self._messages.clear()

    async def create(self, conversation: Conversation) -> Conversation:
        async with self._lock:
            if conversation.id in self._conversations:
                raise ValueError(f"conversation_id_already_exists: {conversation.id}")
            self._conversations[conversation.id] = conversation
            self._messages[conversation.id] = []
        return conversation

    async def list_for_user(
        self, user_id: str, *, limit: int = 20, offset: int = 0
    ) -> tuple[list[Conversation], int]:
        async with self._lock:
            owned = [c for c in self._conversations.values() if c.user_id == user_id]
            owned.sort(key=lambda c: c.updated_at, reverse=True)
            total = len(owned)
            items = owned[offset : offset + limit]
        return items, total

    async def get(self, conversation_id: str, user_id: str) -> Conversation:
        async with self._lock:
            conv = self._conversations.get(conversation_id)
            if conv is None or conv.user_id != user_id:
                raise ConversationNotFoundError(conversation_id)
            return conv

    async def list_messages(
        self, conversation_id: str, user_id: str
    ) -> list[Message]:
        async with self._lock:
            conv = self._conversations.get(conversation_id)
            if conv is None or conv.user_id != user_id:
                raise ConversationNotFoundError(conversation_id)
            return list(self._messages.get(conversation_id, []))

    async def update(
        self,
        conversation_id: str,
        user_id: str,
        *,
        title: str,
        kb_id: str | None,
    ) -> Conversation:
        from api.schemas.conversation import _utcnow

        async with self._lock:
            conv = self._conversations.get(conversation_id)
            if conv is None or conv.user_id != user_id:
                raise ConversationNotFoundError(conversation_id)
            new_conv = conv.model_copy(
                update={"title": title, "kb_id": kb_id, "updated_at": _utcnow()}
            )
            self._conversations[conversation_id] = new_conv
        return new_conv

    async def delete(self, conversation_id: str, user_id: str) -> None:
        async with self._lock:
            conv = self._conversations.get(conversation_id)
            if conv is None or conv.user_id != user_id:
                raise ConversationNotFoundError(conversation_id)
            del self._conversations[conversation_id]
            self._messages.pop(conversation_id, None)

    async def append_message(
        self, conversation_id: str, user_id: str, message: Message
    ) -> Message:
        from api.schemas.conversation import _utcnow

        async with self._lock:
            conv = self._conversations.get(conversation_id)
            if conv is None or conv.user_id != user_id:
                raise ConversationNotFoundError(conversation_id)
            self._messages.setdefault(conversation_id, []).append(message)
            new_conv = conv.model_copy(
                update={
                    "message_count": conv.message_count + 1,
                    "updated_at": _utcnow(),
                }
            )
            self._conversations[conversation_id] = new_conv
        return message


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #


def make_conversation_store(settings: Settings) -> ConversationStore:
    """Return a Postgres-backed store when `database_url` is set, else the
    process-local in-memory store. Mirrors `kb_management.factory.make_kb_backend`
    + `api.auth.users_store.make_users_store` — `PostgresConversationStore` (and
    `psycopg`) is imported lazily inside the branch."""
    if settings.database_url:
        from conversations.postgres_store import PostgresConversationStore

        return PostgresConversationStore(settings.database_url)
    return InMemoryConversationStore()

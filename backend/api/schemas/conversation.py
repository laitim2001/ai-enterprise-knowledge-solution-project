"""Conversation + Message Pydantic v2 schemas (per ADR-0031 Option B server-side Tier 1).

C10 §7 — promotes Conversation History from Tier 2 (localStorage W18 baseline) to
Tier 1 server-side. Postgres-backed via the ADR-0023 pattern (PostgresConversationStore
+ in-memory fallback when DATABASE_URL is unset). The route surface is 6 CRUD endpoints
under /conversations (W20 F3.3) all gated by Depends(get_current_user) — per-user
isolation enforced.

Schema choice notes:
- `Conversation.user_id` = `AuthenticatedUser.oid` (stable principal id, mock + real MSAL
  share the field name)
- `Conversation.kb_id` is nullable — Tier 1 chat is single-KB (W3 hardcoded `drive_user_manuals`),
  but the schema is future-proof for multi-KB or "global" conversations
- `Message.citations` carries the W3 Citation list verbatim (chunk_id / doc_id / image refs
  / etc); the route stores it as JSONB so the streaming SSE event shape survives the
  round-trip without a schema migration when new fields land
- `created_at` uses Pydantic v2's UTC-default factory so the in-memory + Postgres paths
  agree on tz-awareness (Postgres TIMESTAMPTZ)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.query import Citation


def _utcnow() -> datetime:
    """Tz-aware default for created_at/updated_at; matches Postgres TIMESTAMPTZ."""
    return datetime.now(UTC)


# --------------------------------------------------------------------------- #
# Records (what the store layer round-trips; the route response_models reuse these)
# --------------------------------------------------------------------------- #


class Message(BaseModel):
    """One turn in a conversation (user prompt OR assistant response)."""

    id: str = Field(..., description="Stable message id (uuid4 hex).")
    conversation_id: str = Field(..., description="Owning conversation id.")
    role: Literal["user", "assistant"] = Field(
        ..., description="Who emitted the turn."
    )
    content: str = Field(..., description="Plain-text body — the streamed answer for assistant turns.")
    citations: list[Citation] | None = Field(
        default=None,
        description=(
            "Citation list for assistant turns (W3 Citation shape); None for user turns. "
            "Postgres stores this as JSONB so SSE event shape extensions survive without migration."
        ),
    )
    created_at: datetime = Field(default_factory=_utcnow)


class Conversation(BaseModel):
    """A chat thread for a single user. Title auto-gens from the first user turn."""

    id: str = Field(..., description="Stable conversation id (uuid4 hex).")
    user_id: str = Field(..., description="Owner — AuthenticatedUser.oid.")
    title: str = Field(..., description="Display title (first-50-char slice of first user message Tier 1).")
    kb_id: str | None = Field(
        default=None,
        description="Optional KB scope; None = not yet bound (single-KB Tier 1 = `drive_user_manuals`).",
    )
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    message_count: int = Field(
        default=0,
        description="Count of messages — kept in sync at append_message time (denormalized for list view).",
    )


# --------------------------------------------------------------------------- #
# Request schemas (what the route accepts)
# --------------------------------------------------------------------------- #


class ConversationCreate(BaseModel):
    """`POST /conversations` payload — both fields optional (auto-titled empty conversation)."""

    title: str | None = Field(default=None, max_length=200)
    kb_id: str | None = None


class ConversationUpdate(BaseModel):
    """`PATCH /conversations/{id}` payload — partial update (omitted fields preserve current value)."""

    title: str | None = Field(default=None, max_length=200)
    kb_id: str | None = None


class MessageCreate(BaseModel):
    """`POST /conversations/{id}/messages` payload — frontend writes after each turn settles."""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)
    citations: list[Citation] | None = None


# --------------------------------------------------------------------------- #
# Response schemas
# --------------------------------------------------------------------------- #


class ConversationDetail(BaseModel):
    """`GET /conversations/{id}` — conversation + messages in chronological order."""

    conversation: Conversation
    messages: list[Message]


class ConversationListResponse(BaseModel):
    """`GET /conversations` — paginated list (descending by updated_at)."""

    items: list[Conversation]
    total: int
    limit: int
    offset: int

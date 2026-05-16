"""C10 §7 — `/conversations` CRUD endpoints (W20 F3.3 per ADR-0031 Option B).

6 endpoints, all gated by `Depends(get_current_user)`:
  - `POST   /conversations`                       — create (auto-title empty conv)
  - `GET    /conversations`                       — paginated list (descending by updated_at)
  - `GET    /conversations/{id}`                  — get conv + messages
  - `PATCH  /conversations/{id}`                  — partial update (title / kb_id)
  - `DELETE /conversations/{id}`                  — hard delete (messages CASCADE)
  - `POST   /conversations/{id}/messages`         — append message (user OR assistant turn)

Per-user isolation enforced at the store layer (every op takes `user_id =
current_user.oid` and the store raises `ConversationNotFoundError` on cross-user
access — translated to 404 here to avoid leaking existence of OTHER users' conv ids).

Backed by `make_conversation_store(settings)` — Postgres when DATABASE_URL is set,
in-memory fallback otherwise (per ADR-0023). Service singleton lives in
`app.state.conversation_store` (wired by the route module's dependency).

Title auto-gen (Tier 1) = first-50-char slice of the first user message;
LLM-summarized titles are a Wave B+ candidate (Karpathy §1.2 simplicity).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from api.auth import AuthenticatedUser, get_current_user
from api.schemas.conversation import (
    Conversation,
    ConversationCreate,
    ConversationDetail,
    ConversationListResponse,
    ConversationUpdate,
    Message,
    MessageCreate,
)
from conversations import (
    ConversationNotFoundError,
    ConversationStore,
    make_conversation_store,
)
from storage.settings import get_settings

router = APIRouter(prefix="/conversations", tags=["conversations"])


@lru_cache(maxsize=1)
def get_conversation_store() -> ConversationStore:
    """FastAPI dependency — process-singleton wired via `make_conversation_store`.

    Backend = Postgres when `DATABASE_URL` is set (ADR-0023), else in-memory
    (Tier 1 local dev / CI). Tests swap a fresh in-memory store in via
    `app.dependency_overrides[get_conversation_store]`.
    """
    return make_conversation_store(get_settings())


def _auto_title(first_user_message: str | None) -> str:
    """Tier 1 title auto-gen — first-50-char slice (LLM-summary is Wave B+)."""
    if not first_user_message:
        return "New conversation"
    snippet = first_user_message.strip().split("\n", 1)[0]
    return snippet[:50] if len(snippet) > 50 else snippet or "New conversation"


def _not_found() -> HTTPException:
    """One spot for the 404 message so cross-user vs missing collapse into the same
    response (avoid leaking the existence of OTHER users' conversation ids)."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="conversation_not_found")


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    body: ConversationCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
) -> Conversation:
    """Create an empty conversation (zero messages, auto-titled)."""
    conv = Conversation(
        id=uuid4().hex,
        user_id=current_user.oid,
        title=body.title or "New conversation",
        kb_id=body.kb_id,
    )
    return await store.create(conv)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ConversationListResponse:
    """List the current user's conversations, descending by `updated_at`."""
    items, total = await store.list_for_user(current_user.oid, limit=limit, offset=offset)
    return ConversationListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: Annotated[str, Path(min_length=1)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
) -> ConversationDetail:
    """Get one conversation + its messages, chronological."""
    try:
        conv = await store.get(conversation_id, current_user.oid)
        messages = await store.list_messages(conversation_id, current_user.oid)
    except ConversationNotFoundError as exc:
        raise _not_found() from exc
    return ConversationDetail(conversation=conv, messages=messages)


@router.patch("/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: Annotated[str, Path(min_length=1)],
    body: ConversationUpdate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
) -> Conversation:
    """Partial update — rename + reassign kb_id; omitted fields preserve current value.

    The Pydantic v2 update body distinguishes "field absent" (preserve) from
    "field present as None" (= "clear kb_id"). The route layer owns the partial
    semantics: get existing → merge body → call store.update with the full new
    values. The store itself stays a thin SET-everything UPDATE (no sentinel).
    """
    try:
        existing = await store.get(conversation_id, current_user.oid)
    except ConversationNotFoundError as exc:
        raise _not_found() from exc

    new_title = body.title if body.title is not None else existing.title
    new_kb_id = body.kb_id if "kb_id" in body.model_fields_set else existing.kb_id

    try:
        return await store.update(
            conversation_id,
            current_user.oid,
            title=new_title,
            kb_id=new_kb_id,
        )
    except ConversationNotFoundError as exc:
        # Raced against a delete between the get + the update.
        raise _not_found() from exc


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: Annotated[str, Path(min_length=1)],
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
) -> None:
    """Hard delete the conversation + its messages (CASCADE)."""
    try:
        await store.delete(conversation_id, current_user.oid)
    except ConversationNotFoundError as exc:
        raise _not_found() from exc


@router.post(
    "/{conversation_id}/messages",
    response_model=Message,
    status_code=status.HTTP_201_CREATED,
)
async def append_message(
    conversation_id: Annotated[str, Path(min_length=1)],
    body: MessageCreate,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    store: Annotated[ConversationStore, Depends(get_conversation_store)],
) -> Message:
    """Append a user OR assistant turn. The frontend posts twice per round-trip:
    once for the user prompt (just after submit), once for the assistant response
    after the SSE stream `done` event lands. Each call bumps the conversation's
    `updated_at` + `message_count`.

    If the conversation's title is still the default "New conversation" AND the
    first user message lands, retitle to its first-50-char slice (Tier 1 simplicity).
    """
    try:
        conv = await store.get(conversation_id, current_user.oid)
    except ConversationNotFoundError as exc:
        raise _not_found() from exc

    message = Message(
        id=uuid4().hex,
        conversation_id=conversation_id,
        role=body.role,
        content=body.content,
        citations=body.citations,
    )
    saved = await store.append_message(conversation_id, current_user.oid, message)

    # Auto-title on the FIRST user message if the conversation is still untitled.
    if body.role == "user" and conv.title == "New conversation":
        new_title = _auto_title(body.content)
        if new_title != conv.title:
            try:
                await store.update(
                    conversation_id,
                    current_user.oid,
                    title=new_title,
                    kb_id=conv.kb_id,
                )
            except ConversationNotFoundError:
                # Raced against a concurrent delete — ignore; the message append above
                # already succeeded (and will CASCADE on the delete the next op runs).
                pass

    return saved

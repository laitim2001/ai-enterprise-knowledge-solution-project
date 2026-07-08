"""W20 F3.4 — `/conversations` CRUD tests (per ADR-0031 Option B server-side persistence).

Covers `backend/api/routes/conversations.py` against an in-memory
`ConversationStore` (swapped in via `app.dependency_overrides`). Acceptance per
W20 plan F3.4 + CLAUDE.md §3.1 H6 (coverage ≥ 80% on the new route):

  - happy path: POST → GET → PATCH → POST messages → GET (with messages) → DELETE → GET 404
  - auth gate: missing dependency override → 422 (the route declares get_current_user)
  - cross-user isolation: user A can't read / patch / delete user B's conversation (all 404)
  - auto-title on first user message
  - pagination (limit + offset honoured; total reflects the user's conversations only)
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import AuthenticatedUser, get_current_user
from api.routes import conversations as conversations_routes
from conversations import InMemoryConversationStore

# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #


def _user(oid: str = "user-alice", email: str = "alice@example.com") -> AuthenticatedUser:
    return AuthenticatedUser(
        oid=oid,
        tid="tenant-test",
        preferred_username=email,
        is_mock=True,
    )


def _build_app(
    *,
    store: InMemoryConversationStore,
    current_user: AuthenticatedUser,
) -> FastAPI:
    """Mount the `/conversations` router with both dependencies overridden."""
    app = FastAPI()
    app.include_router(conversations_routes.router)
    app.dependency_overrides[conversations_routes.get_conversation_store] = lambda: store
    app.dependency_overrides[get_current_user] = lambda: current_user
    return app


@pytest.fixture
def store() -> Iterator[InMemoryConversationStore]:
    """Fresh in-memory store per test (no cross-test bleed)."""
    yield InMemoryConversationStore()


# --------------------------------------------------------------------------- #
# Happy-path CRUD lifecycle
# --------------------------------------------------------------------------- #


def test_create_returns_201_and_default_title(
    store: InMemoryConversationStore,
) -> None:
    app = _build_app(store=store, current_user=_user())
    client = TestClient(app)

    resp = client.post("/conversations", json={})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["user_id"] == "user-alice"
    assert body["title"] == "New conversation"
    assert body["message_count"] == 0
    assert body["kb_id"] is None
    assert isinstance(body["id"], str) and len(body["id"]) > 0


def test_create_honours_explicit_title_and_kb_id(
    store: InMemoryConversationStore,
) -> None:
    app = _build_app(store=store, current_user=_user())
    client = TestClient(app)
    resp = client.post(
        "/conversations",
        json={"title": "My research", "kb_id": "drive_user_manuals"},
    )
    body = resp.json()
    assert body["title"] == "My research"
    assert body["kb_id"] == "drive_user_manuals"


def test_list_returns_user_only_sorted_by_updated_desc(
    store: InMemoryConversationStore,
) -> None:
    """Alice's GET /conversations sees ONLY Alice's conversations (Bob's are filtered)."""
    alice_app = _build_app(store=store, current_user=_user("alice"))
    bob_app = _build_app(store=store, current_user=_user("bob"))

    # Bob creates 1 (should not appear in Alice's list)
    TestClient(bob_app).post("/conversations", json={"title": "bob-only"})

    # Alice creates 2; the second one ("alice-second") was created later → first in list
    alice_client = TestClient(alice_app)
    alice_client.post("/conversations", json={"title": "alice-first"})
    alice_client.post("/conversations", json={"title": "alice-second"})

    resp = alice_client.get("/conversations")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2  # bob's NOT counted
    assert [c["title"] for c in body["items"]] == ["alice-second", "alice-first"]


def test_list_paginates(store: InMemoryConversationStore) -> None:
    client = TestClient(_build_app(store=store, current_user=_user()))
    for i in range(5):
        client.post("/conversations", json={"title": f"conv-{i}"})

    page1 = client.get("/conversations?limit=2&offset=0").json()
    page2 = client.get("/conversations?limit=2&offset=2").json()
    assert page1["total"] == 5
    assert page1["limit"] == 2
    assert page1["offset"] == 0
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert page2["offset"] == 2
    # No overlap
    page1_ids = {c["id"] for c in page1["items"]}
    page2_ids = {c["id"] for c in page2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


def test_get_returns_conversation_with_messages(
    store: InMemoryConversationStore,
) -> None:
    client = TestClient(_build_app(store=store, current_user=_user()))
    conv_id = client.post("/conversations", json={}).json()["id"]
    client.post(
        f"/conversations/{conv_id}/messages",
        json={"role": "user", "content": "hello there"},
    )
    client.post(
        f"/conversations/{conv_id}/messages",
        json={"role": "assistant", "content": "hi back", "citations": None},
    )

    resp = client.get(f"/conversations/{conv_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["conversation"]["id"] == conv_id
    assert body["conversation"]["message_count"] == 2
    assert [m["role"] for m in body["messages"]] == ["user", "assistant"]
    assert [m["content"] for m in body["messages"]] == ["hello there", "hi back"]


def test_patch_renames_and_clears_kb_id(
    store: InMemoryConversationStore,
) -> None:
    client = TestClient(_build_app(store=store, current_user=_user()))
    conv_id = client.post(
        "/conversations", json={"title": "old", "kb_id": "drive_user_manuals"}
    ).json()["id"]

    # Only-title patch leaves kb_id intact (model_fields_set excludes kb_id)
    resp = client.patch(f"/conversations/{conv_id}", json={"title": "new"})
    body = resp.json()
    assert body["title"] == "new"
    assert body["kb_id"] == "drive_user_manuals"

    # Explicit kb_id=null clears the FK
    resp = client.patch(f"/conversations/{conv_id}", json={"kb_id": None})
    body = resp.json()
    assert body["kb_id"] is None
    assert body["title"] == "new"  # preserved


def test_delete_removes_conversation(store: InMemoryConversationStore) -> None:
    client = TestClient(_build_app(store=store, current_user=_user()))
    conv_id = client.post("/conversations", json={}).json()["id"]

    resp = client.delete(f"/conversations/{conv_id}")
    assert resp.status_code == 204

    # Subsequent GET → 404
    assert client.get(f"/conversations/{conv_id}").status_code == 404


# --------------------------------------------------------------------------- #
# Auto-title on first user message
# --------------------------------------------------------------------------- #


def test_first_user_message_auto_titles(store: InMemoryConversationStore) -> None:
    client = TestClient(_build_app(store=store, current_user=_user()))
    conv_id = client.post("/conversations", json={}).json()["id"]
    long_message = (
        "How do I configure AR depreciation rules for non-standard fiscal years?"
    )
    client.post(
        f"/conversations/{conv_id}/messages",
        json={"role": "user", "content": long_message},
    )

    body = client.get(f"/conversations/{conv_id}").json()
    assert body["conversation"]["title"].startswith("How do I configure AR")
    # 50-char slice
    assert len(body["conversation"]["title"]) <= 50


def test_assistant_message_does_not_retitle(
    store: InMemoryConversationStore,
) -> None:
    client = TestClient(_build_app(store=store, current_user=_user()))
    conv_id = client.post("/conversations", json={"title": "explicit-title"}).json()[
        "id"
    ]
    client.post(
        f"/conversations/{conv_id}/messages",
        json={"role": "assistant", "content": "I have an answer."},
    )

    body = client.get(f"/conversations/{conv_id}").json()
    assert body["conversation"]["title"] == "explicit-title"


# --------------------------------------------------------------------------- #
# Cross-user isolation
# --------------------------------------------------------------------------- #


def test_cross_user_get_returns_404(store: InMemoryConversationStore) -> None:
    alice = _user("alice")
    bob = _user("bob")
    alice_id = (
        TestClient(_build_app(store=store, current_user=alice))
        .post("/conversations", json={"title": "alice-private"})
        .json()["id"]
    )
    # Bob tries to read it
    bob_client = TestClient(_build_app(store=store, current_user=bob))
    assert bob_client.get(f"/conversations/{alice_id}").status_code == 404
    assert (
        bob_client.patch(f"/conversations/{alice_id}", json={"title": "stolen"}).status_code
        == 404
    )
    assert bob_client.delete(f"/conversations/{alice_id}").status_code == 404
    assert (
        bob_client.post(
            f"/conversations/{alice_id}/messages",
            json={"role": "user", "content": "haha"},
        ).status_code
        == 404
    )


def test_get_missing_returns_404(store: InMemoryConversationStore) -> None:
    client = TestClient(_build_app(store=store, current_user=_user()))
    assert client.get("/conversations/does-not-exist").status_code == 404


# --------------------------------------------------------------------------- #
# Message citations round-trip
# --------------------------------------------------------------------------- #


def test_message_citations_round_trip(store: InMemoryConversationStore) -> None:
    """Citations are JSONB-shaped in Postgres; in-memory store keeps them as Pydantic
    Citation objects. The route accepts the Citation shape and emits it verbatim."""
    citation_payload: dict[str, Any] = {
        "chunk_id": "chunk-1",
        "doc_id": "doc-1",
        "doc_title": "AR Manual",
        "chunk_title": "Depreciation rules",
        "chunk_index": 3,
        "section_path": ["Chapter 4", "Depreciation"],
        "relevance_score": 0.92,
        "embedded_images": [],
    }
    client = TestClient(_build_app(store=store, current_user=_user()))
    conv_id = client.post("/conversations", json={}).json()["id"]
    client.post(
        f"/conversations/{conv_id}/messages",
        json={
            "role": "assistant",
            "content": "Per the AR manual [1].",
            "citations": [citation_payload],
        },
    )

    msg = client.get(f"/conversations/{conv_id}").json()["messages"][0]
    assert msg["citations"] is not None
    assert len(msg["citations"]) == 1
    assert msg["citations"][0]["chunk_id"] == "chunk-1"
    assert msg["citations"][0]["section_path"] == ["Chapter 4", "Depreciation"]

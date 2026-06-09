"""W57 F6.4 — per-document config CRUD route (ADR-0050).

Asserts GET (empty default + after-set), PUT upsert, DELETE (idempotent 204),
the KB-scoped list, and 404 for an unknown KB. Uses an InMemoryDocConfigStore on
app.state + an InMemory KB backend (one registered KB).
"""

from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import doc_config as dc_route
from api.schemas.kb import KbConfig, KbCreate
from kb_management.doc_config_store import InMemoryDocConfigStore
from kb_management.service import KBService, get_kb_service
from kb_management.storage import InMemoryKBBackend


def _app() -> FastAPI:
    service = KBService(InMemoryKBBackend())
    asyncio.run(service.create(KbCreate(kb_id="kb1", name="t", config=KbConfig())))
    app = FastAPI()
    app.state.doc_config_store = InMemoryDocConfigStore()
    app.dependency_overrides[get_kb_service] = lambda: service
    app.include_router(dc_route.router)
    return app


def test_get_absent_returns_empty_doc_config() -> None:
    client = TestClient(_app())
    resp = client.get("/kb/kb1/docs/docA/config")
    assert resp.status_code == 200, resp.text
    # all-None DocConfig (inherit per-KB)
    assert all(v is None for v in resp.json().values())


def test_put_then_get_round_trips() -> None:
    client = TestClient(_app())
    put = client.put(
        "/kb/kb1/docs/docA/config",
        json={"answer_detail": "detailed", "max_images_per_answer": 30},
    )
    assert put.status_code == 200, put.text
    assert put.json()["answer_detail"] == "detailed"
    assert put.json()["max_images_per_answer"] == 30

    got = client.get("/kb/kb1/docs/docA/config")
    assert got.status_code == 200
    assert got.json()["answer_detail"] == "detailed"
    assert got.json()["max_images_per_answer"] == 30


def test_put_replaces() -> None:
    client = TestClient(_app())
    client.put("/kb/kb1/docs/docA/config", json={"max_images_per_answer": 10})
    client.put("/kb/kb1/docs/docA/config", json={"max_images_per_answer": 20})
    got = client.get("/kb/kb1/docs/docA/config")
    assert got.json()["max_images_per_answer"] == 20


def test_delete_idempotent_204() -> None:
    client = TestClient(_app())
    client.put("/kb/kb1/docs/docA/config", json={"max_images_per_answer": 10})
    d1 = client.delete("/kb/kb1/docs/docA/config")
    assert d1.status_code == 204
    d2 = client.delete("/kb/kb1/docs/docA/config")  # already gone
    assert d2.status_code == 204
    # GET after delete → empty default again
    assert all(v is None for v in client.get("/kb/kb1/docs/docA/config").json().values())


def test_list_doc_configs_for_kb() -> None:
    client = TestClient(_app())
    client.put("/kb/kb1/docs/docA/config", json={"max_images_per_answer": 1})
    client.put("/kb/kb1/docs/docB/config", json={"max_images_per_answer": 2})
    listed = client.get("/kb/kb1/doc-configs")
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert set(body) == {"docA", "docB"}
    assert body["docA"]["max_images_per_answer"] == 1
    assert body["docB"]["max_images_per_answer"] == 2


def test_unknown_kb_404_on_all_verbs() -> None:
    client = TestClient(_app())
    assert client.get("/kb/nope/docs/docA/config").status_code == 404
    assert client.put("/kb/nope/docs/docA/config", json={}).status_code == 404
    assert client.delete("/kb/nope/docs/docA/config").status_code == 404
    assert client.get("/kb/nope/doc-configs").status_code == 404

"""POST /chunking-preview tests (W20 F5.3 — per ADR-0025 KB Detail Tab 4 Chunking Lab).

Coverage:
- Happy path with multi-paragraph sample_text → preview chunks emit
- Markdown-style heading detection → section_path reflects the heading
- sample_doc_id-only request → 200 with `note` explaining the Wave B+ seam
- Empty body (no sample_text + no sample_doc_id) → 422
- overlap > 0 → echoed in response + `note` explains it was ignored
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import chunking as chunking_routes


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(chunking_routes.router)
    return app


def test_chunking_preview_happy_path() -> None:
    """Multi-paragraph plain text → at least one chunk back."""
    app = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/chunking-preview",
        json={
            "sample_text": (
                "First paragraph about accounts receivable.\n\n"
                "Second paragraph about the depreciation rules and the way the "
                "ledger reconciles month-end balances across accounts."
            ),
            "strategy": "layout_aware",
            "chunk_size": 700,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 1
    assert body["strategy"] == "layout_aware"
    assert body["chunk_size"] == 700
    assert body["note"] is None
    item = body["items"][0]
    assert "chunk_text" in item
    assert item["chunk_token_count"] > 0


def test_chunking_preview_heading_detection() -> None:
    """Markdown `## Heading` → chunker emits a section bounded by that heading."""
    app = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/chunking-preview",
        json={
            "sample_text": (
                "## Depreciation rules\n\n"
                "The system computes depreciation monthly based on the asset class."
                "\n\nThe ledger entries are posted on the last business day of the month."
            ),
            "strategy": "layout_aware",
            "chunk_size": 700,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] >= 1
    # The first chunk's section path should include the detected heading.
    item = body["items"][0]
    assert any("Depreciation" in part for part in item["section_path"])


def test_chunking_preview_sample_doc_id_seam_returns_note() -> None:
    """`sample_doc_id` only (no sample_text) → 200 with the forward-compat note."""
    app = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/chunking-preview",
        json={"sample_doc_id": "manual-A", "strategy": "auto"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["note"] is not None
    assert "Wave B+" in body["note"]


def test_chunking_preview_empty_body_returns_422() -> None:
    """Neither sample_text nor sample_doc_id → 422."""
    app = _build_app()
    client = TestClient(app)
    resp = client.post("/chunking-preview", json={"sample_text": "", "sample_doc_id": ""})
    assert resp.status_code == 422


def test_chunking_preview_overlap_echoed_with_note() -> None:
    """`overlap > 0` → echoed in the response + the `note` explains it was ignored."""
    app = _build_app()
    client = TestClient(app)
    resp = client.post(
        "/chunking-preview",
        json={"sample_text": "Body text.", "overlap": 32},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["overlap"] == 32
    assert body["note"] is not None
    assert "overlap" in body["note"].lower()

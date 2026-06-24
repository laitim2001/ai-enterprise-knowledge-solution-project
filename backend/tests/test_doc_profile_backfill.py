"""W80 / ADR-0059 — profile-only backfill tests (per CLAUDE.md §5.6 H6).

Coverage:
- POST /kb/{kb_id}/profiles/backfill — compute + persist a profile for every
  already-indexed doc WITHOUT re-chunk / re-embed / re-upsert.
- idempotent skip (doc already has a profile) + skipped_no_source (no stored source).
- per-doc failure isolation (one parse failure never aborts the batch).
- D6 守 — backfill routes the profile's preset to per-doc config UNLESS a manual config
  exists; _backfill_one_doc_profile preserves a prior manual_override on re-profile.
- 503 when no profile store wired.
- zero retrieval dependency — backfill succeeds with NO embedder/populator/chunker wired
  (proves it never touches the retrieval-mutating ingest path).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth.dependency import get_current_user
from api.auth.models import AuthenticatedUser
from api.routes import documents as documents_routes
from api.routes import kb as kb_routes
from api.schemas.doc_config import DocConfig
from api.schemas.doc_profile import DocProfileInfo
from api.schemas.kb import KbConfig, KbCreate
from ingestion.profiler import ProfileResult, ProfileSignals
from kb_management import KBService, get_kb_service
from kb_management.doc_config_store import InMemoryDocConfigStore
from kb_management.doc_profile_store import InMemoryDocProfileStore
from kb_management.storage import InMemoryKBBackend

# --------------------------------------------------------------------------- #
# duck-typed ParserResult — the profiler reads only these attrs (no API boundary)
# --------------------------------------------------------------------------- #


@dataclass
class _MockPara:
    kind: str
    heading_level: int | None = None


@dataclass
class _MockResult:
    doc_format: str = "docx"
    paragraphs_total: int = 100
    paragraphs: list[_MockPara] = field(default_factory=list)
    embedded_images: list[object] = field(default_factory=list)
    tables: list[object] = field(default_factory=list)
    raw_text: str = ""
    parse_failed: bool = False
    parse_error: str | None = None


class _MockParser:
    def __init__(self, result: _MockResult) -> None:
        self._result = result

    def parse(self, path: Path) -> _MockResult:
        return self._result


def _result_p1_imgdense(parse_failed: bool = False) -> _MockResult:
    """A docx-shaped result the real profiler classifies as P1_sop_imgdense.

    img_density 0.3 (30/100) ≥ 0.15 + list_ratio 0.4 (40/100) ≥ 0.3 + max_depth 4 ≥ 3.
    """
    headings = [_MockPara(kind="heading", heading_level=min(i + 1, 4)) for i in range(12)]
    lists = [_MockPara(kind="list_item") for _ in range(40)]
    return _MockResult(
        doc_format="docx",
        paragraphs_total=100,
        paragraphs=headings + lists,
        embedded_images=[object() for _ in range(30)],
        parse_failed=parse_failed,
        parse_error="boom" if parse_failed else None,
    )


# --------------------------------------------------------------------------- #
# harness (mirrors test_doc_profile_override.py)
# --------------------------------------------------------------------------- #


def _signals(**over: float) -> ProfileSignals:
    base: dict[str, Any] = dict(
        paragraphs=100,
        headings=10,
        max_depth=4,
        list_items=55,
        images=30,
        tables=2,
        img_density=0.3,
        head_density=0.1,
        list_ratio=0.55,
        tickbox_density=0.0,
    )
    base.update(over)
    return ProfileSignals(**base)


def _info(profile: str = "P2_prose", confidence: float = 0.8) -> DocProfileInfo:
    return DocProfileInfo.from_result(
        ProfileResult(profile=profile, confidence=confidence, signals=_signals()),  # type: ignore[arg-type]
        profiled_at="2026-06-15T00:00:00+00:00",
    )


class _MockEngine:
    def __init__(self, doc_ids: list[str]) -> None:
        self._rows = [{"doc_id": d} for d in doc_ids]

    async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict[str, Any]]:
        return self._rows


async def _kb_service() -> KBService:
    service = KBService(InMemoryKBBackend())
    await service.create(KbCreate(kb_id="kb1", name="KB One", description="", config=KbConfig()))
    return service


def _build_app(
    *,
    profile_store: InMemoryDocProfileStore | None,
    config_store: InMemoryDocConfigStore | None,
    kb_service: KBService,
    engine: _MockEngine | None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(kb_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service
    # W88 P0 F5 — POST /kb/{id}/profiles/backfill now gates on require_kb_acl("edit").
    # Override with an admin so the guard passes without a wired rbac_backend (admin
    # is unconditional per ADR-0027); the route's own 503/skip logic is unaffected.
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        oid="oid-admin", tid="t", preferred_username="admin@ricoh.com", role="admin"
    )
    if engine is not None:
        app.state.retrieval_engine = engine
    if profile_store is not None:
        app.state.doc_profile_store = profile_store
    if config_store is not None:
        app.state.doc_config_store = config_store
    return app


def _patch_source_and_parser(
    monkeypatch: pytest.MonkeyPatch,
    *,
    sources: dict[str, tuple[bytes, str] | None],
    results: dict[str, _MockResult],
) -> None:
    """Patch download_source_document (per doc_id) + select_parser (per filename)."""

    async def _fake_download(conn: str, kb_id: str, doc_id: str) -> tuple[bytes, str] | None:
        return sources.get(doc_id)

    def _fake_select_parser(path: Path, extract_images: bool = False) -> _MockParser:
        return _MockParser(results[path.name])

    monkeypatch.setattr(documents_routes, "download_source_document", _fake_download)
    monkeypatch.setattr(documents_routes, "select_parser", _fake_select_parser)


# --------------------------------------------------------------------------- #
# backfill endpoint
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_backfill_profiles_docs_without_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    config_store = InMemoryDocConfigStore()
    app = _build_app(
        profile_store=profile_store,
        config_store=config_store,
        kb_service=service,
        engine=_MockEngine(["doc-a", "doc-b"]),
    )
    _patch_source_and_parser(
        monkeypatch,
        sources={"doc-a": (b"x", "doc-a.docx"), "doc-b": (b"x", "doc-b.docx")},
        results={"doc-a.docx": _result_p1_imgdense(), "doc-b.docx": _result_p1_imgdense()},
    )

    resp = TestClient(app).post("/kb/kb1/profiles/backfill")
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["status"] == "profiled"
    assert body["profiled"] == 2
    assert body["profiles"] == {"doc-a": "P1_sop_imgdense", "doc-b": "P1_sop_imgdense"}
    # profile persisted for the read surface.
    persisted = await profile_store.get("kb1", "doc-a")
    assert persisted is not None and persisted.profile == "P1_sop_imgdense"
    # preset routed to per-doc config (no prior manual config → D6 writes).
    cfg = await config_store.get("kb1", "doc-a")
    assert cfg is not None and cfg.max_images_per_answer == 80


@pytest.mark.asyncio
async def test_backfill_skips_doc_with_existing_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    await profile_store.upsert("kb1", "doc-a", _info(profile="P2_prose"))
    app = _build_app(
        profile_store=profile_store,
        config_store=InMemoryDocConfigStore(),
        kb_service=service,
        engine=_MockEngine(["doc-a"]),
    )
    # download would raise if called — proving the idempotent skip short-circuits first.
    _patch_source_and_parser(monkeypatch, sources={}, results={})

    resp = TestClient(app).post("/kb/kb1/profiles/backfill")
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["profiled"] == 0
    assert body["skipped_has_profile"] == ["doc-a"]
    # untouched — system profile stays P2_prose.
    persisted = await profile_store.get("kb1", "doc-a")
    assert persisted is not None and persisted.profile == "P2_prose"


@pytest.mark.asyncio
async def test_backfill_skips_doc_without_source(monkeypatch: pytest.MonkeyPatch) -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    app = _build_app(
        profile_store=profile_store,
        config_store=InMemoryDocConfigStore(),
        kb_service=service,
        engine=_MockEngine(["doc-a"]),
    )
    _patch_source_and_parser(monkeypatch, sources={"doc-a": None}, results={})

    resp = TestClient(app).post("/kb/kb1/profiles/backfill")
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["profiled"] == 0
    assert body["skipped_no_source"] == ["doc-a"]
    assert await profile_store.get("kb1", "doc-a") is None


@pytest.mark.asyncio
async def test_backfill_per_doc_failure_does_not_abort(monkeypatch: pytest.MonkeyPatch) -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    app = _build_app(
        profile_store=profile_store,
        config_store=InMemoryDocConfigStore(),
        kb_service=service,
        engine=_MockEngine(["doc-bad", "doc-ok"]),
    )
    _patch_source_and_parser(
        monkeypatch,
        sources={"doc-bad": (b"x", "doc-bad.docx"), "doc-ok": (b"x", "doc-ok.docx")},
        results={
            "doc-bad.docx": _result_p1_imgdense(parse_failed=True),  # → RuntimeError in helper
            "doc-ok.docx": _result_p1_imgdense(),
        },
    )

    resp = TestClient(app).post("/kb/kb1/profiles/backfill")
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["profiled"] == 1
    assert body["profiles"] == {"doc-ok": "P1_sop_imgdense"}
    assert [f["doc_id"] for f in body["failed"]] == ["doc-bad"]


@pytest.mark.asyncio
async def test_backfill_503_when_no_profile_store(monkeypatch: pytest.MonkeyPatch) -> None:
    service = await _kb_service()
    app = _build_app(
        profile_store=None,
        config_store=InMemoryDocConfigStore(),
        kb_service=service,
        engine=_MockEngine(["doc-a"]),
    )
    resp = TestClient(app).post("/kb/kb1/profiles/backfill")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_backfill_route_skips_when_manual_config(monkeypatch: pytest.MonkeyPatch) -> None:
    # doc has NO profile (so backfill profiles it) but DOES have a manual per-doc config
    # → D6: profile persisted, but the preset route is skipped (manual config wins).
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    config_store = InMemoryDocConfigStore()
    await config_store.upsert("kb1", "doc-a", DocConfig(max_images_per_answer=3))
    app = _build_app(
        profile_store=profile_store,
        config_store=config_store,
        kb_service=service,
        engine=_MockEngine(["doc-a"]),
    )
    _patch_source_and_parser(
        monkeypatch,
        sources={"doc-a": (b"x", "doc-a.docx")},
        results={"doc-a.docx": _result_p1_imgdense()},
    )

    resp = TestClient(app).post("/kb/kb1/profiles/backfill")
    assert resp.status_code == 202, resp.text
    assert resp.json()["profiled"] == 1
    # profile persisted, but the manual config is preserved (D6 skip-if-manual).
    assert (await profile_store.get("kb1", "doc-a")) is not None
    cfg = await config_store.get("kb1", "doc-a")
    assert cfg is not None and cfg.max_images_per_answer == 3  # NOT the P1 preset's 80


@pytest.mark.asyncio
async def test_backfill_succeeds_without_ingestion_services(monkeypatch: pytest.MonkeyPatch) -> None:
    # No embedder / populator / chunker wired — backfill must still work, proving it
    # never touches the retrieval-mutating ingest path (zero retrieval impact).
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    app = _build_app(
        profile_store=profile_store,
        config_store=InMemoryDocConfigStore(),
        kb_service=service,
        engine=_MockEngine(["doc-a"]),
    )
    assert getattr(app.state, "index_populator", None) is None
    assert getattr(app.state, "embedder", None) is None
    _patch_source_and_parser(
        monkeypatch,
        sources={"doc-a": (b"x", "doc-a.docx")},
        results={"doc-a.docx": _result_p1_imgdense()},
    )

    resp = TestClient(app).post("/kb/kb1/profiles/backfill")
    assert resp.status_code == 202, resp.text
    assert resp.json()["profiled"] == 1


# --------------------------------------------------------------------------- #
# _backfill_one_doc_profile unit — D6 preserve manual_override on re-profile
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_backfill_one_doc_preserves_manual_override(monkeypatch: pytest.MonkeyPatch) -> None:
    # A prior row carries a human override; a (future force-mode) re-profile updates the
    # system fact but must preserve manual_override (D6 守 — same merge as ingest persist).
    profile_store = InMemoryDocProfileStore()
    config_store = InMemoryDocConfigStore()
    prior = _info(profile="P2_prose").model_copy(update={"manual_override": "P5_form"})
    await profile_store.upsert("kb1", "doc-a", prior)
    monkeypatch.setattr(
        documents_routes,
        "select_parser",
        lambda path, extract_images=False: _MockParser(_result_p1_imgdense()),
    )

    label = await documents_routes._backfill_one_doc_profile(
        kb_id="kb1",
        doc_id="doc-a",
        data=b"x",
        filename="doc-a.docx",
        kb_config=None,
        profile_store=profile_store,
        config_store=config_store,
    )
    assert label == "P1_sop_imgdense"
    persisted = await profile_store.get("kb1", "doc-a")
    assert persisted is not None
    assert persisted.profile == "P1_sop_imgdense"  # system re-detect updated
    assert persisted.manual_override == "P5_form"  # human override preserved

"""W79 / ADR-0058 — profile manual-override write surface tests (per CLAUDE.md §5.6 H6).

Coverage:
- PUT /kb/{kb_id}/docs/{doc_id}/profile — 套 preset 落 per-doc config + manual_override persist;
  system auto profile/confidence/signals 保留; 覆蓋現有 per-doc config; 404 未 ingest (no stored
  profile); 422 invalid profile (no routable preset); 503 when no store wired.
- list_documents summary effective resolve (manual_override 優先於 system auto).
- DocProfileInfo backward-compat (舊 W76 row 無 manual_override key → None) + re-ingest preserve
  merge 機制 (ADR-0058 D6 守).
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import documents as documents_routes
from api.schemas.doc_config import DocConfig
from api.schemas.doc_profile import DocProfileInfo
from api.schemas.kb import KbConfig, KbCreate
from ingestion.profiler import ProfileResult, ProfileSignals
from kb_management import KBService, get_kb_service
from kb_management.doc_config_store import InMemoryDocConfigStore
from kb_management.doc_profile_store import InMemoryDocProfileStore
from kb_management.storage import InMemoryKBBackend

# --------------------------------------------------------------------------- #
# helpers
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


def _info(profile: str = "P1_sop_imgdense", confidence: float = 0.9) -> DocProfileInfo:
    return DocProfileInfo.from_result(
        ProfileResult(profile=profile, confidence=confidence, signals=_signals()),  # type: ignore[arg-type]
        profiled_at="2026-06-15T00:00:00+00:00",
    )


class _MockEngine:
    """Minimal RetrievalEngine stand-in for list_documents."""

    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    async def list_documents(self, kb_id: str, max_chunks: int = 1000) -> list[dict[str, Any]]:
        return self._docs

    async def list_chunks(self, kb_id: str, doc_id: str) -> list[dict[str, Any]]:
        return []


async def _kb_service() -> KBService:
    service = KBService(InMemoryKBBackend())
    await service.create(KbCreate(kb_id="kb1", name="KB One", description="", config=KbConfig()))
    return service


def _doc_row(doc_id: str) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "doc_title": doc_id.upper(),
        "doc_format": "docx",
        "total_chunks": 5,
        "last_indexed_at": "2026-06-15T00:00:00Z",
        "source_url": None,
        "tags": [],
    }


def _build_app(
    profile_store: InMemoryDocProfileStore | None,
    config_store: InMemoryDocConfigStore | None,
    kb_service: KBService,
    engine: _MockEngine | None = None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(documents_routes.router)
    app.dependency_overrides[get_kb_service] = lambda: kb_service
    if engine is not None:
        app.state.retrieval_engine = engine
    if profile_store is not None:
        app.state.doc_profile_store = profile_store
    if config_store is not None:
        app.state.doc_config_store = config_store
    return app


# --------------------------------------------------------------------------- #
# override endpoint
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_override_applies_preset_and_records_annotation() -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    config_store = InMemoryDocConfigStore()
    await profile_store.upsert("kb1", "doc-A", _info(profile="P2_prose", confidence=0.7))
    app = _build_app(profile_store, config_store, service)

    resp = TestClient(app).put("/kb/kb1/docs/doc-A/profile", json={"profile": "P1_sop_imgdense"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # system auto profile 保留 (read-only fact), manual_override 額外記 override.
    assert body["profile"] == "P2_prose"
    assert body["confidence"] == 0.7
    assert body["manual_override"] == "P1_sop_imgdense"
    # 套 P1_sop_imgdense preset 落 per-doc config.
    cfg = await config_store.get("kb1", "doc-A")
    assert cfg is not None
    assert cfg.max_images_per_answer == 80
    assert cfg.enable_section_anchored_aux_images is True
    # manual_override persisted.
    persisted = await profile_store.get("kb1", "doc-A")
    assert persisted is not None and persisted.manual_override == "P1_sop_imgdense"


@pytest.mark.asyncio
async def test_override_overwrites_existing_manual_config() -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    config_store = InMemoryDocConfigStore()
    await profile_store.upsert("kb1", "doc-A", _info())
    # user 已手調 per-doc config — override 套 preset 覆蓋之 (ADR-0056 D3, 非 merge).
    await config_store.upsert("kb1", "doc-A", DocConfig(max_images_per_answer=3))
    app = _build_app(profile_store, config_store, service)

    resp = TestClient(app).put("/kb/kb1/docs/doc-A/profile", json={"profile": "P1_sop_text"})
    assert resp.status_code == 200, resp.text
    cfg = await config_store.get("kb1", "doc-A")
    assert cfg is not None and cfg.max_images_per_answer == 20  # P1_sop_text preset, 非舊 3


@pytest.mark.asyncio
async def test_override_404_when_not_profiled() -> None:
    service = await _kb_service()
    app = _build_app(InMemoryDocProfileStore(), InMemoryDocConfigStore(), service)
    resp = TestClient(app).put("/kb/kb1/docs/doc-X/profile", json={"profile": "P1_sop_imgdense"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_override_422_when_profile_has_no_preset() -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    await profile_store.upsert("kb1", "doc-A", _info())
    app = _build_app(profile_store, InMemoryDocConfigStore(), service)
    resp = TestClient(app).put("/kb/kb1/docs/doc-A/profile", json={"profile": "too_small"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_override_503_when_no_store() -> None:
    service = await _kb_service()
    app = _build_app(None, None, service)  # no stores wired
    resp = TestClient(app).put("/kb/kb1/docs/doc-A/profile", json={"profile": "P1_sop_imgdense"})
    assert resp.status_code == 503


# --------------------------------------------------------------------------- #
# list_documents effective resolve
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_documents_effective_profile_uses_override() -> None:
    service = await _kb_service()
    profile_store = InMemoryDocProfileStore()
    info = _info(profile="P2_prose", confidence=0.7).model_copy(
        update={"manual_override": "P1_sop_imgdense"}
    )
    await profile_store.upsert("kb1", "doc-A", info)
    engine = _MockEngine(docs=[_doc_row("doc-A")])
    app = _build_app(profile_store, InMemoryDocConfigStore(), service, engine=engine)

    resp = TestClient(app).get("/kb/kb1/documents")
    assert resp.status_code == 200, resp.text
    row = resp.json()[0]
    # L2 badge effective = manual_override (非 system auto P2_prose); override = human-set →
    # confidence null (L2 badge 唔顯示 % + 唔黃旗).
    assert row["profile"] == "P1_sop_imgdense"
    assert row["profile_confidence"] is None


# --------------------------------------------------------------------------- #
# schema backward-compat + re-ingest preserve mechanism
# --------------------------------------------------------------------------- #


def test_backward_compat_old_row_defaults_manual_override_none() -> None:
    # 舊 W76 row (無 manual_override key) deserialize → default None.
    dumped = _info().model_dump()
    dumped.pop("manual_override", None)
    reloaded = DocProfileInfo(**dumped)
    assert reloaded.manual_override is None


def test_reingest_preserve_merge_mechanism() -> None:
    # ADR-0058 D6 守 — re-ingest 取 fresh from_result (system re-detect) + preserve prior
    # manual_override annotation (per _run_ingest_pipeline merge logic).
    prior = _info(profile="P2_prose").model_copy(update={"manual_override": "P1_sop_imgdense"})
    fresh = _info(profile="P2_prose", confidence=0.75)  # re-detect, no override
    assert fresh.manual_override is None
    merged = fresh.model_copy(update={"manual_override": prior.manual_override})
    assert merged.manual_override == "P1_sop_imgdense"  # override preserved
    assert merged.confidence == 0.75  # system re-detect 更新 confidence

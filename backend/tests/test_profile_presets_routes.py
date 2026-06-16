"""W82 F2 / ADR-0063 — global profile→preset mapping CRUD route + call-site migrate.

Asserts the `/profile-presets` GET (effective factory view) / PUT (upsert override +
422 for non-routable) / DELETE (還原預設, idempotent 204) / 503 (unwired store), plus
that `_route_profile_preset` honours an admin override end-to-end (the call-site
migration `preset_for`→`resolve_preset`) and stays production-preserve without one.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import profile_presets as pp_route
from api.routes.documents import _route_profile_preset
from api.schemas.doc_config import DocConfig
from ingestion.profile_presets import preset_for
from ingestion.profiler import ProfileResult, ProfileSignals
from kb_management.doc_config_store import InMemoryDocConfigStore
from kb_management.preset_override_store import InMemoryPresetOverrideStore

_ROUTABLE = (
    "P1_sop_imgdense",
    "P1_sop_text",
    "P2_prose",
    "P3_slide_imgdense",
    "P3_slide_text",
    "P4_scan_imgdense",
    "P5_form",
)


def _app(*, wire_store: bool = True) -> FastAPI:
    app = FastAPI()
    if wire_store:
        app.state.preset_override_store = InMemoryPresetOverrideStore()
    app.include_router(pp_route.router)
    return app


def _profile_result(profile: str, confidence: float = 0.9) -> ProfileResult:
    sig = ProfileSignals(
        paragraphs=100,
        headings=10,
        max_depth=2,
        list_items=10,
        images=0,
        tables=0,
        img_density=0.0,
        head_density=0.1,
        list_ratio=0.1,
        tickbox_density=0.0,
    )
    return ProfileResult(profile=profile, confidence=confidence, signals=sig)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# GET — effective factory view
# --------------------------------------------------------------------------- #


def test_get_lists_routable_factory_presets() -> None:
    client = TestClient(_app())
    resp = client.get("/profile-presets")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [item["profile"] for item in body] == list(_ROUTABLE)  # mockup order
    assert all(item["overridden"] is False for item in body)
    p1 = next(i for i in body if i["profile"] == "P1_sop_imgdense")
    assert p1["config"]["max_images_per_answer"] == 80  # factory value


def test_get_excludes_non_routable_profiles() -> None:
    client = TestClient(_app())
    profiles = {i["profile"] for i in client.get("/profile-presets").json()}
    assert "too_small" not in profiles
    assert "unknown" not in profiles


# --------------------------------------------------------------------------- #
# PUT — upsert override + 422
# --------------------------------------------------------------------------- #


def test_put_override_then_get_reflects_it() -> None:
    client = TestClient(_app())
    put = client.put(
        "/profile-presets/P2_prose",
        json={"max_images_per_answer": 99, "answer_detail": "concise"},
    )
    assert put.status_code == 200, put.text
    assert put.json()["overridden"] is True
    assert put.json()["config"]["max_images_per_answer"] == 99

    p2 = next(i for i in client.get("/profile-presets").json() if i["profile"] == "P2_prose")
    assert p2["overridden"] is True
    assert p2["config"]["max_images_per_answer"] == 99  # not the factory 12


def test_put_replaces_existing_override() -> None:
    client = TestClient(_app())
    client.put("/profile-presets/P2_prose", json={"max_images_per_answer": 10})
    client.put("/profile-presets/P2_prose", json={"max_images_per_answer": 20})
    p2 = next(i for i in client.get("/profile-presets").json() if i["profile"] == "P2_prose")
    assert p2["config"]["max_images_per_answer"] == 20


@pytest.mark.parametrize("profile", ["too_small", "unknown", "P9_bogus", "garbage"])
def test_put_non_routable_profile_422(profile: str) -> None:
    client = TestClient(_app())
    resp = client.put(f"/profile-presets/{profile}", json={"max_images_per_answer": 5})
    assert resp.status_code == 422, resp.text


# --------------------------------------------------------------------------- #
# DELETE — 還原預設 (idempotent)
# --------------------------------------------------------------------------- #


def test_delete_restores_factory_idempotent() -> None:
    client = TestClient(_app())
    client.put("/profile-presets/P2_prose", json={"max_images_per_answer": 99})
    d1 = client.delete("/profile-presets/P2_prose")
    assert d1.status_code == 204
    d2 = client.delete("/profile-presets/P2_prose")  # already gone (還原預設)
    assert d2.status_code == 204
    # back to factory (overridden False + factory cap 12)
    p2 = next(i for i in client.get("/profile-presets").json() if i["profile"] == "P2_prose")
    assert p2["overridden"] is False
    assert p2["config"]["max_images_per_answer"] == 12


# --------------------------------------------------------------------------- #
# 503 — store not wired
# --------------------------------------------------------------------------- #


def test_endpoints_503_when_store_unwired() -> None:
    client = TestClient(_app(wire_store=False))
    assert client.get("/profile-presets").status_code == 503
    assert client.put("/profile-presets/P2_prose", json={}).status_code == 503
    assert client.delete("/profile-presets/P2_prose").status_code == 503


# --------------------------------------------------------------------------- #
# call-site migration — _route_profile_preset honours the override (F2.3)
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_route_preset_honours_admin_override() -> None:
    config_store = InMemoryDocConfigStore()
    override_store = InMemoryPresetOverrideStore()
    # admin edits P1's global mapping cap 80 → 7.
    await override_store.upsert("P1_sop_imgdense", DocConfig(max_images_per_answer=7))
    await _route_profile_preset(
        store=config_store,
        kb_id="kb1",
        doc_id="d1",
        profile=_profile_result("P1_sop_imgdense"),
        preset_override_store=override_store,
    )
    written = await config_store.get("kb1", "d1")
    assert written is not None
    assert written.max_images_per_answer == 7  # edited override, not factory 80


@pytest.mark.asyncio
async def test_route_preset_production_preserve_without_override() -> None:
    # No override stored → factory preset routed (bit-identical to pre-W82).
    config_store = InMemoryDocConfigStore()
    override_store = InMemoryPresetOverrideStore()
    await _route_profile_preset(
        store=config_store,
        kb_id="kb1",
        doc_id="d1",
        profile=_profile_result("P1_sop_imgdense"),
        preset_override_store=override_store,
    )
    written = await config_store.get("kb1", "d1")
    assert written is not None
    assert written.max_images_per_answer == preset_for("P1_sop_imgdense").max_images_per_answer

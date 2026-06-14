"""profile→preset routing tests (ADR-0056 層 A 段 ②a+②b / W73; per CLAUDE.md §5.6 H6).

Coverage:
- PROFILE_PRESETS values (P1_sop_imgdense 對齊 drive-images-1 good config;
  P2_prose neighbour off; too_small / unknown = None inherit)
- preset_for returns a fresh copy (no shared singleton instance)
- _route_profile_preset (caller routing policy):
  - auto-write when the doc has no per-doc config
  - D6 守: existing manual config → skip (never overwrite)
  - None preset (too_small / unknown) → no write (inherit, D7)
"""

from __future__ import annotations

import pytest

from api.routes.documents import _route_profile_preset
from api.schemas.doc_config import DocConfig
from ingestion.profile_presets import PROFILE_PRESETS, preset_for
from ingestion.profiler import ProfileResult, ProfileSignals
from kb_management.doc_config_store import InMemoryDocConfigStore


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


# --- PROFILE_PRESETS values ---


def test_p1_imgdense_preset_aligns_good_config() -> None:
    # drive-images-1 已驗 good config — auto-write 對 P1 不退化 (R1 緩解)。
    p = PROFILE_PRESETS["P1_sop_imgdense"]
    assert p is not None
    assert p.max_images_per_answer == 80
    assert p.enable_citation_neighbour_images is True
    assert p.citation_neighbour_max_aux_images == 40
    assert p.enable_inline_image_markers is True
    assert p.enable_section_anchored_aux_images is True  # W75 / ADR-0056 段②d 方案 A
    assert p.enable_chapter_overview_pin is True
    assert p.answer_detail == "detailed"


def test_p2_prose_neighbour_off() -> None:
    # D1 — 散文唔做 neighbour-image 避錯位。
    p = PROFILE_PRESETS["P2_prose"]
    assert p is not None
    assert p.enable_citation_neighbour_images is False


def test_too_small_unknown_no_preset() -> None:
    assert PROFILE_PRESETS["too_small"] is None
    assert PROFILE_PRESETS["unknown"] is None
    assert preset_for("too_small") is None
    assert preset_for("unknown") is None


def test_preset_for_returns_copy() -> None:
    a = preset_for("P1_sop_imgdense")
    b = preset_for("P1_sop_imgdense")
    assert a is not None and b is not None
    assert a is not b  # fresh copy, never the shared module-level instance


# --- _route_profile_preset (D6 守 / auto-write / inherit) ---


@pytest.mark.asyncio
async def test_routing_auto_writes_when_no_existing() -> None:
    store = InMemoryDocConfigStore()
    await _route_profile_preset(
        store=store,
        kb_id="kb1",
        doc_id="d1",
        profile=_profile_result("P1_sop_imgdense"),
    )
    written = await store.get("kb1", "d1")
    assert written is not None
    assert written.max_images_per_answer == 80


@pytest.mark.asyncio
async def test_routing_d6_skips_existing_manual() -> None:
    store = InMemoryDocConfigStore()
    manual = DocConfig(max_images_per_answer=5)  # KB owner 手動值
    await store.upsert("kb1", "d1", manual)
    await _route_profile_preset(
        store=store,
        kb_id="kb1",
        doc_id="d1",
        profile=_profile_result("P1_sop_imgdense"),
    )
    # D6 — manual config 不被 P1 preset(cap=80)覆蓋
    kept = await store.get("kb1", "d1")
    assert kept is not None
    assert kept.max_images_per_answer == 5


@pytest.mark.asyncio
async def test_routing_none_preset_no_write() -> None:
    store = InMemoryDocConfigStore()
    await _route_profile_preset(
        store=store,
        kb_id="kb1",
        doc_id="d1",
        profile=_profile_result("too_small"),
    )
    # too_small → 唔 routing,inherit per-KB/global (D7)
    assert await store.get("kb1", "d1") is None

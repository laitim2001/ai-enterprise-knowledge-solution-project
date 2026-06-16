"""Global profile→preset mapping CRUD endpoints (W82 / ADR-0063 — 層 A 段③ 缺口 B).

The Settings →「文件分類規則」admin surface. Edits the GLOBAL profile→preset mapping
that the ingest router / manual-override / backfill paths read via `resolve_preset`
(`override ?? factory`). Backed by the `PresetOverrideStore` wired on app.state.

    GET    /profile-presets           → [{profile, config (effective), overridden}]
    PUT    /profile-presets/{profile} → upsert override DocConfig, returns the item
    DELETE /profile-presets/{profile} → 204 (還原預設 — restore the factory value)

`config` is the EFFECTIVE mapping (admin override overlaid on the hardcoded factory
`PROFILE_PRESETS`); `overridden=True` flags a profile the admin has edited (the UI
shows a「已覆寫」badge + enables 還原預設). Only the routable profiles (those with a
factory preset — P1-P5) are listed / editable; ``too_small`` / ``unknown`` inherit
and are not part of the mapping surface (PUT → 422).

GLOBAL scope — no ``kb_id`` (per-KB / per-doc overrides are separate layers,
ADR-0040 / ADR-0050 / ADR-0058). The edit only affects FUTURE routing (next ingest /
manual override / backfill); existing per-doc configs are not re-routed (ADR-0063).
"""

from typing import cast

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from api.schemas.doc_config import DocConfig
from ingestion.profile_presets import PROFILE_PRESETS, preset_for
from ingestion.profiler import DocProfile
from kb_management.preset_override_store import PresetOverrideStore

router = APIRouter()


class PresetMappingItem(BaseModel):
    """One row of the profile→preset mapping (effective view).

    `config` overlays the admin override (if any) on the factory preset.
    `overridden` flags an admin-edited profile (UI「已覆寫」badge + 還原預設).
    """

    profile: str
    config: DocConfig
    overridden: bool


def _store(request: Request) -> PresetOverrideStore:
    store: PresetOverrideStore | None = getattr(
        request.app.state, "preset_override_store", None
    )
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="preset-override store not initialized",
        )
    return store


def _routable_profiles() -> list[DocProfile]:
    """Factory profiles that carry a routable preset (P1-P5) — the editable surface.

    Excludes ``too_small`` / ``unknown`` (factory `None` → inherit, not part of the
    mapping). Insertion order matches the mockup table.
    """
    return [profile for profile, preset in PROFILE_PRESETS.items() if preset is not None]


@router.get("/profile-presets", response_model=list[PresetMappingItem])
async def list_profile_presets(request: Request) -> list[PresetMappingItem]:
    """Return the effective profile→preset mapping (factory overlaid by admin override)."""
    overrides = await _store(request).list_all()
    items: list[PresetMappingItem] = []
    for profile in _routable_profiles():
        override = overrides.get(profile)
        # factory preset is guaranteed non-None here (_routable_profiles filters it).
        effective = override or cast(DocConfig, preset_for(profile))
        items.append(
            PresetMappingItem(
                profile=profile,
                config=effective,
                overridden=override is not None,
            )
        )
    return items


@router.put("/profile-presets/{profile}", response_model=PresetMappingItem)
async def put_profile_preset(
    profile: str,
    config: DocConfig,
    request: Request,
) -> PresetMappingItem:
    """Upsert the admin override for ``profile``; returns the new effective item.

    422 when ``profile`` is not a routable factory profile (``too_small`` / ``unknown``
    / unknown label) — the mapping surface only edits P1-P5.
    """
    # preset_for narrows a free-form label via dict.get → None for non-routable /
    # invalid labels (same guard as documents.override_doc_profile). cast is runtime-safe.
    if preset_for(cast(DocProfile, profile)) is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Profile '{profile}' is not an editable mapping target. Use one of "
                "P1_sop_imgdense / P1_sop_text / P2_prose / P3_slide_imgdense / "
                "P3_slide_text / P4_scan_imgdense / P5_form."
            ),
        )
    stored = await _store(request).upsert(profile, config)
    return PresetMappingItem(profile=profile, config=stored, overridden=True)


@router.delete("/profile-presets/{profile}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile_preset(profile: str, request: Request) -> None:
    """Delete the admin override (還原預設 — restore the factory value). Idempotent (204)."""
    await _store(request).delete(profile)

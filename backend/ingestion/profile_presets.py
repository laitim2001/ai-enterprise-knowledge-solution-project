"""Profile → per-document preset mapping (ADR-0056 層 A 段 ②b / W73).

Maps a W72 `DocumentProfiler` classification to a per-doc `DocConfig` preset that
the ingest router (`documents.py:_run_ingest_pipeline`) conservatively auto-writes
— ONLY when the doc has no manual per-doc config (D6 admin override 守).

Preset values 對齊 ADR-0056 D1 流程 + 已驗 good config:
- `P1_sop_imgdense` = drive-images-1 已驗 good config (cap=80 / neighbour / max_aux=40 /
  markers / overview_pin) → auto-write 對 P1 不退化 (W73 R1 緩解)。
- 其他 profile = D1 描述 + D7 保守 default;中值未逐一實證,段③ UI 俾 admin 調 mapping。
- `too_small` / `unknown` → None (唔 routing,inherit per-KB / global,D7 保守)。

`DocConfig` 只含 post-retrieval 旋鈕 (ADR-0050) — top_k / rerank / parent_doc 係
per-KB,preset 掂唔到。每個 `None` field = inherit 下一層 (per-KB → global)。
"""

from __future__ import annotations

from api.schemas.doc_config import DocConfig
from ingestion.profiler import DocProfile

# 每 profile 套嘅 per-doc 後處理 preset。None = 唔 routing (inherit)。
PROFILE_PRESETS: dict[DocProfile, DocConfig | None] = {
    # 圖密結構化 SOP — drive-images-1 已驗 good config (避退化)。
    # W75 / ADR-0056 段②d — section 級錨定 (方案 A) 只開呢個 profile (結構化 SOP 收益高
    # 錯位風險低;P2/prose 留 False 避反噬,per ADR-0056 D7 條件式)。
    "P1_sop_imgdense": DocConfig(
        max_images_per_answer=80,
        enable_citation_neighbour_images=True,
        citation_neighbour_max_aux_images=40,
        citation_neighbour_section_path_prefix_depth=1,
        enable_inline_image_markers=True,
        enable_section_anchored_aux_images=True,
        enable_chapter_overview_pin=True,
        answer_detail="detailed",
    ),
    # 純文字步驟型 SOP — 步驟錨定 + 低圖 cap。
    "P1_sop_text": DocConfig(
        max_images_per_answer=20,
        enable_citation_neighbour_images=True,
        citation_neighbour_max_aux_images=10,
        citation_neighbour_section_path_prefix_depth=1,
        enable_inline_image_markers=True,
        enable_chapter_overview_pin=True,
        answer_detail="detailed",
    ),
    # 散文政策 / 報告 — D1 唔做 neighbour 避錯位;散文要完整。
    "P2_prose": DocConfig(
        max_images_per_answer=12,
        enable_citation_neighbour_images=False,
        enable_inline_image_markers=False,
        enable_chapter_overview_pin=False,
        answer_detail="detailed",
    ),
    # 圖密簡報 — 開圖流程。
    "P3_slide_imgdense": DocConfig(
        max_images_per_answer=40,
        enable_citation_neighbour_images=True,
        citation_neighbour_max_aux_images=20,
        citation_neighbour_section_path_prefix_depth=1,
        enable_inline_image_markers=True,
        enable_chapter_overview_pin=False,
        answer_detail="concise",
    ),
    # 文字簡報 — 低圖。
    "P3_slide_text": DocConfig(
        max_images_per_answer=12,
        enable_citation_neighbour_images=False,
        enable_inline_image_markers=False,
        enable_chapter_overview_pin=False,
        answer_detail="concise",
    ),
    # 掃描 / 純圖 — 純 gallery。
    "P4_scan_imgdense": DocConfig(
        max_images_per_answer=20,
        enable_citation_neighbour_images=False,
        enable_inline_image_markers=False,
        enable_chapter_overview_pin=False,
        answer_detail="concise",
    ),
    # 表單 / 問卷 — table 為主、末尾堆。
    "P5_form": DocConfig(
        max_images_per_answer=8,
        enable_citation_neighbour_images=False,
        enable_inline_image_markers=False,
        enable_chapter_overview_pin=False,
        answer_detail="concise",
    ),
    # 噪音 / 無法判斷 — D7 保守,唔 routing。
    "too_small": None,
    "unknown": None,
}


def preset_for(profile: DocProfile) -> DocConfig | None:
    """Return a fresh copy of the auto-write preset for ``profile``, or ``None``.

    ``None`` means no routing (the doc inherits per-KB / global). A copy is returned
    so callers / the in-memory store never share the module-level preset instance.
    """
    preset = PROFILE_PRESETS.get(profile)
    return preset.model_copy() if preset is not None else None

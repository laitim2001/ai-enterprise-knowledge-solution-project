"""W43 F1.8 — EffectiveConfig resolver + image cap + KbConfig back-compat (ADR-0040).

Covers the three F1 acceptance pillars:
- resolver priority: per-query > per-KB (non-None) > global Settings default
- production-preserve (G7): a KB with no explicit knob resolves bit-identical to global
- KbConfig migration-default (F1.7): a legacy config dict missing the W43 keys parses
  with all-None knobs (zero breaking change, ADR-0028 precedent)
- cap_images_per_answer (F1.6): blunt per-answer image ceiling
"""

from __future__ import annotations

from api.schemas.doc_config import DocConfig
from api.schemas.kb import KbConfig
from api.schemas.query import Citation, ImageRef
from generation.citation_enrichment import cap_images_per_answer
from generation.effective_config import (
    PerQueryOverrides,
    resolve_effective_config,
)
from storage.settings import Settings


def _settings() -> Settings:
    """Deterministic global baseline — ignore any repo-root .env so the class
    defaults drive the assertions."""
    return Settings(_env_file=None)


# --------------------------------------------------------------------------- #
# resolver — global inherit (kb_config=None) == production-preserve (G7)
# --------------------------------------------------------------------------- #


def test_resolve_no_kb_config_inherits_every_global_default() -> None:
    s = _settings()
    eff = resolve_effective_config(s, kb_config=None)

    # Every tunable knob falls through to the global Settings value.
    assert eff.enable_parent_doc_retrieval == s.enable_parent_doc_retrieval
    assert eff.parent_doc_section_depth_offset == s.parent_doc_section_depth_offset
    assert eff.parent_doc_top_k == s.parent_doc_top_k
    assert eff.parent_doc_max_tokens_per_parent == s.parent_doc_max_tokens_per_parent
    assert eff.enable_citation_post_hoc_expansion == s.enable_citation_post_hoc_expansion
    assert eff.citation_expansion_max_aux == s.citation_expansion_max_aux
    assert eff.citation_expansion_window == s.citation_expansion_window
    assert (
        eff.citation_expansion_section_path_prefix_depth
        == s.citation_expansion_section_path_prefix_depth
    )
    assert eff.enable_citation_neighbour_images == s.enable_citation_neighbour_images
    assert eff.citation_neighbour_max_aux_images == s.citation_neighbour_max_aux_images
    assert (
        eff.citation_neighbour_section_path_prefix_depth
        == s.citation_neighbour_section_path_prefix_depth
    )
    # global-only pass-throughs (no per-KB knob in MVP)
    assert eff.parent_doc_max_chunks_per_parent == s.parent_doc_max_chunks_per_parent
    assert eff.parent_doc_fallback_to_doc_on_shallow == s.parent_doc_fallback_to_doc_on_shallow
    assert eff.citation_neighbour_window == s.citation_neighbour_window
    # max_images_per_answer has no global field → None by default (no backend cap)
    assert eff.max_images_per_answer is None
    # CH-007 — top_k overfetch + rerank depth fall through to the global retrieval defaults
    assert eff.default_top_k == s.hybrid_top_k_retrieval
    assert eff.default_rerank_k == s.rerank_top_k


def test_resolve_empty_kb_config_is_bit_identical_to_global() -> None:
    """G7 back-compat — an all-None KbConfig resolves exactly like kb_config=None."""
    s = _settings()
    eff_none = resolve_effective_config(s, kb_config=None)
    eff_empty = resolve_effective_config(s, kb_config=KbConfig())
    assert eff_none == eff_empty


# --------------------------------------------------------------------------- #
# resolver — per-KB override wins over global
# --------------------------------------------------------------------------- #


def test_resolve_per_kb_overrides_global() -> None:
    s = _settings()
    kb = KbConfig(
        enable_parent_doc_retrieval=True,
        parent_doc_section_depth_offset=2,
        citation_expansion_max_aux=10,
        citation_expansion_section_path_prefix_depth=1,
        enable_citation_neighbour_images=False,
        max_images_per_answer=8,
    )
    eff = resolve_effective_config(s, kb_config=kb)

    # set per-KB fields win
    assert eff.enable_parent_doc_retrieval is True
    assert eff.parent_doc_section_depth_offset == 2
    assert eff.citation_expansion_max_aux == 10
    assert eff.citation_expansion_section_path_prefix_depth == 1
    assert eff.enable_citation_neighbour_images is False
    assert eff.max_images_per_answer == 8
    # un-set per-KB fields still inherit global
    assert eff.parent_doc_top_k == s.parent_doc_top_k
    assert eff.citation_expansion_window == s.citation_expansion_window


def test_resolve_per_kb_false_flag_overrides_true_global() -> None:
    """A per-KB `False` must win over a `True` global (not be treated as 'unset')."""
    s = Settings(_env_file=None, enable_citation_post_hoc_expansion=True)
    kb = KbConfig(enable_citation_post_hoc_expansion=False)
    eff = resolve_effective_config(s, kb_config=kb)
    assert eff.enable_citation_post_hoc_expansion is False


# --------------------------------------------------------------------------- #
# resolver — per-query override wins over per-KB and global
# --------------------------------------------------------------------------- #


def test_resolve_per_query_overrides_per_kb_and_global() -> None:
    s = _settings()
    kb = KbConfig(parent_doc_top_k=2, max_images_per_answer=8)
    pq = PerQueryOverrides(parent_doc_top_k=5, max_images_per_answer=3)
    eff = resolve_effective_config(s, kb_config=kb, per_query=pq)
    assert eff.parent_doc_top_k == 5  # per-query beats per-KB(2) + global
    assert eff.max_images_per_answer == 3  # per-query beats per-KB(8)


def test_resolve_per_query_partial_falls_through_to_per_kb() -> None:
    s = _settings()
    kb = KbConfig(parent_doc_top_k=4)
    pq = PerQueryOverrides()  # all None — no override
    eff = resolve_effective_config(s, kb_config=kb, per_query=pq)
    assert eff.parent_doc_top_k == 4  # per-KB (per-query all-None)


# --------------------------------------------------------------------------- #
# CH-007 — default_top_k / default_rerank_k resolution (per-query > per-KB > global)
# --------------------------------------------------------------------------- #


def test_resolve_ch007_top_k_per_kb_overrides_global() -> None:
    """A KB's saved default_top_k / default_rerank_k win over the global retrieval
    defaults — the chat path (no per-query top_k) then uses the KB's values."""
    s = _settings()
    kb = KbConfig(default_top_k=80, default_rerank_k=20)
    eff = resolve_effective_config(s, kb_config=kb)
    assert eff.default_top_k == 80
    assert eff.default_rerank_k == 20


def test_resolve_ch007_top_k_per_query_overrides_per_kb_and_global() -> None:
    """An explicit per-query top_k (eval harness / tests) beats the per-KB default."""
    s = _settings()
    kb = KbConfig(default_top_k=80, default_rerank_k=20)
    pq = PerQueryOverrides(default_top_k=12, default_rerank_k=3)
    eff = resolve_effective_config(s, kb_config=kb, per_query=pq)
    assert eff.default_top_k == 12  # per-query beats per-KB(80) + global
    assert eff.default_rerank_k == 3  # per-query beats per-KB(20)


def test_resolve_ch007_top_k_none_per_query_falls_through_to_per_kb() -> None:
    """The chat path sends neither top_k → PerQueryOverrides all-None → KB default wins."""
    s = _settings()
    kb = KbConfig(default_top_k=80, default_rerank_k=20)
    eff = resolve_effective_config(s, kb_config=kb, per_query=PerQueryOverrides())
    assert eff.default_top_k == 80
    assert eff.default_rerank_k == 20


# --------------------------------------------------------------------------- #
# W57 / ADR-0050 — per-DOC layer (per-query > per-DOC > per-KB > global)
# --------------------------------------------------------------------------- #


def test_resolve_doc_config_none_is_bit_identical() -> None:
    """G7 production-preserve — doc_config=None resolves exactly like the per-KB-only
    chain (the W57 doc layer is a strict superset that no-ops when absent)."""
    s = _settings()
    kb = KbConfig(citation_expansion_max_aux=10, max_images_per_answer=8)
    assert resolve_effective_config(s, kb) == resolve_effective_config(s, kb, None, None)
    assert resolve_effective_config(s, kb) == resolve_effective_config(
        s, kb, doc_config=DocConfig()
    )


def test_resolve_per_doc_overrides_per_kb_for_post_retrieval_knobs() -> None:
    s = _settings()
    kb = KbConfig(
        citation_expansion_max_aux=10,
        max_images_per_answer=8,
        answer_detail="concise",
        enable_chapter_overview_pin=False,
    )
    dc = DocConfig(
        citation_expansion_max_aux=18,
        max_images_per_answer=30,
        answer_detail="detailed",
        enable_chapter_overview_pin=True,
    )
    eff = resolve_effective_config(s, kb, doc_config=dc)
    # per-DOC wins over per-KB for every post-retrieval knob it sets
    assert eff.citation_expansion_max_aux == 18
    assert eff.max_images_per_answer == 30
    assert eff.answer_detail == "detailed"
    assert eff.enable_chapter_overview_pin is True


def test_resolve_per_doc_partial_falls_through_to_per_kb() -> None:
    """A DocConfig only overrides the knobs it sets; the rest inherit per-KB."""
    s = _settings()
    kb = KbConfig(citation_expansion_max_aux=10, citation_expansion_window=2)
    dc = DocConfig(citation_expansion_max_aux=18)  # window left None
    eff = resolve_effective_config(s, kb, doc_config=dc)
    assert eff.citation_expansion_max_aux == 18  # per-DOC
    assert eff.citation_expansion_window == 2  # per-KB (doc didn't set it)


def test_resolve_per_doc_does_not_touch_retrieval_entry_knobs() -> None:
    """DocConfig has no retrieval-entry fields, so top_k / rerank / parent_doc stay
    resolved from per-KB (per ADR-0050 — these are consumed before any doc is cited)."""
    s = _settings()
    kb = KbConfig(
        default_top_k=80,
        default_rerank_k=20,
        enable_parent_doc_retrieval=True,
        parent_doc_top_k=4,
    )
    dc = DocConfig(citation_expansion_max_aux=18)
    eff = resolve_effective_config(s, kb, doc_config=dc)
    assert eff.default_top_k == 80
    assert eff.default_rerank_k == 20
    assert eff.enable_parent_doc_retrieval is True
    assert eff.parent_doc_top_k == 4


def test_resolve_per_query_beats_per_doc() -> None:
    """per-query override still wins over the per-DOC layer (chain head)."""
    s = _settings()
    kb = KbConfig(max_images_per_answer=8)
    dc = DocConfig(max_images_per_answer=30)
    pq = PerQueryOverrides(max_images_per_answer=3)
    eff = resolve_effective_config(s, kb, per_query=pq, doc_config=dc)
    assert eff.max_images_per_answer == 3  # per-query > per-DOC(30) > per-KB(8)


def test_resolve_per_doc_false_flag_overrides_true_per_kb() -> None:
    """A per-DOC `False` must win over a per-KB `True` (not be read as 'unset')."""
    s = _settings()
    kb = KbConfig(enable_citation_neighbour_images=True)
    dc = DocConfig(enable_citation_neighbour_images=False)
    eff = resolve_effective_config(s, kb, doc_config=dc)
    assert eff.enable_citation_neighbour_images is False


# --------------------------------------------------------------------------- #
# KbConfig migration-default (F1.7) — legacy dict missing W43 keys
# --------------------------------------------------------------------------- #


def test_kb_config_legacy_dict_without_w43_keys_parses_with_none() -> None:
    """A KbConfig persisted before W43 (JSONB lacks the new keys) reconstructs with
    all knob fields None → inherits global → bit-identical behaviour (ADR-0028)."""
    legacy = {
        "embedding_model": "text-embedding-3-large",
        "embedding_dimension": 1024,
        "chunk_strategy": "auto",
        "default_top_k": 50,
        "default_rerank_k": 5,
        "extract_embedded_images": False,
        "slide_screenshots": True,
        "dedup_strategy": "sha256",
        "return_images_in_chat": False,
    }
    cfg = KbConfig(**legacy)
    assert cfg.enable_parent_doc_retrieval is None
    assert cfg.parent_doc_section_depth_offset is None
    assert cfg.citation_expansion_max_aux is None
    assert cfg.enable_citation_neighbour_images is None
    assert cfg.max_images_per_answer is None
    # and it resolves to global-identical
    s = _settings()
    assert resolve_effective_config(s, cfg) == resolve_effective_config(s, None)


# --------------------------------------------------------------------------- #
# cap_images_per_answer (F1.6)
# --------------------------------------------------------------------------- #


def _img(i: int) -> ImageRef:
    return ImageRef(
        blob_url=f"blob://img-{i}",
        alt_text=f"img {i}",
        checksum_sha256=f"sha-{i}",
        width=10,
        height=10,
    )


def _citation(chunk_id: str, n_images: int, img_offset: int = 0) -> Citation:
    """`img_offset` keeps checksums DISTINCT across citations — under ADR-0054 the
    cap budget counts unique images, so tests of the cumulative budget must not
    accidentally exercise the dedup path (and the dedup tests set offsets to
    overlap on purpose)."""
    return Citation(
        chunk_id=chunk_id,
        doc_id="doc-a",
        doc_title="Doc A",
        doc_format="docx",
        chunk_title="T",
        chunk_index=0,
        section_path=["Doc"],
        relevance_score=0.9,
        embedded_images=[_img(i) for i in range(img_offset, img_offset + n_images)],
    )


def test_cap_none_returns_unchanged() -> None:
    cites = [_citation("c1", 5), _citation("c2", 5)]
    out = cap_images_per_answer(cites, None)
    # None = no cap AND no dedup (ADR-0054 keeps the capless path bit-identical),
    # even though c1/c2 here share every checksum.
    assert out is cites  # no copy when no cap (production-preserve)


def test_cap_trims_cumulative_total_across_citations() -> None:
    # Distinct checksums (ADR-0054 rewrite — the old fixture shared sha-0..4 across
    # both citations, so the unique-counting budget would dedup c2 to zero).
    cites = [_citation("c1", 5), _citation("c2", 5, img_offset=5)]
    out = cap_images_per_answer(cites, 7)
    total = sum(len(c.embedded_images) for c in out)
    assert total == 7
    assert len(out[0].embedded_images) == 5  # first citation keeps all
    assert len(out[1].embedded_images) == 2  # second trimmed to remaining budget
    # citations themselves never dropped
    assert [c.chunk_id for c in out] == ["c1", "c2"]


def test_cap_zero_strips_all_images_but_keeps_citations() -> None:
    cites = [_citation("c1", 3), _citation("c2", 2, img_offset=3)]
    out = cap_images_per_answer(cites, 0)
    assert all(len(c.embedded_images) == 0 for c in out)
    assert [c.chunk_id for c in out] == ["c1", "c2"]


def test_cap_above_total_keeps_objects_untrimmed() -> None:
    cites = [_citation("c1", 2), _citation("c2", 1, img_offset=2)]
    out = cap_images_per_answer(cites, 99)
    # untrimmed citations preserve the original objects (no needless copy)
    assert out[0] is cites[0]
    assert out[1] is cites[1]


def test_cap_dedup_duplicate_refs_consume_no_budget() -> None:
    """ADR-0054 core: c2 re-embeds c1's images (the W67 neighbour-aux overlap shape).
    The dups are dropped without eating budget, so c3's FRESH images still fit —
    under the old ref-counting walk c2's dups would have exhausted the budget and
    zeroed c3 (the 'cited but zeroed' failure W67 mapped)."""
    cites = [
        _citation("c1", 4),  # sha-0..3 fresh
        _citation("c2", 4),  # sha-0..3 again — all dups
        _citation("c3", 3, img_offset=4),  # sha-4..6 fresh
    ]
    out = cap_images_per_answer(cites, 7)
    assert len(out[0].embedded_images) == 4
    assert len(out[1].embedded_images) == 0  # dups dropped, no budget consumed
    assert len(out[2].embedded_images) == 3  # fresh images still within budget
    kept_keys = [i.checksum_sha256 for c in out for i in c.embedded_images]
    assert len(kept_keys) == len(set(kept_keys)) == 7


def test_cap_dedup_drops_dups_even_with_budget_left() -> None:
    """ADR-0054 payload hygiene: a dup is dropped even when budget remains."""
    cites = [_citation("c1", 2), _citation("c2", 2)]  # c2 = same sha-0..1
    out = cap_images_per_answer(cites, 99)
    assert len(out[0].embedded_images) == 2
    assert len(out[1].embedded_images) == 0


def test_cap_dedup_within_one_citation() -> None:
    """Within-citation duplicate refs collapse too (same seen-set walk)."""
    dup = _img(0)
    cite = Citation(
        chunk_id="c1",
        doc_id="doc-a",
        doc_title="Doc A",
        doc_format="docx",
        chunk_title="T",
        chunk_index=0,
        section_path=["Doc"],
        relevance_score=0.9,
        embedded_images=[dup, _img(1), dup],
    )
    out = cap_images_per_answer([cite], 10)
    assert [i.checksum_sha256 for i in out[0].embedded_images] == ["sha-0", "sha-1"]


# --------------------------------------------------------------------------- #
# W70 / ADR-0055 - enable_inline_image_markers four-layer resolution
# --------------------------------------------------------------------------- #


def test_w70_markers_global_default_off_inherited() -> None:
    """G3 zero-regression: global default False; kb_config=None AND an all-None
    KbConfig both resolve OFF - identical to pre-W70 behaviour."""
    s = _settings()
    assert s.enable_inline_image_markers is False
    assert resolve_effective_config(s, kb_config=None).enable_inline_image_markers is False
    assert resolve_effective_config(s, kb_config=KbConfig()).enable_inline_image_markers is False


def test_w70_markers_per_kb_on_overrides_global_off() -> None:
    s = _settings()
    kb = KbConfig(enable_inline_image_markers=True)
    eff = resolve_effective_config(s, kb_config=kb)
    assert eff.enable_inline_image_markers is True


def test_w70_markers_per_doc_overrides_per_kb() -> None:
    """Per-DOC layer (ADR-0050) sits between per-query and per-KB."""
    s = _settings()
    kb = KbConfig(enable_inline_image_markers=True)
    dc = DocConfig(enable_inline_image_markers=False)
    eff = resolve_effective_config(s, kb_config=kb, doc_config=dc)
    assert eff.enable_inline_image_markers is False


def test_w70_markers_per_query_wins_over_all_layers() -> None:
    s = _settings()
    kb = KbConfig(enable_inline_image_markers=True)
    dc = DocConfig(enable_inline_image_markers=True)
    pq = PerQueryOverrides(enable_inline_image_markers=False)
    eff = resolve_effective_config(s, kb_config=kb, doc_config=dc, per_query=pq)
    assert eff.enable_inline_image_markers is False


def test_w70_markers_legacy_kb_config_dict_parses_all_none() -> None:
    """Migration-default (ADR-0028 precedent): a persisted pre-W70 config dict
    without the new key reconstructs with None -> inherits global OFF."""
    kb = KbConfig.model_validate({"default_top_k": 50})
    assert kb.enable_inline_image_markers is None
    eff = resolve_effective_config(_settings(), kb_config=kb)
    assert eff.enable_inline_image_markers is False

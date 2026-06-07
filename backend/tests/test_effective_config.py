"""W43 F1.8 — EffectiveConfig resolver + image cap + KbConfig back-compat (ADR-0040).

Covers the three F1 acceptance pillars:
- resolver priority: per-query > per-KB (non-None) > global Settings default
- production-preserve (G7): a KB with no explicit knob resolves bit-identical to global
- KbConfig migration-default (F1.7): a legacy config dict missing the W43 keys parses
  with all-None knobs (zero breaking change, ADR-0028 precedent)
- cap_images_per_answer (F1.6): blunt per-answer image ceiling
"""

from __future__ import annotations

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
        blob_url=f"blob://img-{i}", alt_text=f"img {i}",
        checksum_sha256=f"sha-{i}", width=10, height=10,
    )


def _citation(chunk_id: str, n_images: int) -> Citation:
    return Citation(
        chunk_id=chunk_id, doc_id="doc-a", doc_title="Doc A", doc_format="docx",
        chunk_title="T", chunk_index=0, section_path=["Doc"], relevance_score=0.9,
        embedded_images=[_img(i) for i in range(n_images)],
    )


def test_cap_none_returns_unchanged() -> None:
    cites = [_citation("c1", 5), _citation("c2", 5)]
    out = cap_images_per_answer(cites, None)
    assert out is cites  # no copy when no cap (production-preserve)


def test_cap_trims_cumulative_total_across_citations() -> None:
    cites = [_citation("c1", 5), _citation("c2", 5)]
    out = cap_images_per_answer(cites, 7)
    total = sum(len(c.embedded_images) for c in out)
    assert total == 7
    assert len(out[0].embedded_images) == 5  # first citation keeps all
    assert len(out[1].embedded_images) == 2  # second trimmed to remaining budget
    # citations themselves never dropped
    assert [c.chunk_id for c in out] == ["c1", "c2"]


def test_cap_zero_strips_all_images_but_keeps_citations() -> None:
    cites = [_citation("c1", 3), _citation("c2", 2)]
    out = cap_images_per_answer(cites, 0)
    assert all(len(c.embedded_images) == 0 for c in out)
    assert [c.chunk_id for c in out] == ["c1", "c2"]


def test_cap_above_total_keeps_objects_untrimmed() -> None:
    cites = [_citation("c1", 2), _citation("c2", 1)]
    out = cap_images_per_answer(cites, 99)
    # untrimmed citations preserve the original objects (no needless copy)
    assert out[0] is cites[0]
    assert out[1] is cites[1]

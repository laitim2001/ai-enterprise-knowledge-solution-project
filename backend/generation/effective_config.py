"""EffectiveConfig — request-entry resolution of retrieval / citation knobs (ADR-0040).

Resolves each tunable knob with priority:

    per-query override  >  per-KB ``KbConfig`` (non-None field)  >  global ``Settings``

Built once at request entry (``query.py`` ``/query`` + ``/query/stream``) and threaded
through the pipeline so call sites read ``effective.*`` instead of ``settings.*``
directly. This is what lets two KBs with different content shapes run different
parent-doc / citation-expansion / image configs against the same global default
(per ADR-0040 — the W43 config-scope resolution model that formalises the per-KB
config twice deferred by ADR-0035 / ADR-0037).

Production-preserve (G7 back-compat): a KB whose ``KbConfig`` carries no explicit
per-KB knob (every knob field ``None``) and no per-query override resolves to exactly
the global ``Settings`` values, so behaviour is bit-identical to pre-W43.

MVP scope note: the per-query layer is a seam — ``query.py`` does NOT populate it yet
(only ``top_k_*`` are per-query today, handled separately by
``RetrievalEngine.retrieve``). It is typed + unit-tested here so it can be exposed
later without touching the resolution logic.
"""

from __future__ import annotations

from dataclasses import dataclass

from api.schemas.kb import KbConfig
from storage.settings import Settings


@dataclass(slots=True, frozen=True)
class PerQueryOverrides:
    """Optional per-request overrides — same field shape as the per-KB knobs.

    All-``None`` default = no override. Highest priority in the resolution chain.
    Unused by the W43 MVP wiring (seam only); kept typed for the unit test +
    forward-compat exposure.
    """

    enable_parent_doc_retrieval: bool | None = None
    parent_doc_section_depth_offset: int | None = None
    parent_doc_top_k: int | None = None
    parent_doc_max_tokens_per_parent: int | None = None
    enable_citation_post_hoc_expansion: bool | None = None
    citation_expansion_max_aux: int | None = None
    citation_expansion_window: int | None = None
    citation_expansion_section_path_prefix_depth: int | None = None
    enable_citation_neighbour_images: bool | None = None
    citation_neighbour_max_aux_images: int | None = None
    citation_neighbour_section_path_prefix_depth: int | None = None
    max_images_per_answer: int | None = None
    answer_detail: str | None = None  # CH-006 — synthesis detail level override


@dataclass(slots=True, frozen=True)
class EffectiveConfig:
    """Resolved retrieval / citation config for a single request.

    Carries every value the query pipeline + synthesizer read — both the per-KB
    tunable knobs (resolved per the priority chain) and the handful of pass-through
    globals that stay global-only in the W43 MVP (``parent_doc_max_chunks_per_parent``
    / ``parent_doc_fallback_to_doc_on_shallow`` / ``citation_neighbour_window``) — so
    wire points uniformly read ``effective.*``.

    The four ``citation_expansion_*`` attributes (+ the enable flag) match the field
    names ``generation.citation_expansion.expand_citations`` reads, so an
    ``EffectiveConfig`` is accepted there structurally (see that module's
    ``ExpansionConfig`` protocol).
    """

    # parent-doc retrieval (ADR-0037 / architecture.md §3.1)
    enable_parent_doc_retrieval: bool
    parent_doc_section_depth_offset: int
    parent_doc_top_k: int
    parent_doc_max_tokens_per_parent: int
    parent_doc_max_chunks_per_parent: int  # global-only pass-through (not per-KB in MVP)
    parent_doc_fallback_to_doc_on_shallow: bool  # global-only pass-through
    # post-hoc citation expansion (ADR-0034 / architecture.md §3.7; read by expand_citations)
    enable_citation_post_hoc_expansion: bool
    citation_expansion_max_aux: int
    citation_expansion_window: int
    citation_expansion_section_path_prefix_depth: int
    # neighbour-image attach (ADR-0034)
    enable_citation_neighbour_images: bool
    citation_neighbour_max_aux_images: int
    citation_neighbour_section_path_prefix_depth: int
    citation_neighbour_window: int  # global-only pass-through
    # image flood cap (ADR-0040 + BUG-031); None = no backend cap (frontend caps display)
    max_images_per_answer: int | None
    # CH-006 — synthesis answer detail level ("concise" | "detailed"), read by the
    # Synthesizer to pick the prompt_builder system-prompt variant. Always a concrete
    # str after resolution (per-query > per-KB > global Settings.synthesis_answer_detail).
    answer_detail: str


def _resolve[T: int](per_query: T | None, kb_value: T | None, global_value: T) -> T:
    """First non-None of (per-query, per-KB), else the global default.

    Bound to `int` because `bool` is an `int` subtype — covers every tunable knob.
    """
    if per_query is not None:
        return per_query
    if kb_value is not None:
        return kb_value
    return global_value


def resolve_effective_config(
    settings: Settings,
    kb_config: KbConfig | None = None,
    per_query: PerQueryOverrides | None = None,
) -> EffectiveConfig:
    """Resolve the live retrieval / citation config for one request.

    ``kb_config=None`` (KB record absent, e.g. a query against an index with no KB
    metadata row) → every knob falls through to the global ``Settings`` default, so
    the request behaves exactly as pre-W43.
    """
    kb = kb_config
    pq = per_query

    return EffectiveConfig(
        enable_parent_doc_retrieval=_resolve(
            pq.enable_parent_doc_retrieval if pq else None,
            kb.enable_parent_doc_retrieval if kb else None,
            settings.enable_parent_doc_retrieval,
        ),
        parent_doc_section_depth_offset=_resolve(
            pq.parent_doc_section_depth_offset if pq else None,
            kb.parent_doc_section_depth_offset if kb else None,
            settings.parent_doc_section_depth_offset,
        ),
        parent_doc_top_k=_resolve(
            pq.parent_doc_top_k if pq else None,
            kb.parent_doc_top_k if kb else None,
            settings.parent_doc_top_k,
        ),
        parent_doc_max_tokens_per_parent=_resolve(
            pq.parent_doc_max_tokens_per_parent if pq else None,
            kb.parent_doc_max_tokens_per_parent if kb else None,
            settings.parent_doc_max_tokens_per_parent,
        ),
        # global-only pass-throughs (no per-KB knob in the W43 MVP per plan §2 F1.1)
        parent_doc_max_chunks_per_parent=settings.parent_doc_max_chunks_per_parent,
        parent_doc_fallback_to_doc_on_shallow=settings.parent_doc_fallback_to_doc_on_shallow,
        enable_citation_post_hoc_expansion=_resolve(
            pq.enable_citation_post_hoc_expansion if pq else None,
            kb.enable_citation_post_hoc_expansion if kb else None,
            settings.enable_citation_post_hoc_expansion,
        ),
        citation_expansion_max_aux=_resolve(
            pq.citation_expansion_max_aux if pq else None,
            kb.citation_expansion_max_aux if kb else None,
            settings.citation_expansion_max_aux,
        ),
        citation_expansion_window=_resolve(
            pq.citation_expansion_window if pq else None,
            kb.citation_expansion_window if kb else None,
            settings.citation_expansion_window,
        ),
        citation_expansion_section_path_prefix_depth=_resolve(
            pq.citation_expansion_section_path_prefix_depth if pq else None,
            kb.citation_expansion_section_path_prefix_depth if kb else None,
            settings.citation_expansion_section_path_prefix_depth,
        ),
        enable_citation_neighbour_images=_resolve(
            pq.enable_citation_neighbour_images if pq else None,
            kb.enable_citation_neighbour_images if kb else None,
            settings.enable_citation_neighbour_images,
        ),
        citation_neighbour_max_aux_images=_resolve(
            pq.citation_neighbour_max_aux_images if pq else None,
            kb.citation_neighbour_max_aux_images if kb else None,
            settings.citation_neighbour_max_aux_images,
        ),
        citation_neighbour_section_path_prefix_depth=_resolve(
            pq.citation_neighbour_section_path_prefix_depth if pq else None,
            kb.citation_neighbour_section_path_prefix_depth if kb else None,
            settings.citation_neighbour_section_path_prefix_depth,
        ),
        citation_neighbour_window=settings.citation_neighbour_window,
        # max_images_per_answer has NO global Settings field (per-KB / per-query only;
        # default None = no backend cap, frontend INLINE_IMAGE_CAP handles display).
        max_images_per_answer=(
            pq.max_images_per_answer if pq and pq.max_images_per_answer is not None
            else (kb.max_images_per_answer if kb else None)
        ),
        # CH-006 — str field, so resolve via `or` chain (the int-bound `_resolve`
        # helper can't type it). Non-empty strings are truthy → falls through to the
        # global default when both per-query and per-KB are None.
        answer_detail=(
            (pq.answer_detail if pq else None)
            or (kb.answer_detail if kb else None)
            or settings.synthesis_answer_detail
        ),
    )

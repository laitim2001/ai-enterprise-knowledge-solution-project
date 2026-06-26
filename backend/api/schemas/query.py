"""Query / Citation Pydantic schemas (per architecture.md §4.5)."""

from typing import Literal

from pydantic import BaseModel, Field


class ImageRef(BaseModel):
    blob_url: str
    alt_text: str
    checksum_sha256: str
    width: int
    height: int
    # BUG-026 C-ii — the section the image visually belongs to (propagated from
    # the owning chunk at ingest). Lets the chat label show the image's OWN
    # section even when a neighbour-attach surfaces it under an intro/meta
    # citation. Default [] for images indexed before C-ii.
    source_section: list[str] = Field(default_factory=list)
    # CH-011 / ADR-0048 — the image's true document position (parser `doc_order`,
    # monotonic across the document). Read back from `embedded_images_json` by
    # `parse_embedded_images`. Lets the chat order images by reading flow even
    # WITHIN one section (all §X.Y step figures share one `source_section`, so the
    # lexical section sort can't page-order them). Default 0 = pre-CH-011 / not yet
    # re-indexed → frontend falls back to `source_section` ordering (production-preserve).
    doc_order: int = 0


class ChunkPreview(BaseModel):
    chunk_id: str
    chunk_title: str
    chunk_text: str
    relevance_score: float


class Citation(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    # BUG-021 added doc_format; default "docx" preserves backward compatibility
    # for Citations persisted to conversations.messages BEFORE the field existed
    # (Postgres JSONB rows from pre-BUG-021 sessions skip the field on read).
    # The Drive corpus is .docx-only so the default is realistic for legacy data;
    # `build_citations` overrides with the chunk-fields doc_format for fresh
    # retrievals so live `/query` answers always carry the accurate format.
    doc_format: Literal["docx", "pdf", "pptx"] = "docx"
    chunk_title: str
    chunk_index: int
    section_path: list[str]
    relevance_score: float
    embedded_images: list[ImageRef]


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    kb_id: str
    # CH-007 — `None` = no per-query override → the pipeline falls back to the KB's
    # `default_top_k` / `default_rerank_k` (resolved via EffectiveConfig: per-query >
    # per-KB > global). A concrete int IS an explicit per-query override (eval harness,
    # tests). Pre-CH-007 these defaulted to 50 / 5 (int), which was indistinguishable
    # from "unset" — so a KB's saved values could never take effect for the chat path,
    # which sends neither field. `top_k_retrieval` maps to the retrieval overfetch (the
    # rerank candidate pool); `top_k_rerank` to the final rerank depth.
    top_k_retrieval: int | None = None
    top_k_rerank: int | None = None
    llm_model: Literal["gpt-5.5", "gpt-5.4-mini"] = "gpt-5.5"
    reranker: Literal[
        "cohere-v4.0-pro",
        "cohere-v3.5",
        "voyage-rerank-2.5",
        "zeroentropy-zerank-1",
        "azure-semantic",
        "off",
    ] = "cohere-v4.0-pro"  # ADR-0012 production lock; v3.5 retained for backwards-compat
    # W39 F2 — Path A additive enhancement (對齊 ADR-0021 /retrieval_test schema symmetry).
    # Default "hybrid" preserves W38- production behavior (semantic ranker for full quality).
    # "vector" / "fulltext" exposed for Free tier workaround when Azure semantic ranker
    # monthly quota exhausted (W38 F3 + W39 F1 evidence) — also useful for debug + A/B test.
    mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"
    enable_crag: bool = True
    enable_intent_routing: bool = False


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[ChunkPreview]
    crag_triggered: bool
    crag_iterations: int
    latency_ms: int
    trace_id: str
    model_used: str
    reranker_used: str
    refused: bool = False

"""Query / Citation Pydantic schemas (per architecture.md §4.5)."""

from typing import Literal

from pydantic import BaseModel, Field


class ImageRef(BaseModel):
    blob_url: str
    alt_text: str
    checksum_sha256: str
    width: int
    height: int


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
    top_k_retrieval: int = 50
    top_k_rerank: int = 5
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


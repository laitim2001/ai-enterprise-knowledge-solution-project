"""Retrieval Testing endpoint schemas (ADR-0021 — V4 Retrieval Testing tab §5.5.4).

`POST /kb/{kb_id}/retrieval-test` runs a pure retrieval pass (no CRAG, no LLM
synthesis) so the admin can compare Vector / Full-Text / Hybrid modes, tune
Top-K / score threshold, and toggle rerank — surfacing ranked chunks + scores.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RetrievalTestRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    mode: Literal["hybrid", "vector", "fulltext"] = "hybrid"
    top_k: int = Field(5, ge=1, le=50)
    rerank: bool = True
    # Similarity threshold for vector / hybrid scores (0–1). Ignored for fulltext —
    # BM25 scores are unbounded above and have no 0–1 meaning (the frontend disables
    # this control when Full-Text mode is selected).
    score_threshold: float = Field(0.0, ge=0.0, le=1.0)


class RetrievalTestChunk(BaseModel):
    rank: int
    chunk_id: str
    doc_id: str
    doc_title: str
    chunk_title: str
    chunk_index: int
    section_path: list[str]
    score: float
    chunk_text_preview: str


class RetrievalTestResult(BaseModel):
    kb_id: str
    query: str
    mode: str
    reranked: bool
    reranker: str  # "cohere-v4.0-pro" when reranked, else "none"
    embed_latency_ms: int
    search_latency_ms: int
    rerank_latency_ms: int
    total_latency_ms: int
    total_hits: int  # before the score_threshold filter
    chunks: list[RetrievalTestChunk]

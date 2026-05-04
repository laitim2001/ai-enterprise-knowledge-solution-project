"""Reranker Protocol — unified contract for any reranker backend.

Per architecture.md §3.1 retrieval flow:
    hybrid(top_k=50) → reranker(query, candidates) → top_k=5

Implementations supply backend-specific transport (Cohere REST / Voyage SDK
/ Azure built-in semantic ranker call). The Protocol pins the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from retrieval.hybrid import HybridSearchHit


@dataclass(slots=True, frozen=True)
class RerankedChunk:
    """Hit augmented with reranker relevance score and original hybrid score."""

    fields: dict
    rerank_score: float          # reranker model score (0-1 typically)
    hybrid_score: float          # original hybrid RRF score (preserved for trace)
    original_index: int          # candidate index pre-rerank (for trace)


@runtime_checkable
class Reranker(Protocol):
    """Async reranker contract. MUST be safe to call concurrently."""

    async def rerank(
        self,
        query: str,
        candidates: list[HybridSearchHit],
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        """Rerank candidates by relevance to query; return top-k descending.

        Implementations should:
        - Preserve fields dict from HybridSearchHit unchanged in RerankedChunk
        - Return at most `top_k` items
        - Return empty list on empty candidates (no API call)
        """
        ...

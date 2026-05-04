"""Reranker factory — config-flag selector per architecture.md §3.2.

Returns None when reranker config not populated (allows RetrievalEngine to
operate hybrid-only as W2 baseline did) — useful for local dev without
Cohere endpoint, and for unit tests not exercising rerank.

W4 4-way shootout adds Voyage / ZeroEntropy / Azure built-in selectors.
"""

from __future__ import annotations

from retrieval.reranker.base import Reranker
from retrieval.reranker.cohere import CohereReranker
from storage.settings import Settings


def make_reranker(settings: Settings) -> Reranker | None:
    """Return a configured reranker, or None if not configured.

    None signals RetrievalEngine to skip rerank step (hybrid → top_k direct).
    """
    if not (settings.cohere_endpoint and settings.cohere_api_key):
        return None
    return CohereReranker(
        endpoint=settings.cohere_endpoint,
        api_key=settings.cohere_api_key,
        model=settings.cohere_rerank_model,
        timeout_s=settings.cohere_request_timeout_s,
        path=settings.cohere_procurement_path,
    )

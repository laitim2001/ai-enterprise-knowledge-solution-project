"""Reranker factory — config-flag selector per architecture.md §3.2.

W3 D1 baseline returned None when Cohere not configured (allows
RetrievalEngine to operate hybrid-only as W2 baseline did).

W4 D3 F3 expansion: switch on `settings.reranker_kind` to dispatch one of
4 reranker backends — cohere / voyage / zeroentropy / azure_semantic /
off (None). Each backend returns None when its required config (api_key
/ endpoint) is unset, falling through to None — same hybrid-only safety
as before.

Selection rules:
- "off"          → None (explicit hybrid-only)
- "cohere"       → CohereReranker if cohere_endpoint+api_key set, else None;
                   wrapped in FallbackReranker (auto-degrade to Azure semantic
                   ranker on Cohere outage) when reranker_fallback_enabled AND
                   Azure Search creds set (CH-020 / ADR-0074 — §7.3 E7 / §8.3 R6)
- "voyage"       → VoyageReranker if voyage_api_key set, else None
- "zeroentropy"  → ZeroEntropyReranker if zeroentropy_api_key set, else None
- "azure"        → AzureSemanticReranker if Azure Search endpoint+key set
                   (always set when retrieval engine is up — semantic
                   ranker reuses S1 SKU)
"""

from __future__ import annotations

from retrieval.reranker.azure_semantic import AzureSemanticReranker
from retrieval.reranker.base import Reranker
from retrieval.reranker.cohere import CohereReranker
from retrieval.reranker.fallback import FallbackReranker
from retrieval.reranker.voyage import VoyageReranker
from retrieval.reranker.zeroentropy import ZeroEntropyReranker
from storage.settings import Settings


def make_reranker(settings: Settings) -> Reranker | None:
    """Return a configured reranker per `settings.reranker_kind`, or None."""
    kind = settings.reranker_kind
    if kind == "off":
        return None
    if kind == "cohere":
        if not (settings.cohere_endpoint and settings.cohere_api_key):
            return None
        cohere = CohereReranker(
            endpoint=settings.cohere_endpoint,
            api_key=settings.cohere_api_key,
            model=settings.cohere_rerank_model,
            timeout_s=settings.cohere_request_timeout_s,
            path=settings.cohere_procurement_path,
        )
        # CH-020 / ADR-0074 — hot fallback: wrap Cohere in a FallbackReranker that
        # auto-degrades to the Azure built-in semantic ranker on Cohere outage
        # (architecture.md §7.3 E7 + §8.3 R6). Only when the flag is on AND Azure
        # Search creds are available (always set when the retrieval engine is up —
        # semantic ranker reuses the S1 SKU). Else return plain Cohere (zero regression).
        if settings.reranker_fallback_enabled and (
            settings.azure_search_endpoint and settings.azure_search_admin_key
        ):
            azure_fallback = AzureSemanticReranker(
                endpoint=settings.azure_search_endpoint,
                admin_key=settings.azure_search_admin_key,
                index_name=settings.azure_search_default_index,
                semantic_config=settings.azure_semantic_config_name,
                timeout_s=settings.azure_semantic_request_timeout_s,
            )
            return FallbackReranker(primary=cohere, fallback=azure_fallback)
        return cohere
    if kind == "voyage":
        if not settings.voyage_api_key:
            return None
        return VoyageReranker(
            api_key=settings.voyage_api_key,
            model=settings.voyage_rerank_model,
            timeout_s=settings.voyage_request_timeout_s,
        )
    if kind == "zeroentropy":
        if not settings.zeroentropy_api_key:
            return None
        return ZeroEntropyReranker(
            api_key=settings.zeroentropy_api_key,
            model=settings.zeroentropy_rerank_model,
            timeout_s=settings.zeroentropy_request_timeout_s,
        )
    if kind == "azure":
        if not (settings.azure_search_endpoint and settings.azure_search_admin_key):
            return None
        return AzureSemanticReranker(
            endpoint=settings.azure_search_endpoint,
            admin_key=settings.azure_search_admin_key,
            index_name=settings.azure_search_default_index,
            semantic_config=settings.azure_semantic_config_name,
            timeout_s=settings.azure_semantic_request_timeout_s,
        )
    # Unknown kind — fail safe with None (hybrid-only) rather than raise; the
    # Pydantic Literal already prevents invalid values at config-load time, so
    # reaching this branch indicates Settings drift that warrants investigation
    # rather than a runtime crash.
    return None

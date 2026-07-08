"""FallbackReranker — Cohere primary with hot fallback to Azure semantic ranker.

Per ADR-0074 (CH-020) closing the gap between `architecture.md §7.3 E7` /
`§8.3 R6` (which promise a hot fallback to the Azure built-in semantic ranker
on Cohere outage, config-flag switchable without redeploy) and the prior
implementation where a Cohere 5xx bubbled straight to a 502.

Design: a transparent composite that itself satisfies the Reranker Protocol
(and the async-context lifecycle the lifespan expects), so `server.py` and
`RetrievalEngine.retrieve()` need zero changes. `make_reranker` wraps a
`CohereReranker` + `AzureSemanticReranker` in this class when
`reranker_kind="cohere"`, `reranker_fallback_enabled=True`, and Azure Search
credentials are available.

Behaviour (option A — automatic hot degrade):
- `rerank()` calls the primary first; on ANY primary exception (the tenacity
  retries are exhausted and re-raised as httpx errors, or any other failure),
  degrade to the fallback and continue — no 502.
- Emits a `reranker_fallback_activated` warning event on degrade (observability
  per pipeline review Q-R8, same style as CH-021).
- Cohere recovery is automatic: every `rerank()` starts from the primary again
  (no sticky state), so the next query retries Cohere.
- If the fallback ITSELF fails (e.g. dev Free-tier semantic ranker hits its
  1000/month 402 cap), the exception propagates — preserving the pre-ADR-0074
  bubble behaviour rather than inventing a hybrid-only degrade (out of scope
  per ADR-0074 Alternatives).
"""

from __future__ import annotations

from typing import Any, Protocol

import structlog

from retrieval.hybrid import HybridSearchHit
from retrieval.reranker.base import RerankedChunk

logger = structlog.get_logger(__name__)


class _ManagedReranker(Protocol):
    """A reranker whose httpx client lifecycle is managed via async context.

    Both `CohereReranker` and `AzureSemanticReranker` satisfy this structurally
    (they expose `__aenter__` / `__aexit__` alongside the `Reranker.rerank`
    surface). Declared here so `FallbackReranker` can drive both the rerank call
    and the lifecycle without depending on either concrete class.
    """

    async def __aenter__(self) -> Any: ...

    async def __aexit__(self, *exc_info: object) -> None: ...

    async def rerank(
        self,
        query: str,
        candidates: list[HybridSearchHit],
        top_k: int = 5,
    ) -> list[RerankedChunk]: ...


class FallbackReranker:
    """Primary reranker with automatic hot fallback to a secondary (ADR-0074)."""

    def __init__(
        self,
        primary: _ManagedReranker,
        fallback: _ManagedReranker,
        enabled: bool = True,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._enabled = enabled

    async def __aenter__(self) -> FallbackReranker:
        await self._primary.__aenter__()
        await self._fallback.__aenter__()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        # Close fallback then primary; guard so a fallback close error doesn't
        # skip the primary close.
        try:
            await self._fallback.__aexit__(*exc_info)
        finally:
            await self._primary.__aexit__(*exc_info)

    async def rerank(
        self,
        query: str,
        candidates: list[HybridSearchHit],
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        if not candidates:
            return []
        try:
            return await self._primary.rerank(query, candidates, top_k=top_k)
        except Exception as exc:  # noqa: BLE001 — graceful degrade to fallback reranker
            if not self._enabled:
                raise
            logger.warning(
                "reranker_fallback_activated",
                primary=type(self._primary).__name__,
                fallback=type(self._fallback).__name__,
                error=f"{type(exc).__name__}: {exc}",
                candidates_in=len(candidates),
            )
            # A fallback failure here propagates (preserves pre-ADR-0074 bubble).
            return await self._fallback.rerank(query, candidates, top_k=top_k)

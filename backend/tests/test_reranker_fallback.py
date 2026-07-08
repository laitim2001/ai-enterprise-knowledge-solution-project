"""FallbackReranker + factory hot-fallback tests (CH-020 / ADR-0074; per CLAUDE.md §5.6 H6).

Covers the transparent composite that auto-degrades a Cohere primary to the
Azure semantic ranker on outage (architecture.md §7.3 E7 / §8.3 R6):

FallbackReranker:
- primary succeeds → primary result, fallback untouched
- primary raises → degrade to fallback result
- enabled=False → primary error re-raised, fallback untouched
- primary raises + fallback raises → propagates (pre-ADR-0074 bubble preserved)
- empty candidates → [] with no reranker call
- __aenter__ / __aexit__ manage BOTH primary and fallback lifecycles

factory (make_reranker):
- kind="cohere" + fallback_enabled + Azure creds → FallbackReranker(Cohere, Azure)
- kind="cohere" + fallback_enabled=False → plain CohereReranker
- kind="cohere" + Azure creds missing → plain CohereReranker (zero regression)
"""

from __future__ import annotations

import pytest

from retrieval.hybrid import HybridSearchHit
from retrieval.reranker.azure_semantic import AzureSemanticReranker
from retrieval.reranker.base import RerankedChunk
from retrieval.reranker.cohere import CohereReranker
from retrieval.reranker.factory import make_reranker
from retrieval.reranker.fallback import FallbackReranker
from storage.settings import Settings


def _hits(*chunk_ids: str) -> list[HybridSearchHit]:
    return [
        HybridSearchHit(score=0.5, fields={"chunk_id": cid, "chunk_text": cid})
        for cid in chunk_ids
    ]


def _reranked(chunk_id: str) -> RerankedChunk:
    return RerankedChunk(
        fields={"chunk_id": chunk_id},
        rerank_score=0.9,
        hybrid_score=0.5,
        original_index=0,
    )


class _FakeReranker:
    """Managed reranker stub — records lifecycle + rerank calls, or raises."""

    def __init__(
        self,
        *,
        result: list[RerankedChunk] | None = None,
        raise_exc: Exception | None = None,
    ) -> None:
        self._result = result if result is not None else []
        self._raise = raise_exc
        self.rerank_calls = 0
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _FakeReranker:
        self.entered = True
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        self.exited = True

    async def rerank(
        self,
        query: str,
        candidates: list[HybridSearchHit],
        top_k: int = 5,
    ) -> list[RerankedChunk]:
        self.rerank_calls += 1
        if self._raise is not None:
            raise self._raise
        return self._result


# ---------- FallbackReranker behaviour ---------------------------------------


@pytest.mark.asyncio
async def test_uses_primary_when_primary_succeeds() -> None:
    primary = _FakeReranker(result=[_reranked("p")])
    fallback = _FakeReranker(result=[_reranked("f")])
    fb = FallbackReranker(primary=primary, fallback=fallback)

    out = await fb.rerank("q", _hits("a"), top_k=5)

    assert [c.fields["chunk_id"] for c in out] == ["p"]
    assert primary.rerank_calls == 1
    assert fallback.rerank_calls == 0  # fallback untouched on success


@pytest.mark.asyncio
async def test_degrades_to_fallback_on_primary_error() -> None:
    primary = _FakeReranker(raise_exc=RuntimeError("cohere 503"))
    fallback = _FakeReranker(result=[_reranked("f")])
    fb = FallbackReranker(primary=primary, fallback=fallback)

    out = await fb.rerank("q", _hits("a"), top_k=5)

    assert [c.fields["chunk_id"] for c in out] == ["f"]
    assert primary.rerank_calls == 1
    assert fallback.rerank_calls == 1


@pytest.mark.asyncio
async def test_disabled_reraises_primary_error_without_fallback() -> None:
    primary = _FakeReranker(raise_exc=RuntimeError("cohere 503"))
    fallback = _FakeReranker(result=[_reranked("f")])
    fb = FallbackReranker(primary=primary, fallback=fallback, enabled=False)

    with pytest.raises(RuntimeError, match="cohere 503"):
        await fb.rerank("q", _hits("a"), top_k=5)
    assert fallback.rerank_calls == 0  # escape hatch: never touch fallback


@pytest.mark.asyncio
async def test_fallback_error_propagates() -> None:
    primary = _FakeReranker(raise_exc=RuntimeError("cohere 503"))
    fallback = _FakeReranker(raise_exc=RuntimeError("azure 402"))
    fb = FallbackReranker(primary=primary, fallback=fallback)

    # Double failure propagates (preserves pre-ADR-0074 bubble; no hybrid-only degrade).
    with pytest.raises(RuntimeError, match="azure 402"):
        await fb.rerank("q", _hits("a"), top_k=5)


@pytest.mark.asyncio
async def test_empty_candidates_short_circuits() -> None:
    primary = _FakeReranker(result=[_reranked("p")])
    fallback = _FakeReranker(result=[_reranked("f")])
    fb = FallbackReranker(primary=primary, fallback=fallback)

    out = await fb.rerank("q", [], top_k=5)

    assert out == []
    assert primary.rerank_calls == 0
    assert fallback.rerank_calls == 0


@pytest.mark.asyncio
async def test_aenter_aexit_manage_both_lifecycles() -> None:
    primary = _FakeReranker()
    fallback = _FakeReranker()

    async with FallbackReranker(primary=primary, fallback=fallback):
        assert primary.entered is True
        assert fallback.entered is True

    assert primary.exited is True
    assert fallback.exited is True


# ---------- factory dispatch -------------------------------------------------


def test_factory_cohere_wraps_fallback_when_enabled_and_azure_creds() -> None:
    settings = Settings(
        reranker_kind="cohere",
        cohere_endpoint="https://m.example.com",
        cohere_api_key="key",
        reranker_fallback_enabled=True,
        azure_search_endpoint="https://x.search.windows.net",
        azure_search_admin_key="ak",
        azure_search_default_index="ekp-kb-drive-v1",
        azure_semantic_config_name="ekp-semantic-config",
    )
    r = make_reranker(settings)
    assert isinstance(r, FallbackReranker)
    assert isinstance(r._primary, CohereReranker)
    assert isinstance(r._fallback, AzureSemanticReranker)


def test_factory_cohere_no_wrap_when_fallback_disabled() -> None:
    settings = Settings(
        reranker_kind="cohere",
        cohere_endpoint="https://m.example.com",
        cohere_api_key="key",
        reranker_fallback_enabled=False,
        azure_search_endpoint="https://x.search.windows.net",
        azure_search_admin_key="ak",
    )
    r = make_reranker(settings)
    assert isinstance(r, CohereReranker)


def test_factory_cohere_no_wrap_when_azure_creds_missing() -> None:
    settings = Settings(
        reranker_kind="cohere",
        cohere_endpoint="https://m.example.com",
        cohere_api_key="key",
        reranker_fallback_enabled=True,
        azure_search_endpoint="",
        azure_search_admin_key="",
    )
    r = make_reranker(settings)
    assert isinstance(r, CohereReranker)

"""Retrieval Testing endpoint (ADR-0021 — V4 Retrieval Testing tab §5.5.4).

`POST /kb/{kb_id}/retrieval-test` — pure retrieval (no CRAG / no LLM synthesis):
embed (skipped for fulltext) → mode-selected search (hybrid / vector / fulltext)
→ optional rerank → score-threshold filter (vector / hybrid only) → ranked chunks
+ per-stage timings. Lets the admin compare retrieval modes and tune Top-K /
threshold / rerank-on-off, surfacing the retrieved chunks + relevance scores.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.schemas.retrieval_test import (
    RetrievalTestChunk,
    RetrievalTestRequest,
    RetrievalTestResult,
)
from kb_management import KBNotFoundError, KBService, get_kb_service
from retrieval.retrieval_engine import RetrievalEngine

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]

_PREVIEW_CHARS = 280
# Tier 1 reranker is locked to Cohere v4.0-pro (ADR-0012 + Q21 Resolved); the
# V4 tab's "Reranker" dropdown surfaces only this + "None" (Voyage / ZeroEntropy
# were dropped Tier 1 — that §5.5.4 dropdown item is superseded).
_RERANKER_LABEL = "cohere-v4.0-pro"


def _engine_or_503(request: Request) -> RetrievalEngine:
    engine = getattr(request.app.state, "retrieval_engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "RetrievalEngine not initialized — check Azure OpenAI + AI Search "
                ".env config (Q3 + Q4 dependencies)."
            ),
        )
    return engine


async def _verify_kb_or_404(kb_id: str, service: KBService) -> None:
    try:
        await service.get(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/kb/{kb_id}/retrieval-test", response_model=RetrievalTestResult)
async def retrieval_test(
    kb_id: str,
    payload: RetrievalTestRequest,
    request: Request,
    service: KbServiceDep,
) -> RetrievalTestResult:
    """ADR-0021 — pure retrieval test harness for the V4 Retrieval Testing tab.

    Verifies kb_id exists (404); runs `RetrievalEngine.retrieve` with the chosen
    `mode` + `rerank` flag; filters by `score_threshold` for vector / hybrid
    modes (BM25 scores have no 0–1 meaning so Full-Text ignores it). No CRAG,
    no LLM synthesis — surfaces the retrieved chunks + relevance scores only.
    """
    await _verify_kb_or_404(kb_id, service)
    engine = _engine_or_503(request)

    try:
        result = await engine.retrieve(
            query=payload.query,
            kb_id=kb_id,
            top_k=payload.top_k,
            mode=payload.mode,
            rerank=payload.rerank,
        )
    except Exception as exc:  # noqa: BLE001 — surface downstream Azure errors as 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"retrieval failure: {type(exc).__name__}: {exc}",
        ) from exc

    ordered = result.chunks
    threshold_applies = payload.mode != "fulltext" and payload.score_threshold > 0.0
    filtered = (
        [c for c in ordered if c.score >= payload.score_threshold]
        if threshold_applies
        else ordered
    )

    chunks: list[RetrievalTestChunk] = []
    for rank, c in enumerate(filtered, start=1):
        text = str(c.fields.get("chunk_text", ""))
        preview = text[:_PREVIEW_CHARS] + ("…" if len(text) > _PREVIEW_CHARS else "")
        chunks.append(
            RetrievalTestChunk(
                rank=rank,
                chunk_id=str(c.fields.get("chunk_id", "")),
                doc_id=str(c.fields.get("doc_id", "")),
                doc_title=str(c.fields.get("doc_title", "")),
                chunk_title=str(c.fields.get("chunk_title", "")),
                chunk_index=int(c.fields.get("chunk_index", 0) or 0),
                section_path=list(c.fields.get("section_path") or []),
                score=c.score,
                chunk_text_preview=preview,
            )
        )

    return RetrievalTestResult(
        kb_id=kb_id,
        query=payload.query,
        mode=payload.mode,
        reranked=result.reranked,
        reranker=_RERANKER_LABEL if result.reranked else "none",
        embed_latency_ms=result.embed_latency_ms,
        search_latency_ms=result.search_latency_ms,
        rerank_latency_ms=result.rerank_latency_ms,
        total_latency_ms=result.total_latency_ms,
        total_hits=len(ordered),
        chunks=chunks,
    )

"""On-platform config-test harness (W43 F2, ADR-0040 §Decision 3).

`POST /kb/{kb_id}/config-test` — run the FULL `/query` pipeline N times with a
DRAFT (unsaved) per-KB config override, aggregate presentation counters (citation
/ figure raw+dedup) + latency with a variance band. Lets the KB owner preview a
config's effect (and optionally A/B vs the saved config) before persisting it.

Distinct from `POST /kb/{kb_id}/retrieval-test` (ADR-0021 V4) which is RETRIEVE-ONLY
(no synth / citation / image) — this one runs the full pipeline via the shared
`execute_query_pipeline`, so it measures the EXACT pipeline a real query runs
(F2.6 trust requirement). The draft is injected as the highest-priority per-query
override in the resolver (draft > saved KbConfig > global Settings default).
"""

import asyncio
from collections.abc import Callable
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.routes.query import execute_query_pipeline
from api.schemas.config_test import (
    CitationBreakdown,
    ConfigRunSummary,
    ConfigTestRequest,
    ConfigTestResult,
    MetricBand,
    RunMetrics,
)
from api.schemas.query import Citation, QueryRequest
from eval.ragas_evaluator import make_faithfulness_evaluator
from generation.effective_config import EffectiveConfig, PerQueryOverrides, resolve_effective_config
from kb_management import KBNotFoundError, KBService, get_kb_service
from storage.settings import Settings, get_settings

# W48 — faithfulness evaluator signature (question, answer, contexts) -> score | None.
FaithfulnessFn = Callable[[str, str, list[str]], float | None]

router = APIRouter()

KbServiceDep = Annotated[KBService, Depends(get_kb_service)]


def _figure_counts(citations: list[Citation]) -> tuple[int, int]:
    """(raw, dedup) image counts across an answer's citations. Dedup keys on
    `checksum_sha256` (fallback `blob_url`) — mirrors the frontend display dedup so
    the harness's dedup number matches what the user actually sees rendered."""
    raw = 0
    seen: set[str] = set()
    for c in citations:
        for img in c.embedded_images:
            raw += 1
            seen.add(img.checksum_sha256 or img.blob_url)
    return raw, len(seen)


def _band(values: list[float]) -> MetricBand:
    return MetricBand(
        min=min(values),
        max=max(values),
        mean=sum(values) / len(values),
        band=max(values) - min(values),
    )


async def _faithfulness_band(
    faithfulness_fn: FaithfulnessFn | None,
    query: str,
    per_run_qa: list[tuple[str, list[str]]],
) -> MetricBand | None:
    """W49 (決策 7) — judge faithfulness on EVERY run's (answer, contexts) and
    aggregate into a band, so the quality axis exposes its run-to-run noise (a
    single-shot judge swung 0.93 vs 0.53 on the same config, 2026-06-06 live).

    The N judge calls run concurrently — each offloaded via `asyncio.to_thread` so it
    never blocks the event loop, and each self-degrades to None on a judge error. The
    band is computed over the runs whose judge succeeded; None only when the axis is
    off (`faithfulness_fn is None`) or every run errored. N=1 → band=0.
    """
    if faithfulness_fn is None:
        return None
    scores: list[float | None] = list(
        await asyncio.gather(
            *(
                asyncio.to_thread(faithfulness_fn, query, answer, contexts)
                for answer, contexts in per_run_qa
            )
        )
    )
    ok = [s for s in scores if s is not None]
    return _band(ok) if ok else None


async def _run_n(
    qreq: QueryRequest,
    request: Request,
    effective: EffectiveConfig,
    settings: Settings,
    runs: int,
    faithfulness_fn: FaithfulnessFn | None = None,
) -> ConfigRunSummary:
    """Run the full pipeline `runs` times with `effective`; aggregate counters.

    When `faithfulness_fn` is supplied, the reference-free RAGAs faithfulness quality
    axis (W48 / ADR-0040 dual-axis) is computed PER RUN and aggregated into an N-run
    `MetricBand` (W49 / 決策 7) — so the quality axis exposes its run-to-run noise,
    mirroring the presentation counters. The judge cost scales with `runs` (the user's
    own choice); each judge call self-degrades to `None`, so the band is taken over the
    runs that succeeded.
    """
    metrics: list[RunMetrics] = []
    last_citations: list[Citation] = []
    # W49 — capture every run's (answer, contexts) so faithfulness is judged per run
    # (an N-run band), not just on the last run.
    per_run_qa: list[tuple[str, list[str]]] = []
    for i in range(1, runs + 1):
        resp = await execute_query_pipeline(qreq, request, effective, settings)
        raw, dedup = _figure_counts(resp.citations)
        # W51 (決策 7 option d) — distinct cited sections = completeness/coverage proxy
        # (breadth: how many different document sections the answer drew from).
        distinct_sections = len({tuple(c.section_path) for c in resp.citations})
        metrics.append(
            RunMetrics(
                run=i,
                citation_count=len(resp.citations),
                distinct_sections=distinct_sections,
                figure_count_raw=raw,
                figure_count_dedup=dedup,
                latency_ms=resp.latency_ms,
                answer_chars=len(resp.answer),
                refused=resp.refused,
            )
        )
        last_citations = resp.citations
        # Contexts for faithfulness = the reranked chunks synthesis grounded on.
        per_run_qa.append((resp.answer, [c.chunk_text for c in resp.retrieved_chunks]))
    per_citation = [
        CitationBreakdown(
            chunk_id=c.chunk_id,
            section_path=c.section_path,
            image_count=len(c.embedded_images),
        )
        for c in last_citations
    ]
    faithfulness = await _faithfulness_band(faithfulness_fn, qreq.query, per_run_qa)
    return ConfigRunSummary(
        runs=metrics,
        citation_count=_band([float(m.citation_count) for m in metrics]),
        distinct_sections=_band([float(m.distinct_sections) for m in metrics]),
        figure_count_raw=_band([float(m.figure_count_raw) for m in metrics]),
        figure_count_dedup=_band([float(m.figure_count_dedup) for m in metrics]),
        latency_ms=_band([float(m.latency_ms) for m in metrics]),
        per_citation=per_citation,
        faithfulness=faithfulness,
    )


@router.post("/kb/{kb_id}/config-test", response_model=ConfigTestResult)
async def config_test(
    kb_id: str,
    payload: ConfigTestRequest,
    request: Request,
    service: KbServiceDep,
) -> ConfigTestResult:
    """W43 F2 — full-pipeline draft-config试跑 with multi-run variance band.

    Verifies kb_id (404), resolves the draft over the KB's saved config + global
    default, runs the pipeline `runs` times, and returns per-run + aggregated
    presentation counters. With `compare_to_saved=True`, also runs the saved config
    for a side-by-side A/B (each side = `runs` full synth calls, so this endpoint is
    intentionally slow — it is a tuning harness, not a hot path).
    """
    try:
        kb_status = await service.get(kb_id)
    except KBNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    settings = get_settings()
    saved_cfg = kb_status.config

    qreq = QueryRequest(
        query=payload.query,
        kb_id=kb_id,
        mode=payload.mode,
        enable_crag=payload.enable_crag,
    )

    # W48 — build the faithfulness evaluator ONCE (draft + saved share it); None when
    # the axis is off or no judge credential → summaries get faithfulness=None.
    faithfulness_fn: FaithfulnessFn | None = (
        make_faithfulness_evaluator(settings) if payload.eval_faithfulness else None
    )

    # W57 / ADR-0050 — per-DOCUMENT scope: load the doc's STORED per-doc config so
    # both the draft and the A/B-saved resolutions insert it as the per-DOC layer.
    # `None` doc_id (or no store / no config for the doc) → KB-scoped (pre-W57).
    doc_cfg = None
    if payload.doc_id:
        store = getattr(request.app.state, "doc_config_store", None)
        if store is not None:
            doc_cfg = await store.get(kb_id, payload.doc_id)

    draft_override = PerQueryOverrides(**payload.draft_config.model_dump())
    draft_effective = resolve_effective_config(settings, saved_cfg, draft_override, doc_cfg)
    draft_summary = await _run_n(
        qreq, request, draft_effective, settings, payload.runs, faithfulness_fn
    )

    saved_summary: ConfigRunSummary | None = None
    if payload.compare_to_saved:
        saved_effective = resolve_effective_config(settings, saved_cfg, None, doc_cfg)
        saved_summary = await _run_n(
            qreq, request, saved_effective, settings, payload.runs, faithfulness_fn
        )

    return ConfigTestResult(
        kb_id=kb_id,
        query=payload.query,
        runs=payload.runs,
        resolved_config=asdict(draft_effective),
        draft=draft_summary,
        saved=saved_summary,
    )

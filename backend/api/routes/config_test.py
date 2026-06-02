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
from generation.effective_config import EffectiveConfig, PerQueryOverrides, resolve_effective_config
from kb_management import KBNotFoundError, KBService, get_kb_service
from storage.settings import Settings, get_settings

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


async def _run_n(
    qreq: QueryRequest,
    request: Request,
    effective: EffectiveConfig,
    settings: Settings,
    runs: int,
) -> ConfigRunSummary:
    """Run the full pipeline `runs` times with `effective`; aggregate counters."""
    metrics: list[RunMetrics] = []
    last_citations: list[Citation] = []
    for i in range(1, runs + 1):
        resp = await execute_query_pipeline(qreq, request, effective, settings)
        raw, dedup = _figure_counts(resp.citations)
        metrics.append(
            RunMetrics(
                run=i,
                citation_count=len(resp.citations),
                figure_count_raw=raw,
                figure_count_dedup=dedup,
                latency_ms=resp.latency_ms,
                answer_chars=len(resp.answer),
                refused=resp.refused,
            )
        )
        last_citations = resp.citations
    per_citation = [
        CitationBreakdown(
            chunk_id=c.chunk_id,
            section_path=c.section_path,
            image_count=len(c.embedded_images),
        )
        for c in last_citations
    ]
    return ConfigRunSummary(
        runs=metrics,
        citation_count=_band([float(m.citation_count) for m in metrics]),
        figure_count_raw=_band([float(m.figure_count_raw) for m in metrics]),
        figure_count_dedup=_band([float(m.figure_count_dedup) for m in metrics]),
        latency_ms=_band([float(m.latency_ms) for m in metrics]),
        per_citation=per_citation,
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

    draft_override = PerQueryOverrides(**payload.draft_config.model_dump())
    draft_effective = resolve_effective_config(settings, saved_cfg, draft_override)
    draft_summary = await _run_n(qreq, request, draft_effective, settings, payload.runs)

    saved_summary: ConfigRunSummary | None = None
    if payload.compare_to_saved:
        saved_effective = resolve_effective_config(settings, saved_cfg, None)
        saved_summary = await _run_n(qreq, request, saved_effective, settings, payload.runs)

    return ConfigTestResult(
        kb_id=kb_id,
        query=payload.query,
        runs=payload.runs,
        resolved_config=asdict(draft_effective),
        draft=draft_summary,
        saved=saved_summary,
    )

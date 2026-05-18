"""Debug + trace-list endpoints (per architecture.md §4.4 #17 + §5.7 Debug View).

W16 F5.5 closure (CO_W15_F2) — replaced 501 stub with full Langfuse SDK
integration per Decision D.2. Unblocks Drift #3 ADR-0020 frontend Session 2
V6 6→9 stage `PipelineStageCollapsible` expansion.

W21 F2.2 — added `GET /traces` index list endpoint per ADR-0030 absorbed
scope (architecture.md v6 §5.7 Traces). Sibling to `/debug/trace/{id}` (W16
F5.5); shares the graceful-degrade matrix via `observability.langfuse_trace_list`.
Router-level `Depends(get_current_user)` enforced at `api/server.py:256`.
"""

from fastapi import APIRouter, Query

from api.schemas.observability import TraceDetail, TraceListResponse
from observability.langfuse_trace import fetch_trace
from observability.langfuse_trace_list import fetch_trace_list

router = APIRouter()


@router.get("/debug/trace/{trace_id}", response_model=TraceDetail)
async def get_trace(trace_id: str) -> TraceDetail:
    """W16 F5.5 — Langfuse trace detail correlation per Decision D.2.

    Returns TraceDetail with per-stage breakdown for V6 9-stage Debug View
    (frontend ADR-0020 Session 2 consumer). Graceful degrade matrix:
    - Langfuse not configured → trace_url pattern only (status="langfuse_not_configured")
    - SDK fetch_trace missing → trace_url + status="sdk_method_missing"
    - Trace not found → status="not_found" (200 OK with explicit status field
      rather than 404 — frontend uses status to render appropriate UI state)
    - Fetch failure → status="fetch_failed" + note with error
    - Happy path → status="ok" + populated stages + aggregates

    Note: returns 200 in all cases (status field communicates result).
    Frontend distinguishes between scenarios via status enum rather than
    HTTP status code, simplifying client-side error handling.
    """
    return await fetch_trace(trace_id)


@router.get("/traces", response_model=TraceListResponse)
async def list_traces(
    status_filter: str = Query(
        "all",
        alias="filter",
        description="Status filter: all | errors | crag_triggered",
    ),
    since: str | None = Query(
        None,
        description="ISO 8601 timestamp lower-bound (inclusive); rows with timestamp < since are excluded",
    ),
    kb_id: str | None = Query(
        None,
        description="Optional KB scope filter; matches trace metadata.kb_id or input.kb_id",
    ),
    limit: int = Query(50, ge=1, le=500, description="Page size (1-500)"),
    offset: int = Query(0, ge=0, description="Page offset (≥0)"),
) -> TraceListResponse:
    """W21 F2.2 — Langfuse trace-list index endpoint per ADR-0030 absorbed scope.

    Returns paginated `TraceListResponse` for the `/traces` index view
    (architecture.md v6 §5.7). The graceful-degrade matrix mirrors
    `/debug/trace/{id}` (W16 F5.5) — endpoint always returns 200; the
    `status` field on the response carries the Langfuse fetch outcome
    ("ok" | "no_client" | "sdk_method_missing" | "fetch_failed"), so
    frontend never has to branch on HTTP status code for observability
    degrade paths.

    Filter is applied post-fetch in Python (Langfuse v2 SDK `fetch_traces`
    doesn't expose status/error filter pushdown). Fetch window sized to
    `min(100, offset + limit + 100)` — Langfuse cloud enforces ≤100 per page
    (W22 D8 clamp landed 2026-05-18; pre-clamp was 500 + W21 F2 regression).
    Sufficient for Beta cohort scale per W17 F4 pricing baseline (50 user ×
    5 q/day × 24h ≈ 250 traces); beyond 100 paginate via repeated SDK calls
    (Wave C+ scope).

    Parameter naming: URL param `?filter=` aliases Python `status_filter` —
    avoids Python builtin shadow + improves call-site readability while
    preserving the canonical frontend query-string shape per the W21 plan.
    """
    return await fetch_trace_list(
        status_filter=status_filter,
        since=since,
        kb_id=kb_id,
        limit=limit,
        offset=offset,
    )

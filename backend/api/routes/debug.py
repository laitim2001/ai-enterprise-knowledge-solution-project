"""Debug endpoint (per architecture.md §4.4 #17 + §5.7 Debug View).

W16 F5.5 closure (CO_W15_F2) — replaced 501 stub with full Langfuse SDK
integration per Decision D.2. Unblocks Drift #3 ADR-0020 frontend Session 2
V6 6→9 stage `PipelineStageCollapsible` expansion.
"""

from fastapi import APIRouter

from api.schemas.observability import TraceDetail
from observability.langfuse_trace import fetch_trace

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

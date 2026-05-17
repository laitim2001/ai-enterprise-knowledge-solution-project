"""Langfuse trace-list aggregator for `GET /traces` endpoint (W21 F2.2).

Per ADR-0030 absorbed scope (W19 F6 SKIPPED-but-implemented) + plan W21 F2.2 —
serves the `/traces` index list view. Sibling to `langfuse_trace.py` which
serves the `/debug/trace/{id}` detail endpoint; both share the graceful
degrade matrix established W16 F5.5:
  - Langfuse client = None → status="no_client"
  - SDK method missing → status="sdk_method_missing"
  - Fetch raises → status="fetch_failed" + error in note
  - Happy path → status="ok" + populated items

Karpathy §1.2 simplicity-first design:
  - Use `client.fetch_traces` trace-summary endpoint (NOT per-trace deep fetch)
    — `stage_count` comes from the SDK-returned observations-id list length.
  - Post-fetch Python filter (no SDK-side filter pushdown) — Langfuse v2 SDK
    `fetch_traces` doesn't expose `level=ERROR` filter natively; filter the
    fetched window in-process. Window size = `limit + offset + safety
    headroom` (capped at 500) — sufficient for Beta cohort scale (W17 F4
    pricing baseline = 50 user × 5 q/day × 24h window ≈ 250 traces).
  - Cost / total_tokens fall through to 0 when Langfuse server omits derived
    fields (older self-hosted v2 deployments). Dashboard renders rows OK.

Filter semantics:
  - `status_filter="all"` (default) → no status filter applied
  - `status_filter="errors"` → keep traces where rolled-up `status == "error"`
  - `status_filter="crag_triggered"` → keep traces where `status == "crag_triggered"`

Status priority (per-trace rollup):
    "error" > "crag_triggered" > "ok"
A CRAG-triggered trace that also errored surfaces as "error" so the
frontend errors-filter bucket catches it (operator intent: see all failures).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from api.schemas.observability import TraceListResponse, TraceSummary
from observability.langfuse_tracer import get_langfuse_client

logger = structlog.get_logger(__name__)


_DEFAULT_FETCH_LIMIT = 500  # Langfuse SDK v2 max per page;safe upper bound


def _coerce_iso(value: Any) -> str:
    """Best-effort ISO 8601 string extraction from datetime / str / None."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat() if value.tzinfo else value.isoformat()
    return str(value)


def _query_preview(input_payload: Any, name: Any) -> str:
    """Pull a 100-char preview of the user query from trace input or fall back to name.

    Tier 1 trace shape (W17 F4 + observe_async wires):
      - `input` is typically `{"query": "..."}` for `/query` + `/chat` paths
      - For other code paths (eval / shootout) `input` may be a list/dict;
        cast to `str` and truncate
      - Empty fallback to trace `name` (e.g. "api.query.run") so the row
        is never blank
    """
    if isinstance(input_payload, dict):
        candidate = input_payload.get("query") or input_payload.get("question")
        if isinstance(candidate, str) and candidate:
            return candidate[:100]
    if input_payload is not None:
        text = str(input_payload).strip()
        if text and text not in {"None", "{}"}:
            return text[:100]
    if isinstance(name, str) and name:
        return name[:100]
    return ""


def _trace_status(trace: Any) -> tuple[str, int | None]:
    """Roll up trace-level status + crag_iterations from trace summary + metadata.

    Returns `(status, crag_iterations)` where:
      - status ∈ {"ok", "error", "crag_triggered"}
      - crag_iterations is the upstream-stamped iteration count, or None
        when the trace isn't a CRAG-triggered run

    Priority: error > crag_triggered > ok. Langfuse trace summary doesn't
    always expose a top-level error flag, so we check (in order):
      1. `trace.level == "ERROR"` (some Langfuse v2 server builds set this)
      2. `trace.metadata.get("status") == "error"` (upstream observe_async
         can stamp this on completion when an exception bubbled out)
      3. `trace.metadata.get("error")` truthy
    CRAG detection: `metadata.get("crag_iterations")` int > 0 OR
    `metadata.get("crag_triggered")` truthy.
    """
    metadata = getattr(trace, "metadata", None)
    meta_dict: dict[str, Any] = metadata if isinstance(metadata, dict) else {}

    crag_iterations_raw = meta_dict.get("crag_iterations")
    crag_iter: int | None = None
    if isinstance(crag_iterations_raw, (int, float)) and not isinstance(crag_iterations_raw, bool):
        crag_iter = int(crag_iterations_raw)

    level = str(getattr(trace, "level", "") or "").upper()
    if level == "ERROR":
        return ("error", crag_iter)
    meta_status = str(meta_dict.get("status", "") or "").lower()
    if meta_status == "error" or meta_dict.get("error"):
        return ("error", crag_iter)

    if (crag_iter is not None and crag_iter > 0) or meta_dict.get("crag_triggered"):
        return ("crag_triggered", crag_iter)

    return ("ok", crag_iter)


def _duration_ms(trace: Any) -> int:
    """Pull duration in ms from `latency` (seconds, Langfuse-derived) or compute from start/end."""
    latency_s = getattr(trace, "latency", None)
    if isinstance(latency_s, (int, float)) and not isinstance(latency_s, bool):
        return int(float(latency_s) * 1000.0)
    start = getattr(trace, "start_time", None) or getattr(trace, "startTime", None)
    end = getattr(trace, "end_time", None) or getattr(trace, "endTime", None)
    if isinstance(start, datetime) and isinstance(end, datetime):
        try:
            return int((end - start).total_seconds() * 1000)
        except (TypeError, ValueError):
            return 0
    return 0


def _stage_count(trace: Any) -> int:
    """Count observations on the trace summary (Langfuse returns list of obs IDs)."""
    obs = getattr(trace, "observations", None)
    if obs is None:
        return 0
    try:
        return len(obs)
    except TypeError:
        return 0


def _kb_id(trace: Any, input_payload: Any) -> str | None:
    """Pull kb_id from `metadata.kb_id` first, fall back to `input.kb_id`."""
    metadata = getattr(trace, "metadata", None)
    if isinstance(metadata, dict):
        kb = metadata.get("kb_id")
        if isinstance(kb, str) and kb:
            return kb
    if isinstance(input_payload, dict):
        kb = input_payload.get("kb_id")
        if isinstance(kb, str) and kb:
            return kb
    return None


def _total_tokens(trace: Any) -> int:
    """Pull total_tokens from server-aggregate fields when present; 0 otherwise.

    Langfuse v2 server exposes `totalTokens` / `total_tokens` on the trace
    summary when generations were billed. We don't recompute from per-obs
    usage here (that would require a deep fetch) — surface what the server
    gave us, 0 otherwise, and let the frontend show "—" for missing data.
    """
    for attr in ("totalTokens", "total_tokens"):
        value = getattr(trace, attr, None)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return int(value)
    return 0


def _cost_usd(trace: Any) -> float:
    """Pull cost in USD from server-aggregate `totalCost` / `total_cost` when present."""
    for attr in ("totalCost", "total_cost", "calculatedTotalCost"):
        value = getattr(trace, attr, None)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return round(float(value), 4)
    return 0.0


def _build_summary(trace: Any) -> TraceSummary:
    """Map one Langfuse trace summary → `TraceSummary` row.

    Defensive against Langfuse SDK shape variations between v2 minor versions
    and self-hosted vs cloud server differences. All field extractions fall
    back to safe defaults (empty string / 0 / None) — the dashboard renders
    the row even when many fields are absent.
    """
    trace_id = str(getattr(trace, "id", "") or getattr(trace, "trace_id", "") or "")
    timestamp = _coerce_iso(getattr(trace, "timestamp", None))
    input_payload = getattr(trace, "input", None)
    name = getattr(trace, "name", None)
    status, crag_iter = _trace_status(trace)

    return TraceSummary(
        trace_id=trace_id,
        timestamp=timestamp,
        duration_ms=_duration_ms(trace),
        status=status,  # type: ignore[arg-type]  # Literal narrowing handled by _trace_status
        kb_id=_kb_id(trace, input_payload),
        query_preview=_query_preview(input_payload, name),
        total_tokens=_total_tokens(trace),
        cost_usd=_cost_usd(trace),
        crag_iterations=crag_iter,
        stage_count=_stage_count(trace),
    )


def _apply_filters(
    items: list[TraceSummary],
    *,
    status_filter: str,
    since: str | None,
    kb_id: str | None,
) -> list[TraceSummary]:
    """Apply post-fetch Python filters (Langfuse SDK doesn't expose these natively)."""
    result = items

    if status_filter == "errors":
        result = [t for t in result if t.status == "error"]
    elif status_filter == "crag_triggered":
        result = [t for t in result if t.status == "crag_triggered"]
    # "all" or anything else → no status filter

    if since:
        result = [t for t in result if t.timestamp and t.timestamp >= since]

    if kb_id:
        result = [t for t in result if t.kb_id == kb_id]

    return result


async def fetch_trace_list(
    *,
    status_filter: str = "all",
    since: str | None = None,
    kb_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> TraceListResponse:
    """Fetch + filter + paginate Langfuse traces for the `/traces` index view.

    Synchronous Langfuse SDK call wrapped in async signature for FastAPI
    route consistency (route is async; SDK is sync — no actual await needed).

    Args:
        status_filter: "all" | "errors" | "crag_triggered" (frontend filter seg)
        since: ISO 8601 timestamp; rows with timestamp < since are excluded
        kb_id: Optional KB scope filter
        limit: Page size 1..500
        offset: Page offset (≥0)

    Returns:
        `TraceListResponse` with paginated items + total (post-filter, pre-page)
        + status (graceful degrade) + note. Never raises.
    """
    client = get_langfuse_client()
    if client is None:
        logger.info("trace_list_fetch_no_client")
        return TraceListResponse(
            items=[],
            total=0,
            limit=limit,
            offset=offset,
            status="no_client",
            note=(
                "Langfuse client not initialized — trace list empty. "
                "Configure LANGFUSE_HOST + LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY "
                ".env to enable trace listing."
            ),
        )

    fetch_method = getattr(client, "fetch_traces", None)
    if fetch_method is None or not callable(fetch_method):
        logger.warning("trace_list_fetch_sdk_method_missing")
        return TraceListResponse(
            items=[],
            total=0,
            limit=limit,
            offset=offset,
            status="sdk_method_missing",
            note=(
                "Langfuse SDK does not expose `fetch_traces` method (SDK version may "
                "be older than v2.x). Upgrade langfuse package to enable trace listing."
            ),
        )

    # Fetch a window large enough to apply post-filter + paging in-process.
    # Cap at `_DEFAULT_FETCH_LIMIT` to bound memory / response time.
    fetch_window = min(_DEFAULT_FETCH_LIMIT, offset + limit + 100)
    try:
        response = fetch_method(limit=fetch_window)
    except Exception as exc:  # noqa: BLE001 — graceful degrade per langfuse_trace.py pattern
        logger.warning(
            "trace_list_fetch_failed",
            error=f"{type(exc).__name__}: {exc}",
        )
        return TraceListResponse(
            items=[],
            total=0,
            limit=limit,
            offset=offset,
            status="fetch_failed",
            note=f"Langfuse fetch error: {type(exc).__name__}: {exc}",
        )

    # Langfuse SDK v2 returns `FetchTracesResponse(data=[...], meta=...)` OR
    # a plain list, depending on version. Duck-type both.
    raw_items = getattr(response, "data", None)
    if raw_items is None:
        raw_items = response if isinstance(response, list) else []

    summaries = [_build_summary(t) for t in raw_items]
    filtered = _apply_filters(
        summaries,
        status_filter=status_filter,
        since=since,
        kb_id=kb_id,
    )
    total = len(filtered)
    page = filtered[offset : offset + limit]

    logger.info(
        "trace_list_fetch_ok",
        fetched=len(summaries),
        filtered=total,
        page_size=len(page),
        status_filter=status_filter,
        since=since,
        kb_id=kb_id,
    )

    return TraceListResponse(
        items=page,
        total=total,
        limit=limit,
        offset=offset,
        status="ok",
    )

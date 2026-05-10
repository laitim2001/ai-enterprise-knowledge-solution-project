"""Langfuse trace fetch for /debug/trace/{trace_id} endpoint (W16 F5.5 CO_W15_F2).

Per Decision D.2 (full Langfuse SDK integration) — extracts per-stage trace
detail from Langfuse client.fetch_trace() response, mapping to V6 9-stage
Debug View consumer (ADR-0020 frontend Session 2 unblock).

Graceful degrade matrix (per CO_F5_refresh feedback.py pattern):
- Langfuse client = None → status "langfuse_not_configured" + trace_url pattern only
- Client.fetch_trace SDK method missing → status "sdk_method_missing"
- Trace not found → status "not_found"
- Fetch raises → status "fetch_failed" + error in note
- Happy path → status "ok" + populated stages

Frontend consumer (V6 9-stage):
- trace_url for "Open in Langfuse" CTA
- stages list for collapsible per-stage breakdown
- total_* aggregates for summary header
"""

from __future__ import annotations

from typing import Any

import structlog

from api.schemas.observability import TraceDetail, TraceStage
from observability.langfuse_tracer import get_langfuse_client
from storage.settings import get_settings

logger = structlog.get_logger(__name__)


def _trace_url(trace_id: str) -> str:
    """Build Langfuse UI URL pattern for a trace_id."""
    settings = get_settings()
    host = settings.langfuse_host.rstrip("/")
    return f"{host}/trace/{trace_id}"


def _extract_stage(observation: Any) -> TraceStage:
    """Map one Langfuse observation → TraceStage. Defensive against SDK shape variations."""
    name = str(getattr(observation, "name", "") or "")
    obs_type = str(getattr(observation, "type", "SPAN") or "SPAN").upper()

    # Latency: end_time - start_time (ms);some SDK versions provide latency_ms directly
    latency_ms = int(getattr(observation, "latency_ms", 0) or 0)
    if latency_ms == 0:
        start = getattr(observation, "start_time", None)
        end = getattr(observation, "end_time", None)
        if start is not None and end is not None:
            try:
                # datetime objects: end - start = timedelta
                latency_ms = int((end - start).total_seconds() * 1000)
            except (TypeError, AttributeError):
                latency_ms = 0

    # ADR-0020 Session 2 — stage-specific metadata. Both `observe_async` and
    # `emit_stage_metadata` stash a `duration_ms` int plus arbitrary extra keys
    # in the observation's `metadata` dict (e.g. Context Expander
    # `expanded_count` / `boundary_skip_count`, CRAG `triggered` / `iterations`).
    # Surface the extras as `details`; use `duration_ms` as a final latency
    # fallback when the SDK didn't expose timed start/end on this observation.
    metadata = getattr(observation, "metadata", None)
    details: dict[str, Any] | None = None
    if isinstance(metadata, dict):
        if latency_ms == 0:
            raw_duration = metadata.get("duration_ms")
            if isinstance(raw_duration, (int, float)) and not isinstance(raw_duration, bool):
                latency_ms = int(raw_duration)
        extra = {k: v for k, v in metadata.items() if k != "duration_ms"}
        if extra:
            details = extra

    model = getattr(observation, "model", None)
    if model is not None:
        model = str(model)

    # Token usage shape varies: usage.input / usage.output OR usage.prompt_tokens / completion_tokens
    usage = getattr(observation, "usage", None)
    input_tokens = 0
    output_tokens = 0
    if usage is not None:
        input_tokens = int(
            getattr(usage, "input", None)
            or getattr(usage, "prompt_tokens", None)
            or 0
        )
        output_tokens = int(
            getattr(usage, "output", None)
            or getattr(usage, "completion_tokens", None)
            or 0
        )

    # Status: level field (DEBUG/DEFAULT/WARNING/ERROR) → ok/error
    level = str(getattr(observation, "level", "DEFAULT") or "DEFAULT").upper()
    if level == "ERROR":
        status = "error"
    elif level == "WARNING":
        status = "ok"  # warnings don't fail the stage
    else:
        status = "ok"

    return TraceStage(
        name=name,
        type=obs_type,
        latency_ms=latency_ms,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        status=status,
        details=details,
    )


async def fetch_trace(trace_id: str) -> TraceDetail:
    """Fetch trace detail from Langfuse SDK + return TraceDetail per D.2 full integration.

    Synchronous Langfuse SDK call wrapped in async signature for FastAPI route
    consistency (route is async; SDK is sync — no actual await needed).
    """
    trace_url = _trace_url(trace_id)

    client = get_langfuse_client()
    if client is None:
        logger.info(
            "langfuse_trace_fetch_no_client",
            trace_id=trace_id,
        )
        return TraceDetail(
            trace_id=trace_id,
            trace_url=trace_url,
            status="langfuse_not_configured",
            note=(
                "Langfuse client not initialized — trace_url pattern returned for "
                "frontend Langfuse UI deep-link (CTA still functional). "
                "Configure LANGFUSE_HOST + LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY "
                ".env to enable stage extraction."
            ),
        )

    fetch_method = getattr(client, "fetch_trace", None)
    if fetch_method is None or not callable(fetch_method):
        logger.warning(
            "langfuse_trace_fetch_sdk_method_missing",
            trace_id=trace_id,
        )
        return TraceDetail(
            trace_id=trace_id,
            trace_url=trace_url,
            status="sdk_method_missing",
            note=(
                "Langfuse SDK does not expose `fetch_trace` method (SDK version may "
                "be older than v2.x);trace_url pattern returned for UI deep-link. "
                "Upgrade langfuse package to enable stage extraction."
            ),
        )

    try:
        response = fetch_method(trace_id)
    except Exception as exc:  # noqa: BLE001 — graceful degrade per CO_F5_refresh pattern
        logger.warning(
            "langfuse_trace_fetch_failed",
            trace_id=trace_id,
            error=f"{type(exc).__name__}: {exc}",
        )
        return TraceDetail(
            trace_id=trace_id,
            trace_url=trace_url,
            status="fetch_failed",
            note=f"Langfuse fetch error: {type(exc).__name__}: {exc}",
        )

    # Langfuse SDK fetch_trace returns FetchTraceResponse with .data attribute
    trace_data = getattr(response, "data", response)
    if trace_data is None:
        return TraceDetail(
            trace_id=trace_id,
            trace_url=trace_url,
            status="not_found",
            note=f"Trace '{trace_id}' not found in Langfuse",
        )

    # Extract stages from observations list
    observations = getattr(trace_data, "observations", []) or []
    stages = [_extract_stage(obs) for obs in observations]

    # Aggregate totals
    total_latency_ms = sum(s.latency_ms for s in stages)
    total_input_tokens = sum(s.input_tokens for s in stages)
    total_output_tokens = sum(s.output_tokens for s in stages)

    logger.info(
        "langfuse_trace_fetch_ok",
        trace_id=trace_id,
        stages_count=len(stages),
        total_latency_ms=total_latency_ms,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
    )

    return TraceDetail(
        trace_id=trace_id,
        trace_url=trace_url,
        status="ok",
        total_latency_ms=total_latency_ms,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        stages=stages,
    )

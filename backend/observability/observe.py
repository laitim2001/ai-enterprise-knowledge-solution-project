"""C07 Observability — `@observe_async` decorator (W9 D1 F5.2-kickoff).

Per W08 retro § Carry-over C8 + W9 plan §2 F5.2:wire Langfuse SDK accessor
(W8 D5 F5.1)to per-stage trace capture so `/observability/cost-summary`
roadmap upgrade from static projection to real-time attribution can flow。

Three design tenets(Karpathy §1.2 simplicity-first):
  1. **Degrade-graceful** — wrapper NEVER raises into the wrapped function
     path;Langfuse client absent / `trace()` raise / SDK API drift all become
     no-ops with structured warning logs。
  2. **Surgical decoration** — single decorator covers query / synthesizer /
     retrieval / crag stages without touching their bodies;`capture_attrs`
     extracts attributes from the awaited result(e.g. `input_tokens` /
     `output_tokens` / `latency_ms` / `total_latency_ms`)so per-stage cost
     attribution flows automatically。
  3. **Always-emit structlog** — even when Langfuse is None,every wrapped
     call emits a `stage_complete` / `stage_failed` JSON log line。Audit
     pipeline + future log-based cost reconstruction both benefit。

W9 D2+ progressive scope = upgrade `client.trace()` to `client.generation()`
for LLM-stage calls so Langfuse cost-attribution dashboard flows real-time
USD per query。This module is the seam where that upgrade lands。
"""

from __future__ import annotations

import functools
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import structlog

from observability.langfuse_tracer import get_langfuse_client

T = TypeVar("T")

_logger = structlog.get_logger("ekp.observe")


def observe_async(
    name: str | None = None,
    capture_attrs: tuple[str, ...] = (),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator emitting a Langfuse trace span(when client wired)+
    `stage_complete` / `stage_failed` structlog event(always)around an
    async callable。

    Args:
        name: Span name(defaults to `fn.__qualname__` so methods get
            `Class.method` and free functions get the bare name)。
        capture_attrs: Attribute names to extract from the awaited result
            for inclusion in the trace metadata + structured log。Used to
            pull token counts off `SynthesisResult` and timing fields off
            `RetrievalResult` without modifying their bodies。Missing
            attributes are silently skipped。

    The wrapper preserves the wrapped function's signature via
    `functools.wraps`,so FastAPI Depends + Pydantic model_rebuild + tests
    that introspect `__wrapped__` keep working。
    """

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        span_name = name or getattr(fn, "__qualname__", fn.__name__)

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            client = get_langfuse_client()
            start = time.perf_counter()

            try:
                result = await fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 — re-raised below
                duration_ms = int((time.perf_counter() - start) * 1000)
                _logger.warning(
                    "stage_failed",
                    stage=span_name,
                    duration_ms=duration_ms,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
                _emit_trace_safe(
                    client,
                    span_name,
                    output={"status": "error", "error_type": type(exc).__name__},
                    metadata={"duration_ms": duration_ms},
                )
                raise

            duration_ms = int((time.perf_counter() - start) * 1000)
            metadata: dict[str, Any] = {"duration_ms": duration_ms}
            for attr in capture_attrs:
                value = getattr(result, attr, None)
                if value is not None:
                    metadata[attr] = value

            _logger.info("stage_complete", stage=span_name, **metadata)
            _emit_trace_safe(
                client,
                span_name,
                output={"status": "ok"},
                metadata=metadata,
            )
            return result

        return wrapper

    return decorator


def _emit_trace_safe(
    client: object | None,
    span_name: str,
    *,
    output: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    """Best-effort Langfuse trace emit — swallow every failure mode.

    Three SDK API shapes considered(any one suffices;all skipped if absent):
      - `client.trace(name=..., output=..., metadata=...)`(2.x baseline)
      - Legacy positional / keyword variants captured via try/except

    Tracer must NEVER block the wrapped function path on observability error。
    Test coverage:`test_observe.py::test_trace_emit_failure_swallowed`。
    """
    if client is None:
        return
    trace_fn = getattr(client, "trace", None)
    if not callable(trace_fn):
        return
    try:
        trace_fn(name=span_name, output=output, metadata=metadata)
    except Exception as exc:  # noqa: BLE001 — observability never breaks the request path
        _logger.warning(
            "trace_emit_failed",
            stage=span_name,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )

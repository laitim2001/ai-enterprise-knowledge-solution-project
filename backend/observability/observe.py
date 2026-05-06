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

import asyncio
import functools
import time
from collections.abc import AsyncIterator, Awaitable, Callable
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


def observe_llm_async(
    name: str | None = None,
    *,
    model_attr: str = "deployment",
    input_tokens_attr: str = "input_tokens",
    output_tokens_attr: str = "output_tokens",
    extra_metadata_attrs: tuple[str, ...] = (),
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """LLM-stage decorator emitting Langfuse `client.generation()`(W9 D2 F5.2 upgrade).

    Difference from `observe_async`:
      - Emits `client.generation()` instead of `client.trace()` so Langfuse
        cost-attribution dashboard sees the LLM call as a billable
        generation event(per-model cost table multiplies usage tokens)
      - Maps result attributes to generation event shape:`model` from
        `model_attr` + `usage` from `input_tokens_attr` + `output_tokens_attr`
      - Anything else listed in `extra_metadata_attrs` lands in metadata

    `/observability/cost-summary` endpoint thus rises from static projection
    (architecture.md §9 baseline)to **real-time per-query USD attribution**
    once Langfuse client is wired and `client.generation_dashboard_api` reads
    these events(W11+ Beta cohort onset)。

    Apply to LLM-stage methods only(synthesizer.synthesize / crag.grade /
    crag.rewrite_query)。Non-LLM stages keep `observe_async`(retrieve / refine
    orchestration)。

    H5 SECURITY:wrapper does NOT pass `input` / `output` text to Langfuse —
    only token COUNTS。Full prompt / answer payload remains private(per
    CLAUDE.md §5.5 — never log full LLM prompts to plaintext)。Langfuse
    cloud receives:model name + input/output token counts + metadata fields;
    NO prompt content, NO answer content, NO chunk_text。
    """

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        gen_name = name or getattr(fn, "__qualname__", fn.__name__)

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            client = get_langfuse_client()
            start = time.perf_counter()

            try:
                result = await fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 — re-raised below
                duration_ms = int((time.perf_counter() - start) * 1000)
                _logger.warning(
                    "llm_stage_failed",
                    stage=gen_name,
                    duration_ms=duration_ms,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                )
                _emit_generation_safe(
                    client,
                    gen_name,
                    model=None,
                    input_tokens=None,
                    output_tokens=None,
                    metadata={"duration_ms": duration_ms, "status": "error"},
                )
                raise

            duration_ms = int((time.perf_counter() - start) * 1000)
            model = getattr(result, model_attr, None)
            input_tokens = getattr(result, input_tokens_attr, None)
            output_tokens = getattr(result, output_tokens_attr, None)

            metadata: dict[str, Any] = {"duration_ms": duration_ms, "status": "ok"}
            for attr in extra_metadata_attrs:
                value = getattr(result, attr, None)
                if value is not None:
                    metadata[attr] = value

            _logger.info(
                "llm_stage_complete",
                stage=gen_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                **metadata,
            )
            _emit_generation_safe(
                client,
                gen_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                metadata=metadata,
            )
            return result

        return wrapper

    return decorator


def _emit_generation_safe(
    client: object | None,
    gen_name: str,
    *,
    model: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
    metadata: dict[str, Any],
) -> None:
    """Best-effort Langfuse generation emit — swallow every failure mode.

    Generation event shape per Langfuse SDK 2.x:
        client.generation(
            name=..., model=..., usage={"input": N, "output": M, "unit": "TOKENS"},
            metadata=...,
        )

    `usage` skipped when token counts are None(graceful degradation when
    upstream stage didn't capture tokens)。Tracer must NEVER block the wrapped
    function path on observability error — same H5 + Karpathy §1.2 pattern as
    `_emit_trace_safe`。
    """
    if client is None:
        return
    gen_fn = getattr(client, "generation", None)
    if not callable(gen_fn):
        # Fallback to trace() when generation() not available — keeps cost
        # attribution best-effort across SDK versions
        _emit_trace_safe(client, gen_name, output={"status": metadata.get("status", "ok")}, metadata=metadata)
        return
    kwargs: dict[str, Any] = {"name": gen_name, "metadata": metadata}
    if model is not None:
        kwargs["model"] = model
    if input_tokens is not None and output_tokens is not None:
        kwargs["usage"] = {
            "input": input_tokens,
            "output": output_tokens,
            "unit": "TOKENS",
        }
    try:
        gen_fn(**kwargs)
    except Exception as exc:  # noqa: BLE001
        _logger.warning(
            "generation_emit_failed",
            stage=gen_name,
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


async def observe_streaming(
    stream: AsyncIterator[Any],
    *,
    name: str,
    done_event_type: str = "done",
    model_field: str = "model",
    input_tokens_field: str = "input_tokens",
    output_tokens_field: str = "output_tokens",
    extra_metadata_fields: tuple[str, ...] = (),
) -> AsyncIterator[Any]:
    """SSE async-iterator passthrough wrapper(W10 D1 F4.1 — closes W9 D4 carry-over).

    Difference from `observe_async` / `observe_llm_async`(decorators on
    result-returning coroutines):
      - Wraps an async iterator(NOT a coroutine);events flow through
        unchanged so SSE protocol semantics + Vercel AI SDK frame ordering
        preserved exactly。
      - Captures usage metadata from a terminal sentinel event matching
        `done_event_type`(matches `compose_query_stream` final frame
        `{"type":"done", "model":..., "input_tokens":..., "output_tokens":...}`)。
      - Handles `asyncio.CancelledError` gracefully — client disconnect
        mid-stream still emits a Langfuse generation event with
        `status=cancelled` so partial-spend cost attribution remains
        accurate(no metadata leak past the disconnect point)。

    Use as a passthrough wrapper around `compose_query_stream(...)` in the
    `/query/stream` SSE handler。Decorator form rejected because the
    natural seam is the iterator object,not the iterator-producing function。

    Args:
        stream: Async iterator yielding SSE event dicts。`done` event must
            be a dict for capture to fire;non-dict events pass through
            silently(no capture attempted)。
        name: Langfuse generation event name(e.g. "api.query.stream")。
        done_event_type: Event `type` value signalling end-of-stream
            (default "done" matches `compose_query_stream`)。
        model_field / input_tokens_field / output_tokens_field: Field
            names on the done event that carry usage data。
        extra_metadata_fields: Additional fields pulled from the done
            event into Langfuse metadata(e.g. `("refused", "reranker_used")`)。

    H5 SECURITY:same guarantee as `observe_llm_async` — only token counts
    + model + structured metadata flow to Langfuse。`text-delta` content
    + `citation` payloads are NEVER captured into trace metadata。Full
    prompt / answer remain private(per CLAUDE.md §5.5 H5)。

    Cost attribution flow:
        client connects → /query/stream → compose_query_stream yields
        text-delta* citation* done → observe_streaming captures usage from
        done frame → emits client.generation() with model + usage tokens →
        Langfuse cost dashboard rolls per-query USD attribution real-time
        (per architecture.md §9 + W11+ Beta cohort cost dashboard upgrade)。
    """
    client = get_langfuse_client()
    start = time.perf_counter()
    captured_model: str | None = None
    captured_input_tokens: int | None = None
    captured_output_tokens: int | None = None
    captured_extras: dict[str, Any] = {}
    status = "ok"
    error_type: str | None = None

    try:
        async for event in stream:
            if isinstance(event, dict) and event.get("type") == done_event_type:
                model_value = event.get(model_field)
                if model_value:
                    captured_model = str(model_value)
                input_value = event.get(input_tokens_field)
                if input_value is not None:
                    try:
                        captured_input_tokens = int(input_value)
                    except (TypeError, ValueError):
                        captured_input_tokens = None
                output_value = event.get(output_tokens_field)
                if output_value is not None:
                    try:
                        captured_output_tokens = int(output_value)
                    except (TypeError, ValueError):
                        captured_output_tokens = None
                for field in extra_metadata_fields:
                    value = event.get(field)
                    if value is not None:
                        captured_extras[field] = value
            yield event
    except asyncio.CancelledError:
        status = "cancelled"
        raise
    except Exception as exc:  # noqa: BLE001 — observed in finally + re-raised
        status = "error"
        error_type = type(exc).__name__
        raise
    finally:
        duration_ms = int((time.perf_counter() - start) * 1000)
        metadata: dict[str, Any] = {"duration_ms": duration_ms, "status": status}
        if error_type is not None:
            metadata["error_type"] = error_type
        metadata.update(captured_extras)
        log_event = "stream_complete" if status == "ok" else "stream_terminated"
        log_kwargs: dict[str, Any] = {
            "stage": name,
            "status": status,
            "model": captured_model,
            "input_tokens": captured_input_tokens,
            "output_tokens": captured_output_tokens,
            "duration_ms": duration_ms,
        }
        if error_type is not None:
            log_kwargs["error_type"] = error_type
        log_kwargs.update(captured_extras)
        _logger.info(log_event, **log_kwargs)
        _emit_generation_safe(
            client,
            name,
            model=captured_model,
            input_tokens=captured_input_tokens,
            output_tokens=captured_output_tokens,
            metadata=metadata,
        )

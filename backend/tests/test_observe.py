"""W9 D1 F5.2-kickoff — `@observe_async` decorator coverage.

Per W08 retro § Carry-over C8 + W9 plan §2 F5.2 acceptance:
  - Wrapped async function emits structured `stage_complete` log line
  - Langfuse `client.trace()` invoked when client wired
  - No-op when client absent (local dev / CI)
  - capture_attrs extracts attributes from the awaited result for trace metadata
  - Wrapper NEVER raises into the wrapped call path on Langfuse failure
  - Exception in wrapped fn → `stage_failed` event + trace error span + re-raise

Tests use the `_set_langfuse_client_for_tests` fixture from F5.1 to swap in
a `MagicMock` for assertion;production code path goes through `init_tracer`.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
import structlog

from observability import langfuse_tracer
from observability.observe import (
    emit_stage_metadata,
    observe_async,
    observe_llm_async,
    observe_streaming,
)


@pytest.fixture(autouse=True)
def _reset_singleton_and_bridge_structlog() -> None:
    """Reset Langfuse singleton + bridge structlog → stdlib logging so caplog
    captures `ekp.observe` events(matches test_audit_log.py pattern)。
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    langfuse_tracer._set_langfuse_client_for_tests(None)
    yield
    langfuse_tracer._set_langfuse_client_for_tests(None)


@dataclass(slots=True, frozen=True)
class _FakeResult:
    input_tokens: int
    output_tokens: int
    latency_ms: int


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------


async def test_wrapper_returns_unchanged_result_when_no_client() -> None:
    @observe_async(name="test.unit")
    async def fn(x: int) -> int:
        return x * 2

    assert await fn(21) == 42


async def test_wrapper_emits_stage_complete_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="ekp.observe")

    @observe_async(name="test.timing")
    async def fn() -> str:
        return "ok"

    await fn()

    blob = "\n".join(r.getMessage() for r in caplog.records if r.name == "ekp.observe")
    assert "stage_complete" in blob
    assert "test.timing" in blob


async def test_capture_attrs_pulls_token_counts_into_metadata() -> None:
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @observe_async(
        name="synthesizer.synthesize",
        capture_attrs=("input_tokens", "output_tokens", "latency_ms"),
    )
    async def fake_synth() -> _FakeResult:
        return _FakeResult(input_tokens=128, output_tokens=64, latency_ms=80)

    result = await fake_synth()

    assert result.input_tokens == 128
    fake_client.trace.assert_called_once()
    _args, kwargs = fake_client.trace.call_args
    assert kwargs["name"] == "synthesizer.synthesize"
    assert kwargs["output"] == {"status": "ok"}
    md = kwargs["metadata"]
    assert md["input_tokens"] == 128
    assert md["output_tokens"] == 64
    assert md["latency_ms"] == 80
    assert "duration_ms" in md


async def test_capture_attrs_skips_missing_attribute_silently() -> None:
    """Result lacks `output_tokens` — wrapper extracts what it can."""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @dataclass
    class _Partial:
        input_tokens: int

    @observe_async(
        name="partial.stage",
        capture_attrs=("input_tokens", "output_tokens"),
    )
    async def fn() -> _Partial:
        return _Partial(input_tokens=42)

    await fn()
    md = fake_client.trace.call_args.kwargs["metadata"]
    assert md["input_tokens"] == 42
    assert "output_tokens" not in md


async def test_default_name_uses_qualname() -> None:
    """When `name=None`,decorator uses `fn.__qualname__`."""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @observe_async()
    async def my_named_function() -> int:
        return 7

    await my_named_function()
    assert fake_client.trace.call_args.kwargs["name"].endswith("my_named_function")


# ---------------------------------------------------------------------------
# Failure paths — wrapper must never raise into call path
# ---------------------------------------------------------------------------


async def test_trace_emit_failure_swallowed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`client.trace()` raises → wrapper still returns the wrapped result."""
    fake_client = MagicMock()
    fake_client.trace.side_effect = RuntimeError("network down")
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)
    caplog.set_level(logging.WARNING, logger="ekp.observe")

    @observe_async(name="emit.failing")
    async def fn() -> str:
        return "still ok"

    result = await fn()  # MUST NOT raise
    assert result == "still ok"

    warn_msgs = "\n".join(
        r.getMessage()
        for r in caplog.records
        if r.name == "ekp.observe" and r.levelno >= logging.WARNING
    )
    assert "trace_emit_failed" in warn_msgs


async def test_client_without_trace_method_is_noop() -> None:
    fake_client = object()  # no .trace attribute
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @observe_async(name="trace.absent")
    async def fn() -> str:
        return "ok"

    assert await fn() == "ok"


async def test_wrapped_exception_propagates_with_stage_failed_event(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)
    caplog.set_level(logging.WARNING, logger="ekp.observe")

    @observe_async(name="test.failing")
    async def fn() -> None:
        raise ValueError("upstream broke")

    with pytest.raises(ValueError, match="upstream broke"):
        await fn()

    blob = "\n".join(r.getMessage() for r in caplog.records if r.name == "ekp.observe")
    assert "stage_failed" in blob
    assert "ValueError" in blob

    # Trace span emitted with error output
    fake_client.trace.assert_called_once()
    kwargs = fake_client.trace.call_args.kwargs
    assert kwargs["output"]["status"] == "error"
    assert kwargs["output"]["error_type"] == "ValueError"


async def test_signature_preserved_for_introspection() -> None:
    """`functools.wraps` preserves __wrapped__ + __name__ for FastAPI Depends."""
    @observe_async(name="api.handler")
    async def my_handler(x: int, y: int = 5) -> int:
        return x + y

    assert my_handler.__name__ == "my_handler"
    assert hasattr(my_handler, "__wrapped__")

    import inspect

    sig = inspect.signature(my_handler)
    assert "x" in sig.parameters
    assert "y" in sig.parameters
    assert sig.parameters["y"].default == 5


# ---------------------------------------------------------------------------
# Integration smoke — decorator stacks compatibly with @retry
# ---------------------------------------------------------------------------


async def test_decorator_composes_with_tenacity_retry() -> None:
    """observe_async + @retry(reraise=True) — wrapper observes the FINAL outcome
    after retries(matches synthesizer.py production stack order)."""
    from tenacity import retry, stop_after_attempt

    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    attempt_counter = {"n": 0}

    @observe_async(name="composed.stage")
    @retry(stop=stop_after_attempt(3), reraise=True)
    async def fn() -> str:
        attempt_counter["n"] += 1
        if attempt_counter["n"] < 2:
            raise ConnectionError("transient")
        return "settled"

    assert await fn() == "settled"
    assert attempt_counter["n"] == 2
    # Single trace span for the FINAL outcome (retries are internal).
    fake_client.trace.assert_called_once()
    assert fake_client.trace.call_args.kwargs["output"]["status"] == "ok"


# ===========================================================================
# observe_llm_async — W9 D2 F5.2 upgrade(client.generation()emit)
# ===========================================================================


# ---------------------------------------------------------------------------
# emit_stage_metadata (ADR-0020 Session 2 — Context Expander stage emit)
# ---------------------------------------------------------------------------


async def test_emit_stage_metadata_emits_trace_with_metadata() -> None:
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    emit_stage_metadata(
        "generation.context_expansion",
        duration_ms=37,
        requested_count=5,
        expanded_count=3,
        boundary_skip_count=2,
    )

    fake_client.trace.assert_called_once()
    kwargs = fake_client.trace.call_args.kwargs
    assert kwargs["name"] == "generation.context_expansion"
    assert kwargs["output"] == {"status": "ok"}
    assert kwargs["metadata"] == {
        "duration_ms": 37,
        "requested_count": 5,
        "expanded_count": 3,
        "boundary_skip_count": 2,
    }


async def test_emit_stage_metadata_no_op_when_client_absent() -> None:
    # autouse fixture already set client to None — assert it doesn't raise.
    emit_stage_metadata("generation.context_expansion", duration_ms=0)


async def test_emit_stage_metadata_swallows_trace_failure() -> None:
    fake_client = MagicMock()
    fake_client.trace = MagicMock(side_effect=RuntimeError("langfuse down"))
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    # Must NOT propagate — observability never breaks the request path.
    emit_stage_metadata("generation.context_expansion", duration_ms=12, expanded_count=1)


@dataclass(slots=True, frozen=True)
class _FakeLLMResult:
    deployment: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    refused: bool


async def test_llm_decorator_emits_generation_with_usage() -> None:
    """LLM decorator maps deployment + token counts to client.generation()."""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @observe_llm_async(
        name="synthesizer.synthesize",
        extra_metadata_attrs=("latency_ms", "refused"),
    )
    async def fake_synthesize() -> _FakeLLMResult:
        return _FakeLLMResult(
            deployment="gpt-5-5",
            input_tokens=1024,
            output_tokens=256,
            latency_ms=1500,
            refused=False,
        )

    result = await fake_synthesize()
    assert result.input_tokens == 1024

    fake_client.generation.assert_called_once()
    kwargs = fake_client.generation.call_args.kwargs
    assert kwargs["name"] == "synthesizer.synthesize"
    assert kwargs["model"] == "gpt-5-5"
    assert kwargs["usage"] == {"input": 1024, "output": 256, "unit": "TOKENS"}
    md = kwargs["metadata"]
    assert md["status"] == "ok"
    assert md["duration_ms"] >= 0
    assert md["latency_ms"] == 1500
    assert md["refused"] is False
    # trace() NOT called when generation() is available
    fake_client.trace.assert_not_called()


async def test_llm_decorator_skips_usage_when_tokens_missing() -> None:
    """Result without token counts → generation emitted without usage field."""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @dataclass
    class _NoTokens:
        deployment: str

    @observe_llm_async(name="missing.tokens")
    async def fn() -> _NoTokens:
        return _NoTokens(deployment="gpt-5-5")

    await fn()
    kwargs = fake_client.generation.call_args.kwargs
    assert kwargs["model"] == "gpt-5-5"
    assert "usage" not in kwargs


async def test_llm_decorator_falls_back_to_trace_when_no_generation() -> None:
    """Older SDK without generation() — wrapper falls back to trace()."""
    fake_client = MagicMock(spec=["trace"])  # NO generation attribute
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @observe_llm_async(name="legacy.client")
    async def fn() -> _FakeLLMResult:
        return _FakeLLMResult("gpt-5-5", 100, 50, 200, False)

    await fn()
    fake_client.trace.assert_called_once()


async def test_llm_decorator_no_op_when_client_absent() -> None:
    """Local dev / CI — no client → wrapper returns unchanged result."""
    @observe_llm_async(name="solo.test")
    async def fn() -> _FakeLLMResult:
        return _FakeLLMResult("gpt-5-5", 100, 50, 200, False)

    result = await fn()
    assert result.input_tokens == 100


async def test_llm_decorator_swallows_generation_emit_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`client.generation()` raises → wrapper still returns result + warns."""
    fake_client = MagicMock()
    fake_client.generation.side_effect = RuntimeError("network down")
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)
    caplog.set_level(logging.WARNING, logger="ekp.observe")

    @observe_llm_async(name="emit.failing")
    async def fn() -> _FakeLLMResult:
        return _FakeLLMResult("gpt-5-5", 100, 50, 200, False)

    result = await fn()
    assert result.input_tokens == 100

    warn_msgs = "\n".join(
        r.getMessage() for r in caplog.records if r.name == "ekp.observe"
    )
    assert "generation_emit_failed" in warn_msgs


async def test_llm_decorator_propagates_exception_with_error_status(
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)
    caplog.set_level(logging.WARNING, logger="ekp.observe")

    @observe_llm_async(name="llm.failing")
    async def fn() -> _FakeLLMResult:
        raise TimeoutError("LLM call exceeded 30s")

    with pytest.raises(TimeoutError):
        await fn()

    blob = "\n".join(r.getMessage() for r in caplog.records if r.name == "ekp.observe")
    assert "llm_stage_failed" in blob
    assert "TimeoutError" in blob

    # Generation emitted with error status + no usage(model+tokens unknown)
    fake_client.generation.assert_called_once()
    kwargs = fake_client.generation.call_args.kwargs
    assert kwargs["metadata"]["status"] == "error"
    assert "model" not in kwargs
    assert "usage" not in kwargs


async def test_llm_decorator_h5_no_prompt_or_answer_text_emitted() -> None:
    """H5 SECURITY:wrapper passes ONLY token counts + model + metadata —
    NEVER prompt content / answer content / chunk text."""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    @observe_llm_async(name="h5.privacy")
    async def fn() -> _FakeLLMResult:
        return _FakeLLMResult("gpt-5-5", 100, 50, 200, False)

    await fn()
    kwargs = fake_client.generation.call_args.kwargs
    # Crucial H5 assertion:no `input` / `output` text fields ever emitted
    assert "input" not in kwargs
    assert "output" not in kwargs
    # Only structured fields:name, model, usage, metadata
    assert set(kwargs.keys()) <= {"name", "model", "usage", "metadata"}


# ===========================================================================
# observe_streaming — W10 D1 F4.1(SSE flow capture variant;closes W9 D4 carry-over)
# ===========================================================================


async def _make_stream(events: list[dict]) -> AsyncIterator[dict]:
    """Build a tiny async iterator yielding the supplied events in order。"""
    for event in events:
        yield event


async def test_observe_streaming_emits_generation_with_done_frame() -> None:
    """Terminal `done` event drives Langfuse `client.generation()` emit。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    events = [
        {"type": "text-delta", "content": "Hello "},
        {"type": "text-delta", "content": "world."},
        {
            "type": "done",
            "model": "gpt-5-5",
            "input_tokens": 1024,
            "output_tokens": 256,
            "latency_ms": 1500,
            "refused": False,
            "reranker_used": "cohere-v3.5",
        },
    ]

    seen: list[dict] = []
    async for event in observe_streaming(
        _make_stream(events),
        name="api.query.stream",
        extra_metadata_fields=("refused", "reranker_used"),
    ):
        seen.append(event)

    # Passthrough preserves order + content unchanged
    assert seen == events

    fake_client.generation.assert_called_once()
    kwargs = fake_client.generation.call_args.kwargs
    assert kwargs["name"] == "api.query.stream"
    assert kwargs["model"] == "gpt-5-5"
    assert kwargs["usage"] == {"input": 1024, "output": 256, "unit": "TOKENS"}
    md = kwargs["metadata"]
    assert md["status"] == "ok"
    assert md["duration_ms"] >= 0
    assert md["refused"] is False
    assert md["reranker_used"] == "cohere-v3.5"


async def test_observe_streaming_no_done_frame_emits_generation_without_usage() -> None:
    """Stream ends without `done` sentinel — generation emitted with no usage。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    events = [
        {"type": "text-delta", "content": "partial "},
        {"type": "text-delta", "content": "no terminal frame"},
    ]

    async for _ in observe_streaming(_make_stream(events), name="stream.no-done"):
        pass

    fake_client.generation.assert_called_once()
    kwargs = fake_client.generation.call_args.kwargs
    assert kwargs["name"] == "stream.no-done"
    assert "model" not in kwargs
    assert "usage" not in kwargs
    assert kwargs["metadata"]["status"] == "ok"


async def test_observe_streaming_no_op_when_client_absent() -> None:
    """Local dev / CI — no client → wrapper passes events through silently。"""
    events = [
        {"type": "text-delta", "content": "hi"},
        {"type": "done", "model": "gpt-5-5", "input_tokens": 5, "output_tokens": 3},
    ]

    seen = [event async for event in observe_streaming(_make_stream(events), name="solo.test")]
    assert seen == events


async def test_observe_streaming_handles_cancellation_with_status_cancelled() -> None:
    """Mid-stream `asyncio.CancelledError` → emit generation `status=cancelled`。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    async def _stream_then_cancel() -> AsyncIterator[dict]:
        yield {"type": "text-delta", "content": "before-cancel"}
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        async for _ in observe_streaming(_stream_then_cancel(), name="stream.cancel"):
            pass

    fake_client.generation.assert_called_once()
    kwargs = fake_client.generation.call_args.kwargs
    assert kwargs["metadata"]["status"] == "cancelled"
    # No usage captured(no done frame seen before cancellation)
    assert "usage" not in kwargs
    assert "model" not in kwargs


async def test_observe_streaming_handles_exception_with_status_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Mid-stream exception → emit generation `status=error` + propagate。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)
    caplog.set_level(logging.INFO, logger="ekp.observe")

    async def _stream_then_raise() -> AsyncIterator[dict]:
        yield {"type": "text-delta", "content": "before-error"}
        raise RuntimeError("synth blew up mid-stream")

    with pytest.raises(RuntimeError, match="synth blew up"):
        async for _ in observe_streaming(_stream_then_raise(), name="stream.error"):
            pass

    fake_client.generation.assert_called_once()
    kwargs = fake_client.generation.call_args.kwargs
    assert kwargs["metadata"]["status"] == "error"
    assert kwargs["metadata"]["error_type"] == "RuntimeError"

    blob = "\n".join(r.getMessage() for r in caplog.records if r.name == "ekp.observe")
    assert "stream_terminated" in blob


async def test_observe_streaming_swallows_emit_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """`client.generation()` raises → wrapper still passes events + warns。"""
    fake_client = MagicMock()
    fake_client.generation.side_effect = RuntimeError("network down")
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)
    caplog.set_level(logging.WARNING, logger="ekp.observe")

    events = [
        {"type": "text-delta", "content": "ok"},
        {"type": "done", "model": "gpt-5-5", "input_tokens": 10, "output_tokens": 5},
    ]
    seen = [event async for event in observe_streaming(_make_stream(events), name="emit.fail")]
    assert seen == events

    warn_msgs = "\n".join(
        r.getMessage()
        for r in caplog.records
        if r.name == "ekp.observe" and r.levelno >= logging.WARNING
    )
    assert "generation_emit_failed" in warn_msgs


async def test_observe_streaming_h5_no_text_delta_content_in_metadata() -> None:
    """H5 SECURITY:text-delta content + citation payloads NEVER captured into metadata。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    events = [
        {"type": "text-delta", "content": "secret prompt content here"},
        {"type": "citation", "citation": {"chunk_id": "c1", "chunk_text": "private chunk"}},
        {
            "type": "done",
            "model": "gpt-5-5",
            "input_tokens": 100,
            "output_tokens": 50,
            "refused": False,
        },
    ]

    async for _ in observe_streaming(
        _make_stream(events),
        name="h5.privacy",
        extra_metadata_fields=("refused",),
    ):
        pass

    kwargs = fake_client.generation.call_args.kwargs
    serialised = repr(kwargs)
    # H5 hard guarantees:no text-delta content + no citation chunk_text in payload
    assert "secret prompt content here" not in serialised
    assert "private chunk" not in serialised
    assert "input" not in kwargs  # raw input field not emitted
    assert "output" not in kwargs  # raw output field not emitted
    # Only structured shape:name, model, usage, metadata
    assert set(kwargs.keys()) <= {"name", "model", "usage", "metadata"}


async def test_observe_streaming_extra_metadata_fields_filter_to_done_only() -> None:
    """`extra_metadata_fields` only pulled from the `done` event,not other events。"""
    fake_client = MagicMock()
    langfuse_tracer._set_langfuse_client_for_tests(fake_client)

    events = [
        # Fake non-done event with `refused` field — must NOT leak into metadata
        {"type": "text-delta", "content": "x", "refused": True},
        {"type": "done", "model": "m", "input_tokens": 1, "output_tokens": 1, "refused": False},
    ]

    async for _ in observe_streaming(
        _make_stream(events),
        name="filter.test",
        extra_metadata_fields=("refused",),
    ):
        pass

    md = fake_client.generation.call_args.kwargs["metadata"]
    # refused captured from the done frame(False),not from the text-delta(True)
    assert md["refused"] is False

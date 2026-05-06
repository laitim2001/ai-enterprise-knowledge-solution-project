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

import logging
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
import structlog

from observability import langfuse_tracer
from observability.observe import observe_async


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

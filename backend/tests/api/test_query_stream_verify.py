"""ADR-0073 方案 B — 串流事後 verify(純後端信號)單元 test(per CLAUDE.md §5.6 H6)。

覆蓋 `api.routes.query._verify_stream_retrieval_confidence`:
- grader 未 wire(None)→ 回 None,零告警(graceful)
- 高信心(≥ threshold)→ 回 confidence,不 emit low-confidence 告警
- 低信心(< threshold)→ 回 confidence + emit `stream_low_retrieval_confidence` warning
- grade 失敗(raise)→ 回 None + emit `stream_retrieval_verify_failed` warning(verify 是
  advisory,絕不可影響已串出的回應)

verify 純事後、不 re-synth/rewrite/re-retrieve,故只需 grade 一步的單元覆蓋。
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from unittest.mock import AsyncMock

import pytest
import structlog

from api.routes.query import _verify_stream_retrieval_confidence
from generation.crag import GradeResult
from retrieval.retrieval_engine import RetrievedChunk


@pytest.fixture
def _verify_log_capture(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Bridge structlog → stdlib logging so caplog sees the verify warnings
    (mirrors test_audit_log._structlog_capture). Reset on teardown so the global
    structlog config doesn't leak into sibling tests."""
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    caplog.set_level(logging.WARNING, logger="api.routes.query")
    yield caplog
    structlog.reset_defaults()


def _chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(
        score=0.8,
        fields={
            "chunk_id": chunk_id,
            "chunk_title": f"title-{chunk_id}",
            "chunk_text": f"body-{chunk_id}",
        },
    )


def _grade_result(confidence: float) -> GradeResult:
    return GradeResult(
        confidence=confidence,
        raw_text=str(confidence),
        input_tokens=50,
        output_tokens=5,
        latency_ms=100,
        deployment="gpt-5-4-mini",
    )


@pytest.mark.asyncio
async def test_verify_grader_unwired_returns_none() -> None:
    """grader 未 wire(None)→ 回 None,graceful 不 grade(verify 是 advisory)。"""
    result = await _verify_stream_retrieval_confidence(
        None, "查詢", [_chunk("c1")], threshold=0.70, kb_id="kb"
    )
    assert result is None


@pytest.mark.asyncio
async def test_verify_high_confidence_no_low_confidence_warning(
    _verify_log_capture: pytest.LogCaptureFixture,
) -> None:
    """高信心(≥ threshold)→ 回 confidence,不 emit low-confidence 告警。"""
    grader = AsyncMock()
    grader.grade = AsyncMock(return_value=_grade_result(0.85))

    result = await _verify_stream_retrieval_confidence(
        grader, "查詢", [_chunk("c1")], threshold=0.70, kb_id="kb"
    )

    assert result == 0.85
    grader.grade.assert_awaited_once()
    messages = [r.getMessage() for r in _verify_log_capture.records]
    assert not any("stream_low_retrieval_confidence" in m for m in messages)


@pytest.mark.asyncio
async def test_verify_low_confidence_emits_warning(
    _verify_log_capture: pytest.LogCaptureFixture,
) -> None:
    """低信心(< threshold)→ 回 confidence + emit `stream_low_retrieval_confidence`。"""
    grader = AsyncMock()
    grader.grade = AsyncMock(return_value=_grade_result(0.30))

    result = await _verify_stream_retrieval_confidence(
        grader, "查詢", [_chunk("c1")], threshold=0.70, kb_id="drive_user_manuals"
    )

    assert result == 0.30
    messages = [r.getMessage() for r in _verify_log_capture.records]
    low_conf = [m for m in messages if "stream_low_retrieval_confidence" in m]
    assert low_conf, "expected a stream_low_retrieval_confidence warning below threshold"
    assert any("drive_user_manuals" in m for m in low_conf)


@pytest.mark.asyncio
async def test_verify_grade_failure_returns_none_and_warns(
    _verify_log_capture: pytest.LogCaptureFixture,
) -> None:
    """grade 失敗(raise)→ 回 None + emit `stream_retrieval_verify_failed`;絕不 raise
    上去(verify 是 advisory,不可影響已串出的回應)。"""
    grader = AsyncMock()
    grader.grade = AsyncMock(side_effect=RuntimeError("azure 503"))

    result = await _verify_stream_retrieval_confidence(
        grader, "查詢", [_chunk("c1")], threshold=0.70, kb_id="kb"
    )

    assert result is None
    messages = [r.getMessage() for r in _verify_log_capture.records]
    assert any("stream_retrieval_verify_failed" in m for m in messages)

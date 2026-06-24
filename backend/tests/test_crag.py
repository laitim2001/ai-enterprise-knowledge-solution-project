"""CRAG L2 correction loop unit tests (W4 D1 F1; per CLAUDE.md §5.6 H6).

Coverage:
- Above-threshold: grader returns ≥ threshold → no correction triggered
- Below-threshold: grader returns < threshold → rewrite + re-retrieve + re-synth
- Confidence parser robustness (decimal / leading text / out-of-range / empty)
- Graceful fallback: rewrite failure / re-retrieve failure / re-synthesize
  failure → returns initial synthesis with fallback_used=True
- Empty chunks → confidence 0.0 short-circuit (no API call)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from generation.crag import (
    CragGrader,
    CragLoop,
    _parse_confidence,
)
from generation.synthesizer import SynthesisResult
from retrieval.retrieval_engine import RetrievalResult, RetrievedChunk

# ---------- helpers ----------------------------------------------------------


def _chunk(chunk_id: str, score: float = 0.8) -> RetrievedChunk:
    return RetrievedChunk(
        score=score,
        fields={
            "chunk_id": chunk_id,
            "chunk_title": f"title-{chunk_id}",
            "chunk_text": f"body-{chunk_id}",
        },
    )


def _synth(answer: str = "initial answer", citations: list[str] | None = None) -> SynthesisResult:
    return SynthesisResult(
        answer=answer,
        citation_ids=citations or [],
        refused=False,
        input_tokens=120,
        output_tokens=40,
        latency_ms=200,
        deployment="gpt-5-5",
    )


def _retrieval_result(chunks: list[RetrievedChunk] | None = None) -> RetrievalResult:
    chunks = chunks if chunks is not None else [_chunk("c1"), _chunk("c2")]
    return RetrievalResult(
        chunks=chunks,
        embed_latency_ms=10,
        search_latency_ms=20,
        rerank_latency_ms=0,
        total_latency_ms=30,
        reranked=False,
    )


@dataclass
class _MockCompletion:
    content: str
    prompt_tokens: int = 50
    completion_tokens: int = 5

    @property
    def choices(self) -> list[Any]:
        return [
            MagicMock(message=MagicMock(content=self.content)),
        ]

    @property
    def usage(self) -> Any:
        return MagicMock(prompt_tokens=self.prompt_tokens,
                         completion_tokens=self.completion_tokens)


def _grader_with_responses(*texts: str) -> CragGrader:
    """Build a CragGrader with a mocked Azure OpenAI client returning the given
    grader / rewrite outputs in order. Caller queues 1 string per call."""
    grader = CragGrader(
        endpoint="https://x.openai.azure.com",
        api_key="k",
        api_version="2025-04-01-preview",
        deployment="gpt-5-4-mini",
    )
    client = MagicMock()
    completions = [_MockCompletion(t) for t in texts]
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=completions)
    grader._client = client  # bypass __aenter__ for test
    return grader


# ---------- _parse_confidence ------------------------------------------------


def test_parse_confidence_simple_decimal() -> None:
    assert _parse_confidence("0.82") == pytest.approx(0.82)


def test_parse_confidence_leading_whitespace_and_newline() -> None:
    assert _parse_confidence("  0.55\n(some explanation)") == pytest.approx(0.55)


def test_parse_confidence_clamps_above_one() -> None:
    assert _parse_confidence("1.5") == 1.0


def test_parse_confidence_clamps_below_zero() -> None:
    assert _parse_confidence("-0.3") == 0.0


def test_parse_confidence_falls_back_to_first_float_in_text() -> None:
    assert _parse_confidence("Confidence: 0.42 because reason") == pytest.approx(0.42)


def test_parse_confidence_empty_returns_zero() -> None:
    assert _parse_confidence("") == 0.0


def test_parse_confidence_no_number_returns_zero() -> None:
    assert _parse_confidence("relevant") == 0.0


# ---------- CragGrader.grade -------------------------------------------------


@pytest.mark.asyncio
async def test_grade_empty_chunks_returns_zero_no_api_call() -> None:
    grader = _grader_with_responses()  # no responses queued
    result = await grader.grade("question?", chunks=[])
    assert result.confidence == 0.0
    assert result.input_tokens == 0
    assert result.raw_text == "(no chunks)"
    grader._client.chat.completions.create.assert_not_called()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_grade_parses_numeric_response() -> None:
    grader = _grader_with_responses("0.85")
    result = await grader.grade("question?", chunks=[_chunk("c1")])
    assert result.confidence == pytest.approx(0.85)
    assert result.input_tokens == 50
    assert result.output_tokens == 5


# ---------- CragLoop.refine: above-threshold = no-op -------------------------


@pytest.mark.asyncio
async def test_refine_skips_correction_when_confidence_above_threshold() -> None:
    grader = _grader_with_responses("0.90")  # only initial grade called
    engine = MagicMock()
    engine.retrieve = AsyncMock()
    synthesizer = MagicMock()
    synthesizer.synthesize = AsyncMock()

    loop = CragLoop(retrieval_engine=engine, synthesizer=synthesizer,
                    grader=grader, threshold=0.70)

    initial_result = _retrieval_result()
    initial_synth = _synth()
    outcome = await loop.refine("question?", initial_result, initial_synth, kb_id="drive_user_manuals")

    assert outcome.triggered is False
    assert outcome.iterations == 0
    assert outcome.confidence_before == pytest.approx(0.90)
    assert outcome.confidence_after is None
    assert outcome.synthesis is initial_synth
    assert outcome.chunks == initial_result.chunks
    assert outcome.fallback_used is False
    engine.retrieve.assert_not_called()
    synthesizer.synthesize.assert_not_called()


# ---------- CragLoop.refine: below-threshold = full correction ---------------


@pytest.mark.asyncio
async def test_refine_triggers_correction_when_confidence_below_threshold() -> None:
    # 3 grader calls: initial grade (0.40) → rewrite ("rewritten q") → grade2 (0.85)
    grader = _grader_with_responses("0.40", "rewritten question with more keywords", "0.85")

    new_chunks = [_chunk("nc1"), _chunk("nc2"), _chunk("nc3")]
    new_result = _retrieval_result(new_chunks)
    new_synth = _synth(answer="corrected answer [chunk-nc1]", citations=["nc1"])

    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=new_result)
    synthesizer = MagicMock()
    synthesizer.synthesize = AsyncMock(return_value=new_synth)

    loop = CragLoop(retrieval_engine=engine, synthesizer=synthesizer,
                    grader=grader, threshold=0.70, expanded_top_k=20)

    initial_result = _retrieval_result()
    initial_synth = _synth()
    outcome = await loop.refine("original question?", initial_result, initial_synth, kb_id="drive_user_manuals")

    assert outcome.triggered is True
    assert outcome.iterations == 1
    assert outcome.confidence_before == pytest.approx(0.40)
    assert outcome.confidence_after == pytest.approx(0.85)
    assert outcome.rewritten_query == "rewritten question with more keywords"
    assert outcome.synthesis is new_synth
    assert outcome.chunks == new_chunks
    assert outcome.fallback_used is False
    assert outcome.extra_synth_input_tokens == new_synth.input_tokens

    # ADR-0018: re-retrieve must propagate kb_id (multi-KB invariant per CragLoop.refine signature)
    engine.retrieve.assert_awaited_once_with(
        query="rewritten question with more keywords",
        kb_id="drive_user_manuals",
        top_k=20,
        user_principals=None,  # W90 P2.2 — refine threads ACL (None in this test)
    )
    # W32 F1.4 — CRAG re-synth path passes engine + kb_id kwargs for engine-fetch
    # citation expansion (h') per W32 plan §2 F1.4.
    synthesizer.synthesize.assert_awaited_once()
    call_args = synthesizer.synthesize.await_args
    assert call_args.args == ("rewritten question with more keywords", new_chunks)
    assert "engine" in call_args.kwargs
    assert call_args.kwargs.get("kb_id") == "drive_user_manuals"


# ---------- CragLoop.refine: graceful fallback paths -------------------------


@pytest.mark.asyncio
async def test_refine_fallback_when_resynth_fails() -> None:
    grader = _grader_with_responses("0.30", "rewritten q")  # grade + rewrite
    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=_retrieval_result([_chunk("nc1")]))
    synthesizer = MagicMock()
    synthesizer.synthesize = AsyncMock(side_effect=RuntimeError("openai 503"))

    loop = CragLoop(retrieval_engine=engine, synthesizer=synthesizer,
                    grader=grader, threshold=0.70)

    initial_result = _retrieval_result()
    initial_synth = _synth()
    outcome = await loop.refine("q?", initial_result, initial_synth, kb_id="drive_user_manuals")

    assert outcome.triggered is True
    assert outcome.iterations == 1
    assert outcome.fallback_used is True
    # Falls back to initial synth + initial chunks.
    assert outcome.synthesis is initial_synth
    assert outcome.chunks == initial_result.chunks
    assert outcome.confidence_before == pytest.approx(0.30)
    assert outcome.confidence_after is None
    assert outcome.rewritten_query == "rewritten q"
    assert any("re-synthesize" in msg for msg in outcome.error_messages)


@pytest.mark.asyncio
async def test_refine_fallback_when_grader_fails_outright() -> None:
    grader = CragGrader(
        endpoint="https://x.openai.azure.com",
        api_key="k",
        api_version="2025-04-01-preview",
        deployment="gpt-5-4-mini",
    )
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(side_effect=RuntimeError("grader 500"))
    grader._client = client

    engine = MagicMock()
    engine.retrieve = AsyncMock()
    synthesizer = MagicMock()
    synthesizer.synthesize = AsyncMock()

    loop = CragLoop(retrieval_engine=engine, synthesizer=synthesizer,
                    grader=grader, threshold=0.70)
    initial_result = _retrieval_result()
    initial_synth = _synth()
    outcome = await loop.refine("q?", initial_result, initial_synth, kb_id="drive_user_manuals")

    assert outcome.triggered is False  # no-op outcome since grader failed
    assert outcome.fallback_used is True
    assert outcome.synthesis is initial_synth
    assert outcome.chunks == initial_result.chunks
    engine.retrieve.assert_not_called()
    synthesizer.synthesize.assert_not_called()


@pytest.mark.asyncio
async def test_refine_fallback_when_rewrite_returns_empty() -> None:
    grader = _grader_with_responses("0.20", "   ")  # grade low + empty rewrite
    engine = MagicMock()
    engine.retrieve = AsyncMock()
    synthesizer = MagicMock()
    synthesizer.synthesize = AsyncMock()

    loop = CragLoop(retrieval_engine=engine, synthesizer=synthesizer,
                    grader=grader, threshold=0.70)
    initial_result = _retrieval_result()
    initial_synth = _synth()
    outcome = await loop.refine("q?", initial_result, initial_synth, kb_id="drive_user_manuals")

    assert outcome.triggered is True
    assert outcome.fallback_used is True
    assert outcome.synthesis is initial_synth
    assert "rewrite: empty" in outcome.error_messages
    engine.retrieve.assert_not_called()
    synthesizer.synthesize.assert_not_called()

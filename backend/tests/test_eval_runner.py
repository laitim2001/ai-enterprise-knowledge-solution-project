"""Eval runner unit tests (per CLAUDE.md §5.6 H6 — eval is critical pipeline).

Tests cover:
- Mode selection (strict vs keyword fallback per validated flag + placeholder detect)
- Recall@5 computation in both modes
- OOS query exclusion from aggregate
- Per-query error path
- Gate 1 threshold logic (≥ 80% pass)
- Report YAML serialization round-trip
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from eval.gates import gate1_recall_at_5
from eval.runner import EvalRunner, report_to_yaml
from retrieval.retrieval_engine import RetrievalResult, RetrievedChunk


def _hit(chunk_id: str, chunk_text: str, score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(score=score, fields={"chunk_id": chunk_id, "chunk_text": chunk_text})


def _retrieval_result(hits: list[RetrievedChunk]) -> RetrievalResult:
    return RetrievalResult(
        chunks=hits,
        embed_latency_ms=10,
        search_latency_ms=20,
        rerank_latency_ms=0,
        total_latency_ms=30,
        reranked=False,
    )


def _eval_set(queries: list[dict]) -> dict:
    return {
        "metadata": {"version": "test"},
        "queries": queries,
    }


def _write_yaml(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "eval-set.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


@pytest.mark.asyncio
async def test_keyword_mode_when_chunk_ids_are_placeholder(tmp_path: Path) -> None:
    """Default eval-set v0 has placeholder chunk_ids → keyword fallback mode applied."""
    queries = [
        {
            "query_id": "Q001",
            "query_text": "How to clear paper jam",
            "ground_truth": {
                "primary_chunk_ids": ["kb-drive_doc-M042_chunk-0007"],
                "acceptable_chunk_ids": ["kb-drive_doc-M042_chunk-0007"],
                "expected_answer_keywords": ["rear cover", "lever", "jam"],
                "expected_refusal": False,
            },
            "annotation": {"validated": False},
        },
    ]
    eval_path = _write_yaml(tmp_path, _eval_set(queries))

    engine = MagicMock()
    engine.retrieve = AsyncMock(
        return_value=_retrieval_result([
            _hit("kb-drive_user_manuals_doc-real-A_chunk-0001",
                 "Open the rear cover and pull the lever to clear the jam."),
        ]),
    )
    runner = EvalRunner(engine=engine, top_k=5)
    report = await runner.run(eval_path)

    assert report.queries_evaluated == 1
    assert report.per_query[0].mode == "keyword"
    assert report.per_query[0].recall_at_5 == 1.0  # all 3 keywords matched
    assert set(report.per_query[0].matched_keywords) == {"rear cover", "lever", "jam"}


@pytest.mark.asyncio
async def test_keyword_mode_partial_match(tmp_path: Path) -> None:
    queries = [
        {
            "query_id": "Q002",
            "query_text": "Replace toner",
            "ground_truth": {
                "expected_answer_keywords": ["toner", "cartridge", "release"],
                "expected_refusal": False,
            },
            "annotation": {"validated": False},
        },
    ]
    eval_path = _write_yaml(tmp_path, _eval_set(queries))

    engine = MagicMock()
    engine.retrieve = AsyncMock(
        return_value=_retrieval_result([_hit("c1", "Use the toner cartridge.")]),
    )
    runner = EvalRunner(engine=engine, top_k=5)
    report = await runner.run(eval_path)

    # 2 of 3 keywords matched ("release" missing)
    assert report.per_query[0].recall_at_5 == pytest.approx(2 / 3, rel=1e-3)
    assert set(report.per_query[0].matched_keywords) == {"toner", "cartridge"}


@pytest.mark.asyncio
async def test_strict_mode_when_validated_and_real_chunk_ids(tmp_path: Path) -> None:
    """Validated=True AND non-placeholder chunk_ids → strict mode."""
    queries = [
        {
            "query_id": "Q003",
            "query_text": "Q",
            "ground_truth": {
                "acceptable_chunk_ids": [
                    "kb-drive_user_manuals_doc-real-A_chunk-0001",
                    "kb-drive_user_manuals_doc-real-A_chunk-0002",
                ],
                "expected_answer_keywords": ["x"],
                "expected_refusal": False,
            },
            "annotation": {"validated": True},
        },
    ]
    eval_path = _write_yaml(tmp_path, _eval_set(queries))

    engine = MagicMock()
    engine.retrieve = AsyncMock(
        return_value=_retrieval_result([
            _hit("kb-drive_user_manuals_doc-real-A_chunk-0001", "..."),
            _hit("kb-drive_user_manuals_doc-real-B_chunk-0099", "..."),
        ]),
    )
    runner = EvalRunner(engine=engine, top_k=5)
    report = await runner.run(eval_path)

    assert report.per_query[0].mode == "strict"
    assert report.per_query[0].recall_at_5 == 0.5  # 1 of 2 acceptable matched
    assert report.aggregate_recall_at_5 == 0.5


@pytest.mark.asyncio
async def test_oos_queries_excluded_from_aggregate(tmp_path: Path) -> None:
    queries = [
        {
            "query_id": "Q-MAIN",
            "query_text": "main",
            "ground_truth": {
                "expected_answer_keywords": ["a"],
                "expected_refusal": False,
            },
            "annotation": {"validated": False},
        },
        {
            "query_id": "Q-OOS",
            "query_text": "out of scope",
            "ground_truth": {
                "expected_answer_keywords": [],
                "expected_refusal": True,  # OOS
            },
            "annotation": {"validated": False},
        },
    ]
    eval_path = _write_yaml(tmp_path, _eval_set(queries))

    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=_retrieval_result([_hit("c", "a a a")]))
    runner = EvalRunner(engine=engine, top_k=5)
    report = await runner.run(eval_path)

    assert report.total_queries == 2
    assert report.main_queries == 1
    assert report.oos_queries == 1
    # Aggregate over main only (OOS excluded)
    assert report.aggregate_recall_at_5 == 1.0


@pytest.mark.asyncio
async def test_per_query_error_recorded_excluded_from_aggregate(tmp_path: Path) -> None:
    queries = [
        {
            "query_id": "Q-OK",
            "query_text": "ok",
            "ground_truth": {"expected_answer_keywords": ["x"], "expected_refusal": False},
            "annotation": {"validated": False},
        },
        {
            "query_id": "Q-FAIL",
            "query_text": "fail",
            "ground_truth": {"expected_answer_keywords": ["y"], "expected_refusal": False},
            "annotation": {"validated": False},
        },
    ]
    eval_path = _write_yaml(tmp_path, _eval_set(queries))

    call_count = {"n": 0}

    async def _retrieve_side_effect(query: str, **kwargs) -> RetrievalResult:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _retrieval_result([_hit("c", "x x x")])
        raise RuntimeError("rate limited")

    engine = MagicMock()
    engine.retrieve = AsyncMock(side_effect=_retrieve_side_effect)
    runner = EvalRunner(engine=engine, top_k=5)
    report = await runner.run(eval_path)

    assert report.queries_errored == 1
    assert report.queries_evaluated == 1
    assert report.aggregate_recall_at_5 == 1.0  # only Q-OK counted
    fail_result = next(r for r in report.per_query if r.query_id == "Q-FAIL")
    assert fail_result.error is not None
    assert "RuntimeError" in fail_result.error


def test_gate1_pass_when_recall_above_threshold() -> None:
    from eval.runner import EvalReport
    report = EvalReport(
        eval_set="test", eval_set_version="v",
        started_at="", finished_at="",
        total_queries=10, main_queries=10, oos_queries=0,
        queries_evaluated=10, queries_errored=0,
        aggregate_recall_at_5=0.85,
        mode_breakdown={"strict": 10, "keyword": 0},
        avg_embed_latency_ms=10, avg_search_latency_ms=20,
        per_query=[],
    )
    decision = gate1_recall_at_5(report)
    assert decision.passed is True
    assert decision.threshold == 0.80
    assert decision.actual == 0.85


def test_gate1_fail_when_recall_below_threshold() -> None:
    from eval.runner import EvalReport
    report = EvalReport(
        eval_set="test", eval_set_version="v",
        started_at="", finished_at="",
        total_queries=10, main_queries=10, oos_queries=0,
        queries_evaluated=10, queries_errored=0,
        aggregate_recall_at_5=0.65,
        mode_breakdown={"strict": 0, "keyword": 10},
        avg_embed_latency_ms=10, avg_search_latency_ms=20,
        per_query=[],
    )
    decision = gate1_recall_at_5(report)
    assert decision.passed is False
    assert "FAIL" in decision.note
    assert "keyword-fallback" in decision.note  # mode breakdown noted


def test_gate1_at_exactly_threshold_passes() -> None:
    from eval.runner import EvalReport
    report = EvalReport(
        eval_set="t", eval_set_version="v",
        started_at="", finished_at="",
        total_queries=1, main_queries=1, oos_queries=0,
        queries_evaluated=1, queries_errored=0,
        aggregate_recall_at_5=0.80,
        mode_breakdown={"strict": 1, "keyword": 0},
        avg_embed_latency_ms=0, avg_search_latency_ms=0,
        per_query=[],
    )
    assert gate1_recall_at_5(report).passed is True


def test_gate1_note_warns_about_errored_queries() -> None:
    from eval.runner import EvalReport
    report = EvalReport(
        eval_set="t", eval_set_version="v",
        started_at="", finished_at="",
        total_queries=10, main_queries=10, oos_queries=0,
        queries_evaluated=8, queries_errored=2,
        aggregate_recall_at_5=0.85,
        mode_breakdown={"strict": 0, "keyword": 8},
        avg_embed_latency_ms=10, avg_search_latency_ms=20,
        per_query=[],
    )
    decision = gate1_recall_at_5(report)
    assert decision.passed is True
    assert "errored" in decision.note
    assert "R8" in decision.note  # mention to verify R8 cleared


@pytest.mark.asyncio
async def test_report_to_yaml_round_trips(tmp_path: Path) -> None:
    queries = [
        {
            "query_id": "Q1",
            "query_text": "Q",
            "ground_truth": {"expected_answer_keywords": ["x"], "expected_refusal": False},
            "annotation": {"validated": False},
        },
    ]
    eval_path = _write_yaml(tmp_path, _eval_set(queries))
    engine = MagicMock()
    engine.retrieve = AsyncMock(return_value=_retrieval_result([_hit("c", "x")]))
    runner = EvalRunner(engine=engine, top_k=5)
    report = await runner.run(eval_path)

    out_yaml = report_to_yaml(report)
    parsed = yaml.safe_load(out_yaml)
    assert parsed["aggregate"]["aggregate_recall_at_5"] == 1.0
    assert parsed["aggregate"]["main_queries"] == 1
    assert len(parsed["per_query"]) == 1
    assert parsed["per_query"][0]["query_id"] == "Q1"
    assert parsed["per_query"][0]["mode"] == "keyword"


@pytest.mark.asyncio
async def test_recall_zero_when_no_keywords_match(tmp_path: Path) -> None:
    queries = [
        {
            "query_id": "Q-NOMATCH",
            "query_text": "Q",
            "ground_truth": {
                "expected_answer_keywords": ["alpha", "beta"],
                "expected_refusal": False,
            },
            "annotation": {"validated": False},
        },
    ]
    eval_path = _write_yaml(tmp_path, _eval_set(queries))
    engine = MagicMock()
    engine.retrieve = AsyncMock(
        return_value=_retrieval_result([_hit("c", "completely unrelated text")]),
    )
    runner = EvalRunner(engine=engine, top_k=5)
    report = await runner.run(eval_path)

    assert report.per_query[0].recall_at_5 == 0.0
    assert report.per_query[0].matched_keywords == []

"""Controlled shared-question A/B harness unit tests (W54 — per CLAUDE.md §5.6 H6).

Covers:
- _parse_qa_keywords: tolerant JSON / markdown-fence parse + reject malformed
- build_section_passages: group by section_path, concat, truncate, drop empty/short
- generate_text_anchored_qa: seeded stable sample + drop keyword-less pairs
- to_keyword_eval_set_payload + EvalRunner: KEYWORD-mode recall path (R4 — proves
  validated=False entries score chunk_id-agnostically; zero new recall math)
- build_shared_eval_set: enumerate -> section passages -> generate -> frozen eval-set
- run_controlled_strategy_comparison: SAME frozen set scored across strategies + best
- make_qa_keyword_generator: graceful None without judge credential
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import yaml

from eval.controlled_comparison import (
    TextAnchoredQAPair,
    _parse_qa_keywords,
    build_section_passages,
    build_shared_eval_set,
    generate_text_anchored_qa,
    make_qa_keyword_generator,
    run_controlled_strategy_comparison,
    to_keyword_eval_set_payload,
)
from eval.runner import EvalReport, EvalRunner
from retrieval.retrieval_engine import RetrievalResult, RetrievedChunk


def _hit(chunk_id: str, chunk_text: str) -> RetrievedChunk:
    return RetrievedChunk(score=0.9, fields={"chunk_id": chunk_id, "chunk_text": chunk_text})


def _result(hits: list[RetrievedChunk]) -> RetrievalResult:
    return RetrievalResult(
        chunks=hits,
        embed_latency_ms=1,
        search_latency_ms=2,
        rerank_latency_ms=0,
        total_latency_ms=3,
        reranked=False,
    )


async def _gen_two_words(passage_text: str) -> tuple[str, list[str]] | None:
    """Stub judge: question references the passage; keywords = its first two words."""
    words = passage_text.split()
    if not words:
        return None
    return f"q::{passage_text[:15]}", words[:2]


# --------------------------------------------------------------------------- parse


def test_parse_qa_keywords_plain_json() -> None:
    assert _parse_qa_keywords('{"question": "What is X?", "keywords": ["alpha", "beta"]}') == (
        "What is X?",
        ["alpha", "beta"],
    )


def test_parse_qa_keywords_markdown_fence_and_dedupe() -> None:
    raw = '```json\n{"question": "Q?", "keywords": ["a", "b", "a"]}\n```'
    assert _parse_qa_keywords(raw) == ("Q?", ["a", "b"])  # fence stripped + dedupe


def test_parse_qa_keywords_rejects_malformed() -> None:
    assert _parse_qa_keywords(None) is None
    assert _parse_qa_keywords("") is None
    assert _parse_qa_keywords("not json at all") is None
    assert _parse_qa_keywords('{"question": "", "keywords": ["a"]}') is None  # empty question
    assert _parse_qa_keywords('{"question": "Q", "keywords": []}') is None  # no keyword
    assert _parse_qa_keywords('{"question": "Q"}') is None  # missing keywords
    assert _parse_qa_keywords('["not", "a", "dict"]') is None


# ------------------------------------------------------------------ section passages


def test_build_section_passages_groups_by_section() -> None:
    chunks = [
        {"chunk_id": "c1", "chunk_text": "Alpha first paragraph here.", "section_path": ["Intro"]},
        {"chunk_id": "c2", "chunk_text": "Alpha second paragraph here.", "section_path": ["Intro"]},
        {
            "chunk_id": "c3",
            "chunk_text": "Beta content paragraph here too.",
            "section_path": ["Setup", "Install"],
        },
    ]
    passages = build_section_passages(chunks, max_passage_chars=1000, min_passage_chars=5)
    assert len(passages) == 2
    assert passages[0]["section_path"] == ["Intro"]
    assert "Alpha first" in passages[0]["text"] and "Alpha second" in passages[0]["text"]
    assert passages[1]["section_path"] == ["Setup", "Install"]


def test_build_section_passages_drops_empty_short_and_truncates() -> None:
    chunks = [
        {"chunk_id": "c1", "chunk_text": "   ", "section_path": ["Empty"]},  # empty → dropped
        {"chunk_id": "c2", "chunk_text": "hi", "section_path": ["Tiny"]},  # < min → dropped
        {"chunk_id": "c3", "chunk_text": "x" * 50, "section_path": ["Big"]},
    ]
    passages = build_section_passages(chunks, max_passage_chars=10, min_passage_chars=5)
    assert len(passages) == 1
    assert passages[0]["section_path"] == ["Big"]
    assert len(passages[0]["text"]) == 10  # truncated to max_passage_chars


# ---------------------------------------------------------------- generate QA pairs


@pytest.mark.asyncio
async def test_generate_text_anchored_qa_seeded_stable() -> None:
    passages = [
        {"section_path": [f"S{i}"], "text": f"word{i} alpha beta gamma"} for i in range(1, 6)
    ]
    a = await generate_text_anchored_qa(passages, _gen_two_words, sample_size=3, seed=0)
    b = await generate_text_anchored_qa(passages, _gen_two_words, sample_size=3, seed=0)
    assert len(a) == 3
    # deterministic across runs + stable sort by section_path
    sects = ["/".join(p.source_section_path) for p in a]
    assert sects == sorted(sects)
    assert sects == ["/".join(p.source_section_path) for p in b]
    assert a[0].expected_keywords  # keywords propagate


@pytest.mark.asyncio
async def test_generate_text_anchored_qa_drops_keywordless() -> None:
    passages = [
        {"section_path": ["A"], "text": "alpha beta"},
        {"section_path": ["B"], "text": "gamma delta"},
    ]

    async def _gen(text: str) -> tuple[str, list[str]] | None:
        return None if "gamma" in text else ("q?", ["alpha"])

    pairs = await generate_text_anchored_qa(passages, _gen, sample_size=10, seed=0)
    assert [p.source_section_path for p in pairs] == [["A"]]


# ------------------------------------------------------- payload + EvalRunner (R4)


def test_to_keyword_eval_set_payload_shape() -> None:
    pairs = [
        TextAnchoredQAPair(
            question="Qa?",
            expected_keywords=["install path", "C drive"],
            source_section_path=["Setup"],
            source_text="...",
        )
    ]
    payload = to_keyword_eval_set_payload(pairs, kb_id="kb-y", seed=3)
    assert payload["metadata"]["version"] == "controlled-ab-W54-kb-y-seed3"
    assert payload["metadata"]["kind"] == "controlled_ab_keyword_recall"
    q0 = payload["queries"][0]
    assert q0["query_id"] == "CA001"
    assert q0["kb_id"] == "kb-y"
    # KEYWORD-mode invariants: NOT validated + no acceptable ids + keywords populated
    assert q0["annotation"]["validated"] is False
    assert q0["ground_truth"]["acceptable_chunk_ids"] == []
    assert q0["ground_truth"]["expected_answer_keywords"] == ["install path", "C drive"]


@pytest.mark.asyncio
async def test_keyword_eval_set_scores_keyword_mode(tmp_path: Path) -> None:
    """R4: payload entries drive EvalRunner's KEYWORD path (NOT strict), so the same
    frozen set scores any strategy chunk_id-agnostically."""
    pairs = [
        TextAnchoredQAPair(
            question="install?",
            expected_keywords=["install path", "C drive"],
            source_section_path=["Setup"],
            source_text="...",
        ),
        TextAnchoredQAPair(
            question="reset?",
            expected_keywords=["reset button", "hold 5s"],
            source_section_path=["Reset"],
            source_text="...",
        ),
    ]
    payload = to_keyword_eval_set_payload(pairs, kb_id="kb-y", seed=0)
    path = tmp_path / "shared.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")

    engine = MagicMock()

    async def _retrieve(query: str, **kwargs: object) -> RetrievalResult:
        if "install" in query:
            return _result([_hit("z1", "The install path is C drive root.")])  # both keywords
        return _result([_hit("z2", "Press the reset button now.")])  # 1 of 2 keywords

    engine.retrieve = AsyncMock(side_effect=_retrieve)

    report = await EvalRunner(engine, top_k=5, kb_id="kb-y").run(path)
    assert all(r.mode == "keyword" for r in report.per_query)  # NOT strict
    assert report.aggregate_recall_at_5 == pytest.approx((1.0 + 0.5) / 2, rel=1e-3)


# ---------------------------------------------------------------- build shared set


@pytest.mark.asyncio
async def test_build_shared_eval_set_round_trip(tmp_path: Path) -> None:
    """enumerate chunks → section passages → generate → frozen keyword eval-set YAML."""
    engine = MagicMock()
    engine.list_documents = AsyncMock(return_value=[{"doc_id": "doc-A"}])
    engine.list_chunks = AsyncMock(
        return_value=[
            {"chunk_id": "c1", "section_path": ["Intro"]},
            {"chunk_id": "c2", "section_path": ["Intro"]},
            {"chunk_id": "c3", "section_path": ["Setup"]},
        ]
    )
    engine.fetch_by_chunk_ids = AsyncMock(
        return_value={
            "c1": {"chunk_text": "alpha one paragraph with enough text to keep here."},
            "c2": {"chunk_text": "alpha two paragraph with enough text to keep here."},
            "c3": {"chunk_text": "beta three paragraph with enough body text content here."},
        }
    )
    out = tmp_path / "shared.yaml"
    count = await build_shared_eval_set(
        engine, "kb-z", generate_fn=_gen_two_words, output_path=out, sample_size=10, seed=0
    )
    # 2 sections (Intro merges c1+c2; Setup = c3) → 2 passages → 2 pairs
    assert count == 2
    parsed = yaml.safe_load(out.read_text(encoding="utf-8"))
    assert parsed["metadata"]["kind"] == "controlled_ab_keyword_recall"
    assert len(parsed["queries"]) == 2
    assert all(q["annotation"]["validated"] is False for q in parsed["queries"])
    assert all(q["ground_truth"]["expected_answer_keywords"] for q in parsed["queries"])


# ------------------------------------------------------- controlled comparison loop


def _report(recall: float, evaluated: int = 5, errored: int = 0) -> EvalReport:
    return EvalReport(
        eval_set="shared.yaml",
        eval_set_version="controlled-ab-W54-kb-z-seed0",
        started_at="t0",
        finished_at="t1",
        total_queries=evaluated,
        main_queries=evaluated,
        oos_queries=0,
        queries_evaluated=evaluated,
        queries_errored=errored,
        aggregate_recall_at_5=recall,
        mode_breakdown={"strict": 0, "keyword": evaluated},
        avg_embed_latency_ms=1.0,
        avg_search_latency_ms=2.0,
        per_query=[],
    )


@pytest.mark.asyncio
async def test_run_controlled_strategy_comparison_assembles_and_picks_best() -> None:
    recalls = {"layout_aware": 0.6, "heading_aware": 0.8}
    chunk_counts = {"layout_aware": 120, "heading_aware": 80}
    current = {"s": ""}

    async def _reindex(strategy: str) -> int:
        current["s"] = strategy
        return chunk_counts[strategy]

    async def _score() -> EvalReport:
        return _report(recalls[current["s"]])

    cmp = await run_controlled_strategy_comparison(
        "kb-z",
        ["layout_aware", "heading_aware"],
        eval_set_version="controlled-ab-W54-kb-z-seed0",
        shared_sample_size=5,
        reindex_with_strategy_fn=_reindex,
        score_fn=_score,
        top_k=5,
    )
    assert cmp.best_strategy == "heading_aware"  # higher keyword recall
    assert cmp.sample_size == 5  # shared frozen set size (controlled invariant)
    assert cmp.eval_set_version == "controlled-ab-W54-kb-z-seed0"
    assert [r.strategy for r in cmp.results] == ["layout_aware", "heading_aware"]
    assert cmp.results[0].chunk_count == 120
    assert cmp.results[1].recall_at_k == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_run_controlled_strategy_comparison_empty() -> None:
    async def _reindex(strategy: str) -> int:
        return 0

    async def _score() -> EvalReport:
        return _report(0.0)

    cmp = await run_controlled_strategy_comparison(
        "kb-z",
        [],
        eval_set_version="v",
        shared_sample_size=0,
        reindex_with_strategy_fn=_reindex,
        score_fn=_score,
    )
    assert cmp.best_strategy is None
    assert cmp.results == []


# ----------------------------------------------------------------- generator guard


def test_make_qa_keyword_generator_none_without_credential() -> None:
    settings = MagicMock()
    settings.azure_openai_api_key = ""
    assert make_qa_keyword_generator(settings) is None

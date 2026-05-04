"""stream_composer.compose_query_stream tests (W3 D3 F4)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from generation.stream_composer import compose_query_stream
from retrieval.retrieval_engine import RetrievalResult, RetrievedChunk


def _chunk(cid: str, **fields_override) -> RetrievedChunk:
    fields = {
        "chunk_id": cid,
        "doc_id": "doc-1",
        "doc_title": "Doc One",
        "chunk_title": "Section",
        "chunk_index": 0,
        "section_path": ["A"],
        "embedded_images_json": "[]",
    }
    fields.update(fields_override)
    return RetrievedChunk(score=0.5, fields=fields)


def _result(chunks: list[RetrievedChunk], reranked: bool = False) -> RetrievalResult:
    return RetrievalResult(
        chunks=chunks,
        embed_latency_ms=100,
        search_latency_ms=200,
        rerank_latency_ms=300 if reranked else 0,
        total_latency_ms=600 if reranked else 300,
        reranked=reranked,
    )


async def _async_iter(events: list[dict]) -> AsyncIterator[dict]:
    for e in events:
        yield e


@pytest.mark.asyncio
async def test_compose_passes_text_deltas_then_citations_then_done() -> None:
    chunks = [_chunk("c1"), _chunk("c2")]
    synth = _async_iter([
        {"type": "text-delta", "content": "Hello "},
        {"type": "text-delta", "content": "[chunk-c1]"},
        {
            "type": "result",
            "answer": "Hello [chunk-c1]",
            "citation_ids": ["c1"],
            "refused": False,
            "input_tokens": 100,
            "output_tokens": 20,
            "latency_ms": 800,
            "deployment": "gpt-5-5",
        },
    ])

    out = [e async for e in compose_query_stream(_result(chunks), synth)]

    types = [e["type"] for e in out]
    assert types == ["text-delta", "text-delta", "citation", "done"]
    assert out[2]["citation"]["chunk_id"] == "c1"
    done = out[3]
    assert done["model"] == "gpt-5-5"
    assert done["latency_ms"] == 300 + 800  # retrieval total + synth latency
    assert done["refused"] is False
    assert done["reranker_used"] == "off"


@pytest.mark.asyncio
async def test_compose_done_marks_reranker_used_when_reranked() -> None:
    chunks = [_chunk("c1")]
    synth = _async_iter([
        {
            "type": "result",
            "answer": "x",
            "citation_ids": [],
            "refused": False,
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": 100,
            "deployment": "gpt-5-5",
        },
    ])

    out = [e async for e in compose_query_stream(_result(chunks, reranked=True), synth)]

    done = out[-1]
    assert done["reranker_used"] == "cohere-v3.5"
    assert done["latency_ms"] == 600 + 100  # rerank-included retrieval total + synth


@pytest.mark.asyncio
async def test_compose_emits_citation_per_unique_cited_chunk_id() -> None:
    chunks = [_chunk("a"), _chunk("b"), _chunk("c")]
    synth = _async_iter([
        {
            "type": "result",
            "answer": "[chunk-a] [chunk-c] [chunk-a]",
            "citation_ids": ["a", "c"],  # ordered + dedup already done in synthesizer
            "refused": False,
            "input_tokens": 1, "output_tokens": 1, "latency_ms": 1,
            "deployment": "gpt-5-5",
        },
    ])

    out = [e async for e in compose_query_stream(_result(chunks), synth)]

    cit_events = [e for e in out if e["type"] == "citation"]
    assert [c["citation"]["chunk_id"] for c in cit_events] == ["a", "c"]


@pytest.mark.asyncio
async def test_compose_done_carries_refusal_flag_through() -> None:
    chunks = [_chunk("c1")]
    synth = _async_iter([
        {
            "type": "result",
            "answer": "(refusal)",
            "citation_ids": [],
            "refused": True,
            "input_tokens": 0, "output_tokens": 0, "latency_ms": 50,
            "deployment": "gpt-5-5",
        },
    ])

    out = [e async for e in compose_query_stream(_result(chunks), synth)]

    assert out[-1]["type"] == "done"
    assert out[-1]["refused"] is True


@pytest.mark.asyncio
async def test_compose_skips_unknown_citation_ids_silently() -> None:
    chunks = [_chunk("c1")]
    synth = _async_iter([
        {
            "type": "result",
            "answer": "[chunk-ghost]",
            "citation_ids": ["ghost"],  # not in retrieved
            "refused": False,
            "input_tokens": 0, "output_tokens": 0, "latency_ms": 1,
            "deployment": "gpt-5-5",
        },
    ])

    out = [e async for e in compose_query_stream(_result(chunks), synth)]

    citation_count = sum(1 for e in out if e["type"] == "citation")
    assert citation_count == 0  # hallucinated id silently skipped per F3 design
    assert out[-1]["type"] == "done"

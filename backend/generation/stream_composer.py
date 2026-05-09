"""Compose retrieval result + Synthesizer stream into final SSE event sequence (W3 D3 F4).

Pure-data composer (no I/O) so unit tests don't need TestClient. The
`/query/stream` route just iterates events and serializes via
`data: {json}\\n\\n` Vercel AI SDK SSE format.

Event sequence to client:
    text-delta  ← passthrough from Synthesizer
    text-delta
    ...
    citation    ← one per cited chunk after stream complete
    citation
    ...
    done        ← final frame (model / total_latency_ms / refused / reranker_used)
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from generation.citation_enrichment import build_citations
from retrieval.retrieval_engine import RetrievalResult


async def compose_query_stream(
    retrieval_result: RetrievalResult,
    synth_stream: AsyncIterator[dict],
) -> AsyncIterator[dict]:
    """Yield ordered SSE events:text-delta* citation* done.

    `synth_stream` is `Synthesizer.synthesize_stream(query, chunks)` directly.
    """
    async for event in synth_stream:
        if event.get("type") == "text-delta":
            yield event
            continue

        if event.get("type") == "result":
            citations = build_citations(
                event.get("citation_ids") or [],
                retrieval_result.chunks,
            )
            for cit in citations:
                yield {"type": "citation", "citation": cit.model_dump()}

            yield {
                "type": "done",
                "model": event.get("deployment", ""),
                "input_tokens": int(event.get("input_tokens", 0) or 0),
                "output_tokens": int(event.get("output_tokens", 0) or 0),
                "latency_ms": int(retrieval_result.total_latency_ms)
                + int(event.get("latency_ms", 0) or 0),
                "refused": bool(event.get("refused", False)),
                "reranker_used": "cohere-v4.0-pro" if retrieval_result.reranked else "off",  # ADR-0012
            }
            return  # result is terminal — no more events expected

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
    done        ← final frame (model / cost / total_latency_ms / refused / reranker_used)
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable

from api.schemas.query import Citation
from generation.citation_enrichment import build_citations
from observability.realtime_cost import estimate_query_cost
from retrieval.retrieval_engine import RetrievalResult


async def compose_query_stream(
    retrieval_result: RetrievalResult,
    synth_stream: AsyncIterator[dict],
    citation_post_process: Callable[[list[Citation]], Awaitable[list[Citation]]] | None = None,
) -> AsyncIterator[dict]:
    """Yield ordered SSE events:text-delta* citation* done.

    `synth_stream` is `Synthesizer.synthesize_stream(query, chunks)` directly.

    W25 F5 D1 — optional `citation_post_process` runs on the batch of
    citations once the synthesizer's `result` event delivers them, before
    they emit. Used by `/query/stream` to attach neighbour-chunk images
    via `attach_neighbour_images`. Pure-data semantics preserved when
    callback omitted (default None = original behaviour bit-identical).
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
            if citation_post_process is not None:
                citations = await citation_post_process(citations)
            for cit in citations:
                yield {"type": "citation", "citation": cit.model_dump()}

            deployment = event.get("deployment", "")
            input_tokens = int(event.get("input_tokens", 0) or 0)
            output_tokens = int(event.get("output_tokens", 0) or 0)
            yield {
                "type": "done",
                "model": deployment,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": estimate_query_cost(deployment, input_tokens, output_tokens),
                "latency_ms": int(retrieval_result.total_latency_ms)
                + int(event.get("latency_ms", 0) or 0),
                "refused": bool(event.get("refused", False)),
                "reranker_used": "cohere-v4.0-pro" if retrieval_result.reranked else "off",  # ADR-0012
            }
            return  # result is terminal — no more events expected

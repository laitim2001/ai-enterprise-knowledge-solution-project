"""GPT-5.5 synthesizer per architecture.md §3.1 + §3.2 (W3 D2 F2 + W3 D3 F4).

Wraps Azure OpenAI chat.completions with:
- Citation-required prompt (prompt_builder.SYSTEM_PROMPT)
- Citation marker parsing (`[chunk-{id}]` regex, ordered+deduped)
- tenacity retry on RateLimitError / APITimeoutError (synthesize() only;
  stream is not retried since partial output already delivered to client)
- structlog cost log per architecture.md §7 (input_tokens / output_tokens / latency)
- Refusal detection via REFUSAL_PHRASE substring match
- W3 D3: synthesize_stream() async generator yielding {text-delta, result}
  events for SSE consumption (Vercel AI SDK protocol via stream_composer)
"""

from __future__ import annotations

import re
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dataclasses import field as dataclasses_field

import structlog
from openai import APITimeoutError, AsyncAzureOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from generation.citation_expansion import ExpansionConfig, expand_citations
from generation.prompt_builder import REFUSAL_PHRASE, build_prompt
from observability.observe import observe_llm_async
from retrieval.retrieval_engine import RetrievalEngine, RetrievedChunk
from storage.settings import get_settings

logger = structlog.get_logger(__name__)

_CITATION_PATTERN = re.compile(r"\[chunk-([^\]\s]+)\]")


@dataclass(slots=True, frozen=True)
class SynthesisResult:
    """Synthesizer output — answer text + ordered cited chunk_ids + cost trace."""

    answer: str
    citation_ids: list[str]  # ordered unique chunk_ids cited in answer
    refused: bool
    input_tokens: int
    output_tokens: int
    latency_ms: int
    deployment: str
    # W32 F1.8 integration fix — neighbor chunks materialized by post-hoc
    # citation expansion (engine-fetched from full doc, NOT in top-K reranked).
    # Caller extends its retrieved_chunks list with this before build_citations
    # to avoid Rule 5「hallucinated」filter dropping W32-added citation_ids。
    expanded_neighbor_chunks: list[RetrievedChunk] = dataclasses_field(default_factory=list)


def extract_citation_ids(answer_text: str) -> list[str]:
    """Return ordered unique chunk_ids cited via `[chunk-{id}]` markers."""
    seen: list[str] = []
    for m in _CITATION_PATTERN.finditer(answer_text):
        cid = m.group(1).strip()
        if cid and cid not in seen:
            seen.append(cid)
    return seen


class Synthesizer:
    """GPT-5.5 chat-completion synthesizer with citation parsing + cost trace."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        timeout_s: float = 120.0,  # mirrors Settings.synthesizer_request_timeout_s (ADR-0053 / DD-7)
        temperature: float | None = None,
    ) -> None:
        # W5 D1 F1.7 fix: GPT-5 reasoning-style deployments(GPT-5.5 / GPT-5.4-mini /
        # GPT-5.5-pro)reject any `temperature` value other than the default 1 with
        # 400 "Unsupported value:'temperature' does not support 0.1 with this
        # model"。Default to None → omit the parameter entirely so OpenAI uses
        # model default。Older non-reasoning deployments(GPT-4 family)can still
        # pass an explicit value via the constructor for sampling control。
        self._client_kwargs = {
            "azure_endpoint": endpoint,
            "api_key": api_key,
            "api_version": api_version,
            "timeout": timeout_s,
        }
        self.deployment = deployment
        self.temperature = temperature
        self._client: AsyncAzureOpenAI | None = None

    def _completion_kwargs(self, **base: object) -> dict[str, object]:
        """Inject temperature only when the constructor received a non-None value."""
        kwargs = dict(base)
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        return kwargs

    async def __aenter__(self) -> Synthesizer:
        self._client = AsyncAzureOpenAI(**self._client_kwargs)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @observe_llm_async(
        name="synthesizer.synthesize",
        model_attr="deployment",
        input_tokens_attr="input_tokens",
        output_tokens_attr="output_tokens",
        extra_metadata_attrs=("latency_ms", "refused"),
    )
    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def synthesize(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        engine: RetrievalEngine | None = None,
        kb_id: str | None = None,
        effective_config: ExpansionConfig | None = None,
        detail_level: str = "concise",
    ) -> SynthesisResult:
        """W32 F1.1.a — `engine + kb_id` keyword-only optional params enable post-hoc
        citation expansion via async `engine.list_chunks` full-doc fetch (mirror W25 F5 D1
        attach_neighbour_images pattern); when either is None, expansion skipped (backward
        compat for legacy callers / tests per plan §2 F1.1.d).

        W43 F1.5 (ADR-0040) — `effective_config` carries the per-KB-resolved citation
        expansion knobs. When None (legacy callers / tests) the synthesizer falls back to
        the global `get_settings()` so behaviour is unchanged.
        """
        assert self._client is not None, "use 'async with' to manage Synthesizer lifecycle"

        # W34 F2.1.a — stage timing instrumentation (Karpathy §1.3 surgical;observability
        # only — no behavior change). Per W33 retro #2 latency profile breakdown:determine
        # if W33 +57-91% latency vs W32 is LLM emit / prompt token / engine-fetch dominant.
        synth_overall_start = time.perf_counter()

        # F2.1.b prompt-build sub-stage timing
        prompt_build_start = time.perf_counter()
        # W70 / ADR-0055 — marker knob read off the resolved config (EffectiveConfig
        # or Settings both carry it; the ExpansionConfig protocol annotation doesn't,
        # hence getattr). Legacy callers (effective_config=None) fall back to global.
        _marker_cfg = effective_config if effective_config is not None else get_settings()
        inline_image_markers = bool(getattr(_marker_cfg, "enable_inline_image_markers", False))
        prompt = build_prompt(
            query,
            chunks,
            dispatch_mode=get_settings().parent_doc_dispatch_mode,
            detail_level=detail_level,
            inline_image_markers=inline_image_markers,
        )
        prompt_build_latency_ms = int((time.perf_counter() - prompt_build_start) * 1000)

        # F2.1.c LLM chat completion sub-stage timing (existing `latency_ms` preserved
        # for backward compat with cost_dashboard.py / Langfuse trace parsing).
        start = time.perf_counter()
        completion = await self._client.chat.completions.create(
            **self._completion_kwargs(
                model=self.deployment,
                messages=prompt.messages,
            ),
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        choice = completion.choices[0] if completion.choices else None
        answer_text = (choice.message.content if choice and choice.message else "") or ""
        citation_ids = extract_citation_ids(answer_text)
        refused = REFUSAL_PHRASE in answer_text

        # W32 F1.4.a + F1.8 — post-hoc citation expansion via engine-fetch (h')。
        # Apply only when not refused AND engine + kb_id provided。`expand_citations`
        # returns 3-tuple including neighbor_chunks materialized from list_chunks
        # raw dicts — caller extends retrieved_chunks for build_citations to avoid
        # Rule 5「hallucinated」filter dropping W32-added citation_ids。
        expanded_neighbor_chunks: list[RetrievedChunk] = []
        # F2.1.d expand_citations overall sub-stage timing
        expand_citations_start = time.perf_counter()
        if not refused and engine is not None and kb_id is not None:
            answer_text, citation_ids, expanded_neighbor_chunks = await expand_citations(
                answer_text,
                citation_ids,
                chunks,
                engine=engine,
                kb_id=kb_id,
                settings=effective_config if effective_config is not None else get_settings(),
            )
        expand_citations_latency_ms = int((time.perf_counter() - expand_citations_start) * 1000)

        usage = getattr(completion, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

        synth_overall_latency_ms = int((time.perf_counter() - synth_overall_start) * 1000)

        logger.info(
            "synthesizer_call",
            deployment=self.deployment,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            citations_count=len(citation_ids),
            refused=refused,
            chunks_in=len(chunks),
            # W34 F2.1 stage timing fields (additive,backward compat preserved)
            synth_overall_latency_ms=synth_overall_latency_ms,
            synth_prompt_build_latency_ms=prompt_build_latency_ms,
            synth_llm_completion_latency_ms=latency_ms,
            synth_expand_citations_latency_ms=expand_citations_latency_ms,
        )

        return SynthesisResult(
            answer=answer_text,
            citation_ids=citation_ids,
            refused=refused,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            deployment=self.deployment,
            expanded_neighbor_chunks=expanded_neighbor_chunks,
        )

    async def synthesize_stream(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        *,
        engine: RetrievalEngine | None = None,
        kb_id: str | None = None,
        effective_config: ExpansionConfig | None = None,
        detail_level: str = "concise",
    ) -> AsyncIterator[dict]:
        """Stream chat.completions tokens; yield SSE events for stream_composer.

        Yielded event shapes:
            {"type": "text-delta", "content": str}
            {"type": "result", "answer": str, "citation_ids": list[str],
             "refused": bool, "input_tokens": int, "output_tokens": int,
             "latency_ms": int, "deployment": str}

        Stream events come during streaming; the single `result` event is
        emitted after the OpenAI stream completes (citation parse + refusal
        detection happen on the accumulated answer). Caller (stream_composer)
        translates `result` into per-citation events + final `done` frame.

        Cancellation: if the consumer aborts (e.g. client disconnect), the
        underlying OpenAI stream is closed in finally; the `result` event is
        skipped (no partial citation enrichment on cancel).
        """
        assert self._client is not None, "use 'async with' to manage Synthesizer lifecycle"

        # W70 / ADR-0055 — same marker-knob read as the non-stream path.
        _marker_cfg = effective_config if effective_config is not None else get_settings()
        prompt = build_prompt(
            query,
            chunks,
            dispatch_mode=get_settings().parent_doc_dispatch_mode,
            detail_level=detail_level,
            inline_image_markers=bool(getattr(_marker_cfg, "enable_inline_image_markers", False)),
        )
        start = time.perf_counter()
        accumulated = ""
        input_tokens = 0
        output_tokens = 0

        stream = await self._client.chat.completions.create(
            **self._completion_kwargs(
                model=self.deployment,
                messages=prompt.messages,
                stream=True,
                stream_options={"include_usage": True},
            ),
        )
        try:
            async for chunk in stream:
                usage = getattr(chunk, "usage", None)
                if usage is not None:
                    input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                    output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
                if not getattr(chunk, "choices", None):
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None) or ""
                if content:
                    accumulated += content
                    yield {"type": "text-delta", "content": content}
        finally:
            close = getattr(stream, "close", None)
            if close is not None:
                try:
                    await close()
                except Exception:  # noqa: BLE001 — best-effort cleanup
                    pass

        latency_ms = int((time.perf_counter() - start) * 1000)
        citation_ids = extract_citation_ids(accumulated)
        refused = REFUSAL_PHRASE in accumulated

        # W32 F1.4.b + F1.8 — post-hoc citation expansion via engine-fetch applied to
        # accumulated stream result. Text-delta partial frames already yielded before
        # expansion;final `result` event below carries expanded answer + citation_ids
        # + neighbor_chunks per plan §2 F1.1.b + F1.8.
        expanded_neighbor_chunks: list[RetrievedChunk] = []
        if not refused and engine is not None and kb_id is not None:
            accumulated, citation_ids, expanded_neighbor_chunks = await expand_citations(
                accumulated,
                citation_ids,
                chunks,
                engine=engine,
                kb_id=kb_id,
                settings=effective_config if effective_config is not None else get_settings(),
            )

        logger.info(
            "synthesizer_stream_complete",
            deployment=self.deployment,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            citations_count=len(citation_ids),
            refused=refused,
            chunks_in=len(chunks),
        )

        yield {
            "type": "result",
            "answer": accumulated,
            "citation_ids": citation_ids,
            "refused": refused,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "latency_ms": latency_ms,
            "deployment": self.deployment,
            "expanded_neighbor_chunks": expanded_neighbor_chunks,
        }

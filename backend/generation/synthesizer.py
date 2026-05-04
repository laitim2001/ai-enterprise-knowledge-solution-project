"""GPT-5.5 synthesizer per architecture.md §3.1 + §3.2 (W3 D2 F2).

Wraps Azure OpenAI chat.completions with:
- Citation-required prompt (prompt_builder.SYSTEM_PROMPT)
- Citation marker parsing (`[chunk-{id}]` regex, ordered+deduped)
- tenacity retry on RateLimitError / APITimeoutError
- structlog cost log per architecture.md §7 (input_tokens / output_tokens / latency)
- Refusal detection via REFUSAL_PHRASE substring match
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import structlog
from openai import AsyncAzureOpenAI, APITimeoutError, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from generation.prompt_builder import REFUSAL_PHRASE, build_prompt
from retrieval.retrieval_engine import RetrievedChunk

logger = structlog.get_logger(__name__)

_CITATION_PATTERN = re.compile(r"\[chunk-([^\]\s]+)\]")


@dataclass(slots=True, frozen=True)
class SynthesisResult:
    """Synthesizer output — answer text + ordered cited chunk_ids + cost trace."""

    answer: str
    citation_ids: list[str]   # ordered unique chunk_ids cited in answer
    refused: bool
    input_tokens: int
    output_tokens: int
    latency_ms: int
    deployment: str


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
        timeout_s: float = 30.0,
        temperature: float = 0.1,
    ) -> None:
        self._client_kwargs = {
            "azure_endpoint": endpoint,
            "api_key": api_key,
            "api_version": api_version,
            "timeout": timeout_s,
        }
        self.deployment = deployment
        self.temperature = temperature
        self._client: AsyncAzureOpenAI | None = None

    async def __aenter__(self) -> Synthesizer:
        self._client = AsyncAzureOpenAI(**self._client_kwargs)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

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
    ) -> SynthesisResult:
        assert self._client is not None, "use 'async with' to manage Synthesizer lifecycle"

        prompt = build_prompt(query, chunks)
        start = time.perf_counter()
        completion = await self._client.chat.completions.create(
            model=self.deployment,
            messages=prompt.messages,
            temperature=self.temperature,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        choice = completion.choices[0] if completion.choices else None
        answer_text = (choice.message.content if choice and choice.message else "") or ""
        citation_ids = extract_citation_ids(answer_text)
        refused = REFUSAL_PHRASE in answer_text

        usage = getattr(completion, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

        logger.info(
            "synthesizer_call",
            deployment=self.deployment,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            citations_count=len(citation_ids),
            refused=refused,
            chunks_in=len(chunks),
        )

        return SynthesisResult(
            answer=answer_text,
            citation_ids=citation_ids,
            refused=refused,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            deployment=self.deployment,
        )

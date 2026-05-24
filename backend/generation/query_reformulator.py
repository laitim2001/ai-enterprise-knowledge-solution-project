"""Query reformulator per ADR-0034 (W25 F3 D4 deliverable).

Generates `max_variants - 1` reformulated query variants alongside the
original query, used by `retrieval.result_fusion.fused_retrieve` for
RAG-fusion multi-variant retrieval. Reuses Azure OpenAI judge deployment
(gpt-5.4-mini) — same model class as CragGrader.rewrite_query but a
distinct orchestration shape (CRAG L2 = serial loop with re-grade;
ADR-0034 D4 = parallel fan-out with RRF fusion).

Lifecycle: async context manager — caller wires once at lifespan, reuses
the AsyncAzureOpenAI client across requests (matches CragGrader pattern).

Graceful fallback (per ADR-0034 §Consequences negative): any exception
during reformulation (API timeout, JSON parse failure, rate-limit) returns
`ReformulationResult(variants=[original], ...)` so the downstream
`fused_retrieve` degrades to single-query baseline without erroring out
the request. Latency cap via asyncio.wait_for enforces the P95 budget
allocation (default 3.0s leaves headroom for downstream retrieve+rerank+
synthesize under W25 plan §8 Q4 hard P95 < 5s envelope).

Per CLAUDE.md §5.2 H2: zero new dependency — reuses existing openai SDK
+ tenacity + observability decorators (no R8 trigger per ADR-0017).
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass

import structlog
from openai import APITimeoutError, AsyncAzureOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from observability.observe import observe_llm_async

logger = structlog.get_logger(__name__)


REFORMULATOR_SYSTEM_PROMPT = (
    "You are a query reformulation assistant. Given a user search query, "
    "generate {N} alternative phrasings that explore distinct semantic "
    "angles of the same information need. Variants should: "
    "(1) Use synonyms or domain-specific vocabulary likely to appear in "
    "source documents; "
    "(2) Decompose multi-part questions into focused sub-queries when the "
    "original is broad; "
    "(3) NOT change the user's intent or scope; "
    "(4) Be self-contained search queries (not conversational replies). "
    "Return STRICTLY JSON of the form "
    '{{"variants": ["variant 1", "variant 2", ...]}} '
    "with exactly {N} variants — no preamble, no explanation, no markdown."
)


# Defensive JSON extraction: LLM may wrap output in ```json fences despite
# instructions. The first `{...}` block in the output is parsed.
_JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


@dataclass(slots=True, frozen=True)
class ReformulationResult:
    """Output of one reformulate call.

    variants is always non-empty: at minimum [original_query] when reformulation
    fails / times out. Caller (fused_retrieve) iterates all variants for fan-out.
    """

    variants: list[str]              # [original, variant_1, variant_2, ...] OR [original] on fallback
    fallback_used: bool              # True iff returned [original] only due to error/timeout
    input_tokens: int                # 0 on fallback
    output_tokens: int               # 0 on fallback
    latency_ms: int                  # wall-clock including any retries
    deployment: str                  # surfaced for observe_llm_async cost attribution
    error_message: str | None = None  # populated when fallback_used=True


class QueryReformulator:
    """GPT-5.4-mini query reformulator (separate AsyncAzureOpenAI client).

    Reuses the same Azure OpenAI endpoint+key as Synthesizer + CragGrader
    but the judge deployment (gpt-5.4-mini) — cheap LLM for the variant
    generation use case. Lifecycle managed via async context manager —
    caller wires once at lifespan.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        max_variants: int = 3,
        latency_cap_s: float = 3.0,
        request_timeout_s: float = 5.0,
        temperature: float | None = None,
    ) -> None:
        # GPT-5.4-mini reasoning judge rejects non-default temperature (per
        # CragGrader W5 D1 F1.7 fix). Default to None → omit parameter so
        # OpenAI uses model default. Caller can override via constructor.
        self._client_kwargs = {
            "azure_endpoint": endpoint,
            "api_key": api_key,
            "api_version": api_version,
            "timeout": request_timeout_s,
        }
        self.deployment = deployment
        self.max_variants = max_variants
        self.latency_cap_s = latency_cap_s
        self.temperature = temperature
        self._client: AsyncAzureOpenAI | None = None

    def _completion_kwargs(self, **base: object) -> dict[str, object]:
        kwargs = dict(base)
        if self.temperature is not None:
            kwargs["temperature"] = self.temperature
        return kwargs

    async def __aenter__(self) -> QueryReformulator:
        self._client = AsyncAzureOpenAI(**self._client_kwargs)
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None

    @observe_llm_async(
        name="query_reformulator.reformulate",
        model_attr="deployment",
        input_tokens_attr="input_tokens",
        output_tokens_attr="output_tokens",
        extra_metadata_attrs=("latency_ms", "fallback_used"),
    )
    async def reformulate(self, query: str) -> ReformulationResult:
        """Generate up to `max_variants` query variants (incl. original).

        Returns [original] on empty/blank input. Returns [original] with
        fallback_used=True on any LLM error / JSON parse failure / latency
        cap exceeded — preserves downstream pipeline robustness per
        ADR-0034 §Consequences negative.
        """
        original = query.strip()
        if not original:
            return ReformulationResult(
                variants=[],
                fallback_used=False,
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                deployment=self.deployment,
            )

        if self.max_variants <= 1:
            # Single-variant fan-out is degenerate (no fusion benefit); return
            # original-only without spending an LLM call.
            return ReformulationResult(
                variants=[original],
                fallback_used=False,
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
                deployment=self.deployment,
            )

        start = time.perf_counter()
        try:
            variants = await asyncio.wait_for(
                self._call_llm(original),
                timeout=self.latency_cap_s,
            )
        except TimeoutError:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(
                "query_reformulator_timeout",
                query_chars=len(original),
                cap_s=self.latency_cap_s,
                latency_ms=latency_ms,
            )
            return ReformulationResult(
                variants=[original],
                fallback_used=True,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                deployment=self.deployment,
                error_message=f"reformulation timeout after {self.latency_cap_s}s",
            )
        except Exception as exc:  # noqa: BLE001 — graceful fallback per ADR-0034
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.warning(
                "query_reformulator_failed_using_original",
                error=f"{type(exc).__name__}: {exc}",
                latency_ms=latency_ms,
            )
            return ReformulationResult(
                variants=[original],
                fallback_used=True,
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                deployment=self.deployment,
                error_message=f"{type(exc).__name__}: {exc}",
            )

        result_variants, input_tokens, output_tokens = variants
        latency_ms = int((time.perf_counter() - start) * 1000)

        # Always prepend original to the fan-out set (RAG-fusion needs the
        # literal user query as one variant; reformulator only generates
        # alternative phrasings).
        all_variants = [original, *result_variants]

        logger.info(
            "query_reformulator_complete",
            query_chars=len(original),
            variant_count=len(all_variants),
            latency_ms=latency_ms,
        )

        return ReformulationResult(
            variants=all_variants,
            fallback_used=False,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            deployment=self.deployment,
        )

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        stop=stop_after_attempt(2),  # one retry — total ≤ 2 attempts inside latency cap
        wait=wait_exponential(multiplier=1, min=0.5, max=2),
        reraise=True,
    )
    async def _call_llm(self, original: str) -> tuple[list[str], int, int]:
        """Inner LLM call: returns (variants_excluding_original, input_tokens, output_tokens).

        Raises on API error (caller catches to enter fallback path) OR on
        JSON parse failure (treated same — graceful fallback).
        """
        assert self._client is not None, "use 'async with' to manage QueryReformulator lifecycle"

        # We ask the LLM for `max_variants - 1` variants because the caller
        # prepends the original — RAG-fusion total fan-out width = max_variants.
        n_alt = self.max_variants - 1
        system_msg = REFORMULATOR_SYSTEM_PROMPT.format(N=n_alt)

        completion = await self._client.chat.completions.create(
            **self._completion_kwargs(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f'Reformulate this query into {n_alt} alternative phrasings: "{original}"'},
                ],
            ),
        )

        choice = completion.choices[0] if completion.choices else None
        raw_text = (choice.message.content if choice and choice.message else "") or ""
        variants = _parse_variants(raw_text, expected_count=n_alt)

        usage = getattr(completion, "usage", None)
        input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)

        return variants, input_tokens, output_tokens


def _parse_variants(raw_text: str, expected_count: int) -> list[str]:
    """Extract variants list from LLM JSON output. Lenient JSON block detection.

    Raises ValueError on parse failure (caller catches → fallback). Returns
    up to `expected_count` non-empty stripped variants — if LLM returns
    fewer (rare), we accept what we get without padding.
    """
    match = _JSON_BLOCK_PATTERN.search(raw_text)
    if not match:
        raise ValueError(f"no JSON block found in reformulator output: {raw_text!r}")

    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(f"reformulator output is not valid JSON: {exc}") from exc

    if not isinstance(parsed, dict) or "variants" not in parsed:
        raise ValueError(f'reformulator JSON missing "variants" key: {parsed!r}')

    variants_raw = parsed["variants"]
    if not isinstance(variants_raw, list):
        raise ValueError(f"reformulator variants is not a list: {variants_raw!r}")

    # Strip + filter empties + dedupe while preserving order; cap at expected_count.
    seen: set[str] = set()
    cleaned: list[str] = []
    for v in variants_raw:
        if not isinstance(v, str):
            continue
        stripped = v.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        cleaned.append(stripped)
        if len(cleaned) >= expected_count:
            break

    if not cleaned:
        raise ValueError("reformulator returned zero usable variants after cleaning")

    return cleaned

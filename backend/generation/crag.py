"""CRAG L2 correction loop per architecture.md §3.5 (W4 D1 F1).

Pipeline (post initial retrieve + synthesize):
    grader.grade(query, chunks) → confidence ∈ [0, 1]
    if confidence ≥ threshold: emit CragOutcome(triggered=False) — no-op
    else:                       grader.rewrite_query(query, chunks) →
                                engine.retrieve(rewritten, top_k=expanded) →
                                synthesizer.synthesize(rewritten, new_chunks) →
                                emit CragOutcome(triggered=True, iterations=1)

L2 baseline (max 1 correction iteration); L3 routing deferred to W5
conditional on Gate 2 全 pass per architecture.md §6.1 W5 row.

Graceful fallback: any grader / rewrite / re-synthesize exception logs the
error and returns the initial synthesis (`fallback_used=True`). Initial
synthesis is never re-executed by CRAG — caller must always do the first
retrieve+synthesize before invoking `CragLoop.refine()`.

Cost trace via structlog `crag_loop` event (input/output tokens for grader +
rewrite + cumulative across initial+corrected synth; threshold; triggered
flag; final confidence).

Wired into `/query` non-stream path only — stream path is L3-only per
architecture.md §3.5 (correction loop would require buffering tokens which
breaks SSE token-by-token UX).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

import structlog
from openai import APITimeoutError, AsyncAzureOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from generation.synthesizer import SynthesisResult, Synthesizer
from retrieval.retrieval_engine import RetrievalEngine, RetrievalResult, RetrievedChunk

logger = structlog.get_logger(__name__)

GRADER_SYSTEM_PROMPT = (
    "You are a retrieval-quality grader. Given a user question and a set of "
    "retrieved document chunks, assess whether the chunks contain enough "
    "information to answer the question. Output STRICTLY a single floating-point "
    "number between 0.0 and 1.0 on the first line — nothing else. "
    "0.0 = chunks are entirely irrelevant; 1.0 = chunks fully answer the question. "
    "Do not output explanation, JSON, or any other text — only the number."
)

REWRITE_SYSTEM_PROMPT = (
    "You are a query reformulation assistant. Given a user question and the "
    "retrieved chunks that were judged insufficient, output a single rewritten "
    "query that is more likely to retrieve the missing information. Preserve "
    "the user's intent and terminology where possible; expand abbreviations, "
    "add synonyms, and split compound questions only if it helps retrieval. "
    "Output STRICTLY the rewritten query as a single line — no preamble, no "
    "explanation, no quotes, no formatting."
)

# Allow optional whitespace, optional sign, decimal or integer, then end-of-line.
_CONFIDENCE_PATTERN = re.compile(r"^\s*([+-]?\d*\.?\d+)\s*$")


@dataclass(slots=True, frozen=True)
class GradeResult:
    confidence: float
    raw_text: str  # what the grader returned (for trace if parse fails)
    input_tokens: int
    output_tokens: int
    latency_ms: int


@dataclass(slots=True, frozen=True)
class RewriteResult:
    rewritten_query: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


@dataclass(slots=True)
class CragOutcome:
    """Final state after CRAG refine — initial OR corrected synthesis."""

    synthesis: SynthesisResult     # may be initial OR post-correction
    chunks: list[RetrievedChunk]   # final chunks used for synthesis
    triggered: bool                # True iff confidence < threshold
    iterations: int                # 0 if not triggered, 1 if corrected
    confidence_before: float       # initial grader score
    confidence_after: float | None  # post-correction grader score (None if not triggered)
    rewritten_query: str | None    # rewritten query (None if not triggered)
    fallback_used: bool            # True iff correction failed and we returned initial
    grader_input_tokens: int
    grader_output_tokens: int
    rewrite_input_tokens: int
    rewrite_output_tokens: int
    extra_synth_input_tokens: int   # tokens used by corrected synthesis (0 if not triggered)
    extra_synth_output_tokens: int
    extra_retrieval_latency_ms: int  # latency of re-retrieve (0 if not triggered)
    crag_latency_ms: int            # total latency added by CRAG (grade + rewrite + re-fetch + re-synth)
    error_messages: list[str] = field(default_factory=list)


class CragGrader:
    """GPT-5.4-mini grader + query rewriter (separate AsyncAzureOpenAI client).

    Reuses the same Azure OpenAI endpoint+key as Synthesizer but a different
    deployment (gpt-5.4-mini judge per Settings.azure_openai_deployment_llm_judge).
    Lifecycle managed via async context manager — caller wires once at lifespan.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        api_version: str,
        deployment: str,
        timeout_s: float = 15.0,
        temperature: float = 0.0,
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

    async def __aenter__(self) -> CragGrader:
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
    async def grade(self, query: str, chunks: list[RetrievedChunk]) -> GradeResult:
        """Score chunk relevance ∈ [0, 1]. Returns 0.0 if chunks empty."""
        if not chunks:
            return GradeResult(confidence=0.0, raw_text="(no chunks)",
                               input_tokens=0, output_tokens=0, latency_ms=0)

        assert self._client is not None, "use 'async with' to manage CragGrader lifecycle"
        user_msg = _build_grader_user_message(query, chunks)
        start = time.perf_counter()
        completion = await self._client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": GRADER_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=self.temperature,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        choice = completion.choices[0] if completion.choices else None
        raw_text = (choice.message.content if choice and choice.message else "") or ""
        confidence = _parse_confidence(raw_text)

        usage = getattr(completion, "usage", None)
        return GradeResult(
            confidence=confidence,
            raw_text=raw_text,
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            latency_ms=latency_ms,
        )

    @retry(
        retry=retry_if_exception_type((RateLimitError, APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    async def rewrite_query(self, query: str, chunks: list[RetrievedChunk]) -> RewriteResult:
        """Generate a reformulated query for re-retrieval. Empty input → empty output."""
        if not query.strip():
            return RewriteResult(rewritten_query="", input_tokens=0,
                                 output_tokens=0, latency_ms=0)

        assert self._client is not None, "use 'async with' to manage CragGrader lifecycle"
        user_msg = _build_rewrite_user_message(query, chunks)
        start = time.perf_counter()
        completion = await self._client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=self.temperature,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)

        choice = completion.choices[0] if completion.choices else None
        raw_text = (choice.message.content if choice and choice.message else "") or ""
        rewritten = raw_text.strip()
        # Defensive: if grader returned multi-line, take first non-empty line.
        if "\n" in rewritten:
            for line in rewritten.split("\n"):
                if line.strip():
                    rewritten = line.strip()
                    break

        usage = getattr(completion, "usage", None)
        return RewriteResult(
            rewritten_query=rewritten,
            input_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            latency_ms=latency_ms,
        )


class CragLoop:
    """Orchestrate L2 correction: grade → maybe rewrite + re-fetch + re-synth."""

    def __init__(
        self,
        retrieval_engine: RetrievalEngine,
        synthesizer: Synthesizer,
        grader: CragGrader,
        threshold: float = 0.70,
        max_corrections: int = 1,
        expanded_top_k: int = 20,
    ) -> None:
        self._engine = retrieval_engine
        self._synthesizer = synthesizer
        self._grader = grader
        self._threshold = threshold
        self._max_corrections = max_corrections
        self._expanded_top_k = expanded_top_k

    async def refine(
        self,
        query: str,
        initial_result: RetrievalResult,
        initial_synth: SynthesisResult,
    ) -> CragOutcome:
        """Apply L2 correction if initial chunks insufficient; else return initial."""
        crag_start = time.perf_counter()

        try:
            grade = await self._grader.grade(query, initial_result.chunks)
        except Exception as exc:  # noqa: BLE001 — fall through to no-op outcome
            logger.warning("crag_grader_error", error=f"{type(exc).__name__}: {exc}")
            return _no_op_outcome(initial_synth, initial_result.chunks,
                                  errors=[f"grader: {exc}"],
                                  crag_latency_ms=_elapsed_ms(crag_start))

        if grade.confidence >= self._threshold or self._max_corrections <= 0:
            outcome = CragOutcome(
                synthesis=initial_synth,
                chunks=initial_result.chunks,
                triggered=False,
                iterations=0,
                confidence_before=grade.confidence,
                confidence_after=None,
                rewritten_query=None,
                fallback_used=False,
                grader_input_tokens=grade.input_tokens,
                grader_output_tokens=grade.output_tokens,
                rewrite_input_tokens=0,
                rewrite_output_tokens=0,
                extra_synth_input_tokens=0,
                extra_synth_output_tokens=0,
                extra_retrieval_latency_ms=0,
                crag_latency_ms=_elapsed_ms(crag_start),
            )
            _log_outcome(outcome, threshold=self._threshold)
            return outcome

        # Below threshold → trigger correction.
        errors: list[str] = []
        try:
            rewrite = await self._grader.rewrite_query(query, initial_result.chunks)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"rewrite: {exc}")
            logger.warning("crag_rewrite_error", error=f"{type(exc).__name__}: {exc}")
            return _fallback_outcome(initial_synth, initial_result.chunks,
                                     grade=grade, errors=errors,
                                     crag_latency_ms=_elapsed_ms(crag_start))

        if not rewrite.rewritten_query:
            errors.append("rewrite: empty")
            return _fallback_outcome(initial_synth, initial_result.chunks,
                                     grade=grade, errors=errors,
                                     rewrite=rewrite,
                                     crag_latency_ms=_elapsed_ms(crag_start))

        try:
            new_result = await self._engine.retrieve(
                query=rewrite.rewritten_query,
                top_k=self._expanded_top_k,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"re-retrieve: {exc}")
            logger.warning("crag_retrieve_error", error=f"{type(exc).__name__}: {exc}")
            return _fallback_outcome(initial_synth, initial_result.chunks,
                                     grade=grade, errors=errors,
                                     rewrite=rewrite,
                                     crag_latency_ms=_elapsed_ms(crag_start))

        try:
            new_synth = await self._synthesizer.synthesize(
                rewrite.rewritten_query, new_result.chunks,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"re-synthesize: {exc}")
            logger.warning("crag_resynth_error", error=f"{type(exc).__name__}: {exc}")
            return _fallback_outcome(initial_synth, initial_result.chunks,
                                     grade=grade, errors=errors,
                                     rewrite=rewrite,
                                     extra_retrieval_latency_ms=new_result.total_latency_ms,
                                     crag_latency_ms=_elapsed_ms(crag_start))

        # Optional second-pass grade for confidence_after — non-fatal if it fails.
        confidence_after: float | None = None
        try:
            grade2 = await self._grader.grade(rewrite.rewritten_query, new_result.chunks)
            confidence_after = grade2.confidence
        except Exception as exc:  # noqa: BLE001
            logger.warning("crag_grader2_error", error=f"{type(exc).__name__}: {exc}")
            errors.append(f"grader2: {exc}")
            grade2 = None

        outcome = CragOutcome(
            synthesis=new_synth,
            chunks=new_result.chunks,
            triggered=True,
            iterations=1,
            confidence_before=grade.confidence,
            confidence_after=confidence_after,
            rewritten_query=rewrite.rewritten_query,
            fallback_used=False,
            grader_input_tokens=grade.input_tokens + (grade2.input_tokens if grade2 else 0),
            grader_output_tokens=grade.output_tokens + (grade2.output_tokens if grade2 else 0),
            rewrite_input_tokens=rewrite.input_tokens,
            rewrite_output_tokens=rewrite.output_tokens,
            extra_synth_input_tokens=new_synth.input_tokens,
            extra_synth_output_tokens=new_synth.output_tokens,
            extra_retrieval_latency_ms=new_result.total_latency_ms,
            crag_latency_ms=_elapsed_ms(crag_start),
            error_messages=errors,
        )
        _log_outcome(outcome, threshold=self._threshold)
        return outcome


def _build_grader_user_message(query: str, chunks: list[RetrievedChunk]) -> str:
    chunk_blocks = "\n\n".join(
        f"[chunk-{c.fields.get('chunk_id', '')}]\n"
        f"{c.fields.get('chunk_title', '')}\n"
        f"{c.fields.get('chunk_text', '')}"
        for c in chunks
    )
    return f"Question:\n{query}\n\nRetrieved chunks:\n{chunk_blocks}"


def _build_rewrite_user_message(query: str, chunks: list[RetrievedChunk]) -> str:
    titles = ", ".join(
        str(c.fields.get("chunk_title", "")) for c in chunks if c.fields.get("chunk_title")
    )
    return (
        f"Original question:\n{query}\n\n"
        f"Retrieved chunk titles (deemed insufficient): {titles or '(none)'}\n\n"
        "Rewrite the question to retrieve the missing information."
    )


def _parse_confidence(raw_text: str) -> float:
    """Parse grader output to confidence ∈ [0, 1]; return 0.0 on parse failure."""
    if not raw_text:
        return 0.0
    # Try first line first.
    first_line = raw_text.strip().split("\n", 1)[0].strip()
    m = _CONFIDENCE_PATTERN.match(first_line)
    if m is None:
        # Fallback: any float in raw text.
        m = re.search(r"([+-]?\d*\.?\d+)", raw_text)
    if m is None:
        return 0.0
    try:
        v = float(m.group(1))
    except ValueError:
        return 0.0
    return max(0.0, min(1.0, v))


def _no_op_outcome(
    initial_synth: SynthesisResult,
    initial_chunks: list[RetrievedChunk],
    errors: list[str],
    crag_latency_ms: int,
) -> CragOutcome:
    """When grader fails outright — return initial synth, do not trigger correction."""
    return CragOutcome(
        synthesis=initial_synth,
        chunks=initial_chunks,
        triggered=False,
        iterations=0,
        confidence_before=0.0,
        confidence_after=None,
        rewritten_query=None,
        fallback_used=True,
        grader_input_tokens=0,
        grader_output_tokens=0,
        rewrite_input_tokens=0,
        rewrite_output_tokens=0,
        extra_synth_input_tokens=0,
        extra_synth_output_tokens=0,
        extra_retrieval_latency_ms=0,
        crag_latency_ms=crag_latency_ms,
        error_messages=errors,
    )


def _fallback_outcome(
    initial_synth: SynthesisResult,
    initial_chunks: list[RetrievedChunk],
    grade: GradeResult,
    errors: list[str],
    rewrite: RewriteResult | None = None,
    extra_retrieval_latency_ms: int = 0,
    crag_latency_ms: int = 0,
) -> CragOutcome:
    """Correction was attempted but a stage failed — return initial with metadata."""
    return CragOutcome(
        synthesis=initial_synth,
        chunks=initial_chunks,
        triggered=True,
        iterations=1,
        confidence_before=grade.confidence,
        confidence_after=None,
        rewritten_query=rewrite.rewritten_query if rewrite else None,
        fallback_used=True,
        grader_input_tokens=grade.input_tokens,
        grader_output_tokens=grade.output_tokens,
        rewrite_input_tokens=rewrite.input_tokens if rewrite else 0,
        rewrite_output_tokens=rewrite.output_tokens if rewrite else 0,
        extra_synth_input_tokens=0,
        extra_synth_output_tokens=0,
        extra_retrieval_latency_ms=extra_retrieval_latency_ms,
        crag_latency_ms=crag_latency_ms,
        error_messages=errors,
    )


def _log_outcome(outcome: CragOutcome, threshold: float) -> None:
    logger.info(
        "crag_loop",
        threshold=threshold,
        triggered=outcome.triggered,
        iterations=outcome.iterations,
        confidence_before=outcome.confidence_before,
        confidence_after=outcome.confidence_after,
        fallback_used=outcome.fallback_used,
        grader_input_tokens=outcome.grader_input_tokens,
        grader_output_tokens=outcome.grader_output_tokens,
        rewrite_input_tokens=outcome.rewrite_input_tokens,
        rewrite_output_tokens=outcome.rewrite_output_tokens,
        extra_synth_input_tokens=outcome.extra_synth_input_tokens,
        extra_synth_output_tokens=outcome.extra_synth_output_tokens,
        crag_latency_ms=outcome.crag_latency_ms,
        errors=outcome.error_messages or None,
    )


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)

"""Azure-judge-bound RAGAs evaluator factory (W17 F3 — extracted from
`scripts/run_ragas_eval.py` so `/eval/run` + `/eval/shootout` can reuse it).

`make_ragas_evaluator(settings)` returns a per-sample callable matching the
`RagasRunner` evaluator contract — takes a `RagasQuerySample`, returns a dict of
the 4 RAGAs metric scores + token placeholders. Returns **None** when the Azure
OpenAI judge credential is absent (local dev / CI) → callers fall back to the
Recall@5-only `EvalReport` (per the W16-style PARTIAL-PASS pattern).

`ragas` 0.4.3 quirks handled here (originally fixed W5 D1 Path A / W5 D4 Bug I):
- the `collections` metrics are now MODULES not classes → import the classes
  (`Faithfulness` / `AnswerRelevancy` / `ContextPrecision` / `ContextRecall`)
  directly; per-metric `ascore` signatures diverge.
- ragas internally calls `agenerate()` → needs an `AsyncAzureOpenAI` client.
- GPT-5 reasoning judges reject `temperature`/`max_tokens`/`logprobs` → the
  `patch_for_gpt5` shim translates `max_tokens → max_completion_tokens` (floor
  4096 so faithfulness statement-extraction JSON doesn't truncate) and drops
  the unsupported params, while preserving `AsyncAzureOpenAI` type identity so
  `instructor.from_openai`'s `isinstance` check still passes.
- `RagasRunner.evaluate` is sync (13 unit tests use sync stubs) → the async
  `ascore` calls are bridged via `asyncio.run` in a worker thread.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from collections.abc import Callable

import structlog

from eval.ragas_runner import RagasQuerySample
from storage.settings import Settings

logger = structlog.get_logger(__name__)

_MIN_MAX_COMPLETION_TOKENS = 4096  # W5 D4 Bug I — faithfulness statement-extraction headroom
_GPT5_DROP_PARAMS = ("temperature", "logprobs", "top_logprobs")


def patch_for_gpt5(client) -> None:
    """Monkey-patch `chat.completions.create` on a live `AsyncAzureOpenAI` client
    to translate GPT-5-reasoning-incompatible params before forwarding.

    `client` is kept untyped on purpose — the patch mutates the live instance so
    `instructor.from_openai`'s `isinstance(client, openai.AsyncOpenAI)` check (in
    ragas 0.4.3's LLM factory) keeps matching. `max_tokens` →
    `max_completion_tokens` (floor `_MIN_MAX_COMPLETION_TOKENS`); `temperature` /
    `logprobs` / `top_logprobs` → dropped.
    """
    inner_create = client.chat.completions.create

    async def patched_create(**kwargs):
        if "max_tokens" in kwargs:
            kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
        if kwargs.get("max_completion_tokens", 0) < _MIN_MAX_COMPLETION_TOKENS:
            kwargs["max_completion_tokens"] = _MIN_MAX_COMPLETION_TOKENS
        for p in _GPT5_DROP_PARAMS:
            kwargs.pop(p, None)
        return await inner_create(**kwargs)

    client.chat.completions.create = patched_create


def make_ragas_evaluator(
    settings: Settings,
) -> Callable[[RagasQuerySample], dict] | None:
    """Build the per-sample RAGAs evaluator bound to the Azure OpenAI judge, or
    `None` when no judge credential is configured (local dev / CI → Recall@5-only).

    The 4 metrics (`faithfulness` / `answer_relevancy` / `context_precision` /
    `context_recall`) require an LLM judge (`azure_openai_deployment_llm_judge`,
    same model as the CRAG grader for cost containment) + embeddings (Q19
    `text-embedding-3-large`) for AnswerRelevancy cosine similarity. When the
    eval-set has no reference answers (Q14 SME label cascade pending),
    context_precision/recall fall back to `expected_keywords` joined as the
    pseudo-reference.
    """
    if not settings.azure_openai_api_key:
        logger.info(
            "ragas_evaluator_skipped",
            reason="no AZURE_OPENAI_API_KEY — eval falls back to Recall@5-only",
        )
        return None

    # Defer ragas/openai imports so the no-judge path (and unit tests with stub
    # evaluators) don't need ragas wired.
    from openai import AsyncAzureOpenAI  # noqa: PLC0415
    from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings  # noqa: PLC0415
    from ragas.llms import llm_factory  # noqa: PLC0415
    from ragas.metrics.collections.answer_relevancy import AnswerRelevancy  # noqa: PLC0415
    from ragas.metrics.collections.context_precision import ContextPrecision  # noqa: PLC0415
    from ragas.metrics.collections.context_recall import ContextRecall  # noqa: PLC0415
    from ragas.metrics.collections.faithfulness import Faithfulness  # noqa: PLC0415

    judge_deployment = settings.azure_openai_deployment_llm_judge
    judge_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    patch_for_gpt5(judge_client)
    wrapped_llm = llm_factory(judge_deployment, client=judge_client)

    embed_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    wrapped_embed = RagasOpenAIEmbeddings(
        client=embed_client,
        model=settings.azure_openai_deployment_embedding,
    )

    faithfulness_m = Faithfulness(llm=wrapped_llm)
    answer_relevancy_m = AnswerRelevancy(llm=wrapped_llm, embeddings=wrapped_embed)
    context_precision_m = ContextPrecision(llm=wrapped_llm)
    context_recall_m = ContextRecall(llm=wrapped_llm)

    async def _ascore_metric(
        metric_name: str,
        ascore_call: Callable[[], object],
        sample_query_id: str,
    ) -> float:
        """W36 F2 (b) — per-metric try/except isolation per PC-W34-2.

        Catches ragas / instructor library exceptions (InstructorRetryException +
        其他 transient parse failure) per-metric → fallback 0.0 + structlog warning
        so single bad query 唔拖跨整個 4-metric eval pass。Without 呢個 isolation
        W34 F1 Q-W25-I06+I07 InstructorRetryException 會 throw 上 RagasRunner →
        whole sample marked errored 而失 other 3 metrics 嘅 score。
        """
        try:
            r = await ascore_call()
            return float(r.value)
        except Exception as exc:  # noqa: BLE001 — ragas/instructor exception chain unpredictable
            logger.warning(
                "ragas_metric_exception_fallback",
                metric=metric_name,
                query_id=sample_query_id,
                exception_type=type(exc).__name__,
                error=str(exc)[:200],
            )
            return 0.0

    async def _ascore_all(sample: RagasQuerySample) -> dict:
        reference = sample.reference or " ".join(sample.expected_keywords) or sample.answer
        scores: dict[str, float | int] = {
            "faithfulness": await _ascore_metric(
                "faithfulness",
                lambda: faithfulness_m.ascore(
                    user_input=sample.question,
                    response=sample.answer,
                    retrieved_contexts=sample.contexts,
                ),
                sample.query_id,
            ),
            "answer_relevancy": await _ascore_metric(
                "answer_relevancy",
                lambda: answer_relevancy_m.ascore(
                    user_input=sample.question,
                    response=sample.answer,
                ),
                sample.query_id,
            ),
            "context_precision": await _ascore_metric(
                "context_precision",
                lambda: context_precision_m.ascore(
                    user_input=sample.question,
                    reference=reference,
                    retrieved_contexts=sample.contexts,
                ),
                sample.query_id,
            ),
            "context_recall": await _ascore_metric(
                "context_recall",
                lambda: context_recall_m.ascore(
                    user_input=sample.question,
                    retrieved_contexts=sample.contexts,
                    reference=reference,
                ),
                sample.query_id,
            ),
        }
        # ragas 0.4.3 doesn't expose per-metric token usage — cost via Langfuse
        # trace correlation per architecture.md §7.
        scores["input_tokens"] = 0
        scores["output_tokens"] = 0
        return scores

    def _sync_eval(sample: RagasQuerySample) -> dict:
        # ragas 0.4.3 metric.ascore() must run in its own event loop; the sync
        # RagasRunner contract (+ sync test stubs) means we bridge via a worker
        # thread running asyncio.run rather than awaiting here.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, _ascore_all(sample)).result()

    return _sync_eval


def make_faithfulness_evaluator(
    settings: Settings,
) -> Callable[[str, str, list[str]], float | None] | None:
    """W48 (ADR-0040 dual-axis) — a faithfulness-ONLY evaluator for the config-test
    quality axis. Reference-free (no ground truth): scores whether the answer's
    claims are grounded in the retrieved contexts. Returns `None` when no Azure
    OpenAI judge credential is configured (local dev / CI) → config-test omits the
    quality axis and still returns the presentation counters.

    Distinct from `make_ragas_evaluator` (the 4-metric eval-set path): this computes
    ONLY faithfulness — config-test runs it once per试跑 (last-run answer + contexts),
    so paying for answer_relevancy embeddings + the 2 context metrics would be wasted
    cost. Judge = `azure_openai_deployment_llm_judge` (gpt-5.4-mini per the cost
    policy), same as `make_ragas_evaluator`. Takes a plain (question, answer,
    contexts) tuple rather than a `RagasQuerySample`. Per-call try/except → `None` so
    a judge hiccup never fails the config-test (graceful degradation).
    """
    if not settings.azure_openai_api_key:
        logger.info(
            "faithfulness_evaluator_skipped",
            reason="no AZURE_OPENAI_API_KEY — config-test omits the quality axis",
        )
        return None

    from openai import AsyncAzureOpenAI  # noqa: PLC0415
    from ragas.llms import llm_factory  # noqa: PLC0415
    from ragas.metrics.collections.faithfulness import Faithfulness  # noqa: PLC0415

    judge_client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    patch_for_gpt5(judge_client)
    wrapped_llm = llm_factory(settings.azure_openai_deployment_llm_judge, client=judge_client)
    faithfulness_m = Faithfulness(llm=wrapped_llm)

    def _eval(question: str, answer: str, contexts: list[str]) -> float | None:
        # faithfulness needs both an answer to judge and contexts to judge against;
        # a refused/empty answer or an empty retrieval has no meaningful score.
        if not answer.strip() or not contexts:
            return None

        async def _ascore() -> float:
            r = await faithfulness_m.ascore(
                user_input=question,
                response=answer,
                retrieved_contexts=contexts,
            )
            return float(r.value)

        try:
            # Mirror `_sync_eval`: ragas needs its own event loop, bridged via a
            # worker thread running asyncio.run (robust whether the caller is sync
            # or — via asyncio.to_thread — an async route).
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, _ascore()).result()
        except Exception as exc:  # noqa: BLE001 — ragas/instructor exception chain unpredictable
            logger.warning(
                "faithfulness_eval_exception_fallback",
                exception_type=type(exc).__name__,
                error=str(exc)[:200],
            )
            return None

    return _eval

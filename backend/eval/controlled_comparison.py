"""C06 Eval Framework — controlled shared-question A/B recall comparison (W54).

The **controlled A/B** that W53 explicitly deferred (W53 plan §1:「controlled A/B
(shared text-anchored QA);留更未來」). W53 regenerated synthetic QA per chunk
strategy → each strategy got a DIFFERENT question set → the recall delta was
confounded by question difficulty (it measured *self-retrievability*, NOT a
controlled A/B). W54 removes that confounding: ONE frozen question set is generated
once and scored across every strategy — only the chunk strategy varies.

**How the chunk_id problem is solved** — chunk_ids change on every reindex, so W52's
strict chunk_id recall cannot be reused across strategies. Instead we anchor the
ground truth to TEXT (document sections) and score with keyword-containment:

  - `EvalRunner` (eval/runner.py) ALREADY has a keyword-mode recall path
    (runner.py:166-184): when a query is `validated=False` / has no real
    `acceptable_chunk_ids`, recall = |expected_answer_keywords found in the top-K
    chunk_text (case-insensitive substring)| / |expected_answer_keywords|. This is
    chunk_id-agnostic → the SAME frozen eval-set scores every strategy. W54 reuses it
    → **zero new recall math** (mirrors W52's reuse of strict mode).
  - text anchors = document SECTIONS. `section_path` is assigned at parse time (before
    chunking) and `HeadingAwareChunker` (W53) inherits `LayoutAwareChunker`'s
    section-walk → section_path is **strategy-invariant** → a strategy-independent
    text anchor. Reference chunks are grouped by section_path into passages; the judge
    LLM writes one question + extracts a few verbatim answer keywords per passage.
  - chunk enumeration + the judge client pattern are reused from `eval.synthetic_qa`
    (`_collect_chunks` + `make_qa_generator` shape). Judge = `gpt-5.4-mini` per the
    cost policy. No credential → `None` (harness skips, same graceful contract).

**Honesty (R1 — honesty ladder, 4th phase)**: W51 coverage proxy → W52 synthetic
(not human ground truth) → W53 self-retrievability (not controlled) → W54 IS
controlled (shared frozen set eliminates the per-config confounding). But two limits
remain and MUST be stated: (1) still synthetic — LLM-written questions + LLM-extracted
keywords, NOT human-validated ground truth; (2) keyword-containment is a LEXICAL proxy
— a chunk containing a keyword is not proof it is the answer-bearing chunk, and a
section-anchored question may be answerable from several chunks → recall runs lenient.
Read results as a RELATIVE signal across strategies, never an absolute quality verdict.

This is an OFFLINE engineering harness; live driver / CLI:
`scripts/run_controlled_ab_comparison.py`. This module stays bootstrap-free so the
core is unit-testable with stubs.
"""

from __future__ import annotations

import asyncio
import json
import random
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import structlog

from eval.ragas_evaluator import patch_for_gpt5
from storage.settings import Settings

logger = structlog.get_logger(__name__)

# An async passage -> (question, answer_keywords) generator (or None on error/parse-fail).
KeywordQAGenerateFn = Callable[[str], Awaitable[tuple[str, list[str]] | None]]

# Single judge call returns BOTH the question and the verbatim answer keywords so they
# stay aligned (keywords must appear in the passage text, else keyword-mode recall can
# never match). R2 — distinctive answer terms, not generic words any chunk would carry.
_QA_KEYWORD_SYSTEM_PROMPT = (
    "You are building a CONTROLLED retrieval recall test for a document knowledge base. "
    "Given ONE passage from a document, produce: (1) a single, specific, self-contained "
    "question a real user would ask AND whose answer is found in this passage; (2) 3 to 5 "
    "short DISTINCTIVE answer keywords or key phrases that appear VERBATIM in the passage "
    "and that the answer-bearing chunk MUST contain (avoid generic stopwords or words that "
    "any chunk would have). The question must stand on its own (do NOT write 'the passage' "
    "/ 'this text' / 'according to the document'). Output ONLY a JSON object of the form: "
    '{"question": "<question>", "keywords": ["<kw1>", "<kw2>", "<kw3>"]}'
)

# patch_for_gpt5 floors max_completion_tokens to 4096 when max_tokens is supplied so a
# GPT-5 reasoning judge keeps completion budget after reasoning tokens. The JSON is short.
_QA_MAX_TOKENS = 512


class ControlledRecallError(RuntimeError):
    """Raised when no controlled QA pairs could be produced (empty KB / no judge)."""


@dataclass(slots=True, frozen=True)
class TextAnchoredQAPair:
    """One LLM-generated question + the verbatim answer keywords that anchor it to text.

    The ground truth is the keyword set (chunk_id-agnostic), so the same pair scores any
    chunk strategy. `source_section_path` is the strategy-invariant text anchor it was
    generated from (traceability only — not used for scoring).
    """

    question: str
    expected_keywords: list[str]
    source_section_path: list[str]
    source_text: str


def _parse_qa_keywords(content: str | None) -> tuple[str, list[str]] | None:
    """Parse the judge's JSON reply into (question, keywords), or None on any malformation.

    Tolerant of a markdown ```json fence. Pure (no I/O) so it is unit-testable without a
    live judge. Returns None when the question is empty or no usable keyword survives.
    """
    if not content:
        return None
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text[:4].lower() == "json":
            text = text[4:].strip()
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    question = obj.get("question")
    keywords_raw = obj.get("keywords")
    if not isinstance(question, str) or not question.strip():
        return None
    if not isinstance(keywords_raw, list):
        return None
    keywords: list[str] = []
    for k in keywords_raw:
        if isinstance(k, str) and k.strip() and k.strip() not in keywords:
            keywords.append(k.strip())
    if not keywords:
        return None
    return question.strip(), keywords


def make_qa_keyword_generator(settings: Settings) -> KeywordQAGenerateFn | None:
    """Build the judge-bound question+keyword generator, or `None` when no Azure OpenAI
    credential is configured (local dev / CI) → callers skip the harness.

    Judge = `azure_openai_deployment_llm_judge` (gpt-5.4-mini per the cost policy), same
    deployment as `synthetic_qa.make_qa_generator`. Each call self-degrades to `None` on a
    judge error or unparseable reply so one bad passage never aborts the run.
    """
    if not settings.azure_openai_api_key:
        logger.info(
            "controlled_qa_generator_skipped",
            reason="no AZURE_OPENAI_API_KEY — controlled A/B recall harness unavailable",
        )
        return None

    from openai import AsyncAzureOpenAI  # noqa: PLC0415 — defer so the no-cred path needs no openai

    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    patch_for_gpt5(client)
    deployment = settings.azure_openai_deployment_llm_judge

    async def _generate(passage_text: str) -> tuple[str, list[str]] | None:
        if not passage_text.strip():
            return None
        try:
            resp = await client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": _QA_KEYWORD_SYSTEM_PROMPT},
                    {"role": "user", "content": passage_text},
                ],
                max_tokens=_QA_MAX_TOKENS,
            )
            content = resp.choices[0].message.content
        except Exception as exc:  # noqa: BLE001 — openai exception chain unpredictable; degrade
            logger.warning(
                "controlled_qa_generate_exception",
                exception_type=type(exc).__name__,
                error=str(exc)[:200],
            )
            return None
        return _parse_qa_keywords(content)

    return _generate


def build_section_passages(
    chunks: Sequence[Mapping[str, Any]],
    *,
    max_passage_chars: int = 4000,
    min_passage_chars: int = 40,
) -> list[dict[str, Any]]:
    """Group reference chunks into strategy-invariant section passages (text anchors).

    Chunks are grouped by `tuple(section_path)` (parse-time, strategy-invariant) and their
    text concatenated in encounter order. Each passage is truncated to `max_passage_chars`
    (bounds judge cost + keeps the question focused) and passages shorter than
    `min_passage_chars` are dropped (degenerate single-word sections give poor questions).

    Limitation (honest): grouping is by section_path only — `_collect_chunks` omits doc_id
    — so in a multi-doc KB, identically-named sections across docs merge into one passage.
    Section_path top-level headings are typically doc-distinctive, and the truncation cap
    bounds any merge; this affects passage quality only, not the controlled property (the
    frozen set is still shared across strategies).
    """
    grouped: dict[tuple[str, ...], list[str]] = {}
    order: list[tuple[str, ...]] = []
    for c in chunks:
        text = str(c.get("chunk_text") or "").strip()
        if not text:
            continue
        key = tuple(str(s) for s in (c.get("section_path") or []))
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(text)

    passages: list[dict[str, Any]] = []
    for key in order:
        joined = "\n".join(grouped[key]).strip()
        if len(joined) < min_passage_chars:
            continue
        passages.append({"section_path": list(key), "text": joined[:max_passage_chars]})
    return passages


async def generate_text_anchored_qa(
    passages: Sequence[Mapping[str, Any]],
    generate_fn: KeywordQAGenerateFn,
    *,
    sample_size: int = 30,
    seed: int = 0,
    max_concurrency: int = 4,
) -> list[TextAnchoredQAPair]:
    """Deterministically sample section passages and generate one Q + keyword set each.

    Sampling is seeded for reproducibility and the sample is sorted by section_path so
    output order is stable regardless of the RNG draw order. A passage whose `generate_fn`
    returns `None` (judge error / unparseable / no keyword) is skipped, so the result may
    be shorter than `sample_size`.
    """
    usable = [p for p in passages if str(p.get("text") or "").strip()]
    if not usable:
        return []
    rng = random.Random(seed)
    sampled = usable if len(usable) <= sample_size else rng.sample(usable, sample_size)
    sampled = sorted(sampled, key=lambda p: "/".join(str(s) for s in (p.get("section_path") or [])))

    sem = asyncio.Semaphore(max_concurrency)

    async def _one(passage: Mapping[str, Any]) -> TextAnchoredQAPair | None:
        text = str(passage.get("text") or "")
        async with sem:
            result = await generate_fn(text)
        if not result:
            return None
        question, keywords = result
        return TextAnchoredQAPair(
            question=question,
            expected_keywords=keywords,
            source_section_path=list(passage.get("section_path") or []),
            source_text=text,
        )

    results = await asyncio.gather(*(_one(p) for p in sampled))
    return [r for r in results if r is not None]


def to_keyword_eval_set_payload(
    pairs: list[TextAnchoredQAPair],
    *,
    kb_id: str,
    seed: int,
) -> dict[str, Any]:
    """Build an `EvalRunner`-compatible KEYWORD-mode eval-set dict from QA pairs.

    Each pair becomes a keyword-mode entry: `validated=False` + `acceptable_chunk_ids=[]`
    (so EvalRunner's `use_strict` is False → keyword path) + `expected_answer_keywords`
    populated. EvalRunner then scores recall by keyword containment in the top-K
    chunk_text — chunk_id-agnostic, so the same frozen set scores every strategy.
    `kb_id` is set per-query for EvalRunner's ADR-0018 multi-KB override.
    """
    queries: list[dict[str, Any]] = []
    for i, p in enumerate(pairs, start=1):
        queries.append(
            {
                "query_id": f"CA{i:03d}",
                "query_text": p.question,
                "query_phrasing_source": "controlled_ab_W54",
                "kb_id": kb_id,
                "difficulty": "",
                "query_type": "single_step_lookup",
                "ground_truth": {
                    "primary_chunk_ids": [],
                    "acceptable_chunk_ids": [],  # empty → EvalRunner keyword mode
                    "expected_screenshot_chunks": [],
                    "expected_answer_keywords": list(p.expected_keywords),
                    "expected_refusal": False,
                },
                "annotation": {
                    "annotator": "controlled_ab_W54",
                    "annotated_at": "",
                    "validated": False,  # forces keyword-mode recall (not strict chunk_id)
                    "notes": (
                        "controlled A/B keyword-containment recall (NOT human ground truth; "
                        "lexical proxy) | source_section=" + "/".join(p.source_section_path)
                    ),
                },
            }
        )
    return {
        "metadata": {
            "version": f"controlled-ab-W54-{kb_id}-seed{seed}",
            "kind": "controlled_ab_keyword_recall",
            "note": (
                "Controlled shared-question A/B: ONE frozen LLM-generated question set "
                "(text-anchored to document sections) scored across chunk strategies via "
                "keyword-containment recall. Eliminates W53 per-config question-set "
                "confounding. STILL synthetic (LLM question + keywords) + a lexical-"
                "containment proxy (a chunk containing a keyword is not proof it is the "
                "answer-bearing chunk). NOT human-validated ground-truth recall."
            ),
        },
        "queries": queries,
    }

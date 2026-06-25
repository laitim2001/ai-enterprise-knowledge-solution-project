"""W96 F2 — completeness judge layer (LLM-bound; nugget extract + presence).

Turns a (query, retrieved-context, answer) triple into the per-nugget
``NuggetJudgement`` labels that ``completeness_coverage.compute_metrics`` scores.
Two judge calls, both on ``gpt-5.4-mini`` (``azure_openai_deployment_llm_judge``,
per the cost policy — NOT gpt-5.5), mirroring the eval judge pattern in
``controlled_comparison.make_qa_keyword_generator`` / ``synthetic_qa``:

1. EXTRACT — query-conditioned nugget extraction: given the question + the retrieved
   source context, list the atomic content nuggets a COMPLETE answer should include
   (one step / sub-procedure / variant each), grounded in the context and RELEVANT to
   the question. Query-conditioning is what stops the metric from punishing the
   synthesiser for correctly omitting irrelevant retrieved context.
2. PRESENCE — for each nugget, decide whether the ANSWER conveys it (paraphrase
   counts). The covered/total ratio is the 乙類 over-summarisation signal.

The pure parse helpers (``_parse_nuggets`` / ``_parse_presence``) are I/O-free and
unit-tested without a live judge (per §5.6 H6). ``make_completeness_judge`` returns
``None`` when no Azure OpenAI credential is configured (local dev / CI) so callers
skip the harness, and each call self-degrades to ``None`` on a judge error / bad
reply so one bad query never aborts the run.

CAVEAT (per source-fidelity research): LLM-judged coverage is reliable at
RUN/SYSTEM level (config A/B band) but UNRELIABLE per-answer — see
``completeness_coverage`` module docstring + W96 plan §4.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

import structlog

from eval.completeness_coverage import NuggetJudgement
from eval.ragas_evaluator import patch_for_gpt5
from storage.settings import Settings

logger = structlog.get_logger(__name__)

# (query, retrieved_context, answer) -> per-nugget judgements (or None on error/no-cred).
CompletenessJudgeFn = Callable[[str, str, str], Awaitable[list[NuggetJudgement] | None]]

_EXTRACT_SYSTEM_PROMPT = (
    "You build a CONTENT-COMPLETENESS test for answers drawn from a procedural / SOP "
    "document knowledge base. Given a user QUESTION and the RETRIEVED SOURCE CONTEXT, "
    "list the atomic content nuggets that a COMPLETE answer to the question should "
    "include. Each nugget = ONE step, sub-procedure, or variant/branch that is (a) "
    "present in the context and (b) RELEVANT to the question. Ground every nugget in the "
    "context — invent nothing. Do NOT include content that is irrelevant to the question "
    "(a good answer is allowed to omit irrelevant context). Keep nuggets atomic and "
    'non-overlapping. Output ONLY a JSON object: {"nuggets": ["<nugget1>", '
    '"<nugget2>"]}. Use an empty list if the context holds nothing relevant.'
)

_PRESENCE_SYSTEM_PROMPT = (
    "You judge answer completeness. Given a user QUESTION, an ANSWER, and a list of "
    "content NUGGETS (atomic facts a complete answer should convey), decide for EACH "
    "nugget whether the ANSWER conveys it. A paraphrase counts as present; exact wording "
    "is not required. Judge ONLY against the answer text. Output ONLY a JSON object: "
    '{"judgements": [{"nugget": "<verbatim nugget text>", "present": true}, ...]} '
    "with ONE entry per input nugget, in the SAME order."
)

# patch_for_gpt5 floors max_completion_tokens to 4096 when max_tokens is supplied so a
# GPT-5 reasoning judge keeps completion budget after reasoning tokens.
_EXTRACT_MAX_TOKENS = 1024
_PRESENCE_MAX_TOKENS = 1024


def _strip_fence(content: str) -> str:
    """Strip an optional markdown ```json fence (mirror _parse_qa_keywords)."""
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text[:4].lower() == "json":
            text = text[4:].strip()
    return text


def _parse_nuggets(content: str | None) -> list[str] | None:
    """Parse the extract reply into a deduped nugget list, or None on malformation.

    An explicit empty list (no relevant content) parses to ``[]`` — distinct from a
    parse failure (``None``). Pure (no I/O) so it is unit-testable without a live judge.
    """
    if not content:
        return None
    try:
        obj = json.loads(_strip_fence(content))
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or not isinstance(obj.get("nuggets"), list):
        return None
    nuggets: list[str] = []
    for n in obj["nuggets"]:
        if isinstance(n, str) and n.strip() and n.strip() not in nuggets:
            nuggets.append(n.strip())
    return nuggets


def _parse_presence(content: str | None, nuggets: list[str]) -> list[bool] | None:
    """Parse the presence reply into a per-nugget bool list aligned to ``nuggets``.

    Aligns by the judge's echoed nugget text (robust to reordering); falls back to
    positional alignment when the echo is absent. Any nugget the judge omits is treated
    as NOT present (a dropped judgement should never silently count as covered). Returns
    None only when the reply is unparseable. Pure (no I/O).
    """
    if not content:
        return None
    try:
        obj = json.loads(_strip_fence(content))
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or not isinstance(obj.get("judgements"), list):
        return None
    judged = obj["judgements"]

    by_text: dict[str, bool] = {}
    positional: list[bool] = []
    for entry in judged:
        if not isinstance(entry, dict):
            positional.append(False)
            continue
        present = bool(entry.get("present"))
        positional.append(present)
        text = entry.get("nugget")
        if isinstance(text, str) and text.strip():
            by_text[text.strip()] = present

    # Prefer text alignment; only fall back to positional when NO echoed text matched.
    if any(n in by_text for n in nuggets):
        return [by_text.get(n, False) for n in nuggets]
    if len(positional) == len(nuggets):
        return positional
    return [False] * len(nuggets)


def make_completeness_judge(settings: Settings) -> CompletenessJudgeFn | None:
    """Build the judge-bound (query, context, answer) -> [NuggetJudgement] function, or
    ``None`` when no Azure OpenAI credential is configured → callers skip the harness.

    Judge = ``azure_openai_deployment_llm_judge`` (gpt-5.4-mini per the cost policy).
    """
    if not settings.azure_openai_api_key:
        logger.info(
            "completeness_judge_skipped",
            reason="no AZURE_OPENAI_API_KEY — completeness harness unavailable",
        )
        return None

    from openai import AsyncAzureOpenAI  # noqa: PLC0415 — defer so no-cred path needs no openai

    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
    )
    patch_for_gpt5(client)
    deployment = settings.azure_openai_deployment_llm_judge

    async def _judge(query: str, context: str, answer: str) -> list[NuggetJudgement] | None:
        if not query.strip() or not context.strip():
            return None
        try:
            extract_resp = await client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": _EXTRACT_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"QUESTION:\n{query}\n\nRETRIEVED SOURCE CONTEXT:\n{context}",
                    },
                ],
                max_tokens=_EXTRACT_MAX_TOKENS,
            )
            nuggets = _parse_nuggets(extract_resp.choices[0].message.content)
        except Exception as exc:  # noqa: BLE001 — openai exception chain unpredictable; degrade
            logger.warning(
                "completeness_extract_exception",
                exception_type=type(exc).__name__,
                error=str(exc)[:200],
            )
            return None
        if nuggets is None:
            return None
        if not nuggets:
            return []  # no relevant context nugget → coverage 1.0 (nothing to drop)

        numbered = "\n".join(f"{i + 1}. {n}" for i, n in enumerate(nuggets))
        try:
            presence_resp = await client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": _PRESENCE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"QUESTION:\n{query}\n\nANSWER:\n{answer}\n\nNUGGETS:\n{numbered}",
                    },
                ],
                max_tokens=_PRESENCE_MAX_TOKENS,
            )
            present_flags = _parse_presence(presence_resp.choices[0].message.content, nuggets)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "completeness_presence_exception",
                exception_type=type(exc).__name__,
                error=str(exc)[:200],
            )
            return None
        if present_flags is None:
            return None
        return [
            NuggetJudgement(text=n, present=p) for n, p in zip(nuggets, present_flags, strict=True)
        ]

    return _judge

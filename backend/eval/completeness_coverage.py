"""W96 F1 — answer-completeness / nugget-coverage metric core (pure logic, no IO).

Detects 乙類 over-summarisation (per CLAUDE.md §15 north-star + the source-fidelity
research in ``docs/09-analysis/``): the synthesiser condenses away source content that
WAS in its retrieved context, so a dropped paragraph's images lose their text anchor.

Operationalises "answer content completeness" as nugget-coverage recall — the
peer-reviewed method line confirmed by the 2026-06-25 research round (FineSurE ACL
2024 ``Completeness = covered keyfacts / all keyfacts``; AutoNuggetizer SIGIR 2025
nugget recall; CRUX EMNLP 2025 sub-question coverage). See
``docs/09-analysis/source_fidelity_recall_external_research_20260625.md``.

answer_coverage = |context nuggets present in answer| / |context nuggets|
    The 乙類 ISOLATOR: of the query-relevant facts the synthesiser HAD in its
    retrieved context, how many survived into the answer. Low = synthesiser dropped
    content (CRUX "retrieved but not answered"). Nuggets are extracted
    QUERY-CONDITIONED (only facts a complete answer should include) so correctly
    filtering irrelevant context is NOT counted as a drop — that filtering happens in
    the F2 judge, not here.

context_coverage (optional) = |reference nuggets present in context| / |reference|
    CRUX retrieval-ceiling axis — separates "context insufficient" from "synthesiser
    condensed". Needs a reference nugget set (e.g. GT-section); left None when not
    computed (human GT is a known blocker — W96 plan §5).

This module is the PURE scoring core. Nugget EXTRACTION and presence JUDGEMENT are
LLM calls (gpt-5.4-mini judge per cost policy) that live in the live driver
(``scripts/run_completeness.py``) / F2 judge layer; they are injected here as
already-computed ``NuggetJudgement`` labels so the maths is unit-testable without
mocks (mirrors ``image_recall.py`` / ``marker_placement.py``).

CAVEAT (per research): LLM-judged coverage is a reliable RUN/SYSTEM-level proxy
(config A/B gate) but UNRELIABLE per-answer (per-topic Kendall τ≈0.30-0.44). Use for
A/B band comparison across multiple runs, NOT single-answer debug.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class NuggetJudgement:
    """One query-conditioned atomic nugget + whether it is present in the answer.

    ``text`` is the atomic fact/step a complete answer to the query should include
    (extracted from the synthesiser's retrieved context by the F2 judge); ``present``
    is the judge's verdict that the answer conveys it.
    """

    text: str
    present: bool


@dataclass(frozen=True, slots=True)
class CompletenessMetrics:
    """One query's nugget-coverage outcome.

    answer_coverage = covered / total context nuggets — 1.0 when no nugget was
    extracted (nothing the answer could have dropped). The 乙類 axis: low coverage =
    the synthesiser condensed away content that was in its retrieved context.
    """

    total_nuggets: int
    covered_nuggets: int
    answer_coverage: float
    missed: list[str] = field(default_factory=list)  # context nuggets absent from answer


def compute_metrics(judgements: list[NuggetJudgement]) -> CompletenessMetrics:
    """Pure coverage maths over per-nugget presence judgements."""
    total = len(judgements)
    covered = sum(1 for j in judgements if j.present)
    coverage = covered / total if total else 1.0
    return CompletenessMetrics(
        total_nuggets=total,
        covered_nuggets=covered,
        answer_coverage=coverage,
        missed=[j.text for j in judgements if not j.present],
    )


@dataclass(frozen=True, slots=True)
class CompletenessQueryResult:
    """One query's outcome — answer_coverage (always) + context_coverage (optional)."""

    query_id: str
    query_text: str
    metrics: CompletenessMetrics
    context_coverage: float | None = None  # CRUX retrieval-ceiling axis; None = not computed
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CompletenessReport:
    eval_set: str
    kb_id: str
    total_queries: int
    scored_queries: int  # non-errored
    mean_answer_coverage: float
    mean_context_coverage: float | None  # None when no query computed context coverage
    per_query: list[CompletenessQueryResult] = field(default_factory=list)


def aggregate(
    eval_set: str,
    kb_id: str,
    per_query: list[CompletenessQueryResult],
) -> CompletenessReport:
    """Mean answer-coverage over non-errored queries; mean context-coverage over the
    subset that computed it (None when none did)."""
    scored = [r for r in per_query if r.error is None]
    n = len(scored)
    mean_answer = sum(r.metrics.answer_coverage for r in scored) / n if n else 0.0
    ctx = [r.context_coverage for r in scored if r.context_coverage is not None]
    mean_context = sum(ctx) / len(ctx) if ctx else None
    return CompletenessReport(
        eval_set=eval_set,
        kb_id=kb_id,
        total_queries=len(per_query),
        scored_queries=n,
        mean_answer_coverage=mean_answer,
        mean_context_coverage=mean_context,
        per_query=per_query,
    )


def report_to_dict(report: CompletenessReport) -> dict[str, Any]:
    """Serialize the report to a plain dict (YAML/JSON-friendly)."""
    meta: dict[str, Any] = {
        "eval_set": report.eval_set,
        "kb_id": report.kb_id,
        "total_queries": report.total_queries,
        "scored_queries": report.scored_queries,
        "mean_answer_coverage": round(report.mean_answer_coverage, 4),
        "caveat": (
            "run-level A/B gate only — per-answer coverage is unreliable "
            "(per source-fidelity research); compare bands over multiple runs"
        ),
    }
    if report.mean_context_coverage is not None:
        meta["mean_context_coverage"] = round(report.mean_context_coverage, 4)
    return {
        "metadata": meta,
        "per_query": [
            {
                "query_id": r.query_id,
                "query_text": r.query_text,
                "answer_coverage": round(r.metrics.answer_coverage, 4),
                "total_nuggets": r.metrics.total_nuggets,
                "covered_nuggets": r.metrics.covered_nuggets,
                "missed_count": len(r.metrics.missed),
                "missed": r.metrics.missed,
                "context_coverage": (
                    round(r.context_coverage, 4) if r.context_coverage is not None else None
                ),
                "error": r.error,
            }
            for r in report.per_query
        ],
    }


# --------------------------------------------------------------------------- #
# W96 DD-15 — gate hardening: K-run averaging + paired A/B (fixed nugget set)  #
# --------------------------------------------------------------------------- #
# F4 proved per-answer coverage is noisy (synthesiser + judge stochasticity).
# To turn the metric into a usable config A/B gate we (1) fix the nugget set per
# query (extract once, reuse — research-backed: AutoNuggetizer "fix creation,
# automate assignment"), (2) average K answer generations per query, and (3)
# compare two configs PAIRED on the same query + same nuggets so query-level and
# nugget-level offset cancels. These pure helpers are the scoring/aggregation
# layer; the K generations + presence judgements come from the live A/B driver.


def mean_std(values: list[float]) -> tuple[float, float]:
    """Population mean + standard deviation of a coverage sample (0.0, 0.0 when empty)."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    return mean, math.sqrt(var)


@dataclass(frozen=True, slots=True)
class PairedQueryResult:
    """One query's paired A/B outcome over K runs per arm, against a FIXED nugget set.

    delta = mean_b - mean_a. A positive delta means config B covers more of the same
    fixed nuggets than config A. Per-query ``std_*`` exposes the residual answer/judge
    noise that K-run averaging is smoothing (the F4 instability made visible).
    """

    query_id: str
    query_text: str
    total_nuggets: int
    coverage_a_runs: list[float]
    coverage_b_runs: list[float]
    mean_a: float
    std_a: float
    mean_b: float
    std_b: float
    delta: float
    error: str | None = None


def build_paired_query_result(
    query_id: str,
    query_text: str,
    total_nuggets: int,
    a_runs: list[float],
    b_runs: list[float],
    error: str | None = None,
) -> PairedQueryResult:
    """Summarise K-run coverage samples for both arms into a paired result."""
    mean_a, std_a = mean_std(a_runs)
    mean_b, std_b = mean_std(b_runs)
    return PairedQueryResult(
        query_id=query_id,
        query_text=query_text,
        total_nuggets=total_nuggets,
        coverage_a_runs=list(a_runs),
        coverage_b_runs=list(b_runs),
        mean_a=mean_a,
        std_a=std_a,
        mean_b=mean_b,
        std_b=std_b,
        delta=mean_b - mean_a,
        error=error,
    )


@dataclass(frozen=True, slots=True)
class PairedReport:
    eval_set: str
    kb_id: str
    config_a: str
    config_b: str
    runs_per_arm: int
    total_queries: int
    scored_queries: int
    mean_coverage_a: float
    mean_coverage_b: float
    mean_delta: float
    mean_per_query_std: float  # avg residual noise after K-run averaging (lower = more stable)
    delta_positive: int  # queries where B beat A
    delta_negative: int
    delta_zero: int
    per_query: list[PairedQueryResult] = field(default_factory=list)


def aggregate_paired(
    eval_set: str,
    kb_id: str,
    config_a: str,
    config_b: str,
    runs_per_arm: int,
    per_query: list[PairedQueryResult],
) -> PairedReport:
    """Aggregate paired per-query results — arm means, mean delta, delta-sign tally
    (B-beats-A stability), and the average residual per-query std."""
    scored = [r for r in per_query if r.error is None]
    n = len(scored)
    mean_a = sum(r.mean_a for r in scored) / n if n else 0.0
    mean_b = sum(r.mean_b for r in scored) / n if n else 0.0
    # Residual noise after K-run averaging: avg of both arms' per-query std.
    per_q_std = sum(r.std_a + r.std_b for r in scored) / (2 * n) if n else 0.0
    return PairedReport(
        eval_set=eval_set,
        kb_id=kb_id,
        config_a=config_a,
        config_b=config_b,
        runs_per_arm=runs_per_arm,
        total_queries=len(per_query),
        scored_queries=n,
        mean_coverage_a=mean_a,
        mean_coverage_b=mean_b,
        mean_delta=mean_b - mean_a,
        mean_per_query_std=per_q_std,
        delta_positive=sum(1 for r in scored if r.delta > 0),
        delta_negative=sum(1 for r in scored if r.delta < 0),
        delta_zero=sum(1 for r in scored if r.delta == 0),
        per_query=per_query,
    )


def paired_report_to_dict(report: PairedReport) -> dict[str, Any]:
    """Serialize a paired A/B report to a YAML/JSON-friendly dict."""
    return {
        "metadata": {
            "eval_set": report.eval_set,
            "kb_id": report.kb_id,
            "config_a": report.config_a,
            "config_b": report.config_b,
            "runs_per_arm": report.runs_per_arm,
            "total_queries": report.total_queries,
            "scored_queries": report.scored_queries,
            "mean_coverage_a": round(report.mean_coverage_a, 4),
            "mean_coverage_b": round(report.mean_coverage_b, 4),
            "mean_delta": round(report.mean_delta, 4),
            "mean_per_query_std": round(report.mean_per_query_std, 4),
            "delta_sign": {
                "B_beats_A": report.delta_positive,
                "A_beats_B": report.delta_negative,
                "tie": report.delta_zero,
            },
            "caveat": (
                "paired delta cancels query/nugget offset; fixed nuggets + K-run "
                "averaging smooth answer/judge noise. Read mean_delta + delta_sign "
                "stability, not absolute per-query coverage."
            ),
        },
        "per_query": [
            {
                "query_id": r.query_id,
                "query_text": r.query_text,
                "total_nuggets": r.total_nuggets,
                "mean_a": round(r.mean_a, 4),
                "std_a": round(r.std_a, 4),
                "mean_b": round(r.mean_b, 4),
                "std_b": round(r.std_b, 4),
                "delta": round(r.delta, 4),
                "coverage_a_runs": [round(v, 4) for v in r.coverage_a_runs],
                "coverage_b_runs": [round(v, 4) for v in r.coverage_b_runs],
                "error": r.error,
            }
            for r in report.per_query
        ],
    }

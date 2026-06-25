"""W96 F1 — answer-completeness / nugget-coverage metric unit tests (per §5.6 H6).

Tests the pure metric core (``backend/eval/completeness_coverage.py``):
- answer_coverage computation (full / partial drop / total drop / empty)
- missed-nugget list (the dropped 乙類 content)
- aggregate over mixed scored / errored queries
- context_coverage optional axis (None vs computed; mean over the computed subset)
- report_to_dict shape + per-answer-unreliable caveat present
"""

from __future__ import annotations

from eval.completeness_coverage import (
    CompletenessQueryResult,
    NuggetJudgement,
    aggregate,
    compute_metrics,
    report_to_dict,
)


def _judgements(present_flags: list[bool]) -> list[NuggetJudgement]:
    return [NuggetJudgement(text=f"nugget-{i}", present=p) for i, p in enumerate(present_flags)]


def test_full_coverage() -> None:
    m = compute_metrics(_judgements([True, True, True]))
    assert m.answer_coverage == 1.0
    assert m.total_nuggets == 3
    assert m.covered_nuggets == 3
    assert m.missed == []


def test_partial_drop_lists_missed() -> None:
    # 4 nuggets, synthesiser kept 2 → 乙類: coverage 0.5, the 2 dropped listed
    js = [
        NuggetJudgement("post the journal", True),
        NuggetJudgement("confirm voucher", True),
        NuggetJudgement("RMS/RSP petty cash variant", False),
        NuggetJudgement("GL03 overview", False),
    ]
    m = compute_metrics(js)
    assert m.answer_coverage == 0.5
    assert m.covered_nuggets == 2
    assert m.missed == ["RMS/RSP petty cash variant", "GL03 overview"]


def test_total_drop() -> None:
    m = compute_metrics(_judgements([False, False]))
    assert m.answer_coverage == 0.0
    assert m.covered_nuggets == 0
    assert len(m.missed) == 2


def test_empty_nuggets_is_full_coverage() -> None:
    # nothing extracted → nothing could be dropped → 1.0 (not a div-by-zero / not 0.0)
    m = compute_metrics([])
    assert m.answer_coverage == 1.0
    assert m.total_nuggets == 0
    assert m.missed == []


def test_aggregate_skips_errored() -> None:
    per_query = [
        CompletenessQueryResult("Q1", "a", compute_metrics(_judgements([True, True]))),  # 1.0
        CompletenessQueryResult("Q2", "b", compute_metrics(_judgements([True, False]))),  # 0.5
        CompletenessQueryResult("Q3", "c", compute_metrics([]), error="query failed"),  # excluded
    ]
    report = aggregate("eval-set", "kb-1", per_query)
    assert report.total_queries == 3
    assert report.scored_queries == 2
    assert report.mean_answer_coverage == 0.75  # (1.0 + 0.5) / 2, Q3 excluded
    assert report.mean_context_coverage is None  # none computed it


def test_aggregate_empty() -> None:
    report = aggregate("eval-set", "kb-1", [])
    assert report.scored_queries == 0
    assert report.mean_answer_coverage == 0.0
    assert report.mean_context_coverage is None


def test_context_coverage_mean_over_computed_subset() -> None:
    per_query = [
        CompletenessQueryResult(
            "Q1", "a", compute_metrics(_judgements([True])), context_coverage=0.8
        ),
        CompletenessQueryResult(
            "Q2", "b", compute_metrics(_judgements([True])), context_coverage=0.6
        ),
        CompletenessQueryResult(
            "Q3", "c", compute_metrics(_judgements([True])), context_coverage=None
        ),  # not computed → excluded from context mean only
    ]
    report = aggregate("eval-set", "kb-1", per_query)
    assert report.scored_queries == 3
    assert report.mean_context_coverage == 0.7  # (0.8 + 0.6) / 2, Q3 excluded


def test_report_to_dict_shape_and_caveat() -> None:
    per_query = [
        CompletenessQueryResult(
            "Q1",
            "How do I post a journal entry?",
            compute_metrics([NuggetJudgement("step a", True), NuggetJudgement("variant b", False)]),
        ),
    ]
    d = report_to_dict(aggregate("eval-set", "kb-1", per_query))
    assert d["metadata"]["mean_answer_coverage"] == 0.5
    assert "per-answer" in d["metadata"]["caveat"]  # run-level-only caveat surfaced
    assert "mean_context_coverage" not in d["metadata"]  # omitted when None
    row = d["per_query"][0]
    assert row["answer_coverage"] == 0.5
    assert row["missed"] == ["variant b"]
    assert row["context_coverage"] is None


def test_report_to_dict_includes_context_coverage_when_present() -> None:
    per_query = [
        CompletenessQueryResult(
            "Q1", "a", compute_metrics(_judgements([True])), context_coverage=0.9
        ),
    ]
    d = report_to_dict(aggregate("eval-set", "kb-1", per_query))
    assert d["metadata"]["mean_context_coverage"] == 0.9
    assert d["per_query"][0]["context_coverage"] == 0.9

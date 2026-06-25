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
    aggregate_paired,
    build_paired_query_result,
    compute_metrics,
    mean_std,
    paired_report_to_dict,
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


# --- DD-15 gate hardening: mean_std + paired A/B --------------------------- #


def test_mean_std_basic() -> None:
    mean, std = mean_std([1.0, 1.0, 1.0])
    assert mean == 1.0
    assert std == 0.0
    mean, std = mean_std([0.0, 1.0])
    assert mean == 0.5
    assert std == 0.5  # population std of {0,1}


def test_mean_std_empty() -> None:
    assert mean_std([]) == (0.0, 0.0)


def test_build_paired_query_result_delta() -> None:
    # A noisy (the F4 problem) but mean lower; B higher mean → positive delta
    r = build_paired_query_result(
        "Q1", "q", total_nuggets=10, a_runs=[0.2, 0.8, 0.5], b_runs=[0.9, 1.0, 0.8]
    )
    assert round(r.mean_a, 4) == 0.5
    assert round(r.mean_b, 4) == 0.9
    assert round(r.delta, 4) == 0.4
    assert r.std_a > 0  # residual noise still visible per-arm


def test_aggregate_paired_delta_sign_tally_and_residual_std() -> None:
    per_query = [
        build_paired_query_result("Q1", "a", 5, [0.4, 0.6], [0.8, 1.0]),  # delta +0.4
        build_paired_query_result("Q2", "b", 5, [1.0, 1.0], [1.0, 1.0]),  # delta 0 (tie)
        build_paired_query_result("Q3", "c", 5, [0.9, 0.9], [0.5, 0.5]),  # delta -0.4
        build_paired_query_result("Q4", "d", 5, [], [], error="failed"),  # excluded
    ]
    rep = aggregate_paired("set", "kb", "gpt-5.4-mini", "gpt-5.5", 2, per_query)
    assert rep.total_queries == 4
    assert rep.scored_queries == 3
    assert rep.delta_positive == 1
    assert rep.delta_negative == 1
    assert rep.delta_zero == 1
    assert round(rep.mean_delta, 4) == 0.0  # (+0.4 + 0 - 0.4) / 3
    # Q2 has zero std both arms; Q1/Q3 have std 0.1 each arm → avg residual > 0
    assert rep.mean_per_query_std > 0


def test_paired_report_to_dict_shape() -> None:
    per_query = [build_paired_query_result("Q1", "a", 5, [0.4, 0.6], [0.8, 1.0])]
    d = paired_report_to_dict(aggregate_paired("set", "kb", "A", "B", 2, per_query))
    assert d["metadata"]["mean_delta"] == 0.4
    assert d["metadata"]["delta_sign"]["B_beats_A"] == 1
    assert "paired delta" in d["metadata"]["caveat"]
    row = d["per_query"][0]
    assert row["coverage_a_runs"] == [0.4, 0.6]
    assert row["delta"] == 0.4

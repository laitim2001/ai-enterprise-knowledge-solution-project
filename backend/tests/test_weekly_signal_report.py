"""W10 D2 F4.3 — Q15 weekly signal report scaffold coverage.

Per W10 plan §2 F4.3 acceptance:
  - ISO-week bucketing splits records correctly across week boundaries
  - Top-N selection per signal axis(frequency / refusal / CRAG / negative feedback)
  - Feedback join by query_hash surfaces query text in negative-feedback list
  - PII strip at render time(belt-and-braces H5)
  - Empty corpus → graceful Markdown
  - CLI dry-run + write-to-output paths
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from observability.query_collector import build_record
from observability.weekly_signal_report import (
    FeedbackRecord,
    TopQuery,
    WeeklyAggregation,
    aggregate_all_weeks,
    aggregate_week,
    current_iso_week,
    main,
    parse_iso_week,
    read_feedback_yaml,
    render_markdown,
)

# ---------------------------------------------------------------------------
# ISO-week parser
# ---------------------------------------------------------------------------


def test_parse_iso_week_z_suffix() -> None:
    # 2026-06-03 Wednesday → ISO week 23 of year 2026
    assert parse_iso_week("2026-06-03T10:15:00Z") == "2026-W23"


def test_parse_iso_week_offset_suffix() -> None:
    assert parse_iso_week("2026-06-03T10:15:00+00:00") == "2026-W23"


def test_parse_iso_week_date_only_falls_through_to_zero_time_utc() -> None:
    assert parse_iso_week("2026-06-03") == "2026-W23"


def test_parse_iso_week_year_boundary() -> None:
    # 2025-12-29 Monday → ISO week 1 of YEAR 2026 per ISO-8601 rule
    assert parse_iso_week("2025-12-29T00:00:00Z") == "2026-W01"


def test_parse_iso_week_raises_on_garbage() -> None:
    with pytest.raises(ValueError):
        parse_iso_week("not-a-date")


def test_current_iso_week_well_formed() -> None:
    label = current_iso_week()
    assert label[:4].isdigit()
    assert label[4:6] == "-W"
    assert label[6:].isdigit() and 1 <= int(label[6:]) <= 53


# ---------------------------------------------------------------------------
# Aggregation core
# ---------------------------------------------------------------------------


def _make_record(
    text: str,
    *,
    refused: bool = False,
    crag: bool = False,
    timestamp: datetime | None = None,
):
    return build_record(
        query_text=text,
        kb_id="drive_user_manuals",
        user_oid="aaaa-bbbb-cccc-dddd",
        status_code=200,
        duration_ms=1500,
        refused=refused,
        crag_triggered=crag,
        timestamp=timestamp or datetime(2026, 6, 3, 10, 0, 0, tzinfo=UTC),
    )


def _make_feedback(
    *,
    rating: str = "thumbs_up",
    comment: str | None = None,
    query_hash: str | None = None,
    timestamp: datetime | None = None,
) -> FeedbackRecord:
    ts = (timestamp or datetime(2026, 6, 3, 10, 0, 0, tzinfo=UTC)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    return FeedbackRecord(
        feedback_id="11111111-2222-3333-4444-555555555555",
        trace_id="trace-test",
        timestamp=ts,
        rating=rating,
        comment=comment,
        query_hash=query_hash,
        user_oid_redacted="u_test",
    )


def test_aggregate_week_volume_summary_correct() -> None:
    records = [
        _make_record("query A?"),
        _make_record("query B?", refused=True),
        _make_record("query C?", crag=True),
    ]
    feedback = [
        _make_feedback(rating="thumbs_up"),
        _make_feedback(rating="thumbs_down", comment="bad"),
    ]
    agg = aggregate_week("2026-W23", records, feedback)
    assert agg.total_queries == 3
    assert agg.refused_queries == 1
    assert agg.crag_triggered == 1
    assert agg.total_feedback == 2
    assert agg.thumbs_up == 1
    assert agg.thumbs_down == 1


def test_aggregate_week_top_frequent_orders_by_count_desc() -> None:
    records = [
        _make_record("popular?"),
        _make_record("popular?"),
        _make_record("popular?"),
        _make_record("rare?"),
    ]
    agg = aggregate_week("2026-W23", records, [], top_n=5)
    assert len(agg.top_frequent) == 2
    assert agg.top_frequent[0].query_text == "popular?"
    assert agg.top_frequent[0].count == 3
    assert agg.top_frequent[1].query_text == "rare?"
    assert agg.top_frequent[1].count == 1


def test_aggregate_week_top_refused_segregated_from_top_frequent() -> None:
    records = [
        _make_record("ok query?"),
        _make_record("oos query?", refused=True),
        _make_record("oos query?", refused=True),
    ]
    agg = aggregate_week("2026-W23", records, [])
    assert all(t.query_text != "oos query?" or t.count == 2 for t in agg.top_refused)
    refused_texts = {t.query_text for t in agg.top_refused}
    assert refused_texts == {"oos query?"}
    # Frequent list still includes BOTH(refusal does not exclude from frequency tally)
    freq_texts = {t.query_text for t in agg.top_frequent}
    assert "oos query?" in freq_texts and "ok query?" in freq_texts


def test_aggregate_week_top_crag_segregated() -> None:
    records = [
        _make_record("plain"),
        _make_record("crag-fired?", crag=True),
    ]
    agg = aggregate_week("2026-W23", records, [])
    assert {t.query_text for t in agg.top_crag} == {"crag-fired?"}


def test_aggregate_week_top_n_caps_list_length() -> None:
    records = [_make_record(f"q{i}?") for i in range(20)]
    agg = aggregate_week("2026-W23", records, [], top_n=5)
    assert len(agg.top_frequent) == 5


def test_aggregate_week_negative_feedback_joins_to_query_text() -> None:
    record = _make_record("how to reset password?")
    feedback = _make_feedback(
        rating="thumbs_down",
        comment="outdated screenshots",
        query_hash=record.query_hash,
    )
    agg = aggregate_week("2026-W23", [record], [feedback])
    assert len(agg.top_negative_feedback) == 1
    text, comment = agg.top_negative_feedback[0]
    assert text == "how to reset password?"
    assert comment == "outdated screenshots"


def test_aggregate_week_negative_feedback_unknown_when_no_query_hash() -> None:
    feedback = _make_feedback(rating="thumbs_down", comment="bad UX", query_hash=None)
    agg = aggregate_week("2026-W23", [], [feedback])
    assert agg.top_negative_feedback == [("(unknown)", "bad UX")]


def test_aggregate_week_negative_feedback_pii_strip_applied() -> None:
    """Belt-and-braces H5 — render-time strip catches anything missed upstream。"""
    feedback = _make_feedback(
        rating="thumbs_down",
        comment="email me at user@example.com or call 555-123-4567",
    )
    agg = aggregate_week("2026-W23", [], [feedback])
    _, stripped_comment = agg.top_negative_feedback[0]
    assert "user@example.com" not in stripped_comment
    assert "555-123-4567" not in stripped_comment
    assert "<REDACTED_EMAIL>" in stripped_comment
    assert "<REDACTED_PHONE>" in stripped_comment


def test_aggregate_week_empty_inputs() -> None:
    agg = aggregate_week("2026-W23", [], [])
    assert agg.total_queries == 0
    assert agg.top_frequent == []
    assert agg.top_negative_feedback == []


# ---------------------------------------------------------------------------
# Multi-week bucketing
# ---------------------------------------------------------------------------


def test_aggregate_all_weeks_partitions_by_iso_week() -> None:
    week_a = _make_record("a?", timestamp=datetime(2026, 6, 1, tzinfo=UTC))  # Mon = W23
    week_b = _make_record("b?", timestamp=datetime(2026, 6, 8, tzinfo=UTC))  # Mon = W24
    aggs = aggregate_all_weeks([week_a, week_b], [])
    assert [a.iso_week for a in aggs] == ["2026-W23", "2026-W24"]
    assert aggs[0].total_queries == 1
    assert aggs[1].total_queries == 1


def test_aggregate_all_weeks_filter_returns_only_matching_week() -> None:
    week_a = _make_record("a?", timestamp=datetime(2026, 6, 1, tzinfo=UTC))
    week_b = _make_record("b?", timestamp=datetime(2026, 6, 8, tzinfo=UTC))
    aggs = aggregate_all_weeks([week_a, week_b], [], week_filter="2026-W24")
    assert [a.iso_week for a in aggs] == ["2026-W24"]
    assert aggs[0].top_frequent[0].query_text == "b?"


def test_aggregate_all_weeks_empty_corpora_returns_empty_list() -> None:
    assert aggregate_all_weeks([], []) == []


def test_aggregate_all_weeks_skips_unparseable_timestamps() -> None:
    """Records with malformed timestamps must NOT crash aggregation。"""
    good = _make_record("good?", timestamp=datetime(2026, 6, 1, tzinfo=UTC))
    bad = good.model_copy(update={"timestamp": "garbage-not-iso"})
    aggs = aggregate_all_weeks([good, bad], [])
    assert sum(a.total_queries for a in aggs) == 1


# ---------------------------------------------------------------------------
# Feedback YAML reader
# ---------------------------------------------------------------------------


def test_read_feedback_yaml_round_trip(tmp_path: Path) -> None:
    payload = {
        "collection_metadata": {"phase": "W10-test", "collection_owner": "test"},
        "feedback_records": [
            {
                "feedback_id": "abc",
                "trace_id": "tr-1",
                "timestamp": "2026-06-03T10:00:00Z",
                "rating": "thumbs_down",
                "comment": "stale info",
                "query_hash": "h" * 64,
                "user_oid_redacted": "u_xxxx",
            }
        ],
    }
    path = tmp_path / "fb.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    metadata, records = read_feedback_yaml(path)
    assert metadata["phase"] == "W10-test"
    assert len(records) == 1
    assert records[0].rating == "thumbs_down"
    assert records[0].query_hash == "h" * 64


def test_read_feedback_yaml_handles_datetime_timestamp(tmp_path: Path) -> None:
    """PyYAML parses ISO-8601 strings into datetime — coerce back to ISO string。"""
    text = """
collection_metadata:
  phase: W10-test
feedback_records:
  - feedback_id: abc
    trace_id: tr-1
    timestamp: 2026-06-03T10:00:00Z
    rating: thumbs_up
    user_oid_redacted: u_xxxx
"""
    path = tmp_path / "fb.yaml"
    path.write_text(text, encoding="utf-8")
    _, records = read_feedback_yaml(path)
    assert records[0].timestamp == "2026-06-03T10:00:00Z"


# ---------------------------------------------------------------------------
# Markdown render
# ---------------------------------------------------------------------------


def test_render_markdown_includes_required_sections() -> None:
    record = _make_record("how do i print?")
    feedback = _make_feedback(
        rating="thumbs_down",
        comment="bad screenshot",
        query_hash=record.query_hash,
    )
    aggs = aggregate_all_weeks([record], [feedback])
    md = render_markdown(aggs)

    assert "# EKP Beta Cohort — Weekly Signal Report" in md
    assert "ISO Week 2026-W23" in md
    assert "Volume Summary" in md
    assert "Top Frequent Queries" in md
    assert "Refusal Cluster" in md
    assert "CRAG-Triggered Cluster" in md
    assert "Negative Feedback" in md
    assert "how do i print?" in md
    assert "bad screenshot" in md


def test_render_markdown_empty_aggregations_message() -> None:
    md = render_markdown([])
    assert "no records found" in md.lower()


def test_render_markdown_empty_section_placeholder() -> None:
    """Per-section empty case → friendly placeholder rather than blank list。"""
    record = _make_record("only frequent?")
    aggs = aggregate_all_weeks([record], [])
    md = render_markdown(aggs)
    # Refusal + CRAG + negative-feedback all empty
    assert "_(no entries this week)_" in md
    assert "_(no thumbs_down this week)_" in md


def test_render_markdown_long_query_text_truncated() -> None:
    long_text = "How do I configure a very specific feature " * 5  # > 100 chars
    record = _make_record(long_text)
    aggs = aggregate_all_weeks([record], [])
    md = render_markdown(aggs)
    assert "…" in md  # truncation marker present


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def _write_query_corpus(tmp_path: Path, records) -> Path:
    """Write a query_collector-style corpus YAML directly(no dedup)。"""
    payload = {
        "collection_metadata": {"phase": "test", "collection_owner": "test"},
        "queries": [r.model_dump() for r in records],
    }
    path = tmp_path / "queries.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_cli_stdout_default(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    queries_path = _write_query_corpus(tmp_path, [_make_record("hello?")])
    rc = main(["--queries", str(queries_path)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Weekly Signal Report" in captured.out
    assert "ISO Week 2026-W23" in captured.out


def test_cli_writes_output_file(tmp_path: Path) -> None:
    queries_path = _write_query_corpus(tmp_path, [_make_record("hello?")])
    output_path = tmp_path / "report.md"
    rc = main([
        "--queries", str(queries_path),
        "--output", str(output_path),
    ])
    assert rc == 0
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Weekly Signal Report" in content


def test_cli_with_feedback_corpus(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    record = _make_record("printer reset?")
    queries_path = _write_query_corpus(tmp_path, [record])

    feedback_path = tmp_path / "fb.yaml"
    feedback_path.write_text(
        yaml.safe_dump({
            "collection_metadata": {"phase": "test"},
            "feedback_records": [{
                "feedback_id": "fb1",
                "trace_id": "tr1",
                "timestamp": "2026-06-03T10:00:00Z",
                "rating": "thumbs_down",
                "comment": "outdated firmware screenshot",
                "query_hash": record.query_hash,
                "user_oid_redacted": "u_test",
            }],
        }, sort_keys=False),
        encoding="utf-8",
    )

    rc = main([
        "--queries", str(queries_path),
        "--feedback", str(feedback_path),
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "outdated firmware screenshot" in captured.out
    assert "👎 1" in captured.out


def test_cli_week_filter(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    week_a = _make_record("a?", timestamp=datetime(2026, 6, 1, tzinfo=UTC))
    week_b = _make_record("b?", timestamp=datetime(2026, 6, 8, tzinfo=UTC))
    queries_path = _write_query_corpus(tmp_path, [week_a, week_b])

    rc = main([
        "--queries", str(queries_path),
        "--week", "2026-W24",
    ])
    assert rc == 0
    out = capsys.readouterr().out
    assert "ISO Week 2026-W24" in out
    assert "ISO Week 2026-W23" not in out


def test_cli_missing_queries_file_returns_2(tmp_path: Path) -> None:
    rc = main(["--queries", str(tmp_path / "does-not-exist.yaml")])
    assert rc == 2


# ---------------------------------------------------------------------------
# Smoke contracts
# ---------------------------------------------------------------------------


def test_weekly_aggregation_field_set_stable() -> None:
    fields = {
        "iso_week",
        "total_queries",
        "refused_queries",
        "crag_triggered",
        "total_feedback",
        "thumbs_down",
        "thumbs_up",
        "top_frequent",
        "top_refused",
        "top_crag",
        "top_negative_feedback",
    }
    assert fields <= set(WeeklyAggregation.__dataclass_fields__.keys())


def test_top_query_field_set_stable() -> None:
    fields = {"query_text", "query_hash", "count"}
    assert fields == set(TopQuery.__dataclass_fields__.keys())


def test_mock_feedback_corpus_loads_cleanly() -> None:
    """Bootstrap mock corpus YAML must round-trip through the reader。"""
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "docs" / "03-implementation" / "beta-feedback-W9-W10.yaml"
    metadata, records = read_feedback_yaml(path)
    assert metadata["phase"] == "W9-W10 Beta internal testing"
    assert len(records) == 6
    assert sum(1 for r in records if r.rating == "thumbs_up") == 3
    assert sum(1 for r in records if r.rating == "thumbs_down") == 3

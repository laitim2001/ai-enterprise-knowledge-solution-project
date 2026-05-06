"""C07 Observability — Q15 manual update frequency signal scaffold(W10 D2 F4.3).

Per W10 plan §2 F4.3 + Open Q15(manual update frequency)deferred to W9-W10
Beta phase real query log signal trigger + W9 D1 三方 outcome IT cred populate
target early June real-calendar。

**Signal goal**:Q15「How often do we update the manuals?」surfaces from real
cohort traffic patterns。Three orthogonal signal axes:

  1. **Frequency** — top-N most-asked queries within a week → high-volume
     topics need accurate / up-to-date manual coverage(stale manual = bad UX
     amplified by traffic)
  2. **Refusal-but-answerable** — queries that triggered OOS refusal but the
     phrasing is plausibly in-scope → manual coverage gap signal
  3. **CRAG-triggered + 👎 feedback** — answer needed mid-stream rewrite OR
     user explicitly disliked → ambiguity / outdated content signal

Pipeline:
    query_collector YAML(real query corpus)
      + feedback YAML(👍/👎 + comment;PII-stripped)
        → ISO-week bucketing(2026-W23 etc。)
        → top-N selection per signal axis
        → weekly Markdown report

W11+ scope:
  - Hook live Langfuse generations API for trace-id ↔ feedback correlation
    (currently offline YAML bootstrap matches W9 D3 query_collector pattern)
  - Hook bug report Slack `#ekp-beta` channel scrape for "outdated" /
    "old version" mention frequency

Karpathy §1.2 simplicity-first:
  - **No live API fetch** — offline YAML inputs;real cohort traffic plumbs
    in W11+ post-IT-cred populate
  - **No clustering / NLP topic modelling** — top-N by raw frequency / hash
    counts(SME spots patterns post-report read)
  - **No DB layer** — Markdown-on-disk output;git history audit trail +
    zero infra dep matches `query_collector` precedent
  - **Feedback comment PII strip** — re-uses `query_collector.pii_strip`
    so H5 H5 redaction stays consistent across observability modules
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from observability.query_collector import (
    RealQueryRecord,
    pii_strip,
)
from observability.query_collector import read_yaml as read_query_corpus

# ---------------------------------------------------------------------------
# Feedback schema(parallel to query_collector.RealQueryRecord)
# ---------------------------------------------------------------------------


class FeedbackRecord(BaseModel):
    """One per-answer 👍/👎 event from a Beta cohort user。

    Schema parallels `feedback.py` + `feedback_received` structlog event
    (`/feedback` endpoint W8 D5 F5.3)+ adds optional `query_hash` for
    cross-join with `query_collector` corpus(populated when the
    `/query` route is wired to emit query_hash into the trace tag set
    W11+)。
    """

    feedback_id: str = Field(..., description="uuid4 from /feedback POST")
    trace_id: str
    timestamp: str = Field(..., description="ISO 8601 UTC e.g. 2026-06-03T10:15:00Z")
    rating: str = Field(..., description="thumbs_up | thumbs_down")
    comment: str | None = Field(None, description="PII-stripped optional comment")
    query_hash: str | None = Field(
        None,
        description="Optional join key into RealQueryRecord(W11+ when wired)",
    )
    user_oid_redacted: str = Field(..., description="4-char user-ID slug — H5 redaction")


# ---------------------------------------------------------------------------
# Aggregation dataclass
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class TopQuery:
    """One entry in a top-N signal list — text + count + provenance hash。"""

    query_text: str
    query_hash: str
    count: int


@dataclass(slots=True)
class WeeklyAggregation:
    """One ISO-week bucket of cohort signal across query + feedback corpora。"""

    iso_week: str  # e.g. "2026-W23"
    total_queries: int = 0
    refused_queries: int = 0
    crag_triggered: int = 0
    total_feedback: int = 0
    thumbs_down: int = 0
    thumbs_up: int = 0
    top_frequent: list[TopQuery] = field(default_factory=list)
    top_refused: list[TopQuery] = field(default_factory=list)
    top_crag: list[TopQuery] = field(default_factory=list)
    top_negative_feedback: list[tuple[str, str]] = field(default_factory=list)
    # ↑ list of (query_text or "(unknown)", PII-stripped comment preview)


# ---------------------------------------------------------------------------
# ISO-week helpers
# ---------------------------------------------------------------------------


def parse_iso_week(timestamp: str) -> str:
    """Map an ISO-8601 timestamp to an ISO-week label `YYYY-Www`。

    Accepts `2026-06-03T10:15:00Z` / `2026-06-03T10:15:00+00:00` /
    `2026-06-03` shapes(query_collector emits the `Z` suffix variant)。
    Raises `ValueError` on unparseable input(callers expected to filter
    out-of-spec records before aggregation)。
    """
    cleaned = timestamp.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    dt = datetime.fromisoformat(cleaned)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    iso_year, iso_week, _ = dt.date().isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def current_iso_week(today: date | None = None) -> str:
    """Convenience for CLI default — `today.isocalendar()` formatted。"""
    d = today or datetime.now(UTC).date()
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


# ---------------------------------------------------------------------------
# Aggregation core
# ---------------------------------------------------------------------------


def _bucket_records_by_week(
    records: Iterable[RealQueryRecord],
) -> dict[str, list[RealQueryRecord]]:
    """Partition query records into ISO-week buckets;skip parse-failed rows。"""
    buckets: dict[str, list[RealQueryRecord]] = {}
    for record in records:
        try:
            week = parse_iso_week(record.timestamp)
        except (ValueError, TypeError):
            continue
        buckets.setdefault(week, []).append(record)
    return buckets


def _bucket_feedback_by_week(
    feedback: Iterable[FeedbackRecord],
) -> dict[str, list[FeedbackRecord]]:
    buckets: dict[str, list[FeedbackRecord]] = {}
    for record in feedback:
        try:
            week = parse_iso_week(record.timestamp)
        except (ValueError, TypeError):
            continue
        buckets.setdefault(week, []).append(record)
    return buckets


def _top_queries_by_count(
    records: list[RealQueryRecord], *, top_n: int
) -> list[TopQuery]:
    """Order by(count desc, first-seen text)— stable across runs。"""
    if not records:
        return []
    counts: Counter[str] = Counter(r.query_hash for r in records)
    text_for_hash: dict[str, str] = {}
    for r in records:
        text_for_hash.setdefault(r.query_hash, r.query_text)
    ranked = counts.most_common(top_n)
    return [
        TopQuery(query_text=text_for_hash[h], query_hash=h, count=n)
        for h, n in ranked
    ]


def _top_negative_feedback(
    feedback: list[FeedbackRecord],
    query_text_for_hash: dict[str, str],
    *,
    top_n: int,
    comment_preview_chars: int = 80,
) -> list[tuple[str, str]]:
    """Surface up to `top_n` thumbs_down feedback with PII-stripped comment。"""
    negatives = [f for f in feedback if f.rating == "thumbs_down"]
    out: list[tuple[str, str]] = []
    for f in negatives[:top_n]:
        text = "(unknown)"
        if f.query_hash and f.query_hash in query_text_for_hash:
            text = query_text_for_hash[f.query_hash]
        comment = pii_strip(f.comment or "")
        if len(comment) > comment_preview_chars:
            comment = comment[:comment_preview_chars] + "…"
        out.append((text, comment or "(no comment)"))
    return out


def aggregate_week(
    iso_week: str,
    query_records: list[RealQueryRecord],
    feedback_records: list[FeedbackRecord],
    *,
    top_n: int = 10,
) -> WeeklyAggregation:
    """Build one `WeeklyAggregation` from already-bucketed records。"""
    refused = [r for r in query_records if r.refused]
    crag = [r for r in query_records if r.crag_triggered]
    text_for_hash: dict[str, str] = {}
    for r in query_records:
        text_for_hash.setdefault(r.query_hash, r.query_text)

    return WeeklyAggregation(
        iso_week=iso_week,
        total_queries=len(query_records),
        refused_queries=len(refused),
        crag_triggered=len(crag),
        total_feedback=len(feedback_records),
        thumbs_down=sum(1 for f in feedback_records if f.rating == "thumbs_down"),
        thumbs_up=sum(1 for f in feedback_records if f.rating == "thumbs_up"),
        top_frequent=_top_queries_by_count(query_records, top_n=top_n),
        top_refused=_top_queries_by_count(refused, top_n=top_n),
        top_crag=_top_queries_by_count(crag, top_n=top_n),
        top_negative_feedback=_top_negative_feedback(
            feedback_records, text_for_hash, top_n=top_n
        ),
    )


def aggregate_all_weeks(
    query_records: list[RealQueryRecord],
    feedback_records: list[FeedbackRecord],
    *,
    week_filter: str | None = None,
    top_n: int = 10,
) -> list[WeeklyAggregation]:
    """Bucket both corpora by ISO-week,emit aggregation per week。

    Args:
        week_filter: When set,return only the matching week(empty list if
            no records hit that bucket)。Default emits every week present
            across either corpus,sorted ascending。
    """
    query_buckets = _bucket_records_by_week(query_records)
    feedback_buckets = _bucket_feedback_by_week(feedback_records)
    weeks_present = sorted(set(query_buckets) | set(feedback_buckets))
    if week_filter is not None:
        weeks_present = [w for w in weeks_present if w == week_filter]
    return [
        aggregate_week(
            week,
            query_buckets.get(week, []),
            feedback_buckets.get(week, []),
            top_n=top_n,
        )
        for week in weeks_present
    ]


# ---------------------------------------------------------------------------
# YAML feedback corpus reader
# ---------------------------------------------------------------------------


def read_feedback_yaml(path: Path) -> tuple[dict[str, Any], list[FeedbackRecord]]:
    """Read feedback corpus YAML;mirror `query_collector.read_yaml` shape。"""
    text = path.read_text(encoding="utf-8")
    payload = yaml.safe_load(text) or {}
    metadata = payload.get("collection_metadata", {})
    raw_records = payload.get("feedback_records", [])
    records: list[FeedbackRecord] = []
    for raw in raw_records:
        ts = raw.get("timestamp")
        if isinstance(ts, datetime):
            raw = {**raw, "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ")}
        records.append(FeedbackRecord(**raw))
    return metadata, records


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def _render_top_section(heading: str, items: list[TopQuery]) -> list[str]:
    """Build one `## heading` + bullet list block。"""
    lines = [f"## {heading}", ""]
    if not items:
        lines.append("_(no entries this week)_")
    else:
        for top in items:
            preview = top.query_text if len(top.query_text) <= 100 else top.query_text[:100] + "…"
            lines.append(f"- **{top.count}×** — `{top.query_hash[:12]}` — {preview}")
    lines.append("")
    return lines


def render_markdown(aggregations: list[WeeklyAggregation]) -> str:
    """Render a list of `WeeklyAggregation` into a single Markdown report。

    Format(per Q15 governance signal review pattern):
        # EKP Beta Cohort — Weekly Signal Report

        > Auto-generated by `weekly_signal_report.py`(W10 D2 F4.3 scaffold)。
        > Q15 manual update frequency signal source。

        ## ISO Week 2026-W23

        ### Volume Summary
        - Total queries: 42
        - Refused: 3
        - CRAG-triggered: 7
        - Feedback: 12(👍 9 / 👎 3)

        ### Top Frequent Queries
        - **5×** — `5b1a7f3c8e9d` — How do I configure the printer for...
        ...

        ### Refusal Cluster
        - **2×** — `0a6f2c8d3e4f` — What is the airspeed velocity...

        ### CRAG-Triggered Cluster
        - **3×** — `6c2b8e4d9f0a` — 點樣 reset 個 Ricoh MP C5503 嘅密碼?

        ### Negative Feedback
        - "Reset password procedure" — outdated UI screenshot for v2.1
        ...
    """
    lines: list[str] = [
        "# EKP Beta Cohort — Weekly Signal Report",
        "",
        "> Auto-generated by `backend/observability/weekly_signal_report.py`"
        "(W10 D2 F4.3 scaffold)。",
        "> **Purpose**:Q15 manual update frequency signal source — top-N "
        "patterns surface manual coverage gaps + outdated content + "
        "ambiguity hotspots。SME reviews weekly + decides which manual "
        "section needs refresh。",
        "> **Privacy**:query text PII-stripped via `query_collector.pii_strip`;"
        "feedback comment re-stripped at render time(belt-and-braces H5)。",
        "",
    ]

    if not aggregations:
        lines.extend(["_(no records found in supplied corpora)_", ""])
        return "\n".join(lines)

    for agg in aggregations:
        lines.append(f"## ISO Week {agg.iso_week}")
        lines.append("")
        lines.append("### Volume Summary")
        lines.append("")
        lines.append(f"- Total queries:**{agg.total_queries}**")
        lines.append(f"- Refused:{agg.refused_queries}")
        lines.append(f"- CRAG-triggered:{agg.crag_triggered}")
        lines.append(
            f"- Feedback:{agg.total_feedback}"
            f"(👍 {agg.thumbs_up} / 👎 {agg.thumbs_down})"
        )
        lines.append("")
        lines.extend(_render_top_section("Top Frequent Queries", agg.top_frequent))
        lines.extend(_render_top_section("Refusal Cluster", agg.top_refused))
        lines.extend(_render_top_section("CRAG-Triggered Cluster", agg.top_crag))
        lines.append("### Negative Feedback")
        lines.append("")
        if not agg.top_negative_feedback:
            lines.append("_(no thumbs_down this week)_")
        else:
            for query_text, comment in agg.top_negative_feedback:
                preview = query_text if len(query_text) <= 80 else query_text[:80] + "…"
                lines.append(f"- _{preview}_ — {comment}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="weekly-signal-report",
        description=(
            "Aggregate query_collector + feedback corpora into a weekly "
            "Markdown signal report(W10 D2 F4.3 — Q15 manual update "
            "frequency scaffold)。"
        ),
    )
    parser.add_argument(
        "--queries",
        required=True,
        type=Path,
        help="query_collector YAML(produced by RealQueryRecord pipeline)",
    )
    parser.add_argument(
        "--feedback",
        type=Path,
        default=None,
        help="Feedback YAML(optional;omit when no feedback corpus available)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output Markdown path;default = stdout",
    )
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help="Filter to single ISO week e.g. 2026-W23(default = all weeks present)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Top-N items per signal axis(default 10)",
    )
    args = parser.parse_args(argv)

    try:
        _, query_records = read_query_corpus(args.queries)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    feedback_records: list[FeedbackRecord] = []
    if args.feedback is not None:
        try:
            _, feedback_records = read_feedback_yaml(args.feedback)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    aggregations = aggregate_all_weeks(
        query_records,
        feedback_records,
        week_filter=args.week,
        top_n=args.top_n,
    )
    report = render_markdown(aggregations)

    if args.output is not None:
        args.output.write_text(report, encoding="utf-8")
        print(
            f"Wrote weekly signal report to {args.output}"
            f"({len(aggregations)} week-bucket(s))",
            file=sys.stderr,
        )
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""C06 Eval Framework — eval-set augmentation pipeline(W10 D1 F4.2).

Per W10 plan §2 F4.2 + architecture.md §6.1 W4 D5 pattern of「加 20 條 real query
into eval set」+ W9 D3 carry-over「Live query collection plumbing」。

Pipeline:
    real query corpus(query_collector YAML)
        → candidate eval-set entries(SME-validation stubs)
        → dedup against existing eval set canonical hashes
        → emit augmented eval-set YAML(new file,never overwrite source)

Karpathy §1.2 simplicity-first:
  - **No LLM-driven topic classification**:`query_type` defaults to
    `single_step_lookup`(or `oos` when `refused=True`);SME refines。
  - **No difficulty heuristic**:left empty for SME annotation。
  - **No in-place overwrite**:always write to `--output` path so the
    SME-validated source stays preserved + diff is review-friendly。
  - **No external API**:relies on `query_collector.read_yaml` + PyYAML only。

CLI:
    python -m eval.eval_set_augmentor \\
        --eval-set docs/eval-set-v1-draft.yaml \\
        --real-corpus docs/03-implementation/beta-real-queries-W9-W10.yaml \\
        --output docs/eval-set-v1-draft-augmented-W10.yaml \\
        [--dry-run]                  # preview report without writing output
        [--start-qid 56]             # default = max existing + 1

W11+ scope:
  - Hook augmented eval-set as input to RAGAs runner for replay regression
    (`backend/eval/runner.py`)。
  - SME validation cascade per `eval-methodology.md §4`:Chris reviews each
    candidate,fills `acceptable_chunk_ids` + `validated=true` + flips file
    name to `eval-set-v2.yaml`(per `eval-set-v1-draft.yaml` header line 30
    cascade pattern)。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from observability.query_collector import RealQueryRecord
from observability.query_collector import read_yaml as read_real_corpus

_QID_PATTERN = re.compile(r"^Q(\d+)$")


@dataclass(slots=True, frozen=True)
class CandidateOutcome:
    """One real-query record's fate during augmentation."""

    query_text: str
    canonical_hash: str
    accepted: bool
    reason: str  # "added" | "duplicate_of_existing" | "duplicate_within_corpus"
    assigned_qid: str | None = None  # None when not accepted


@dataclass(slots=True, frozen=True)
class MergeReport:
    """Aggregate stats from one augmentation run。"""

    eval_set_path: str
    real_corpus_path: str
    output_path: str | None  # None when dry-run
    existing_count: int
    candidate_count: int
    added_count: int
    duplicate_against_existing: int
    duplicate_within_corpus: int
    next_qid: str  # next available id AFTER this run
    outcomes: list[CandidateOutcome] = field(default_factory=list)
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Hashing — must match query_collector canonicalisation rules
# ---------------------------------------------------------------------------


def _canonical(text: str) -> str:
    """Lowercase + collapse whitespace + strip — matches `query_collector._canonical`。

    Duplicated here(rather than imported as private)to keep the augmentor's
    dedup contract visible alongside its own logic;both functions must move
    in lockstep if canonicalisation rules change(see test guard
    `test_augmentor_canonical_matches_query_collector`)。
    """
    return " ".join(text.lower().split()).strip()


def _query_hash(text: str) -> str:
    return hashlib.sha256(_canonical(text).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Eval-set parsing helpers
# ---------------------------------------------------------------------------


def load_eval_set(path: Path) -> dict[str, Any]:
    """Read eval-set YAML preserving full structure for round-trip。"""
    text = path.read_text(encoding="utf-8")
    payload = yaml.safe_load(text) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"eval-set root must be a mapping;got {type(payload).__name__}")
    if "queries" not in payload or not isinstance(payload["queries"], list):
        raise ValueError("eval-set missing `queries` list")
    return payload


def existing_query_hashes(eval_set: dict[str, Any]) -> set[str]:
    """Hash existing queries by canonical text for dedup against real corpus。"""
    hashes: set[str] = set()
    for entry in eval_set.get("queries", []):
        text = entry.get("query_text", "")
        if isinstance(text, str) and text.strip():
            hashes.add(_query_hash(text))
    return hashes


def next_query_id(eval_set: dict[str, Any]) -> int:
    """Compute `max(existing query_id numeric prefix) + 1`,defaulting to 1。"""
    max_seen = 0
    for entry in eval_set.get("queries", []):
        qid = str(entry.get("query_id", ""))
        match = _QID_PATTERN.match(qid)
        if match:
            max_seen = max(max_seen, int(match.group(1)))
    return max_seen + 1


# ---------------------------------------------------------------------------
# Candidate construction
# ---------------------------------------------------------------------------


def _format_qid(n: int) -> str:
    """Three-zero-padded format matching v1-draft convention(Q001..Q999)。"""
    return f"Q{n:03d}"


def _classify_query_type(record: RealQueryRecord) -> str:
    """Heuristic default — refusal → oos;else single_step_lookup(SME refines)。"""
    return "oos" if record.refused else "single_step_lookup"


def build_candidate(
    record: RealQueryRecord,
    *,
    query_id: str,
    phrasing_source: str = "real_user_W10",
) -> dict[str, Any]:
    """Convert one `RealQueryRecord` into an eval-set entry stub。

    Produces the schema enforced by `eval-set-v1-draft.yaml` Q001+ entries:
      - ground_truth chunk_ids left empty(SME populates)
      - expected_answer_keywords left empty(SME populates)
      - expected_refusal mirrors `record.refused`(seed for SME confirm)
      - annotation.validated=False;notes embed corpus provenance fields
    """
    notes = (
        f"W10 augment from query_collector real corpus "
        f"| hash={record.query_hash[:12]} "
        f"| duration_ms={record.duration_ms} "
        f"| crag_triggered={record.crag_triggered} "
        f"| user_oid_redacted={record.user_oid_redacted}"
    )
    return {
        "query_id": query_id,
        "query_text": record.query_text,
        "query_phrasing_source": phrasing_source,
        "difficulty": "",
        "query_type": _classify_query_type(record),
        "ground_truth": {
            "primary_chunk_ids": [],
            "acceptable_chunk_ids": [],
            "expected_screenshot_chunks": [],
            "expected_answer_keywords": [],
            "expected_refusal": bool(record.refused),
        },
        "annotation": {
            "annotator": "",
            "annotated_at": "",
            "validated": False,
            "notes": notes,
        },
    }


# ---------------------------------------------------------------------------
# Merge driver
# ---------------------------------------------------------------------------


def _augmentation_metadata(
    *,
    real_corpus_path: Path,
    real_corpus_meta: dict[str, Any],
    added_count: int,
) -> dict[str, Any]:
    """Header block describing the augmentation run for the augmented file。"""
    return {
        "augmented_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "augmentation_source": str(real_corpus_path),
        "augmentation_phase": real_corpus_meta.get("phase", "unknown"),
        "added_count": added_count,
        "spec_ref": "W10 plan §2 F4.2 + architecture.md §6.1 W4 D5 augmentation pattern",
    }


def merge(
    *,
    eval_set_path: Path,
    real_corpus_path: Path,
    output_path: Path | None,
    dry_run: bool = False,
    start_qid: int | None = None,
) -> MergeReport:
    """Build augmented eval-set + (optionally) write to `output_path`。

    Args:
        eval_set_path: Source eval-set YAML(read-only;never modified)。
        real_corpus_path: query_collector YAML produced by Beta cohort flow。
        output_path: Target file for augmented YAML(must differ from source);
            ignored when `dry_run=True`。
        dry_run: Skip write;report-only run for stakeholder preview。
        start_qid: Override numeric start for new query_ids;default
            `next_query_id(eval_set) → max + 1`。

    Returns:
        MergeReport with per-record outcomes + aggregate stats。

    Raises:
        ValueError: when output_path equals eval_set_path(prevents overwrite),
            or eval-set malformed,or both source files cannot be parsed。
    """
    eval_set_path = Path(eval_set_path)
    real_corpus_path = Path(real_corpus_path)

    if not dry_run:
        if output_path is None:
            raise ValueError("output_path is required when dry_run is False")
        output_path = Path(output_path)
        if output_path.resolve() == eval_set_path.resolve():
            raise ValueError(
                "output_path must differ from eval_set_path to prevent overwrite"
            )

    eval_set = load_eval_set(eval_set_path)
    existing_hashes = existing_query_hashes(eval_set)
    real_meta, real_records = read_real_corpus(real_corpus_path)

    next_n = start_qid if start_qid is not None else next_query_id(eval_set)
    seen_within_corpus: set[str] = set()
    outcomes: list[CandidateOutcome] = []
    new_entries: list[dict[str, Any]] = []
    dup_existing = 0
    dup_within = 0

    for record in real_records:
        canonical_hash = _query_hash(record.query_text)
        if canonical_hash in existing_hashes:
            outcomes.append(
                CandidateOutcome(
                    query_text=record.query_text,
                    canonical_hash=canonical_hash,
                    accepted=False,
                    reason="duplicate_of_existing",
                )
            )
            dup_existing += 1
            continue
        if canonical_hash in seen_within_corpus:
            outcomes.append(
                CandidateOutcome(
                    query_text=record.query_text,
                    canonical_hash=canonical_hash,
                    accepted=False,
                    reason="duplicate_within_corpus",
                )
            )
            dup_within += 1
            continue

        qid = _format_qid(next_n)
        next_n += 1
        new_entries.append(build_candidate(record, query_id=qid))
        seen_within_corpus.add(canonical_hash)
        outcomes.append(
            CandidateOutcome(
                query_text=record.query_text,
                canonical_hash=canonical_hash,
                accepted=True,
                reason="added",
                assigned_qid=qid,
            )
        )

    if not dry_run and new_entries:
        augmented = dict(eval_set)
        augmented["queries"] = list(eval_set["queries"]) + new_entries
        augmented["augmentation"] = _augmentation_metadata(
            real_corpus_path=real_corpus_path,
            real_corpus_meta=real_meta,
            added_count=len(new_entries),
        )
        text = yaml.safe_dump(
            augmented,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
        assert output_path is not None  # noqa: S101 — guarded above
        output_path.write_text(text, encoding="utf-8")
    elif not dry_run and not new_entries:
        # No-op write avoided — surface a clear marker so the caller knows
        # output file was NOT created
        output_path = None

    # Truthfully reflect whether a file was written:dry-run never writes,
    # and a no-candidate full run skips the write,so report None in both cases。
    reported_output: str | None = None
    if not dry_run and new_entries and output_path is not None:
        reported_output = str(output_path)

    return MergeReport(
        eval_set_path=str(eval_set_path),
        real_corpus_path=str(real_corpus_path),
        output_path=reported_output,
        existing_count=len(eval_set["queries"]),
        candidate_count=len(real_records),
        added_count=len(new_entries),
        duplicate_against_existing=dup_existing,
        duplicate_within_corpus=dup_within,
        next_qid=_format_qid(next_n),
        outcomes=outcomes,
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------


def _format_report(report: MergeReport) -> str:
    """Human-readable run summary for CLI stdout。"""
    lines = [
        "Eval-set augmentation report",
        "=" * 60,
        f"  Source eval-set:    {report.eval_set_path}",
        f"  Real query corpus:  {report.real_corpus_path}",
        f"  Output target:      {report.output_path or '(dry-run — no write)'}",
        f"  Existing queries:   {report.existing_count}",
        f"  Candidate records:  {report.candidate_count}",
        f"  Added:              {report.added_count}",
        f"  Duplicates(existing):    {report.duplicate_against_existing}",
        f"  Duplicates(within corpus): {report.duplicate_within_corpus}",
        f"  Next available qid: {report.next_qid}",
        "-" * 60,
    ]
    for outcome in report.outcomes:
        prefix = "+" if outcome.accepted else "-"
        qid_marker = f" → {outcome.assigned_qid}" if outcome.assigned_qid else ""
        text_preview = outcome.query_text[:60] + ("…" if len(outcome.query_text) > 60 else "")
        lines.append(f"  {prefix} [{outcome.reason:>26}]{qid_marker}  {text_preview}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="eval-set-augmentor",
        description=(
            "Merge query_collector real query corpus into an eval-set as "
            "SME-validation candidate stubs(W10 D1 F4.2)。"
        ),
    )
    parser.add_argument("--eval-set", required=True, type=Path, help="Source eval-set YAML")
    parser.add_argument("--real-corpus", required=True, type=Path, help="query_collector YAML")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Augmented eval-set output path(required unless --dry-run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report-only;skip write",
    )
    parser.add_argument(
        "--start-qid",
        type=int,
        default=None,
        help="Override numeric start for new qids(default = max existing + 1)",
    )
    args = parser.parse_args(argv)

    if not args.dry_run and args.output is None:
        parser.error("--output is required unless --dry-run is set")

    try:
        report = merge(
            eval_set_path=args.eval_set,
            real_corpus_path=args.real_corpus,
            output_path=args.output,
            dry_run=args.dry_run,
            start_qid=args.start_qid,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(_format_report(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())

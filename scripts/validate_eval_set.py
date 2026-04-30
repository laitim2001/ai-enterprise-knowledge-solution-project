"""Eval set v0 validator (per docs/eval-set-v0.yaml step 5e + eval-methodology.md).

Sanity-check the eval set YAML against the schema + cross-field invariants.
Used by SME workflow when promoting v0 placeholder → v1 SME-validated.

Usage (run from repo root):
    backend/.venv/Scripts/python.exe -m scripts.validate_eval_set docs/eval-set-v0.yaml

Exit codes:
    0  All checks passed
    1  Schema / structural error
    2  Validation rule failure (counts / duplicates / OOS rules)

Stdlib + pyyaml only (no pydantic dep, runs even when backend deps are partially installed).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_VALID_DIFFICULTIES = {"easy", "medium", "hard", "n_a_oos"}
_VALID_QUERY_TYPES = {"single_step_lookup", "multi_step_synthesis", "troubleshooting", "oos"}


@dataclass
class GroundTruth:
    primary_chunk_ids: list[str] = field(default_factory=list)
    acceptable_chunk_ids: list[str] = field(default_factory=list)
    expected_screenshot_chunks: list[str] = field(default_factory=list)
    expected_answer_keywords: list[str] = field(default_factory=list)
    expected_refusal: bool = False


@dataclass
class Annotation:
    annotator: str = ""
    annotated_at: str = ""
    validated: bool = False
    notes: str = ""


@dataclass
class Query:
    query_id: str
    query_text: str
    query_phrasing_source: str
    difficulty: str | None
    query_type: str
    ground_truth: GroundTruth
    annotation: Annotation


def _coerce_query(raw: dict[str, Any]) -> Query:
    diff = raw.get("difficulty")
    return Query(
        query_id=str(raw["query_id"]),
        query_text=str(raw["query_text"]),
        query_phrasing_source=str(raw.get("query_phrasing_source", "synthetic")),
        difficulty=str(diff) if diff is not None else None,
        query_type=str(raw["query_type"]),
        ground_truth=GroundTruth(**raw.get("ground_truth", {})),
        annotation=Annotation(**raw.get("annotation", {})),
    )


def validate(yaml_path: Path) -> list[str]:
    """Return list of issue strings (empty = all checks pass)."""
    issues: list[str] = []

    if not yaml_path.exists():
        return [f"file not found: {yaml_path}"]

    with yaml_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    metadata = data.get("metadata", {})
    raw_queries = data.get("queries", [])

    try:
        queries = [_coerce_query(q) for q in raw_queries]
    except (KeyError, TypeError) as e:
        return [f"schema error parsing queries: {e}"]

    declared_total = metadata.get("total_queries")
    if declared_total is not None and declared_total != len(queries):
        issues.append(
            f"metadata.total_queries={declared_total} but len(queries)={len(queries)}",
        )

    composition = metadata.get("composition", {})
    expected_total = (
        composition.get("synthetic_main", 0)
        + composition.get("synthetic_oos", 0)
        + composition.get("user_collected", 0)
    )
    if expected_total and expected_total != len(queries):
        issues.append(
            f"composition sum={expected_total} but len(queries)={len(queries)}",
        )

    seen_ids: set[str] = set()
    for q in queries:
        if q.query_id in seen_ids:
            issues.append(f"duplicate query_id: {q.query_id}")
        seen_ids.add(q.query_id)

        if q.difficulty is None and q.query_type != "oos":
            issues.append(
                f"{q.query_id}: non-oos query must have difficulty set "
                f"(expected one of {sorted(_VALID_DIFFICULTIES)})",
            )
        elif q.difficulty is not None and q.difficulty not in _VALID_DIFFICULTIES:
            issues.append(
                f"{q.query_id}: invalid difficulty '{q.difficulty}' "
                f"(expected one of {sorted(_VALID_DIFFICULTIES)} or null for oos)",
            )
        if q.query_type not in _VALID_QUERY_TYPES:
            issues.append(
                f"{q.query_id}: invalid query_type '{q.query_type}' "
                f"(expected one of {sorted(_VALID_QUERY_TYPES)})",
            )

        if q.query_type == "oos" and not q.ground_truth.expected_refusal:
            issues.append(f"{q.query_id}: oos query must have expected_refusal=true")
        if q.query_type != "oos" and not q.ground_truth.primary_chunk_ids:
            issues.append(
                f"{q.query_id}: non-oos query must have ≥1 primary_chunk_id",
            )

    return issues


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: python -m scripts.validate_eval_set <path-to-yaml>", file=sys.stderr)
        return 2
    yaml_path = Path(argv[1])
    issues = validate(yaml_path)

    if not issues:
        print(f"OK: {yaml_path} passed all validation checks")
        return 0

    print(f"FAIL: {yaml_path} has {len(issues)} issue(s):", file=sys.stderr)
    for issue in issues:
        print(f"  - {issue}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

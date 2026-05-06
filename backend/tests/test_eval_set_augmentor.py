"""W10 D1 F4.2 — eval-set augmentation pipeline coverage.

Per W10 plan §2 F4.2 acceptance:
  - Real query corpus(`query_collector` YAML)→ eval-set candidate stubs
  - Dedup against existing eval-set + within corpus
  - Dry-run preview yields report without writing
  - Augmented YAML round-trip(load → augmentation header + new entries)
  - Refuse to overwrite source eval-set(safety guard for SME-validated content)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from eval.eval_set_augmentor import (
    MergeReport,
    _canonical,
    _query_hash,
    build_candidate,
    existing_query_hashes,
    main,
    merge,
    next_query_id,
)
from observability.query_collector import (
    RealQueryRecord,
    build_record,
)
from observability.query_collector import _canonical as collector_canonical
from observability.query_collector import (
    write_yaml as write_real_corpus,
)

# ---------------------------------------------------------------------------
# Hash function alignment with query_collector
# ---------------------------------------------------------------------------


def test_canonical_matches_query_collector() -> None:
    """Guard rule:augmentor + query_collector canonicalisation MUST agree。

    If this drifts,dedup against existing eval-set queries will silently
    diverge from query_hash stored in the real corpus,leading to false
    positives / negatives in the augmentation pipeline。
    """
    samples = [
        "How do I print double-sided?",
        "  HOW DO I PRINT  Double-Sided?  ",
        "如何 reset 個 printer 嘅密碼?",
    ]
    for s in samples:
        assert _canonical(s) == collector_canonical(s)


# ---------------------------------------------------------------------------
# Eval-set parsing helpers
# ---------------------------------------------------------------------------


def _make_minimal_eval_set(query_ids: list[str], texts: list[str]) -> dict:
    """Tiny eval-set fixture with only fields the augmentor cares about。"""
    assert len(query_ids) == len(texts)
    return {
        "metadata": {"version": "test", "total_queries": len(query_ids)},
        "queries": [
            {
                "query_id": qid,
                "query_text": text,
                "query_phrasing_source": "synthetic",
                "difficulty": "easy",
                "query_type": "single_step_lookup",
                "ground_truth": {
                    "primary_chunk_ids": [],
                    "acceptable_chunk_ids": [],
                    "expected_screenshot_chunks": [],
                    "expected_answer_keywords": [],
                    "expected_refusal": False,
                },
                "annotation": {
                    "annotator": "",
                    "annotated_at": "",
                    "validated": False,
                    "notes": "",
                },
            }
            for qid, text in zip(query_ids, texts, strict=True)
        ],
    }


def test_existing_query_hashes_collects_all_queries() -> None:
    eval_set = _make_minimal_eval_set(
        ["Q001", "Q002"],
        ["First query?", "Second query?"],
    )
    hashes = existing_query_hashes(eval_set)
    assert _query_hash("First query?") in hashes
    assert _query_hash("Second query?") in hashes
    assert len(hashes) == 2


def test_next_query_id_default_one_when_empty() -> None:
    eval_set = {"queries": []}
    assert next_query_id(eval_set) == 1


def test_next_query_id_skips_non_qid_format() -> None:
    eval_set = {
        "queries": [
            {"query_id": "Q005"},
            {"query_id": "custom-tag"},  # non-conforming → skipped
            {"query_id": "Q012"},
        ]
    }
    assert next_query_id(eval_set) == 13


# ---------------------------------------------------------------------------
# Candidate construction
# ---------------------------------------------------------------------------


def _make_real_record(text: str, *, refused: bool = False, crag: bool = False) -> RealQueryRecord:
    return build_record(
        query_text=text,
        kb_id="drive_user_manuals",
        user_oid="aaaa-bbbb-cccc-dddd",
        status_code=200,
        duration_ms=1500,
        refused=refused,
        crag_triggered=crag,
        timestamp=datetime(2026, 6, 2, 10, 0, 0, tzinfo=UTC),
    )


def test_build_candidate_schema_matches_v1_draft_shape() -> None:
    record = _make_real_record("How do I clear a paper jam?")
    candidate = build_candidate(record, query_id="Q099")

    assert candidate["query_id"] == "Q099"
    assert candidate["query_text"] == "How do I clear a paper jam?"
    assert candidate["query_phrasing_source"] == "real_user_W10"
    assert candidate["difficulty"] == ""
    assert candidate["query_type"] == "single_step_lookup"
    assert candidate["ground_truth"]["primary_chunk_ids"] == []
    assert candidate["ground_truth"]["acceptable_chunk_ids"] == []
    assert candidate["ground_truth"]["expected_refusal"] is False
    assert candidate["annotation"]["validated"] is False
    assert "W10 augment" in candidate["annotation"]["notes"]
    assert "duration_ms=1500" in candidate["annotation"]["notes"]
    assert "crag_triggered=False" in candidate["annotation"]["notes"]


def test_build_candidate_refused_record_classified_as_oos() -> None:
    record = _make_real_record("Tell me the airspeed velocity of an unladen swallow", refused=True)
    candidate = build_candidate(record, query_id="Q200")
    assert candidate["query_type"] == "oos"
    assert candidate["ground_truth"]["expected_refusal"] is True


# ---------------------------------------------------------------------------
# Merge — dedup behaviour
# ---------------------------------------------------------------------------


def _setup_merge_files(tmp_path: Path, *, eval_texts: list[str], corpus_texts: list[str], refused_flags: list[bool] | None = None) -> tuple[Path, Path]:
    """Write both source files into tmp_path and return paths."""
    eval_set = _make_minimal_eval_set(
        [f"Q{i+1:03d}" for i in range(len(eval_texts))],
        eval_texts,
    )
    eval_path = tmp_path / "eval-set.yaml"
    eval_path.write_text(yaml.safe_dump(eval_set, sort_keys=False, allow_unicode=True), encoding="utf-8")

    refused_flags = refused_flags or [False] * len(corpus_texts)
    records = [_make_real_record(text, refused=refused) for text, refused in zip(corpus_texts, refused_flags, strict=True)]
    corpus_path = tmp_path / "real-corpus.yaml"
    write_real_corpus(records, corpus_path, phase="W10-test", collection_owner="test")
    return eval_path, corpus_path


def test_merge_dedup_against_existing_eval_set(tmp_path: Path) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["How do I print double-sided?"],
        corpus_texts=[
            "  HOW DO I PRINT  Double-Sided?  ",  # canonicalised → matches existing
            "What is the toner replacement procedure?",  # new
        ],
    )
    output_path = tmp_path / "augmented.yaml"
    report = merge(
        eval_set_path=eval_path,
        real_corpus_path=corpus_path,
        output_path=output_path,
    )

    assert report.added_count == 1
    assert report.duplicate_against_existing == 1
    assert report.duplicate_within_corpus == 0
    accepted = [o for o in report.outcomes if o.accepted]
    assert accepted[0].query_text == "What is the toner replacement procedure?"
    assert accepted[0].assigned_qid == "Q002"


def test_merge_dedup_within_corpus(tmp_path: Path) -> None:
    """Two corpus records with same canonical text but different hashes(simulates
    a corpus that bypassed `query_collector.write_yaml` dedup,e.g. ingested
    from a raw audit log stream)。Augmentor's own dedup must catch them。
    """
    eval_path, _ = _setup_merge_files(tmp_path, eval_texts=["Existing query?"], corpus_texts=["throwaway?"])
    corpus_path = tmp_path / "real-corpus-with-internal-dups.yaml"
    # Hand-write to bypass write_yaml's dedup pass — both records canonicalise
    # to the same text but carry distinct stored hashes(only the augmentor's
    # internal canonicalisation should catch the dup)
    corpus_path.write_text(
        """\
collection_metadata:
  phase: W10-test-internal-dup
  collection_owner: test
  privacy_class: Internal
  pii_strip_version: v1
  record_count: 2
  spec_ref: test
queries:
  - query_hash: aa11bb22cc33dd44ee55ff66aa11bb22cc33dd44ee55ff66aa11bb22cc33dd44
    query_text: Brand new query?
    kb_id: drive
    timestamp: 2026-06-02T10:00:00Z
    status_code: 200
    duration_ms: 1500
    refused: false
    crag_triggered: false
    user_oid_redacted: u_aaaa
  - query_hash: bb22cc33dd44ee55ff66aa11bb22cc33dd44ee55ff66aa11bb22cc33dd44ee55
    query_text: BRAND new   QUERY?
    kb_id: drive
    timestamp: 2026-06-02T10:00:00Z
    status_code: 200
    duration_ms: 1500
    refused: false
    crag_triggered: false
    user_oid_redacted: u_bbbb
""",
        encoding="utf-8",
    )

    output_path = tmp_path / "augmented.yaml"
    report = merge(
        eval_set_path=eval_path,
        real_corpus_path=corpus_path,
        output_path=output_path,
    )

    assert report.added_count == 1
    assert report.duplicate_within_corpus == 1
    assert report.duplicate_against_existing == 0


# ---------------------------------------------------------------------------
# Merge — write semantics
# ---------------------------------------------------------------------------


def test_merge_dry_run_skips_write(tmp_path: Path) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["Old"],
        corpus_texts=["New A?", "New B?"],
    )
    output_path = tmp_path / "should-not-exist.yaml"
    report = merge(
        eval_set_path=eval_path,
        real_corpus_path=corpus_path,
        output_path=output_path,
        dry_run=True,
    )

    assert report.dry_run is True
    assert report.output_path is None
    assert report.added_count == 2
    assert not output_path.exists()


def test_merge_writes_augmented_yaml_with_metadata(tmp_path: Path) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["Existing one"],
        corpus_texts=["Real one A?", "Real one B?"],
    )
    output_path = tmp_path / "augmented.yaml"
    report = merge(
        eval_set_path=eval_path,
        real_corpus_path=corpus_path,
        output_path=output_path,
    )

    assert output_path.exists()
    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert len(payload["queries"]) == 3  # 1 existing + 2 added
    assert payload["queries"][0]["query_text"] == "Existing one"
    assert payload["queries"][1]["query_id"] == "Q002"
    assert payload["queries"][2]["query_id"] == "Q003"
    assert payload["augmentation"]["added_count"] == 2
    assert payload["augmentation"]["augmentation_phase"] == "W10-test"
    assert "augmented_at" in payload["augmentation"]
    assert report.next_qid == "Q004"


def test_merge_refuses_overwrite_source(tmp_path: Path) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["Anything"],
        corpus_texts=["x?"],
    )
    with pytest.raises(ValueError, match="must differ"):
        merge(
            eval_set_path=eval_path,
            real_corpus_path=corpus_path,
            output_path=eval_path,  # overwrite attempt
        )


def test_merge_dry_run_does_not_require_output_path(tmp_path: Path) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["x"],
        corpus_texts=["y?"],
    )
    report = merge(
        eval_set_path=eval_path,
        real_corpus_path=corpus_path,
        output_path=None,
        dry_run=True,
    )
    assert report.added_count == 1


def test_merge_no_candidates_skips_write(tmp_path: Path) -> None:
    """Real corpus entirely overlaps existing eval set → no write,output_path None。"""
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["Same one"],
        corpus_texts=["Same one"],
    )
    output_path = tmp_path / "augmented.yaml"
    report = merge(
        eval_set_path=eval_path,
        real_corpus_path=corpus_path,
        output_path=output_path,
    )
    assert report.added_count == 0
    assert report.output_path is None
    assert not output_path.exists()


def test_merge_start_qid_override(tmp_path: Path) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["a"],
        corpus_texts=["new?"],
    )
    output_path = tmp_path / "augmented.yaml"
    report = merge(
        eval_set_path=eval_path,
        real_corpus_path=corpus_path,
        output_path=output_path,
        start_qid=100,
    )
    assert report.outcomes[0].assigned_qid == "Q100"
    assert report.next_qid == "Q101"


def test_merge_preserves_existing_queries_verbatim(tmp_path: Path) -> None:
    """Augmentation MUST NOT mutate existing entries — SME-validated content sacrosanct。"""
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["Original Q1", "Original Q2"],
        corpus_texts=["New one"],
    )
    output_path = tmp_path / "augmented.yaml"
    merge(eval_set_path=eval_path, real_corpus_path=corpus_path, output_path=output_path)

    augmented = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert augmented["queries"][0]["query_text"] == "Original Q1"
    assert augmented["queries"][1]["query_text"] == "Original Q2"


def test_merge_outcomes_one_per_record(tmp_path: Path) -> None:
    """One outcome per surviving record(post `query_collector.write_yaml` dedup)。

    Note:`write_yaml` collapses within-corpus dups at the source layer,so only
    the existing-eval-set dedup path fires here。Within-corpus dedup is
    exercised separately in `test_merge_dedup_within_corpus`(via raw YAML
    fixture that bypasses `write_yaml`)。
    """
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["e"],
        corpus_texts=["a?", "b?", "e"],  # 1 existing dup
    )
    output_path = tmp_path / "augmented.yaml"
    report = merge(eval_set_path=eval_path, real_corpus_path=corpus_path, output_path=output_path)

    assert len(report.outcomes) == 3  # one per surviving record
    accepted = sum(1 for o in report.outcomes if o.accepted)
    assert accepted == report.added_count == 2
    assert report.duplicate_against_existing == 1
    assert report.duplicate_within_corpus == 0


# ---------------------------------------------------------------------------
# CLI surface
# ---------------------------------------------------------------------------


def test_cli_dry_run_exit_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["Existing"],
        corpus_texts=["Fresh real query?"],
    )
    rc = main([
        "--eval-set", str(eval_path),
        "--real-corpus", str(corpus_path),
        "--dry-run",
    ])
    assert rc == 0
    captured = capsys.readouterr()
    assert "Eval-set augmentation report" in captured.out
    assert "Added:              1" in captured.out


def test_cli_missing_output_without_dry_run_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["x"],
        corpus_texts=["y?"],
    )
    with pytest.raises(SystemExit) as exc_info:
        main([
            "--eval-set", str(eval_path),
            "--real-corpus", str(corpus_path),
            # no --output, no --dry-run
        ])
    assert exc_info.value.code == 2


def test_cli_full_run_writes_output(tmp_path: Path) -> None:
    eval_path, corpus_path = _setup_merge_files(
        tmp_path,
        eval_texts=["existing"],
        corpus_texts=["a brand new query?"],
    )
    output_path = tmp_path / "out.yaml"
    rc = main([
        "--eval-set", str(eval_path),
        "--real-corpus", str(corpus_path),
        "--output", str(output_path),
    ])
    assert rc == 0
    assert output_path.exists()
    payload = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert payload["augmentation"]["added_count"] == 1


# ---------------------------------------------------------------------------
# Smoke — MergeReport dataclass exposes documented fields
# ---------------------------------------------------------------------------


def test_merge_report_field_set() -> None:
    """Stable contract for downstream tooling consuming MergeReport。"""
    fields = {
        "eval_set_path",
        "real_corpus_path",
        "output_path",
        "existing_count",
        "candidate_count",
        "added_count",
        "duplicate_against_existing",
        "duplicate_within_corpus",
        "next_qid",
        "outcomes",
        "dry_run",
    }
    assert fields <= set(MergeReport.__dataclass_fields__.keys())

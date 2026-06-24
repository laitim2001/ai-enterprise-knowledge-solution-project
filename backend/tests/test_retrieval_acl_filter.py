"""Retrieval-layer ACL + classification filter injection tests (ADR-0066 / W90 P2.2+P2.3).

The fail-open `allowed_principals` OData clause (P2.2) + the classification-clearance
clause (P2.3) are threaded into every search path that feeds the synthesizer (search /
fetch_by_chunk_ids / fetch_chunks_by_section_path / list_chunks). Covers:

- `_build_acl_filter` shape: None → None (BC + admin = restricted-cleared, no filter);
  list → fail-open ACL disjunction ANDed with the classification clause; empty list
  (no principals → public-only); single-quote escaping
- P2.3 classification clearance: a non-None list (non-admin = internal clearance) always
  appends `(classification eq 'internal' or classification eq null)`; None never does
- Each method's `filter` payload gains both clauses when user_principals passed
- BC: user_principals=None → filter byte-identical to pre-P2.2 (no ACL/classification)

Per CLAUDE.md §5.6 H6 — retrieval critical pipeline test coverage.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from retrieval.hybrid import HybridSearcher, _build_acl_filter


def _mock_response(status_code: int, body: dict[str, Any] | None = None) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.is_success = 200 <= status_code < 300
    response.json = MagicMock(return_value=body or {"value": []})
    response.raise_for_status = MagicMock()
    return response


async def _searcher_with_post(response: MagicMock) -> tuple[HybridSearcher, AsyncMock]:
    searcher = HybridSearcher(
        endpoint="https://test.search.windows.net",
        admin_key="test-key",
        index_name="ekp-kb-drive-v1",
    )
    searcher._client = MagicMock(spec=httpx.AsyncClient)
    post_mock = AsyncMock(return_value=response)
    searcher._client.post = post_mock
    return searcher, post_mock


def _filter_of(post_mock: AsyncMock) -> str:
    payload = json.loads(post_mock.call_args.kwargs["content"])
    return str(payload["filter"])


# ── _build_acl_filter unit ────────────────────────────────────────────────────


# P2.3 — the classification-clearance clause every non-None list appends.
_CLEARANCE = "(classification eq 'internal' or classification eq null)"


def test_build_acl_filter_none_is_no_op() -> None:
    # None = BC path (internal tooling / tests / V4) AND admin (restricted-cleared) →
    # no ACL filter AND no classification restriction (admins see restricted chunks).
    assert _build_acl_filter(None) is None


def test_build_acl_filter_list_is_fail_open_disjunction_with_clearance() -> None:
    clause = _build_acl_filter(["oid-a", "grp-eng"])
    assert clause == (
        "(not allowed_principals/any()"
        " or allowed_principals/any(p: search.in(p, 'oid-a,grp-eng', ',')))"
        f" and {_CLEARANCE}"
    )


def test_build_acl_filter_empty_list_sees_only_public() -> None:
    # A user with zero principals: the second disjunct's search.in('') matches
    # nothing, so only empty-allowed_principals (public) chunks survive — plus the
    # P2.3 internal-clearance restriction.
    clause = _build_acl_filter([])
    assert clause == (
        "(not allowed_principals/any()"
        " or allowed_principals/any(p: search.in(p, '', ',')))"
        f" and {_CLEARANCE}"
    )


def test_build_acl_filter_escapes_single_quotes() -> None:
    clause = _build_acl_filter(["o'brien"])
    assert clause is not None
    assert "search.in(p, 'o''brien', ',')" in clause


# ── P2.3 classification clearance ─────────────────────────────────────────────


def test_build_acl_filter_non_admin_restricts_to_internal() -> None:
    # A non-admin (non-None list = internal clearance) only sees internal / unclassified
    # (null) chunks; restricted chunks are excluded by the appended clearance clause.
    clause = _build_acl_filter(["oid-a"])
    assert clause is not None
    assert clause.endswith(f" and {_CLEARANCE}")
    assert "classification eq 'internal'" in clause
    assert "classification eq null" in clause  # fail-open: null = not-yet-classified


def test_build_acl_filter_admin_none_has_no_classification_clause() -> None:
    # Admins reach the None branch (principals_for_user → None) → NO classification
    # restriction → they see restricted chunks too. Guards against accidentally
    # appending the clearance clause to the admin/BC path.
    assert _build_acl_filter(None) is None


# ── search() main retrieval ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_injects_acl_clause_when_principals_passed() -> None:
    searcher, post_mock = await _searcher_with_post(_mock_response(200, {"value": []}))
    await searcher.search(
        query_text="q",
        query_vector=[0.0] * 1024,
        kb_id="drive_user_manuals",
        user_principals=["oid-a"],
    )
    filter_str = _filter_of(post_mock)
    assert "kb_id eq 'drive_user_manuals'" in filter_str  # kb scope preserved
    assert "enabled eq true" in filter_str  # default filter preserved
    assert "allowed_principals/any(p: search.in(p, 'oid-a', ','))" in filter_str
    assert "not allowed_principals/any()" in filter_str  # fail-open disjunct
    # P2.3 — non-admin caller gets the internal-clearance restriction too.
    assert "classification eq 'internal'" in filter_str


@pytest.mark.asyncio
async def test_search_no_acl_clause_when_principals_none_bc() -> None:
    # BC: admin / internal callers pass None → filter has NO ACL / classification clause.
    searcher, post_mock = await _searcher_with_post(_mock_response(200, {"value": []}))
    await searcher.search(
        query_text="q",
        query_vector=[0.0] * 1024,
        kb_id="drive_user_manuals",
        user_principals=None,
    )
    filter_str = _filter_of(post_mock)
    assert "allowed_principals" not in filter_str
    assert "classification" not in filter_str  # P2.3 — admin/BC sees restricted too
    assert filter_str == "kb_id eq 'drive_user_manuals' and enabled eq true"


# ── fetch_by_chunk_ids (context expansion) ────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_by_chunk_ids_injects_acl_clause() -> None:
    searcher, post_mock = await _searcher_with_post(_mock_response(200, {"value": []}))
    await searcher.fetch_by_chunk_ids(
        ["c1", "c2"], kb_id="drive_user_manuals", user_principals=["oid-a"],
    )
    filter_str = _filter_of(post_mock)
    assert "search.in(chunk_id, 'c1,c2', ',')" in filter_str  # chunk batch preserved
    assert "allowed_principals/any(p: search.in(p, 'oid-a', ','))" in filter_str


@pytest.mark.asyncio
async def test_fetch_by_chunk_ids_no_acl_when_none_bc() -> None:
    searcher, post_mock = await _searcher_with_post(_mock_response(200, {"value": []}))
    await searcher.fetch_by_chunk_ids(["c1"], kb_id="drive_user_manuals")
    assert "allowed_principals" not in _filter_of(post_mock)


# ── fetch_chunks_by_section_path (parent-doc) ─────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_chunks_by_section_path_injects_acl_clause() -> None:
    searcher, post_mock = await _searcher_with_post(_mock_response(200, {"value": []}))
    await searcher.fetch_chunks_by_section_path(
        parent_path=["Doc", "Section 8"],
        doc_id="doc-A",
        kb_id="drive_user_manuals",
        user_principals=["oid-a"],
    )
    filter_str = _filter_of(post_mock)
    assert "section_path/any(s: s eq 'Section 8')" in filter_str  # section preserved
    assert "allowed_principals/any(p: search.in(p, 'oid-a', ','))" in filter_str


# ── list_chunks (citation expansion neighbour fetch) ──────────────────────────


@pytest.mark.asyncio
async def test_list_chunks_injects_acl_clause() -> None:
    searcher, post_mock = await _searcher_with_post(_mock_response(200, {"value": []}))
    await searcher.list_chunks(
        kb_id="drive_user_manuals", doc_id="doc-A", user_principals=["oid-a"],
    )
    filter_str = _filter_of(post_mock)
    assert "doc_id eq 'doc-A'" in filter_str  # doc scope preserved
    assert "allowed_principals/any(p: search.in(p, 'oid-a', ','))" in filter_str


@pytest.mark.asyncio
async def test_list_chunks_no_acl_when_none_bc() -> None:
    # GET listing routes pass None → no ACL filter (P2 = query-path trimming only).
    searcher, post_mock = await _searcher_with_post(_mock_response(200, {"value": []}))
    await searcher.list_chunks(kb_id="drive_user_manuals", doc_id="doc-A")
    assert "allowed_principals" not in _filter_of(post_mock)

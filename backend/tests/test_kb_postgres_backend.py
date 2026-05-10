"""Postgres KB backend CRUD tests (W17 F1 / ADR-0023).

Gated — runs only when **both**:
  - `psycopg` is importable (R8 corp-proxy may block `pip install psycopg[binary]`)
  - `DATABASE_URL` is set (e.g. `postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp`
    — the docker-compose postgres `ekp` DB)
Otherwise the whole module skips — the in-memory `KBStorageBackend` path is
covered by the existing `test_kb*.py` suites, and Tier 1 accepts a DB-less CI
(plan §3 PARTIAL PASS allowance: "manual `docker compose up` smoke suffices").

Manual smoke:
  docker compose -f infrastructure/docker-compose.yml up -d postgres
  docker compose -f infrastructure/docker-compose.yml exec postgres createdb -U langfuse ekp   # if not auto-created
  DATABASE_URL=postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp \
    backend/.venv/Scripts/python.exe -m pytest backend/tests/test_kb_postgres_backend.py -v
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402 — after importorskip

from api.schemas.kb import FailureRecord, KbConfig, KbStatus  # noqa: E402
from kb_management import KBAlreadyExistsError, KBNotFoundError  # noqa: E402
from kb_management.postgres_backend import PostgresKBBackend  # noqa: E402

_DSN = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not _DSN, reason="DATABASE_URL not set — Postgres KB backend tests skipped (Tier 1 PARTIAL PASS)",
)


def _sample_kb(kb_id: str = "test_kb", *, with_failure: bool = False) -> KbStatus:
    return KbStatus(
        kb_id=kb_id,
        name=f"Test KB {kb_id}",
        description="W17 F1 Postgres backend test fixture",
        config=KbConfig(),
        total_documents=2,
        total_chunks=17,
        total_screenshots=3,
        failed_documents=(
            [FailureRecord(doc_id="bad.docx", error="parse boom", failed_at=datetime.now(UTC))]
            if with_failure
            else []
        ),
        last_indexed_at=datetime.now(UTC),
        storage_size_mb=1.25,
    )


@pytest.fixture
async def backend() -> AsyncIterator[PostgresKBBackend]:
    # Clean slate before + after — drop the table so the backend recreates it empty.
    with psycopg.connect(_DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS knowledge_bases")
    yield PostgresKBBackend(_DSN)
    with psycopg.connect(_DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS knowledge_bases")


async def test_create_then_get_roundtrips_all_fields(backend: PostgresKBBackend) -> None:
    kb = _sample_kb(with_failure=True)
    await backend.create(kb)
    got = await backend.get(kb.kb_id)
    assert got.kb_id == kb.kb_id
    assert got.name == kb.name
    assert got.description == kb.description
    assert got.config == kb.config
    assert got.total_documents == 2
    assert got.total_chunks == 17
    assert got.total_screenshots == 3
    assert got.storage_size_mb == pytest.approx(1.25)
    assert len(got.failed_documents) == 1
    assert got.failed_documents[0].doc_id == "bad.docx"
    assert got.failed_documents[0].error == "parse boom"


async def test_create_duplicate_raises_already_exists(backend: PostgresKBBackend) -> None:
    await backend.create(_sample_kb("dup"))
    with pytest.raises(KBAlreadyExistsError):
        await backend.create(_sample_kb("dup"))


async def test_get_missing_raises_not_found(backend: PostgresKBBackend) -> None:
    with pytest.raises(KBNotFoundError):
        await backend.get("nope")


async def test_list_all_returns_created_kbs_sorted(backend: PostgresKBBackend) -> None:
    assert await backend.list_all() == []
    await backend.create(_sample_kb("bbb"))
    await backend.create(_sample_kb("aaa"))
    rows = await backend.list_all()
    assert [r.kb_id for r in rows] == ["aaa", "bbb"]


async def test_update_config_replaces_config(backend: PostgresKBBackend) -> None:
    await backend.create(_sample_kb("cfg"))
    new_cfg = KbConfig(default_top_k=99, default_rerank_k=7)
    updated = await backend.update_config("cfg", new_cfg)
    assert updated.config.default_top_k == 99
    assert updated.config.default_rerank_k == 7
    assert (await backend.get("cfg")).config.default_top_k == 99


async def test_update_config_missing_raises_not_found(backend: PostgresKBBackend) -> None:
    with pytest.raises(KBNotFoundError):
        await backend.update_config("nope", KbConfig())


async def test_update_metadata_partial(backend: PostgresKBBackend) -> None:
    await backend.create(_sample_kb("md"))
    # name only
    r1 = await backend.update_metadata("md", name="Renamed")
    assert r1.name == "Renamed"
    assert r1.description == "W17 F1 Postgres backend test fixture"
    # description only
    r2 = await backend.update_metadata("md", description="new desc")
    assert r2.name == "Renamed"
    assert r2.description == "new desc"
    # both None — no-op, returns current state
    r3 = await backend.update_metadata("md")
    assert r3.name == "Renamed"
    assert r3.description == "new desc"


async def test_update_metadata_missing_raises_not_found(backend: PostgresKBBackend) -> None:
    with pytest.raises(KBNotFoundError):
        await backend.update_metadata("nope", name="x")
    # both-None branch on a missing kb still 404s (via the get() fallthrough)
    with pytest.raises(KBNotFoundError):
        await backend.update_metadata("nope")


async def test_delete_then_get_404(backend: PostgresKBBackend) -> None:
    await backend.create(_sample_kb("del"))
    await backend.delete("del")
    with pytest.raises(KBNotFoundError):
        await backend.get("del")


async def test_delete_missing_raises_not_found(backend: PostgresKBBackend) -> None:
    with pytest.raises(KBNotFoundError):
        await backend.delete("nope")

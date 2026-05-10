"""Postgres users + sessions store CRUD tests (W17 F1 / ADR-0023).

Gated — runs only when **both**:
  - `psycopg` is importable (R8 corp-proxy may block `pip install psycopg[binary]`)
  - `DATABASE_URL` is set (e.g. `postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp`
    — the docker-compose postgres `ekp` DB)
Otherwise the whole module skips — the in-memory `UsersStore` path is covered by
`test_auth_self_register.py`, and Tier 1 accepts a DB-less CI (per ADR-0017
PARTIAL-PASS allowance: "manual `docker compose up` smoke suffices").

Manual smoke:
  docker compose -f infrastructure/docker-compose.yml up -d postgres
  docker compose -f infrastructure/docker-compose.yml exec postgres createdb -U langfuse ekp   # if not auto-created
  DATABASE_URL=postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp \
    backend/.venv/Scripts/python.exe -m pytest backend/tests/test_auth_users_postgres_store.py -v
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest

pytest.importorskip("psycopg")

import psycopg  # noqa: E402 — after importorskip

from api.auth.postgres_users_store import PostgresUsersStore  # noqa: E402
from api.auth.users_store import SessionRecord, UserRecord  # noqa: E402

_DSN = os.environ.get("DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not _DSN, reason="DATABASE_URL not set — Postgres users-store tests skipped (Tier 1 PARTIAL PASS)",
)

_PWD_HASH = "scrypt$dummy$hash$value"  # not a real hash — store layer doesn't verify


def _user(oid: str = "u-1", email: str = "a@example.com", *, verified: bool = False) -> UserRecord:
    return UserRecord(
        oid=oid,
        email=email,
        display_name=f"User {oid}",
        password_hash=_PWD_HASH,
        verified=verified,
        verification_code=None if verified else "123456",
        verification_code_expires_at=None if verified else datetime.now(UTC) + timedelta(hours=24),
        last_resend_at=datetime.now(UTC),
    )


@pytest.fixture
def store() -> Iterator[PostgresUsersStore]:
    # Clean slate before + after — drop both tables so the store recreates them empty.
    with psycopg.connect(_DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS sessions")
        conn.execute("DROP TABLE IF EXISTS users")
    yield PostgresUsersStore(_DSN)
    with psycopg.connect(_DSN, autocommit=True) as conn:
        conn.execute("DROP TABLE IF EXISTS sessions")
        conn.execute("DROP TABLE IF EXISTS users")


def test_add_user_then_get_roundtrips_all_fields(store: PostgresUsersStore) -> None:
    u = _user()
    store.add_user(u)
    by_oid = store.get_user_by_oid("u-1")
    assert by_oid is not None
    assert by_oid.email == "a@example.com"
    assert by_oid.display_name == "User u-1"
    assert by_oid.password_hash == _PWD_HASH
    assert by_oid.verified is False
    assert by_oid.verification_code == "123456"
    assert by_oid.verification_code_expires_at is not None
    assert by_oid.last_resend_at is not None
    assert by_oid.created_at is not None
    by_email = store.get_user_by_email("a@example.com")
    assert by_email is not None and by_email.oid == "u-1"


def test_get_missing_user_returns_none(store: PostgresUsersStore) -> None:
    assert store.get_user_by_oid("nope") is None
    assert store.get_user_by_email("nope@example.com") is None


def test_add_user_duplicate_email_raises_value_error(store: PostgresUsersStore) -> None:
    store.add_user(_user(oid="u-1", email="dup@example.com"))
    with pytest.raises(ValueError, match="email_already_exists"):
        store.add_user(_user(oid="u-2", email="dup@example.com"))


def test_replace_user_overwrites(store: PostgresUsersStore) -> None:
    store.add_user(_user())
    updated = _user(verified=True)  # same oid + email, now verified, code cleared
    store.replace_user(updated)
    got = store.get_user_by_oid("u-1")
    assert got is not None
    assert got.verified is True
    assert got.verification_code is None
    assert got.verification_code_expires_at is None


def test_reset_truncates_both_tables(store: PostgresUsersStore) -> None:
    store.add_user(_user())
    store.add_session(SessionRecord(token="t-1", user_oid="u-1", expires_at=datetime.now(UTC) + timedelta(days=7)))
    store.reset()
    assert store.get_user_by_oid("u-1") is None
    assert store.get_session("t-1") is None


def test_session_add_get_delete(store: PostgresUsersStore) -> None:
    store.add_user(_user())
    sess = SessionRecord(token="t-1", user_oid="u-1", expires_at=datetime.now(UTC) + timedelta(days=7))
    store.add_session(sess)
    got = store.get_session("t-1")
    assert got is not None
    assert got.user_oid == "u-1"
    assert got.expires_at == sess.expires_at
    assert store.delete_session("t-1") is True
    assert store.delete_session("t-1") is False
    assert store.get_session("t-1") is None


def test_get_missing_session_returns_none(store: PostgresUsersStore) -> None:
    assert store.get_session("not-a-token") is None


def test_session_cascades_when_user_deleted(store: PostgresUsersStore) -> None:
    """FK ON DELETE CASCADE — wiping the users table drops dependent sessions."""
    store.add_user(_user())
    store.add_session(SessionRecord(token="t-1", user_oid="u-1", expires_at=datetime.now(UTC) + timedelta(days=7)))
    with psycopg.connect(_DSN, autocommit=True) as conn:
        conn.execute("DELETE FROM users WHERE oid = %s", ("u-1",))
    assert store.get_session("t-1") is None

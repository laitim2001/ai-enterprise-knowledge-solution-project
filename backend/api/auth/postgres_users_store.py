"""Postgres-backed users + sessions store (per ADR-0023 — closes CO18 for the
self-register user table; restart no longer wipes accounts).

Satisfies the `UsersStore` Protocol. **Sync** `psycopg` connection-per-op — the
`users_repo` public surface is sync (consumed by the sync `get_current_user`
dependency + sync calls in async route bodies), so an async DAL would force a
ripple change through `dependency.py` / `auth.py` / the test suite. Auth ops are
infrequent and off the query hot path, so connection-per-op (no pool) is fine —
same trade as `PostgresKBBackend` (deviation from a "lifespan pool" logged in the
W17 plan §7 changelog). `CREATE TABLE IF NOT EXISTS` runs on every connect:
idempotent, microseconds when the tables exist, race-free.

Imported only when `Settings.database_url` is set — see
`api.auth.users_store.make_users_store`, which lazily imports this module so an
unset `DATABASE_URL` never touches `psycopg`.

Schema (in the `ekp` database per ADR-0023, or whatever DB the DSN points at):
    users(oid PK / email UNIQUE / display_name / password_hash / verified /
          verification_code / verification_code_expires_at / last_resend_at /
          created_at)
    sessions(token PK / user_oid FK→users(oid) ON DELETE CASCADE / expires_at /
             created_at)
"""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from api.auth.users_store import SessionRecord, UserRecord

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    oid                          TEXT PRIMARY KEY,
    email                        TEXT NOT NULL UNIQUE,
    display_name                 TEXT NOT NULL,
    password_hash                TEXT NOT NULL,
    verified                     BOOLEAN NOT NULL DEFAULT FALSE,
    verification_code            TEXT,
    verification_code_expires_at TIMESTAMPTZ,
    last_resend_at               TIMESTAMPTZ,
    created_at                   TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_oid   TEXT NOT NULL REFERENCES users(oid) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);
"""

_USER_COLS = (
    "oid, email, display_name, password_hash, verified, verification_code, "
    "verification_code_expires_at, last_resend_at, created_at"
)
_SESSION_COLS = "token, user_oid, expires_at, created_at"


def _row_to_user(row: dict) -> UserRecord:
    return UserRecord(
        oid=row["oid"],
        email=row["email"],
        display_name=row["display_name"],
        password_hash=row["password_hash"],
        verified=row["verified"],
        verification_code=row["verification_code"],
        verification_code_expires_at=row["verification_code_expires_at"],
        last_resend_at=row["last_resend_at"],
        created_at=row["created_at"],
    )


def _row_to_session(row: dict) -> SessionRecord:
    return SessionRecord(
        token=row["token"],
        user_oid=row["user_oid"],
        expires_at=row["expires_at"],
        created_at=row["created_at"],
    )


class PostgresUsersStore:
    """Users + sessions backed by Postgres tables — satisfies the `UsersStore` Protocol."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def _connect(self) -> psycopg.Connection:
        conn = psycopg.connect(self._dsn, autocommit=True, row_factory=dict_row)
        conn.execute(_CREATE_TABLES)
        return conn

    def reset(self) -> None:
        with self._connect() as conn:
            conn.execute("TRUNCATE TABLE sessions, users")

    def add_user(self, record: UserRecord) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            try:
                cur.execute(
                    f"INSERT INTO users ({_USER_COLS}) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        record.oid,
                        record.email,
                        record.display_name,
                        record.password_hash,
                        record.verified,
                        record.verification_code,
                        record.verification_code_expires_at,
                        record.last_resend_at,
                        record.created_at,
                    ),
                )
            except psycopg.errors.UniqueViolation as exc:
                # PK (oid) collisions are astronomically unlikely with token_urlsafe;
                # in practice this is the email UNIQUE constraint.
                raise ValueError(f"email_already_exists: {record.email}") from exc

    def get_user_by_oid(self, oid: str) -> UserRecord | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {_USER_COLS} FROM users WHERE oid = %s", (oid,))
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def get_user_by_email(self, normalized_email: str) -> UserRecord | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT {_USER_COLS} FROM users WHERE email = %s", (normalized_email,)
            )
            row = cur.fetchone()
        return _row_to_user(row) if row else None

    def replace_user(self, record: UserRecord) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email = %s, display_name = %s, password_hash = %s, "
                "verified = %s, verification_code = %s, verification_code_expires_at = %s, "
                "last_resend_at = %s, created_at = %s WHERE oid = %s",
                (
                    record.email,
                    record.display_name,
                    record.password_hash,
                    record.verified,
                    record.verification_code,
                    record.verification_code_expires_at,
                    record.last_resend_at,
                    record.created_at,
                    record.oid,
                ),
            )

    def add_session(self, record: SessionRecord) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO sessions ({_SESSION_COLS}) VALUES (%s, %s, %s, %s)",
                (record.token, record.user_oid, record.expires_at, record.created_at),
            )

    def get_session(self, token: str) -> SessionRecord | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                f"SELECT {_SESSION_COLS} FROM sessions WHERE token = %s", (token,)
            )
            row = cur.fetchone()
        return _row_to_session(row) if row else None

    def delete_session(self, token: str) -> bool:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
            return cur.rowcount > 0

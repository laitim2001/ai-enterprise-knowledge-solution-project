"""C11 — users + sessions storage backend (Protocol + in-memory impl + factory).

Extracted from `users_repo.py` in W17 F1 (per ADR-0023). `users_repo` keeps the
public surface (`find_by_email`, `register`, `resolve_session`, …) + all the
business logic (oid / code / hash generation, expiry math); this module owns the
*persistence* primitives behind a `UsersStore` Protocol, mirroring the
`kb_management.storage.KBStorageBackend` pattern.

Two impls:
  - `InMemoryUsersStore` — process-local dicts (W13 behaviour; local dev / CI).
  - `PostgresUsersStore` (in `postgres_users_store.py`) — durable, picked when
    `Settings.database_url` is set. Lazily imported inside `make_users_store` so
    an unset `DATABASE_URL` never touches `psycopg` (R8 corp-proxy — keeps the
    in-memory path working even if `pip install psycopg[binary]` is blocked).

Sync, not async: `users_repo`'s public functions are consumed by the **sync**
`get_current_user` FastAPI dependency (run in a threadpool) and by sync calls in
the async `/auth/*` route bodies — so the store interface stays sync and
`PostgresUsersStore` uses sync `psycopg` connection-per-op. Blocking DB I/O in an
async route body is acceptable for Tier 1 (auth is infrequent + low-traffic Beta).
This differs from `PostgresKBBackend`, which is async because `KBService` /
`/kb` routes `await` it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from typing import Protocol

from pydantic import BaseModel, Field

from storage.settings import Settings


class UserRecord(BaseModel):
    """Internal user record (includes password_hash — NEVER serialize externally)."""

    oid: str
    email: str
    display_name: str
    password_hash: str
    verified: bool = False
    verification_code: str | None = None
    verification_code_expires_at: datetime | None = None
    last_resend_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SessionRecord(BaseModel):
    token: str
    user_oid: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UsersStore(Protocol):
    """Persistence primitives for users + sessions. Implementations must be
    thread-safe (the in-memory store is poked from threadpool-run dependencies)."""

    def reset(self) -> None:
        """Test fixture helper — wipes both users + sessions tables."""
        ...

    def add_user(self, record: UserRecord) -> None:
        """Insert a new user. Raises ValueError if the oid or (lowercased) email
        already exists — defense-in-depth contract; callers also pre-check."""
        ...

    def get_user_by_oid(self, oid: str) -> UserRecord | None: ...

    def get_user_by_email(self, normalized_email: str) -> UserRecord | None:
        """Look up by an already-lowercased/stripped email."""
        ...

    def replace_user(self, record: UserRecord) -> None:
        """Overwrite the user with matching oid (must already exist)."""
        ...

    def add_session(self, record: SessionRecord) -> None: ...

    def get_session(self, token: str) -> SessionRecord | None: ...

    def delete_session(self, token: str) -> bool:
        """Drop the session token. Returns True if it existed."""
        ...


class InMemoryUsersStore:
    """Process-local users + sessions store — W13 behaviour, not durable across
    restart. Single-process Tier 1 dev / CI scope."""

    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}  # key = oid
        self._sessions: dict[str, SessionRecord] = {}  # key = session token
        self._lock = RLock()

    def reset(self) -> None:
        with self._lock:
            self._users.clear()
            self._sessions.clear()

    def add_user(self, record: UserRecord) -> None:
        with self._lock:
            if record.oid in self._users:
                raise ValueError(f"oid_already_exists: {record.oid}")
            if any(u.email == record.email for u in self._users.values()):
                raise ValueError(f"email_already_exists: {record.email}")
            self._users[record.oid] = record

    def get_user_by_oid(self, oid: str) -> UserRecord | None:
        with self._lock:
            return self._users.get(oid)

    def get_user_by_email(self, normalized_email: str) -> UserRecord | None:
        with self._lock:
            for user in self._users.values():
                if user.email == normalized_email:
                    return user
        return None

    def replace_user(self, record: UserRecord) -> None:
        with self._lock:
            self._users[record.oid] = record

    def add_session(self, record: SessionRecord) -> None:
        with self._lock:
            self._sessions[record.token] = record

    def get_session(self, token: str) -> SessionRecord | None:
        with self._lock:
            return self._sessions.get(token)

    def delete_session(self, token: str) -> bool:
        with self._lock:
            return self._sessions.pop(token, None) is not None


def make_users_store(settings: Settings) -> UsersStore:
    """Return a Postgres-backed users store when `database_url` is set, else the
    process-local in-memory store. Mirrors `kb_management.factory.make_kb_backend`
    — `PostgresUsersStore` (and `psycopg`) is imported lazily inside the branch."""
    if settings.database_url:
        from api.auth.postgres_users_store import PostgresUsersStore

        return PostgresUsersStore(settings.database_url)
    return InMemoryUsersStore()

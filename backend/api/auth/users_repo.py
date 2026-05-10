"""C11 — users + sessions repository (W13 D5 F5; W17 F1 Postgres-backed per ADR-0023).

Public surface = the module-level functions below (`find_by_email`, `register`,
`resolve_session`, …) — call sites in `routes/auth.py` + `dependency.py` are
unchanged. Business logic (oid / verification-code / scrypt-hash generation,
expiry math, email normalization, the `AuthenticatedUser` projection) lives here;
*persistence* is delegated to a `UsersStore` (see `users_store.py`):
  - no `DATABASE_URL`  → `InMemoryUsersStore` (W13 behaviour — process-local,
    not durable across restart; local dev / CI).
  - `DATABASE_URL` set → `PostgresUsersStore` (durable — closes CO18).

The store is selected once at import time from `get_settings()`. Tests that need
to inspect in-memory state reach it via `users_repo._store._users` /
`._sessions` (the store owns those dicts now).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from storage.settings import get_settings

from .models import AuthenticatedUser
from .security import (
    SESSION_TOKEN_TTL_SEC,
    VERIFICATION_TOKEN_TTL_SEC,
    generate_session_token,
    generate_user_oid,
    generate_verification_code,
    hash_password,
)
from .users_store import (
    SessionRecord,
    UserRecord,
    UsersStore,
    make_users_store,
)

__all__ = [
    "SELF_REGISTER_TID",
    "SessionRecord",
    "UserRecord",
    "create_session",
    "find_by_email",
    "find_by_oid",
    "mark_verified",
    "regenerate_verification_code",
    "register",
    "reset_repo",
    "resolve_session",
    "revoke_session",
]

# Sentinel tenant id for self-register users — distinguishes from real Entra
# ID tenant in audit log + retrieval scope checks.
SELF_REGISTER_TID = "ekp-self-register"

# Persistence backend — Postgres when DATABASE_URL is set, else process-local
# in-memory (per ADR-0023 + W11 retro CO18).
_store: UsersStore = make_users_store(get_settings())


def reset_repo() -> None:
    """Test fixture helper — wipes both users + sessions tables."""
    _store.reset()


def find_by_email(email: str) -> UserRecord | None:
    return _store.get_user_by_email(email.strip().lower())


def find_by_oid(oid: str) -> UserRecord | None:
    return _store.get_user_by_oid(oid)


def register(*, email: str, password: str, display_name: str) -> UserRecord:
    """Create new user record + initial verification code. Caller must check
    duplicate via find_by_email() first; the store also raises ValueError on
    collision as a defense-in-depth contract."""
    normalized_email = email.strip().lower()
    if _store.get_user_by_email(normalized_email) is not None:
        raise ValueError(f"email_already_exists: {normalized_email}")
    record = UserRecord(
        oid=generate_user_oid(),
        email=normalized_email,
        display_name=display_name.strip(),
        password_hash=hash_password(password),
        verified=False,
        verification_code=generate_verification_code(),
        verification_code_expires_at=datetime.now(UTC)
        + timedelta(seconds=VERIFICATION_TOKEN_TTL_SEC),
        last_resend_at=datetime.now(UTC),
    )
    _store.add_user(record)
    return record


def regenerate_verification_code(oid: str) -> UserRecord | None:
    """Mint a fresh code + reset 24h expiry + bump last_resend_at. Returns the
    updated user, or None if oid missing / already verified."""
    user = _store.get_user_by_oid(oid)
    if user is None or user.verified:
        return None
    updated = user.model_copy(
        update={
            "verification_code": generate_verification_code(),
            "verification_code_expires_at": datetime.now(UTC)
            + timedelta(seconds=VERIFICATION_TOKEN_TTL_SEC),
            "last_resend_at": datetime.now(UTC),
        }
    )
    _store.replace_user(updated)
    return updated


def mark_verified(oid: str) -> UserRecord | None:
    """Clear verification_code + flip verified=True. Idempotent — re-call on
    already-verified user is a no-op returning the existing record."""
    user = _store.get_user_by_oid(oid)
    if user is None:
        return None
    if user.verified:
        return user
    updated = user.model_copy(
        update={
            "verified": True,
            "verification_code": None,
            "verification_code_expires_at": None,
        }
    )
    _store.replace_user(updated)
    return updated


def create_session(user_oid: str) -> SessionRecord:
    """Mint a new session token tied to user_oid; 7-day expiry per F5.5."""
    record = SessionRecord(
        token=generate_session_token(),
        user_oid=user_oid,
        expires_at=datetime.now(UTC) + timedelta(seconds=SESSION_TOKEN_TTL_SEC),
    )
    _store.add_session(record)
    return record


def resolve_session(token: str) -> AuthenticatedUser | None:
    """Look up active session and project to AuthenticatedUser shape so the
    F1.3 dependency can return the same model as mock/MSAL paths."""
    session = _store.get_session(token)
    if session is None:
        return None
    if session.expires_at < datetime.now(UTC):
        _store.delete_session(token)
        return None
    user = _store.get_user_by_oid(session.user_oid)
    if user is None:
        return None
    return AuthenticatedUser(
        oid=user.oid,
        tid=SELF_REGISTER_TID,
        preferred_username=user.email,
        is_mock=False,
    )


def revoke_session(token: str) -> bool:
    """Drop session token from the table. Returns True if a session existed."""
    return _store.delete_session(token)

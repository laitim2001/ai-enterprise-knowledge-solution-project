"""Audit log storage — Protocol + InMemory impl (W24-wave-c1 F4.8 per ADR-0026).

Mirrors F2 + F3 3-file Protocol + lazy-import shape:

- `AuditLogBackend` Protocol lives here
- `InMemoryAuditLogBackend` lives here (install-free, restart-wipes; CI baseline)
- `PostgresAuditLogBackend` in `audit_log_postgres.py` (lazy-imported by factory)

`append` is write-only at Wave C1 — list/query endpoints land Wave C2 +
SettingsAccount surface. The Protocol exposes `list_recent` so callers can
exercise it in tests, but no FastAPI route surfaces it Tier 1.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol, runtime_checkable

from api.schemas.audit_log import AuditAction, AuditLogEntry


def _now() -> datetime:
    return datetime.now(UTC)


@runtime_checkable
class AuditLogBackend(Protocol):
    """Audit log write-mostly interface. List for tests + Wave C2 promotion."""

    async def append(
        self,
        *,
        actor: str | None,
        action: AuditAction,
        resource: str,
        payload: dict[str, object] | None = None,
    ) -> AuditLogEntry: ...

    async def list_recent(
        self,
        limit: int = 50,
        *,
        action_type: AuditAction | None = None,
        since: datetime | None = None,
        cursor: int | None = None,
    ) -> list[AuditLogEntry]: ...

    async def prune_expired(self, retention_days: int = 90) -> int:
        """Delete entries older than `retention_days`; return the count removed.

        Best-effort retention — called at app startup (Tier 1 has no
        scheduler), so the window is approximate (W24c F7 per ADR-0027)."""
        ...


class InMemoryAuditLogBackend:
    """Process-local audit log. Restart-wipes — matches `InMemoryAdminProviderBackend`."""

    def __init__(self) -> None:
        self._rows: list[AuditLogEntry] = []
        self._next_id = 1

    async def append(
        self,
        *,
        actor: str | None,
        action: AuditAction,
        resource: str,
        payload: dict[str, object] | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            id=self._next_id,
            actor=actor,
            action=action,
            resource=resource,
            payload=payload,
            created_at=_now(),
        )
        self._rows.append(entry)
        self._next_id += 1
        return entry

    async def list_recent(
        self,
        limit: int = 50,
        *,
        action_type: AuditAction | None = None,
        since: datetime | None = None,
        cursor: int | None = None,
    ) -> list[AuditLogEntry]:
        # Newest-first; filters applied in-pass so `limit` counts post-filter
        # rows. `cursor` is an exclusive `id` bound — `id < cursor` walks older.
        result: list[AuditLogEntry] = []
        for entry in reversed(self._rows):
            if action_type is not None and entry.action != action_type:
                continue
            if since is not None and entry.created_at < since:
                continue
            if cursor is not None and entry.id is not None and entry.id >= cursor:
                continue
            result.append(entry)
            if len(result) >= limit:
                break
        return result

    async def prune_expired(self, retention_days: int = 90) -> int:
        cutoff = _now() - timedelta(days=retention_days)
        before = len(self._rows)
        self._rows = [r for r in self._rows if r.created_at >= cutoff]
        return before - len(self._rows)

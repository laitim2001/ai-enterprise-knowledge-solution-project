"""`GET /admin/audit-log` — read-only recent entries (W24-wave-c1 F5 hook;
W24b-wave-c2 F6 filter + cursor pagination).

F4 deferred the read endpoint to F5/Wave C2; F5 promoted it because
`<SettingsAccount>` surfaces recent audit rows. W24b F6 adds the filter +
pagination promised at W24-c1: `action_type` / `since` / `cursor` query
params and an `AuditLogPage` wrapper response carrying `next_cursor`.

Endpoint is read-only — writes happen at the F2/F3/F4 PATCH hook points.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request, status

from api.schemas.audit_log import AuditAction, AuditLogPage
from storage.audit_log_storage import AuditLogBackend

router = APIRouter(prefix="/admin")


def _get_backend(request: Request) -> AuditLogBackend:
    backend = getattr(request.app.state, "audit_log_backend", None)
    if backend is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="audit_log_backend not initialized — check lifespan logs",
        )
    return backend  # type: ignore[no-any-return]


@router.get("/audit-log", response_model=AuditLogPage)
async def list_audit_log(
    request: Request,
    limit: int = Query(default=10, ge=1, le=200),
    action_type: AuditAction | None = Query(default=None),
    since: datetime | None = Query(default=None),
    cursor: int | None = Query(default=None, ge=1),
) -> AuditLogPage:
    backend = _get_backend(request)
    # A date-only `?since=YYYY-MM-DD` parses tz-naive — assume UTC so the
    # comparison against tz-aware `created_at` doesn't raise TypeError.
    if since is not None and since.tzinfo is None:
        since = since.replace(tzinfo=UTC)
    # Over-fetch by one row to detect whether an older page exists.
    rows = await backend.list_recent(
        limit=limit + 1, action_type=action_type, since=since, cursor=cursor
    )
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = page[-1].id if has_more and page else None
    return AuditLogPage(entries=page, next_cursor=next_cursor)

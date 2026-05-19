"""`GET /admin/audit-log` — read-only recent entries (W24-wave-c1 F5 backend hook).

F4 deferred the read endpoint to F5/Wave C2; F5 promotes it because
`<SettingsAccount>` (mockup line 842-870) surfaces the last-10 audit rows.
Wave C2 will add filters + pagination once SettingsAccount UI lands properly.

Endpoint is read-only — writes happen at the F2/F3/F4 PATCH hook points.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, status

from api.schemas.audit_log import AuditLogEntry
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


@router.get("/audit-log", response_model=list[AuditLogEntry])
async def list_audit_log(
    request: Request,
    limit: int = Query(default=10, ge=1, le=200),
) -> list[AuditLogEntry]:
    backend = _get_backend(request)
    return await backend.list_recent(limit=limit)

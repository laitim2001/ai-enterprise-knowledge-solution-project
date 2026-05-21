"""C16 — `/kb/{kb_id}/acl` per-KB ACL endpoints (W24c F8 per ADR-0027 Option A).

4 CRUD endpoints, all gated by the router-level `require_kb_acl("manage")` —
managing a KB's access list itself requires `manage` access (workspace admins
always pass):
  - GET    /kb/{kb_id}/acl              — explicit ACL grants for the KB
  - POST   /kb/{kb_id}/acl              — grant a user/group access
  - PATCH  /kb/{kb_id}/acl/{entry_id}   — change a grant's role
  - DELETE /kb/{kb_id}/acl/{entry_id}   — revoke a grant

Surfaced by the KB Detail Access tab (`references/design-mockups/
ekp-page-users.jsx:389 TabKbAccess`). The mockup's synthetic rows — workspace-
admin auto-access, group-inherited access — are not stored; only explicit
grants live in `kb_acl` (CLAUDE.md §13). KB Visibility (private/workspace/
public) is a KB-level setting, out of scope here.

PATCH / DELETE are scoped by `kb_id` in the store so a manager of one KB
cannot reach another KB's grants by guessing the global entry id. `POST`
writes a `kb.access.granted` audit row when an audit backend is wired.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from api.auth import AuthenticatedUser, get_current_user
from api.middleware.acl import require_kb_acl
from api.schemas.audit_log import AuditAction
from api.schemas.rbac import (
    KbAclEntry,
    KbAclGrantRequest,
    KbAclListResponse,
    KbAclRoleChangeRequest,
)
from storage.audit_log_storage import AuditLogBackend
from storage.rbac_storage import RbacBackend

router = APIRouter(
    tags=["kb-acl"],
    dependencies=[Depends(require_kb_acl("manage"))],
)


def _get_rbac_backend(request: Request) -> RbacBackend:
    """Resolve the lifespan-wired RBAC backend, or 503 when unwired."""
    backend = getattr(request.app.state, "rbac_backend", None)
    if backend is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="rbac_backend not initialized — check lifespan logs",
        )
    return backend  # type: ignore[no-any-return]


async def _audit(
    request: Request,
    *,
    actor: str,
    action: AuditAction,
    resource: str,
    payload: dict[str, object],
) -> None:
    """Write a per-KB ACL mutation to the audit log when a backend is wired."""
    audit: AuditLogBackend | None = getattr(
        request.app.state, "audit_log_backend", None
    )
    if audit is not None:
        await audit.append(
            actor=actor, action=action, resource=resource, payload=payload
        )


@router.get("/kb/{kb_id}/acl", response_model=KbAclListResponse)
async def list_kb_acl(
    kb_id: Annotated[str, Path(min_length=1)], request: Request
) -> KbAclListResponse:
    """Every explicit ACL grant on the KB."""
    backend = _get_rbac_backend(request)
    entries = await backend.list_kb_acl(kb_id)
    return KbAclListResponse(entries=entries, total=len(entries))


@router.post(
    "/kb/{kb_id}/acl",
    response_model=KbAclEntry,
    status_code=status.HTTP_201_CREATED,
)
async def grant_kb_access(
    kb_id: Annotated[str, Path(min_length=1)],
    body: KbAclGrantRequest,
    request: Request,
    current_user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> KbAclEntry:
    """Grant a user or group access to the KB (upserts an existing grant)."""
    backend = _get_rbac_backend(request)
    entry = await backend.add_kb_acl(
        kb_id=kb_id,
        principal_type=body.principal_type,
        principal_id=body.principal_id,
        access_role=body.access_role,
        granted_by=current_user.preferred_username,
    )
    await _audit(
        request,
        actor=current_user.preferred_username,
        action="kb.access.granted",
        resource=f"kb/{kb_id}",
        payload={
            "principal_type": entry.principal_type,
            "principal_id": entry.principal_id,
            "access_role": entry.access_role,
        },
    )
    return entry


@router.patch("/kb/{kb_id}/acl/{entry_id}", response_model=KbAclEntry)
async def change_kb_acl_role(
    kb_id: Annotated[str, Path(min_length=1)],
    entry_id: Annotated[int, Path(ge=1)],
    body: KbAclRoleChangeRequest,
    request: Request,
) -> KbAclEntry:
    """Change an existing grant's role."""
    backend = _get_rbac_backend(request)
    entry = await backend.set_kb_acl_role(kb_id, entry_id, body.access_role)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="acl_entry_not_found"
        )
    return entry


@router.delete(
    "/kb/{kb_id}/acl/{entry_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_kb_access(
    kb_id: Annotated[str, Path(min_length=1)],
    entry_id: Annotated[int, Path(ge=1)],
    request: Request,
) -> None:
    """Revoke a grant."""
    backend = _get_rbac_backend(request)
    removed = await backend.remove_kb_acl(kb_id, entry_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="acl_entry_not_found"
        )

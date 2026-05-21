"""C16 — `/roles` Roles tab endpoints (W24c F5 per ADR-0027 Option A).

2 read-only endpoints, both admin-gated by the router-level
`require_role("admin")`:
  - GET /roles             — the 4 RBAC role definitions (Admin → Power User)
  - GET /roles/permissions — the flat 92-cell permissions matrix

Surfaced by the `/users` page Roles tab (`references/design-mockups/
ekp-page-users.jsx:209 RolesTab`). The permissions matrix is hard-coded static
admin policy — custom roles are Tier 2 (CLAUDE.md H4), so both endpoints are
read-only. Per-role member counts are computed client-side per the mockup
(`RolesTab` counts from the users list — CLAUDE.md §13, F5 R6 finding #3).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.middleware.acl import require_role
from api.schemas.rbac import PermissionMatrixResponse, RoleListResponse
from storage.rbac_storage import RbacBackend

router = APIRouter(
    prefix="/roles",
    tags=["roles"],
    dependencies=[Depends(require_role("admin"))],
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


@router.get("", response_model=RoleListResponse)
async def list_roles(request: Request) -> RoleListResponse:
    """The 4 RBAC roles, ordered Admin → Editor → End User → Power User."""
    backend = _get_rbac_backend(request)
    roles = await backend.list_roles()
    return RoleListResponse(roles=roles, total=len(roles))


@router.get("/permissions", response_model=PermissionMatrixResponse)
async def list_permissions(request: Request) -> PermissionMatrixResponse:
    """The flat 92-cell permissions matrix — one row per (role, permission)."""
    backend = _get_rbac_backend(request)
    perms = await backend.list_role_permissions()
    return PermissionMatrixResponse(permissions=perms, total=len(perms))

"""C16 — `/groups` Groups tab endpoints (W24c F6 per ADR-0027 Option A).

2 endpoints, both admin-gated by the router-level `require_role("admin")`:
  - GET  /groups                 — every workspace group, with member counts
  - POST /groups/sync-from-entra  — pull the group list from Microsoft Graph

Surfaced by the `/users` page Groups tab (`references/design-mockups/
ekp-page-users.jsx:288 GroupsTab`). The group → EKP role mapping shown there
is a separate concern (`admin_identity.RoleMappingConfig`) — the frontend
joins it client-side (CLAUDE.md §13).

`sync-from-entra` degrades gracefully (`status='skipped'`) when Entra ID is
not configured — mock-auth dev never reaches Microsoft Graph. Group *member*
sync (Graph `/groups/{id}/members`) is a deferred follow-up; F6 syncs the
group list only.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from api.auth import entra_graph
from api.middleware.acl import require_role
from api.schemas.rbac import GroupListResponse, GroupSyncResult
from storage.rbac_storage import RbacBackend
from storage.settings import Settings, get_settings

router = APIRouter(
    prefix="/groups",
    tags=["groups"],
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


@router.get("", response_model=GroupListResponse)
async def list_groups(request: Request) -> GroupListResponse:
    """Every workspace group, ordered by name, with member counts."""
    backend = _get_rbac_backend(request)
    groups = await backend.list_groups()
    return GroupListResponse(groups=groups, total=len(groups))


@router.post("/sync-from-entra", response_model=GroupSyncResult)
async def sync_from_entra(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> GroupSyncResult:
    """Pull the group list from Microsoft Graph and upsert it.

    A graceful no-op when Entra ID is not configured (mock-auth dev)."""
    if not settings.azure_tenant_id:
        return GroupSyncResult(
            status="skipped",
            synced_count=0,
            detail="Entra ID is not configured — group sync skipped (mock-auth mode).",
        )
    backend = _get_rbac_backend(request)
    try:
        entra_groups = await entra_graph.fetch_entra_groups()
    except Exception as exc:  # noqa: BLE001 — any Graph/credential failure → 502
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Microsoft Graph group fetch failed: {exc}",
        ) from exc
    for grp in entra_groups:
        await backend.upsert_entra_group(
            object_id=grp.object_id,
            name=grp.display_name,
            description=grp.description,
        )
    return GroupSyncResult(
        status="synced",
        synced_count=len(entra_groups),
        detail=f"Synced {len(entra_groups)} group(s) from Entra ID.",
    )

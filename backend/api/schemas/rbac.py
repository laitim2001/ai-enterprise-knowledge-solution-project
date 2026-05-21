"""RBAC schema models — roles + permissions matrix (W24c F2 per ADR-0027 Option A).

C16 Users Service (Tier 1.5). Mirrors the `roles` + `role_permissions` Postgres
tables. The `groups` / `group_members` / `kb_acl` tables get their `CREATE TABLE`
at F2.1 too, but their API schemas arrive with F6 (Groups) / F8 (per-KB ACL) —
W24c plan §2 rolling JIT, no speculative surface (Karpathy §1.2).

Tier 1.5 ships 3 active roles (Admin / Editor / End User). Power User is a
Tier 2 reserved role surfaced as a disabled affordance per CLAUDE.md H4 —
seeded with `active=False` so the matrix's 4th column renders without granting
any Tier 2 capability.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Role keys — 3 Tier 1.5 active roles + Power User (Tier 2 reserved, active=False).
RoleKey = Literal["admin", "editor", "user", "power"]


class Role(BaseModel):
    """One RBAC role definition. Mirrors a `roles` table row."""

    role_key: RoleKey
    label: str = Field(..., description="Display name, e.g. 'Workspace Admin'.")
    description: str = Field(..., description="One-line capability summary, per mockup ROLES.")
    tier: int = Field(..., description="1 = Tier 1.5 active role; 2 = Tier 2 reserved (Power User).")
    active: bool = Field(
        ...,
        description="False = disabled affordance (Power User Tier 2 per CLAUDE.md H4).",
    )


class RolePermission(BaseModel):
    """One cell of the permissions matrix — a (role, permission) grant.

    Mirrors a `role_permissions` table row. The matrix is hard-coded static
    admin policy (custom roles are Tier 2 per CLAUDE.md H4), so there is no
    Tier 1.5 write path — `role_permissions` is read + seeded only.
    """

    role_key: RoleKey
    permission_key: str = Field(..., description="Stable slug, e.g. 'kb.view_assigned'.")
    area: str = Field(..., description="Matrix section header, e.g. 'Knowledge bases'.")
    label: str = Field(..., description="Human-readable permission, verbatim from the mockup.")
    granted: bool


# --- F5 /roles response wrappers (W24c F5 per ADR-0027 §Context Roles tab) ---


class RoleListResponse(BaseModel):
    """`GET /roles` payload — the 4 RBAC roles, ordered Admin → Power User.

    Per-role member counts are not carried — the mockup `RolesTab` counts
    client-side from the users list (CLAUDE.md §13, F5 R6 finding #3).
    """

    roles: list[Role]
    total: int


class PermissionMatrixResponse(BaseModel):
    """`GET /roles/permissions` payload — the flat 92-cell permissions matrix.

    One `RolePermission` per (role, permission). The backend ships the
    canonical per-cell shape; the frontend pivots by `area` + `role_key` to
    render the matrix table (CLAUDE.md §13 — backend wins on field shape).
    """

    permissions: list[RolePermission]
    total: int


# --- F6 /groups schema (W24c F6 per ADR-0027 §Context Groups tab) -----------

# Group provenance — `local` (created in EKP) or `entra` (synced from Graph).
GroupSource = Literal["local", "entra"]


class Group(BaseModel):
    """One workspace group. Mirrors a `groups` table row + computed member count.

    Entra-synced groups carry `source='entra'`; `group_key` equals the Graph
    object id (a stable upsert key). The group → EKP role mapping is a separate
    concern (`admin_identity.RoleMappingConfig`) — not carried here; the
    frontend joins it client-side (CLAUDE.md §13, F6 R6 finding #3).
    """

    group_key: str = Field(..., description="Stable PK — the Entra object id for synced groups.")
    name: str = Field(..., description="Display name, e.g. 'grp-ekp-admins'.")
    description: str | None = None
    source: GroupSource = "local"
    entra_object_id: str | None = Field(
        default=None, description="Entra security group GUID; None for local groups."
    )
    synced_at: datetime | None = Field(
        default=None, description="Last Entra sync time; None until first synced."
    )
    member_count: int = Field(
        default=0,
        description="Members in `group_members`; 0 until member sync lands (F6 syncs the group list only).",
    )


class GroupListResponse(BaseModel):
    """`GET /groups` payload — every workspace group, with member counts."""

    groups: list[Group]
    total: int


class GroupSyncResult(BaseModel):
    """`POST /groups/sync-from-entra` payload.

    `skipped` when Entra ID is not configured (mock-auth dev) — a graceful
    degrade, not an error (F6 R6 finding #5).
    """

    status: Literal["synced", "skipped"]
    synced_count: int = 0
    detail: str


# --- F8 per-KB ACL schema (W24c F8 per ADR-0027 §Decision kb_acl) -----------

# Per-KB access role — ranked manage > edit > query (see acl.require_kb_acl).
KbAclRole = Literal["manage", "edit", "query"]
# An ACL grant targets either a single user or a whole group.
KbPrincipalType = Literal["user", "group"]


class KbAclEntry(BaseModel):
    """One explicit per-KB access grant. Mirrors a `kb_acl` table row.

    A user or group given a `manage`/`edit`/`query` role on one KB. Synthetic
    rows the mockup shows — workspace-admin auto-access, group-inherited
    access — are NOT stored here; the frontend derives them (CLAUDE.md §13).
    """

    id: int
    kb_id: str
    principal_type: KbPrincipalType
    principal_id: str = Field(..., description="User oid or group key.")
    access_role: KbAclRole
    granted_by: str | None = Field(
        default=None, description="Actor who created the grant; None for legacy rows."
    )
    created_at: datetime


class KbAclListResponse(BaseModel):
    """`GET /kb/{kb_id}/acl` payload — the KB's explicit ACL grants."""

    entries: list[KbAclEntry]
    total: int


class KbAclGrantRequest(BaseModel):
    """`POST /kb/{kb_id}/acl` body — grant a principal access to the KB."""

    principal_type: KbPrincipalType
    principal_id: str
    access_role: KbAclRole


class KbAclRoleChangeRequest(BaseModel):
    """`PATCH /kb/{kb_id}/acl/{entry_id}` body — change a grant's role."""

    access_role: KbAclRole

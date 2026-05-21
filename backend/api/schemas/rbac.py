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

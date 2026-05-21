"""RBAC storage — Protocol + InMemory impl + permissions seed (W24c F2 per ADR-0027).

C16 Users Service (Tier 1.5). 3-file split mirrors `audit_log` / `admin_provider`:

  - `RbacBackend` Protocol + `InMemoryRbacBackend` live here
  - `PostgresRbacBackend` in `rbac_postgres.py` (lazy-imported by the factory)
  - `make_rbac_backend` in `rbac_factory.py`

F2 scope = `roles` + `role_permissions` read + idempotent seed. W24c F6 adds
the `groups` read/sync surface (`list_groups` / `upsert_entra_group`) + an
additive `synced_at` column ALTER (see `rbac_postgres.py`). `group_members`
write + `kb_acl` surface stay absent until F8 (W24c plan §2 rolling JIT +
Karpathy §1.2 no speculative surface).

Async, not sync: the RBAC backend is consumed by the async `/users/*` route
bodies + the ACL middleware (F3+), with no sync-dependency tie like
`UsersStore` has — so this mirrors the async `AuditLogBackend` shape.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol, runtime_checkable

from api.schemas.rbac import Group, Role, RoleKey, RolePermission

# --- Seed data --------------------------------------------------------------

# Role order — Admin / Editor / End User / Power User. Drives `list_roles`
# ordering + the per-role columns of the permissions matrix below.
_ROLE_ORDER: tuple[RoleKey, ...] = ("admin", "editor", "user", "power")

# 4 default roles. Power User is Tier 2 (active=False) — a disabled affordance
# per CLAUDE.md H4, surfaced so the matrix renders its 4th column.
_DEFAULT_ROLES: tuple[Role, ...] = (
    Role(
        role_key="admin",
        label="Workspace Admin",
        description="Full platform control · manages KBs, users, providers, API keys",
        tier=1,
        active=True,
    ),
    Role(
        role_key="editor",
        label="Knowledge Editor",
        description="Create + upload to assigned KBs · manages own content · cannot change platform config",
        tier=1,
        active=True,
    ),
    Role(
        role_key="user",
        label="End User",
        description="Query assigned KBs · view own traces · no admin access",
        tier=1,
        active=True,
    ),
    Role(
        role_key="power",
        label="Power User",
        description="Tier 2 — End User + retrieval tuning + model picker access",
        tier=2,
        active=False,
    ),
)

# Permissions matrix — 5 areas × 23 permissions, verbatim from the mockup
# `references/design-mockups/ekp-page-users.jsx` lines 26-60 (PERMISSIONS_MATRIX).
# Hard-coded static admin policy: custom roles are Tier 2 per CLAUDE.md H4, so
# this constant is the single source of truth (no Tier 1.5 write path).
# Row shape: (permission_key, label, admin, editor, user, power).
_PERMISSION_MATRIX: tuple[
    tuple[str, tuple[tuple[str, str, bool, bool, bool, bool], ...]], ...
] = (
    (
        "Knowledge bases",
        (
            ("kb.view_assigned", "View assigned KBs", True, True, True, True),
            ("kb.create", "Create new KB", True, True, False, False),
            ("kb.edit_config", "Edit KB config", True, True, False, False),
            ("kb.trigger_reindex", "Trigger re-index", True, True, False, False),
            ("kb.delete", "Delete KB", True, False, False, False),
            ("kb.manage_access", "Manage KB access list", True, False, False, False),
        ),
    ),
    (
        "Documents",
        (
            ("doc.upload", "Upload to assigned KBs", True, True, False, False),
            ("doc.delete", "Delete documents", True, True, False, False),
            ("doc.view_parse_errors", "View parse errors", True, True, False, False),
        ),
    ),
    (
        "Chat & queries",
        (
            ("chat.query", "Query assigned KBs", True, True, True, True),
            ("chat.view_own_traces", "View own traces", True, True, True, True),
            ("chat.view_all_traces", "View all users' traces", True, False, False, False),
            ("chat.submit_feedback", "Submit feedback", True, True, True, True),
            ("chat.tune_retrieval", "Tune top-K / rerank-K", True, True, False, True),
            ("chat.pick_model", "Pick LLM model per query", True, False, False, True),
        ),
    ),
    (
        "Eval & ops",
        (
            ("eval.view_console", "View Eval Console", True, True, False, True),
            ("eval.run_suite", "Run eval suite", True, False, False, False),
            ("eval.view_cost", "View cost dashboard", True, False, False, False),
        ),
    ),
    (
        "Platform config",
        (
            ("cfg.manage_providers", "Manage LLM providers", True, False, False, False),
            ("cfg.manage_api_keys", "Manage API keys", True, False, False, False),
            ("cfg.manage_auth", "Manage Entra/Auth", True, False, False, False),
            ("cfg.manage_users", "Manage users + roles", True, False, False, False),
            ("cfg.view_audit_log", "View audit log", True, False, False, False),
        ),
    ),
)


def permission_matrix_rows() -> list[RolePermission]:
    """Flatten `_PERMISSION_MATRIX` into one `RolePermission` per (role, perm).

    23 permissions × 4 roles = 92 rows, ordered area → permission → role. Both
    backends seed from this; `PostgresRbacBackend` also uses the iteration index
    as the `sort_order` column so SQL can `ORDER BY` a single column.
    """
    rows: list[RolePermission] = []
    for area, perms in _PERMISSION_MATRIX:
        for perm_key, label, *grants in perms:
            # strict=True — a matrix row must carry exactly 4 grants (a/e/u/w).
            for role_key, granted in zip(_ROLE_ORDER, grants, strict=True):
                rows.append(
                    RolePermission(
                        role_key=role_key,
                        permission_key=perm_key,
                        area=area,
                        label=label,
                        granted=granted,
                    )
                )
    return rows


def default_roles() -> list[Role]:
    """The 4 seed roles, in `_ROLE_ORDER`."""
    return list(_DEFAULT_ROLES)


# --- Protocol ---------------------------------------------------------------


@runtime_checkable
class RbacBackend(Protocol):
    """RBAC persistence — F2 surfaces roles + the permissions matrix.

    Group + per-KB ACL methods land with F6 / F8 (their tables already exist
    per F2.1). Implementations must be safe to `seed_defaults` repeatedly.
    """

    async def reset(self) -> None:
        """Test fixture helper — wipes all RBAC tables."""
        ...

    async def seed_defaults(self) -> None:
        """Idempotent seed — 4 roles + the 92-row permissions matrix. A no-op
        when the roles already exist, so it is safe to call on every startup."""
        ...

    async def list_roles(self) -> list[Role]:
        """All roles, ordered Admin → Editor → End User → Power User."""
        ...

    async def get_role(self, role_key: str) -> Role | None: ...

    async def list_role_permissions(
        self, role_key: str | None = None
    ) -> list[RolePermission]:
        """The permissions matrix — all 92 cells, or one role's 23 when
        `role_key` is given. Ordered area → permission → role."""
        ...

    async def list_groups(self) -> list[Group]:
        """Every workspace group, ordered by name, with member counts. F6."""
        ...

    async def upsert_entra_group(
        self, *, object_id: str, name: str, description: str | None
    ) -> None:
        """Insert-or-update an Entra-synced group keyed by its Graph object id;
        stamps `source='entra'` + `synced_at=now`. F6 (sync-from-entra)."""
        ...


# --- In-memory impl ---------------------------------------------------------


class InMemoryRbacBackend:
    """Process-local RBAC store — restart-wipes. CI baseline + local dev.

    Matches `InMemoryAuditLogBackend`: install-free, no `psycopg`. Insertion
    order is preserved (seed order = `_ROLE_ORDER` / matrix order), so the
    `list_*` methods need no explicit sort.
    """

    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._role_permissions: list[RolePermission] = []
        self._groups: dict[str, Group] = {}

    async def reset(self) -> None:
        self._roles.clear()
        self._role_permissions.clear()
        self._groups.clear()

    async def seed_defaults(self) -> None:
        if self._roles:
            return
        for role in _DEFAULT_ROLES:
            self._roles[role.role_key] = role
        self._role_permissions = permission_matrix_rows()

    async def list_roles(self) -> list[Role]:
        return list(self._roles.values())

    async def get_role(self, role_key: str) -> Role | None:
        return self._roles.get(role_key)

    async def list_role_permissions(
        self, role_key: str | None = None
    ) -> list[RolePermission]:
        if role_key is None:
            return list(self._role_permissions)
        return [rp for rp in self._role_permissions if rp.role_key == role_key]

    async def list_groups(self) -> list[Group]:
        return sorted(self._groups.values(), key=lambda g: g.name)

    async def upsert_entra_group(
        self, *, object_id: str, name: str, description: str | None
    ) -> None:
        self._groups[object_id] = Group(
            group_key=object_id,
            name=name,
            description=description,
            source="entra",
            entra_object_id=object_id,
            synced_at=datetime.now(UTC),
            member_count=0,
        )

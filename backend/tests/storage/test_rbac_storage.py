"""RBAC storage tests (W24c F2 per ADR-0027 Option A).

Covers `InMemoryRbacBackend` seed / list / reset + the permissions-matrix
constant + the `UsersStore` `role` column smoke. `PostgresRbacBackend` round
-trip is an F11 item (needs a live DB — R8/CO17).
"""

from __future__ import annotations

import pytest

from api.schemas.rbac import RolePermission
from storage.rbac_storage import InMemoryRbacBackend, permission_matrix_rows


def _find(
    rows: list[RolePermission], *, role_key: str, permission_key: str
) -> bool:
    """The `granted` value of one matrix cell."""
    cell = next(
        rp for rp in rows if rp.role_key == role_key and rp.permission_key == permission_key
    )
    return cell.granted


@pytest.mark.asyncio
async def test_seed_defaults_creates_4_roles() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    roles = await backend.list_roles()
    assert len(roles) == 4
    assert {r.role_key for r in roles} == {"admin", "editor", "user", "power"}


@pytest.mark.asyncio
async def test_seed_defaults_role_order() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    roles = await backend.list_roles()
    assert [r.role_key for r in roles] == ["admin", "editor", "user", "power"]


@pytest.mark.asyncio
async def test_power_user_is_tier2_disabled_others_tier1_active() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    by_key = {r.role_key: r for r in await backend.list_roles()}
    # Power User — Tier 2 reserved, disabled affordance per CLAUDE.md H4.
    assert by_key["power"].tier == 2
    assert by_key["power"].active is False
    # The 3 Tier 1.5 roles are active.
    for key in ("admin", "editor", "user"):
        assert by_key[key].tier == 1
        assert by_key[key].active is True


@pytest.mark.asyncio
async def test_seed_defaults_idempotent() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    await backend.seed_defaults()  # second call must not duplicate
    roles = await backend.list_roles()
    perms = await backend.list_role_permissions()
    assert len(roles) == 4
    assert len(perms) == 92


@pytest.mark.asyncio
async def test_get_role() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    admin = await backend.get_role("admin")
    assert admin is not None
    assert admin.label == "Workspace Admin"
    assert await backend.get_role("nonexistent") is None


@pytest.mark.asyncio
async def test_list_role_permissions_full_matrix() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    rows = await backend.list_role_permissions()
    # 23 permissions × 4 roles = 92 cells.
    assert len(rows) == 92
    assert len({rp.permission_key for rp in rows}) == 23
    assert len({rp.area for rp in rows}) == 5


@pytest.mark.asyncio
async def test_list_role_permissions_per_role() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    admin = await backend.list_role_permissions("admin")
    assert len(admin) == 23
    # Admin holds every permission per the mockup matrix.
    assert all(rp.granted for rp in admin)


@pytest.mark.asyncio
async def test_permission_grants_match_mockup() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    rows = await backend.list_role_permissions()
    # End User — query yes, create-KB no, manage-users no.
    assert _find(rows, role_key="user", permission_key="kb.view_assigned") is True
    assert _find(rows, role_key="user", permission_key="kb.create") is False
    assert _find(rows, role_key="user", permission_key="cfg.manage_users") is False
    # Editor — cannot delete a KB, can create one.
    assert _find(rows, role_key="editor", permission_key="kb.delete") is False
    assert _find(rows, role_key="editor", permission_key="kb.create") is True
    # Power User (Tier 2) — retrieval tuning + model picker, but no KB creation.
    assert _find(rows, role_key="power", permission_key="chat.tune_retrieval") is True
    assert _find(rows, role_key="power", permission_key="chat.pick_model") is True
    assert _find(rows, role_key="power", permission_key="kb.create") is False


@pytest.mark.asyncio
async def test_reset_wipes_roles_and_permissions() -> None:
    backend = InMemoryRbacBackend()
    await backend.seed_defaults()
    await backend.reset()
    assert await backend.list_roles() == []
    assert await backend.list_role_permissions() == []
    # Re-seed after reset works (no idempotency lock-out).
    await backend.seed_defaults()
    assert len(await backend.list_roles()) == 4


def test_permission_matrix_rows_constant() -> None:
    rows = permission_matrix_rows()
    assert len(rows) == 92
    assert len({rp.permission_key for rp in rows}) == 23
    assert len({rp.area for rp in rows}) == 5


def test_factory_returns_in_memory_when_database_url_unset() -> None:
    from storage.rbac_factory import make_rbac_backend
    from storage.settings import Settings

    backend = make_rbac_backend(Settings(database_url=""))
    assert isinstance(backend, InMemoryRbacBackend)


def test_user_record_carries_role_column() -> None:
    from api.auth.users_store import UserRecord

    # F2.2 — new registrations default to 'user'.
    default = UserRecord(oid="o1", email="a@ricoh.com", display_name="A", password_hash="h")
    assert default.role == "user"
    # Explicit role round-trips.
    elevated = UserRecord(
        oid="o2", email="b@ricoh.com", display_name="B", password_hash="h", role="admin"
    )
    assert elevated.role == "admin"


# ---- W24c F8 — kb_acl per-KB ACL -------------------------------------------


@pytest.mark.asyncio
async def test_add_and_list_kb_acl() -> None:
    backend = InMemoryRbacBackend()
    await backend.add_kb_acl(
        kb_id="kb-1", principal_type="user", principal_id="u-1",
        access_role="edit", granted_by="admin@ricoh.com",
    )
    entries = await backend.list_kb_acl("kb-1")
    assert len(entries) == 1
    assert entries[0].access_role == "edit"
    assert entries[0].granted_by == "admin@ricoh.com"
    # Scoped per KB — another KB sees nothing.
    assert await backend.list_kb_acl("kb-other") == []


@pytest.mark.asyncio
async def test_add_kb_acl_upserts_on_same_principal() -> None:
    backend = InMemoryRbacBackend()
    first = await backend.add_kb_acl(
        kb_id="kb-1", principal_type="user", principal_id="u-1",
        access_role="query", granted_by="a",
    )
    second = await backend.add_kb_acl(
        kb_id="kb-1", principal_type="user", principal_id="u-1",
        access_role="manage", granted_by="b",
    )
    assert first.id == second.id  # same row updated, not duplicated
    entries = await backend.list_kb_acl("kb-1")
    assert len(entries) == 1
    assert entries[0].access_role == "manage"


@pytest.mark.asyncio
async def test_get_kb_access_direct_user_grant_only() -> None:
    backend = InMemoryRbacBackend()
    await backend.add_kb_acl(
        kb_id="kb-1", principal_type="user", principal_id="u-1",
        access_role="edit", granted_by="a",
    )
    assert await backend.get_kb_access("kb-1", "u-1") == "edit"
    assert await backend.get_kb_access("kb-1", "u-other") is None
    # A group grant is NOT a user's direct access (group-inherited resolution
    # lands with F6 member sync — W24c F8 R6 finding #5).
    await backend.add_kb_acl(
        kb_id="kb-1", principal_type="group", principal_id="g-1",
        access_role="manage", granted_by="a",
    )
    assert await backend.get_kb_access("kb-1", "g-1") is None


@pytest.mark.asyncio
async def test_set_kb_acl_role_scoped_by_kb() -> None:
    backend = InMemoryRbacBackend()
    entry = await backend.add_kb_acl(
        kb_id="kb-1", principal_type="user", principal_id="u-1",
        access_role="query", granted_by="a",
    )
    updated = await backend.set_kb_acl_role("kb-1", entry.id, "manage")
    assert updated is not None
    assert updated.access_role == "manage"
    # Wrong kb_id → no match, even with a valid entry id.
    assert await backend.set_kb_acl_role("kb-other", entry.id, "edit") is None


@pytest.mark.asyncio
async def test_remove_kb_acl_scoped_by_kb() -> None:
    backend = InMemoryRbacBackend()
    entry = await backend.add_kb_acl(
        kb_id="kb-1", principal_type="user", principal_id="u-1",
        access_role="edit", granted_by="a",
    )
    # Wrong kb_id → not removed.
    assert await backend.remove_kb_acl("kb-other", entry.id) is False
    assert await backend.remove_kb_acl("kb-1", entry.id) is True
    assert await backend.list_kb_acl("kb-1") == []
    assert await backend.remove_kb_acl("kb-1", entry.id) is False  # already gone

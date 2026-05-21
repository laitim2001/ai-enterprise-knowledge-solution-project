"""Postgres-backed RBAC store (W24c F2 per ADR-0027 Option A).

Satisfies the `RbacBackend` Protocol. Async psycopg 3 connection-per-op —
mirrors `PostgresAuditLogBackend` (RBAC reads are infrequent + off the query
hot path, so a pool is not warranted). Idempotent `CREATE TABLE IF NOT EXISTS`
for all 5 RBAC tables on every connect.

F2.1 declares all 5 tables ahead of need: `roles` + `role_permissions` are
read + seeded now; `groups` + `group_members` + `kb_acl` exist so F6 (Groups
tab) / F8 (per-KB ACL) add Protocol methods only — plus, at F6, one additive
`synced_at` column ALTER on `groups` (no breaking migration).

Schema (in the `ekp` database per ADR-0023):

    roles(role_key PK / label / description / tier / active / sort_order /
          created_at)
    role_permissions(role_key / permission_key / area / label / granted /
                     sort_order, PK (role_key, permission_key))
    groups(group_key PK / name / description / source / entra_object_id /
           synced_at / created_at)
    group_members(group_key / user_oid, PK (group_key, user_oid) / added_at)
    kb_acl(id SERIAL PK / kb_id / principal_type / principal_id /
           access_role / created_at, UNIQUE (kb_id, principal_type, principal_id))

`sort_order` carries the seed iteration index so `list_*` can `ORDER BY` a
single column and reproduce the mockup's matrix order.
"""

from __future__ import annotations

from typing import Any, cast

import psycopg
from psycopg.rows import dict_row

from api.schemas.rbac import Group, GroupSource, Role, RoleKey, RolePermission
from storage.rbac_storage import default_roles, permission_matrix_rows

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS roles (
    role_key    TEXT PRIMARY KEY,
    label       TEXT NOT NULL,
    description TEXT NOT NULL,
    tier        INTEGER NOT NULL DEFAULT 1,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS role_permissions (
    role_key       TEXT NOT NULL,
    permission_key TEXT NOT NULL,
    area           TEXT NOT NULL,
    label          TEXT NOT NULL,
    granted        BOOLEAN NOT NULL,
    sort_order     INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (role_key, permission_key)
);
CREATE TABLE IF NOT EXISTS groups (
    group_key       TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    source          TEXT NOT NULL DEFAULT 'local',
    entra_object_id TEXT,
    synced_at       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS group_members (
    group_key TEXT NOT NULL,
    user_oid  TEXT NOT NULL,
    added_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (group_key, user_oid)
);
CREATE TABLE IF NOT EXISTS kb_acl (
    id             SERIAL PRIMARY KEY,
    kb_id          TEXT NOT NULL,
    principal_type TEXT NOT NULL,
    principal_id   TEXT NOT NULL,
    access_role    TEXT NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (kb_id, principal_type, principal_id)
)
"""

_ROLE_COLS = "role_key, label, description, tier, active"
_PERM_COLS = "role_key, permission_key, area, label, granted"

# F6 — additive: `groups` predates `synced_at` (F2 created the table without
# it). IF NOT EXISTS keeps this idempotent on every connect, mirroring the F4
# `users` ALTERs in `postgres_users_store.py`.
_ALTER_GROUPS = "ALTER TABLE groups ADD COLUMN IF NOT EXISTS synced_at TIMESTAMPTZ"


def _row_to_role(row: dict[str, Any]) -> Role:
    return Role(
        role_key=cast(RoleKey, row["role_key"]),
        label=row["label"],
        description=row["description"],
        tier=row["tier"],
        active=row["active"],
    )


def _row_to_role_permission(row: dict[str, Any]) -> RolePermission:
    return RolePermission(
        role_key=cast(RoleKey, row["role_key"]),
        permission_key=row["permission_key"],
        area=row["area"],
        label=row["label"],
        granted=row["granted"],
    )


def _row_to_group(row: dict[str, Any]) -> Group:
    return Group(
        group_key=row["group_key"],
        name=row["name"],
        description=row["description"],
        source=cast(GroupSource, row["source"]),
        entra_object_id=row["entra_object_id"],
        synced_at=row["synced_at"],
        member_count=row["member_count"],
    )


class PostgresRbacBackend:
    """RBAC store backed by Postgres — satisfies the `RbacBackend` Protocol."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def _ensure_schema(self, conn: psycopg.AsyncConnection) -> None:
        async with conn.cursor() as cur:
            await cur.execute(_CREATE_TABLES)
            await cur.execute(_ALTER_GROUPS)

    async def reset(self) -> None:
        async with await psycopg.AsyncConnection.connect(
            self._dsn, row_factory=dict_row
        ) as conn:
            await self._ensure_schema(conn)
            async with conn.cursor() as cur:
                # users table is owned by PostgresUsersStore — left untouched.
                await cur.execute(
                    "TRUNCATE TABLE kb_acl, group_members, groups, role_permissions, roles"
                )

    async def seed_defaults(self) -> None:
        # ON CONFLICT DO NOTHING keeps this idempotent — safe on every startup.
        async with await psycopg.AsyncConnection.connect(
            self._dsn, row_factory=dict_row
        ) as conn:
            await self._ensure_schema(conn)
            async with conn.cursor() as cur:
                for i, role in enumerate(default_roles()):
                    await cur.execute(
                        f"INSERT INTO roles ({_ROLE_COLS}, sort_order) "
                        "VALUES (%s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (role_key) DO NOTHING",
                        (
                            role.role_key,
                            role.label,
                            role.description,
                            role.tier,
                            role.active,
                            i,
                        ),
                    )
                for i, rp in enumerate(permission_matrix_rows()):
                    await cur.execute(
                        f"INSERT INTO role_permissions ({_PERM_COLS}, sort_order) "
                        "VALUES (%s, %s, %s, %s, %s, %s) "
                        "ON CONFLICT (role_key, permission_key) DO NOTHING",
                        (
                            rp.role_key,
                            rp.permission_key,
                            rp.area,
                            rp.label,
                            rp.granted,
                            i,
                        ),
                    )

    async def list_roles(self) -> list[Role]:
        async with await psycopg.AsyncConnection.connect(
            self._dsn, row_factory=dict_row
        ) as conn:
            await self._ensure_schema(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT {_ROLE_COLS} FROM roles ORDER BY sort_order"
                )
                rows = await cur.fetchall()
                return [_row_to_role(r) for r in rows]

    async def get_role(self, role_key: str) -> Role | None:
        async with await psycopg.AsyncConnection.connect(
            self._dsn, row_factory=dict_row
        ) as conn:
            await self._ensure_schema(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT {_ROLE_COLS} FROM roles WHERE role_key = %s", (role_key,)
                )
                row = await cur.fetchone()
                return _row_to_role(row) if row else None

    async def list_role_permissions(
        self, role_key: str | None = None
    ) -> list[RolePermission]:
        where = "WHERE role_key = %s" if role_key is not None else ""
        params: tuple[Any, ...] = (role_key,) if role_key is not None else ()
        async with await psycopg.AsyncConnection.connect(
            self._dsn, row_factory=dict_row
        ) as conn:
            await self._ensure_schema(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT {_PERM_COLS} FROM role_permissions {where} "
                    "ORDER BY sort_order",
                    params,
                )
                rows = await cur.fetchall()
                return [_row_to_role_permission(r) for r in rows]

    async def list_groups(self) -> list[Group]:
        async with await psycopg.AsyncConnection.connect(
            self._dsn, row_factory=dict_row
        ) as conn:
            await self._ensure_schema(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT g.group_key, g.name, g.description, g.source, "
                    "g.entra_object_id, g.synced_at, "
                    "COUNT(gm.user_oid) AS member_count "
                    "FROM groups g "
                    "LEFT JOIN group_members gm ON gm.group_key = g.group_key "
                    "GROUP BY g.group_key, g.name, g.description, g.source, "
                    "g.entra_object_id, g.synced_at "
                    "ORDER BY g.name"
                )
                rows = await cur.fetchall()
                return [_row_to_group(r) for r in rows]

    async def upsert_entra_group(
        self, *, object_id: str, name: str, description: str | None
    ) -> None:
        # group_key = the Entra object id — a stable upsert key (displayName
        # may change). source/synced_at are owned here, not caller-supplied.
        async with await psycopg.AsyncConnection.connect(
            self._dsn, row_factory=dict_row
        ) as conn:
            await self._ensure_schema(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    "INSERT INTO groups "
                    "(group_key, name, description, source, entra_object_id, synced_at) "
                    "VALUES (%s, %s, %s, 'entra', %s, NOW()) "
                    "ON CONFLICT (group_key) DO UPDATE SET "
                    "name = EXCLUDED.name, "
                    "description = EXCLUDED.description, "
                    "synced_at = EXCLUDED.synced_at",
                    (object_id, name, description, object_id),
                )

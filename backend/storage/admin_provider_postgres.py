"""Postgres-backed admin provider config storage (W24-wave-c1 F2 per ADR-0026).

Satisfies the `AdminProviderConfigBackend` Protocol. Connection-per-op via
psycopg 3 async — admin ops are infrequent and off the query hot path, no pool
warranted (parallel to `kb_management.postgres_backend` shape). Idempotent
`CREATE TABLE IF NOT EXISTS` on every connect.

Wired only when `settings.database_url` is set — see
`storage.admin_provider_factory.make_admin_provider_backend`, which lazily
imports this module so an unset `DATABASE_URL` never touches `psycopg`.

Schema (in the `ekp` database per ADR-0023):
    admin_provider_configs(
        provider_id PK,
        category, display_name, endpoint_url, region,
        deployments JSONB, secret_kv_ref, secret_masked_preview,
        last_test_at, last_test_status, last_test_detail,
        last_rotated_at, created_at, updated_at
    )
"""

from __future__ import annotations

from datetime import datetime
from typing import cast

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from api.schemas.admin import (
    ProviderCategory,
    ProviderConfig,
    ProviderDeployment,
    ProviderPatch,
    TestStatus,
)
from storage.admin_provider_storage import ProviderNotFoundError, default_providers

_TABLE = "admin_provider_configs"

_CREATE_TABLE = f"""
CREATE TABLE IF NOT EXISTS {_TABLE} (
    provider_id              TEXT PRIMARY KEY,
    category                 TEXT NOT NULL,
    display_name             TEXT NOT NULL,
    endpoint_url             TEXT,
    region                   TEXT,
    deployments              JSONB NOT NULL DEFAULT '[]'::jsonb,
    settings                 JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    secret_kv_ref            TEXT,
    secret_masked_preview    TEXT,
    last_test_at             TIMESTAMPTZ,
    last_test_status         TEXT NOT NULL DEFAULT 'not_tested',
    last_test_detail         TEXT,
    last_rotated_at          TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL,
    updated_at               TIMESTAMPTZ NOT NULL
)
"""

_COLS = (
    "provider_id, category, display_name, endpoint_url, region, "
    "deployments, settings, secret_kv_ref, secret_masked_preview, "
    "last_test_at, last_test_status, last_test_detail, "
    "last_rotated_at, created_at, updated_at"
)


def _row_to_config(row: dict) -> ProviderConfig:
    return ProviderConfig(
        provider_id=row["provider_id"],
        category=cast(ProviderCategory, row["category"]),
        display_name=row["display_name"],
        endpoint_url=row["endpoint_url"],
        region=row["region"],
        deployments=[ProviderDeployment(**d) for d in row["deployments"]],
        settings=row["settings"],
        secret_kv_ref=row["secret_kv_ref"],
        secret_masked_preview=row["secret_masked_preview"],
        last_test_at=row["last_test_at"],
        last_test_status=cast(TestStatus, row["last_test_status"]),
        last_test_detail=row["last_test_detail"],
        last_rotated_at=row["last_rotated_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _config_params(cfg: ProviderConfig) -> tuple:
    return (
        cfg.provider_id,
        cfg.category,
        cfg.display_name,
        cfg.endpoint_url,
        cfg.region,
        Jsonb([d.model_dump(mode="json") for d in cfg.deployments]),
        Jsonb(cfg.settings),
        cfg.secret_kv_ref,
        cfg.secret_masked_preview,
        cfg.last_test_at,
        cfg.last_test_status,
        cfg.last_test_detail,
        cfg.last_rotated_at,
        cfg.created_at,
        cfg.updated_at,
    )


class PostgresAdminProviderBackend:
    """Postgres-backed admin provider config store. Seeds the 9 defaults on first connect."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    async def _ensure_schema_and_seed(self, conn: psycopg.AsyncConnection) -> None:
        async with conn.cursor() as cur:
            await cur.execute(_CREATE_TABLE)
            # ADR-0072 — additive `settings` column for pre-W102 tables. Idempotent,
            # no separate migration step (mirrors the deployments-column shape).
            await cur.execute(
                f"ALTER TABLE {_TABLE} ADD COLUMN IF NOT EXISTS "
                f"settings JSONB NOT NULL DEFAULT '{{}}'::jsonb"
            )
            # Idempotent seed — only inserts rows missing by provider_id PK.
            # NB: the connection uses dict_row, so rows are dicts — index by column
            # name, not position (`r[0]` KeyErrors on a populated table; surfaced
            # W102 when adding the 10th provider forced the seed-insert branch).
            await cur.execute(f"SELECT provider_id FROM {_TABLE}")
            existing = {r["provider_id"] for r in await cur.fetchall()}
            for cfg in default_providers():
                if cfg.provider_id in existing:
                    continue
                placeholders = ",".join(["%s"] * 15)
                await cur.execute(
                    f"INSERT INTO {_TABLE} ({_COLS}) VALUES ({placeholders})",
                    _config_params(cfg),
                )

    async def list_all(self) -> list[ProviderConfig]:
        async with await psycopg.AsyncConnection.connect(self._dsn, row_factory=dict_row) as conn:
            await self._ensure_schema_and_seed(conn)
            async with conn.cursor() as cur:
                await cur.execute(f"SELECT {_COLS} FROM {_TABLE} ORDER BY provider_id")
                rows = await cur.fetchall()
                return [_row_to_config(r) for r in rows]

    async def get(self, provider_id: str) -> ProviderConfig:
        async with await psycopg.AsyncConnection.connect(self._dsn, row_factory=dict_row) as conn:
            await self._ensure_schema_and_seed(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"SELECT {_COLS} FROM {_TABLE} WHERE provider_id = %s", (provider_id,)
                )
                row = await cur.fetchone()
                if row is None:
                    raise ProviderNotFoundError(f"provider {provider_id!r} not found")
                return _row_to_config(row)

    async def update(self, provider_id: str, patch: ProviderPatch) -> ProviderConfig:
        # Build SET clause from set fields only; leaves untouched columns alone.
        patch_dict = {k: v for k, v in patch.model_dump(exclude_unset=True).items() if v is not None}
        # settings is a dict → wrap for JSONB binding (ADR-0072); other fields are scalars.
        if "settings" in patch_dict:
            patch_dict["settings"] = Jsonb(patch_dict["settings"])
        if not patch_dict:
            # No-op PATCH still returns the current row (idempotent endpoint contract).
            return await self.get(provider_id)
        set_clauses = ", ".join(f"{k} = %s" for k in patch_dict)
        set_clauses += ", updated_at = NOW()"
        params: tuple = tuple(patch_dict.values()) + (provider_id,)
        async with await psycopg.AsyncConnection.connect(self._dsn, row_factory=dict_row) as conn:
            await self._ensure_schema_and_seed(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE {_TABLE} SET {set_clauses} WHERE provider_id = %s "
                    f"RETURNING {_COLS}",
                    params,
                )
                row = await cur.fetchone()
                if row is None:
                    raise ProviderNotFoundError(f"provider {provider_id!r} not found")
                return _row_to_config(row)

    async def update_test_result(
        self,
        provider_id: str,
        *,
        status: TestStatus,
        detail: str | None,
        tested_at: datetime,
    ) -> ProviderConfig:
        async with await psycopg.AsyncConnection.connect(self._dsn, row_factory=dict_row) as conn:
            await self._ensure_schema_and_seed(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE {_TABLE} SET last_test_status = %s, last_test_detail = %s, "
                    f"last_test_at = %s, updated_at = NOW() "
                    f"WHERE provider_id = %s RETURNING {_COLS}",
                    (status, detail, tested_at, provider_id),
                )
                row = await cur.fetchone()
                if row is None:
                    raise ProviderNotFoundError(f"provider {provider_id!r} not found")
                return _row_to_config(row)

    async def update_rotation_timestamp(
        self,
        provider_id: str,
        *,
        rotated_at: datetime,
        secret_masked_preview: str,
    ) -> ProviderConfig:
        async with await psycopg.AsyncConnection.connect(self._dsn, row_factory=dict_row) as conn:
            await self._ensure_schema_and_seed(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE {_TABLE} SET last_rotated_at = %s, secret_masked_preview = %s, "
                    f"updated_at = NOW() "
                    f"WHERE provider_id = %s RETURNING {_COLS}",
                    (rotated_at, secret_masked_preview, provider_id),
                )
                row = await cur.fetchone()
                if row is None:
                    raise ProviderNotFoundError(f"provider {provider_id!r} not found")
                return _row_to_config(row)

    async def update_deployment_alert_threshold(
        self,
        provider_id: str,
        deployment_id: str,
        *,
        alert_threshold_pct: int,
    ) -> ProviderConfig:
        current = await self.get(provider_id)
        new_deployments = []
        found = False
        for d in current.deployments:
            if d.deployment_id == deployment_id:
                new_deployments.append(d.model_copy(update={"alert_threshold_pct": alert_threshold_pct}))
                found = True
            else:
                new_deployments.append(d)
        if not found:
            raise ProviderNotFoundError(
                f"deployment {deployment_id!r} not found in provider {provider_id!r}"
            )
        new_json = Jsonb([d.model_dump(mode="json") for d in new_deployments])
        async with await psycopg.AsyncConnection.connect(self._dsn, row_factory=dict_row) as conn:
            await self._ensure_schema_and_seed(conn)
            async with conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE {_TABLE} SET deployments = %s, updated_at = NOW() "
                    f"WHERE provider_id = %s RETURNING {_COLS}",
                    (new_json, provider_id),
                )
                row = await cur.fetchone()
                if row is None:
                    raise ProviderNotFoundError(f"provider {provider_id!r} not found")
                return _row_to_config(row)

"""Audit log storage tests (W24-wave-c1 F4.8 per ADR-0026;
W24b-wave-c2 F6 filter + cursor cases)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from storage.audit_log_storage import InMemoryAuditLogBackend


@pytest.mark.asyncio
async def test_append_assigns_incrementing_ids() -> None:
    backend = InMemoryAuditLogBackend()
    e1 = await backend.append(
        actor="alice@ricoh.com",
        action="connection_patch",
        resource="admin_provider_configs/azure_openai",
        payload={"endpoint_url": "https://new.openai.azure.com"},
    )
    e2 = await backend.append(
        actor=None,
        action="identity_patch",
        resource="admin_identity_config/tenant",
        payload={"tenant_id": "new-tenant"},
    )
    assert e1.id == 1
    assert e2.id == 2
    assert e1.created_at <= e2.created_at


@pytest.mark.asyncio
async def test_append_preserves_actor_and_payload() -> None:
    backend = InMemoryAuditLogBackend()
    e = await backend.append(
        actor="bob@ricoh.com",
        action="connection_rotate_secret",
        resource="admin_provider_configs/cohere",
        payload={"kv_ref": "ekp-cohere-api-key", "masked_preview": "***xY1z"},
    )
    assert e.actor == "bob@ricoh.com"
    assert e.action == "connection_rotate_secret"
    assert e.payload == {"kv_ref": "ekp-cohere-api-key", "masked_preview": "***xY1z"}


@pytest.mark.asyncio
async def test_append_allows_none_actor_for_system_actions() -> None:
    backend = InMemoryAuditLogBackend()
    e = await backend.append(
        actor=None,
        action="api_keys_alert_threshold_patch",
        resource="admin_provider_configs/azure_openai/llm_primary",
        payload={"alert_threshold_pct": 75},
    )
    assert e.actor is None


@pytest.mark.asyncio
async def test_list_recent_returns_newest_first() -> None:
    backend = InMemoryAuditLogBackend()
    for i in range(5):
        await backend.append(
            actor=None,
            action="connection_test",
            resource=f"admin_provider_configs/provider_{i}",
            payload={"status": "ok"},
        )
    rows = await backend.list_recent()
    assert len(rows) == 5
    # Newest first — last inserted (provider_4) leads.
    assert rows[0].resource == "admin_provider_configs/provider_4"
    assert rows[-1].resource == "admin_provider_configs/provider_0"


@pytest.mark.asyncio
async def test_list_recent_respects_limit() -> None:
    backend = InMemoryAuditLogBackend()
    for i in range(10):
        await backend.append(
            actor=None, action="connection_test", resource=f"r_{i}", payload=None
        )
    rows = await backend.list_recent(limit=3)
    assert len(rows) == 3


@pytest.mark.asyncio
async def test_factory_returns_in_memory_when_database_url_unset() -> None:
    from storage.audit_log_factory import make_audit_log_backend
    from storage.settings import Settings

    settings = Settings(database_url="")
    backend = make_audit_log_backend(settings)
    assert isinstance(backend, InMemoryAuditLogBackend)


# ---- W24b F6 — filter + cursor ---------------------------------------------


@pytest.mark.asyncio
async def test_list_recent_filter_by_action_type() -> None:
    backend = InMemoryAuditLogBackend()
    for _ in range(3):
        await backend.append(
            actor=None, action="connection_patch", resource="r", payload=None
        )
    for _ in range(2):
        await backend.append(
            actor=None, action="identity_patch", resource="r", payload=None
        )
    rows = await backend.list_recent(action_type="identity_patch")
    assert len(rows) == 2
    assert all(r.action == "identity_patch" for r in rows)


@pytest.mark.asyncio
async def test_list_recent_filter_by_cursor_walks_strictly_older() -> None:
    backend = InMemoryAuditLogBackend()
    for i in range(10):
        await backend.append(
            actor=None, action="connection_test", resource=f"r_{i}", payload=None
        )
    # ids 1..10; cursor=6 is exclusive → strictly-older ids 5..1.
    rows = await backend.list_recent(cursor=6)
    assert [r.id for r in rows] == [5, 4, 3, 2, 1]


@pytest.mark.asyncio
async def test_list_recent_filter_by_since() -> None:
    backend = InMemoryAuditLogBackend()
    for i in range(4):
        await backend.append(
            actor=None, action="connection_test", resource=f"r_{i}", payload=None
        )
    # Backdate the two oldest rows so `since` filters them out.
    old = datetime(2020, 1, 1, tzinfo=UTC)
    backend._rows[0].created_at = old
    backend._rows[1].created_at = old
    rows = await backend.list_recent(
        since=datetime(2021, 1, 1, tzinfo=UTC)
    )
    assert len(rows) == 2  # only the two recent rows survive


@pytest.mark.asyncio
async def test_list_recent_combined_action_type_and_cursor() -> None:
    backend = InMemoryAuditLogBackend()
    await backend.append(
        actor=None, action="connection_patch", resource="a", payload=None
    )  # id 1
    await backend.append(
        actor=None, action="identity_patch", resource="b", payload=None
    )  # id 2
    await backend.append(
        actor=None, action="connection_patch", resource="c", payload=None
    )  # id 3
    await backend.append(
        actor=None, action="connection_patch", resource="d", payload=None
    )  # id 4
    # connection_patch + cursor=4 → id 3, id 1 (id 2 wrong action, id 4 not < 4).
    rows = await backend.list_recent(action_type="connection_patch", cursor=4)
    assert [r.id for r in rows] == [3, 1]


# ---- W24c F7 — 90d retention prune -----------------------------------------


@pytest.mark.asyncio
async def test_prune_expired_removes_old_rows() -> None:
    backend = InMemoryAuditLogBackend()
    for i in range(4):
        await backend.append(
            actor=None, action="connection_test", resource=f"r_{i}", payload=None
        )
    # Backdate the two oldest rows well past any retention window.
    old = datetime(2020, 1, 1, tzinfo=UTC)
    backend._rows[0].created_at = old
    backend._rows[1].created_at = old
    removed = await backend.prune_expired(90)
    assert removed == 2
    assert len(await backend.list_recent()) == 2


@pytest.mark.asyncio
async def test_prune_expired_keeps_recent_rows() -> None:
    backend = InMemoryAuditLogBackend()
    for i in range(3):
        await backend.append(
            actor=None, action="connection_test", resource=f"r_{i}", payload=None
        )
    removed = await backend.prune_expired(90)
    assert removed == 0
    assert len(await backend.list_recent()) == 3


@pytest.mark.asyncio
async def test_prune_expired_respects_retention_days() -> None:
    backend = InMemoryAuditLogBackend()
    entry = await backend.append(
        actor=None, action="connection_test", resource="r", payload=None
    )
    # 10 days old — survives a 90d window, pruned by a 1d window.
    entry.created_at = datetime.now(UTC) - timedelta(days=10)
    assert await backend.prune_expired(90) == 0
    assert await backend.prune_expired(1) == 1

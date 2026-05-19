"""Admin provider backend factory (W24-wave-c1 F2 per ADR-0026).

Picks `PostgresAdminProviderBackend` when `settings.database_url` is set, else
`InMemoryAdminProviderBackend`. Mirrors the `kb_management.factory.make_kb_backend`
+ ADR-0023 lazy-import shape — unset `DATABASE_URL` never touches `psycopg`.
"""

from __future__ import annotations

from storage.admin_provider_storage import (
    AdminProviderConfigBackend,
    InMemoryAdminProviderBackend,
)
from storage.settings import Settings


def make_admin_provider_backend(settings: Settings) -> AdminProviderConfigBackend:
    """Return a Postgres-backed admin provider store when `database_url` is set, else in-memory."""
    if settings.database_url:
        from storage.admin_provider_postgres import PostgresAdminProviderBackend

        return PostgresAdminProviderBackend(settings.database_url)
    return InMemoryAdminProviderBackend()

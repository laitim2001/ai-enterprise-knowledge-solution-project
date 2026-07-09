"""pytest session bootstrap — store-backend test isolation (BUG-008).

The developer `.env` may set `DATABASE_URL` to wire the ADR-0023 Postgres-backed
stores. pytest reads the same `.env` (via `storage.settings.Settings`), so
without isolation the whole suite would silently switch to Postgres and the
in-memory-mode tests (KB list, auth sessions, `/health` postgres
`not_configured`) would fail against Postgres-backed behaviour.

Force `DATABASE_URL` empty here, at conftest import time — before any test
module imports `api.server` and builds the `lru_cache`d `Settings`. An empty
environment variable wins over the `.env` file in Pydantic Settings precedence,
so the suite always exercises the in-memory stores deterministically.
Postgres-path tests opt in explicitly via `Settings(database_url=...)` and are
unaffected by this.
"""

import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from azure.core.exceptions import ResourceNotFoundError

# Must run before the first `Settings()` construction — conftest.py is imported
# by pytest ahead of every test module under `tests/`.
os.environ["DATABASE_URL"] = ""

# W44 F4.4 — disable the eval-only per-query retrieve throttle (eval/throttle.py)
# during tests so the runner/orchestrator unit tests don't sleep 1s per mocked
# query. The throttle's own unit tests pass an explicit `throttle_s` to exercise
# the delay; everything else reads this env knob at call time.
os.environ["EVAL_RETRIEVE_THROTTLE_S"] = "0"


@pytest.fixture(autouse=True)
def _block_real_async_blob_clients(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stop ANY test from constructing a real `azure.storage.blob.aio` client (BUG-045 / B-23).

    Both `ingestion/screenshots/uploader.py` and `ingestion/source_store.py` build an
    async client via `BlobServiceClient.from_connection_string(...)`. An endpoint test
    that reaches these (upload / reindex / eval / ...) would, without a real backend
    (CI has no Azurite), block on the network — the best-effort `try/except` in those
    modules catches *exceptions*, NOT a blocked socket, so `pytest -q` hangs instead of
    fast-failing. That hang was masked only because CI lacked `aiohttp` (the async
    transport `ImportError`'d fast); declaring `aiohttp` (B-22) unmasked it.

    Patch the shared choke point — `BlobServiceClient.from_connection_string` — so the
    async client is a no-network mock: `async with` works, `create_container` /
    `upload_blob` succeed, and the read HEAD-checks report "absent" (so
    `download_source_document` → None / the uploader dedup treats the blob as new).

    Tests needing specific blob behaviour override this at a narrower scope, which wins
    over this autouse default:
      - `test_source_store` / `test_screenshots` patch the module-local `BlobServiceClient`;
      - `test_kb_reindex` / `test_doc_profile_backfill` patch `download_source_document`.
    """

    def _make_blob_service(*_args: object, **_kwargs: object) -> MagicMock:
        blob = MagicMock(name="BlobClient")
        blob.upload_blob = AsyncMock()
        # HEAD-check / download report "absent": download_source_document → None
        # (skipped_no_source); the uploader dedup then treats the blob as new.
        blob.download_blob = AsyncMock(side_effect=ResourceNotFoundError("mocked: no blob"))
        blob.get_blob_properties = AsyncMock(side_effect=ResourceNotFoundError("mocked: no blob"))
        blob.url = "http://mock.invalid/blob"

        svc = MagicMock(name="BlobServiceClient")
        svc.__aenter__ = AsyncMock(return_value=svc)
        svc.__aexit__ = AsyncMock(return_value=None)
        svc.close = AsyncMock()
        svc.create_container = AsyncMock()
        svc.get_blob_client = MagicMock(return_value=blob)
        svc.get_container_client = MagicMock(return_value=blob)
        return svc

    monkeypatch.setattr(
        "azure.storage.blob.aio.BlobServiceClient.from_connection_string",
        _make_blob_service,
    )

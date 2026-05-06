"""C07 Observability — structlog config + Langfuse SDK lifecycle.

W1 baseline: structlog JSON renderer + Langfuse host log line.
W8 D5 F5.1: real Langfuse SDK init + flush hook per architecture.md §3.2
+ §7.4 Day-2 Readiness (all query / retrieval / LLM call logged to Langfuse).

The SDK is initialised lazily as a module-level singleton:
  - When `langfuse_public_key` + `langfuse_secret_key` populated → real client
  - When either missing → singleton stays None (local dev / CI no-op)

Service modules read `get_langfuse_client()` and emit traces / scores / cost
events when the client is non-None. F5.3 `/feedback` + F5.2 cost dashboard +
W9+ progressive `@observe` decoration on query / retrieval / synthesis paths
all funnel through this single accessor — Karpathy §1.2 simplicity-first.

Lifespan integration (api/server.py):
  - lifespan startup → `init_tracer(settings)` (existing contract preserved)
  - lifespan shutdown → `flush_tracer()` drains queued events before process
    exit so short-lived tasks (CI / one-shot scripts) don't lose traces.
"""

from __future__ import annotations

import structlog

from storage.settings import Settings

# Module-level singleton. Typed as Any to avoid import-time dependency on the
# langfuse package — keeps `from observability.langfuse_tracer import ...`
# cheap and lets tests substitute via `_set_langfuse_client_for_tests`.
_langfuse_client: object | None = None


def init_tracer(settings: Settings) -> None:
    """Initialise observability layer (W1 contract preserved + W8 D5 SDK wire).

    structlog config runs unconditionally — audit middleware + structlog JSON
    renderer must work even when Langfuse cred is absent (local dev / CI).
    Langfuse client init is best-effort:
      - Missing keys → leave singleton None, log a structured note
      - Import failure → leave singleton None, log a structured warning
      - Init failure → leave singleton None, log a structured error
    Init never raises — observability layer must never break the API surface.
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(settings.log_level_int),
    )
    log = structlog.get_logger()

    global _langfuse_client
    _langfuse_client = None

    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        log.info(
            "tracer_initialized",
            langfuse_host=settings.langfuse_host,
            environment=settings.environment,
            feature_auth_enabled=settings.feature_auth_enabled,
            langfuse_sdk_status="not_configured",
        )
        return

    try:
        from langfuse import Langfuse
    except ImportError as exc:
        log.warning(
            "tracer_initialized",
            langfuse_host=settings.langfuse_host,
            environment=settings.environment,
            feature_auth_enabled=settings.feature_auth_enabled,
            langfuse_sdk_status="import_failed",
            error=str(exc),
        )
        return

    try:
        _langfuse_client = Langfuse(
            host=settings.langfuse_host,
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
        )
    except Exception as exc:  # noqa: BLE001 — tracer must never break server boot
        log.error(
            "tracer_initialized",
            langfuse_host=settings.langfuse_host,
            environment=settings.environment,
            feature_auth_enabled=settings.feature_auth_enabled,
            langfuse_sdk_status="init_failed",
            error=str(exc),
        )
        return

    log.info(
        "tracer_initialized",
        langfuse_host=settings.langfuse_host,
        environment=settings.environment,
        feature_auth_enabled=settings.feature_auth_enabled,
        langfuse_sdk_status="wired",
    )


def get_langfuse_client() -> object | None:
    """Return the lazy-initialised Langfuse client, or None when not configured.

    Service modules (F5.3 feedback + F5.2 cost dashboard + W9+ @observe wraps)
    branch on `if client is not None` so the same code path works on local dev
    (no cred → None) and Beta+ (cred present → real client).
    """
    return _langfuse_client


def flush_tracer() -> None:
    """Drain queued Langfuse events before process exit.

    Called from lifespan shutdown (FastAPI) + on-demand from tests / one-shot
    eval scripts. No-op when client is None or flush raises — observability
    must never block process shutdown.
    """
    client = _langfuse_client
    if client is None:
        return
    flush = getattr(client, "flush", None)
    if flush is None:
        return
    try:
        flush()
    except Exception:  # noqa: BLE001 — never block shutdown on flush error
        log = structlog.get_logger()
        log.warning("langfuse_flush_failed")


def _set_langfuse_client_for_tests(client: object | None) -> None:
    """Test-only escape hatch — substitute the singleton from a fixture.

    Production code MUST go through `init_tracer` + `get_langfuse_client`.
    """
    global _langfuse_client
    _langfuse_client = client

"""C07 — `GET /health` per-component liveness payload (W20 F2.1 per W19 F2 §3.1 item 1).

Extracted from `api/server.py`'s inline `{"status": "ok"}` route. Now returns the
per-component connectivity payload the `/dashboard` System health card needs:
each of the 5 Tier 1 backends (Azure AI Search / Azure OpenAI / Cohere reranker /
Langfuse / Postgres) reports `ok` / `not_configured` / `degraded` / `error`.

**Wave A scope = configuration-state check** (no real I/O pings):
  - The check looks at whether each component's singleton was successfully
    initialized at lifespan startup (`app.state.*` is not None) — i.e. whether
    the env vars / config wired together at process boot. This catches the
    most common operator-error class (missing env / bad endpoint) and is
    side-effect-free, so the `/dashboard` 60s poll is cheap.
  - Real-I/O liveness pings (`SearchClient.get_service_statistics()`,
    Postgres `SELECT 1`, Cohere reranker echo) are deliberately Wave B+ polish
    per Karpathy §1.2 — they trade flap risk + cost for marginal signal until
    Beta cohort traffic exposes real outages.
  - `latency_ms` is therefore `None` across the board for Wave A; the schema
    keeps the field so the Wave B+ pings can populate it without a breaking
    response-shape change.

Azure Container Apps liveness probe still gets a 200 + `status: "ok"|"degraded"`
top-level (it parses neither field) — keeping the route unaudited (W7 D3 audit
middleware) and unauthenticated.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from observability.langfuse_tracer import get_langfuse_client
from storage.settings import get_settings

router = APIRouter(tags=["meta"])

# Per-component status taxonomy. `not_configured` is distinct from `degraded`
# because Cohere + Postgres are legitimately optional (Q5 Path A; ADR-0023
# in-memory fallback) — the dashboard should render those as grey/neutral, not red.
ComponentStatus = Literal["ok", "not_configured", "degraded", "error"]

# Top-level rolls down to `ok` only if every component is `ok` OR `not_configured`;
# any `degraded` / `error` flips to `degraded` (single signal for the dashboard top dot).
OverallStatus = Literal["ok", "degraded"]


class ComponentHealth(BaseModel):
    """Per-component liveness signal."""

    status: ComponentStatus
    latency_ms: int | None = Field(
        default=None,
        description=(
            "Real-I/O ping latency (Wave B+); always None in Wave A "
            "(configuration-state check only)."
        ),
    )
    detail: str | None = Field(
        default=None,
        description="Optional human-readable note (e.g. 'no DATABASE_URL — in-memory fallback').",
    )


class HealthResponse(BaseModel):
    """W20 F2.1 — replaces the W1 `{status: 'ok'}` shape with per-component payload."""

    status: OverallStatus
    components: dict[str, ComponentHealth]


def _check_azure_search(request: Request) -> ComponentHealth:
    """Azure AI Search — singleton wired into `app.state.retrieval_engine` at lifespan startup."""
    engine = getattr(request.app.state, "retrieval_engine", None)
    if engine is None:
        return ComponentHealth(
            status="degraded",
            detail="retrieval_engine not initialized — check Azure AI Search env / lifespan logs",
        )
    return ComponentHealth(status="ok")


def _check_azure_openai(request: Request) -> ComponentHealth:
    """Azure OpenAI — embedder singleton wired into `app.state.embedder` at lifespan startup."""
    embedder = getattr(request.app.state, "embedder", None)
    if embedder is None:
        return ComponentHealth(
            status="degraded",
            detail="embedder not initialized — check Azure OpenAI env / lifespan logs",
        )
    return ComponentHealth(status="ok")


def _check_cohere(request: Request) -> ComponentHealth:
    """Cohere reranker — optional per Q5 Path A; `None` reranker = `not_configured`."""
    engine = getattr(request.app.state, "retrieval_engine", None)
    if engine is None:
        return ComponentHealth(
            status="degraded",
            detail="retrieval_engine not initialized — Cohere status indeterminate",
        )
    reranker = getattr(engine, "reranker", None)
    if reranker is None:
        return ComponentHealth(
            status="not_configured",
            detail="Cohere reranker not configured (Q5 Path A optional)",
        )
    return ComponentHealth(status="ok")


def _check_langfuse() -> ComponentHealth:
    """Langfuse — `get_langfuse_client()` returns the v2-pinned SDK client or None."""
    client = get_langfuse_client()
    if client is None:
        return ComponentHealth(
            status="not_configured",
            detail="Langfuse not configured (LANGFUSE_PUBLIC_KEY / SECRET_KEY unset)",
        )
    return ComponentHealth(status="ok")


def _check_postgres() -> ComponentHealth:
    """Postgres — checks `settings.database_url` (ADR-0023; unset = in-memory fallback)."""
    settings = get_settings()
    if not settings.database_url:
        return ComponentHealth(
            status="not_configured",
            detail="DATABASE_URL unset — in-memory KB + users store (ADR-0023 fallback)",
        )
    # Wave A scope: don't run a real `SELECT 1` ping here (would flap + add 60s
    # poll cost). The fact that `database_url` is set + the process started
    # means `PostgresKBBackend` was instantiated successfully via `make_kb_backend`
    # — sufficient signal for the dashboard dot. Wave B+ may add a real ping.
    return ComponentHealth(status="ok")


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Liveness probe + per-component connectivity payload.

    Azure Container Apps health probe target — still returns 200; the probe
    parses neither `status` nor `components`. The `/dashboard` System health
    card consumes the full payload (W20 F2 per ADR-0030 absorbed scope).
    """
    components = {
        "azure_search": _check_azure_search(request),
        "azure_openai": _check_azure_openai(request),
        "cohere": _check_cohere(request),
        "langfuse": _check_langfuse(),
        "postgres": _check_postgres(),
    }

    # Roll-up: `ok` only if no component flagged `degraded` or `error`.
    overall: OverallStatus = (
        "ok"
        if all(c.status in {"ok", "not_configured"} for c in components.values())
        else "degraded"
    )
    return HealthResponse(status=overall, components=components)

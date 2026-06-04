"""EKP FastAPI application entry point.

Per architecture.md §4.1 + §4.4: exposes 18 RESTful endpoints across 8 routers.
W1 scaffold: routes registered, return 501 for non-trivial endpoints (real impl per §6.1 sprint).
"""

# Use OS trust store (Windows Cert Store) for TLS verification so Ricoh corp
# proxy SSL inspection is honoured. Must run before any ssl/urllib3/httpx import.
import truststore

truststore.inject_into_ssl()

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import get_current_user
from api.error_handlers import register_error_handlers
from api.middleware import AuditLogMiddleware, RateLimitMiddleware
from api.routes import (
    auth as auth_routes,
)
from api.routes import (
    chunking,
    chunks,
    config_test,
    conversations,
    debug,
    documents,
    feedback,
    groups,
    health,
    kb,
    kb_acl,
    observability,
    query,
    retrieval_test,
    roles,
    screenshots,
    users,
)
from api.routes import (
    eval as eval_routes,
)
from api.routes.admin import api_keys as admin_api_keys
from api.routes.admin import audit_log as admin_audit_log
from api.routes.admin import connections as admin_connections
from api.routes.admin import identity as admin_identity
from api.routes.admin import usage_stats as admin_usage_stats
from generation.crag import CragGrader, CragLoop
from generation.query_reformulator import QueryReformulator
from generation.synthesizer import Synthesizer
from indexing.populate import IndexPopulator  # noqa: E402 — truststore-after-imports
from ingestion.chunker.layout_aware import LayoutAwareChunker  # noqa: E402
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder
from observability.langfuse_tracer import flush_tracer, init_tracer
from retrieval.hybrid import HybridSearcher
from retrieval.reranker.base import Reranker
from retrieval.reranker.factory import make_reranker
from retrieval.retrieval_engine import RetrievalEngine
from storage.admin_identity_factory import make_admin_identity_backend
from storage.admin_provider_factory import make_admin_provider_backend
from storage.audit_log_factory import make_audit_log_backend
from storage.key_vault_factory import make_key_vault_provider
from storage.rbac_factory import make_rbac_backend
from storage.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_tracer(settings)

    # Embedder + searcher + reranker + synthesizer + populator are all context-managed;
    # we manually enter/exit so they stay open across requests.
    embedder: AzureOpenAIEmbedder | None = None
    searcher: HybridSearcher | None = None
    reranker: Reranker | None = None
    synthesizer: Synthesizer | None = None
    crag_grader: CragGrader | None = None
    populator: IndexPopulator | None = None
    # W25 F3 D4 — ADR-0034 query reformulator (cheap-LLM variant generator
    # for RAG-fusion). Wired only when `enable_query_expansion=True` to
    # avoid spinning up an extra AsyncAzureOpenAI client for the default
    # baseline path.
    query_reformulator: QueryReformulator | None = None
    app.state.retrieval_engine = None
    app.state.synthesizer = None
    app.state.crag_loop = None
    app.state.query_reformulator = None
    # CH-001 — ingestion-side state (embedder exposed for the ingestion orchestrator;
    # populator owned here so POST /kb / POST /kb/{kb_id}/documents / DELETE /kb route
    # handlers can call create_index_for_kb / upload / delete_doc / delete_index without
    # re-instantiating Azure clients per request; chunker is stateless).
    app.state.embedder = None
    app.state.index_populator = None

    # W45 / ADR-0042 — per-KB ingest-time chunker image cap. The factory builds a
    # chunker with a per-KB cap when a KB sets `KbConfig.chunker_max_images_per_chunk`;
    # the singleton below carries the global cap and serves the inherit path (cap=None)
    # + every existing caller/test that reads `ingestion_chunker`. server.py owns the
    # concrete-class construction so the ingest route (`documents.py`) stays decoupled.
    def _make_ingestion_chunker(cap: int | None) -> LayoutAwareChunker:
        return LayoutAwareChunker(max_images_per_chunk=cap)

    app.state.make_ingestion_chunker = _make_ingestion_chunker
    app.state.ingestion_chunker = _make_ingestion_chunker(settings.chunker_max_images_per_chunk)

    # W24-wave-c1 F1 + F2 — Key Vault provider + admin provider config backend.
    # Both factories pick lazy-imported production impls only when their env
    # vars are set (KEY_VAULT_URL / DATABASE_URL); unset → process-local fallbacks
    # (EnvVarProvider + InMemoryAdminProviderBackend). Mirrors the ADR-0023
    # make_kb_backend pattern; no startup cost when neither is configured.
    app.state.key_vault_provider = make_key_vault_provider(settings)
    app.state.admin_provider_backend = make_admin_provider_backend(settings)
    # F3 — admin identity config backend (5 sub-resources per ADR-0026 Option B).
    app.state.admin_identity_backend = make_admin_identity_backend(settings)
    # F4 — audit log backend (write-mostly Wave C1; read endpoint = Wave C2 / F5).
    # W24c F7 — prune entries past the 90d retention window at startup
    # (best-effort; Tier 1 has no scheduler — restart/deploy triggers the prune).
    audit_log_backend = make_audit_log_backend(settings)
    await audit_log_backend.prune_expired(90)
    app.state.audit_log_backend = audit_log_backend
    # W24c F5 — RBAC backend (roles + permissions matrix). Seeded at startup —
    # `InMemoryRbacBackend` is restart-wiped; `seed_defaults` is idempotent so
    # the Postgres path is a no-op once the rows exist.
    rbac_backend = make_rbac_backend(settings)
    await rbac_backend.seed_defaults()
    app.state.rbac_backend = rbac_backend

    if settings.azure_openai_api_key and settings.azure_search_admin_key:
        embedder = AzureOpenAIEmbedder(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment=settings.azure_openai_deployment_embedding,
            dimensions=settings.embedding_dimension,
        )
        searcher = HybridSearcher(
            endpoint=settings.azure_search_endpoint,
            admin_key=settings.azure_search_admin_key,
            index_name=settings.azure_search_default_index,
            image_weight=settings.retrieval_image_low_value_weight,  # ADR-0035 W25 F5 D2
            use_semantic_ranker=settings.hybrid_use_semantic_ranker,  # W42 ADR-0039
            semantic_config_name=settings.azure_semantic_config_name,
        )
        populator = IndexPopulator(
            endpoint=settings.azure_search_endpoint,
            admin_key=settings.azure_search_admin_key,
            index_name=settings.azure_search_default_index,
        )
        await embedder.__aenter__()
        await searcher.__aenter__()
        await populator.__aenter__()
        # Expose embedder + populator to ingestion routes (CH-001); the existing
        # RetrievalEngine wraps the same embedder for query embedding — sharing is
        # safe because the embedder is a stateless async httpx client.
        app.state.embedder = embedder
        app.state.index_populator = populator

        # Optional Cohere reranker (Path A Marketplace per Q5 Resolved); factory
        # returns None when cohere_endpoint or cohere_api_key not populated.
        reranker = make_reranker(settings)
        if reranker is not None:
            await reranker.__aenter__()  # type: ignore[attr-defined]

        app.state.retrieval_engine = RetrievalEngine(
            embedder=embedder,
            searcher=searcher,
            reranker=reranker,
            hybrid_overfetch_for_rerank=settings.hybrid_top_k_retrieval,
            reranker_cross_section_deboost=settings.reranker_cross_section_deboost,
            reranker_section_path_prefix_depth=settings.reranker_section_path_prefix_depth,
            reranker_overfetch_multiplier=settings.reranker_overfetch_multiplier,
        )

        # Synthesizer reuses the same Azure OpenAI endpoint+key but a different
        # deployment (gpt-5.5 chat model vs embedding deployment).
        synthesizer = Synthesizer(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment=settings.azure_openai_deployment_llm_primary,
            timeout_s=settings.synthesizer_request_timeout_s,
        )
        await synthesizer.__aenter__()
        app.state.synthesizer = synthesizer

        # CRAG L2 grader uses GPT-5.4-mini (judge deployment) — separate Azure
        # OpenAI client wrapping the same endpoint+key. CragLoop orchestrates
        # grade → maybe rewrite + re-fetch + re-synth around the synthesizer.
        crag_grader = CragGrader(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment=settings.azure_openai_deployment_llm_judge,
        )
        await crag_grader.__aenter__()
        app.state.crag_loop = CragLoop(
            retrieval_engine=app.state.retrieval_engine,
            synthesizer=synthesizer,
            grader=crag_grader,
            threshold=settings.crag_confidence_threshold,
            max_corrections=settings.crag_max_reformulations,
        )

        # W25 F3 D4 — Query reformulator (ADR-0034). Spin up only when the
        # feature is enabled to avoid an extra AsyncAzureOpenAI client for
        # the default-off Tier 1 baseline path.
        if settings.enable_query_expansion:
            query_reformulator = QueryReformulator(
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                deployment=settings.azure_openai_deployment_llm_judge,
                max_variants=settings.query_expansion_max_variants,
                latency_cap_s=settings.query_expansion_latency_cap_s,
            )
            await query_reformulator.__aenter__()
            app.state.query_reformulator = query_reformulator

    try:
        yield
    finally:
        if query_reformulator is not None:
            await query_reformulator.__aexit__(None, None, None)
        if crag_grader is not None:
            await crag_grader.__aexit__(None, None, None)
        if synthesizer is not None:
            await synthesizer.__aexit__(None, None, None)
        if reranker is not None:
            await reranker.__aexit__(None, None, None)  # type: ignore[attr-defined]
        if populator is not None:
            await populator.__aexit__(None, None, None)
        if embedder is not None:
            await embedder.__aexit__(None, None, None)
        if searcher is not None:
            await searcher.__aexit__(None, None, None)
        # W8 D5 F5.1 — drain Langfuse queue before process exit so short-lived
        # tasks (CI / one-shot scripts) don't lose trace events.
        flush_tracer()


app = FastAPI(
    title="EKP API",
    description="Enterprise Knowledge Platform — Tier 1 Foundation",
    version="0.1.0",
    lifespan=lifespan,
)

# W7 D4 F4.1 — uniform ApiError envelope for all 4xx + 5xx + ValidationError.
# Wired before middleware so middleware-raised HTTPException (rate limit 429
# from F2; auth Depends 401 from F1.3; audit fail-closed) all return the
# same {"error": {...}} shape — frontend error boundary (F4.2) never sees
# raw stack traces or implementation detail.
register_error_handlers(app)

# W7 D2 F2 — token-bucket rate limiter scoped to the same routers as auth
# (Karpathy §1.3 surgical: shared protected prefix list keeps F1.3 + F2 in
# lock-step). 50 req/min + 5 concurrent per user (architecture.md §8.1 R5).
# W7 D3 F1.5 — /auth/** auth endpoints also rate-limited; they are themselves
# auth-protected via in-route Depends(get_current_user).
_PROTECTED_PREFIXES = ("/query", "/kb", "/feedback", "/auth")
app.add_middleware(
    RateLimitMiddleware,
    settings=get_settings(),
    protected_prefixes=_PROTECTED_PREFIXES,
)

# W7 D3 F3 — audit log middleware. Registered AFTER rate limiter so it sits
# OUTERMOST in the Starlette stack (Starlette wraps later add_middleware calls
# around earlier ones); the audit row therefore captures 429 responses too.
# Scope = same protected prefixes; /health stays unaudited to avoid liveness
# probe noise (W8 cost-effective Langfuse retention).
app.add_middleware(
    AuditLogMiddleware,
    settings=get_settings(),
    protected_prefixes=_PROTECTED_PREFIXES,
)

# Local-dev CORS — Next.js dev server (localhost:3000-3002) calls this API
# cross-origin (no Next rewrite proxy). Added last = outermost in the Starlette
# stack so preflight OPTIONS short-circuit before rate-limit/audit. Production
# frontends serve from a real domain and simply won't match the localhost
# pattern, so this is a no-op there. Per docs/setup.md §8.5.
# W17 F2 — allow_credentials=True so a cross-origin browser fetch with
# `credentials:'include'` can carry the `ekp_session` / `ekp_csrf` cookies
# (the same-origin `/api/backend/*` proxy path sends them regardless; this
# covers any direct browser→backend dev call). A regex origin (not `*`) is
# required when credentials are allowed.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# W20 F2.1 — `/health` extracted to `api/routes/health.py`; payload extended from
# `{status: "ok"}` to per-component connectivity (Azure Search / OpenAI / Cohere /
# Langfuse / Postgres) consumed by the `/dashboard` System health card.
app.include_router(health.router)


# W7 D2 F1.3 — auth Depends wired router-level. W8 D5 F4.4 cascade extends
# coverage to admin-only routers (documents / chunks / eval / screenshots /
# debug + W8 D5 F5.2/F5.4 observability) so every authenticated surface lands
# behind the same gate. /health stays public (Azure Container Apps liveness
# probe target). /auth/** keeps in-route Depends so /auth/refresh + /auth/logout
# require an existing valid bearer (no unauthenticated session bootstrap).
_auth = [Depends(get_current_user)]

app.include_router(query.router, tags=["query"], dependencies=_auth)
app.include_router(feedback.router, tags=["query"], dependencies=_auth)
app.include_router(kb.router, tags=["kb"], dependencies=_auth)
# W20 F3.3 — /conversations CRUD per ADR-0031 Option B server-side Conversation History.
# Endpoint-level `Depends(get_current_user)` inside the route handlers (the route
# emits 404 on cross-user access — no per-router gate, since the in-handler dependency
# is the authoritative isolation guard).
app.include_router(conversations.router, tags=["conversations"], dependencies=_auth)
app.include_router(auth_routes.router)
# W8 D5 F4.4 — admin routes auth wire (W7 D2 字面 scope 之外 cascade per
# beta-plan-v1.md §2 W8.F1). All 5 admin routers + new observability dashboard
# now require authentication — Beta phase prerequisite.
app.include_router(documents.router, tags=["documents"], dependencies=_auth)
app.include_router(chunks.router, tags=["chunks"], dependencies=_auth)
# W20 F5.3 — POST /chunking-preview per ADR-0025 KB Detail Tab 4 Chunking Lab.
app.include_router(chunking.router, tags=["chunking"], dependencies=_auth)
app.include_router(retrieval_test.router, tags=["retrieval-test"], dependencies=_auth)
app.include_router(config_test.router, tags=["config-test"], dependencies=_auth)
app.include_router(eval_routes.router, tags=["eval"], dependencies=_auth)
app.include_router(debug.router, tags=["debug"], dependencies=_auth)
app.include_router(screenshots.router, tags=["screenshots"], dependencies=_auth)
app.include_router(observability.router, tags=["observability"], dependencies=_auth)
# W24-wave-c1 F2 — /admin/connections/* per ADR-0026 Option B.
app.include_router(admin_connections.router, tags=["admin"], dependencies=_auth)
# W24-wave-c1 F3 — /admin/identity/* per ADR-0026 Option B.
app.include_router(admin_identity.router, tags=["admin"], dependencies=_auth)
# W24-wave-c1 F4 — /admin/usage-stats + /admin/api-keys/* per ADR-0026 Option B.
app.include_router(admin_usage_stats.router, tags=["admin"], dependencies=_auth)
app.include_router(admin_api_keys.router, tags=["admin"], dependencies=_auth)
# W24-wave-c1 F5 backend hook — /admin/audit-log read endpoint promoted from Wave C2.
app.include_router(admin_audit_log.router, tags=["admin"], dependencies=_auth)
# W24c F4 — /users Members tab per ADR-0027 Option A. The router carries its own
# `require_role("admin")` gate (which chains get_current_user), so no _auth here.
app.include_router(users.router)
# W24c F5 — /roles Roles tab per ADR-0027 Option A. Same self-gated pattern as
# /users — the router carries `require_role("admin")`.
app.include_router(roles.router)
# W24c F6 — /groups Groups tab per ADR-0027 Option A. Same self-gated pattern.
app.include_router(groups.router)
# W24c F8 — /kb/{id}/acl per-KB ACL per ADR-0027. Router self-gated by
# require_kb_acl("manage") — no _auth (the guard chains get_current_user).
app.include_router(kb_acl.router)


# ── Server launcher (BUG-008) ──────────────────────────────────────────────
# Run with `python -m api.server` — NOT `python -m uvicorn api.server:app`.
#
# uvicorn's `Server.run()` builds its event loop with `loop_factory=
# asyncio.ProactorEventLoop` on Windows (uvicorn/loops/asyncio.py) — it ignores
# the event loop policy entirely. psycopg's async mode (ADR-0023 Postgres path)
# rejects ProactorEventLoop. So on Windows we bypass `Server.run()` and drive
# `Server.serve()` through `asyncio.run` with an explicit SelectorEventLoop
# factory. Off Windows, uvicorn's default (SelectorEventLoop) is already fine.
#
# PC-W32-1 (documented W38 F1.2 2026-05-27): NO `reload=True` preserved.
# Rationale — adding `reload=True` to `uvicorn.Config(...)` risks breaking the
# above SelectorEventLoop factory: WatchFiles reload mode is managed by an
# internal uvicorn subprocess which may not honor the parent process's
# `asyncio.run(..., loop_factory=...)` override, regressing BUG-008. Explicit
# kill+restart discipline is preferred — covered by CLAUDE.md §10.3 step 5b
# pre-flight protocol (W36 PC-W34-1 ship). Cost: dev iteration requires manual
# restart per code change. Benefit: production parity with BUG-008 fix preserved.
if __name__ == "__main__":
    import asyncio
    import sys

    import uvicorn

    _server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8000))
    if sys.platform == "win32":
        asyncio.run(_server.serve(), loop_factory=asyncio.SelectorEventLoop)
    else:
        _server.run()

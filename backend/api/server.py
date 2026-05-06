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

from api.auth import get_current_user
from api.error_handlers import register_error_handlers
from api.middleware import AuditLogMiddleware, RateLimitMiddleware
from api.routes import (
    auth as auth_routes,
)
from api.routes import (
    chunks,
    debug,
    documents,
    feedback,
    kb,
    observability,
    query,
    screenshots,
)
from api.routes import (
    eval as eval_routes,
)
from generation.crag import CragGrader, CragLoop
from generation.synthesizer import Synthesizer
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder
from observability.langfuse_tracer import flush_tracer, init_tracer
from retrieval.hybrid import HybridSearcher
from retrieval.reranker.base import Reranker
from retrieval.reranker.factory import make_reranker
from retrieval.retrieval_engine import RetrievalEngine
from storage.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    init_tracer(settings)

    # Embedder + searcher + reranker + synthesizer are all context-managed;
    # we manually enter/exit so they stay open across requests.
    embedder: AzureOpenAIEmbedder | None = None
    searcher: HybridSearcher | None = None
    reranker: Reranker | None = None
    synthesizer: Synthesizer | None = None
    crag_grader: CragGrader | None = None
    app.state.retrieval_engine = None
    app.state.synthesizer = None
    app.state.crag_loop = None

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
        )
        await embedder.__aenter__()
        await searcher.__aenter__()

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
        )

        # Synthesizer reuses the same Azure OpenAI endpoint+key but a different
        # deployment (gpt-5.5 chat model vs embedding deployment).
        synthesizer = Synthesizer(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment=settings.azure_openai_deployment_llm_primary,
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

    try:
        yield
    finally:
        if crag_grader is not None:
            await crag_grader.__aexit__(None, None, None)
        if synthesizer is not None:
            await synthesizer.__aexit__(None, None, None)
        if reranker is not None:
            await reranker.__aexit__(None, None, None)  # type: ignore[attr-defined]
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


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Liveness probe (Azure Container Apps health check target)."""
    return {"status": "ok"}


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
app.include_router(auth_routes.router)
# W8 D5 F4.4 — admin routes auth wire (W7 D2 字面 scope 之外 cascade per
# beta-plan-v1.md §2 W8.F1). All 5 admin routers + new observability dashboard
# now require authentication — Beta phase prerequisite.
app.include_router(documents.router, tags=["documents"], dependencies=_auth)
app.include_router(chunks.router, tags=["chunks"], dependencies=_auth)
app.include_router(eval_routes.router, tags=["eval"], dependencies=_auth)
app.include_router(debug.router, tags=["debug"], dependencies=_auth)
app.include_router(screenshots.router, tags=["screenshots"], dependencies=_auth)
app.include_router(observability.router, tags=["observability"], dependencies=_auth)

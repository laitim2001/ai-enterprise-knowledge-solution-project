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

from fastapi import FastAPI

from api.routes import chunks, debug, documents, feedback, kb, query, screenshots
from api.routes import eval as eval_routes
from generation.synthesizer import Synthesizer
from ingestion.embedding.azure_openai_embedder import AzureOpenAIEmbedder
from observability.langfuse_tracer import init_tracer
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
    app.state.retrieval_engine = None
    app.state.synthesizer = None

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

    try:
        yield
    finally:
        if synthesizer is not None:
            await synthesizer.__aexit__(None, None, None)
        if reranker is not None:
            await reranker.__aexit__(None, None, None)  # type: ignore[attr-defined]
        if embedder is not None:
            await embedder.__aexit__(None, None, None)
        if searcher is not None:
            await searcher.__aexit__(None, None, None)


app = FastAPI(
    title="EKP API",
    description="Enterprise Knowledge Platform — Tier 1 Foundation",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Liveness probe (Azure Container Apps health check target)."""
    return {"status": "ok"}


app.include_router(query.router, tags=["query"])
app.include_router(feedback.router, tags=["query"])
app.include_router(kb.router, tags=["kb"])
app.include_router(documents.router, tags=["documents"])
app.include_router(chunks.router, tags=["chunks"])
app.include_router(eval_routes.router, tags=["eval"])
app.include_router(debug.router, tags=["debug"])
app.include_router(screenshots.router, tags=["screenshots"])

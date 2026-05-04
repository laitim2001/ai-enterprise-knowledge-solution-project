"""Application settings (per .env.example + architecture.md §4.3)."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic Settings reading from .env (gitignored).

    Field names map to UPPER_SNAKE env var via case_sensitive=False.
    Defaults safe for local Azurite + missing cloud credential (will 501 at use site).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Azure AI Search
    azure_search_endpoint: str = "https://ekp-search-poc.search.windows.net"
    azure_search_admin_key: str = ""
    azure_search_default_index: str = "ekp-kb-drive-v1"

    # Azure OpenAI
    azure_openai_endpoint: str = "https://ekp-openai-poc.openai.azure.com"
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2025-04-01-preview"
    azure_openai_deployment_embedding: str = "text-embedding-3-large"
    azure_openai_deployment_llm_primary: str = "gpt-5-5"
    azure_openai_deployment_llm_judge: str = "gpt-5-4-mini"
    azure_openai_deployment_llm_eval_judge: str = "gpt-5-5-pro"
    embedding_dimension: int = 1024

    # Azure Blob (default = Azurite local)
    azure_blob_connection_string: str = (
        "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;"
        "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEhGzF0ePEMoxLdF8Ok2j3pgnT88t1MUSzJGdu"
        "/XpGV1KZL3Y7gLXnUMNm5zlcA==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    )
    azure_blob_container_screenshots: str = "ekp-kb-drive-screenshots"

    # Reranker selection — W4 D3 F3 4-way shootout per architecture.md §3.2
    # cohere = Cohere v3.5 (W3 baseline; Path A Marketplace per Q5 Resolved)
    # voyage = Voyage rerank-2.5 (direct API)
    # zeroentropy = ZeroEntropy zerank-1 (direct API)
    # azure = Azure AI Search built-in semantic ranker (no extra procurement)
    # off = hybrid-only (W2 baseline behaviour preserved for local dev / CI)
    reranker_kind: Literal["cohere", "voyage", "zeroentropy", "azure", "off"] = "cohere"

    # Cohere — Path A Azure Marketplace per Q5 Resolved 2026-05-04 (Chris signoff)
    # Endpoint format: https://<deployment>.<region>.models.ai.azure.com/v2/rerank
    # Path B fallback (direct API api.cohere.com/v2) selected via cohere_path_b flag
    cohere_endpoint: str = ""  # Marketplace endpoint base (e.g. https://...models.ai.azure.com)
    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-v3.5"
    cohere_procurement_path: Literal["A", "B"] = "A"  # A=Marketplace, B=direct API
    cohere_request_timeout_s: float = 10.0

    # Voyage — direct API (W4 D3 F3 reranker shootout candidate)
    # Endpoint: https://api.voyageai.com/v1/rerank
    voyage_api_key: str = ""
    voyage_rerank_model: str = "voyage-rerank-2.5"
    voyage_request_timeout_s: float = 10.0

    # ZeroEntropy — direct API (W4 D3 F3 reranker shootout candidate)
    # Endpoint: https://api.zeroentropy.dev/v1/rerank
    zeroentropy_api_key: str = ""
    zeroentropy_rerank_model: str = "zerank-1"
    zeroentropy_request_timeout_s: float = 10.0

    # Azure AI Search built-in semantic ranker (W4 D3 F3 — no extra procurement
    # since semantic config baked into Standard S1 SKU). Default config name
    # matches `architecture.md §3.6` index template; override per index variant.
    azure_semantic_config_name: str = "ekp-semantic-default"
    azure_semantic_request_timeout_s: float = 10.0

    # Langfuse
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # CRAG / Pipeline tuning
    crag_confidence_threshold: float = 0.70
    crag_max_reformulations: int = 1
    hybrid_top_k_retrieval: int = 50
    rerank_top_k: int = 5

    # Feature flags
    feature_l3_routing_enabled: bool = False
    feature_auth_enabled: bool = False

    # Logging / Environment
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    environment: Literal["local", "poc", "beta", "production"] = "local"

    @property
    def log_level_int(self) -> int:
        import logging

        level = logging.getLevelName(self.log_level)
        return level if isinstance(level, int) else logging.INFO


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings singleton — used by FastAPI lifespan + test override."""
    return Settings()

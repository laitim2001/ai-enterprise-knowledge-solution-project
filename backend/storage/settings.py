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

    # Multi-KB invariant per ADR-0018 (W16+ Phase 3 audit §CC-1 closure).
    # kb_id_default = backwards-compat fallback when QueryRequest.kb_id omitted
    # (legacy clients pre-ADR-0018). Tier 1 first KB per Q7 Resolved 2026-05-05.
    # storage/kb_naming.py maps kb_id → index_name + blob container + filter clause.
    kb_id_default: str = "drive_user_manuals"

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
    # cohere = Cohere v4.0-pro (W6 production lock per ADR-0012 + Q21 Resolved;
    #          W3 D1 baseline = v3.5 → W5 D1 same-vendor model upgrade → W6 D1 LIVE
    #          Azure 2-way 互換 verify reaffirms Cohere lock via faith Δ -11.76pp +
    #          rel Δ -9.81pp WORSE alternative-disprove frame)
    # voyage = Voyage rerank-2.5 (direct API; W4 D3 scaffold preserved future-proof
    #          but DROPPED Tier 1 per Karpathy §1.2 simplicity-first W5 D1)
    # zeroentropy = ZeroEntropy zerank-1 (direct API; same DROPPED Tier 1 status)
    # azure = Azure AI Search built-in semantic ranker (no extra procurement;
    #         hot fallback path per architecture.md §7.3 E7 Cohere outage mitigation)
    # off = hybrid-only (W2 baseline behaviour preserved for local dev / CI)
    reranker_kind: Literal["cohere", "voyage", "zeroentropy", "azure", "off"] = "cohere"

    # Cohere — Path A Azure Marketplace per Q5 Resolved 2026-05-04 (Chris signoff)
    # Endpoint format: https://<deployment>.<region>.models.ai.azure.com/v2/rerank
    # Path B fallback (direct API api.cohere.com/v2) selected via cohere_path_b flag
    cohere_endpoint: str = ""  # Marketplace endpoint base (e.g. https://...models.ai.azure.com)
    cohere_api_key: str = ""
    cohere_rerank_model: str = "rerank-v4.0-pro"  # ADR-0012 v3.5 → v4.0-pro same-vendor upgrade
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
    # since semantic config baked into S1+ SKU; W5 D1 verified Free tier S0 also
    # provides 1k requests/month free). Default config name matches the actual
    # config defined in `backend/indexing/schema.json` line 45 (W2 D5 landed
    # config name = "ekp-semantic-config", NOT "ekp-semantic-default" which was
    # a W4 D3 Settings typo — fixed W5 D1 F1.3 after F1.6 shootout azure row 15
    # queries errored due to mismatch). Override per index variant via .env.
    azure_semantic_config_name: str = "ekp-semantic-config"
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

    # W7 F1.2.1 mock auth dev mode (per plan §2 F1 a-revised 2026-05-05).
    # Default False = production gate; W7 dev sets True via .env to short-circuit
    # MSAL JWT validation through `backend/api/auth/mock_msal.py` while real Entra
    # ID cred lands W8 D4. Single FastAPI Depends switching point in F1.3.
    feature_auth_mock: bool = False

    # W7 F1.2.1 mock identity payload — matches real MSAL JWT claim shape so
    # downstream F2 rate-key + F3 audit-tag use the same fields whether dev or
    # LIVE. `oid` = stable principal id (Entra ID object id); `tid` = tenant id.
    auth_mock_oid: str = "00000000-0000-0000-0000-000000000001"
    auth_mock_tid: str = "00000000-0000-0000-0000-0000000000ff"
    auth_mock_preferred_username: str = "dev-user@ekp.local"
    auth_mock_bearer_token: str = "dev-token"

    # W7 F2 rate limiter (per architecture.md §8.1 R5 spec: 50 req/min per user
    # + 5 concurrent active queries per user). Conservative W7 thresholds;
    # production tuning W8-W10 based on real query patterns.
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 50
    rate_limit_concurrent: int = 5

    # W13 F6 — C13 Email Verification Service (Azure Communication Services per
    # Q22 Resolved 2026-06-10 + ADR-0014 hybrid auth). `feature_email_mock=True`
    # OR empty `acs_connection_string` falls back to ConsoleEmailProvider stub
    # (logs verification code) — preserves R8 corp-proxy graceful path. Real
    # ACS path requires `azure-communication-email` SDK installed; when it
    # isn't, AcsEmailProvider raises EmailSendError clearly identifying the
    # missing dep. Sender domain SPF/DKIM setup happens IT-side post Track A
    # (Beta phase) — Tier 1 default points at dev.ekp-beta.ricoh.com.
    feature_email_mock: bool = True
    acs_connection_string: str = ""
    acs_sender_address: str = "noreply@dev.ekp-beta.ricoh.com"
    acs_request_timeout_s: float = 30.0
    acs_max_retries: int = 3

    # W8 D2 F1.2 — Real Microsoft Entra ID JWT validation. Backend = resource
    # server only; frontend msal-react acquires tokens (W8 D3 F1.3). Empty
    # tenant_id falls back to msal_provider 503 fail-closed (W7 D1 baseline).
    azure_tenant_id: str = ""
    azure_client_id: str = ""  # API audience the backend expects in JWT `aud`
    # JWKS endpoint TTL — Microsoft rotates keys ~24h; 1h cache balances
    # rotation tolerance against per-request latency.
    jwks_cache_ttl_s: int = 3600
    # Allowed JWT issuer pattern — defaults to Entra ID v2.0 endpoint per tenant.
    azure_jwt_issuer_template: str = "https://login.microsoftonline.com/{tenant_id}/v2.0"
    azure_jwks_uri_template: str = "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

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

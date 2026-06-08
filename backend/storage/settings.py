"""Application settings (per .env.example + architecture.md §4.3)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# The single repo-root `.env` (gitignored) — `settings.py` lives at
# `backend/storage/settings.py`, so `parents[2]` is the repo root. Pinning an
# absolute path here (rather than a bare `".env"`) makes the settings load
# CWD-independent: `uvicorn api.server:app` works the same whether launched from
# the repo root, from `backend/`, or by a test runner. A `.env` next to the CWD
# is still honoured as a *secondary override* (e.g. a `backend/.env` symlink, or
# a per-invocation override) — listed last so its values win.
_REPO_ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Pydantic Settings reading from .env (gitignored).

    Field names map to UPPER_SNAKE env var via case_sensitive=False.
    Defaults safe for local Azurite + missing cloud credential (will 501 at use site).
    """

    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT_ENV, ".env"),  # repo-root .env (base) → CWD .env (override)
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        # Allow Optional fields to be set to None via env: a var whose value is the
        # literal "null" parses to None (e.g. CHUNKER_MAX_IMAGES_PER_CHUNK=null →
        # the pre-W44 no-cap chunker for the W44 F4.7 before-baseline re-index).
        # Opt-in: no existing env var uses the literal "null", so this is a no-op
        # for current config and only enables the mapping.
        env_parse_none_str="null",
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

    # W17 F1 — KB Manager + users_repo persistent backing (ADR-0023).
    # Empty → in-memory backend (local dev / CI — W1 behaviour, restart-wipes).
    # Set → PostgresKBBackend + Postgres users store, e.g.
    #   postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp
    # (the docker-compose postgres service, dedicated `ekp` database). Schema
    # auto-created via CREATE TABLE IF NOT EXISTS on connect.
    database_url: str = ""

    # W24-wave-c1 F1 — Key Vault provider selection (ADR-0026 Option B).
    # Empty → EnvVarProvider fallback (W1 `.env` workflow preserved, rotate
    # raises NotImplementedError). Set → AzureKeyVaultProvider via
    # `azure-keyvault-secrets` + DefaultAzureCredential (Managed Identity in
    # Container Apps prod, `az login` in local dev). Lazy-imported by
    # `storage/key_vault_factory.py` so unset never touches the SDK.
    key_vault_url: str = ""

    # Azure OpenAI
    azure_openai_endpoint: str = "https://ekp-openai-poc.openai.azure.com"
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = "2025-04-01-preview"
    azure_openai_deployment_embedding: str = "text-embedding-3-large"
    azure_openai_deployment_llm_primary: str = "gpt-5-5"
    azure_openai_deployment_llm_judge: str = "gpt-5-4-mini"
    azure_openai_deployment_llm_eval_judge: str = "gpt-5-5-pro"
    embedding_dimension: int = 1024

    # Azure Blob — the local default targets the Azurite emulator via the SDK's
    # `UseDevelopmentStorage=true` shortcut (BUG-009). An explicit path-style
    # `BlobEndpoint=.../devstoreaccount1` connection string makes
    # azure-storage-blob 12.28 compute a SharedKey canonicalized-resource that
    # Azurite rejects (403 — R12); the shortcut routes the SDK through its
    # Azurite-correct path-style logic. Cloud overrides the env var with a real
    # `DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...` string.
    azure_blob_connection_string: str = "UseDevelopmentStorage=true"
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
    # Canonical model identifier = the Azure Marketplace deployment name
    # `Cohere-rerank-v4.0-pro` (matches the live `.env` COHERE_RERANK_MODEL).
    # ADR-0012 v3.5 → v4.0-pro same-vendor upgrade. Path B (direct api.cohere.com)
    # would need a Cohere-native name (e.g. `rerank-v3.5`) — out of scope here.
    cohere_rerank_model: str = "Cohere-rerank-v4.0-pro"
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

    # Synthesizer (GPT-5.5) chat-completion client timeout. Default 30s mirrors the
    # synthesizer.py constructor default (production preserve). GPT-5.5 generating a
    # complete multi-scenario answer can take ~90-98s (deboost surfaces more content
    # → longer generation), tipping over 30s → APITimeoutError ("Thinking…" hang on
    # the streaming path). Raise via .env SYNTHESIZER_REQUEST_TIMEOUT_S for full-
    # answer chat (dev/demo); leave at 30 in production.
    synthesizer_request_timeout_s: float = 30.0

    # CH-006 — synthesis answer detail level (global default; per-KB overridable via
    # KbConfig.answer_detail, resolved by EffectiveConfig). "concise" = W2 baseline
    # prompt_builder Rule 3 150-word cap (production preserve, zero behaviour change).
    # "detailed" = relaxed Rule 3 (no word cap, enumerate every sub-step) for KBs whose
    # procedural answers must reproduce the full source procedure.
    synthesis_answer_detail: str = "concise"

    # W42 (ADR-0039) — hybrid mode semantic ranker toggle. True (default) =
    # preserve W2 baseline (hybrid uses `queryType="semantic"` + semantic config →
    # Azure built-in semantic L2 rerank). False = hybrid drops semantic ranker →
    # BM25 + vector + RRF (Azure auto-fusion when both `search` text + vectorQueries
    # present) → Cohere rerank handles L2 (Q21: Cohere proven superior + reranks the
    # same top-50 candidate set, so semantic ranker is a redundant intermediate layer).
    # Primary use of False: Free tier Azure AI Search has a semantic ranker monthly
    # quota (1000/mo hard cap) — hybrid mode (chat UI default) 撞 402 once exhausted;
    # flag False bypasses it for $0 Free-tier full-pipeline + chat UI dev/test without
    # vendor swap. Production default True preserved; flip to False is a W43+ separate
    # decision gated on Gate 1 R@5 re-verify (W42 F2). Set via .env HYBRID_USE_SEMANTIC_RANKER.
    hybrid_use_semantic_ranker: bool = True

    # Langfuse
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # CRAG / Pipeline tuning
    crag_confidence_threshold: float = 0.70
    crag_max_reformulations: int = 1
    hybrid_top_k_retrieval: int = 50
    rerank_top_k: int = 5

    # W25 F3 D4 — ADR-0034 query expansion + RAG-Fusion (`backend/generation/
    # query_reformulator.py` + `backend/retrieval/result_fusion.py`). Default
    # False = original single-query path preserved bit-identical (Tier 1
    # backward-compat baseline). Set True via .env ENABLE_QUERY_EXPANSION=true
    # for staging / Beta opt-in; future per-KB tuning would promote to
    # KbConfig per ADR-0034 §Alternatives rationale.
    enable_query_expansion: bool = False
    # max_variants = original + (N-1) reformulations; 3 = original + 2 = ~3
    # parallel retrieves per query. Beyond 4 hits diminishing returns +
    # latency budget pressure per ADR-0034 §Consequences negative.
    query_expansion_max_variants: int = 3
    # Hard reformulation latency cap inside the P95 < 5s pipeline budget
    # (W25 plan §8 Q4). 3s leaves ~2s for downstream retrieve+rerank+
    # synthesize. Timeout → graceful fallback to [original] only.
    query_expansion_latency_cap_s: float = 3.0
    # RRF rank-floor (Cormack et al. 2009). Empirically robust in [40, 100];
    # 60 is the canonical paper value.
    query_expansion_rrf_k: int = 60
    # Per-variant overfetch multiplier — each variant fetches
    # `per_variant_overfetch * top_k` candidates so chunks ranking outside
    # one variant's top-K still seed the fused set if they rank highly in
    # other variants.
    query_expansion_per_variant_overfetch: int = 2

    # W25 F5 D1 — citation post-process attach neighbour-chunk images per
    # ADR-0034 §Implementation Mapping + W25 plan §2 F5. When True, citations
    # gain up to `citation_neighbour_max_aux_images` extra images sourced
    # from chunks within `citation_neighbour_window` chunk_index of the
    # cited chunk (same doc). Default True = W25 phase goal G1 (≥ 5/8
    # image-bearing query citation gain images); disable via .env for A/B
    # measurement (F4/F6 verify gate).
    enable_citation_neighbour_images: bool = True
    citation_neighbour_window: int = 3
    citation_neighbour_max_aux_images: int = 2
    # BUG-027 — section-aware neighbour-image attach (W42 follow-up). The
    # first-cut window±N range (citation_image_neighbors.py docstring "section
    # _path matching NOT implemented in this first cut") misses sibling figures
    # beyond the window: a §8 intro citation (chunk_index 44, window=3) reaches
    # §8.1/§8.2 (chunk 45/47) but NOT §8.3/§8.4/§8.5 (chunk 49/51/53) → text
    # lists 5 scenarios but only 2 images attach. When depth>0, `_find_neighbour
    # _images` matches by `chunk.section_path[:depth] == citation.section_path
    # [:depth]` (section membership REPLACES window proximity — same-section
    # figures attach regardless of chunk distance, nearest-first, capped at
    # citation_neighbour_max_aux_images). Mirrors W37 citation_expansion_section
    # _path_prefix_depth convention. depth=0 (default) keeps window±N behavior
    # bit-identical (measurement-first per memory #1; production flip is a
    # separate user decision needing eval backing). depth=1 = top-level section
    # (e.g. all §8.* under §8); raise max_aux alongside (window cap=2 is too low
    # for a 5-scenario section).
    citation_neighbour_section_path_prefix_depth: int = 0

    # CH-010 / ADR-0047 — chapter-overview image pin. When True, the dominant
    # chapter's §X.1 "Overview" figures (e.g. GL03 High Level Process / Business
    # Process Flow) are fetched and prepended to the FRONT of the lead citation's
    # images BEFORE `cap_images_per_answer`, so a procedural answer leads with the
    # chapter overview/flow diagram. Fixes the root cause that neither the
    # nearest-first neighbour-attach nor post-hoc expansion surfaces the (far,
    # low-relevance) overview chunk's images past the citation-order image cap.
    # depth=0 default OFF (production-preserve); per-KB opt-in via KbConfig.
    enable_chapter_overview_pin: bool = False

    # W25 F5 D2 — retrieval low_value soft-relax per ADR-0035. W2 baseline
    # used Azure Search server-side OData filter `low_value_flag eq false`
    # (hard exclude) — diverged from architecture.md §3.5 "deboost" spec
    # wording. ADR-0035 shifts to server-side filter dropping low_value
    # clause + client-side Python post-filter: low_value+image chunks
    # retain with score × image_weight; low_value+no-image dropped;
    # non-low_value unchanged. Default 0.7 per W25 plan §8 Q5 locked.
    # Empirical tune to 0.5 / 0.8 / 0.9 per F6 manual verify if needed
    # (R7 risk mitigation per W25 plan).
    retrieval_image_low_value_weight: float = 0.7

    # W26 F2 — Parent-Document / Section-Level Retrieval per ADR-0037.
    # Tier 1 ceiling for "show me all" enumeration queries surfaced by W26 F1
    # empirical refutation (Cohere v4.0-pro scores P25=0.83 / min=0.67 cannot
    # differentiate failed vs passed queries — threshold cutoff approach
    # refuted). section_path-based runtime aggregation post-rerank reuses
    # ADR-0020 chunk-aggregation pattern (zero schema change — section_path
    # already indexed Collection(Edm.String) filterable per architecture.md
    # §3.6 line 364). 6 knob defaults locked via Chris AskUserQuestion
    # 2026-05-25 D1 cont (Q1 + Q2 + Q4 + Q6 Recommended picks + Q3 + Q5 +
    # Q7 + Q8 batch-locked). Default False = W26 F2 measurement experiment
    # only via env override (per ADR-0034 enable_query_expansion precedent —
    # measurement-first discipline, NOT default flip). See ADR-0037 §
    # Decision Log for full pick rationale.
    enable_parent_doc_retrieval: bool = False
    # Q2 pick — parent = section_path[:-1] (drop last level). Anchor in
    # ["Doc", "§8: Integration Scenarios", "Scenario A"] → parent =
    # ["Doc", "§8: Integration Scenarios"] aggregates all 5 scenarios.
    parent_doc_section_depth_offset: int = 1
    # Q1 pick W26 → W28 amendment 2026-05-26 — apply parent-doc to top-2
    # reranked anchors(W28 Step 2 sweep best combo evidence). Original W26
    # Q1 default top_k=1 conservative;W28 Run 2.A (top_k=2) achieves G1+G2+G4
    # PASS within F1 baseline ±2pp tolerance + Q-W25-I01 control 0.69 PASS;
    # W28 Run 3.A (top_k=2 + replace) achieves G2 EXCEEDS F1 baseline +1.61pp
    # + Q-W25-I01 control FULL PASS。top_k=3 over-aggregates → Q-W25-I01 0.00
    # catastrophic + correctness MISS 5.95pp。top_k=2 sweet spot per ADR-0037
    # §2.1 trade-off + ADR-0037 amendment 2026-05-26 W28 F4。
    parent_doc_top_k: int = 2
    # Q3 pick W26 → W28 amendment 2026-05-26 — token budget halved 4000→2000
    # per W28 Step 1 sweep best combo evidence。Original W26 Q3 default 4000
    # tokens = ~15 sibling chunks 過大,LLM 注意力被 long parent context 分散
    # (D1.35 H2 partially confirmed by W27);W28 Step 1 max_tokens=2000 + W28
    # Step 2 top_k=2 best combo 達 G1+G2+G4+G5 PASS。max_tokens=1500 too
    # aggressive(broader coverage truncation → 11 failed queries vs 2000 嘅
    # 10)。2000 sweet spot ~7-8 sibling chunks per ADR-0037 §2.3 truncation
    # mechanism + ADR-0037 amendment 2026-05-26 W28 F4。
    parent_doc_max_tokens_per_parent: int = 2000

    # W44 ADR-0041 — chunker per-chunk image cap (切法 D). default 8 caps
    # image-dense mega-chunks (實測 ci=15=57 圖) by distributing images per
    # doc_order text-flush + force-splitting into sub-chunks. None/0 → no cap =
    # pre-W44 whole-section pile-on (bit-identical). Wired into the ingestion
    # chunker at server.py startup; re-index required for changes to take effect.
    chunker_max_images_per_chunk: int | None = 8
    # Safety cap on siblings fetched per parent (pathological-doc protection
    # — a section with 1000+ chunks would explode latency + cost). 50 ≈
    # 12-15K tokens raw before truncation, sufficient envelope.
    parent_doc_max_chunks_per_parent: int = 50
    # When anchor's section_path is shallower than the offset would require
    # (e.g. len=1 + offset=1 → empty parent_path), fall back to doc-level
    # aggregation (kb_id + doc_id filter). True = graceful fallback;
    # False = skip expansion for shallow chunks.
    parent_doc_fallback_to_doc_on_shallow: bool = True

    # W27 F1 — parent-doc dispatch chain mode per ADR-0037 amendment candidate.
    # W26 F2 G RAGAs delta FAIL (faithfulness -8.36pp + correctness -6.12pp +
    # Q-W25-I07 0.00/0.00 + Q-W25-I01 control regression) 觸發 R-W26-1 hypothesis:
    # current replace semantics (prompt_builder._format_chunk top-priority-wins
    # `or` chain — parent_section_text > expanded_text > chunk_text) 導致 LLM
    # cite parent siblings outside top-5 reranked set → RAGAs judge faithfulness
    # mismatch (judge compares retrieved top-5 vs LLM-cited chunks). Append
    # mode 將 anchor chunk_text + parent section context 兩段都 render 入 LLM
    # input,citation invariant preserved → judge mismatch eliminated hypothesis.
    # Default "replace" preserves W26 F2 G semantics per Q4 measurement-
    # experiment-fail-policy. W27 F2 G PASS → ADR-0037 amendment default flip;
    # FAIL → NEW ADR-0038 documents finding + default preserved per Karpathy §1.3.
    parent_doc_dispatch_mode: Literal["replace", "append"] = "replace"

    # W32 F1.3 — engine-fetch citation expansion per W31 retro HIGHEST (h')
    # candidate post-W31 multi-axis fully FAIL (G1 strict 0/15 + G1 marginal
    # +0pp net across v1+v2+v3 batches). Single-axis ship per W31 multi-axis
    # trap lesson + Karpathy §1.2 一次只郁一個旋鈕. When True, synthesizer
    # post `extract_citation_ids` calls async `expand_citations` which uses
    # `engine.list_chunks(kb_id, doc_id)` to fetch FULL doc chunks (not top-K
    # reranked subset) and finds ±N chunk_index neighbors of cited chunks
    # within same doc, filtering on title regex `\\b\\d+\\.\\d+\\b` (corpus-
    # validated bare X.M + §X.M pattern per W31 F2 v2 evidence). Escapes
    # W31 F2 v3 R6 catch (3) window=3 architectural constraint — top-5
    # reranked chunks need NOT contain §X.M walkthroughs of cited intro doc
    # for expansion to fire. Mirror W25 F5 D1 `citation_image_neighbors.py`
    # `attach_neighbour_images` async pattern (batch by doc + parallel
    # asyncio.gather list_chunks + per-doc graceful failure + dedupe + cap).
    # Default True = W32 measurement experiment (per Karpathy §1.4 goal-driven
    # 「make it pass」requires axis enabled); F3 closeout will decide
    # preserve / revert per Q4 measurement-experiment-fail-policy. **NO
    # score_threshold field** per W31 PC-W31-2 lesson — `list_chunks` returns
    # raw Azure Search chunks without rerank score (no filter possible).
    enable_citation_post_hoc_expansion: bool = True
    # ±N chunk_index window — W31 F2 v3 evidence corpus §X.1-§X.5 walkthroughs
    # at idx 46/48/50/51/53 within ±10 of intro idx 44. W31 default 3 too
    # restrictive (§8.4 distance 7 from intro 44 excluded). W32 default 10
    # corpus-empirical; tunable F3 per evidence (smaller if over-expansion
    # crosses sections, larger if §X.M walkthroughs span longer doc).
    citation_expansion_window: int = 10
    # Safety cap on auto-added neighbors per existing citation — parallel to
    # W25 F5 D1 `citation_neighbour_max_aux_images=2` convention. 2 = max 2
    # extra `[chunk-{id}]` markers inserted per original citation marker.
    citation_expansion_max_aux: int = 2
    # W37 (j') section_path prefix filter for engine-fetch citation expansion —
    # additive constraint applied inside `_find_neighbour_chunks` after the
    # existing chunk_title `\b\d+\.\d+\b` regex. When depth>0, a neighbor
    # candidate must satisfy
    # `chunk.section_path[:depth] == cited.section_path[:depth]` exactly. Avoids
    # cross-section drift (W32+W33 Run 1/3/4 mixed §3/§6/§7/§9 alongside §8).
    # depth=0 = filter disabled (W37 baseline preserve W36); depth=1 = top-level
    # section match (e.g. shared "Doc" root); depth=2 = top + sub-level match
    # (e.g. ["Doc","§8"] cite expands within §8 only). Default 0 per W26 PC1
    # 「一次只郁一個旋鈕」— production flip is a separate W38+ decision based on
    # W37 F2 outcome.
    citation_expansion_section_path_prefix_depth: int = 0

    # W38 — Reranker cross-section deboost (per ADR-0035 W25 F5 D2 symmetric
    # pattern reference; post-rerank client-side score multiply, non-architectural
    # per H1). 1.0 = disabled (W38 baseline preserve W37 production behavior);
    # 0.85 = typical 15% rank penalty for cross-section candidates per W25 ADR-0035
    # deboost magnitude; 0.5+ aggressive for strong cross-section drift cases.
    # 真正 root cause per W37 F2 evidence — I07 Run 2 cited §11 Execution plan +
    # §11.2 Phase 1 chunks (cross-section §8 → §11) 由 reranker top-K 直接 surface,
    # unfiltered by W32 (h') citation_expansion layer (scope-out by design).
    # Production flip 屬 W39+ separate decision per W26 PC1 一次只郁一個旋鈕。
    reranker_cross_section_deboost: float = 1.0
    # Section_path prefix depth match required when deboost active. 1 = top-level
    # only (single-doc KB 幾乎 no-op);2 = top + sub-level required (e.g.
    # ["Doc","§8"] vs ["Doc","§11"] = different,deboost triggered);3 = strict
    # subsection (rarely needed)。Default 2 per W37 F2 evidence — single-doc KB
    # top-level「Doc」shared,只有 depth>=2 先有實質區分效果。
    reranker_section_path_prefix_depth: int = 2

    # W40 F2 — Cohere overfetch multiplier (per W39 insight 1)。When deboost
    # active (cross_section_deboost < 1.0) AND multiplier > 1,reranker.rerank
    # is called with top_k * multiplier so deboost loop has wider candidate
    # pool to swap-in same-section candidates from positions 6-50 (otherwise
    # deboost scope-limited to reranker top-K = top_k = e.g. 5)。Post-deboost
    # result truncated to original top_k preserving caller contract。
    #
    # NOTE: 與 `hybrid_overfetch_for_rerank=50` 唔同 — 後者係 hybrid pre-rerank
    # absolute fetch from Azure AI Search,前者係 reranker output multiplier
    # on top of caller's top_k (typically top_k=5 + multiplier=4 → rerank top 20)。
    #
    # Default 1 = disabled (preserves W38 baseline behavior: rerank to exact
    # top_k,no overfetch)。W41+ production ramp recommended after Azure billing
    # resolved: multiplier=4 + deboost=0.85 + depth=2 combo (per W39 retro
    # priority queue locked + Free tier workaround verified mechanism)。
    # Upper bound auto-capped at Cohere `top_n=min(top_k, len(candidates))` =
    # min(top_k * multiplier, fetch_k=hybrid_overfetch_for_rerank=50)。
    reranker_overfetch_multiplier: int = 1

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
    # W24c F3 (per ADR-0027) — RBAC role for the mock dev identity. Default
    # 'admin' so dev exercises every `require_role` guard; a test can override
    # this to drive the 403 path.
    auth_mock_role: str = "admin"

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
    azure_jwks_uri_template: str = (
        "https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    )

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

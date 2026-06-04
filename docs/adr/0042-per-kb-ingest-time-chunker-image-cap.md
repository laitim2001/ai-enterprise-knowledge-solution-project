# ADR-0042: Per-KB Ingest-Time Chunker Image Cap — Extends ADR-0040 Config-Scope to Ingestion

**Date**: 2026-06-04
**Status**: Accepted(W45-per-kb-image-cap kickoff — Chris AskUserQuestion 批准「H1 + ADR-0042」+ None 語意揀「None=繼承,正整數=cap」2026-06-04)
**Approver**: Chris(技術 Lead)

## Context

W44 / ADR-0041 引入 chunker per-chunk 圖數上限 `max_images_per_chunk`(切法 D + cap 8 force-split),根治圖洪 mega-chunk(實測 57→8)。但呢個 cap 係**單一全域值**(`storage/settings.py` `Settings.chunker_max_images_per_chunk: int | None = 8`),喺 `server.py` startup 砌成全域 singleton `LayoutAwareChunker` 落 `app.state.ingestion_chunker`。

**問題 — 同 ADR-0040 留低嘅 content-coupling 同形**:cap 8 對某類文件啱,對另一類未必。
- 圖極密嘅 AR 步驟手冊(每節大量截圖)可能要更低 cap(切更細)。
- 圖疏 / 文字為主嘅手冊,cap 8 永遠唔會 force-split,但若想保留 pre-W44 整節 pile-on 行為(無 cap),今日只能改全域 `.env` —— 一改影響所有 KB。

ADR-0040 已 formalize **per-KB config-scope resolution model**(per-query > per-KB `KbConfig` > 全域 `Settings`),但 explicit 圈定 **MVP scope = runtime-only,唔掂 chunker / ingestion**(ADR-0040 §Decision「MVP scope」+ §Alternatives「chunker 即時修圖洪 → SPLIT OUT ADR-0041」)。ADR-0040 嘅 `EffectiveConfig` resolver 喺 **query 入口** 砌,服侍 retrieval / citation 旋鈕;圖數 cap 係 **ingest-time** knob(切 chunk 時消耗),ADR-0040 嘅 query-time resolution 點覆蓋唔到。

∴ 本 ADR 把 per-KB config-scope **延伸到 ingest-time** —— 令 `chunker_max_images_per_chunk` 成為 per-KB 可調,同 ADR-0040 嘅 runtime 旋鈕一齊,構成 per-KB tunable config vision(用戶 foundational vision,memory `project_per_kb_tunable_config_vision`)嘅 ingestion 半邊。

## Decision

把 ADR-0040 config-scope resolution model 延伸到 **ingest-time chunker 配置**:

1. **`KbConfig`(`api/schemas/kb.py`)加 1 個 `Optional` 欄位** `chunker_max_images_per_chunk: int | None = None`。**語意(Chris 揀)**:`None` = inherit 全域 `Settings.chunker_max_images_per_chunk`(default 8);**正整數** = 該 KB 嘅 per-chunk 圖數 cap。**per-KB 不能表達「無 cap」**(pre-W44 整節 pile-on)—— 「無 cap」只剩全域 level(`CHUNKER_MAX_IMAGES_PER_CHUNK=null`)設得到。理由:`None` 喺呢個欄位用作 inherit 哨兵(對齊 ADR-0040 全部旋鈕),而 chunker 內部 `max_images_per_chunk=None` 本身已係「無 cap」—— 兩個 `None` 語意撞車;揀 inherit 語意 + 唔開「per-KB 無 cap」逃生口係 Karpathy §1.2 最簡解,符合 use case(圖密 KB 調 cap **數值**,而唔係關 cap)。

2. **Ingest-time 解析(唔用 query-time `EffectiveConfig`)**:`documents.py` `_run_ingest_pipeline` 喺 fetch `kb_config` 之後(W20 F4.2 已 thread,`documents.py:556-557`)解析 `cap_override = kb_config.chunker_max_images_per_chunk`(無 kb_config 或欄位 `None` → `None`)。`cap_override is None` → 用全域 singleton `deps.chunker`(零 construct 成本 + 行為同今日 bit-identical);設咗值 → 經 chunker factory 砌一個 per-ingest `LayoutAwareChunker(max_images_per_chunk=cap_override)`。

3. **Chunker factory 落 `app.state`**:`server.py`(已 import `LayoutAwareChunker`)owns 構造,expose `app.state.make_ingestion_chunker`(callable `int | None -> Chunker`);`documents.py` 保持同 concrete chunker class 解耦(只 call factory)。全域 singleton `app.state.ingestion_chunker` 保留(carry 全域 cap,服侍 inherit 路徑 + 所有既有 caller / pytest)。

4. **Production-preserve(G7 back-compat)**:新欄位 default `None`;W43 前持久化(JSONB config 冇此 key)嘅 KB reconstruct 為 `None` → inherit 全域 → 行為 bit-identical(沿用 ADR-0028 / ADR-0040 migration-default 先例,零 breaking change)。

5. **Re-index required**:config 改動對**已索引**嘅 chunk 係 no-op —— cap 喺切 chunk 時消耗,改 cap 後要 re-index 該文件先生效(同 W44 / ADR-0041 相同性質;經現成 doc-level `POST /kb/{id}/documents/{doc_id}/reindex` 即可驗,non-stub)。

**Scope 邊界(窄)**:本 phase = **backend KbConfig 欄 + ingest wiring + test + ADR**。新欄位經**既有** `PATCH /kb/{kb_id}/settings`(KbConfig-only patch)即可設,**唔加新 endpoint**。**UI 暴露**(ingestion config 上自助面)= roadmap W45 較大 candidate(「UI 開放 ingestion 配置 + 真 re-index」),**不在本 phase**,留後續 explicit trigger。

## Alternatives Considered

- **維持全域單一 cap(status quo)** — REJECTED:同 ADR-0040 content-coupling 同形,圖密 vs 圖疏文件服侍唔到單一值。
- **per-call override 落 `Chunker.chunk()` 介面**(`chunk(result, *, max_images_per_chunk=...)`)— REJECTED:改 `Chunker` protocol(§3.3)介面,churn 大過 factory;且要哨兵區分「用 instance default」vs「override 到 None」,複雜。
- **擴 `EffectiveConfig` 帶 chunker cap** — REJECTED:`EffectiveConfig` 喺 query 入口砌,圖數 cap 係 ingest-time;為單一 ingest-time knob 建 query-time resolver 過度(Karpathy §1.2)。直接喺 `_run_ingest_pipeline` inline 解析最簡。
- **`0` / 額外布林欄做 per-KB「無 cap」哨兵** — REJECTED(Chris 揀 None=繼承):多一個欄 / 哨兵語意負擔,use case 唔需要 per-KB 關 cap。
- **直接 per-document scope** — DEFERRED:per-doc 圖數 cap 更幼粒度,但屬 roadmap W46 per-document scope;MVP 先 per-KB(對齊 ADR-0040 MVP 同層)。

## Consequences

- **Positive**:
  - 圖密 vs 圖疏 KB 各用度身訂做 cap,互不干擾(延續 ADR-0040 per-KB 哲學到 ingestion)
  - reuse 既有 `KbConfig` + W20 F4.2 已 thread 嘅 `kb_config` ingest 路徑 + ADR-0028/0040 migration 先例 → 低風險 additive,wiring 缺口細(只欠 chunker per-KB 化)
  - factory 解耦 `documents.py` 同 concrete chunker class;inherit 路徑零 construct 成本
  - 完成 per-KB tunable config vision 嘅 ingestion 半邊(ADR-0040 runtime + 本 ADR ingest)
- **Negative**:
  - per-KB **不能**設「無 cap」(只全域),少咗一個逃生口 —— 接受,use case 唔需要
  - 改 cap 要 re-index 先生效(config 單獨係 no-op)—— 同 W44 性質,doc-level reindex 已現成
  - 多一個 ingest-time per-ingest chunker 構造(cap-override 路徑)—— 成本低(`tiktoken.get_encoding` 全域 cached),且只在 KB explicit set cap 時行
- **Neutral**:
  - production default 維持 = 今日(`None` inherit 全域 8)— 零 production 變化直到用戶 explicit set per-KB cap
  - UI 暴露 + 真 KB-level reindex 留 roadmap,本 ADR 唔關閉佢哋

## References

- ADR-0040(per-KB tunable retrieval/citation config-scope model — 本 ADR 延伸佢到 ingest-time;ADR-0040 explicit「MVP scope = runtime-only,唔掂 chunker/ingestion」係本 ADR 嘅缺口)
- ADR-0041(W44 chunker image-density deep fix — 引入 `max_images_per_chunk` 全域 cap 8 + 切法 D;本 ADR 令佢 per-KB 化)
- ADR-0028(KbConfig +4 multimodal 欄 — additive-field + migration-default 先例)
- W20 F4.2(orchestrator `ingest(kb_config=...)` ingest-time toggle 先例 — `extract_embedded_images` 喺 `orchestrator.py:121` 讀 kb_config 分支;`kb_config` 已 thread 到 `documents.py:556-582`)
- architecture.md §3.3(layout-aware chunker — per-chunk image cap;本 ADR inline-amend per-KB resolution)+ §4.5(KbConfig schema)
- CLAUDE.md §5.1 H1(改 §3 component + config 解析變動 → ADR route)
- roadmap `docs/01-planning/ROADMAP-per-kb-tunable-config.md` §3(W44 carry-over「per-KB 圖數 cap 降 KbConfig」+ W45「UI 開放 ingestion 配置 + 真 re-index」較大 candidate 分流)
- memory `project_per_kb_tunable_config_vision`(用戶 foundational vision)

# Enterprise Knowledge Platform (EKP) — Tier 1 Foundation 規格 v5

**Codename**:EKP(Enterprise Knowledge Platform)
**First Use Case**:Drive Project — Ricoh internal user manuals
**Status**:Draft v5 — content patches over v4(architecture locked,no structural change)
**目標讀者**:Claude Code(實作執行)、Chris(技術 Lead)、Project Stakeholder
**Timeline**:Tier 1 = 12 週(POC 6w + Beta 4w + Staged Rollout 2w)
**最後更新**:2026-04-27

> **v4 → v5 嘅 5 個 targeted patch**(內容補充,架構不變):
> 1. **§1.7 新增 Business Impact Metrics**(time-to-answer reduction、shadow AI displacement、user satisfaction)
> 2. **§6.3 新增 W2 + W4 Explicit Decision Gates**(early fail-fast,避免 sunk-cost continuation)
> 3. **§8 新增 Risk Register**(7 個對 EKP 真正相關嘅 risk + mitigation)
> 4. **§13 新增兩條 Decision Log**(13.0 Build Justification、13.11 Custom CRAG vs LangGraph framework path)
> 5. **§1.2.1 校正 Tier naming**,對齊 RAPO Drive Knowledge Agent POC Strategy 文件
>
> **註**:加入新 §8 Risk Register 後,原 §8–13 順序下推為 §9–14。Cross-references 已 update。
>
> **v3 → v4 嘅重大 reframe**(已固化,不再變更):
> 1. **Project 重新定位**:由「Drive Project Knowledge Agent」變「**Enterprise Knowledge Platform**(EKP)」,Drive Project 係 first use case
> 2. **Tier 1 / Tier 2 分層**:Tier 1(12w)= platform foundation;Tier 2(6–12 個月 roadmap)= GraphRAG / multi-agent / multi-tenancy / workflow
> 3. **Multi-format ingestion**:Word + PDF + PPT(取代 v3 嘅 Tango parser)
> 4. **Layout-aware chunking**:取代 step-based chunking
> 5. **Multi-Knowledge-Base 架構**:Tier 1 即支援結構,first KB = Drive
> 6. **Frontend**:Next.js 14 + shadcn/ui(取代 Streamlit),Day 1 開始即 production-ready
> 7. **Agentic Level L2(CRAG)**:Tier 1 baseline;W5 stretch L3 adaptive routing
> 8. **Dify Reference Policy**:Clone 到 `references/dify/`,layout 抄、視覺風格自訂

---

## 1. Context(背景)

### 1.1 Mission

建立**Enterprise Knowledge Platform(EKP)**:一個自建嘅企業級知識系統 foundation,
support multi-format document ingestion、advanced/agentic RAG retrieval、modern UI,
作為 Ricoh 多個內部 use case 嘅 knowledge backbone。

**Drive Project 係 EKP 嘅第一個 use case**,用嚟驗證平台能力 + 為 250–500 internal user 提供 Ricoh user manual 查詢服務。

### 1.2 Tier 1 vs Tier 2 邊界

| Tier | Scope | Timeline | 包含 |
|---|---|---|---|
| **Tier 1**(本規格) | Platform foundation + Drive Project use case | 12 週 | Multi-format ingestion、hybrid retrieval、L2 agentic(CRAG)、multi-KB 架構、Next.js UI、Azure-native stack |
| **Tier 2**(roadmap,規格 §11) | Advanced capabilities | post W12,6–12 個月 incremental | GraphRAG / Knowledge Graph、L4+ multi-agent、workflow engine、plugin ecosystem、multi-tenancy、multi-modal retrieval |

**Tier 1 嘅 architecture 必須 Tier 2 friendly**(modular、extensible、MCP-ready),但 Tier 1 嘅 implementation **唔包含 Tier 2 任何 feature**。

#### 1.2.1 Naming Alignment 與 Strategy 文件

如果同時參考 **RAPO Drive Knowledge Agent POC Strategy 文件**(2026-04 版),「Tier」呢個字喺兩份文件含意唔同,需要 explicit align:

| 概念 | EKP 規格(本文件)用詞 | Strategy 文件用詞 |
|---|---|---|
| 架構分層(platform foundation vs advanced) | **Tier 1 / Tier 2** | Phase 1 / Phase 2 |
| Query-level routing(cost-aware path 選擇) | **L2 CRAG / W5 stretch L3 adaptive routing** | **Tier 1–4 query routing** |

**換言之**:
- Strategy「Phase 1」≈ EKP「**Tier 1**」(architecture tier)
- Strategy「Phase 2」≈ EKP「**Tier 2 Roadmap**」(architecture tier)
- Strategy「Tier 1–4 query routing」 = 屬於 EKP Tier 1 內部嘅 **L2 CRAG + L3 routing** 範疇(query-level)

本規格全文以 EKP Tier 1 / Tier 2 為準。Strategy 文件嘅 4-tier query cost routing 概念可作為 W5 L3 adaptive routing 嘅 design reference;實際 implementation 規模 cap 喺 Drive Project 嘅 query 分佈(預估 **70% Tier-1-fast / 25% Tier-2-hybrid / 5% Tier-3-CRAG / < 1% multimodal**),而非 Strategy 文件嘅 50/30/15/5(後者係 multi-BU long-term 預估)。

### 1.3 Realistic Quality Target

| 維度 | Tier 1 Target |
|---|---|
| Drive Project 場景嘅 retrieval 質素 | **達到或超越 Dify 對同類文件嘅表現** |
| Platform breadth(KB 種類、user 角色、format) | **Dify 嘅 ~35%**(我哋只做核心,workflow / plugin / multi-tenancy 都係 Tier 2) |
| UI / UX polish | **Dify 嘅 70–80%**(layout 借鑒,視覺自訂) |
| Codebase 量級 | **~5–8 萬行**(Dify 50 萬) |

### 1.4 Drive Project 用戶與場景

| Role | 數量(Drive use case) | 任務 |
|---|---|---|
| **End User** | 250–500 | 自然語言查 Ricoh manual 內容 → 答案 + screenshot |
| **Knowledge Manager / Admin** | 1–3 | 上載文件、管理 KB、re-index、處理失敗 parse |
| **Developer / Evaluator** | 1–3 | 跑 eval、debug、A/B test、收 ground truth |

### 1.5 已決定嘅前提條件

| # | 決定事項 | 理由 |
|---|---|---|
| P1 | Project = EKP(Enterprise Knowledge Platform),Drive 係 first use case | 為 platform 而設,可擴展多 use case |
| P2 | Tier 1 = 12 週 platform foundation;Tier 2 = roadmap | Scope realistic |
| P3 | Multi-format ingestion(Word + PDF + PPT) | RAG 以文件為本,Tango 唔係 source |
| P4 | Layout-aware chunking | 文件天然結構優於 character-based |
| P5 | Hybrid retrieval(BM25 + Dense + Cohere Rerank) | 2K chunks 規模 baseline |
| P6 | L2 Agentic(CRAG)Tier 1 baseline;W5 stretch L3 adaptive routing | Advanced 但唔 over-engineered |
| P7 | GraphRAG / KG = Tier 2,trigger-driven 由 Chris 決定 | 規模未到、ROI 唔 clear |
| P8 | Multi-Knowledge-Base 架構 Day 1 已支援 | First KB = Drive,future use case 直接加 KB |
| P9 | Frontend = Next.js 14 + shadcn/ui from Day 1 | 「POC 都要好好睇」嘅標準,Streamlit 唔達標 |
| P10 | Azure-native stack(AI Search + OpenAI) | 公司 Azure commitment |
| P11 | Embedding:text-embedding-3-large(1024d MRL) | 英文為主、Azure 對齊 |
| P12 | LLM:GPT-5.5 primary,GPT-5.4-mini W3 cost A/B | Token-efficient + Azure-native |
| P13 | 三階段 release:POC 6w → Beta 4w → Staged Rollout 2w | 風險可控 |
| P14 | Eval set:架構師設計 schema、領域專家標 ground truth | 量度基礎 |
| P15 | Screenshot 自託 Azure Blob(local: Azurite) | Security + reliability |
| P16 | Auth Beta+ 加 Microsoft Entra ID | POC 內部 demo,無需 auth |
| P17 | Dify Reference policy:Clone 到 `references/dify/` 唯讀;layout 借鑒;視覺風格自訂;絕不 copy-paste code | License + ambition 對齊 |

### 1.6 Success Metrics(Drive Project Tier 1 POC — Technical)

| 指標 | Target | 量度方法 |
|---|---|---|
| Retrieval Recall@5 | ≥ 90% | 30–50 條 ground truth eval set |
| Answer Faithfulness | ≥ 95% | RAGAs faithfulness + GPT-5.5 Pro judge |
| Answer Correctness(人工) | ≥ 80% | 領域專家盲審 |
| Image Association Accuracy | ≥ 85% | 答案 cite 嘅 screenshot 屬於 correct chunk |

### 1.7 Business Impact Metrics(Beta+ phase measurement)

呢組 metric **無法喺 W6 POC eval 量度**(因為冇真實 user),必須喺 Beta phase(W7–W10)真實用戶接觸後 collect。但要喺 POC kickoff 同 stakeholder pre-align,否則 W12 production launch 之後問「實際幫到我幾多」答唔出。

| 指標 | Target | 量度方法 | Owner |
|---|---|---|---|
| **Time-to-answer reduction** | ≥ 50% | Beta phase A/B:同一 task,用 EKP vs 唔用(自己搵 / 問同事)嘅 average completion time。可以由 W8 user onboarding 時做 5–10 個 task 嘅 stopwatch session | Chris + 領域專家 |
| **Shadow AI displacement** | ≥ 40% | Beta phase user survey + analytics:呢個 task 用 EKP 嘅 % vs 用 ChatGPT / Copilot / 同事。每月 pulse survey | RAPO |
| **User satisfaction(thumbs ratio)** | ≥ 70% positive | Per-answer thumbs up/down,週度匯總 | Auto from feedback API |

**呢 3 條同 1.6 嘅 4 條 technical metric 嘅關係**:
- Technical metric 達標 → POC pass、進 Beta(W6 gate,§7.2)
- Business metric 達標 → Production justify continued investment + Tier 2 unlock(W12 + 嘅 ongoing review)
- **POC 階段唔以 business metric 為 gate**(無真實 user 數據),但 W6 demo deck 必須包含 measurement plan。

> 出處:呢 3 條 metric framing 來自 RAPO Drive Knowledge Agent POC Strategy 文件 §7.1。
> Strategy 文件嘅原 threshold(50% time reduction、40% shadow AI displacement)經評估後直接 adopt;
> 「user satisfaction」係本規格新增,因為 thumbs feedback 已喺 §4.4 endpoint 設計入面。

---

## 2. Scope(範圍)

### 2.1 Tier 1 In Scope(12 週)

**Platform Foundation**:
- ✅ Multi-Knowledge-Base 架構(create / delete / list KB)
- ✅ Multi-format document ingestion(Word + PDF + PPT)
- ✅ Layout-aware chunking strategies
- ✅ Embedded image extraction → Azure Blob 自託
- ✅ Hybrid retrieval(Azure AI Search + Cohere Rerank)
- ✅ L2 Agentic(CRAG self-correction loop)
- ✅ Multi-format prompt + citation
- ✅ Eval harness + 50 條 eval set + W4 reranker mini-shootout

**Application**:
- ✅ Next.js 14 + shadcn/ui frontend(4 個 view)
- ✅ FastAPI backend(extensible RESTful API)
- ✅ Langfuse observability
- ✅ Azure Container Apps deployment

**Drive Project Use Case**:
- ✅ 100 Ricoh manuals onboarded as first KB
- ✅ 4 metric 達 POC target → enter Beta
- ✅ 250–500 user staged rollout

### 2.2 Tier 1 Out of Scope

- ❌ GraphRAG / Knowledge Graph(Tier 2)
- ❌ L4+ Multi-agent orchestration(Tier 2)
- ❌ Workflow / plugin builder(Tier 2)
- ❌ Multi-tenancy(Tier 2)
- ❌ Multi-modal retrieval / B 類圖片搜索(Tier 2)
- ❌ Multi-language(English-first;Tier 2 加 JP/ZH)
- ❌ Auto-sync from external source(POC 階段手動 upload)
- ❌ Custom LLM fine-tuning(Tier 2)

### 2.3 Tier 2 Roadmap(Section 11 詳細)

由 Tier 1 production query log + user feedback 驅動,**遵循 trigger-based 評估**(唔係 calendar-based)。

---

## 3. RAG Core Architecture

### 3.1 Query Pipeline(Tier 1 with L2 CRAG)

```
User Query
    ↓
[Query Preprocessor]                    ← normalization + length check
    ↓
[Query Rewriter]                        ← optional,handle ambiguous query
    ↓
[Hybrid Retrieval - Azure AI Search]
 ├─ Vector search top 50
 ├─ BM25 search top 50
 └─ RRF fusion → top 50 candidates
    ↓
[Cohere Rerank v3.5] → top 5
    ↓
[Confidence Judge]    ← L2 CRAG: 評估 retrieval quality
    ↓                   ↓
    ↓ (high confident)  (low confident)
    ↓                   ↓
    ↓               [Query Reformulation + Re-retrieve]
    ↓                   ↓
    └───────────┬───────┘
                ↓
[Context Expander]                      ← prev/next 相鄰 chunk
    ↓
[GPT-5.5 Synthesis with Citation]
    ↓
[Response Formatter]                    ← {answer, citations, screenshots, trace}
    ↓
End User UI
    
全程 Langfuse traces
```

**L2 CRAG 細節**:
- Confidence judge = lightweight LLM call(GPT-5.4-mini)評估 top-5 chunks 同 query 嘅 alignment
- Threshold:judge score < 0.7 → trigger reformulation
- Reformulation 最多 1 次(避免 infinite loop)
- 若 reformulation 後 confidence 仍低 → **拒答 + 「我喺現有資料搵唔到」message**

**W5 stretch L3 adaptive routing**(若 W4 數字許可):
- Query intent classifier(細模型)分流:
  - `factual_lookup` → 直接 hybrid retrieval
  - `multi_step` → CRAG loop
  - `troubleshooting` → 加 prev/next chunk expansion
  - `oos`(out-of-scope) → 直接拒答

### 3.2 Component Selection

| 組件 | 選型 | 替代 / W4 challenge |
|---|---|---|
| Search Service | **Azure AI Search Standard S1** | — |
| Embedding | **Azure OpenAI text-embedding-3-large**(1024d MRL) | text-embedding-3-small(W3 cost A/B) |
| Reranker | **Cohere Rerank v3.5**(Azure Marketplace) | W4 shootout: Voyage / ZeroEntropy / Azure built-in |
| LLM(synthesis) | **Azure OpenAI GPT-5.5** | GPT-5.4-mini(W3 cost A/B) |
| LLM(judge / confidence) | **GPT-5.4-mini**(快、平) | GPT-5.5 |
| LLM(eval judge) | **GPT-5.5 Pro** | — |
| Eval | **RAGAs** + custom LLM judge | TruLens、DeepEval |

### 3.3 Multi-Format Document Parsing Strategy

| 格式 | Parser | Chunking 單位 | Embedded Image 處理 |
|---|---|---|---|
| **Word(.docx)** | **Docling**(IBM,MIT)+ python-docx fallback | Heading-based(H1/H2/H3 boundary)+ table 獨立 chunk | 抽 inline image → Azure Blob,chunk metadata link |
| **PDF** | **Docling**(layout model) | Layout-aware section detection | 抽 inline image + 必要時 OCR caption |
| **PowerPoint(.pptx)** | **python-pptx** + 自寫 slide extractor | 每 slide = 1 chunk(speaker notes 併入) | 抽 slide images → Azure Blob |

**統一 chunking rules**:
- Hard cap:chunk text > 1500 tokens 自動切細
- Soft floor:chunk text < 100 tokens flag `low_value_chunk`(index 但 deboost retrieval)
- Title + content 結合:chunk text = `chunk_title + "\n\n" + chunk_content`
- Metadata 全保留(畀 retrieval filter)
- Embedded images 統一抽出 → Azure Blob,chunk 記錄 image URL list

**Layout-aware 嘅 secret sauce**:
- Word:用 docx OOXML 嘅 heading style(`Heading 1`、`Heading 2`)推斷 section boundary,而非靠 `\n\n` delimiter
- PDF:Docling 嘅 DocLayNet model 推斷 section / table / figure boundary
- PPT:slide 已係天然語義 unit,直接 1:1 mapping

呢個係**對比 Dify「General mode」嘅核心差異化**:Dify 純 character-based,我哋係 layout-semantic-based。

### 3.4 Multi-Knowledge-Base Architecture

```
EKP Platform
├── KB 1: drive_user_manuals (first use case)
│   ├── 100 documents
│   ├── ~2,000 chunks
│   ├── Azure AI Search index: ekp-kb-drive-v1
│   └── Azure Blob container: ekp-kb-drive-screenshots
├── KB 2: (future use case)
└── KB N: ...
```

**KB-level configuration**:
- 每 KB 獨立 Azure AI Search index(命名 `ekp-kb-{kb_id}-v{version}`)
- 每 KB 獨立 Blob container
- 每 KB 可獨立配置:embedding model、chunk strategy、reranker、retrieval top-K
- Query 時可指定 KB(或 Tier 2:cross-KB retrieval)

**API 設計**(see Section 4):
- `POST /kb` — 創建 KB
- `GET /kb` — 列 KB
- `POST /kb/{kb_id}/documents` — 上載文件
- `POST /query` — 查詢(指定 `kb_id`)

### 3.5 Step Record / Chunk Record Schema(統一格式)

```json
{
  "chunk_id": "kb-drive_doc-M042_chunk-0007",
  "kb_id": "drive_user_manuals",
  "doc_id": "M042_paper_jam_recovery",
  "doc_title": "Paper Jam Recovery Procedure",
  "doc_format": "docx",
  "chunk_index": 7,
  "chunk_total": 15,
  "chunk_title": "Open the rear cover",
  "chunk_text": "Press the lever on the right side ...",
  "chunk_token_count": 287,
  "section_path": ["Operation", "Recovery", "Paper Jam"],
  "embedded_images": [
    {
      "blob_url": "https://...azure.../screenshots/M042/img_007_a.png",
      "alt_text": "Rear cover lever location",
      "checksum_sha256": "a1b2c3...",
      "width": 1920,
      "height": 1080
    }
  ],
  "prev_chunk_id": "kb-drive_doc-M042_chunk-0006",
  "next_chunk_id": "kb-drive_doc-M042_chunk-0008",
  "tags": ["paper_jam", "rear_cover"],
  "low_value_flag": false,
  "enabled": true,
  "source_url": "https://internal.ricoh/docs/M042.docx",
  "ingested_at": "2026-04-28T10:00:00Z"
}
```

`enabled` field 係 Dify-inspired:**Admin Console 可手動 disable 個別 chunk**(例如 logo 頁、目錄)而唔需要 re-ingest 整個 doc。

### 3.6 Azure AI Search Index Schema

```json
{
  "name": "ekp-kb-drive-v1",
  "fields": [
    {"name": "chunk_id", "type": "Edm.String", "key": true},
    {"name": "kb_id", "type": "Edm.String", "filterable": true, "facetable": true},
    {"name": "doc_id", "type": "Edm.String", "filterable": true, "facetable": true},
    {"name": "doc_title", "type": "Edm.String", "searchable": true},
    {"name": "doc_format", "type": "Edm.String", "filterable": true, "facetable": true},
    {"name": "chunk_index", "type": "Edm.Int32", "filterable": true, "sortable": true},
    {"name": "chunk_title", "type": "Edm.String", "searchable": true, "analyzer": "en.microsoft"},
    {"name": "chunk_text", "type": "Edm.String", "searchable": true, "analyzer": "en.microsoft"},
    {"name": "section_path", "type": "Collection(Edm.String)", "filterable": true, "facetable": true},
    {"name": "embedded_images_json", "type": "Edm.String", "retrievable": true},
    {"name": "prev_chunk_id", "type": "Edm.String", "retrievable": true},
    {"name": "next_chunk_id", "type": "Edm.String", "retrievable": true},
    {"name": "tags", "type": "Collection(Edm.String)", "filterable": true, "facetable": true},
    {"name": "low_value_flag", "type": "Edm.Boolean", "filterable": true},
    {"name": "enabled", "type": "Edm.Boolean", "filterable": true},
    {"name": "source_url", "type": "Edm.String", "retrievable": true},
    {"name": "ingested_at", "type": "Edm.DateTimeOffset", "filterable": true, "sortable": true},
    {
      "name": "content_vector",
      "type": "Collection(Edm.Single)",
      "dimensions": 1024,
      "vectorSearchProfile": "ekp-vector-profile"
    }
  ],
  "vectorSearch": {
    "profiles": [{"name": "ekp-vector-profile", "algorithm": "ekp-hnsw"}],
    "algorithms": [{
      "name": "ekp-hnsw",
      "kind": "hnsw",
      "hnswParameters": {"m": 4, "efConstruction": 400, "efSearch": 500, "metric": "cosine"}
    }]
  },
  "semantic": {
    "configurations": [{
      "name": "ekp-semantic-config",
      "prioritizedFields": {
        "titleField": {"fieldName": "chunk_title"},
        "prioritizedContentFields": [{"fieldName": "chunk_text"}],
        "prioritizedKeywordsFields": [{"fieldName": "tags"}]
      }
    }]
  }
}
```

**Query 時 filter**:`enabled eq true and low_value_flag eq false`(default deboost low value chunks)

---

## 4. Application Architecture

### 4.1 高層 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ Frontend - Next.js 14 + shadcn/ui (:3001)                       │
│  Routes:                                                          │
│   /            - End User Chat                                   │
│   /admin       - Admin Console                                   │
│   /admin/kb    - Knowledge Base management                       │
│   /admin/kb/[id] - KB detail (docs / chunks / settings)         │
│   /eval        - Eval Console                                    │
│   /debug/[id]  - Debug View(single trace)                        │
│   /history     - User query history(Beta+)                      │
│   /settings    - User preferences(Beta+)                        │
└─────────────────────────────────────────────────────────────────┘
                  ↓ HTTPS / streaming
┌─────────────────────────────────────────────────────────────────┐
│ Backend - FastAPI (:8000)                                        │
│  - 18 RESTful endpoints (see 4.4)                               │
│  - SSE streaming for chat                                        │
│  - Pydantic models                                               │
│  - Async + uvicorn                                               │
└─────────────────────────────────────────────────────────────────┘
                  ↓
┌────────────┬────────────┬──────────┬──────────┬───────────────┐
│ Azure AI   │ Azure Blob │ Azure    │ Cohere   │ Langfuse      │
│ Search S1  │ (Azurite   │ OpenAI   │ Rerank   │ self-host     │
│ multi-KB   │ for local) │ GPT-5.5+ │ v3.5     │               │
│            │            │ embed    │          │               │
└────────────┴────────────┴──────────┴──────────┴───────────────┘
```

### 4.2 Repository Structure

```
ekp/
├── references/
│   ├── dify/                          ← git clone (read-only,gitignored)
│   │   ├── web/                       ← study Next.js frontend
│   │   ├── api/                       ← study Python backend
│   │   └── README.md
│   └── REFERENCE_USAGE.md             ← policy + how-to
│
├── backend/
│   ├── ingestion/
│   │   ├── parsers/
│   │   │   ├── base_parser.py
│   │   │   ├── docx_parser.py         # Docling + python-docx
│   │   │   ├── pdf_parser.py          # Docling
│   │   │   ├── pptx_parser.py         # python-pptx + custom
│   │   │   └── parser_factory.py      # format detection + dispatch
│   │   ├── chunker/
│   │   │   ├── base_chunker.py
│   │   │   ├── heading_chunker.py     # for Word
│   │   │   ├── layout_chunker.py      # for PDF
│   │   │   ├── slide_chunker.py       # for PPT
│   │   │   └── chunker_factory.py
│   │   ├── image_extractor.py
│   │   ├── blob_uploader.py           # Azurite / Azure Blob unified
│   │   └── azure_indexer.py
│   ├── retrieval/
│   │   ├── azure_search_client.py
│   │   ├── reranker_cohere.py
│   │   ├── reranker_voyage.py         # W4 shootout
│   │   ├── reranker_zeroentropy.py    # W4 shootout
│   │   ├── reranker_azure_native.py   # W4 shootout
│   │   └── confidence_judge.py        # CRAG L2
│   ├── generation/
│   │   ├── prompt_templates.py
│   │   ├── azure_openai_client.py
│   │   └── citation_formatter.py
│   ├── pipeline/
│   │   ├── query_pipeline.py          # main orchestration
│   │   ├── crag_loop.py               # L2 CRAG
│   │   └── intent_router.py           # W5 stretch L3
│   ├── kb_management/
│   │   ├── kb_service.py              # CRUD KB
│   │   └── kb_models.py
│   ├── eval/
│   │   ├── eval_set_loader.py
│   │   ├── ragas_runner.py
│   │   ├── llm_judge.py
│   │   ├── reranker_shootout.py
│   │   └── report_generator.py
│   ├── observability/
│   │   └── langfuse_tracer.py
│   ├── storage/
│   │   ├── blob_client.py             # Azurite / real Blob unified
│   │   └── settings.py
│   └── api/
│       ├── server.py                  # FastAPI app
│       ├── routes/
│       │   ├── query.py
│       │   ├── kb.py
│       │   ├── documents.py
│       │   ├── chunks.py
│       │   ├── eval.py
│       │   ├── feedback.py
│       │   ├── debug.py
│       │   └── screenshots.py
│       ├── schemas/
│       └── middleware/
│           └── auth.py                # Beta+
│
├── frontend/                           # Next.js 14 + shadcn/ui
│   ├── app/
│   │   ├── (chat)/page.tsx            # End User Chat
│   │   ├── admin/
│   │   │   ├── page.tsx               # Admin Dashboard
│   │   │   └── kb/
│   │   │       ├── page.tsx           # KB list
│   │   │       └── [id]/
│   │   │           ├── page.tsx       # KB detail
│   │   │           ├── documents/
│   │   │           ├── chunks/
│   │   │           └── settings/
│   │   ├── eval/page.tsx
│   │   └── debug/[traceId]/page.tsx
│   ├── components/
│   │   ├── ui/                        # shadcn primitives
│   │   ├── chat/                      # ChatMessage、CitationCard、ScreenshotModal
│   │   ├── kb/                        # KbCard、ChunkInspector、UploadWizard
│   │   ├── eval/                      # EvalRunner、MetricCard、ShootoutTable
│   │   └── debug/                     # TraceTimeline、RetrievalStages
│   ├── lib/
│   │   ├── api-client.ts
│   │   └── theming/
│   │       └── tokens.ts              # design tokens(custom,not Dify)
│   └── styles/
│
├── eval_data/
│   ├── eval_set_v1.yaml
│   └── ground_truth/
│
├── infrastructure/
│   ├── docker-compose.yml             # local dev
│   ├── azurite.config.json
│   ├── containerapp.bicep
│   └── azure_search_index.json
│
├── tests/
│   ├── backend/
│   └── frontend/
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── DESIGN_DECISIONS.md
│
└── pyproject.toml + package.json
```

### 4.3 Local Dev Environment(docker-compose)

```yaml
# infrastructure/docker-compose.yml
services:
  azurite:
    image: mcr.microsoft.com/azure-storage/azurite
    ports: ["10000:10000", "10001:10001", "10002:10002"]
    volumes: ["./azurite-data:/data"]

  langfuse:
    image: langfuse/langfuse:latest
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgresql://langfuse:langfuse@postgres:5432/langfuse
      NEXTAUTH_SECRET: dev-secret
      NEXTAUTH_URL: http://localhost:3000
    depends_on: [postgres]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: langfuse
      POSTGRES_USER: langfuse
      POSTGRES_PASSWORD: langfuse

  fastapi:
    build: ../backend
    ports: ["8000:8000"]
    environment:
      AZURE_BLOB_CONN_STR: DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=...
      AZURE_SEARCH_ENDPOINT: ${AZURE_SEARCH_ENDPOINT}
      AZURE_OPENAI_ENDPOINT: ${AZURE_OPENAI_ENDPOINT}
      COHERE_API_KEY: ${COHERE_API_KEY}
      LANGFUSE_HOST: http://langfuse:3000
    depends_on: [azurite, langfuse]

  nextjs:
    build: ../frontend
    ports: ["3001:3001"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on: [fastapi]
```

> **Note**:Azure AI Search 同 Azure OpenAI **冇 local emulator**,必須連 real cloud
> resource(POC stage 用 dev resource group)。Blob 用 Azurite emulator,Langfuse self-host。

### 4.4 FastAPI Endpoint Contract(18 個)

| # | Endpoint | Method | 功能 | Used By |
|---|---|---|---|---|
| **Query** |
| 1 | `/query` | POST | 主 RAG query(支援 SSE streaming) | Chat UI |
| 2 | `/query/stream` | POST(SSE) | Streaming response | Chat UI |
| 3 | `/feedback` | POST | thumbs / comment | Chat UI |
| **KB Management** |
| 4 | `/kb` | GET | List all KBs | Admin |
| 5 | `/kb` | POST | Create KB | Admin |
| 6 | `/kb/{kb_id}` | GET | KB detail + stats | Admin |
| 7 | `/kb/{kb_id}` | DELETE | Delete KB(含 cleanup) | Admin |
| 8 | `/kb/{kb_id}/settings` | PATCH | Update KB config(embedding model, chunk strategy) | Admin |
| **Document Management** |
| 9 | `/kb/{kb_id}/documents` | GET | List docs in KB | Admin |
| 10 | `/kb/{kb_id}/documents` | POST | Upload + ingest doc(multipart) | Admin |
| 11 | `/kb/{kb_id}/documents/{doc_id}` | DELETE | Delete doc + cleanup chunks/blob | Admin |
| 12 | `/kb/{kb_id}/documents/{doc_id}/reindex` | POST | Re-index single doc | Admin |
| **Chunk Management** |
| 13 | `/kb/{kb_id}/documents/{doc_id}/chunks` | GET | List chunks of a doc | Admin |
| 14 | `/kb/{kb_id}/chunks/{chunk_id}` | PATCH | Toggle chunk enabled / edit metadata | Admin |
| **Eval / Debug** |
| 15 | `/eval/run` | POST | Run eval set | Eval Console |
| 16 | `/eval/shootout` | POST | W4 4-way reranker comparison | Eval Console |
| 17 | `/debug/trace/{trace_id}` | GET | Full trace detail | Debug View |
| **Screenshots** |
| 18 | `/screenshots/{kb_id}/{doc_id}/{img_id}` | GET | Redirect to SAS URL | All UI |

### 4.5 Pydantic Schemas(關鍵)

```python
# schemas/query.py
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    kb_id: str
    top_k_retrieval: int = 50
    top_k_rerank: int = 5
    llm_model: Literal["gpt-5.5", "gpt-5.4-mini"] = "gpt-5.5"
    reranker: Literal["cohere-v3.5", "voyage-rerank-2.5",
                      "zeroentropy-zerank-1", "azure-semantic", "off"] = "cohere-v3.5"
    enable_crag: bool = True
    enable_intent_routing: bool = False  # W5 stretch

class Citation(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    chunk_title: str
    chunk_index: int
    section_path: list[str]
    relevance_score: float
    embedded_images: list[ImageRef]

class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    retrieved_chunks: list[ChunkPreview]
    crag_triggered: bool
    crag_iterations: int
    latency_ms: int
    trace_id: str
    model_used: str
    reranker_used: str
    refused: bool = False

# schemas/kb.py
class KbConfig(BaseModel):
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 1024
    chunk_strategy: Literal["heading_aware", "layout_aware", "slide_based", "auto"] = "auto"
    default_top_k: int = 50
    default_rerank_k: int = 5

class KbStatus(BaseModel):
    kb_id: str
    name: str
    description: str
    config: KbConfig
    total_documents: int
    total_chunks: int
    total_screenshots: int
    failed_documents: list[FailureRecord]
    last_indexed_at: datetime
    storage_size_mb: float

# schemas/eval.py
class EvalReport(BaseModel):
    recall_at_5: float
    faithfulness: float
    correctness: float | None
    image_association: float
    p95_latency_ms: int
    failed_queries: list[FailedQueryDetail]
    crag_trigger_rate: float
    avg_cost_per_query_usd: float
```

### 4.6 Screenshot / Image Self-Hosting Pipeline

```
Document Upload
    ↓
[Format Parser] → identify embedded images
    ↓
[Image Extractor]
  - For .docx: 抽 W:drawing / W:pict elements
  - For .pdf: 抽 PDF /Image objects
  - For .pptx: 抽 slide shape / picture
  - 對每 image:
    1. Save 落 temp file
    2. Compute SHA256 checksum
    3. Validate format + size
    4. Generate alt_text(若 docx 已有 alt → 用;否則用 chunk_title placeholder)
  ↓
[Blob Uploader]
  - Path: `{kb_id}/{doc_id}/{img_id}.{ext}`
  - Azurite(local)/ Azure Blob(cloud)
  - Container access:
    POC = Public read(internal demo)
    Beta+ = Private + SAS URL(5min expiry)
  ↓
[Index]
  - Image metadata 存 chunk record `embedded_images` field
```

**Re-sync logic**:
- Re-index 時 SHA256 比對
- Tango / source 端改變 → re-download + re-upload + 舊 blob retain history version
- New URL 寫入新 chunk version,Azure Search index alias 切換

---

## 5. UI Specifications

### 5.1 Visual Identity Strategy(D5 Decision)

**Principle**:Layout / interaction pattern 抄 Dify;visual identity / design tokens 100% 自訂。

**抄(Layout / Interaction Patterns)**:
- Step indicator wizard(Image 1 + 6 嘅 DATA SOURCE → DOCUMENT PROCESSING → EXECUTE)
- Left settings + Right preview split layout
- Card-based selection(General vs Parent-child;High Quality vs Economical)
- Document table layout(name / chunking mode / words / retrieval count / status)
- Chunk inspector(per-chunk preview + enable toggle + retrieval count)
- Sidebar navigation(Documents / Pipeline / Retrieval Testing / Settings)
- Knowledge metadata side panel
- Retrieval setting cards(Vector / Full-Text / Hybrid)

**唔抄(Visual Identity)**:
- ❌ Dify 嘅藍色 primary color → 改用 EKP 自訂 token
- ❌ Dify 嘅 logo / brand mark
- ❌ Dify 嘅 typography choice
- ❌ Dify 嘅 illustration style

**自訂 Design Token 建議**(initial,W2 finalize):

```typescript
// frontend/lib/theming/tokens.ts
export const ekpTokens = {
  colors: {
    primary: 'oklch(...)',          // EKP brand color (待 designer 定)
    accent: 'oklch(...)',
    background: 'oklch(...)',
    foreground: 'oklch(...)',
    muted: 'oklch(...)',
    border: 'oklch(...)',
    success: 'oklch(...)',
    warning: 'oklch(...)',
    destructive: 'oklch(...)',
  },
  radius: {
    sm: '0.25rem',                  // Dify 用 0.5rem,我哋用較銳利感
    md: '0.5rem',
    lg: '0.75rem',
  },
  fontFamily: {
    sans: 'Inter, system-ui',       // 與 Dify 唔同(Dify 用 SF Pro Text)
    mono: 'JetBrains Mono, monospace',
  },
  spacing: { ... },                 // 同 Tailwind default
}
```

**呢個 layer 嘅 implication**:**任何 dev clone Dify code 學 layout 之後**,寫自己 component 時用 `ekpTokens` 而非 hardcoded value,可確保視覺自動 distinct。

### 5.2 View 1:End User Chat(`/`)

**Layout reference**:抄 Claude.ai / ChatGPT,**唔係 Dify**(Dify 唔係 chat tool)。

**Component**:
- Header:logo + KB selector dropdown(Drive Manuals / Future KBs)
- Main:chat history(virtualized list)
  - Message bubble(user / assistant 區分)
  - Streaming text(SSE)
  - Inline citation card(chunk_title + doc_title + screenshot thumbnail)
  - Click citation → side panel 展開 chunk 全文
  - Click thumbnail → modal 大圖
- Input:textarea + send button + KB chip
- Footer:thumbs feedback + 「report issue」link

**Streaming UX**:用 Vercel AI SDK 嘅 `useChat` hook,Day 1 native 支援 SSE。

### 5.3 View 2:Admin Dashboard(`/admin`)

**Layout**:Sidebar(Knowledge / Eval / Settings)+ main content area。
**Layout reference**:**Dify Image 4 嘅 layout pattern**。

**Page content**:
- Top stats card row:Total KBs、Total Documents、Total Chunks、Last Activity
- Recent ingestion log
- Quick actions:Create KB、View Eval Console

### 5.4 View 3:KB List(`/admin/kb`)

**Layout**:Card grid + create button。
**Per-card**:KB name、document count、storage size、last updated、last query rate。

### 5.5 View 4:KB Detail(`/admin/kb/[id]`)

**Layout**:同 Dify Image 4(Sidebar:Documents / Pipeline / Retrieval Testing / Settings)。

#### 5.5.1 Documents Tab

抄 Dify Image 4:
- Top toolbar:Search、Sort、Add file、Metadata
- Table:`#` / NAME / CHUNKING MODE / WORDS / RETRIEVAL COUNT / UPLOAD TIME / STATUS / ACTION
- ACTION column:enable toggle + 三點 menu(re-index、delete、view chunks)

**新增**(EKP-specific,Dify 冇):
- Format icon(.docx / .pdf / .pptx 區分)
- Embedded images count column
- Failed parse status + error preview

#### 5.5.2 Document → Chunks View

抄 Dify Image 5:
- 24 CHUNKS 上方統計
- Per-chunk:Chunk-XX / character count / Retrieval count / Enabled toggle
- 右側 panel:Document Information + Technical Parameters
- **新增**:embedded images preview per chunk、low_value_flag indicator

#### 5.5.3 Pipeline Tab(Ingestion Wizard)

抄 Dify Image 1 + 6 嘅 3-step wizard:`Data Source → Document Processing → Execute & Finish`。

**Step 1 - Data Source**:Drag-drop multi-format upload(.docx / .pdf / .pptx)
**Step 2 - Document Processing**:Chunk strategy selector(Auto / Heading-aware / Layout-aware / Slide-based)+ live preview pane
**Step 3 - Execute & Finish**:Index method confirm + start indexing + progress bar

#### 5.5.4 Retrieval Testing Tab

抄 Dify Image 2:
- Vector Search / Full-Text / Hybrid Search selector
- Top K slider + Score Threshold input
- Rerank Model toggle
- Right pane:test query input + ranked result preview

**新增**(EKP-specific):
- Reranker dropdown(Cohere / Voyage / ZeroEntropy / Azure)→ for W4 shootout
- CRAG enable toggle
- LLM model selector

#### 5.5.5 Settings Tab

KB-level config:embedding model lock、chunk strategy default、retrieval default、KB description。

### 5.6 View 5:Eval Console(`/eval`)

**Layout**:Top filter bar + main content split(left config + right results)。

**Components**:
- Eval set selector
- Run config(LLM、reranker、top-K、CRAG on/off、intent router)
- Run / Run Single buttons
- 4 個 metric card(Recall@5 / Faithfulness / Correctness / Image Assoc)+ Pass/Fail badge
- Failed queries table(Q-id / query / expected / got / inspect)
- W4 Reranker Shootout section(4-way table + recommendation card)

### 5.7 View 6:Debug View(`/debug/[traceId]`)

**Layout**:Top trace summary + vertical timeline + expandable stages。

**Stages**:
1. Query Preprocessor
2. Query Rewriter(if triggered)
3. Hybrid Retrieval(BM25 / Vector top 10 each + RRF fusion)
4. Reranker(top 5 with score)
5. CRAG Confidence Judge(if enabled)
6. Re-retrieve(if CRAG triggered)
7. Context Expander
8. LLM Synthesis(full prompt + raw output)
9. Final Response

**Per-stage**:duration、cost、key data preview、expand/collapse、Langfuse link。

### 5.8 Interaction Details(借鑒 Dify 嘅 small UX win)

| UX 細節 | 來源 | EKP 應用 |
|---|---|---|
| Slider + numeric input combo for Top-K | Dify Image 2 | Eval Console |
| Card-based binary choice with RECOMMEND badge | Dify Image 1 | Chunk strategy / Index method picker |
| Per-document Retrieval Count column | Dify Image 4 | KB Documents table |
| Chunk-level Enabled toggle | Dify Image 5 | Chunk inspector |
| Embedded chunking statistics(Embedding time / Embedded spend) | Dify Image 5 | Document detail |
| Step indicator with status badge | Dify Image 1, 6 | Pipeline wizard |
| Side panel for document metadata | Dify Image 5 | KB detail page |

---

## 6. Sprint Plan(12 週)

### 6.1 POC Phase(W1–W6)

| Week | Milestone | Backend Deliverable | Frontend Deliverable | Risk |
|---|---|---|---|---|
| **W1** | Foundation Setup | • FastAPI skeleton(18 endpoints stubbed)<br>• KB management CRUD<br>• Docling integration POC(.docx parser working on 5 sample)<br>• docker-compose w/ Azurite + Langfuse<br>• Azure AI Search index 建立 | • Next.js 14 + shadcn/ui init<br>• Design tokens layer(custom)<br>• Routing skeleton(7 routes)<br>• API client lib | • Dify clone 落 references/<br>• Eval set v0(30 條 synthetic) |
| **W2** | Multi-format Ingestion + Chunking | • PDF parser(Docling)<br>• Word + PDF chunking(heading + layout-aware)<br>• Image extraction + Blob upload pipeline<br>• 100 manuals indexed(first KB) | • Admin Dashboard layout<br>• KB list page<br>• KB detail Documents tab(借 Dify Image 4) | Embedded image edge case;low_value chunk filter tuning |
| **W3** | Chat + Hybrid Retrieval + Citations | • Hybrid retrieval working<br>• Cohere Rerank integrated<br>• GPT-5.5 synthesis with citation<br>• SSE streaming<br>• PPT parser(python-pptx) | • Chat UI(stream + citation card)<br>• Screenshot modal<br>• Pipeline wizard(借 Dify Image 1)<br>• Settings tab | LLM hallucination on tables; PPT slide edge case |
| **W4** | CRAG + Eval + Reranker Shootout | • CRAG L2 loop<br>• RAGAs eval pipeline<br>• Reranker shootout(Cohere / Voyage / ZeroEntropy / Azure)<br>• Add 20 條 real user query | • Eval Console(借 Dify Image 2)<br>• Reranker comparison table<br>• Failed queries inspector | Ground truth 標註 bottleneck |
| **W5** | Optimization + L3 Stretch | • Optimization round(based on W4 data)<br>• L3 intent router(stretch goal)<br>• Performance tuning | • Debug View(stage timeline)<br>• Chunk-level inspector(借 Dify Image 5)<br>• UI polish | Over-tuning to eval set |
| **W6** | Final Eval + Demo + Beta Prep | • Final 4 metric report<br>• Production decisions lock(LLM / reranker / chunk strategy)<br>• Day-2 ops checklist | • Stakeholder demo polish<br>• Mobile responsive baseline<br>• Beta architecture preview | Eval set drift |

### 6.2 Beta + Rollout Phase(W7–W12)

| Week | Phase | Deliverable |
|---|---|---|
| **W7** | Beta Hardening Sprint 1 | • Microsoft Entra ID auth integration<br>• Rate limiting + error handling<br>• Audit logging<br>• Mobile responsive完成 |
| **W8** | Beta Hardening Sprint 2 | • Beta deploy 到 Azure Container Apps + Static Web Apps<br>• User feedback dashboard<br>• Cost monitoring dashboard<br>• Documentation |
| **W9** | Beta Internal Testing | • 50 internal users onboarded<br>• Real query log collection<br>• 4 metric daily review<br>• UX iteration |
| **W10** | Beta Refinement | • Address Beta feedback<br>• Edge case fixes<br>• Performance optimization<br>• Production readiness review |
| **W11** | Staged Rollout 25% → 50% | • 250–500 嘅 25% 隨機抽樣<br>• Daily metric monitor<br>• 50% rollout end of week |
| **W12** | Staged Rollout 100% | • Full launch(250–500 users)<br>• Day-2 ops handover<br>• Tier 2 roadmap kickoff prep |

### 6.3 Explicit Decision Gates(W2 + W4)

兩個 explicit gate 嵌入 sprint plan,**避免 sunk-cost continuation**。Gate 設計原則:**fail-fast 早過 W6 final eval**,W2 catch foundation issue、W4 catch capability issue。

#### Gate 1 — Foundation Gate(W2 末)

| 維度 | Pass 條件 | Fail 行為 |
|---|---|---|
| Hybrid retrieval Recall@5 on 30 條 synthetic eval set | **≥ 80%**(W6 final target 90% 嘅 -10pp 早期門檻) | **HALT POC** — W3 唔開始,改為 foundation iteration:重 review parser、chunking、embedding、index config |
| 100 manuals ingested without unrecoverable error | **≥ 95%**(允許 ≤ 5 manual fail with logged reason) | 同上 |
| End-to-end query latency p95 | ≤ 30s(無 reranker / no LLM 階段)| 通常 OK,異常先 escalate |

**Rationale**:無 working baseline 就疊 W3 Cohere reranker、W4 CRAG loop = 浪費 budget。Strategy 文件 §6.1 嘅 75% threshold 我哋校正到 80%(因為我哋已用 hybrid + 較強 embedding,baseline 應該更高)。

#### Gate 2 — Capability Gate(W4 末)

| 結果 | 對應行動 |
|---|---|
| **4 metric 全部 within 5pp of W6 target** | **PROCEED** — W5 optimization + W5 stretch L3 routing |
| **任意 1 metric miss target by > 5pp** | **CONTINUE w/ Watch** — W5 集中修嗰個 metric,L3 stretch 取消 |
| **任意 2 metric miss target by > 5pp** | **RESCOPE** — W5 + W6 全 dedicated 修 baseline,放棄 L3 stretch + 部分 UI polish |
| **任意 3+ metric miss target by > 5pp** | **ESCALATE** — Stakeholder review:係 architectural 問題?抑或 ground truth 問題?抑或 build vs buy 要 re-examine? |

**Gate 2 嘅 implication 對 W5–W6**:Sprint plan 要保留 buffer。我哋規定 **W5 嘅 stretch L3 adaptive routing 屬 conditional**(Gate 2 全 pass 先做),呢樣 v4 已有,Gate 2 將佢 explicit 化。

> 出處:Decision Gate 概念來自 RAPO Drive Knowledge Agent POC Strategy 文件 §6.1。
> Strategy 文件 Gate 2 用「Tier 3 cross-department accuracy < 60% → rescope」;
> 本規格因 Drive Project scope 唔涉 cross-department graph reasoning,改用「4 metric 任意 N 個 miss」嘅 generalized 版本。

### 6.4 Sprint 風險點

- **W1 critical**:Docling Docker image ~2GB,first-time pull 慢;Document source access(SharePoint / Drive / share folder)需 Day 1 align
- **W2 critical**:image extraction 可能 surface unexpected format(WMF、EMF、heic 等)
- **W3 critical**:Cohere via Azure Marketplace 嘅 procurement 可能滯後 → fallback 用 Cohere direct API + corporate card
- **W4 critical**:Ground truth 標註人手依賴(W1 必須 secure dedicated labeler)
- **W7 critical**:Microsoft Entra ID tenant access 需公司 IT 配合

---

## 7. Acceptance Criteria

### 7.1 Functional(W6)

| # | 測試案例 | Pass 條件 |
|---|---|---|
| F1 | 100 manual ingested across .docx / .pdf / .pptx | 0 unrecoverable parsing error;失敗 manual 出現喺 Admin failed list |
| F2 | Multi-KB CRUD | 可創建第 2 個 KB,獨立 index + 配置 |
| F3 | Query latency | p50 < 5s,p95 ≤ 30s |
| F4 | Citation 必備 | 答案 cite chunk_id + screenshot 顯示喺 UI |
| F5 | LLM 拒答機制 | 5 條 OOS query 拒答而非 hallucinate |
| F6 | CRAG L2 working | Confidence judge < 0.7 觸發 reformulation,trace 可見 |
| F7 | Document parse fail graceful | 唔 block 其他文件,Admin Console 顯示 fail list |
| F8 | Reranker 切換 | Eval Console dropdown 切換,backend 唔需 redeploy |
| F9 | Screenshot self-host 成功 | Source 端 image 改變後,checksum 偵測 + re-upload |
| F10 | Admin drag-drop upload | 多文件 upload + progress 顯示 |
| F11 | Eval Console A/B | 兩組 config 跑同 eval set 對比 |
| F12 | Local dev fully runnable | docker-compose up + 連 real Azure AI Search/OpenAI 即可 dev |
| F13 | Chunk-level enable / disable | Disable 即生效於下次 query(無需 re-index) |
| F14 | Streaming chat response | SSE streaming first token < 2s |

### 7.2 Performance(W6)

| Metric | Target | Stretch |
|---|---|---|
| Retrieval Recall@5 | ≥ 90% | ≥ 95% |
| Answer Faithfulness | ≥ 95% | ≥ 98% |
| Answer Correctness | ≥ 80% | ≥ 90% |
| Image Association | ≥ 85% | ≥ 95% |
| p95 Latency | ≤ 30s | ≤ 15s |
| First token latency | ≤ 5s | ≤ 2s |

**Gating**:4 metric 全達 → enter Beta;任一 miss → W6 後 1 週 hardening。

### 7.3 Edge Cases(必須處理)

| # | Case | 處理方式 |
|---|---|---|
| E1 | Query 無相關內容 | 拒答 + 友善 message |
| E2 | Query 涉多 doc | 多 source citation merge |
| E3 | Chunk 無 image | 文字答案 + 「無圖」flag |
| E4 | Document parse 失敗 | Skip + log + Admin UI flag |
| E5 | LLM API timeout | Retry 1 次 + graceful error |
| E6 | Query 過長(> 2000 char) | Truncate + warn |
| E7 | Cohere outage | Fallback Azure built-in semantic ranker |
| E8 | Image URL 失效 | UI placeholder + log |
| E9 | Word 內嵌複雜 OOXML(equation、SmartArt) | 抽 fallback text representation |
| E10 | PDF scan + handwriting | Flag 為 `requires_ocr`,Tier 2 處理 |
| E11 | PPT 動畫 only(無文字) | Slide caption / shape title 為 chunk text |
| E12 | Two docs 撞 chunk_id | namespace by `kb_id` + `doc_id` 隔離 |
| E13 | KB delete 中途失敗 | Soft delete + cleanup background job |
| E14 | CRAG 進入 infinite loop | Max 1 reformulation + force return |

### 7.4 Day-2 Readiness Checklist(W6 + Beta)

- [ ] All query / retrieval / LLM call logged to Langfuse
- [ ] Cost dashboard:Azure OpenAI + Cohere + Blob + AI Search daily spend
- [ ] Alerts:p95 latency > 30s、API error > 5%、cost spike、CRAG trigger rate > 50%(可能訊號 retrieval 不足)
- [ ] Runbook:document parse 失敗、API quota 爆、index corruption、reranker outage、CRAG loop bug
- [ ] Index alias 切換可 rollback
- [ ] User feedback loop(thumbs + comment 入 Langfuse)
- [ ] Re-index SOP per KB
- [ ] Security:Azure AI Search Private Endpoint、Managed Identity、Cohere API key in Key Vault、Blob SAS-only(Beta+)
- [ ] Tier 2 trigger metric collected(query type distribution、failed query patterns)

---

## 8. Risk Register

7 個對 EKP Tier 1 真正相關嘅 risk,按 likelihood × impact 排序。每條 risk 配 concrete mitigation,而非 acknowledgement only。

### 8.1 Critical(active mitigation)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R1** | **Shadow AI displacement** — 員工繼續用 ChatGPT / Copilot,EKP adoption 低,ROI 無法證明 | High | High | • Moat = permissioned internal data + audit trail + Ricoh-specific context<br>• Beta phase explicit measure displacement(§1.7)<br>• W9 pulse survey:「過去一週呢類問題你用咩 tool?」<br>• Onboarding 講清楚 EKP 同 ChatGPT 嘅 differentiation |
| **R2** | **Ground truth labeling slips W4** — Eval set 標註人手不足,W4 evaluation 數字唔可信 | Medium | High | • W1 Day 1 secure dedicated labeler(Q13 owner)<br>• 30 條 synthetic ground truth W1 完成做 baseline,W4 加入嘅 20 條 real query 標註可滯後 1 週唔影響 W4 gate<br>• 標註指引 + LLM-judge first pass + human verify 提升標註效率 |

### 8.2 High Priority(planned mitigation)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R3** | **Cohere via Azure Marketplace procurement delay** — W3 critical path 上 reranker 無法 enable | Medium | Medium | • W1 Day 1 同 procurement team initiate Cohere onboarding<br>• Fallback:Cohere direct API + corporate card,W3 唔 block<br>• W4 mini-shootout 數字 confirm 後,production 走 Marketplace billing |
| **R4** | **LLM hallucination on tables / structured content** — Word 表格、PPT 圖表類 chunk 答錯 | Medium | Medium | • Citation-required prompt(force quote chunk_id)<br>• Retrieval-grounded refusal(若 score 低於 threshold 拒答)<br>• Eval set 加入 5 條 table-heavy query 做 regression catch |
| **R5** | **Azure OpenAI quota insufficient at peak** — Beta 50 user 同步 query 觸發 rate limit | Low | High | • W1 同 MS account team pre-negotiate Q3 quota<br>• Implement application-side rate limiting(per-user concurrency cap)<br>• Multi-deployment region fallback |

### 8.3 Lower Priority(monitor + design fallback)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| **R6** | **Cohere outage during demo / Beta** | Low | Medium | • Hot fallback:Azure built-in semantic ranker(§7.3 E7 已 cover)<br>• Config flag 切換,backend 唔需 redeploy |
| **R7** | **Document source format edge case**(.docx 內嵌 SmartArt / equation、PDF scan + handwriting、PPT 純動畫) | Medium | Low | • Parser fail-graceful:flag affected doc,Admin Console 顯示<br>• Edge case E9–E11 已 cover<br>• 真係 critical 嘅 doc → manual fallback workflow(W7+ design) |

### 8.4 Risk Review Cadence

- **W1 Day 5**:Risk register review(team retro),確認所有 Critical mitigation 已 initiate
- **W3 末**:Mid-POC risk re-assessment(R2 / R3 status critical)
- **W6 demo deck**:含 Risk register update(stakeholder transparency)
- **Beta(W7+)**:每週 risk review,新 risk 加入 register

> 出處:Risk register framing 來自 RAPO Drive Knowledge Agent POC Strategy 文件 §8。
> Strategy 文件嘅 8 條 risk 我哋 filter:R2 Japanese handwriting OCR、R3 VLM reader、R5 Gemini Embedding 2、R8 Anthropic API outage 對 EKP Tier 1 唔 applicable(scope 外 / 已替代)。
> R1 Shadow AI、R6 team capacity 直接 inherit。R2 Ground truth、R3 Cohere procurement、R4 LLM hallucination、R5 Azure quota、R7 format edge 為 EKP-specific 新增。

---

## 9. Cost Estimate

| 依賴 | POC 6w | Beta 4w | Production monthly |
|---|---|---|---|
| Azure AI Search Std S1(multi-KB ready) | ~$115 | ~$75 | ~$75 |
| Azure OpenAI text-embedding-3-large | ~$1 | ~$1 | ~$2 |
| Azure OpenAI GPT-5.5(synthesis) | ~$80 | ~$120 | ~$300–800 |
| Azure OpenAI GPT-5.4-mini(CRAG judge) | ~$5 | ~$10 | ~$30 |
| Azure OpenAI GPT-5.5 Pro(eval judge) | ~$30 | ~$10 | ~$10 |
| Cohere Rerank v3.5 | ~$15 | ~$25 | ~$30–50 |
| Voyage / ZeroEntropy(W4 only) | ~$5 | $0 | $0 |
| Azure Blob | ~$5 | ~$5 | ~$10 |
| Azure Container Apps(2 containers) | ~$45 | ~$60 | ~$80 |
| Azure Static Web Apps(Next.js,Beta+) | $0 | ~$10 | ~$10 |
| Langfuse self-host | $0 | $0 | $0 |
| RAGAs | $0 | $0 | $0 |
| Compute / Dev VM | ~$75 | $0 | $0 |
| **TOTAL** | **~$376** | **~$316** | **~$547–1,067/month** |

**12 週 Tier 1 launch 總成本估算:USD 1,000–1,200**(包括 dev compute)
**Production monthly(estimated):USD 600–1,100**(主要 driver 係 GPT-5.5 inference)

---

## 10. Open Questions(W1 內 resolve)

### 9.1 Stakeholder

| # | Q | Default | Impact |
|---|---|---|---|
| Q1 | 100 manual 嘅 actual format 比例(.docx / .pdf / .pptx)? | Mostly .docx | 影響 W1 parser 順序 |
| Q2 | 文件 list + access?(SharePoint? Drive? share folder?) | Chris 提供 | W1 critical |
| Q3 | Azure tenant 有 Azure AI Search resource? | 假設要 provision | W1 setup |
| Q4 | Azure OpenAI GPT-5.5 deployment ready?Deployment name? | Chris 提供 | W3 critical |
| Q5 | Cohere via Azure Marketplace 嘅 procurement timeline? | 假設可 enable | W3 critical |
| Q6 | 真實 user query 收集 owner? | Chris 收 20 條 | Eval quality |
| Q7 | Beta 50 user 來源? | RAPO 內部 | Beta validation |
| Q8 | 4 metric 取代 90% 確認? | Yes | POC 成敗 |
| Q9 | Manual 敏感度?需 CMK? | 一般 internal | Azure 配置 |
| Q10 | EKP visual identity:有冇 designer 出 brand guidelines? | 假設 W1 dev 用中性 token,W4 designer pass | Frontend polish |
| Q11 | Microsoft Entra ID tenant access(Beta+)? | 假設 Ricoh 統一 tenant | Beta auth |
| Q12 | Tier 2 GraphRAG decision owner = Chris 確認? | Yes | Tier 2 trigger |

### 9.2 領域專家

| # | Q | 決定 |
|---|---|---|
| Q13 | Ground truth 標註 owner? | Eval quality |
| Q14 | Manual 更新頻率? | Re-index 策略 |
| Q15 | 用戶平日點搵呢啲資料?(Baseline) | Adoption story |

### 9.3 W1 first-touch

| # | Q | 決定方式 |
|---|---|---|
| Q16 | 5 sample manual 嘅 actual structure(heading 完整度、image 數量、table 多寡)? | W1 sample 確認 |
| Q17 | Embedded image format coverage(PNG / JPG / WMF / EMF / SVG)? | W1 測 sample |
| Q18 | Embedding dim 1024 vs 1536 vs 3072? | W2 baseline |
| Q19 | LLM GPT-5.5 vs 5.4-mini? | W3 A/B |
| Q20 | Reranker final pick? | W4 shootout |
| Q21 | CRAG threshold optimal value? | W4 tuning |

---

## 11. Tier 2 Roadmap(post W12,trigger-driven)

### 11.1 Tier 2 Capabilities Backlog

| Capability | Trigger Condition | Effort Estimate |
|---|---|---|
| **GraphRAG / Knowledge Graph** | 詳見 §11.2 | 2–3 個月 |
| **L4+ Multi-agent orchestration** | 真實 query log 顯示 > 10% 屬「跨 KB synthesis + tool use」 | 2 個月 |
| **Workflow / Plugin builder** | 業務側要求 customizable pipeline per KB | 2–3 個月 |
| **Multi-tenancy** | 第二個 organization 用同一 platform | 1.5 個月 |
| **Multi-modal retrieval(B 類)** | Production 顯示 > 5% 純圖片 query | 1.5 個月 |
| **Multi-language(JP / ZH)** | 業務側擴 APAC | 1 個月 |
| **Auto-sync from external source** | Production 顯示 manual upload 係 ops bottleneck | 1 個月 |
| **Custom LLM fine-tuning** | Generic LLM 喺 domain term 顯著弱 | 視情況 |

### 11.2 GraphRAG / KG Trigger Matrix(Chris 決策)

進入 Tier 2 GraphRAG 評估嘅 5 條 trigger,**滿足至少 3 條** + Chris approve:

| # | Trigger | 量度方法 |
|---|---|---|
| T1 | Corpus scale > 10,000 chunks | Index size |
| T2 | Real query log 顯示 > 15% 屬「跨文檔 entity relationship reasoning」 | Query classifier on 1-month production log |
| T3 | Tier 1 hybrid + rerank 喺 multi-hop query Recall@5 < 80% | Eval set with 20+ multi-hop ground truth |
| T4 | Stakeholder 明確要求「列出所有 X 相關嘅 Y」呢類 query | Business requirement doc |
| T5 | 有 dedicated 0.5 FTE 維護 ontology / graph schema | Resource commitment |

**滿足 < 3 條 → 唔做 GraphRAG**(節省 ROI 不清晰嘅工作量)。

---

## 12. Reference Repository Policy

### 12.1 Dify Reference Setup

```bash
# 喺 ekp/ root 執行
mkdir -p references
cd references
git clone --depth 1 https://github.com/langgenius/dify.git
cd dify
git log -1 > ../DIFY_PINNED_COMMIT.txt    # 固定參考版本

# 加入 .gitignore
echo "references/dify/" >> ../../.gitignore
echo "references/DIFY_PINNED_COMMIT.txt" >> ../../.gitignore  # commit 一次後可 ignore
```

### 12.2 Reference Usage Rules

`references/REFERENCE_USAGE.md` 內容:

```markdown
# Reference Repository Usage Policy

## Allowed
- Read Dify source code to study layout, interaction, component composition
- Reference Dify API design as inspiration for our endpoint patterns
- Take screenshots of Dify UI as visual reference for design discussions
- Document patterns we choose to adopt(in PR comments)

## Not Allowed
- Copy-paste any code from Dify to our codebase
- Fork Dify or maintain a fork
- Reuse Dify component packages directly
- Replicate Dify branding (logo, primary color, marketing copy)

## Required Discipline
- When implementing a feature inspired by Dify, add comment in PR:
  Reference: dify/web/app/components/datasets/documents/list.tsx
  (Studied layout pattern; rewritten with our tokens + types.)

- When in doubt about copyright / license boundary,默認唔抄。

## Visual Identity
- All design tokens (colors, typography, radius) in `frontend/lib/theming/tokens.ts`
- Tokens 100% custom, NOT copy from Dify
- Result: Layout familiar to Dify users, visual identity distinctly EKP
```

### 12.3 Pinning + Update Policy

- Initial clone:pin to commit SHA(寫入 `DIFY_PINNED_COMMIT.txt`)
- 每季 review:Dify 有重大設計更新時,team 一齊 review,決定係咪 update reference
- **唔自動 sync**(避免 reference drift 影響 design consistency)

---

## 13. Decision Log

### 13.0 Build Justification(從 Strategy 文件 inherit)

選擇自建 EKP 而非買 Glean / Gemini Enterprise / M365 Copilot,基於 3 條 differentiator。**任何一條 invalidate → Tier 2 review 必須重新評估 vendor licensing 路線**。

| # | Differentiator | 描述 | Invalidation Trigger |
|---|---|---|---|
| **D1** | **Domain specificity** | Ricoh product manuals + technical content,horizontal search vendor 對呢類 corpus 嘅 domain understanding 弱 | 若 generic vendor(Glean / Gemini Enterprise)喺 same eval set 達到 EKP 嘅 ≥ 90% retrieval quality,build 嘅 ROI 不成立 |
| **D2** | **APAC data sovereignty** | 日本 APPI、新加坡 PDPA、香港 PDPO 嘅 data residency 需求(若 future scope 擴展超出 Drive Project 純內部 manual) | 若 use case 永遠停留 internal English manual,呢條 differentiator 弱化 |
| **D3** | **Deep IPA Platform integration** | 同 RICOH Intelligent Automation Platform 整合(natif.ai IDP、ValueTech workflow),變成 enterprise knowledge OS,而非 standalone search | 若 IPA Platform integration 始終冇 materialize,EKP 同 Glean 嘅功能差距收窄 |

**Build vs Buy 嘅 Cost Reality**(Strategy 文件 §5.2):

| 方案 | 5,000 user 規模年成本 | 15,000 user 規模年成本 |
|---|---|---|
| Glean Enterprise | ~$500K–2M | ~$1M–5M |
| Gemini Enterprise($30/user/月) | ~$1.8M | ~$5.4M |
| M365 Copilot($30/user/月) | ~$1.8M(若未 bundled) | ~$5.4M |
| **EKP 自建(Tier 1 production scale)** | **~$10–15K**(基於 §9 estimates × 規模 factor) | **~$20–30K** |

成本對比 favorable,但**ROI 唔係單睇 cost**:
- Build 必須持續維護 + iteration(隱性 engineering cost)
- MIT NANDA 數字:purchased solution 成功率 67% vs internal build 33%(half rate)
- Build 路線必須以 D1/D2/D3 嘅 differentiation 為前提

**Decision Owner**:Stakeholder + IPA Platform sponsor,W12 production launch 後每 6 個月 review。

> 出處:Build vs Buy framing 來自 RAPO Drive Knowledge Agent POC Strategy 文件 §2.4 + §5.2。

### 13.1 為何 Project 改名做 EKP

由「RAPO Drive Project Knowledge Agent」→ EKP 反映:
- Drive Project 係 first use case,而非唯一 use case
- Platform thinking from Day 1,reduce future re-architecture cost
- 企業層面 visibility,有助 tier 2 投資 case

### 13.2 為何 Multi-format(Word + PDF + PPT)而非單一 format

RAG 原則係文件為本。企業實際文件 portfolio 必然 mixed format。
單一 format 假設(v3 嘅 Tango-only)係錯嘅。

### 13.3 為何 Layout-aware Chunking 而非 Character-based

Dify 預設 character-based + `\n\n` delimiter,我哋 Image 5 已見 chunk-01 純 logo
chunk-02 純 Revision History — 兩 chunk 全部 retrieval-noise。
Layout-aware 用文件天然結構,大幅減少 noise chunk。

### 13.4 為何 Multi-KB 架構 Day 1 已支援

EKP 定位 platform。**Single-KB code 升級到 multi-KB code 嘅 refactor cost
等於 day 1 已用 multi-KB 嘅初始 cost**(`kb_id` 全鏈路 propagate)。
冇理由 day 1 唔做。

### 13.5 為何 Next.js 14 + shadcn/ui from Day 1(放棄 Streamlit)

「POC 都要好好睇」嘅標準 → Streamlit 視覺天花板低,demo stakeholder 一眼識破。
Next.js setup 多 1 日,但 W3 之後 iteration 速度同 Streamlit 接近。
Beta 階段唔需要 React migration,慳 5–8 日。
Vercel AI SDK 對 LLM streaming response native 支援。

### 13.6 為何 L2 CRAG(而非 L0 / L4)

- L0(single-shot)太淺,「Advanced RAG」expectation 不滿足
- L4+(planner-executor agent)over-engineered,12 週做唔好
- L2 CRAG 喺學術 + 業界都係 well-established,實作風險低
- W5 stretch L3 adaptive routing 為 W4 數字驅動嘅升級路徑

### 13.7 為何 GraphRAG 用 Trigger Matrix 而非「Plan B 加上去」

「If needed」嘅模糊講法 = 永遠喺 backlog 飄 / W4 突然加入打亂 plan。
5 條 trigger + Chris approve = 明確 governance,團隊有共識。

### 13.8 為何 Frontend 同 Backend 分開(而非 Next.js full-stack)

- Backend 重 Python ML / RAG ecosystem,Next.js full-stack(Node.js)會 kill ecosystem
- Frontend / Backend 分離 = 各自迭代速度最高
- Future:第三方 client(Slack bot、Teams bot、CLI)直接連 FastAPI,無需經 Next.js
- Cost:多 1 個 container,< $20/month

### 13.9 為何 Dify Reference 唔 fork(只 clone read-only)

Dify modified Apache 2.0 嘅 commercial restriction:
- 唔可 multi-tenant SaaS rebrand
- 唔可移除 Dify branding
- Fork 後 derivative work 受限
- Read-only reference + 自己 codebase = license clean,scope 自主

### 13.10 其他保留 v3 嘅決定

(Azure AI Search、text-embedding-3-large、Cohere Rerank v3.5、GPT-5.5、
Screenshot self-host、Beta+ Microsoft Entra ID auth — 詳情參 v3 規格附錄,
v4 全部 inherit)

### 13.11 為何 Custom CRAG vs LangGraph Framework(framework path)

**Decision**:Tier 1 用自寫 CRAG orchestration(~200 行 Python),**唔用 LangGraph 1.0 / Microsoft Agent Framework**。Tier 2 進入 multi-agent / cross-KB synthesis 時 evaluate framework migration。

**Reason**:

| 維度 | Custom CRAG(Tier 1) | LangGraph 1.0 / MAF(Tier 2 candidate) |
|---|---|---|
| 規模適配 | 2K chunks + L2 single-loop CRAG,~200 lines 自寫足夠 | L4+ multi-agent、stateful workflow、cross-KB synthesis 嘅 sweet spot |
| Per-node overhead | 0(直接函數 call) | ~10–14ms(LangGraph 自報 benchmark,所有 framework 最高) |
| Framework lock-in | 0 | Medium(LangGraph state schema、checkpointer pattern) |
| Debuggability | 100%(自己 code 全可 trace) | High but indirect(經 LangSmith / 自家 trace) |
| Production readiness(2026) | Mature(自己掌控) | LangGraph 1.0 GA Oct 2025,400+ companies prod;MAF 1.0 GA April 2026 < 1 month track record |
| Migration cost(future) | 自己 wrap → LangGraph 較容易 | LangGraph → 自己 wrap 較難(state convention 已固化) |

**Tier 2 評估 framework migration 嘅 trigger**:
1. 跨 KB synthesis(end user 一條 query 同時撈 Drive + future KB)成為 recurring requirement
2. Multi-step planner-executor agent capability 需要(L4+)
3. 跨多個 LLM provider 嘅 prompt-aware orchestration 需要
4. Team 規模擴展 → framework 嘅 standardization value 超過 lock-in cost

**滿足 ≥ 2 條 → evaluate LangGraph 1.0 migration**(Microsoft Agent Framework 作為 Azure-native alternative 同時 evaluate)。

**Strategy 文件 §3.1 stance** 講「framework-agnostic via MCP」+「LangGraph for POC, MAF for production」。本規格嘅判斷:**MCP wrapper 喺 Tier 1 已 ready**(§4.4 endpoint design);LangGraph 對 Drive Project Tier 1 規模係 over-engineering,Tier 2 條件成熟先 migrate。Strategy 文件嘅 LangGraph commitment 反映 multi-BU long-term scale 嘅合理選擇,但唔應該 leak 入 Drive Project Tier 1 implementation。

> 出處:Framework decision logic 來自本規格獨立分析,reconciliation 與 RAPO Drive Knowledge Agent POC Strategy 文件 §3.1 + §4.2 嘅 framework discussion。

---

## 14. Stack Summary(快速 reference)

```
┌──────────────────────────────────────────────────────┐
│ Layer                | Tool / Service                 │
├──────────────────────────────────────────────────────┤
│ Document Source      | Word(.docx) / PDF / PPT       │
│ Parser               | Docling + python-pptx          │
│ Chunker              | Layout-aware(heading/layout/  │
│                      | slide-based)                   │
│ Image Storage        | Azure Blob(Local: Azurite)    │
│ Embedding            | Azure OpenAI                   │
│                      | text-embedding-3-large         │
│                      | (3072d → 1024d MRL)            │
│ Vector + BM25 Index  | Azure AI Search Std S1         │
│                      | (multi-KB,index per KB)       │
│ Reranker             | Cohere Rerank v3.5             │
│                      | (via Azure Marketplace)        │
│ LLM(synthesis)       | Azure OpenAI GPT-5.5           │
│ LLM(CRAG judge)      | Azure OpenAI GPT-5.4-mini      │
│ LLM(eval judge)      | Azure OpenAI GPT-5.5 Pro       │
│ Agentic Loop         | L2 CRAG;W5 stretch L3          │
│ Eval Framework       | RAGAs + custom                 │
│ Observability        | Langfuse(self-host)           │
│ Backend              | FastAPI + uvicorn              │
│ Frontend             | Next.js 14 + shadcn/ui +       │
│                      | Tailwind + Vercel AI SDK       │
│ Auth(Beta+)          | Microsoft Entra ID             │
│ Secrets              | Azure Key Vault                │
│ Deployment           | Azure Container Apps           │
│                      | + Azure Static Web Apps(FE)   │
│ Reference            | Dify(read-only,clone to       │
│                      | references/dify/)              │
└──────────────────────────────────────────────────────┘
```

---

**Document End. Version 5.**
**v5 = v4 + 5 個 targeted patch(business metrics、decision gates、risk register、build justification、framework path)+ Strategy 文件 alignment。**
**Tier 1 主架構繼續 lock;v5 純內容補充,無架構變更。**
**等待 stakeholder sign-off Open Questions Q1–Q21 → 啟動 W1。**

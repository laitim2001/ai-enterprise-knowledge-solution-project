---
component: C01
name: Ingestion Pipeline
catalog_ref: ../COMPONENT_CATALOG.md#c01--ingestion-pipeline
spec_refs: [architecture.md §3.3, architecture.md §3.5]
status: v2-stable
last_updated: 2026-05-06
---

# C01 — Ingestion Pipeline Design Note

> **Status**:`v1-active`(W2 D1 F1 Docling-based docx_parser PoC delivered 2026-05-03 — `backend/ingestion/parsers/{base.py, docx_parser.py}` + `scripts/run_docx_parser_sanity.py`;all 6 Drive sample manuals parsed clean — 217 headings(6.3% coverage,2× W1 D4 F6 raw style baseline 3%)+ 1018 images + 156 tables;0 parse failures。`reports/w02_d1_docx_parser_sanity.yaml` is the sanity baseline)
>
> **Owner**:AI(impl)+ Chris(Q2 source delivery)

---

## 1. Internal Architecture

```
backend/ingestion/                  ← W2 D2 create
├── __init__.py
├── orchestrator.py                 ← Pipeline coordinator: parse → chunk → screenshot → embed → emit
├── parsers/
│   ├── __init__.py
│   ├── base.py                     ← ParserResult dataclass + Parser Protocol
│   ├── docx_parser.py              ← Docling-based(W2 D2 F8)
│   ├── pdf_parser.py               ← Docling-based(W2 D5)
│   └── pptx_parser.py              ← python-pptx(W3 D1)
├── chunker/
│   ├── __init__.py
│   ├── layout_aware.py             ← heading-aware section split + token budget(per spec §3.3)
│   ├── slide_based.py              ← per-slide chunk(.pptx)
│   └── strategies.py               ← strategy selector based on KbConfig.chunk_strategy
├── screenshots/
│   ├── __init__.py
│   ├── extractor.py                ← extract embedded images → PIL Image
│   └── uploader.py                 ← async Blob upload to per-KB container(via C12)
├── embedding/
│   ├── __init__.py
│   └── azure_openai_embedder.py    ← async embedding call,MRL truncate 1024d
└── (W3+) auto_sync.py              ← scheduled re-ingest(Beta+ scope)

scripts/
└── inspect_docx_structure.py       ← ✅ W1 D1 stdlib tool(Q17/Q18 finding,run-blocked Q2)
```

### Pipeline flow

```
Input: file path (.docx / .pdf / .pptx)
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│ 1. Parse                                                      │
│    parser.parse(file) → ParserResult                         │
│      ├─ raw_text (full document)                             │
│      ├─ heading_tree (List[Heading{level, text, anchor}])    │
│      ├─ embedded_images (List[Image{bytes, alt, position}])  │
│      └─ tables (List[Table{rows, headers}])                   │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Chunk (layout-aware per spec §3.3)                        │
│    chunker.chunk(parser_result, strategy) → List[Chunk]      │
│      Each Chunk:                                              │
│        - section_path (List[str], e.g. ["Op", "Recovery"])  │
│        - chunk_title (heading text)                          │
│        - chunk_text (~500 token budget)                      │
│        - embedded_image_refs (positional)                    │
│        - table refs                                           │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Screenshot extract + upload (parallel for all chunks)    │
│    For each chunk's embedded images:                         │
│      - PIL → PNG bytes                                        │
│      - SHA256 checksum (dedup)                               │
│      - upload to Blob: ekp-kb-{kb_id}-screenshots/...        │
│      - chunk gets image_refs: List[{blob_url, alt, hash}]   │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. Embed (parallel for all chunks)                           │
│    For each chunk_text:                                       │
│      - Azure OpenAI text-embedding-3-large API call          │
│      - MRL truncate 3072d → 1024d (per spec)                 │
│      - retry on rate limit (tenacity)                        │
└─────────────────────────────┬────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Emit ChunkRecord (per spec §3.5)                          │
│    For each chunk → ChunkRecord(全 fields per §3.5)          │
│      - C03 indexing pushes batch → Azure AI Search           │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Key Interfaces

### Inputs
- File path(.docx / .pdf / .pptx)or bytes + filename
- `KbConfig`(from C02)— `chunk_strategy` selects layout-aware vs slide-based
- KB metadata(`kb_id`,`doc_id` derived from filename or explicit)

### Outputs
- `list[ChunkRecord]`(per `architecture.md §3.5` schema)
- Side-effect:Blob container populated with screenshots
- Side-effect:Azure OpenAI API quota consumed

### `ChunkRecord` schema(per §3.5)
```python
class ChunkRecord(BaseModel):
    chunk_id: str           # "kb-{kb_id}_doc-{doc_id}_chunk-{idx:04d}"
    kb_id: str
    doc_id: str
    doc_title: str
    doc_format: Literal["docx", "pdf", "pptx"]
    chunk_index: int
    chunk_total: int
    chunk_title: str
    chunk_text: str
    chunk_token_count: int
    section_path: list[str]
    embedded_images: list[ImageRef]
    prev_chunk_id: str | None
    next_chunk_id: str | None
    tags: list[str]
    low_value_flag: bool    # logo / TOC / blank
    enabled: bool           # admin-toggle (per spec §3.5)
    source_url: str
    ingested_at: datetime
    embedding: list[float]  # 1024d
```

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **Docling primary parser**(.docx + .pdf) | Spec H2 lock;handles layout extraction(headings, tables, images)better than python-docx alone;active Microsoft project |
| **python-pptx for .pptx**(non-Docling) | Docling .pptx support immature;python-pptx mature + slide model 直接 maps to slide-based chunk strategy |
| **Layout-aware chunking(non character-based)** | Per spec §3.3 + CLAUDE.md §2 routing:character chunking 破壞 semantic boundary;heading-aware preserves context |
| **MRL truncate 3072d → 1024d**(per Q19 default) | Spec §3.2 stack;3072 全用 storage cost 3×,W4 evaluation will decide if 1024 enough(Q19 W2 resolution)|
| **Async parallel embedding**(non sequential) | 30+ chunks per doc × 50ms/embedding = 1.5s sequential vs ~100ms parallel batched |
| **SHA256 dedup for screenshots** | Same logo / diagram across docs:upload once,reference many。Cost saving + storage saving |
| **`enabled: bool` admin-toggle field**(per spec §3.5)| Admin Console(C09 view 6)可手動 disable individual chunk(low-value:logo頁、目錄、版本聲明)without re-ingest |
| **`low_value_flag` heuristic** | Auto-detect on parse:< 50 token chunk,heading 包含 "Table of Contents"/"目錄"/"Index" 等。Default `enabled=false`,admin can re-enable |
| **`source_url`**(per spec §3.5)| Cite back to original doc location;Drive Project URL or SharePoint link |

---

## 4. Edge Cases & Error Handling

| Edge case | Handling |
|---|---|
| **Parse fail**(R7 edge format:SmartArt / equation / handwriting / scan)| `ParserResult` with `failed: True` + reason;C02 KB stores in `FailureRecord` list;Admin Console flags |
| **Embedded image format unsupported**(WMF / EMF / HEIC) | Convert to PNG via Pillow;若 fail → skip image,log warning,chunk continues without image ref |
| **Embedding API rate limit**(R5)| tenacity retry with exponential backoff;若 persistent → fall back to text-embedding-3-small;若 still fail → push doc to retry queue(W4+) |
| **Large file > 100MB**(typical Drive doc 1-10MB,but PPT may large) | Stream parsing where possible;reject > 500MB with clear error;document policy |
| **Encrypted PDF / password-protected** | Detect → reject with clear error("decrypt before upload");FailureRecord |
| **Empty doc(0 chunks after parse)** | Reject as failed("no extractable content");FailureRecord |
| **Duplicate doc_id within KB** | C02 KB Manager check before reach C01;若 race,409 response |
| **Embedding cost runaway**(batch > 1M token) | Pre-flight cost estimate;若 > $5/doc warn admin;configurable threshold |
| **Mid-pipeline failure**(parse OK, embed fail) | Atomic per-doc:rollback partial state(no half-indexed doc);transaction OR mark all-or-nothing in C03 indexing |

---

## 5. Performance Characteristics

| Operation | Time / cost | Notes |
|---|---|---|
| Parse .docx(typical 50-page Drive manual) | ~3-5s | Docling Python lib |
| Parse .pdf(scan-heavy 100-page) | ~10-30s | OCR if scan;Docling handles |
| Parse .pptx(50-slide deck)| ~2-3s | python-pptx |
| Chunk(layout-aware) | ~1-2s for 100 chunks | Pure Python |
| Screenshot extract + upload(20 images)| ~5-10s | Parallel Blob upload via C12 |
| Embed(50 chunks parallel batch) | ~3-5s | Azure OpenAI batched async |
| **End-to-end per doc(50-page Drive manual)** | ~15-30s | Full pipeline |
| **Cost per doc**(embedding + Blob)| ~$0.02-0.10 | text-embedding-3-large $0.13/M tokens |
| **Throughput**(parallel docs concurrent W2-W3) | ~5 docs/min single instance | Limited by embedding rate quota |

---

## 6. Test Strategy

| Test type | Scope | Status |
|---|---|---|
| **Per-parser unit**(.docx fixture, .pdf fixture, .pptx fixture)| Synthetic small docs in `tests/fixtures/` | W2 D2(blocked R8 pytest) |
| **Chunker unit**(known input → expected chunk count + boundaries) | Layout-aware算法 correctness | W2 D2 |
| **Screenshot dedup** | Same image in 2 docs → 1 Blob upload | W2 D3 |
| **Embedding mock** | Deterministic 1024d vector for known input(test infra,not prod call)| W2 D3 |
| **End-to-end on 5 sample**(F8 acceptance) | Real Q2 sample manual → full pipeline → ChunkRecord output → sanity report | **W2 D2 ★ blocked R10 Q2 sample** |
| **R7 edge case fixtures**(SmartArt, encrypted, scan)| Negative test:assert FailureRecord | W3 |
| **Coverage target** | ≥ 80% per CLAUDE.md H6(critical pipeline)| W4 |

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C01 evolution |
|---|---|
| **Multi-modal retrieval(B 類純圖搜)** | Image embedding model alongside text;ChunkRecord 加 `image_embedding` field;C04 加 image-only query path |
| **GraphRAG entity / relation extraction** | New pipeline step after chunk:NER + relation extraction → entities written to separate Azure AI Search index per `C03 future evolution` |
| **JP / ZH multi-language** | Per-language analyzer in chunker;Azure OpenAI multi-lingual embedding;language-aware token budget |
| **Auto-sync from external source**(Beta+) | `auto_sync.py` schedule poll;C12 Azure Container Apps Jobs;detect change via doc hash diff |
| **OCR fallback for scan PDFs** | Azure Document Intelligence integration when Docling OCR insufficient |
| **Structured table extraction → SQL-queryable**(Tier 2)| Tables → separate Azure SQL database;cross-reference via chunk_id |
| **Custom LLM fine-tune dataset prep** | Tier 2 C14 component;C01 emits training pair format alongside ChunkRecord |

---

## 8. Open Items / TODO

- [x] **R10 Q2 sample manual delivery** ✅ closed W1 D4(6 sample uploaded `docs/06-reference/01-sample-doc/`)
- [x] **R8 mitigation** ✅ closed 2026-05-03(home network direct;Docling pip installed)
- [x] **W2 D1 F1 Docling parser PoC** ✅ closed 2026-05-03(all 6 sample parse clean,0 failure,217 headings 6.3%,1018 images,156 tables;`reports/w02_d1_docx_parser_sanity.yaml` baseline)
- [x] **W2 D1 inspector finding mitigation** ✅ via Docling SECTION_HEADER visual layout heuristic(W1 D4 F6 raw style 3% → Docling layout 6.3% averaged;no standalone font-size heuristic needed per F1 acceptance "OR" branch)
- [ ] **W2 D2 chunker layout-aware impl**(F2 — consume `ParserResult.heading_tree` + `raw_text`)
- [ ] **W2 D2 screenshot extractor + Blob upload**(F3 — consume `ParserResult.embedded_images`,SHA256 dedup already computed in parser)
- [ ] **W2 D3 embedding pipeline first-pass**(F4)
- [ ] **W2 D4 orchestrator + index population**(F5)
- [ ] **W3 D1 .pptx parser**(python-pptx)
- [ ] **W3 D1 .pdf parser** edge case validation
- [ ] **Q19 embedding dim decision**(1024 vs 3072)— W2 D3 evaluation feedback
- [ ] **R7 edge case follow-up**:DrawingML(SmartArt/charts)not extracted by Docling without LibreOffice — W3+ scope or per-doc finding analysis if Gate 1 retrieval impacts

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c01--ingestion-pipeline`](../COMPONENT_CATALOG.md#c01--ingestion-pipeline)
- Spec: `architecture.md §3.3`(multi-format ingestion)+ `§3.5`(ChunkRecord schema)
- Risks: R7(format edge case),R10(Q2 delay — critical),R5(Azure OpenAI quota for embedding)
- W1 commit: `cc0b90b`(F6 inspector script)
- W2 D1 commit: `f30f13a`(F1 docx_parser delivery)
- W2 D2 commit: `170e3db`(F2 layout-aware chunker + parser doc_order refactor)
- W2 D3 commit: `28341b8`(F3 screenshot pipeline + F4 embedder + R12 Azurite risk)
- W2 D4 commit: TBD(this session — F5 orchestrator + F6 retrieval engine + /query wire)
- Cross-component: emits to C03 (index sink);uses C12 (Blob);uses Azure OpenAI (via C12);consumed by C04

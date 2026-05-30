---
bug_id: BUG-026
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed
---

# BUG-026 — Progress

> Investigation → fix → verify timeline。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 1 — 2026-05-30

### Done
- 由 W42 post-closeout UI demo follow-up（memory `project_chat_demo_rag_quality_followups`）開 bug task
- Code-trace 3 個 root cause finding(無 live repro —— demo KB `dce-integration-demo-1` 已喺 demo 清理刪除)
- 寫 `report.md`(Sev3,3-finding 診斷)+ `checklist.md`
- **Finding A fix 實作**:
  - NEW pure helper `frontend/lib/chat/citation-images.ts::dedupeCitationImages`(key `checksum_sha256` fallback `blob_url`,首現 citation attribute,full-citations `citationIdx`)
  - `chat/page.tsx`:import helper + `dedupedImages = dedupeCitationImages(message.citations)`;inline cards + ImageGallery + FeedbackBar count 全部改由 deduped 列表 drive;ImageGallery 簽名 `citations`/`allCitations` → `images: DedupedCitationImage[]`(label 保持 mockup-faithful `chunk_title`+`doc_title` per Finding B)
  - `imageCitations` 保留(meta row「N with screenshots」= citations 數,語意正確)
- **NEW test** `tests/unit/citation-images.test.ts`(6 cases)
- **驗證全綠**:Vitest 13 passed(6 新 + 7 既有 `chat-meta-row` 無 regression)/ ESLint clean(唯一 pre-existing `<img>` warning)/ `tsc --noEmit` exit 0 / `npm run build` exit 0(✓ Compiled,15 頁)/ Prettier clean

### Diagnosis update
- **Finding A**(dedup,真 bug):`attach_neighbour_images`（`citation_image_neighbors.py`）跨 citation 無 dedup → 同 `checksum_sha256` 圖落多個 citation;frontend `chat/page.tsx` inline cards(1228-1245)+ gallery(1796)兩處 flat render 無 dedup
- **Finding B**(gallery label = `chunk_title`):code-trace 對 mockup `ekp-page-chat.jsx:653-656` —— **mockup 本身就用 chunk_title + doc_title**(source attribution),所以唔係 bug,改成 alt_text = H7 violation → 不動
- **Finding C**(per-image 真 caption):`alt_text` = ingest Docling caption(`docx_parser.py:117`);有 caption 時 inline title 已正確,無 caption fallback chunk_title;真 fix 屬 ingest 層 + overlap BUG-017 + 需 re-ingest + live 驗 alt_text → 待 user 決策

### Decisions
- Finding A dedup 位置 = **frontend display dedup**(report §8 Alt 1)—— presentation 層問題喺 presentation 層解;保留 backend citation↔image data 完整;contained 喺 chat page
- Finding B 保持 mockup-faithful(§13 mockup wins)
- Finding C 唔自行做 ingest 深度工作(較大 + 需 re-ingest + 需 live 驗證)→ STOP+ask user 方向

### Blockers
- Manual UI verify 需 demo KB 重新 ingest(blobs 已隨 demo 清理刪除)—— code + Vitest 層先驗,UI 層 user-deferred

### Effort
- Planned:0.5h(dedup fix);Actual:_(進行中)_;Variance:_

### Commits
| Hash | Subject |
|---|---|
| `cb5ed75` | fix(frontend): BUG-026 dedup cross-citation duplicate images in chat (C10) |

### Finding C 驗證(user pick「先驗證 alt_text 實際內容」)—— DONE
- 跑 `backend/scripts/diagnose_image_doc_order.py`(`PYTHONIOENCODING=utf-8` 繞 Windows cp1252 console crash)against sample docx,**無需 re-ingest**(純本地 Docling parse)
- **結果**:8/8 圖 `alt_text` **全空**(Docling 抽唔到「Figure N:」caption)+ per-image section 8/8 正確(post-BUG-017)
- **結論**:label mislabel 係真嘢(alt_text 空 → 永遠 fallback chunk section);Finding C 確認需要 ingest 工作先有準確 per-image label;正確 section 已喺 ingest 知道但冇 propagate 落 `ImageRef`
- 詳見 `report.md §6` Finding C 驗證結果 + 3 候選 fix 方向(C-i parser caption / C-ii propagate section / C-iii defer)

### Next
- Finding C fix 方向 = **C-ii**(user pick 2026-05-30)→ 落 Day 2

---

## Day 2 — 2026-05-30(Finding C-ii —— propagate section)

### Done
- **Backend**(4 edit):storage `ImageRef`(`indexing/schemas.py`)+ API `ImageRef`(`api/schemas/query.py`)加 `source_section: list[str]`;`orchestrator.py` ingest 填 `list(spec.section_path)`(owning chunk = parser-correct post-BUG-017);`citation_enrichment.py::parse_embedded_images` parse + defensive coerce
- **Frontend**:`query.ts::ImageRef` optional `source_section?`;`citation-images.ts` 加 `imageSectionPath`(prefer 圖自己 section)+ `imageTitle`(alt_text > section leaf > chunk_title)helpers;`chat/page.tsx` InlineImageCard title+caption + ImageGallery title 改用 helpers
- **Tests**:backend 4 NEW(parse source_section + default-empty + non-list-coerce + storage→query round-trip)/ frontend 6 NEW(imageSectionPath ×3 + imageTitle ×3)
- **驗證全綠**:Backend pytest **48 passed** + 0 new mypy(15 pre-existing 唔 reference 新 code)/ Frontend Vitest **19 passed** + `tsc` 0 + `build` 0 + Prettier clean

### Diagnosis update
- 機制:圖 attach 落 chunk,neighbour-attach 時 `parse_embedded_images` 複製整個 ImageRef → `source_section` 自然帶住圖**自己** section(唔係 citing chunk)→ §8.4 圖 surface 喺 §8 intro citation 都顯示 §8.4

### Decisions
- H1 邊界評估:`embedded_images_json` 係現有 §3.6 index field,只係 JSON payload 內加 key(非 index schema 改);Pydantic additive optional field → **無 H1 trigger / 無 ADR**(per report §6 C-ii note)
- Gallery title 由 `chunk_title`(citing)改 `imageTitle`(圖自己 section)—— C-ii data-accuracy fix,結構維持 mockup-faithful;user explicit pick C-ii「propagate section to fix label」= approved scope

### Blockers
- 🚧 **Live re-ingest + UI verify deferred** —— C-ii 對既有 index chunk latent(`source_section` 空 → frontend graceful fallback citing section);需 re-ingest 一個 KB(backend+azurite+Azure Search infra)先 populate + UI 睇到效果

### Effort
- Planned:1.5h(C-ii cross-layer);Actual:~1.5h;Variance:0

### Commits
| Hash | Subject |
|---|---|
| `d66f5a5` | fix(ingestion): BUG-026 C-ii propagate image source_section for accurate chat labels |

### Live verify(user pick「即刻做」)—— API 層 PASS
- Pre-flight(§10.3 5b):backend :8000 = 200 / Langfuse `/api/public/health` = 200(docker unhealthy flag = timing artifact)/ Postgres healthy
- 起 azurite native(`--skipApiVersionCheck`,blob upload)+ **重啟 backend**(kill PID 43916 舊 code → 載 C-ii code,READY 25s)
- Fresh KB `bug026-cii-verify-1`(`extract_embedded_images=true`+`return_images_in_chat=true`)ingest sample docx → **88 chunks + 8 images uploaded**
- `/query`(mode=vector)dump 證據:
  - citing chunk 44(**§8 intro**,neighbour-attach)2 圖:d7d95af1 → `source_section`=**8.1 Scenario A** / 07561dbf → **8.2 Scenario B**(各帶**自己** section,非 citing §8 intro)✅
  - citing chunk 45(§8.1,direct)d7d95af1 → **8.1 Scenario A** ✅
- **結論**:ingest stamp → index → query parse → API ImageRef `source_section` 全鏈 PASS;neighbour-attach 圖帶自己 section 已證 → C-ii 解「3 figures all tagged §X」確認 work

### 視覺 UI verify —— PASS（browser automation）
- 起 frontend :3001(mock auth 自動登入 dev-user),KB selector 已選 `BUG-026 C-ii verify`,Show images ON
- 第一次 query hybrid 預設 → **402 Payment Required**(`ekp-kb-bug026-cii-verify-1-v1/docs/search`)= Azure Free-tier semantic ranker quota 用盡(memory `project_azure_search_tier_semantic_billing`,**同 C-ii 無關**)
- 加 `.env` `HYBRID_USE_SEMANTIC_RANKER=false`(W42 deliverable Free-tier workaround,暫時 UI-test override)+ 重啟 → 全 pipeline 無 semantic ranker
- 重問「show me all the Integration scenarios」→ gpt-5.5 · **2 citations · 2 with screenshots** · 19.62s:
  - **Dedup(Finding A)PASS**:gallery「REFERENCED SCREENSHOTS · **3**」3 張獨特圖無重覆
  - **C-ii label PASS**:inline card figure 2 = 「**8.2 Scenario B** — Real-time inventory...」/ figure 3 = 「**8.5 Scenario E** — Snowflake daily ETL...」;caption「Citation [N] · ... > 8.x Scenario X」;gallery thumbnail 各標 **8.1 Scenario A** / **8.2 Scenario B** / **8.5 Scenario E** —— 每圖**自己** section,**唔再** tag citing chunk「§8 intro」
- 完後 revert `.env`(HYBRID override 移除 = production-preserve default True)+ 重啟 backend 回 production config

---

## Closeout(status=closed)

### Root Cause(final)
Chat answer 渲染重覆圖 + 圖標題不準,兩個獨立 root cause:**(A)** `attach_neighbour_images` 把同一張鄰圖 attach 落多個 citation,frontend inline cards + gallery 攤平時無跨 citation dedup → 同 checksum 圖 render 多次;**(C)** 圖無 DOCX caption(8/8 alt_text 空)+ 圖嘅正確 section 喺 ingest 知道但冇 propagate 落 `ImageRef` → label fallback 落 citing chunk section,neighbour-attach 圖顯示錯 section。

### Fix Summary
**Finding A**(`cb5ed75`):frontend `dedupeCitationImages` helper —— 跨 citation 以 `checksum_sha256`(fallback `blob_url`)dedup,首現 citation attribute;inline cards + gallery + count 統一由 deduped 列表 drive。**Finding C-ii**(`d66f5a5`):`source_section` 加落 storage + API `ImageRef`,ingest 填 owning chunk section_path(parser-correct post-BUG-017),`parse_embedded_images` 解析,frontend `imageSectionPath`/`imageTitle` helpers + page 用之。**Finding B** mockup-faithful 不動。

### Regression Test
`frontend/tests/unit/citation-images.test.ts`(12 cases:dedup ×6 + imageSectionPath ×3 + imageTitle ×3)+ `backend/tests/test_citation_enrichment.py`(+4:source_section parse + default + coerce + storage→query round-trip)。Fails before / passes after。

### Lessons
- 既有診斷 script(`diagnose_image_doc_order.py`)第 70 行已印 alt_text → 驗 Finding C 無需 re-ingest,純本地 parse 即知 8/8 alt_text 空(`PYTHONIOENCODING=utf-8` 繞 Windows cp1252 console crash)
- C-ii 機制優雅:neighbour-attach 複製整個 ImageRef → `source_section` 自然帶住圖自己 section,無需改 neighbour-attach 邏輯
- Chat UI hybrid 預設撞 Free-tier 402 與本 bug 無關;W42 `HYBRID_USE_SEMANTIC_RANKER=false` flag 正為此場景而設

### Component design note status updates
- C10 Chat UI:image render 由 per-citation flat → unique-image deduped + 圖自己 section label(presentation enrich)
- C01 Ingestion / C03 Indexing:`embedded_images_json` 加 `source_section` key(additive,需 re-ingest populate)

---

**End of BUG-026 progress**

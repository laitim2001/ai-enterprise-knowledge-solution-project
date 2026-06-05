# W46 — UI Ingestion Config + Real KB-Level Reindex · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-04

### Context / kickoff
W45 closed + pushed(`c3d60bb`)。用戶揀 W46 candidate = **UI 開放 ingestion 配置 + 真 KB-level reindex(dev 層)**(roadmap「後續候選」)。

### R6 grep 驗證(plan kickoff)— 揭真 blocker
Explore agent + 親自核實揭出:roadmap [AUDIT-C]「dev 層 iterate docs → reuse doc-level reindex」**估計過樂觀**。真 blocker:
- **原始檔冇存**(已核實):系統只有一個 blob container(`ekp-kb-{kb_id}-screenshots`),**冇 source-document container**。ingest stream 落 tempfile、`finally` 即刪。真 reindex(改 chunk_strategy / 圖數 cap → 重切)要 re-parse 原檔 → 冇原檔做唔到。doc-level reindex 靠用戶 re-upload;KB-level(`kb.py:252-280`)係純 stub(假 task_id + note pending Track A)。
- **mockup locked design**(H7):`ekp-page-kb.jsx:744-815` 將 `embedding_model` / `chunk_strategy` 設 disabled + hint「changing requires re-index」。改 mockup 解鎖 = H7 STOP+ask。

### 決策
- **AskUserQuestion(scope)**:Chris 揀 **Option 4「原始檔儲存 + UI 一次過(大 W46)」** —— 完整自助 loop(backend storage + frontend unlock + 真 reindex)。
- **H1 批准 → ADR-0043**(original-file blob storage + 真 KB-level reindex):NEW `ekp-kb-{kb_id}-sources` container + ingest best-effort persist + KB-reindex iterate `list_documents` 由 source re-ingest + `_run_ingest_pipeline` refactor(接受 file path/bytes)+ production-preserve(pre-W46 doc skip+report)。v1→v2 原子切換 + embedding_model unlock = out-of-scope。
- **H7 frontend = 獨立 design sub-gate**:F3 frontend GATED on H7 mockup design 確認(unlock `chunk_strategy` + 圖數 cap + Reindex UX;`embedding_model` 維持 locked)。design-first 改 mockup per ADR-0024 precedent。

### Done
- F0.1 ADR-0043 Accepted(H1 backend 方向)`docs/adr/0043-*.md`
- F0.2 ADR README index 加 0043 row + next → 0044
- R1 phase 三件套建立(plan/checklist/progress)

### F0.3 H7 design 確認(同日)
Chris AskUserQuestion 批准 unlock scope:**unlock `chunk_strategy` + per-KB 圖數 cap + Reindex KB UX(button + warning modal + summary);`embedding_model` 維 locked**(re-embed 較重另起)。F3 解鎖。

### F1/F2/F4 backend implementation(同日)
- **F1 source 儲存**:`storage/kb_naming.py` 加 `kb_id_to_source_container`(`ekp-kb-{kb_id}-sources`)+ NEW `backend/ingestion/source_store.py`(`upload_source_document` best-effort / `download_source_document`;blob name = `doc_id`,metadata 存 `original_filename` 令 reindex 重建 tempfile + 揀 parser)+ `_run_ingest_pipeline` ingest 成功後 persist 原檔(best-effort,失敗唔 fail ingest)
- **F2 真 KB-reindex**:NEW `run_kb_reindex`(documents.py)iterate `list_documents` → download source → 每 doc mirror doc-level reindex(delete_doc + counter −1,re-ingest +1)→ 同步 summary。**機制選擇**:用 `_bytes_to_upload_file`(BytesIO-UploadFile adapter)復用現成 `_run_ingest_pipeline`,**唔抽 130 行 core**(Karpathy §1.3 surgical,零 working-path regression 風險;ADR-0043 §Decision #4「refactor」以 adapter 達成)。kb.py `reindex_kb` route:加 `request` + archived guard + local import `run_kb_reindex`(避 circular)+ 移除 stub orphan `uuid` import
- **F4 tests**:`test_source_store.py` +6;`test_kb_reindex.py` 更新舊 stub test(202 mock → 503 without deps)+ 3 個 `run_kb_reindex` unit(skip-no-source / reingest+chunks_total / failed-doc report)

### 驗證(三軸)
- pytest:106 passed(test_source_store 6 + test_kb_reindex 7 + test_documents_route + test_documents_detail + test_orchestrator + test_screenshots + test_kb_management)= **0 regression**(source-persist best-effort swallow 唔影響既有 upload 路徑)
- ruff check + format:6 改動 file clean
- mypy --strict(全 import 解析):2 個 my-code error 修正(`int(object)` → isinstance guard / `reindex_kb -> dict` → `dict[str, object]`)後零 error

### Commits
- `84f5ef0` F0 — ADR-0043 + phase kickoff(plan/checklist/progress)
- _(pending — F1/F2/F4 backend code + checklist/progress tick)_

### Next
- **F3 frontend**(H7 解鎖已批准):mockup `ekp-page-kb.jsx` Settings tab unlock chunk_strategy + 圖數 cap + Reindex UX → frontend `kb/[id]/page.tsx` 100% match → wire `POST /kb/{id}/reindex` + summary 顯示 → F4.4 Vitest
- F5 doc-sync → F6 closeout

### Blockers / carry-over
- 無 blocker(H7 gate 已過,backend 綠燈)。R4 live reindex verify 需 Azure + backend(pytest 覆蓋 resolution 邏輯;live 可後評,可能 🚧 deferred)。

---

## Day 2 — 2026-06-05

### Context
F3 frontend(H7 解鎖已批准,F0.3)。Design-first per ADR-0024 precedent:先改 mockup `ekp-page-kb.jsx` → 再令 `page.tsx` 100% match。

### Done — F3.1 mockup(design-first)
`references/design-mockups/ekp-page-kb.jsx` `TabKbSettings`:
- **Unlock chunk_strategy**:seg 移除 `disabled` + `opacity: 0.7`,改 interactive(`data-active={chunkStrategy} onClick={setChunkStrategy}`);label icon `IcShield`(locked)→ `IcRefresh`(warning,需重索引);hint「Locked」→「需重新索引。改變切分策略 → 影響 chunk 邊界…」
- **NEW Max images / chunk 欄位**(ADR-0042):`<input className="input mono" placeholder="繼承全域 (8)">`;hint「留空 = 沿用全域上限(8)…超過即 force-split」
- **Re-indexing 卡 align W46 現實**:explainer ol 由 *v1→v2 原子切換 + eval gate + $3.42 cost*(Track A 願景)改為 *in-place per-doc re-ingest from stored source · synchronous*;補「pre-W46 無 source doc skipped + reported」+「v1→v2 zero-downtime stays Track A」;counts row 去除 fake cost 改「in-place · brief inconsistency window」
- **NEW warning modal**(`.modal-overlay` + `.modal` per DESIGN_SYSTEM §4.5):confirm 前提示「Save config changes first」+ docs/chunks/strategy/maximg 摘要
- **NEW summary banner**(presentational):reindex 後顯示「Re-indexed N/N · M chunks · skipped/failed」shape
- **R6 catch**:mockup explainer 係 pre-W46 aspirational plan-text(v1→v2/eval-gate/cost)與 ADR-0043 in-place 實作衝突 → align 至實作現實(design-first authorship,非單方改架構;v1→v2 仍標 Track A future,符 Tier 1/2 邊界慣例)

### Done — F3.2/F3.3/F3.4 page.tsx + API client
- `frontend/lib/api/kb.ts`:`KbConfig` 加 `chunker_max_images_per_chunk?: number|null`;NEW `KbReindexFailure` + `KbReindexSummary` interface;`kbApi.reindex(kbId)` → `POST /kb/{id}/reindex`
- `frontend/app/(app)/kb/[id]/page.tsx`:
  - header「Re-index」按鈕 `disabled` → enabled + `onClick={handleTabChange('settings')}`(對齊 Retrieval test 按鈕 pattern;mockup header 顯示 enabled)
  - `SettingsTab`:加 `chunkStrategy`/`maxImages` state + `maxImagesValue`(空→null)+ `configDirty` memo(fold topK/rerankK/chunkStrategy/maxImages/knobs);`buildConfigBody` 加 `chunk_strategy`+`chunker_max_images_per_chunk`;`handleSave` config 條件用 `configDirty`;Cancel reset 補 chunkStrategy/maxImages
  - chunk_strategy seg unlock(Shield→RefreshCw,interactive)+ Max images / chunk 欄位(`type="number" min={1}`,跟 page.tsx W43 KbTuneKnob type=number 慣例)
  - NEW `<ReindexCard kb chunkStrategy maxImages>` 元件(置 `<DangerZone>` 前,對齊 mockup「Re-indexing → Danger zone」相鄰):explainer 摺疊 + reindex mutation(success→invalidate kb query + toast summary;failed→banner-warning)+ summary banner + `.modal-overlay` confirm(target-check close per DESIGN_SYSTEM §4.5 canonical)
  - `embedding_model` disabled select 不動(F3.4)

### Done — F4.4 test
`frontend/tests/unit/kb-settings-reindex.test.tsx` +3:(1) chunk_strategy seg not-disabled + Max images 欄位 render;(2) Save PATCH 完整 config 含 `chunk_strategy: 'layout_aware'` + `chunker_max_images_per_chunk: 5`;(3) Re-index modal → confirm → `kbApi.reindex('test-kb')` → summary banner

### 驗證(F3.5,四軸)
- vitest `kb-settings`:**6 passed**(reindex 3 + tuning 3 regression)0 fail
- tsc --noEmit:clean
- next lint:clean(唯一 pre-existing `chat/page.tsx` `<img>` warning 無關)
- `[oklch`=0 preserved(用 inline style oklch,無 Tailwind arbitrary class)

### H7 design fidelity 自檢
Design-first → page.tsx by-construction match mockup。逐項對齊:label icon(RefreshCw)/ seg interactive / hint 文案 / Max images 欄位 / Re-indexing 卡 explainer+counts / modal markup+文案 / summary banner shape。Live-app 差異(summary 條件渲染 vs mockup static example;type=number vs mockup plain input)= 既有 codebase 慣例(empty-state / W43 KbTuneKnob),非新 drift。

### Commits
- _(pending — F3 frontend + checklist/progress tick)_

### Next
- F5 doc-sync(architecture.md §3.5/§4.4/§4.6 + roadmap + session-start)→ F6 closeout

### Blockers / carry-over
- 🚧 R4 live reindex UI verify(需 backend + Azure + 真 KB)— vitest 覆蓋 mutation→summary 邏輯;live click-through 可後評,carry W46 closeout 或 W47+ Track A

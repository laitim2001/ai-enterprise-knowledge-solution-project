# W76 plan — profile read surface(ADR-0056 層 A 段③ 前置)

**Status**: active
**Kickoff**: 2026-06-15
**Phase 類型**: backend feature(純後端,零 frontend → H7 唔 trigger)
**ADR**: ADR-0056 層 A 範圍內(profile persistence + read API 係 D4 L2/L3「睇 profile + 信心度」嘅隱含前置;非新 architectural decision,沿用 ADR-0023 Postgres + ADR-0050 store pattern)

---

## §1 Context / 緣起

W72-W75 把 ADR-0056 層 A 嘅 backend 主幹落地:profiler engine(W72)+ profile→preset
routing(W73)+ PDF picture(W74)+ section 錨定(W75)。但 **profiler 結果係
fire-and-forget**:ingest 時 `IngestionResult.profile` best-effort compute → route 去
preset auto-write(`documents.py:758`)→ **profile label / 信心度 / signals 本身冇持久化、
冇經 API expose**。

`DocumentSummary` / `DocumentDetail`(`api/schemas/listing.py`)冇 profile 欄位。即係段③
三層 UI 想顯示「呢份文件係 P1、信心度 0.9、signals 係咁」**根本冇 data 可 fetch**。

**本 phase = 段③ 三層 UI 之前嘅純後端前置**:persist profile + 經 read API expose。
做完先有 data 餵將來嘅 UI(L1 上載偵測橫幅 / L2 文件列表 badge / L3 文件畫像 section)。

---

## §2 Scope / Deliverables

### F1 — `DocProfileStore` + API schema
- `backend/kb_management/doc_profile_store.py`:mirror `doc_config_store.py` pattern —
  Protocol + `InMemoryDocProfileStore` + `PostgresDocProfileStore`(table `document_profiles`,
  key `(kb_id, doc_id)`,value JSONB)+ `make_doc_profile_store(settings)` factory。
- `backend/api/schemas/doc_profile.py`:Pydantic `DocProfileInfo`(profile: str / confidence:
  float / fallback_applied: bool / signals: `DocProfileSignals` mirror / profiled_at: str ISO)。
  store value = `DocProfileInfo`(一致,mirror DocConfigStore 用 DocConfig)。
- **acceptance**:store CRUD(get/upsert/delete/list_for_kb)mypy strict 0 + ruff 0;
  Postgres branch lazy psycopg import(unset `DATABASE_URL` 唔 touch driver)。

### F2 — ingest 時 persist(best-effort,advisory)
- `documents.py` `_run_ingest_pipeline`:喺 `_route_profile_preset` 附近,`result.profile`
  非 None 時同時 `doc_profile_store.upsert(kb_id, doc_id, DocProfileInfo.from_result(...))`。
- **advisory wrap**(try/except,唔 fail ingest;mirror W73 routing 嘅 `profile_routing_failed`
  pattern)。
- deps wire:`make_doc_profile_store` 接入 app deps(mirror `doc_config_store`)。
- **acceptance**:profile 非 None ingest → store 有 row;profile None / store 缺 → ingest
  bit-identical(zero 副作用)。

### F3 — expose via read API
- `DocumentDetail.profile: DocProfileInfo | None`(完整 signals,L3 文件畫像 section 用)。
- `DocumentSummary.profile: str | None` + `profile_confidence: float | None`(輕量,L2 table
  badge 用 — 唔倒成個 signals)。
- documents route 讀 `doc_profile_store` join:detail 讀單 doc,list 讀 `list_for_kb` map。
- profile 缺 → `null`(語義 =「未分析」,UI 顯示對應 empty state)。
- **acceptance**:GET DocumentDetail 有 profile 時返完整 info;list 有 profile 時返 label +
  confidence;缺 → null;既有 field bit-identical(純 additive)。

### F4 — test(H6)
- store CRUD test(in-memory):get/upsert/delete/list_for_kb + None fallback。
- ingest persist test:profile 非 None → store 有 row;None → 無 row;advisory(store raise
  唔 fail ingest)。
- API join test:detail / list 讀 store(有 profile / 缺 profile null)。
- **acceptance**:pytest 綠;mypy strict 0 + ruff 0。

### F5 — closeout
- verify:新 upload 一份文件入 test KB → ingest 自動 profile + persist → GET DocumentDetail
  見到 profile(end-to-end);或 unit-level 證 read path 接通(視 infra 可用性)。
- memory `project_per_kb_tunable_config_vision.md` append 段③ 前置落地 + MEMORY.md pointer。
- plan closed + progress retro。

---

## §3 設計決策(implementation-level,非 architectural)

1. **持久化位置 = 新 `DocProfileStore`,唔塞 DocConfig**。理由:語義分離 —— DocConfig 係
   用戶可調 knobs(override 語義);profile 係系統偵測 metadata(read-only 事實)。mirror
   DocConfigStore pattern = 最接近既有 pattern(§13 When in doubt)。
2. **expose 兩種粒度**:DocumentDetail 完整 signals(L3 用);DocumentSummary 只 label +
   confidence(L2 table 輕量,避免 list payload 倒大 signals,mirror listing.py bulk-exclusion
   intent)。
3. **現有 KB 空 profile caveat**:doc 只活喺 Azure Search index(冇 documents 持久化表),
   原文件 bytes ingest 後冇保留 → **backfill re-profile 唔可行(無原文件)**。現有 KB
   (drive-images-1)做完本 phase 仍係空 profile,要 **re-index 一次**(W73 routing compute +
   W76 persist 會一齊生效)先有 data。**drive-images-1 production-preserve,唔建議 re-index**;
   verify 改用新 upload。
4. **verify 策略**:優先 end-to-end(新 upload → ingest → GET 見 profile);infra 受限時退
   unit-level(store + API join test 證 read path)。

---

## §4 Non-goals(明確唔做,留後續 rolling JIT)

- **任何 frontend UI**(L1/L2/L3 元素)— 卡 H7 OQ-B mockup,屬段③,本 phase 純後端。
- **backfill recompute endpoint** — 原文件 bytes 唔持久化,re-profile 不可行;標 open。
- **profile re-classify on config change** — profile 係 ingest-time 事實,唔隨 config 變。
- **layer B 查詢意圖 / layer C** — ADR-0056 scope 外。

---

## §5 Risks

- **R1 deps wire 漏接**:`doc_profile_store` 要接入 app deps + ingest path + read route 三處;
  漏一處 → silent null。緩解:F4 ingest persist + API join test 覆蓋三處接通。
- **R2 現有 KB 空 profile 令 verify 受阻**:見 §3.3,verify 用新 upload 繞過。
- **R3 ProfileSignals dataclass → Pydantic 轉換失真**:13 個 signal field 要逐個 mirror;
  緩解:F1 schema test 對齊 field。

---

## §6 紀律自檢(kickoff)

- **H1** ✅ 屬 ADR-0056 層 A 範圍(persist 係 D4 L2/L3 隱含前置);沿用 ADR-0023 Postgres +
  ADR-0050 store pattern,非新 architectural decision。closeout R5 再評估是否補 ADR-0056 addendum。
- **H2** ✅ 零新 dependency(psycopg / pypdfium2 已有)。
- **H4** ✅ profile 係 rule-based label,純 text/structural signal,無 Tier 2 feature。
- **H5** ✅ 無 secret / PII;profile signals 係結構統計(段落數 / 圖密度),無內容洩漏。
- **H6** ✅ F4 test 覆蓋 store + ingest + API join。
- **H7** ✅ **零 frontend 改動 → 唔 trigger**(純後端 read surface)。
- **Karpathy** ✅ simplicity-first(MVP 唔做 backfill / UI);surgical(additive field,既有
  bit-identical);goal-driven(每 F 有 acceptance)。

---

## §7 Changelog

- 2026-06-15 kickoff — plan active,F1-F5 scope locked。

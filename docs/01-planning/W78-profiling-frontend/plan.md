# W78 plan — profiling frontend 實作(ADR-0056 層 A 段③ 落地)

**Status**: closed(2026-06-15,WITH DD-1-BROWSER-DEFERRED CAVEAT)
**Kickoff**: 2026-06-15
**Phase 類型**: frontend implementation(**H7-binding** — 把 W77 mockup 落實到 `frontend/`)
**ADR**: ADR-0056 D4 三層 UI 段③ frontend 落地(W76 backend read surface + W77 author mockup 前置)

---

## §1 Context / 緣起

W76 開咗 profile 讀取介面(`DocumentSummary.profile` + `DocumentDetail.profile` API expose),
W77 author 咗 profiling UI mockup(L1/L2/L3/Settings)入 `references/design-mockups/`。本 phase =
把嗰套 mockup 落實到 `frontend/`,即段③「真正畀用戶用嘅 UI」。

**H7 定位**:本 phase 係 **implementation**(對 mockup),**完全受 H7 約束** —— 每處 layout / spacing /
typography / color tokens / interaction states 必須 100% 對齊對應 mockup(`references/design-mockups/`)。
非 author mockup(嗰個係 W77)。

**落點 grounding(plan kickoff,4 處逐個 read 核實)**:
- L2 = `frontend/app/(app)/kb/[id]/page.tsx` `DocumentsTab`(line 384-456,table 6 欄簡化版)
- L3 = `frontend/app/(app)/kb/[id]/docs/[docId]/doc-config-tab.tsx` `DocConfigEditor`(scope banner line 187-207)
  + parent `docs/[docId]/page.tsx`(已 fetch `DocumentDetail` line 66-70,line 565 pass 落 `DocConfigTab`)
- Settings = `frontend/app/(app)/settings/page.tsx`(`TABS` line 69-76,6 tab;sub-component extracted pattern)
- L1 = `frontend/app/(app)/kb/[id]/upload/page.tsx` `StepExecute`(line 656-864,single-file flow)
- backend contract = `DocProfileInfo` / `DocProfileSignals`(`backend/api/schemas/doc_profile.py`),
  `DocumentSummary.profile` + `.profile_confidence`(L2 輕量),`DocumentDetail.profile`(L3 完整 signals)

---

## §2 Scope / Deliverables

### F1 — TS type 同步(`frontend/lib/api/documents.ts`)
- 新增 `DocProfileSignals`(13-field,mirror backend)+ `DocProfileInfo`(profile/confidence/fallback_applied/signals/profiled_at)。
- `DocumentSummary` 加 `profile?: string | null` + `profile_confidence?: number | null`(L2 輕量)。
- `DocumentDetail` 加 `profile?: DocProfileInfo | null`(L3 完整)。
- **acceptance**:type shape 對齊 backend Pydantic;`tsc` 0 error。

### F2 — L2 文件列表 profile badge(`kb/[id]/page.tsx` `DocumentsTab`)
- Documents table 加「Profile」欄(Tags 後 / Status 前,對齊 mockup Profile-before-Status 相對次序)+
  `ProfileBadge` helper(`PROFILE_LABELS` 7 類中文縮短 label + 信心度 %;低信心 `badge-warning` 黃旗;
  unprofiled `badge-muted`「未分析」)。
- **acceptance**:對齊 mockup `ekp-page-kb.jsx:139-159` ProfileBadge + line 300/326 table 欄;reuse
  `.badge`/`badge-warning`/`badge-muted`/`badge-dot`/`mono`/`muted`;零 hardcode 顏色。

### F3 — L3 文件畫像 card(`doc-config-tab.tsx` + parent pass profile)
- parent `docs/[docId]/page.tsx` line 565 pass `profile={doc.profile}` 落 `DocConfigTab`(parent 已 fetch,
  唔重複 query)。
- `DocConfigEditor` scope banner 後加「文件畫像(自動偵測)」card:`DocProfileBadge`(右上)+ 低信心
  `banner-warning` + signals 透明展示 `stat-grid`(img_density / list_ratio / max_depth / headings /
  pdf_pages+pdf_empty_ratio+pdf_avg_chars 條件 / paragraphs)+ override `select`(7 類)。
- **acceptance**:對齊 mockup `ekp-page-doc-detail.jsx:453-505`;reuse `.card`/`.stat-grid`/`.stat`/
  `.field`/`.select`/`.banner-warning`;card 喺 tuning card 之上(解釋「點解套呢個 preset」);profile=null →
  唔 render card(graceful)。

### F4 — Settings 文件分類規則 tab(`settings/page.tsx` + 新 sub-component)
- 新 `frontend/components/settings/settings-doc-profiling.tsx`(extracted,對齊 SettingsConnections 等
  pattern):profile→preset mapping `table`(7 profile,值對齊 `profile_presets.py` + W75 cap=5)+
  `ThresholdRow`(confidence 0.70 / img_density 0.15 / too_small 20,對齊 `profiler.py`)。
- `settings/page.tsx` `TABS` 加第 7 entry `doc-profiling`「文件分類規則」+ tab body wire。
- **acceptance**:對齊 mockup `ekp-page-settings-tabs.jsx:52-147` SettingsDocProfiling + ThresholdRow;
  reuse `.table`/`.card`/`.field`/`.badge`/`.banner-info`;wrap `<TabBoundary>`(對齊既有 6 tab pattern)。

### F5 — L1 上載偵測 banner(`upload/page.tsx` `StepExecute`)
- StepExecute card-body 加「自動文件分類(W72 profiler)」`banner-info` 說明 banner(對齊 mockup
  `ekp-page-misc.jsx:266-273`)。
- **acceptance**:對齊 mockup banner;reuse `.banner-info`;放 running banner 後(與 mockup 相對位一致)。

### F6 — 驗證 + closeout
- `pnpm lint` + `pnpm tsc`(typecheck)+ `pnpm build`(Next 14 production build)零 error。
- **browser 肉眼驗(DD-1)**:L2(Documents profile 欄)/ L3(文件畫像 card,需有 profile 嘅 doc)/
  Settings(7 tab + mapping table)/ L1(upload 自動分類 banner)視覺對齊 mockup。
- closeout:plan closed + progress retro + memory append。

---

## §3 設計原則(H7 一致性)

1. **100% 對齊對應 mockup** — 每處 implementation 對 `references/design-mockups/` 對應 jsx 逐項對齊
   (layout / spacing / typography / color tokens / interaction states)。
2. **reuse 既有 frontend primitive + CSS class** — `.badge`/`.card`/`.stat-grid`/`.select`/`.banner-*`/
   `.table` 已喺 `styles-mockup.css`;零 hardcode 顏色(`oklch(var(--token))`)。
3. **surgical(Karpathy §1.3)** — 4 處各 surgical 加 section/欄/tab/banner,唔推倒既有結構。
4. **mockup 詮釋衝突 → mockup spec wins**(DESIGN_SYSTEM.md 係 dev convenience layer)。

---

## §4 Backend-limited adaptation(3 處,透明列明 + 全部有既有 codebase precedent)

呢 3 處 mockup 元素受 backend reality 限制,**唔屬新 H7 deviation**(全部落喺既有 documented adaptation 範圍):

1. **L2 低信心判斷** — mockup `ProfileBadge` 用 `fallback_applied || confidence < 0.7`,但 backend
   `DocumentSummary`(L2 輕量)**只 surface `profile_confidence`,無 `fallback_applied`**(per W76 設計:
   summary 唔倒 13-field bundle)。frontend L2 用 `profile_confidence < 0.7` 判低信心。**視覺零差**(低信心 doc
   confidence 必 < 0.7,如 security doc 0.56 → 黃旗仍正確)。L3(`DocumentDetail.profile` 有 fallback_applied)
   用完整判斷。記 changelog。

2. **L3 override select + Settings 編輯/儲存** — mockup 本身係 **static**(`<select defaultValue>` 無 onChange /
   `<input defaultValue>` + button 無 onClick),backend **無 profile override / threshold write endpoint**。
   frontend render 視覺一致嘅 select / input / button,但**唔 wire persist**(對齊 mockup static 行為 +
   codebase `DisabledAffordance` 慣例)。Write surface 屬段③後續(需 backend write API,另一 phase)。

3. **L1 per-doc 即時 profile badge** — mockup 係 multi-doc batch 每 doc 顯示偵測 badge,但 frontend upload 係
   **single-file** flow(W22 既有 adaptation,per `upload/page.tsx` docstring「mockup multi-doc UI is
   aspirational; backend single-file」)+ `uploadDoc` return `{doc_id}` **無 profile**。frontend 做說明
   `banner-info`(完整重現 mockup 說明 banner);per-doc 即時 badge 因 backend 限制改為「完成後可去 Documents(L2)/
   文件詳情(L3)查看畫像」(upload 完 redirect `/kb/{id}` → L2 table 即見 profile)。§13 backend-wins。

---

## §5 Non-goals(明確唔做)

- **backend write API**(profile override / threshold persist)— 段③後續,另一 phase。
- **現有 KB re-index 攞 profile data** — 現有 index profile=null(W76 已知);本 phase 做 UI,re-index 屬獨立 task。
- **L1 multi-doc batch upload** — frontend single-file flow 不變(W22 既定)。
- **LLM tie-break UI**(ADR-0056 D5 保險未實作)。

---

## §6 Risks

- **R1 4 處各有既有結構** — 緩解:逐 F implement 前 read 對應 surrounding context(已 plan kickoff grep 核實落點)。
- **R2 profile=null 空狀態** — 現有 KB doc profile=null → L2「未分析」/ L3 唔 render card;緩解:graceful empty
  state(mockup 已涵蓋 `if (!profile)`);browser 驗用有 profile 嘅 mock 或新 ingest doc。
- **R3 L2 table 欄結構** — frontend Documents table(6 欄簡化)≠ mockup(11 欄);緩解:Profile 欄按 mockup
  相對次序(Status 前)加入既有簡化 table,唔重建 table。

---

## §7 紀律自檢(kickoff)

- **H1** ✅ 唔改 IA / layout philosophy(per ADR-0024 AppShell);現有 page 加欄/card/tab/banner。
- **H2** ✅ 零新 dep(reuse @tanstack/react-query + lucide + 既有 CSS class)。
- **H4** ✅ profiling 係層 A,無 Tier 2 feature。
- **H7** ✅ **implementation 100% 對齊 mockup**;3 處 backend-limited adaptation 有既有 precedent + 記 §4 + changelog。
- **Karpathy** ✅ simplicity(reuse primitive 不發明)、surgical(現有 page 加,不推倒)、goal(每 F acceptance + F6 lint/build/browser 驗)、think-before(plan kickoff ground 4 落點 + 3 backend-limited 識別)。

---

## §8 Changelog

- 2026-06-15 kickoff — plan active,F1-F6 scope locked;4 落點 read 核實;3 處 backend-limited adaptation 識別(§4)。
- 2026-06-15 F1-F5 implement(commit `1af8f59`)— TS types + L2 badge + L3 文件畫像 card + Settings 第 7 tab +
  L1 說明 banner;對齊各 mockup;3 backend-limited adaptation 兌現(§4)。F6.1 三重綠驗:type-check 0 +
  lint 零新 warning + build ✓ 15/15 static pages。
- 2026-06-15 **F6.2 browser 肉眼驗 DEFERRED**(🚧)— backend + frontend 均 DOWN,需起全套 infra + 現有 KB
  profile=null 要 re-index 先見「有 profile」視覺;三重綠驗 + H7 verbatim CSS class + W77 同類 primitive 已驗
  覆蓋 correctness。target:用戶 explicit trigger 起 infra。
- 2026-06-15 closeout — plan closed WITH DD-1-BROWSER-DEFERRED CAVEAT,F1-F5 + F6.1 + F6.3 tick(F6.2 🚧)。

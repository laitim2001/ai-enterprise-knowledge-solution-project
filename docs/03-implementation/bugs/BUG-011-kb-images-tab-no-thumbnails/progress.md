---
bug_id: BUG-011
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed
last_updated: 2026-05-23
---

# BUG-011 — Progress

> Bug-fix workflow per `PROCESS.md §4`。

## Day 1 — 2026-05-23

### Investigation

BUG-009 / BUG-010 全部 push 後,用戶 chat 報告:`/kb/sample-doc-with-image-1?tab=images` 雖然 badge 數字 = 8,但格子內**完全睇唔到圖片內容**。

逐項隔離:

- **Step 1** — backend proxy probe:用 BUG-010 嘅 proxy URL `curl http://127.0.0.1:8000/kb/sample-doc-with-image-1/screenshots/<sha>.png` → HTTP 200 / image/png / 圖 bytes。即係 backend serve 圖完全冇問題。
- **Step 2** — frontend code review:`frontend/app/(app)/kb/[id]/page.tsx` `ImagesTab`(line 700+)+ `ImageCard`(line 890-981)—— 整個 `ImageCard` JSX **從未 reference `img.url`**;hero 區只係 gradient + `<Layers>` icon + page label,根本冇 `<img>` element。`img.url`(BUG-010 之後已係絕對 proxy URL)係 dead prop。
- **Step 3** — browser network panel:整個 page lifecycle **冇任何** `/screenshots/<sha>.png` GET 觸發 —— 同 frontend code review 一致(冇 `<img>` 等於冇 network request)。

→ Root cause = frontend `ImageCard` 從未 wire `<img>` render。BUG-010 通 proxy URL,但 component 一直 render placeholder。

### Mockup audit + H7 trigger

讀 `references/design-mockups/ekp-page-kb-extras.jsx:100-152`:**mockup `ImageCard` 自己都係 gradient + `<IcLayers>` placeholder**,連 `ImageDetailModal`(`:154-245`)個 preview 區都係 placeholder,而 `blob_url` 當純文字顯示(`:194-197`)。即係 mockup 係**冇 image server 嘅靜態 HTML prototype**,placeholder 係 prototype 技術限制,**唔係刻意嘅設計**。

→ render 真縮圖 = **偏離 mockup 嘅視覺** = **H7 trigger**,per CLAUDE.md §5.7 H7 必須 STOP + surface + 等用戶決定。

**Self-correction**:我上一個 turn(總結請求前)講「問題 1...沿用 chat ImageGallery precedent;非 H7 violation」係錯嘅 —— 當時未讀 mockup `ImageCard`。讀 mockup 後立即更正並 surface deviation 畀用戶,per AskUserQuestion 2 options(Option A real 縮圖 with onError fallback / Option B 保留 placeholder)。

### Decisions

- **D1** — 分類 Bug-fix BUG-011 Sev3。用戶 chat 確認開 BUG。
- **D2** — H7 deviation **Option A authorized**(用戶 AskUserQuestion answer 2026-05-23):130px gradient hero → `<img src={img.url}>` object-fit cover,保留 page label overlay + onError fallback 返 gradient + Layers placeholder。Rationale:Images tab 嘅產品本意係 visual gallery,一個全部 placeholder 嘅 gallery 無實際用途;mockup placeholder 屬 prototype 限制非 design intent。
- **D3** — `ImageDetailModal` 喺 mockup 有(`:154-245`)但 frontend `ImagesTab` 無 wire(現有 ImageCard 冇 `onClick`,亦無 modal component)→ 屬 W20 F5 mockup-expansion 未實作 scope,**Out of BUG-011 scope**(non-existent feature,非 regression)。
- **D4** — 無 ADR:純 frontend component render layer,非 architectural / vendor / storage-layout(H1/H2 不觸發)。

### Code changes

| 檔案 | 改動 | Trigger |
|---|---|---|
| `frontend/app/(app)/kb/[id]/page.tsx` | `ImageCard`(line 890+):130px gradient hero 換成 conditional `<img src={img.url} alt={img.ocr_text || 'screenshot'} loading="lazy" style={{width:'100%',height:'100%',objectFit:'cover'}}>`;`useState<boolean>` for `imgError`;`onError` → `setImgError(true)` 觸發 fallback 返 gradient + `<Layers>` placeholder。保留 page label overlay + 下方 ocr_text / doc_name / `screenshot_type` badge 完全不變 | H7 Option A authorized |

### Verify gates

- `pnpm exec tsc --noEmit` → **exit 0**(zero output;TypeScript strict clean)
- `pnpm exec next lint` → **✔ No ESLint warnings or errors**(`@next/next/no-img-element` 用同 chat page `:1354 / :2076` 一致嘅 `eslint-disable-next-line` annotation pattern)
- `Grep '[oklch'` in `frontend/` → **0 occurrences across 0 files** —— `[oklch`=0 milestone preserved through edit(冇加新 hex;新加嘅 `oklch(var(--muted) / 0.4)` 仍係 CSS variable form)
- Browser smoke → 🚧 **user pre-Beta smoke**:Chrome MCP extension 未連線(同 W12-W18 / W20-W24 carry-over pattern;automated gates 全 green,interactive `<img>` proxy URL render + onError fallback 視覺驗證 = 用戶手動 refresh 個 page。Backend proxy 本身 BUG-010 已 curl-verified HTTP 200 / image/png / 513068 bytes;chat page 用同樣 `<img>` + proxy URL pattern 已實際 work;BUG-011 嘅 edit structurally inherits 同樣 wiring。)

### Commits

_(見 commit footer — `fix(frontend): ...` BUG-011 — placeholder convention same as BUG-009/010)_

### Retro

- **H7 self-correction value**:上一個 turn 講「非 H7 violation」係錯嘅 reflex judgment(基於「render `<img>` 同 mockup mismatch?Auto-assume 冇」)。讀 mockup `ImageCard` 之後立刻發現 mockup 自己都係 placeholder —— 提醒以後**每次涉及 frontend visual change 嘅 chat 判斷,先讀 mockup 對應 component 至少一次**,唔可以基於 hand-wave precedent(chat `ImageGallery`)推斷其他 component(KB Detail `ImageCard`)嘅 H7 狀態。Karpathy §1.1 think-before-coding 嘅實踐 = 讀 mockup 先講話 fidelity。
- **Mockup prototype 限制 vs design intent 嘅 reconciliation**:當 mockup 因技術限制(無 image server / 無 data backend)render placeholder 而真產品明顯需要 real content 時,H7 §5.7 trigger surface + Option A/B AskUserQuestion 係 lightweight + auditable 嘅處理。**將來類似 case**(eg.「mockup 嘅 stat card 顯示 0/—,真產品要顯示真實數字」)應該預期相同 pattern:read mockup → surface deviation as H7 trigger → AskUserQuestion → proceed。
- **BUG-009/010/011 closure cascade**:R12 closure(BUG-009)→ counter + proxy(BUG-010)→ frontend render(BUG-011)三步閉環 = 完整 screenshot pipeline 端到端 visible。Future-tier follow-up:(a) delete/reindex 嘅 `total_screenshots` decrement(dedup ref-counting,per BUG-010 retro)/ (b) `ImageDetailModal` 實作(modal preview + dedup viz + chunk reference list,per mockup `:154-245`)/ (c) chat citation 圖片 render(屬問題 2 範疇,另開 investigation)。

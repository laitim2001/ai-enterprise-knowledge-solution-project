# W84 progress — P4 掃描件 ingest 預檢 guard + force override（ADR-0065）

> Daily progress + decisions + commits + 結尾 retro。

---

## Day 1 — 2026-06-16

### 緣起（擱置層 C → 評估層 A/B → 揀做 P4 guard）

W83 收尾後用戶問「是否繼續推進層 C」→ 我建議 hold（無 precision 痛點 + 反噬全召回 + H4 邊界）。
用戶擱置層 C，要評估層 A scan robustness / 層 B query 意圖 gate：
- **層 B（DD-10）** — 同層 C，動機已被層 A W75 section 錨定吸收（55%→0%），無痛點 → hold。
- **層 A scan（DD-9）** — 核心（robustness + 分類）已 OK（2026-06-15 實證），唯一可做 = **P4 預檢 guard**
  防同步 ingest hang 8–9.5 分鐘，但 conditional on production 開放 PDF 上傳。

用戶 AskUserQuestion 揀「**做層 A P4 預檢 guard**」+ guard 行為「**預檢警告 + 「仍要繼續」force 覆寫**」。

### 設計（ADR-0065 Accepted）

- **核心洞察**：OCR（慢）喺 `parser.parse()`（Docling），profiler 喺 parse **之後** → guard 要喺 OCR **之前**
  判 P4。而 P4 偵測用 pypdfium2 **pre-OCR** probe（秒級，獨立讀 PDF，不依賴 parse 結果）→ 正好可前置攔截。
- **guard**：`is_scan_pdf(path)` helper（抽自 profiler probe）→ `_run_ingest_pipeline` parse 前 `.pdf` 判 P4 +
  非 `force_scan` → 422 `ingest.scan_requires_confirm`；force → 跳 guard。
- **frontend**：`uploadDoc` 帶 `force_scan` + 接 422 → 警告 banner（`banner-warning` 復用）+ 「仍要繼續」→ force 重試。
- **production-preserve**：只對 `.pdf` 跑秒級 probe；born-digital PDF 照常；docx/pptx 跳過。

### 決策

- **ADR-0065 Accepted**（用戶連續 AskUserQuestion：擱置 C → 評估 A/B → 揀 P4 guard → 揀預檢警告+force）。
- guard 行為 = 預檢警告 + force override（非硬 reject，保留自調呼應 vision；非 async，force 同步等待係知情取捨）。
- DD-9 由「結構性 defer」**收窄** — guard 落地後剩餘只有 OCR 慢（Tier 2 本質）。

### Commits

| Hash | Subject | Checklist |
|---|---|---|
| `59d05e2` | W84 kickoff + ADR-0065 | plan/ADR |
| `636699b` | backend `is_scan_pdf` helper + ingest guard + `force_scan` flag + test（70 passed） | F1.1-F1.5 |
| F2 | frontend `ScanRequiresConfirmError` + `uploadDoc(forceScan)` + upload `scan-confirm` 警告態 | F2.1-F2.2 |

### F2 frontend（完成）

- **`kb.ts`**：export `SCAN_REQUIRES_CONFIRM_CODE` + `ScanRequiresConfirmError`；`uploadDoc(kbId, file, forceScan = false)`
  加 `?force_scan=true`；422 時 parse envelope `error.code` 比對 → throw typed（否則 generic Error）。
- **`upload/page.tsx`**：`uploadMutation` mutationFn 改收 `{ file, forceScan }`；新 `onForceRun`（force 重試）；
  `StepExecute` 加 `scan-confirm` status（`error instanceof ScanRequiresConfirmError`）→ `banner-warning` 警告
  （掃描件 + OCR ~8–9.5 分鐘）+ `badge-warning` +「仍要繼續」primary 按鈕。**全用既有 primitive，H7 視覺零發明**。
- **gate**：type-check 0 / lint 零新 warning（唯一 `chat/page.tsx:1882 <img>` pre-existing）/ build ✓（15/15）。

### 下一步

- F3 browser 驗（playwright）：upload scan PDF → reject 路徑秒級判 P4 → `banner-warning` +「仍要繼續」render；
  born-digital / docx → 無警告正常。**需先重啟 dev server**（F2 build 已停 port 3001 dev）。

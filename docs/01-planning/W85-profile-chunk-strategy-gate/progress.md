# W85 progress — profile→chunk_strategy F0 實證 gate

> Daily progress + decisions + commits + 結尾 retro。

---

## Day 1 — 2026-06-16

### 緣起

W84 收尾後用戶 status review 整理 vision 落地全景,揀推進**缺口①**（profile→chunk_strategy ingest 路由 =
「不同文件用不同處理流程」最完整一塊）+ 揀 **F0 實證 gate 先**（避免幻影價值,W83 教訓）。

### Grounding（R6,plan kickoff）

讀 `orchestrator.py` / `documents.py:_select_chunker` / `chunker/strategies.py` / `profile_presets.py` /
`strategy_comparison.py` 揭 5 發現:
1. **技術可行** — orchestrator `parse→ profile→ chunk`,profile 在 chunk 前已算。
2. **chunker parse 前選死** — route `_select_chunker` 用 per-KB `chunk_strategy` 選好傳入 orchestrator 固定 →
   按 profile 路由要延後選 chunker（改 orchestrator 簽名）。
3. **選擇空間小** — 只 2 chunker class（Layout + Heading）;profile→strategy 現階段 = heading vs layout 二選一,
   且只對 docx 有對比意義。
4. **OCR 已自動** — Docling 對無文字層 PDF 自動 OCR（parser 層）→ 缺口①只剩 chunk_strategy 路由。
5. **W53 live runner 不存在** — `strategy_comparison.py` 只有 stub test;方法論 self-retrievability（confounded）
   + synthetic GT（非 human）→ 相對信號非 verdict。

### 決策

- **F0 方法論定為「結構分析為主 + self-retrievability 佐證」** — 因 live runner 不存在 + self-retrievability
  confounded,F0.1 離線 chunk 結構對比（不需 KB/judge）作主判據,F0.2 recall 作 conditional 佐證。
- **F1 框架 conditional on F0 PASS** — F0 PASS 才開 ADR-0066（H1）;FAIL/marginal 則 defer。
- 用戶揀「先做 F0 實證 gate」（status review 對話）。

### 現有 KB（grounding）

12 個 KB,全 `chunk_strategy=auto`（除 `w54-live-ab-1` + `w56-drive-ab-1` = heading_aware,可作 F0.2 throwaway）。
F0.1 離線不需 KB,用 `docs/06-reference/01-sample-doc/` 代表文件。

### Commits

| Hash | Subject | Checklist |
|---|---|---|
| W85 kickoff | plan/checklist/progress | plan |

### 下一步

- F0.1 離線 chunk 結構對比 script（代表 docx × heading/layout chunker → 結構 metrics）。

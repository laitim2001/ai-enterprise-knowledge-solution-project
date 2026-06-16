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

### F0.1 離線結構對比（完成）

script `scripts/w85_chunk_structure_compare.py`（`-m scripts.` module path 跑；first run `python scripts/x.py`
撞 `ModuleNotFoundError: ingestion` — script 所在目錄入 sys.path 非 backend/，改 `-m scripts.x` 解）。
5 代表 docx，profiler 分類 **5/5 全對**（FA/GL=P1_sop_imgdense 0.95 / AI-Gov/DCE=P2_prose 0.80 / Form=P5_form 0.90）。

| 文件 | profile | strat | chunks | tok_mean | frag | img(tot/chk/max) |
|---|---|---|---|---|---|---|
| FA | P1 圖密SOP | heading | 86 | 95 | 2.39 | 222/49/8 |
| | | layout | 78 | 105 | 2.79 | 222/43/8 |
| GL | P1 圖密SOP | heading | 85 | 89 | 2.02 | 212/52/8 |
| | | layout | 74 | 103 | 2.39 | 212/44/8 |
| AI-Gov | P2 散文 | heading | 36 | 100 | 1.44 | 0 |
| | | layout | 35 | 103 | 1.46 | 0 |
| DCE | P2 散文 | heading | 121 | 101 | 1.07 | 8/8/1 |
| | | layout | 88 | 139 | 1.1 | 8/8/1 |
| Form | P5 表單 | heading | 9 | 189 | 9 | 0 |
| | | layout | 10 | 171 | 10 | 0 |

**判讀（偏無顯著 profile-differentiated 差異）**：① 圖分布兩 strategy **完全相同**（圖由 parser 抽，chunker 只分配）;
② 結構差異 3–27% 小，無 profile 出現「用對 strategy 戲劇改善」;③ heading 賣點「1 section 1 chunk」在圖密 SOP(最需要)
失效(frag 2.0–2.4，圖密 section 撐爆 hard_cap 被 split)/ 純散文 DCE 接近理想(1.07)但 layout 也 1.1(沒差)。
**根因**：2 chunker 本質太相似(差別只 target-balance + adjacent-merge)，內容結構(圖+table+短 section)淹沒 strategy 差異。

### 決策待定（gate 方向）

F0.1 結構信號偏 marginal/defer。請用戶定:就此下 gate（省 F0.2，記 DD + 結論「需先有差異化 chunker class」）
vs 仍跑 F0.2 self-retrievability recall 佐證再判。

### 下一步

- gate 方向（用戶定）→ F0 closeout 或 F0.2。

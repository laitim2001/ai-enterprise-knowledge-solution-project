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

### PIVOT（用戶揀「造差異化 chunker」）

F0.1 後用戶 AskUserQuestion 揀 pivot:既然真缺口是「2 chunker 太相似」,把缺口①由「路由」重新界定為「先診斷
哪個 profile 真需要本質不同切法」。F0.2（recall 佐證）取消（路由已否決）;新增 F0.3 診斷。記 plan §7 changelog（R3）。

### F0.3 差異化 chunker 診斷（完成）

dump script `scripts/w85_chunk_dump.py`（坑:① `python scripts/x.py` import 失敗 → `-m scripts.x`;② 我用的 `⏎`
U+23CE 撞 console cp1252 → 改 ASCII ` / ` + `PYTHONIOENCODING=utf-8` 跑）。dump P5 表單全 10 chunk + P1 FA 圖密 top6。

**判讀 — 兩 candidate 都不需要差異化 chunker**：
- **P5 表單**:frag=10 看似異常,但 dump 揭每 chunk = 一個邏輯區塊（layout_aware 按 table row group 切:#0 基本資料 /
  #1 描述 / #2 AI Type 勾選 / #3 資料存取 / #5 第三方 / #6 Output / #7 Stage / #8 Review）,**語意完整無 label/value 切開損害**。
  frag=10 是表單本質（10 個邏輯區塊一個 heading 下）,非硬切。
- **P1 FA 圖密**:top6 chunk 全 img=8（cap 撐滿）,都在 `2 FA01` 的 2.1.x「步驟+每步截圖」= W83 已揭 anchoring 失配
  （圖粒度>步驟粒度）,已被 W59-83 處理（image-recall ~1.0 + 錨定 + 分組 + cap）。
- **根因**:`layout_aware` 已相當通用（table-aware + heading-aware + image-grouped via doc_order）,profile 差異化需求
  要嘛已被它吸收（表單 row group）,要嘛已被他層處理（圖密 → W59-83 呈現層）。

### F0 整體結論（缺口① 兩路皆否決）

- **F0.1**:路由現有 chunker 無價值（heading vs layout 太相似,結構差異 3-27% 小,圖分布相同）。
- **F0.3**:造差異化 chunker 也無明確價值（P5 表單已合理切 / P1 圖密已被吸收）。
- → **缺口① defer**:**有價值的負面實證** — 現有 ingest（通用 layout_aware + W59-83 圖處理）已足夠好,
  profile-differentiated chunking 在 Tier 1 無明確增量。避免投入中等成本框架做幻影價值（W83 教訓再現:
  vision 某層在執行過程被後續工作吸收）。

### 決策待定（gate 確認）

F0.3 診斷信號清楚 → 推薦 gate=defer + 記 DD。待用戶確認（或有其他 candidate profile 想看）。

### 下一步

- gate 確認（用戶）→ F0 closeout（plan closed + DD + memory）。

# W63 — checklist(Q005 section-miss 診斷)

> 對應 plan.md F1–F4。

## F1 — V4 retrieve-only 層(上游穩定性)

- [x] backend health 200(現有條件,唔重啟)
- [x] `POST /kb/drive-images-1/retrieval-test`(Q005 text / hybrid / rerank=true / top_k=20)×5
- [x] 記 S17–S22 chunk 嘅 rank 分佈 + 跨 run 穩定性表 → progress.md(AC1:5 runs 逐位元相同,
      top-5 = AR07 ×4 + AR06 ×1 單錨點;機制 (a) 反證)

## F2 — `/query` @ rerank=5(下游成敗對應)

- [x] `/query`(Q005 + `top_k_rerank=5` 顯式)×6,每 run 記 cited sections + returned 圖數
- [x] 成敗分類 + cited-section 對應表(AC2:4 全覆蓋 / 1 b-1 位移(AR06=0)/ 1 b-2 零引用
      (cits=0);機制 (c) pin 排除為次要)
- [x] 樣本混合,毋須加 runs(R1 解除)

## F3 — `/query` @ rerank=10(假設驗證)

- [x] `/query`(Q005 + `top_k_rerank=10` 顯式)×6,同樣記錄
- [x] 對照 F2:6/6 結構一致(AR06 ×4 + AR07 ×7),連 W62 累計 12/12 零 flip(AC3:
      top-10 有三條 AR06 = 錨點冗餘)

## F4 — 判決 + doc-sync

- [x] 機制判決((b) cite 層雙模式:b-1 單錨點位移 + b-2 零引用)+ 風險一般化 → progress.md(AC4)
- [x] 額外發現:cap 預算被 expansion aux 重複 ref 食(20 ref = 9 unique;citation_enrichment.py:111
      by design 無 dedup)— dedup-before-cap 列候選(H1-adjacent,未做)
- [x] rollup §4.5 / memory doc-sync
- [x] plan.md changelog closeout + status → closed;progress.md retro
- [x] AC5 核對:零 KB 狀態改動(全程 per-query override,免復原)

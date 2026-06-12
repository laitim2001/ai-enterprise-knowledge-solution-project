# W66 — progress(cap 計 refs 假說診斷)

## Day 1(2026-06-12)— kickoff

### 定義決策(本 phase 觸發點)
- 用戶拍板:**圖密文件成功定義 = 全圖召回**(先行,後可改)→ mega-query(GT 65–73)
  recall 0.62–0.74 缺口正式要追;definition-dependent 項解凍方向:GT 型指標軸 = image-recall;
  caption 路線判據 = 本 phase 結果。
- 假說鏈:W62「returned 釘 48 < cap=60 → cap 未 binding」可能誤判 — W63 核實 cap 計 refs
  (citation_enrichment.py:111 無 dedup)+ W65 live cap=50 raw=50 撞 cap / unique=31 →
  **48 可能 = 60 refs 被重複食剩嘅 unique 數,cap 一直 binding 喺 refs 層**。

### 三件套 committed(R1 gate)
- `docs(planning): W66 cap-refs-vs-unique diagnosis kickoff`

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
- `docs(planning): W66 cap-refs-vs-unique diagnosis kickoff`(`fbb7dd0`)

### F1 — cap 50→150 ✅(readback 150,其餘欄位不變)

### F2 — mega query 三個數(直接由 `/query` response 數)
| Run | cits | RAW refs | UNIQUE | GT hit | vs cap=60(W62)|
|---|---|---|---|---|---|
| Q001 r1 | 26 | **150(撞新 cap)** | **48** | 48/65(0.74)| unique 48 → 48,**零增長** |
| Q001 r2 | 26 | 150 | 48 | 48/65 | 兩 run 穩定 |
| Q043 r1 | 23 | 150 | **53** | 53/73(0.726)| unique 48 → 53,**+5** |

### F3 — 復原 ✅(cap=50 + rerank=10 + max_aux=40 + parent_doc=False + pin=True = W64 persisted 值)

### F4 — 判決(plan §2 判決表)
1. **強形式假說反證(Q001)/ 部分成立(Q043)**:refs 確實即刻脹滿任何 cap(60→150 全食),
   但 Q001 unique 釘死 48(多出 90 refs **全部重複**);Q043 unique +5(cap=60 嘅 dup-waste
   有少量真代價)。**結論:48–53 = 收割範圍 unique 圖總量嘅真天花板**,唔係 cap 假象。
2. **漏網圖喺收割範圍以外**:Q001 GT 跨 S03–S06(含 S04 mega-section 44 圖),漏網 17 張
   喺呢啲 section 內但 cited chunks ± window 掂唔到(W62 已證 window=8 無效,即唔係 reach
   半徑問題,係**根本冇 cite 到嗰啲 chunk 區域**)。
3. **dedup-before-cap 提案降級**:由「關鍵槓桿」降為「邊際改善(+0~+5 unique)+ payload 衛生」
   (cap=150 時 response 孭 150 個 ref 好重)。喺 persisted cap=50 下 dup-waste 對 mega query
   代價 ~0–5 張 → **唔值得單為 recall 行 H1 改 pipeline**;若將來做,理由應係 payload/語義
   清潔,非 recall。
4. **全圖召回定義下嘅剩餘路徑**(0.74 → 1.0 需 harvest-range 擴展,全部 H1 territory,
   用戶決策):(a) 程序/章節範圍圖片收割機制(ADR-0047 pin 嘅推廣版);(b) §4.6 caption
   語義揀圖;(c) 接受 ~0.74 為 Tier 1 旋鈕天花板。**下一步建議 = 先做零 code 嘅「漏網 17 張
   chunk-level 映射」診斷**,知道敵人喺邊先揀武器。

### Retro
- 「judgement 表先行」設計(plan §2)令一個 run 出嚟就有判決歸屬,冇 post-hoc 解讀空間。
- 三個數軸(raw / unique / GT-hit)缺一不可:單睇 returned(driver 嘅 unique)會繼續
  誤判 cap 唔 binding;單睇 raw 會以為供給好大。
- 成功定義(全圖召回)已記入 rollup;definition-dependent 項解凍:GT 型指標軸 = image-recall。
- 零 code、KB 已復原 W64 persisted 值、無 ADR(per-KB toggle as-designed)。

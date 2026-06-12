---
phase: W66
name: cap-refs-vs-unique-diagnosis
status: closed       # draft | active | closed
created: 2026-06-12
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "用戶 2026-06-12 拍板成功定義 = 全圖召回 → mega-query 0.62–0.74 缺口要追;W62「returned 釘 48」嘅真因驗證 = 追缺口嘅第一步"
adr: null            # 純 per-KB cap toggle 診斷(跑完復原),零 code → 無 ADR;若證實 → 後續 dedup-before-cap 屬 H1 route 另行 STOP+ask
spec_refs:
  - docs/01-planning/W62-image-recall-supply-side-ab/   # 「48 plateau / cap=60 未 binding」原判讀(本 phase 驗證對象)
  - docs/01-planning/W63-q005-section-miss-diagnosis/   # cap 計 refs 唔計 unique(code 核實 citation_enrichment.py:111)
  - docs/01-planning/W65-config-test-image-section-coverage/  # live 實證:cap=50 raw=50 撞 cap / unique=31
---

# W66 — 「48 plateau」真因診斷(cap 計 refs 假說)

> **緣起**:用戶 2026-06-12 拍板**成功定義 = 全圖召回**(先行,後可改)→ mega-query(GT 65–73)
> recall 0.62–0.74 嘅缺口正式要追。W62 判讀「returned 釘 ~48 < cap=60 → cap 未 binding,另有
> 下一層箝制」— 但 W63 code 核實 **cap 計 refs(含跨 citation 重複)**,W65 live 又見
> cap=50 時 raw=50(撞 cap)/ unique=31。**假說:W62 嘅 48 = 60 refs 預算被重複食剩嘅 unique 數,
> cap 一直 binding(喺 refs 層)**。若證實 → 全圖召回嘅下一槓桿 = dedup-before-cap(H1 route,
> 另行 STOP+ask)或 per-KB cap 再抬(數據層 stopgap);若反證(cap 抬高 unique 仍釘 48)→
> 真供給天花板,指向 §4.6 結構路線。
>
> **R6 核實**:`cap_images_per_answer`(citation_enrichment.py:111)budget 逐 citation 行
> `embedded_images[:budget]`,無 cross-citation dedup(ADR-0040 blunt by design,W63 已核)✅;
> drive-images-1 現 persisted cap=50(W64)→ 本 phase 臨時 PATCH 抬 cap,跑完**復原 50**;
> recall driver 計 unique checksum(`extract_returned_checksums`)→ raw vs unique 要由 `/query`
> response 直接數。

## 1. 設計

| 步 | 內容 | 判據 |
|---|---|---|
| **F1** | PATCH cap 50→**150**(遠超 GT 73×2,保證 refs 不 binding)+ readback gate | readback=150 |
| **F2** | `/query` mega query ×2(Q001;另加 Q043 ×1)直接數 **raw refs / unique / GT hit** | 見 §2 判決表 |
| **F3** | 復原 cap=50 + readback | 逐欄位 = W64 persisted 值 |
| **F4** | 判決 + doc-sync(rollup §4.5/§4.6 + memory + 定義決策記錄)+ 若證實 → 提案 dedup-before-cap(STOP+ask,唔自行做)| 判決寫低 |

## 2. 判決表(AC)

| 觀察(cap=150)| 結論 |
|---|---|
| unique 升至 ~60+,recall 明顯升 | **假說證實**:cap-on-refs 一直 binding;下一槓桿 = dedup-before-cap(H1 提案)或 cap 持久抬高(數據層);caption 路線繼續按兵不動 |
| raw refs 升但 unique 仍釘 ~48,recall 持平 | **假說反證**:48 = 真供給天花板(cited+neighbour 收割範圍嘅 unique 圖總量);追缺口要去供給上游(cite 覆蓋 / §4.6)|
| 介乎兩者(unique 升少少就停)| 混合:cap-on-refs 食咗部分,但供給上限都近;兩個數都報 |

- **AC1**:F2 每 run 報齊 raw / unique / GT-hit 三個數(直接由 response 數,唔靠 driver)。
- **AC2**:F3 復原 readback 逐欄位 = W64 值(cap=50 / max_aux=40 / rerank=10)。
- **AC3**:判決按上表寫低;**任何 code 改動(dedup-before-cap)唔喺本 phase 做** — 屬 pipeline
  行為改動(H1-adjacent),證實後以提案形式 STOP+ask。
- **AC4**:「成功定義 = 全圖召回(2026-06-12 用戶拍板,先行後可改)」記入 rollup(definition-
  dependent 項解凍:GT 型指標入 UI 軸 = image-recall;caption 路線判據 = 本 phase 結果)。

## 3. 風險

- **R1 🟢 cap=150 答案更重 / synth 更慢**:單 query 診斷,timeout 120s 下若 timeout 就記錄(本身
  係有用信號)+ 用 180s env 重試一次分離變量。
- **R2 🟢 infra transient**:同 W61–W64,probe-恢復-重試。

## 4. 非目標

- ❌ dedup-before-cap 實作(H1 route,證實後另行提案)。
- ❌ 改 W64 persisted preset(跑完復原 50;要唔要按結果抬 cap = 用戶決定)。
- ❌ GT 型指標入 UI(定義已鎖,但屬獨立大 phase,另排)。

## 5. H 核對

- **H1**:零 code;per-KB cap 臨時 toggle + 復原(ADR-0040 機制)→ 不觸;後續 fix 先至係 H1 範圍
  (明文唔喺本 phase 做)。**H4/H5/H6/H7**:不觸(checksum 軸 / mock auth / 零新 code / 無前端)。

## 6. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-12 | Initial plan(active)| 用戶拍板成功定義 = 全圖召回 → mega 缺口要追;W63 cap-計-refs + W65 raw=50 撞 cap 實證令「48 plateau」假說可一兩 run 判生死 |
| 2026-06-12 | **Phase closed**(F1–F4 全 done,3 runs)| **強形式反證**:cap 150 下 refs 即脹滿(150)但 Q001 unique 釘死 48(+90 refs 全重複)/ Q043 +5(53)→ **48–53 = 收割範圍 unique 圖總量真天花板**;漏網 GT 圖喺未-cite 區域(window 已證無效)。dedup-before-cap 降級為邊際項(唔提案)。全圖召回剩餘路徑 = harvest-range 擴展機制(H1)/ caption(H1)/ 接受 0.74 — 用戶決策;建議先做零 code 漏網圖 chunk-level 映射。KB 已復原 W64 值 |

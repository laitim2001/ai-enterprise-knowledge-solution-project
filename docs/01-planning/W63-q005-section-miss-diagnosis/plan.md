---
phase: W63
name: q005-section-miss-diagnosis
status: closed       # draft | active | closed
created: 2026-06-12
owner: "Claude (AI) — 技術 Lead Chris 審閱"
gap: "差距 ② — Q005 型 section-miss(普通問題、答案隨機漏成段 section)嘅機制診斷;W62 假設 = rerank=10 買 section 覆蓋穩定性"
adr: null            # 純診斷跑數(existing API surface,per-query override),零 code/schema/KB 狀態改動 = §5.1「加 test」例外
spec_refs:
  - docs/01-planning/W62-image-recall-supply-side-ab/   # rerank=10 穩定性假設來源(Q005 6/6 vs 擲毫)
  - docs/eval-set-image-recall-ar.yaml                  # Q005 GT(S17–S22,32 圖)
  - docs/adr/0021-*                                     # V4 retrieve-only diagnostic surface
---

# W63 — Q005 section-miss 機制診斷

> **緣起**:Q005「How do I set up a collection letter and then generate it?」(雙段程序題,GT =
> S17–S22 六 section / 32 圖)係 W59 起唯一嘅 C 類 section-miss query:同 config 同 query,
> returned 喺 0↔32 之間隨機擺。W62 收窄咗範圍:**rerank=10 嘅 6/6 runs = 1.00;rerank=5 = 擲毫
> (1.00/0/1.00/0/0)**。本 phase 目標 = 搵出**機制**,令 fix 係證據型而非碰彩。
>
> **三個候選機制**(F1/F2 設計就係分辨佢哋):
> - **(a) retrieval/rerank 層**:S17–S22 chunk 喺 rerank top-5 邊界浮沉(入池與否 = 擲毫源頭)
> - **(b) synthesizer cite 層**:chunk 穩定喺 top-5,但 LLM(temperature)隨機唔 cite
> - **(c) neighbour artifact**:成功 run 根本冇 cite S17–S22,32 張圖係隔籬 cited chunk 嘅
>   window±3 neighbour 收割返嚟
>
> **R6 核實(2026-06-12)**:V4 `POST /kb/{kb_id}/retrieval-test`(ADR-0021,retrieve-only,無
> CRAG 無 synthesis)response 有 per-chunk `rank/section_path/score`(`api/schemas/retrieval_test.py`);
> `/query` 支援 **per-query `top_k_rerank`**(CH-007,per-query > per-KB > global,query.py:156)
> → **診斷全程零 KB PATCH、零復原負擔**;Citation 有 `section_path` + `embedded_images`。
> KB 現狀 = 原值(cap=20 / rerank=5 / max_aux=18)— 本 phase 唔郁佢。

## 1. 範圍(Scope)

單 query(Q005)分層診斷,KB = `drive-images-1`,backend 現有條件(timeout 180 / semantic off)。

| 步 | 層 | 方法 | runs |
|---|---|---|---|
| **F1** | retrieval + rerank(上游)| V4 `retrieval-test`(hybrid / rerank=true / top_k=20)記 S17–S22 chunk 嘅 rank 分佈 + run 間穩定性 | ×5 |
| **F2** | full pipeline @ rerank=5 | `/query` + 顯式 `top_k_rerank=5`,記每 run cited sections + 圖數,成敗對應 | ×6 |
| **F3** | full pipeline @ rerank=10 | `/query` + 顯式 `top_k_rerank=10`,驗 W62 穩定性假設 + cited sections | ×6 |
| **F4** | 判決 + doc-sync | 機制敘事((a)/(b)/(c) 邊個)+ 風險一般化 + rollup/memory 更新 | — |

## 2. Acceptance Criteria

- **AC1**(F1):S17–S22 chunk 喺 top-20 嘅 rank 表 ×5 runs + 穩定性判斷(rank 浮動 vs 穩定;
  落喺 1–5 / 6–10 / 11–20 / 不在 邊個 band)。
- **AC2**(F2):6 runs 成敗分類(成 = returned 圖 ∩ GT 顯著)+ 每 run cited section 清單;
  成敗差異必須能用 cited sections 解釋(= 機制證據,分辨 (b) vs (c))。
- **AC3**(F3):rerank=10 成功率 band(W62 預測 ~6/6)+ cited sections 對照 F2 → 確認「點解
  rerank=10 穩」。
- **AC4**(F4):機制判決明文寫低 + 一般化(邊類 query / 文件結構有同樣風險;對「成功定義 =
  section 覆蓋」嘅含意);若 6 runs 樣本唔夠分辨(e.g. F2 全成 / 全敗)→ 加 runs(R1)。
- **AC5**:**零 KB 狀態改動**(per-query override only,前後唔使 PATCH/復原)、零 code、無 ADR。

## 3. 風險

- **R1 🟡 樣本量**:Q005 擲毫型,6 runs 可能唔夠(全成/全敗就分唔到)。緩解:AC4 允許加 runs;
  歷史先驗(rerank=5 ≈ 40% 成功)6 runs 大概率混合。
- **R2 🟢 transient 502**:同 W61/W62,單次重試。
- **R3 🟡 機制混疊**:(a)+(b) 可以並存(rank 浮動 × cite 隨機)。緩解:F1 五 run rank 穩定性
  係分離變量嘅第一證據;F2/F3 cited-section 對照補刀。

## 4. 非目標(Non-goals)

- ❌ 落 fix / persist(rerank=10 係咪入 preset = 用戶 persist 決策,連同 W62 preset 一齊拍板)。
- ❌ Gap B query 意圖 gate(等定義)。
- ❌ 擴 GT / 第二份 prose GT(卡用戶)。
- ❌ 改 image-recall harness(本 phase 直接打 API,唔改 driver)。

## 5. ADR / Hard Constraint 核對(H1–H7)

- **H1**:零 code/schema/vendor/storage/config 改動;per-query param 係 existing API surface → 不觸。
- **H4**:診斷限文字 section / rank / citation 軸,無 image embedding。
- **H5**:mock auth `Bearer dev-token`;不碰 .env。
- **H6**:零新 code。
- **H7**:無前端改動。

## 6. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-06-12 | Initial plan(active)| 隊列 ②;W62 rerank=10 穩定性假設做起點;R6 核實 V4 schema + per-query top_k_rerank(CH-007)→ 零 KB 狀態改動設計 |
| 2026-06-12 | **Phase closed**(F1–F4 全 done,17 runs)| 機制判決:**(a) retrieval 反證**(V4 ×5 逐位元相同,top-5 = AR07×4 + AR06×1 單錨點);**(b) cite 層雙模式證實** — b-1 單錨點位移(LLM 唔 cite 唯一 AR06 → expansion 無錨點,Setup 半邊消失,~1/6)+ b-2 零引用(cits=0,refuse 同族,~1/6);**rerank=10 = 錨點冗餘 fix**(top-10 有 AR06 ×3;連 W62 累計 12/12 零 flip);(c) pin 次要。額外:cap 預算被 expansion aux 重複 ref 食(20 ref = 9 unique;dedup-before-cap 列 H1-adjacent 候選未做)。零 KB 狀態改動、零 code、無 ADR |

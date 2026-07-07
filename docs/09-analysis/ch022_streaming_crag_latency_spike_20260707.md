---
id: CH-022-spike
title: 串流查詢加 CRAG(方案 A)latency spike — 零成本結構性評估
date: 2026-07-07
type: spike / analysis
status: done(零成本估算層;精確實測列為 follow-up)
scope: 診斷 only — 零 production code 改動,不 trigger H1
related: CH-022(spec.md)/ pipeline review Q-R2 / ADR-0007(L2 CRAG)/ architecture.md §3.4 §3.5 §7.3
---

# CH-022 spike — 串流加 CRAG 的 latency 評估(方案 A)

## 0. 目的與範圍

評估「方案 A(串流前 gate):串流合成**之前**先跑 CRAG grade + 必要時 re-retrieve」加在
串流首 token 前的 latency 影響,以決定**值不值得走 ADR 實作方案 A**,還是改採方案 B / C。

**本 spike = 零成本結構性估算**(靜態 code 分析 + 既有 latency baseline + CRAG 既有
instrumentation 欄位),**零 production 改動、零 Azure 成本、不 trigger H1**。latency 絕對值
為基於組件特徵 + 既有 P95 cap 的**量級估算**,非本地實測;精確值列為 follow-up(§6)。

## 1. 現狀(code 核對)

- CRAG L2 只在**非串流** `/query`:`query.py:445` retrieve + 完整 synth 之後呼叫
  `crag_loop.refine()`。
- **串流** `/query/stream`(chat UI 主路徑)**完全無 CRAG**:`crag.py:23` docstring 註
  「stream 是 L3-only」,而 L3 從未實作(`feature_l3_routing_enabled=False`)。
- 效果:**面向用戶的主路徑跑緊零檢索品質修正** —— 低信心檢索不會觸發 rewrite + re-retrieve。

## 2. 方案 A 結構拆解(首 token 前的額外步驟)

**串流路徑現有鏈條**(首 token 前,`query.py:query_stream`):

```
retrieve → per-doc overlay → context expand → parent-doc(flag) → synth stream(首 token 由此出)
```

**CRAG `refine()` 的組件**(`crag.py:CragLoop.refine`):

1. `grade(query, chunks)` — 一次 gpt-5.4-mini call,**input = query + 全部 retrieved
   chunks 全文**(`_build_grader_user_message` 拼晒每個 chunk 的 title + text)。**一定執行**。
2. 若 `confidence < threshold`(default 0.70)→ 觸發修正:
   - `rewrite_query(query, chunks)` — 再一次 gpt-5.4-mini call(input 較細,只 chunk titles)。
   - `engine.retrieve(rewritten, top_k=20)` — 一次 hybrid search + rerank(re-retrieve)。
   - (方案 A 下:對修正後 chunks 串流合成,而非 `refine()` 現有的完整 re-synth)

**關鍵洞察 — `grade` 的是 chunks 不是 synth**:`refine()` 現有簽名收 `initial_synth`,
但 `initial_synth` 只是「不觸發時要回傳的東西」,**grade 本身只需 chunks**。所以方案 A 可
**跳過 initial synth**(省一次完整合成),直接:retrieve → grade →〔低信心:rewrite +
re-retrieve〕→ 對最終 chunks 串流合成。

**方案 A 首 token 前的額外延遲:**

| 情況 | 首 token 前新增 | 說明 |
|---|---|---|
| **一定加**(所有 query) | `grade` 一次 mini call | input = N chunks 全文 → input 大,非輕量 |
| **低信心觸發時再加** | `rewrite`(mini call) + `re-retrieve`(hybrid+rerank) | 疊在 grade 之上 |

## 3. Latency 量級估算(既有 baseline + 組件特徵)

> ⚠️ 以下為**量級估算**,來源:architecture.md §3.4 `Hard latency cap P95 < 5s`
> (query expansion retrieval)+ gpt-5.4-mini call 的組件特徵 + CRAG 既有 `latency_ms` /
> `crag_latency_ms` instrumentation 欄位語義。**非本地實測**;精確值需 §6 follow-up。

- **`grade` call(一定加)**:gpt-5.4-mini 一次 chat completion。output 只 1 個浮點數(輸出極短、
  快),latency 由 **input 處理 + TTFT 主導**;input = N chunks 全文(N = retrieval 後 chunk 數,
  可達數十)→ input token 數千級 → 量級傾向 **~0.5–2s**。
- **`re-retrieve`(低信心觸發)**:一次 hybrid search + rerank,落在既有 **P95 < 5s cap** 量級內,
  典型 **~0.5–2s**;疊 `rewrite`(~0.3–1s)。
- **觸發率**:未有沉澱數字(W4 threshold 0.70 的 empirical calibration 當時 deferred,docs 無實測)。
  觸發率決定 rewrite+re-retrieve 的平均攤銷 —— **這是最需要實測補的一個數(§6)**。

**首 token 前總額外延遲量級:**

| 情境 | 額外延遲量級 |
|---|---|
| 高信心(不觸發,佔多數) | **~0.5–2s**(純 grade) |
| 低信心(觸發修正) | **~1.5–5s**(grade + rewrite + re-retrieve) |

## 4. 核心發現 — 方案 A 的根本張力(與精確數字無關)

**串流的核心價值 = 首 token 快出(即時感)。方案 A 把 grade 放在串流合成之前,意味著
「無論是否觸發修正,每個 query 的首 token 前都必須先等一次完整的 grade LLM call」。**

這是**結構性**的,與 grade 具體多快無關:

- 現狀串流首 token ≈ retrieve + expand 後即開始吐字。
- 方案 A 首 token ≈ 上述 + **一次 grade call**(高信心)甚至 + rewrite + re-retrieve(低信心)。
- 即使 grade 只要 0.5s,也把串流「快首 token」的核心優勢**系統性打折**;觸發時 ~1.5–5s
  才見第一個字,即時感基本消失。

**換言之:方案 A 用「串流體驗」換「主路徑有 CRAG」。** 這正是 `crag.py:23` docstring 當初
把 CRAG 定為 non-stream-only 的原因(「correction loop would require buffering tokens which
breaks SSE token-by-token UX」)—— 方案 A 沒有消除這個張力,只是把它從「mid-stream rewrite」
搬到「pre-stream gate」,首 token 延遲的代價依然存在。

**疊加風險**:synth-timeout(DD-7 / ADR-0053,120s)不變,但 grade + re-retrieve 佔掉的時間會
壓縮合成預算(邊角情況)。

## 5. 三方案評估 + 建議

| 方案 | 串流即時感 | CRAG 品質修正 | 改動幅度 / 風險 |
|---|---|---|---|
| **A 串流前 gate** | ❌ 系統性打折(每 query +grade;觸發 +re-retrieve) | ✅ 與非串流同一 grader,主路徑真有修正 | 大,H1,需 ADR;首 token 代價是結構性的 |
| **B 串流後 verify** | ✅ 保留(先串流,事後 verify) | 🟡 較弱(低信心只提示 / 附註,不 re-synth) | 中,仍 H1;不動首 token |
| **C 維持現狀 + 定調** | ✅ 不變 | ❌ 主路徑續無 CRAG | 最低,只文件化為 Tier 1 已知取捨 |

**Spike 建議(方向仍待用戶 + ADR 定,因屬 H1):**

1. **方案 A 有實質且結構性的串流體驗成本** —— 不是「調一下就好」,而是「串流快首 token」與
   「合成前 gate」本質衝突。若要走 A,ADR 必須明確接受「主路徑首 token 變慢」這個 trade-off,
   並先補 §6 實測數字量化傷害程度。
2. **方案 B 是折衷點**:保留即時感,事後 verify 給低信心信號(如「此回答檢索信心偏低」附註),
   改動與風險都比 A 細。若目標是「讓用戶主路徑對低信心可見」而非「一定要 re-synth」,B 性價比更高。
3. **方案 C 若 stakeholder 接受**:成本最低,只需在 architecture.md 明確定調串流無 CRAG 為
   Tier 1 已知取捨(對齊 spec 原本「屬 spec 允許的 defer」)。

**傾向**:先不急於走 A。B 或 C 更貼 Tier 1 simplicity;A 的價值需由「低信心 query 實際佔比 ×
修正實際帶來的品質提升」證成,而這需要 §6 實測 + 一次品質 A/B,成本不低。

## 6. Follow-up — 若要精確數字(需起 backend,H1 前置)

零成本層已足以支撐「方案 A 有結構性串流成本、傾向先考慮 B/C」的方向判斷。若用戶要在走 ADR 前
拿硬數字,follow-up spike(需起 backend + Azure,注意 loaded machine + Free-tier semantic 402):

1. 起 backend,對 5–10 條 query(**刻意含低信心觸發 case**)跑非串流 `/query`(有 CRAG),
   從 Langfuse `crag.grade` / `crag.refine` observe 或 structlog `crag_loop` event 抽:
   - `grade` latency 分佈(p50/p95)
   - `extra_retrieval_latency_ms`(re-retrieve)
   - **實際觸發率**(confidence < 0.70 佔比)
2. 量串流現有首 token latency baseline 作對比。
3. 把 grade latency 疊上 baseline → 方案 A 首 token 的實測退化幅度。

## 7. 結論

- **不改任何 production code**;本 spike 純診斷。
- 方案 A 的關鍵不是「latency 幾多毫秒」,而是**結構性地犧牲串流首 token 優勢** —— 這點與精確
  數字無關,已足以讓決策 informed。
- **建議**:方向先傾向 B(串流後 verify,保即時感)或 C(定調),A 需 ADR 明確接受首 token
  trade-off + §6 實測證成。最終方向由用戶決定(H1,需 ADR + Chris approve)。

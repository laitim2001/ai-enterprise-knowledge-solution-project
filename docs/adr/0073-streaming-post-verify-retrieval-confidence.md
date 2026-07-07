# ADR-0073: 串流查詢事後檢索信心 verify(方案 B 純後端信號)— CRAG-style grade 擴到 `/query/stream`,不 re-synth

**Date**: 2026-07-07
**Status**: Accepted
**Approver**: 用戶 2026-07-07 作 architecture decision owner 拍板 Accept(對齊 RBAC track ADR-0066/0067/0068 先例;Chris 技術 Lead)

## Context

CRAG L2(ADR-0007)只在**非串流** `/query`(`query.py:445` retrieve + synth 之後呼叫
`crag_loop.refine()`);**串流** `/query/stream`(chat UI 主路徑)**完全無 CRAG** —— `crag.py:23`
docstring 註「stream 是 L3-only」,而 L3 從未實作(`feature_l3_routing_enabled=False`)。

pipeline review Q-R2 指出:**面向用戶的主路徑跑緊零檢索品質信號** —— 低信心檢索不會被
偵測、亦無任何可觀測性。屬 spec 允許的 defer,但效果是「主路徑對低信心完全不可見」。

CH-022 spike(2026-07-07,`docs/09-analysis/ch022_streaming_crag_latency_spike_20260707.md`)
評估三方案:

- **方案 A(串流前 gate)**:串流合成前先 grade + 必要時 re-retrieve。**結構性犧牲串流首 token
  優勢**(每 query 首 token 前必等一次 grade call)—— 被否。
- **方案 B(串流後 verify)**:串流合成**完成後**做事後 verify,低信心給信號、**不 re-synth**。
  保留串流即時感。
- **方案 C(維持現狀 + 定調)**:接受串流無 CRAG,只文件化。

用戶 2026-07-07 選 **方案 B**;呈現方式選 **純後端信號**(不面向用戶 UI → 零 H7)。

## Decision

在 `/query/stream` 串流合成**完成後**加一個事後 verify step:

- 用**既有** `CragGrader.grade(query, streamed_chunks)` grade 已串的 chunks → confidence ∈ [0, 1]。
  **沿用非串流同一 grader**,不新增 vendor / 演算法(H2 clean)。
- **純後端信號**:
  - 低信心(confidence < `crag_confidence_threshold`,default 0.70)→ emit structured warning +
    metric(固定 event name `stream_low_retrieval_confidence`,帶 `kb_id` / `confidence`;對齊
    CH-021 fail-open 可觀測性風格,供 log aggregator 當 metric)。
  - done frame(或 result frame)加 `retrieval_confidence` 欄位(float),供前端**將來**用;
    本期前端不消費 → **零 H7**。
- **明確不做**:
  - 不 re-synth、不 rewrite、不 re-retrieve(避開方案 A 的首 token 代價;grade 在串流後,
    不影響首 token)。
  - 不面向用戶 UI 提示(spike 呈現方式選項 2 badge = 前端 H7;選項 3 末尾附註 = 改回答內容)—
    兩者本期不做,留將來 scope。
  - 不做 L3 adaptive routing(architecture.md §7.3 明列 Tier 2)。

**是否阻塞 done frame**:impl 決定(spec §4),傾向**同步**(串流 token 全部吐完後 grade,
再發帶 `retrieval_confidence` 的 done frame)—— 因 grade 在串流之後,首 token 不受影響。

## Alternatives Considered

- **方案 A(串流前 gate)** — Reject:結構性犧牲串流「快首 token」核心優勢(spike §4)。即使
  grade 只 ~0.5s,也把每個 query 的首 token 前置延遲;低信心觸發時 ~1.5–5s 才見第一個字。
- **方案 C(維持現狀 + 定調)** — Considered:成本最低,但主路徑續無任何低信心信號。方案 B 以
  極小成本(串流後一次 grade call)換到可觀測性,優於純定調。
- **面向用戶提示(選項 2 badge / 選項 3 末尾附註)** — Defer:選項 2 碰前端 = H7;選項 3 改
  回答內容。純後端信號先達成「主路徑對低信心可見」;UI 提示留將來 scope(done frame 已帶
  `retrieval_confidence` 為其保留 hook)。
- **Re-synth 版方案 B** — Reject:串流後 re-synth 等於把方案 A 的 re-retrieve/re-synth 搬到
  串流後,latency + 複雜度上升,違方案 B「輕量事後 verify」定義。

## Consequences

- **Positive**:
  - 主路徑(串流,chat 主要入口)首次有檢索品質可觀測性 —— 低信心不再靜默。
  - **不影響首 token**(grade 在串流完成後)—— 保留串流即時感,這正是選 B 而非 A 的核心理由。
  - 沿用既有 `CragGrader` —— 零新 vendor / 零新演算法(H2 clean)。
  - 對齊 CH-021 fail-open 可觀測性風格(固定 event name + metric)。
  - done frame 帶 `retrieval_confidence` 為將來 UI 提示(選項 2)留 hook,不鎖死。
- **Negative**:
  - 整體回應**完成時間**尾端加一次 grade call(~0.5–2s;不影響首 token,但影響「完全結束」時間)。
  - grade 對「已串 chunks」;若串流路徑用了 context expand / parent-doc 後的 chunks,grade 的
    input 與非串流 CRAG grade 的 input 可能略異 —— impl 需明確對齊用哪一組 chunks(傾向與
    非串流 `refine()` grade 同一組 = retrieval 後的 chunks)。
- **Neutral**:
  - 純後端信號本期前端不消費;是否阻塞 done frame(同步 vs fire-and-forget)為 impl 決定。
  - 不改 CRAG L2 演算法 / grader 本身(沿用)。

**H1 範圍**:改 architecture.md §3.1 串流查詢管線 CRAG 適用範圍(「CRAG = non-stream-only」→
串流有輕量事後 verify)。**architecture.md inline-tag amendment 作 follow-up**:`crag.py:23`
docstring 引「§3.5」之 section ref 待乾淨環境核實正確位置後補(ADR 本身已權威記錄本決定,
H1 流程 = 寫 ADR + Accepted 已滿足,對齊 ADR-0024 doc-sync 先例)。

## References

- ADR-0007 L2 CRAG(base decision;本 ADR **extend** 到串流事後 verify,不 supersede)
- CH-022 spec(`docs/03-implementation/changes/CH-022-streaming-crag-parity/spec.md`)
- CH-022 spike(`docs/09-analysis/ch022_streaming_crag_latency_spike_20260707.md`)
- pipeline review Q-R2(`docs/09-analysis/pipeline_review_20260706.md`)
- architecture.md §3.1 RAG Core pipeline(CRAG / L3 routing)/ §7.3 L3 adaptive routing(Tier 2)
  — 註:`crag.py` docstring 的「§3.5」CRAG 引用待核實,architecture.md inline-tag 作 follow-up
- CH-021 ingest fail-open 可觀測性(`8797108`)— 純後端 structured warning + metric 風格 precedent

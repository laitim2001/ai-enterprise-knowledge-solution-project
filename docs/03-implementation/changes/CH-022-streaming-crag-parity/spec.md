---
id: CH-022
title: 串流查詢路徑(chat 主路徑)加 CRAG,與非串流對齊
status: done            # 2026-07-07 用戶選方案 B + approve ADR-0073 → 落 code(純後端信號)+ 4 test 綠
created: 2026-07-06
requester: pipeline review(`docs/09-analysis/pipeline_review_20260706.md` Q-R2,代碼核對)
backlog: B-17
related: ADR-0073(方案 B 串流事後 verify,Accepted)/ ADR-0007(L2 CRAG)/ architecture.md §7.3(L3 adaptive routing = Tier 2)
---

# CH-022 — 串流 CRAG 對齊

## 1. 背景

CRAG L2 self-correction 只在**非串流** `/query`(`query.py:445`)呼叫;`/query/stream` **完全無 CRAG**(`crag.py:23` 註「stream 是 L3-only」,而 L3 從未實作,`feature_l3_routing_enabled=False`)。**因為 chat UI 用串流,面向用戶的主路徑跑緊零檢索品質修正** —— 低信心檢索不會觸發 rewrite + re-retrieve,CRAG 實際只在 eval / 非串流 harness 生效。

屬 spec 允許的 defer,但效果是「用戶主路徑無 CRAG」,值得補齊或明確定調。

## 2. 行為規格(方向已定 = 方案 B,2026-07-07)

**方向決策**:spike(§6 + `docs/09-analysis/ch022_streaming_crag_latency_spike_20260707.md`)後,用戶 2026-07-07 選 **方案 B(串流後 verify)** —— 保留串流即時感,事後 verify 給低信心信號、**不 re-synth**。方案 A 因結構性犧牲串流首 token 優勢被否。

**方案 B 具體設計(呈現方式暫定 = 純後端信號〔選項 1,推薦〕,待用戶最終確認):**

- 串流合成**完成後**,用既有 `CragGrader.grade(query, streamed_chunks)` grade 已串的 chunks → confidence ∈ [0, 1]。**沿用非串流同一 grader**,不新增 vendor / 演算法(H2 clean)。
- **不 re-synth、不 rewrite、不 re-retrieve**(方案 B 定義:純事後 verify;避開方案 A 的首 token 代價)。
- 低信心(confidence < `crag_confidence_threshold`,default 0.70)→ emit structured warning + metric(對齊 CH-021 風格:固定 event name 如 `stream_low_retrieval_confidence`,帶 `kb_id` / `confidence`)。
- done frame(或 result frame)加 `retrieval_confidence` 欄位(float);**本期前端不消費 → 零 H7**。
- 呈現方式的其他候選(需另定 scope):選項 2 面向用戶提示 badge = 前端 UI = **H7**;選項 3 回答末尾附註 = 改回答內容。兩者本期不做。

**核心張力(原始記錄)**:CRAG 需要完整檢索集 + 可能 re-retrieve,與串流「增量逐 token yield」有結構性張力。原候選方案(spike 前):

- **方案 A(串流前 gate)**:串流合成**之前**先跑 CRAG grade + 必要時 re-retrieve(非增量,短暫延遲),再對修正後的 context 串流合成。保留串流體驗,CRAG 在合成前完成。
- **方案 B(串流後 verify)**:串流合成後做一次事後 verify,低信心時提示 / 附註(不 re-synth)。較弱但改動小。
- **方案 C(維持現狀 + 明確定調)**:接受串流無 CRAG,文件化為 Tier 1 已知取捨,不補。

**建議**:方案 A 最貼近非串流對齊,但需先 **spike** 評估 latency 影響(CRAG grade + 潛在 re-retrieve 加在首 token 前 → 影響串流「即時感」)。

## 3. 唔做(out of scope)

- 不做 L3 adaptive routing(architecture.md §7.3 明列 Tier 2)。
- 不改 CRAG L2 演算法 / grader 本身(沿用非串流既有 `crag_loop`)。

## 4. 邊界 / 待確認

- **屬 H1**(改 architecture.md §3.1 串流查詢管線行為 + §3.5「CRAG = non-stream-only」適用範圍)—— **落 code 前必須寫 ADR + Chris approve**(方案 B 即使純後端信號仍是 H1)。
- **呈現方式**待用戶最終確認(暫定選項 1 純後端信號;選項 2 面向用戶提示 = H7 另一 scope)。
- **是否阻塞 done frame**:同步(done frame 等 grade;因 grade 在串流完成後,首 token 不受影響)vs fire-and-forget(先出 done,grade 後補 log)—— 待定,傾向同步(可把 `retrieval_confidence` 放入 done frame)。
- Latency:方案 B 的 grade 在串流**完成後**,**不影響首 token**(這正是選 B 而非 A 的原因);只在整體回應完成時間的尾端加一次 grade call。
- 疊加 synth-timeout(DD-7 / ADR-0053,120s)風險需一併考量(grade 在 synth 之後,不佔 synth 預算)。

## 5. 驗證(等 approve 後據此驗)

- 串流查詢對低信心檢索**觸發 CRAG 修正**(與非串流同一 grader 判定一致)。
- 正常查詢串流體驗無顯著退化(首 token latency 在可接受範圍)。
- 非串流路徑不受影響。

## 6. 實作記錄

**2026-07-07 spike(零成本結構性估算)完成** — 見 `docs/09-analysis/ch022_streaming_crag_latency_spike_20260707.md`(純診斷,零 production 改動、零 Azure 成本、不 trigger H1)。

摘要:

- 方案 A(串流前 gate)一定把一次 `grade`(gpt-5.4-mini,input = N chunks 全文)加在串流首 token 前;低信心觸發時再加 `rewrite` + `re-retrieve`。量級:高信心 **~0.5–2s** / 低信心 **~1.5–5s**(基於既有 `Hard latency cap P95<5s` + 組件特徵估算,**非本地實測**)。
- **核心發現(與精確數字無關)**:方案 A **結構性地犧牲串流「快首 token」核心優勢** —— 每個 query 首 token 前都必等一次 grade call。這正是 CRAG 當初被定為 non-stream-only 的原因;方案 A 只把張力從 mid-stream 搬到 pre-stream,首 token 代價依然存在。
- **建議**:方向先傾向**方案 B**(串流後 verify,保即時感)或 **方案 C**(定調為 Tier 1 已知取捨);方案 A 需 ADR 明確接受首 token trade-off + 精確實測(follow-up,需起 backend)證成。
- 方向仍待用戶 + ADR 定(屬 H1)。實測 follow-up 步驟見 spike 文檔 §6。

### 6.1 方案 B 實作(純後端信號)— 2026-07-07 landed(ADR-0073 Accepted)

- `backend/api/server.py` — lifespan 暴露 `app.state.crag_grader = crag_grader`(沿用 `CragLoop` 內部同一 grader,不新增 client,H2 clean)。
- `backend/api/routes/query.py`:
  - 新 helper `_verify_stream_retrieval_confidence(grader, query, chunks, threshold, kb_id)` — grade 已檢索 chunks → confidence;低信心(< `crag_confidence_threshold` 0.70)emit `stream_low_retrieval_confidence` warning + metric;grader None / grade 失敗 → 回 None(graceful,verify 是 advisory 絕不影響已串出的回應)。
  - `/query/stream` event_serializer:done frame 發送前,`enable_crag` gate 下 grade `result.chunks`(與非串流 CRAG 同一組),把 `retrieval_confidence` 注入 done frame。**不 re-synth / rewrite / re-retrieve → 不影響首 token**;前端本期不消費 → 零 H7。
- `backend/tests/api/test_query_stream_verify.py` — 4 test(grader None / 高信心無告警 / 低信心告警 / grade 失敗 graceful),全綠(`4 passed`)。
- **驗證**:4 新 test passed;`ruff format` clean;新增 code `mypy` clean。pre-existing debt(surgical 不碰,屬 BACKLOG B-20):server.py 30 個 E402(`truststore.inject` 必須先於 ssl import 的既有 pattern,非本改動引入)+ query.py 4 個 mypy(event_serializer 無 return annotation 等,均非本改動行 / 未改其簽名)。
- **architecture.md inline-tag amendment 作 follow-up**(ADR-0073 §H1 範圍:`crag.py:23` docstring 的「§3.5」CRAG section ref 待乾淨環境核實正確位置;ADR 已權威記錄本決定)。

## 7. Changelog

| 日期 | 動作 | 決定人 |
|---|---|---|
| 2026-07-06 | 立案(pipeline review Q-R2 → CH-022,`status: proposed`,範圍較大可能先 spike,未動 code) | pipeline review / 待用戶 approve |
| 2026-07-07 | 零成本結構性 spike 完成(方案 A latency 量級估算 + 三方案評估)→ 傾向 B/C,方案 A 需 ADR + 實測證成;spike 文檔 `docs/09-analysis/ch022_streaming_crag_latency_spike_20260707.md`。`status` 維持 `proposed`(方向待用戶定) | Claude / 待用戶定方向 |
| 2026-07-07 | 用戶選 **方案 B(串流後 verify)** → spec §2 更新為方案 B 具體設計(呈現方式暫定純後端信號〔選項 1〕,待確認)。**屬 H1,落 code 前需 ADR + Chris approve**,未動 code。`status` 維持 `proposed` | 用戶定方向 / Claude |
| 2026-07-07 | 用戶確認呈現方式 = 純後端信號(選項 1)+ approve write ADR → 起草 **ADR-0073**,用戶作 decision owner 拍板 **Accepted** + ADR README index | 用戶 approve / Claude |
| 2026-07-07 | 落 code(方案 B 純後端信號:server.py 暴露 grader + query.py `_verify_stream_retrieval_confidence` helper + done frame `retrieval_confidence` 注入)+ 4 新 test 綠 + ruff/mypy(新增 clean,pre-existing 屬 B-20)。architecture.md amendment 作 follow-up → `status: done` | Claude |

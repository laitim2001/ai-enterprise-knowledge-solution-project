---
id: CH-020
title: Cohere reranker 故障時 runtime 熱切換 Azure semantic ranker(免 redeploy)
status: done            # 2026-07-08 用戶授權 approve + ADR → ADR-0074 Accepted + FallbackReranker 落地 + 9 新 test 綠(選項 A 自動熱降級)
created: 2026-07-06
requester: pipeline review(`docs/09-analysis/pipeline_review_20260706.md` Q-R3,代碼核對)
backlog: B-15
related: ADR-0074(本 change 落地決策)/ ADR-0012(Cohere v4.0-pro 鎖定)/ ADR-0039(hybrid semantic ranker toggle,Proposed)
---

# CH-020 — Cohere reranker 熱切換 fallback

## 1. 背景

`docs/architecture.md §7.3` E7(`:1296`)+ R6(`:1342`)承諾「Cohere outage → hot fallback Azure built-in semantic ranker,config flag 切換,backend 唔需 redeploy」。**實作與 spec 有落差**:reranker 在 `server.py:225` lifespan **一次性選定**;live Cohere 5xx 經 tenacity 3× 重試(`cohere.py:83`,`reraise=True`)後直接冒泡 → `execute_query_pipeline` except → **502**(`query.py:432`)。要切 Azure semantic ranker 必須改 `reranker_kind` **並重啟**,非 spec 承諾的免 redeploy 熱切換。

→ 可用性風險:Cohere 短暫故障期間查詢直接 502,而非降級續行。

## 2. 行為規格(等 approve)

- Cohere rerank 呼叫重試耗盡(5xx / timeout)後,**runtime fallback 到 Azure built-in semantic ranker**,而非拋 502。
- fallback 由 config flag 控制(預設行為與觸發條件待確認:自動 fallback vs 需手動 flag)。
- fallback 生效時記 warning / metric(可觀測,對齊 review Q-R8「靜默退化需指標化」的方向)。
- Cohere 恢復後自動回主路徑(下一 query 重新嘗試 Cohere)。

## 3. 唔做(out of scope)

- 不改 Cohere 為主 reranker 的既定選擇(ADR-0012 lock 不動)。
- 不改 rerank 演算法 / 分數邏輯。
- semantic ranker 冗餘 default flip = 另一項(B-18 / ADR-0039),不在此。

## 4. 邊界 / 待確認

- Azure semantic ranker 路徑仍須可用(Free-tier 有 1000/月上限 → fallback 亦可能撞 402;production Standard S1 不受此限)。
- 「自動 fallback」vs「需 flag 手動切」需用戶定;spec E7/R6 語意傾向 config flag 熱切。
- 屬 H1-adjacent(改 §3.1 檢索行為 fallback 路徑)—— approve 時確認是否需 ADR 或作 spec-drift 收斂。

## 5. 驗證(等 approve 後據此驗)

- 模擬 Cohere outage(mock 5xx),查詢**自動降級 Azure semantic 續行**、不 502;結果有合理 rerank。
- Cohere 正常時主路徑不變(無 regression)。
- fallback 事件有 warning / metric。

## 6. 實作記錄

**方案**:選項 A —— 自動熱降級(per ADR-0074)。決策點「自動 fallback vs 手動 flag」揀自動:最對齊 §7.3 E7「outage → fallback」+ §8.3 R6「hot fallback」,可用性最高,且比「兩者結合」少 code(Karpathy §1.2)。

**Code 改動**:
- `backend/retrieval/reranker/fallback.py`(新)— `FallbackReranker`:透明 composite,實作 `Reranker` Protocol + `__aenter__`/`__aexit__`(同時管理 primary + fallback client lifecycle)。`rerank()` 先呼叫 primary,任何 exception → 若 `enabled` → emit warning `reranker_fallback_activated` + 改用 fallback 續行;`enabled=False` 或 fallback 自己失敗 → 冒泡(保留 pre-ADR-0074 行為)。空 candidates 短路回 `[]`。
- `backend/retrieval/reranker/factory.py` — `kind="cohere"` 分支:`reranker_fallback_enabled=True` **且** Azure Search endpoint+key 可用時,回 `FallbackReranker(CohereReranker, AzureSemanticReranker)`;否則回純 `CohereReranker`(零回歸)。
- `backend/storage/settings.py` — 加 `reranker_fallback_enabled: bool = True`(對齊 R6「config flag 切換」;`False` = escape hatch 保留舊行為)。
- **`server.py` lifespan + `RetrievalEngine.retrieve()` 零改動**(wrapper 對兩者透明)。

**Test**:
- `backend/tests/test_reranker_fallback.py`(新,9 test)— FallbackReranker 6 行為(primary 成功 / primary 錯降級 / disabled 冒泡 / 雙失敗冒泡 / 空 candidates 短路 / aenter+aexit 管理兩者)+ factory 3 dispatch(包 wrapper / flag 關不包 / Azure creds 缺不包)。
- 修既有 2 個 cohere-dispatch test(`test_reranker.py` + `test_reranker_shootout.py`)加 `reranker_fallback_enabled=False` 隔離 —— 測試環境 .env 有 Azure creds,否則新 wrapper 會令佢哋回 FallbackReranker(我改動製造,自己清理)。

**驗證**:`pytest`(reranker + health + eval)**51 passed / 0 failed**;`ruff check` + `ruff format` clean;`mypy --explicit-package-bases`(fallback/factory/settings)零 error。

**生效需重啟 backend**(`reload=False`)—— running backend pick up 新 factory 後,`reranker_kind=cohere` + Azure creds 齊 → reranker 自動變 `FallbackReranker`。

**明確不做**(per ADR-0074 Alternatives):選項 C 手動覆寫(既有 `reranker_kind` 已提供)/ 終極降級 hybrid-only(fallback 失敗仍冒泡,dev Free-tier 402 邊界已記錄,production S1 不受限)。

## 7. Changelog

| 日期 | 動作 | 決定人 |
|---|---|---|
| 2026-07-06 | 立案(pipeline review Q-R3 → CH-020,`status: proposed`,未動 code) | pipeline review / 待用戶 approve |
| 2026-07-08 | 用戶授權「approve + ADR」→ ADR-0074 Accepted(選項 A 自動熱降級)+ `FallbackReranker` 落地 + 9 新 test 綠 + 2 既有 test 隔離修 + ruff/mypy clean → `status: done` | 用戶 approve / Claude |

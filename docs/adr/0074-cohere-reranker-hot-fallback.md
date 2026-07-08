# ADR-0074: Cohere reranker 故障時 runtime 熱切換 Azure semantic ranker(免 redeploy)

**Date**: 2026-07-08
**Status**: Accepted
**Approver**: Chris(decision owner;用戶 2026-07-08 授權「先執行 ch-020, approve + ADR」)

## Context

`architecture.md §7.3 E7`(`:1296`)承諾「Cohere outage → Fallback Azure built-in semantic ranker」,`§8.3 R6`(`:1342`)進一步寫明「Hot fallback:Azure built-in semantic ranker」+「Config flag 切換,backend 唔需 redeploy」。

**實作與此承諾有落差**(2026-07-06 pipeline review Q-R3 代碼核對 → CH-020 立案):

- reranker 在 `server.py:225-227` lifespan **一次性選定**(`make_reranker(settings)` 按 `reranker_kind` 揀一個,`await __aenter__()` 常開 client)。
- live Cohere 5xx / timeout 經 tenacity 3× 重試(`reranker/cohere.py:83`,`reraise=True`)後直接冒泡 → 上層 `except` → **502**。
- 要切 Azure semantic ranker 必須改 `reranker_kind` **並重啟** backend,並非 spec 承諾的免 redeploy 熱切換。

→ 可用性風險:Cohere 短暫故障期間查詢直接 502,而非降級續行。

**零件其實齊全**:`AzureSemanticReranker`(`reranker/azure_semantic.py`)早在 W4 D3 reranker shootout 已實作,與 `CohereReranker` 同實作 `Reranker` Protocol(`rerank(query, candidates, top_k)`),且重用既有 Azure AI Search S1 SKU(**無額外採購**)。缺的只是「primary 失敗 → 降級 secondary」的組合機制。

本 ADR 屬 **H1**(改 `§3.1` 檢索行為的 fallback 路徑;vendor/service 降級行為),非新 vendor(Cohere + Azure semantic 都已 lock 在 `§3.2`),非新 dependency。

## Decision

新增一個**透明的 composite reranker** `FallbackReranker`(實作 `Reranker` Protocol),持有 primary(Cohere)+ fallback(Azure semantic),採**選項 A —— 自動熱降級**:

1. **自動降級**:`FallbackReranker.rerank()` 先呼叫 primary;primary 任何失敗(retry 耗盡後冒泡的 `httpx` 錯誤或其他 exception)→ 自動改用 fallback 續行,**不再 502**。
2. **Config flag 控制**:新增 `settings.reranker_fallback_enabled: bool = True`(對齊 R6「config flag 切換」)。`False` 時保持現狀(primary 失敗直接冒泡),`True` 時啟用自動降級。
3. **自動回主路徑**:Cohere 恢復後,下一 query 重新呼叫 primary(無狀態黏著;FallbackReranker 每次 rerank 都由 primary 起步)。
4. **可觀測性**:降級生效時 emit `structlog` warning `reranker_fallback_activated`(含 primary / fallback 類型 + 錯誤 + candidate 數),對齊 pipeline review Q-R8「靜默退化需指標化」方向(同 CH-021 風格)。
5. **透明包裝**:`make_reranker(settings)` 在 `reranker_kind="cohere"` **且** `reranker_fallback_enabled=True` **且** Azure Search endpoint+key 可用時,返回 `FallbackReranker(CohereReranker, AzureSemanticReranker)`;否則返回原本的單一 reranker(零回歸)。`FallbackReranker.__aenter__/__aexit__` 同時管理 primary + fallback 的 client lifecycle → **`server.py` lifespan 與 `RetrievalEngine.retrieve()` 完全零改動**。

**觸發判定**:primary 拋 exception 才降級;primary 正常返回(含空結果)不降級。

## Alternatives Considered

- **選項 B — 純手動 flag 切換**:保持 Cohere 5xx 直接 502,運維察覺 outage 後手動改 `reranker_kind=azure`(免 redeploy live reload)。**Reject**:對齊 R6「config flag」字面,但故障期間到 flip 之前仍 502,不算真正 hot fallback(E7「outage → fallback」語意是自動),且加運維負擔。
- **選項 C — 自動降級 + 保留手動覆寫**:選項 A 為預設 + 保留手動 `reranker_kind` 強制切換。**Reject(暫)**:手動覆寫其實已由既有 `reranker_kind` config 提供(改 config + 重啟即可),自動降級才是缺口。選項 A 已滿足 E7/R6;選項 C 多的 code / 測試面不值(Karpathy §1.2 simplicity-first)。將來若需 live 免重啟手動切,另立。
- **在 `retrieve()` 呼叫點加 try/except**(非 wrapper):**Reject**。會令 `RetrievalEngine` 持有兩個 reranker + 兩套 lifecycle,污染 engine 職責;wrapper 對 engine 透明,更 surgical。
- **終極降級到 hybrid-only(fallback 也失敗時返回原始 hits 不 rerank)**:**不在本 ADR 做**。fallback(Azure)本身失敗(如 dev Free-tier 撞 1000/月 402 上限)時,`FallbackReranker` re-raise 保持現有冒泡行為。production Standard S1 無此限,雙重失敗機率極低;為此改 `retrieve()` graceful degrade 屬另一項 robustness 工作,避免擴大 scope。

## Consequences

- **Positive**:Cohere 短暫故障不再令查詢 502,自動降級 Azure semantic 續行,對齊 `§7.3 E7` + `§8.3 R6` 既有承諾;flag 可整體開關;對 `server.py` / `retrieve()` 零改動(透明 wrapper);可觀測(warning event)。
- **Negative**:降級期間 rerank 品質由 Azure semantic 提供(與 Cohere v4.0-pro 有差異,但 W4 D3 shootout 證 Azure 在可接受範圍);dev Free-tier 環境 fallback 自己可能撞 402 → 雙重失敗仍冒泡(已記錄,production S1 不受此限)。
- **Neutral**:`reranker_kind != "cohere"`(如 `azure` / `off`)時完全不包 wrapper,行為 byte-identical;`reranker_fallback_enabled=False` 保留現狀作 escape hatch。不改 `architecture.md` frozen 內容(§7.3 E7 + §8.3 R6 本已承諾 fallback,本 ADR 是實作補齊,非 spec 變更)。

## References

- `architecture.md §7.3 E7`(Cohere outage → fallback)+ `§8.3 R6`(hot fallback + config flag)
- `docs/03-implementation/changes/CH-020-cohere-reranker-hot-fallback/spec.md`
- `docs/09-analysis/pipeline_review_20260706.md` Q-R3(可用性風險)+ Q-R8(靜默退化指標化)
- ADR-0012(Cohere v3.5 → v4.0-pro production lock — 主 reranker 選擇不動)
- ADR-0039(hybrid `use_semantic_ranker` toggle — 檢索層 semantic,與本 ADR 的 rerank 層 fallback 為兩個不同 surface)
- CH-021(ingest ACL fail-open 告警 — 可觀測性風格 precedent)

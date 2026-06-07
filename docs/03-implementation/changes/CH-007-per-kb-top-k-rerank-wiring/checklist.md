---
change_id: CH-007
spec_ref: ./spec.md
status: done            # in-progress | done
last_updated: 2026-06-07
---

# CH-007 — Checklist

> Atomic items derived from `spec.md` §3 acceptance criteria。AI tick 完成 item;唔可以 tick 嘅喺 progress Day-N 寫原因。
> Scope = 兩個都接入(`default_rerank_k` + `default_top_k`,Chris approve 2026-06-07)。

## Implementation — Backend (C02 schema/config + C04 engine/pipeline)

- [x] I1 `QueryRequest.top_k_retrieval` / `top_k_rerank` → `int | None = None`(schemas/query.py;消歧義 None=用 KB/全域預設、明確值=per-query override)
- [x] I2 `PerQueryOverrides` + `EffectiveConfig` 加 `default_top_k` / `default_rerank_k`(effective_config.py)
- [x] I3 `resolve_effective_config` resolve 兩旋鈕(per-query > per-KB `KbConfig.default_*` > 全域 `settings.hybrid_top_k_retrieval`/`rerank_top_k`)
- [x] I4 `RetrievalEngine.retrieve` 加 additive `overfetch: int | None = None`(None=`self._hybrid_overfetch`,零行為改變);`fetch_k = max(top_k, overfetch ?? self._hybrid_overfetch)`
- [x] I5 `retrieval.result_fusion.fused_retrieve` 同步加 `overfetch` 透傳
- [x] I6 `query.py`:`_resolve_effective_config` 加 `per_query` 參數 + helper `_per_query_from_payload`;`query()` + `query_stream()` 由 payload top_k 砌 `PerQueryOverrides` resolve 入 `effective`
- [x] I7 `query.py`:`execute_query_pipeline`(fused + retrieve)+ `query_stream` 三處改讀 `effective.default_rerank_k`(取代 `payload.top_k_rerank`)+ 傳 `overfetch=effective.default_top_k`。CRAG `refine` 的 `_expanded_top_k=20` 屬刻意獨立旋鈕,不郁(scope 註)

## Tests (H6 — query pipeline 強制覆蓋)

- [x] T1 `QueryRequest` top_k Optional 由 route test explicit-override 路徑覆蓋(`test_ch007_explicit_per_query_top_k_overrides_per_kb`)
- [x] T2 `EffectiveConfig` 帶 `default_top_k`/`default_rerank_k` + resolve 次序三層(per-query > per-KB > 全域)— `test_effective_config.py` +3 CH-007 test + global-inherit assert
- [x] T3 `execute_query_pipeline` 用 `effective.default_rerank_k`(`_RecordingEngine` record top_k + overfetch,assert = KB 值)
- [x] T4 `/query` + `/query/stream` 兩路皆生效(`test_ch007_query_*` + `test_ch007_query_stream_*`)
- [x] T5 Non-regression:explicit top_k override(top_k=3/overfetch=12)+ default KB(5/50 bit-identical);`test_multi_kb_routing` 不破
- [x] T6 engine `overfetch` kwarg:None=既有 fetch_k(50)、明確值(80)=改 fetch_k(`test_ch007_overfetch_override_sizes_candidate_pool`)

## Verification

- [x] V1 backend pytest **113 passed**(effective_config + query_per_kb_config + retrieval + multi_kb_routing + result_fusion + api_skeleton + config_test_route + observe_query_route + e1_e5_e12_smoke + answer_detail_ch006)— 0 fail;含恢復 CH-006 incomplete-landing 4 檔
- [x] V2 ruff check clean(8 檔);mypy --strict:query.py schema + effective_config.py clean(`Success: no issues`);retrieval_engine/result_fusion/query route 用 `--explicit-package-bases` clean(per-file 無 explicit-base 撞 `backend/__init__.py` dual-naming = invocation artifact 非 type error)
- [x] V3 Live 驗 **PASS**(2026-06-07,backend restart 載入新 code,KB `w56-drive-ab-1` 415 chunks,`default_rerank_k=11`,mode=vector,enable_crag=false,零 KB mutation):Test A 無 top_k → `retrieved_chunks=11`(= KB default,舊 code 硬寫 5 → 證 per-KB 生效);Test B `top_k_rerank=3` → `retrieved_chunks=3`(證 explicit override 壓過 KB default);reranker=cohere-v4.0-pro 兩者一致

## Cross-Cutting

- [ ] X1 commits 對應 progress Day-N(F0 kickoff / backend+test / closeout)+ component tag(retrieval)— 待用戶 go commit
- [x] X2 非 architectural → **無 ADR**(R5 recheck:無 §3/§4 component 增刪、無 vendor swap、無 storage layout 改;schema 消歧義 + resolver 延伸 + 接線)
- [x] X3 C04-retrieval.md + C02-kb-manager.md design note bump(CH-007 amendment + last_updated)
- [x] X4 progress closeout summary + frontmatter status → closed(V3 live PASS)
- [x] X5 doc-sync:architecture.md §4.5 schema drift note 記入 progress(frozen §1-14 不動);ROADMAP entry(若存在)

---

**Lifecycle reminder**:新加 item 必須先入 spec §2/§3 + changelog,再加 checklist。

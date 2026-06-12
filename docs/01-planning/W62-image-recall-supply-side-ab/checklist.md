# W62 — checklist(供給側 A/B)

> 對應 plan.md F1–F5(+ R3 加 E/F 臂)。逐項 tick,daily 對應 progress.md Day-N entry。

## F1 — pre-flight + baseline 確立

- [x] pre-flight:Docker(ekp-postgres + langfuse endpoint 200)+ azurite(port 10000)+ backend `/health`
- [x] 確認無另一 Claude session 在動 backend(殺 W61 遺留 PID 32132/44344,start=06-11)
- [x] 重啟 backend(venv python;env = `SYNTHESIZER_REQUEST_TIMEOUT_S=180` + `HYBRID_USE_SEMANTIC_RANKER=false`,**無** window env)
- [x] `GET /kb/drive-images-1` 記錄**全份 per-KB config 原值**落 progress.md(F4 復原依據)
- [x] 確認 KB 無 re-index(`last_indexed_at=2026-06-08`,6 docs / 369 chunks)→ A 臂複用 W61 cap60_r1/r2 合法(R5)
- [x] PATCH cap `max_images_per_answer` 20→60(full replacement)+ GET readback = 60

## F2 — B 臂(rerank 軸)

- [x] PATCH `default_rerank_k` 5→10 + GET readback = 10(其餘欄位不變)
- [x] 單條 probe(Q002)200 OK 後跑 run 1(9/9)→ `reports/image_recall_ar_supply_rerank10_r1.yaml`
- [x] run 2 → `..._r2.yaml`(判決:供給零推高)

## F3 — C 臂(window 軸)+ D 臂(combo)

- [x] PATCH `default_rerank_k` 復原 5 + readback
- [x] AC2 gate ①:offline `get_settings().citation_neighbour_window` 喺 env 下回 8
- [x] AC2 gate ②:同 shell 同 env(`CITATION_NEIGHBOUR_WINDOW=8`)重啟 backend → healthy
- [x] C 臂 run 1 + run 2 → `reports/image_recall_ar_supply_win8_r{1,2}.yaml`(r2 Q005/Q006 撞 transient 502,7/9,cap-bound 軸完整)
- [x] PATCH `default_rerank_k`=10 + `citation_neighbour_max_aux_images`=40 + readback(window env 持續)
- [x] D 臂 run 1 + run 2 → `reports/image_recall_ar_supply_combo_r{1,2}.yaml`(**突破 0.890/0.904**)

## F3b — E/F 臂(R3 deviation,拆解 combo)

- [x] F4 先行復原 + 重啟除 window env(E/F 臂前提 = window=3 default)
- [x] E 臂:PATCH cap=60 + rerank=10 + max_aux=40 + readback → run ×2 → `..._perkb_r{1,2}.yaml`(0.889×2 ≈ D → window 多餘)
- [x] F 臂:PATCH rerank=5(max_aux=40 留)+ readback → run ×2 → `..._maxaux40_r{1,2}.yaml`(cap-bound ≈ E → max_aux 係供給核心;Q005 0/0 → rerank=10 = 穩定性項)

## F4 — 完全復原

- [x] PATCH 寫回 F1 原值(cap=20 / rerank=5 / max_aux=18 / 其餘欄位)+ GET readback 逐欄位對(**兩次**:D 臂後 + F 臂後最終)
- [x] 重啟 backend **無** window env
- [x] progress.md 記 RESTORE PASS

## F5 — 分析 + 判決 + doc-sync

- [x] returned_count × recall × precision 三軸對比表(A–F 六臂,cap-bound 5 條 + 對照 3 條 + Q005)
- [x] 判決:max_aux=18 係供給 binding 項(18→40 = 突破);rerank=10 = section 覆蓋穩定性;window 多餘;precision 零代價(AC3/AC4)
- [x] rollup `CONFIG_PLATFORM_W43-W58_ROLLUP.md` §4.5/§4.6 doc-sync(供給側實數)
- [x] plan.md changelog 補 closeout 行 + status → closed
- [x] progress.md retro

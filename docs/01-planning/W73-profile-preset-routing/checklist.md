# W73 — profile→preset routing checklist

> Atomic items per `plan.md` §2。`[ ]`→`[x]`,唔可刪未勾項。

## F1 — profiler 接入 ingest(compute,無 side-effect)

- [x] `IngestionResult` 加 `profile: ProfileResult | None`(default None)
- [x] `orchestrator.ingest()` parse 成功後 compute profile(module singleton `_PROFILER`)
- [x] best-effort:profile 計算 try/except,失敗 → None,**唔 abort ingest**
- [x] 現有 orchestrator test 全綠(IngestionResult 加 field 唔 break)
- [x] mypy 0 + ruff 0(W73 code clean;`_engine_or_503` error = pre-existing,git 核冇 touch)

## F2 — PROFILE_PRESETS + 保守 auto-write routing

- [x] `backend/ingestion/profile_presets.py`:`PROFILE_PRESETS: dict[DocProfile, DocConfig | None]` + `preset_for(profile)`(return copy 防 share singleton)
- [x] preset 值對齊 plan §1 proposal(P1_sop_imgdense=drive-images-1 good config / 其他 D1+保守 / too_small·unknown=None)
- [x] `_run_ingest_pipeline` routing:profile=None/too_small/unknown → skip;preset=None → skip
- [x] D6 守:`doc_config_store.get` 已有 → skip(唔覆蓋 manual)
- [x] auto-write:`doc_config_store.upsert(kb_id, doc_id, preset)`(`_route_profile_preset` helper)
- [x] log routing 決定(`profile_routing_applied` / `_skip_manual`)
- [x] mypy 0 + ruff 0

## F3 — test(H6)

- [x] orchestrator profile compute(`test_ingest_computes_profile` — IngestionResult.profile 有值)
- [x] `PROFILE_PRESETS` 值正確(P1 對齊 good config + P2 neighbour off)
- [x] routing D6 守(已有 manual → skip,cap 不被覆蓋)
- [x] routing auto-write(冇 → upsert preset)
- [x] routing skip(too_small → 無寫入,inherit D7)
- [x] `_run_ingest_pipeline` routing — helper `_route_profile_preset` unit 直測 routing logic + reindex test 確認 wiring 唔 break(full HTTP E2E nice-to-have,best-effort wrap 不影響 ingest,未做)
- [x] pytest 綠(32 passed:test_profile_routing 7 + test_orchestrator + test_kb_reindex)

## F4 — 收爐

- [x] memory 更新(`project_per_kb_tunable_config_vision` + MEMORY.md index — routing 落地)
- [x] closeout retro(progress.md — PASS verdict + 教訓 + commits)
- [x] 段②c(D8 PDF picture)/ ②d(方案 A)/ ③(UI)交棒記錄
- [x] plan.md status → closed

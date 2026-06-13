# W73 — profile→preset routing checklist

> Atomic items per `plan.md` §2。`[ ]`→`[x]`,唔可刪未勾項。

## F1 — profiler 接入 ingest(compute,無 side-effect)

- [ ] `IngestionResult` 加 `profile: ProfileResult | None`(default None)
- [ ] `orchestrator.ingest()` parse 成功後 compute profile(module singleton `_PROFILER`)
- [ ] best-effort:profile 計算 try/except,失敗 → None,**唔 abort ingest**
- [ ] 現有 orchestrator test 全綠(IngestionResult 加 field 唔 break)
- [ ] mypy 0 + ruff 0

## F2 — PROFILE_PRESETS + 保守 auto-write routing

- [ ] `backend/ingestion/profile_presets.py`:`PROFILE_PRESETS: dict[DocProfile, DocConfig | None]` + `preset_for(profile)`
- [ ] preset 值對齊 plan §1 proposal(P1_sop_imgdense=drive-images-1 good config / 其他 D1+保守 / too_small·unknown=None)
- [ ] `_run_ingest_pipeline` routing:profile=None/too_small/unknown → skip;preset=None → skip
- [ ] D6 守:`doc_config_store.get` 已有 → skip(唔覆蓋 manual)
- [ ] auto-write:`doc_config_store.upsert(kb_id, doc_id, preset)`
- [ ] log routing 決定(套 preset / skip 原因)
- [ ] mypy 0 + ruff 0

## F3 — test(H6)

- [ ] orchestrator profile compute(IngestionResult.profile 有值 / best-effort fail → None)
- [ ] `PROFILE_PRESETS` 值正確(P1 對齊 good config)
- [ ] routing D6 守(已有 manual → skip)
- [ ] routing auto-write(冇 → upsert preset)
- [ ] routing skip(profile None/too_small/unknown → 無寫入)
- [ ] `_run_ingest_pipeline` routing integration
- [ ] pytest 綠 + coverage

## F4 — 收爐

- [ ] memory 更新(routing 落地)
- [ ] closeout retro
- [ ] 段②c(D8 PDF picture)/ ②d(方案 A)交棒記錄
- [ ] plan.md status → closed

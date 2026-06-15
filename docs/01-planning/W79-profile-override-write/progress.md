# W79 progress — Profile 人手覆寫 write surface(ADR-0058)

## Day 1 — 2026-06-15(kickoff)

**Context**:W78 落地 profiling frontend 三層 UI(L3 override select static)。用戶 2026-06-15 揀 write surface
scope = ① Profile override(② threshold persist 不做 — threshold 五輪實證已最佳,改門檻 risk>reward)。

**ADR-0058 Accepted**(本 session):override 機制 = 套 `preset_for(profile)` 落 per-doc config(reuse ADR-0050
`doc_config_store`)+ `DocProfileInfo` 加 `manual_override` annotation(保 W76 read-only system fact 分層 +
可解釋)+ D6 守 reuse W73。Alternatives:A 改 system profile field(reject — 破壞分層失可解釋)/ B 純套 preset
唔記 label(reject — UI 唔反映 override)/ C(採用)套 preset + annotation。

**落點 ground(plan kickoff)**:
- profile persist + route preset 喺 `_run_ingest_pipeline`(documents.py:609,persist 813-821)+
  `_route_profile_preset`(834-866,D6 守 skip-if-manual)
- doc config CRUD 喺 `doc_config.py`(separate route);override 套 preset **唔用** `_route_profile_preset`
  (嗰個 D6 skip manual)→ explicit user action 直接 `preset_for` + `doc_config_store.upsert` 覆蓋
- `DocProfileStore`(W76)profile JSONB 存全 `DocProfileInfo` → 加 field 自動 serialize;舊 row deserialize
  `DocProfileInfo(**row)` 無 `manual_override` key → default null(向後相容)

**設計決定**:
- L2 summary.profile = effective(`manual_override ?? profile`,backend resolve);L3 detail 透明見 system auto
  + human override(可解釋)
- override 套 preset = **覆蓋** per-doc config(per D3「套 preset」非 merge);user 可之後 L3 fine-tune

**紀律自檢**:H1 ✅(ADR-0058 Accepted)/ H2 ✅(零新 dep)/ H4 ✅(層 A)/ H6 ✅(F1.5 route test)/ H7 ✅
(override select static → functional,視覺不變)/ Karpathy ✅(reuse preset_for/doc_config_store/W73 守)。

**Plan 落地**:W79 folder + plan.md(active)+ checklist.md(F1-F3)+ progress.md + ADR-0058。

**Commits**:
- (本次)docs(planning): W79 kickoff + ADR-0058 — profile override write surface

# W76 checklist — profile read surface

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — DocProfileStore + API schema

- [ ] F1.1 `api/schemas/doc_profile.py`:`DocProfileSignals`(13 signal field mirror ProfileSignals)+ `DocProfileInfo`(profile / confidence / fallback_applied / signals / profiled_at)+ `from_result()` classmethod
- [ ] F1.2 `kb_management/doc_profile_store.py`:`DocProfileStore` Protocol(get / upsert / delete / list_for_kb)
- [ ] F1.3 `InMemoryDocProfileStore`(nested dict,mirror InMemoryDocConfigStore)
- [ ] F1.4 `PostgresDocProfileStore`(table `document_profiles`,lazy psycopg,CREATE TABLE IF NOT EXISTS)
- [ ] F1.5 `make_doc_profile_store(settings)` factory(database_url 有 → Postgres,else in-memory)
- [ ] F1.6 mypy strict 0 + ruff 0

## F2 — ingest 時 persist(advisory)

- [ ] F2.1 deps wire:`make_doc_profile_store` 接入 app deps(mirror doc_config_store)
- [ ] F2.2 `_run_ingest_pipeline`:`result.profile` 非 None → `doc_profile_store.upsert`(best-effort try/except,唔 fail ingest)
- [ ] F2.3 advisory:store raise → log + 繼續(mirror W73 `profile_routing_failed`)
- [ ] F2.4 mypy strict 0 + ruff 0

## F3 — expose via read API

- [ ] F3.1 `DocumentDetail.profile: DocProfileInfo | None`(完整 signals)
- [ ] F3.2 `DocumentSummary.profile: str | None` + `profile_confidence: float | None`(輕量)
- [ ] F3.3 documents route:detail 讀單 doc profile join;list 讀 `list_for_kb` map
- [ ] F3.4 profile 缺 → null(既有 field bit-identical,純 additive)
- [ ] F3.5 mypy strict 0 + ruff 0

## F4 — test(H6)

- [ ] F4.1 store CRUD test(in-memory):get / upsert / delete / list_for_kb + None fallback
- [ ] F4.2 ingest persist test:profile 非 None → store row;None → 無 row;advisory(store raise 唔 fail)
- [ ] F4.3 API join test:detail / list 有 profile 返值;缺 → null
- [ ] F4.4 pytest 綠 + mypy strict 0 + ruff 0

## F5 — closeout

- [ ] F5.1 verify:新 upload → ingest 自動 profile + persist → GET DocumentDetail 見 profile(end-to-end;infra 受限退 unit-level)
- [ ] F5.2 R5 評估:是否補 ADR-0056 addendum note(段③前置 persist)
- [ ] F5.3 memory append + MEMORY.md pointer + plan closed + progress retro

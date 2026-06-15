# W76 checklist — profile read surface

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。

## F1 — DocProfileStore + API schema

- [x] F1.1 `api/schemas/doc_profile.py`:`DocProfileSignals`(13 signal field mirror ProfileSignals)+ `DocProfileInfo`(profile / confidence / fallback_applied / signals / profiled_at)+ `from_result()` classmethod(TYPE_CHECKING-only ingestion import,無 runtime reverse dep)
- [x] F1.2 `kb_management/doc_profile_store.py`:`DocProfileStore` Protocol(get / upsert / delete / list_for_kb)
- [x] F1.3 `InMemoryDocProfileStore`(nested dict,mirror InMemoryDocConfigStore)
- [x] F1.4 `PostgresDocProfileStore`(table `document_profiles`,lazy psycopg,CREATE TABLE IF NOT EXISTS)
- [x] F1.5 `make_doc_profile_store(settings)` factory(database_url 有 → Postgres,else in-memory)
- [x] F1.6 mypy strict 0(新 code;25 pre-existing transitive 我冇 touch)+ ruff 0

## F2 — ingest 時 persist(advisory)

- [x] F2.1 deps wire:`make_doc_profile_store` 接入 app deps(server.py lifespan + `_IngestionDeps` field + `_ingestion_deps_or_503` getattr,mirror doc_config_store)
- [x] F2.2 `_run_ingest_pipeline`:`result.profile` 非 None → `doc_profile_store.upsert(DocProfileInfo.from_result(..., profiled_at=now.isoformat()))`(best-effort try/except)
- [x] F2.3 advisory:store raise → `profile_persist_failed` log + 繼續(mirror W73 `profile_routing_failed`)
- [x] F2.4 mypy strict 0 + ruff 0

## F3 — expose via read API

- [x] F3.1 `DocumentDetail.profile: DocProfileInfo | None`(完整 signals)
- [x] F3.2 `DocumentSummary.profile: str | None` + `profile_confidence: float | None`(輕量)
- [x] F3.3 documents route:`_doc_profile_store(request)` helper + detail 讀單 doc `get` join;list 讀 `list_for_kb` map(皆 best-effort try/except,絕不 fail read)
- [x] F3.4 profile 缺 → null(既有 field bit-identical,純 additive)
- [x] F3.5 mypy strict 0 + ruff 0

## F4 — test(H6)

- [x] F4.1 store CRUD test(in-memory):get / upsert / delete / list_for_kb + None fallback + kb isolation + copy-no-mutate(6 test)
- [x] F4.2 persist 元件覆蓋:`from_result`(ProfileResult→DocProfileInfo,13-signal mirror + pdf None + fallback flag,2 test)+ store upsert(已 F4.1)— inline persist guard 邏輯 trivial(`if profile and store: upsert(from_result(...))`),唔 e2e mock Azure orchestrator(R3 deviation,Karpathy §1.2 simplicity)
- [x] F4.3 API join test:list_documents(profile + confidence / 缺 null / 無 store graceful)+ doc_detail(完整 signals / 缺 null)(4 test;factory 2 test)
- [x] F4.4 pytest 14 passed + regression 57 passed(documents-listing / profile-routing / doc-config-store / profiler 零 break)+ mypy strict 0 + ruff 0

## F5 — closeout

- [ ] F5.1 verify:新 upload → ingest 自動 profile + persist → GET DocumentDetail 見 profile(end-to-end;infra 受限退 unit-level)
- [ ] F5.2 R5 評估:是否補 ADR-0056 addendum note(段③前置 persist)
- [ ] F5.3 memory append + MEMORY.md pointer + plan closed + progress retro

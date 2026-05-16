---
phase: W19-frontend-audit-and-adr-draft
deliverable: F2
plan_ref: ../plan.md
audit_ref: ./W19-mockup-jsx-audit.md
date: 2026-05-16
status: complete
---

# W19 F2 — Backend Gap Map

> Per `references/design-mockups/` Tier 1 route × backend endpoint dependency check vs `backend/api/routes/*.py` + Pydantic schemas in `backend/api/schemas/*.py`。
>
> Each surface gets one of:
> - **✅ supported** — real endpoint + matching schema
> - **🟡 partial** — endpoint exists,schema/feature gap
> - **🔴 missing** — no endpoint yet
> - **🟣 mock-only** — prototype mock data,no real backend planned for Tier 1
>
> **Wave block**:`Wave A` / `Wave B` / `Wave C` / `Tier 2`(per F4 plan §2.F4.1)

---

## §1 Backend endpoint inventory(current state)

Per `git grep "@router\.(get|post|patch|delete|put)" backend/api/routes/`:

### 1.1 Existing routes(13 route files,28 endpoints)

| Route file | Endpoints |
|---|---|
| `auth.py`(6) | `POST /auth/refresh` · `POST /auth/logout` · `POST /auth/register` · `POST /auth/verify-email` · `POST /auth/login` · `POST /auth/resend-verification` |
| `kb.py`(7) | `GET /kb` · `POST /kb` · `GET /kb/{kb_id}` · `DELETE /kb/{kb_id}` · `PATCH /kb/{kb_id}` · `PATCH /kb/{kb_id}/settings` · `POST /kb/{kb_id}/reindex` |
| `documents.py`(4) | `GET /kb/{kb_id}/documents` · `POST /kb/{kb_id}/documents` · `DELETE /kb/{kb_id}/documents/{doc_id}` · `POST /kb/{kb_id}/documents/{doc_id}/reindex` |
| `chunks.py`(2) | `GET /kb/{kb_id}/chunks` · `PATCH /kb/{kb_id}/chunks/{chunk_id}` |
| `query.py`(2) | `POST /query` · `POST /query/stream`(SSE) |
| `retrieval_test.py`(1) | `POST /kb/{kb_id}/retrieval-test`(per ADR-0021,mode + top_k + score_threshold + rerank toggle) |
| `eval.py`(2) | `POST /eval/run` · `POST /eval/shootout`(per W17 F3 RAGAs 4-metric integration) |
| `debug.py`(1) | `GET /debug/trace/{trace_id}`(per ADR-0020 + W16 F5.5) |
| `feedback.py`(1) | `POST /feedback`(per C06) |
| `observability.py`(2) | `GET /observability/cost-summary` · `GET /observability/alerts` |
| `screenshots.py`(1) | `GET /screenshots/{kb_id}/{doc_id}/{img_id}` |

### 1.2 Pydantic schemas(11 schema files,38 classes)

| Schema file | Classes |
|---|---|
| `auth.py`(11) | RefreshResponse · LogoutResponse · UserRegister/Login/VerifyEmail/ResendVerification Request · UserPublic · Register/VerifyEmail/Login/ResendVerification Response |
| `errors.py`(2) | ApiErrorBody · ApiErrorResponse |
| `eval.py`(4) | FailedQueryDetail · EvalReport · RerankerShootoutEntry · ShootoutReport |
| `feedback.py`(2) | FeedbackRequest · FeedbackResponse |
| `kb.py`(5) | KbConfig · KbCreate · KbMetadataPatch · FailureRecord · KbStatus |
| `listing.py`(2) | DocumentSummary · ChunkSummary |
| `observability.py`(6) | CostRow · RealtimeUsageRow · CostSummary · AlertRule · AlertsConfig · TraceStage · TraceDetail |
| `query.py`(5) | ImageRef · ChunkPreview · Citation · QueryRequest · QueryResponse |
| `retrieval_test.py`(3) | RetrievalTestRequest · RetrievalTestChunk · RetrievalTestResult |

### 1.3 NOT present(F2 missing surface)

| Missing endpoint group | Required by |
|---|---|
| `GET /health` per-component connectivity payload | `/dashboard` System health card(currently `{"status":"ok"}` liveness only per W18 retro)|
| `GET /queries/recent`(or similar query log) | `/dashboard` Recent queries card(Q6 OPEN)|
| `GET /eval/runs/latest`(cached eval run result)| `/dashboard` Latest eval card(currently empty-state CTA per W18 F4) |
| `GET /kb/{kb_id}/docs/{doc_id}` enriched(outline + parse/embed durations + image refs)| `/doc-detail/[kbId]/[docId]` 3-pane(only chunks list exists at `/kb/{kb_id}/chunks?doc_id=...`)|
| `GET /kb/{kb_id}/images`(image library)| `/kb/[id]` Images tab — image listing with SHA256 dedup + chunk refs |
| `POST /chunking-preview`(sample chunking strategy on a doc)| `/kb/[id]` Chunking Lab tab — strategy comparison + sample output |
| `/conversations` CRUD(Beta+) | `/chat` Conversation History sidebar(per C10 §7 — localStorage now,server-side Tier 2)|
| `/admin/connections/*`(provider CRUD + test + secret rotate via Key Vault) | `/settings` → Connections tab 9 providers |
| `/admin/identity/*`(Entra tenant + App registration + MSAL config CRUD) | `/settings` → Identity & Auth tab |
| `/admin/api-keys/*`(CRUD + per-key rate limit + usage telemetry) | `/settings` → API Keys & Quotas tab |
| `/users/*` + RBAC tables(roles / role_permissions / groups / group_members / audit_log + kb_acl) | `/users` Tier 1.5 NET NEW + `/kb/[id]` Access tab |
| `/notifications` feed | Topbar NotificationsMenu(currently inline mock in shell) |

---

## §2 Per-route gap map(14 Tier 1 routes)

### 2.1 Route × surface × endpoint table

| # | Route | Surface | Required endpoint | Status | Wave | Owner Cn | Evidence(`backend/`) |
|---|---|---|---|---|---|---|---|
| 1 | `/dashboard` | KB summary card | `GET /kb` → list[KbStatus] | ✅ supported | Wave A | C02 | `backend/api/routes/kb.py:48` + `schemas/kb.py:49` |
| | | Recent queries card | `GET /queries/recent` → list[RecentQuery] | 🔴 missing(Q6 OPEN) | Wave A blocked or empty-state CTA | C07 + new query-log table | none — Q6 governance(session-start §9) |
| | | Latest eval card | `GET /eval/runs/latest` → EvalReport(cached) | 🔴 missing | Wave A blocked or empty-state CTA | C06 + cache layer | `eval.py` has `POST /eval/run`(W17 F3)but no cached-result endpoint |
| | | System health card | `GET /health` per-component | 🟡 partial | Wave A backend gap | C07 + C08 | currently `{"status":"ok"}` liveness — needs per-component(Azure Search / OpenAI / Cohere / Langfuse / Postgres)connectivity payload |
| | | Cost projection / spend / alerts | `GET /observability/cost-summary` + `GET /observability/alerts` | ✅ supported | Wave A | C07 | `backend/api/routes/observability.py:46+109` + `schemas/observability.py:35` |
| | | Quick actions(4 buttons)| n/a — navigation only | ✅ supported | Wave A | C09 | client-side router |
| 2 | `/chat` | Streaming query(SSE) | `POST /query/stream` → SSE chunks | ✅ supported | Wave A | C04 + C05 | `backend/api/routes/query.py:175` + W3 D4 |
| | | Non-streaming query | `POST /query` → QueryResponse | ✅ supported | Wave A | C04 + C05 | `query.py:52` + `schemas/query.py:52` |
| | | Citation card + screenshot modal | response `QueryResponse.citations[].embedded_images[]` → `ImageRef.blob_url` | ✅ supported | Wave A | C05 + C12 | `schemas/query.py:8` ImageRef + `routes/screenshots.py:8` blob serve |
| | | Feedback widget(thumbs_up/down + comment) | `POST /feedback` → FeedbackResponse | ✅ supported | Wave A | C06 + C07 | `routes/feedback.py:27` + `schemas/feedback.py:8` |
| | | KB selector dropdown | `GET /kb` → list[KbStatus] | ✅ supported | Wave A | C02 | shared with `/dashboard` |
| | | **Conversation History sidebar(Beta+)** | `GET/POST/PATCH/DELETE /conversations` + `GET /conversations/{id}/messages` | 🔴 missing(Beta+) | **Wave A polish or Wave B** — localStorage Tier 1 OK,server-side Tier 2 | new C? Conversations Service | none — C10 §7 spec(Beta+ localStorage),server-side Tier 2 |
| | | CRAG strip(re-retrieve indicator)+ trace link | response `QueryResponse.trace_id` + `QueryResponse.crag_triggered` | 🟡 partial | Wave A | C05 | need to confirm `QueryResponse` includes `crag_triggered` flag + `crag_iterations` — grep `schemas/query.py:52` shows `QueryResponse` exists but field-level coverage TBD per Wave A audit |
| | | 3 citation placement modes(`tweaks.citationPlacement`) | frontend tweaks only | ✅ frontend-only | Wave A polish | C10 | n/a |
| 3 | `/kb` | KB list grid + table view | `GET /kb` → list[KbStatus] | ✅ supported | Wave A | C02 | `routes/kb.py:48` |
| 4 | `/kb/new` | Create KB + provision index | `POST /kb` body=KbCreate → KbStatus | ✅ supported | Wave A | C02 + C03 | `routes/kb.py:54` + `schemas/kb.py:17` KbCreate |
| | | Multimodal step config(extract_embedded_images / slide_screenshots / dedup_strategy / return_images_in_chat / Tier 2:captioning_model / render_pdf_pages / low_value_threshold / perceptual) | `KbCreate.config: KbConfig` — currently has chunk_strategy + embedding_model + default_top_k + default_rerank_k | 🟡 partial — `KbConfig` schema needs multimodal fields | Wave A | C01 + C02 | `schemas/kb.py:9` KbConfig — verify Wave A scope: add ACTIVE fields(extract_embedded_images + slide_screenshots + dedup_strategy + return_images_in_chat),leave Tier 2 fields out per ADR-0028 |
| 5 | `/kb/[id]` Documents tab | List documents + filter + actions | `GET /kb/{kb_id}/documents` → list[DocumentSummary] | ✅ supported | Wave A | C01 + C02 | `routes/documents.py:115` + `schemas/listing.py:14` |
| | | Upload + delete + reindex per doc | `POST /kb/{kb_id}/documents` + `DELETE /kb/{kb_id}/documents/{doc_id}` + `POST /kb/{kb_id}/documents/{doc_id}/reindex` | ✅ supported | Wave A | C01 + C02 | `routes/documents.py:332+394+445`(per CH-001 closed 2026-05-12) |
| | Chunks tab | List + preview chunks | `GET /kb/{kb_id}/chunks` → list[ChunkSummary] | ✅ supported | Wave A | C03 | `routes/chunks.py:55` + `schemas/listing.py:26` |
| | | Enable / disable chunk toggle | `PATCH /kb/{kb_id}/chunks/{chunk_id}` | ✅ supported | Wave A | C03 | `routes/chunks.py:83` |
| | **Images tab(NEW per ADR-0025)** | List images + filter by type + SHA256 dedup viz | `GET /kb/{kb_id}/images` → list[ImageRef + used_in_docs + used_in_chunks + dedup_savings] | 🔴 missing | Wave A backend gap(ADR-0025 dep)| C01 + C02 + C03 | none — needs new endpoint that enriches `ImageRef` with usage cross-refs |
| | **Chunking Lab tab(NEW per ADR-0025)** | Sample doc + chunking parameters + 4-strategy comparison | `POST /chunking-preview` body={kb_id, sample_doc_id, strategy, chunk_size, overlap} → list[StrategyResult] | 🔴 missing | Wave A backend gap | C01 + C03 | none — needs new endpoint dry-running the chunker on a sample doc |
| | Pipeline tab | 6-stage pipeline status | `GET /kb/{kb_id}` → KbStatus(status / last_indexed_at + failed_documents)+ inline aggregate from existing schemas | 🟡 partial — visualization only,no NEW endpoint | Wave A | C01 + C02 | `routes/kb.py:117` + KbStatus has the needed fields |
| | Retrieval Testing tab(per ADR-0021) | Run pure retrieval test with mode + top_k + threshold + reranker | `POST /kb/{kb_id}/retrieval-test` body=RetrievalTestRequest → RetrievalTestResult | ✅ supported | Wave A | C04 | `routes/retrieval_test.py:56` + `schemas/retrieval_test.py:38`(per ADR-0021 + W17 verify) |
| | | Heatmap viz(chunks × retrievers) | frontend visualization from RetrievalTestResult — schema has chunks[] with source(BM25/Vector/BM25+Vector)+ rerank_delta | ✅ supported(schema already carries source per ADR-0021) | Wave A polish | C04 + C09 | `schemas/retrieval_test.py:26` RetrievalTestChunk |
| | **Access tab(NEW per ADR-0025 + dep ADR-0027)** | Per-KB visibility + members + groups + permissions | `GET /kb/{kb_id}/acl` + `POST/PATCH/DELETE /kb/{kb_id}/acl/members` + `POST /kb/{kb_id}/acl/groups` | 🔴 missing(ADR-0027 dep) | Wave C(RBAC dep) | C11 + new C16 Users Service or fold into C02 | none — depends on ADR-0027 RBAC tables(`kb_acl` table) |
| | Settings tab | KB metadata + retrieval config + re-index trigger | `PATCH /kb/{kb_id}` body=KbMetadataPatch + `PATCH /kb/{kb_id}/settings` body=KbConfig + `POST /kb/{kb_id}/reindex` | ✅ supported | Wave A | C02 + C03 | `routes/kb.py:185+202+233` + `schemas/kb.py:9+31` |
| | | Danger zone(Archive + Delete) | `DELETE /kb/{kb_id}` exists;Archive `POST /kb/{kb_id}/archive` 🔴 missing | 🟡 partial | Wave A | C02 | Delete supported,Archive(read-only state)needs new endpoint |
| 6 | `/doc-detail/[kbId]/[docId]` | 3-pane outline + chunks + inspector | `GET /kb/{kb_id}/docs/{doc_id}` enriched(outline + parse_duration_ms + embed_duration_ms + total_images + image refs) | 🔴 missing | Wave B(ADR-0029 dep) | C01 + C03 | only `GET /kb/{kb_id}/chunks?doc_id=...` available;needs new doc-level endpoint with outline tree |
| | | Embedding vector preview(24 dims sampled) | derived from existing chunk embeddings — needs new endpoint or extension | 🟡 partial — could fetch via existing Azure Search if backend exposes it | Wave B polish | C03 | none — Power-user spec,defer if heavy |
| 7 | `/kb-upload/[id]` | 3-step re-ingestion(Data source / Document processing / Execute) | `POST /kb/{kb_id}/documents`(per CH-001) + progress via polling `GET /kb/{kb_id}/documents` | ✅ supported | Wave A | C01 | `routes/documents.py:332` |
| 8 | `/eval` | 4-metric eval run | `POST /eval/run` → EvalReport(per W17 F3 RAGAs) | ✅ supported | Wave B | C06 | `routes/eval.py:104` + `schemas/eval.py:14` |
| | | Reranker Shootout table(5+2 dropped) | `POST /eval/shootout` → ShootoutReport(per W17 F3 + ADR-0012) | ✅ supported | Wave B | C06 | `routes/eval.py:139` + `schemas/eval.py:34` |
| | | Failed queries inspector(Expected vs Got) | response `EvalReport.failed_queries[]` → list[FailedQueryDetail] | ✅ supported | Wave B | C06 | `schemas/eval.py:6` FailedQueryDetail |
| | | CRAG insight card(trigger rate + threshold) | derived from `EvalReport.crag_trigger_rate` | ✅ supported | Wave B | C06 | `schemas/eval.py:14` EvalReport(verify field) |
| 9 | `/traces`(list) | Trace list with filter + date range | `GET /traces?filter=...&since=...` → list[TraceSummary] | 🔴 missing(or `GET /queries/recent` if same backing store) | Wave B | C07 | none — currently only `GET /debug/trace/{id}` single |
| 10 | `/traces/[traceId]` | 9-stage trace detail | `GET /debug/trace/{trace_id}` → TraceDetail with stages[] | ✅ supported | Wave B | C07 | `routes/debug.py:16` + `schemas/observability.py:88` TraceDetail + `:64` TraceStage(per ADR-0020) |
| | | 3 viz modes(vertical / waterfall / flame) | frontend visualization from TraceDetail | ✅ supported(schema has all needed fields) | Wave B polish | C07 + C09 | `schemas/observability.py:64` TraceStage |
| | | Final response card | derived from stages[8].details(final response) | ✅ supported | Wave B | C07 | inline from TraceDetail |
| 11 | `/settings` | **Profile tab** | `GET /auth/me` → UserPublic;Tier 2 Edit profile disabled | 🟡 partial — `GET /auth/me` or session-derived | Wave C | C11 | `auth.py:56` UserPublic schema exists,but GET endpoint TBD verify |
| | | **Appearance tab** | client-side localStorage(theme + language) | ✅ supported(no backend) | Wave A | C09 | n/a |
| | | **Connections tab(9 providers)** | `GET/PATCH /admin/connections/{provider}` + `POST /admin/connections/{provider}/test` + `POST /admin/connections/{provider}/rotate` | 🔴 missing — **MASSIVE backend scope** | Wave C(ADR-0026 dep) | C12 + Key Vault SDK | none — 9 providers × ~3 endpoints each ~= 27 new endpoints **if Option B fully editable**;Option A read-only = `GET /admin/connections/list` only(~3 endpoints) |
| | | **Identity & Auth tab** | `GET/PATCH /admin/identity/{tenant|app|msal|roles|policy}` | 🔴 missing — large scope | Wave C(ADR-0026 dep + ADR-0027 dep) | C11 + C12 | none — Entra tenant + App reg fields are currently `.env`-driven |
| | | **API Keys & Quotas tab** | `GET /admin/api-keys` + `POST /admin/api-keys` + `DELETE /admin/api-keys/{id}` + `GET /admin/usage-stats` | 🔴 missing | Wave C(ADR-0026 dep) | C08 + new API key middleware | none — Tier 2 anonymous API keys per `Incoming API keys`,outgoing TPM/RPM stats via Langfuse(per `observability/realtime_cost.py`)|
| | | **Account tab** | `POST /auth/refresh`(rotate session)+ `POST /auth/logout` | ✅ supported(rotate session)| Wave C | C11 | `routes/auth.py:103+155` |
| | | | Tier 2 Delete account | 🔴 disabled affordance | Tier 2 | C11 | n/a |
| 12 | `/users` | **Members tab** | `GET /users` → list[UserDetail] + `PATCH /users/{id}` + `POST /users/invite` + `POST /users/{id}/suspend` | 🔴 missing | Wave C(ADR-0027 dep) | C11 + new C16 Users Service | `users_repo` table exists per ADR-0023 W17 F1 but no list/CRUD endpoint surface |
| | | **Roles tab** | `GET /roles` + `GET /role-permissions-matrix` | 🔴 missing | Wave C(ADR-0027 dep) | C11 + new tables | depends on RBAC migration |
| | | **Groups tab** | `GET /groups` + `POST /groups/sync-from-entra` + `PATCH /groups/{id}/role` | 🔴 missing | Wave C(ADR-0027 dep) | C11 + Entra graph API | depends on RBAC migration + Entra Graph SDK |
| | | **Audit log tab** | `GET /audit-log` + filter | 🔴 missing | Wave C(ADR-0027 dep) | C11 + new `audit_log` table | depends on RBAC migration |
| | | Stats strip(total / active / pending / avg queries) | derived from `/users` aggregate + `/queries/recent` aggregate | 🔴 missing | Wave C | C11 + C07 | n/a until /users + /queries/recent land |
| 13 | `/login` | Entra ID SSO + email/password | `POST /auth/login`(self-register path) + MSAL redirect(SSO path)| ✅ supported | Wave A(mock-auth default per user 岔口 2) | C11 | `routes/auth.py:304` + W7-W17 MSAL infra |
| | | Forgot password disabled affordance | n/a | ✅ disabled affordance(per ADR-0014) | Wave A | C11 | Tier 2 reset password |
| 14 | `/register` | 2-step form + verify-email | `POST /auth/register` + `POST /auth/verify-email` + `POST /auth/resend-verification` | ✅ supported | Wave A | C11 + C13(ACS Email) | `routes/auth.py:180+247+341` |
| - | Topbar NotificationsMenu | Notification feed(5 mock notif types) | `GET /notifications?user_id={id}` → list[Notification] | 🔴 missing | Wave A polish or Wave B | new endpoint group + Postgres `notifications` table | n/a — prototype inline mock per `ekp-shell.jsx:137` |
| - | Topbar Workspace switcher | Multi-tenancy switcher | n/a — **Tier 2 multi-tenancy hint** | 🟣 mock-only,**should disable** | Wave A | C02 + C11 | per F1 audit §2.3 Tier 2 leak |
| - | Sidebar Tools section(Settings / Users / Audit Log) | navigation to existing routes | ✅ supported | Wave A polish | C09 | n/a |
| - | Sidebar Labs · Tier 2 section | 8 `/labs/*` routes | 🟣 prototype-only(F5.4 recommend Option C — never ship) | Wave A polish | C09 | n/a |

### 2.2 Summary by status

| Status | Count | Surfaces |
|---|---|---|
| ✅ supported(real endpoint + schema match) | 21 | KB CRUD + Documents CRUD + Chunks CRUD + Retrieval Test + Eval + Trace Detail + Feedback + Query SSE + Auth + Cost Summary + Theme/Appearance |
| 🟡 partial(endpoint exists,schema/feature gap) | 7 | `/health` per-component / `KbConfig` multimodal fields / Archive KB / `QueryResponse.crag_*` fields verify / `GET /auth/me` verify / Pipeline tab visualization / Embedding vector preview |
| 🔴 missing(NEW endpoint) | 13 | Recent queries / Latest eval cache / Conversations / KB Images / Chunking preview / Doc detail enriched / Settings Connections × 9 / Settings Identity & Auth / Settings API Keys / `/users` + RBAC tables / Audit log / Notifications / `/traces` list |
| 🟣 mock-only(don't ship Tier 1) | 2 | Workspace switcher / Labs sidebar |

---

## §3 Cumulative backend-work list — grouped by Cn + Wave

### 3.1 Wave A blockers(must land before W20 ship)

**Minimum viable Wave A backend additions**(per Karpathy §1.2 simplicity):

| # | Item | Cn | Effort | Rationale |
|---|---|---|---|---|
| 1 | `GET /health` per-component connectivity payload(Azure Search / OpenAI / Cohere / Langfuse / Postgres connectivity dot)| C07 | 0.5-1d | Wave A `/dashboard` System health card current backend-up/down only,prototype shows per-component;backend small change(`/health` enrich return body)|
| 2 | `KbConfig` schema add multimodal ACTIVE fields(`extract_embedded_images: bool = True` + `slide_screenshots: bool = False` + `dedup_strategy: Literal["sha256"] = "sha256"` + `return_images_in_chat: bool = True`)| C02 + C01 | 0.5d | Wave A `/kb/new` Multimodal step Tier 1 fields;Tier 2 fields leave for ADR-0028 disabled affordance |
| 3 | **Decide**:Q6 recent queries enable OR Wave A `/dashboard` keep empty-state CTA | C07 + new query-log | n/a(decision) | If enable Q6 — needs `query_log` table + `POST /query` writes to it + `GET /queries/recent` endpoint;if keep empty-state CTA — defer(W18 F4 already accepted CTA approach) |
| 4 | **Decide**:Wave A `/dashboard` Latest eval card — cached run endpoint OR keep empty-state CTA | C06 | n/a(decision) | If enable — needs `eval_run` table + `POST /eval/run` writes result + `GET /eval/runs/latest`;if defer — keep CTA |
| 5 | `QueryResponse` schema verify includes `crag_triggered: bool` + `crag_iterations: int`(for Chat CRAG strip indicator)| C05 | 0.2d | grep `schemas/query.py:52`;if absent — add fields + populate from CRAG L2 loop |
| 6 | `POST /kb/{kb_id}/archive` endpoint(KB Settings Danger zone)| C02 | 0.3d | small addition for "Archive KB (read-only)" button |

**Wave A 估計**:6 small items,total ~3-4 days backend work,**can run in parallel with Wave A frontend**(W20-frontend-wave-a)。

### 3.2 Wave A backend gaps(NEW endpoints for ADR-0025 NEW tabs)

| # | Item | Cn | Effort |
|---|---|---|---|
| 7 | `GET /kb/{kb_id}/images` → list[ImageRef enriched with usage cross-refs] | C01 + C02 + C03 | 1d |
| 8 | `POST /chunking-preview` body={kb_id, sample_doc_id, strategy, chunk_size, overlap} → list[StrategyResult] | C01 + C03 | 1.5d(dry-run chunker on sample) |
| 9 | `GET /kb/{kb_id}/docs/{doc_id}` enriched(outline + parse_duration_ms + embed_duration_ms + total_images + image refs)| C01 + C03 | 1d(Wave B but flagged here as Wave A nice-to-have if Doc Detail moves up)|

### 3.3 Wave B backend gaps(new for `/traces` list + Doc Detail)

| # | Item | Cn | Effort |
|---|---|---|---|
| 10 | `GET /traces?filter=...&since=...` → list[TraceSummary] | C07 | 1d(query Langfuse + Postgres + filter) |

### 3.4 Wave C backend(MASSIVE — depends on ADR-0026 + ADR-0027 option pick at F6)

**ADR-0026 Settings → Connections**(Option B fully editable = 27 endpoints / Option A read-only = 3 endpoints / Option C hybrid = ~10 endpoints):

| # | Item | Cn | Effort(Option A / B / C) |
|---|---|---|---|
| 11a | `GET /admin/connections/list` → list[Provider + status + last_check] | C12 | 0.5d / 0.5d / 0.5d |
| 11b | `POST /admin/connections/{id}/test` → connection test result | C12 | n/a / 1.5d / 1.5d |
| 11c | `PATCH /admin/connections/{id}` body=updated fields → 200 | C12 + Key Vault | n/a / 2d / 1d(C only Profile + Appearance + Account)|
| 11d | `POST /admin/connections/{id}/rotate-secret` → new secret stored in Key Vault | C12 + Key Vault SDK | n/a / 2d / n/a |
| 12 | `GET /admin/identity/{tenant|app|msal|roles|policy}` + PATCH | C11 + C12 | 1d / 3d / 2d |
| 13 | `GET /admin/api-keys` + `POST /admin/api-keys` + `DELETE /admin/api-keys/{id}` + `GET /admin/usage-stats` | C08 + new API key middleware | 0.5d / 2d / 0.5d |

**ADR-0027 `/users` Tier 1.5 RBAC**(Option A full / Option B minimal 3-role / Option C stage):

| # | Item | Cn | Effort(Option A / B / C) |
|---|---|---|---|
| 14 | Postgres migration:`roles` + `role_permissions` + `groups` + `group_members` + `audit_log` + `kb_acl` tables | new C16 Users Service | 1.5d / 0.5d(only `users.role` column add)/ 1.5d |
| 15 | `GET /users` + `PATCH /users/{id}` + `POST /users/invite` + `POST /users/{id}/suspend` | C11 + C16 | 1.5d / 1d / 1.5d |
| 16 | `GET /roles` + `GET /role-permissions-matrix` | C16 | 0.5d / n/a(hard-coded matrix in code)/ 0.5d(read-only Tier 1)|
| 17 | `GET /groups` + `POST /groups/sync-from-entra` + `PATCH /groups/{id}/role` | C16 + Entra Graph SDK | 1.5d / n/a / 1.5d |
| 18 | `GET /audit-log` + filter | C16 + audit_log table | 0.5d / n/a / 0.5d(read-only Tier 1)|
| 19 | ACL middleware + role-gated route guard + auth-time role claim | C11 | 1.5d / 0.5d(`users.role` claim only)/ 1d |
| 20 | `GET /kb/{kb_id}/acl` + `POST/PATCH/DELETE /kb/{kb_id}/acl/members` + `POST /kb/{kb_id}/acl/groups`(per-KB ACL — depends on RBAC) | C02 + C11 + C16 | 1.5d / n/a / 1.5d |

**Wave C cumulative effort**(Option set summed):
- **Option A full RBAC + Option B fully editable Connections**:~22 backend days(W22 phase scope HIGH)
- **Option B minimal RBAC + Option A read-only Connections**:~5 backend days(W22 phase scope LOW — recommend if Tier 1 budget tight)
- **Option C stage + Option C hybrid**:~12 backend days(W22 phase scope MEDIUM,balanced)

### 3.5 Wave A polish / Tier 2(non-blocking)

| # | Item | Cn | Disposition |
|---|---|---|---|
| 21 | `GET /notifications?user_id={id}` | C07 | Wave A polish or **Wave B**;currently mock inline |
| 22 | `/conversations` CRUD | new Conversations Service | Beta+ — Wave A localStorage only,server-side Tier 2 |
| 23 | Workspace switcher disabled state | n/a | Wave A polish — **leak fix per F1 audit §2.3** |
| 24 | Labs sidebar section | n/a | F5.4 — Wave A polish — recommend Option C don't ship |

---

## §4 "Blocks Wave A/B/C" classification

### Wave A blockers(W20 cannot start without)

- ✅ **Tier 1 already supported**(21 surfaces):dashboard cards majority / chat full / KB CRUD / Documents CRUD / Chunks CRUD / Retrieval Testing / Pipeline tab / Settings tab basic / `/kb/new` Identity+Config+Defaults+Review steps / `/kb-upload/[id]` re-ingestion / `/login` + `/register`
- 🟡 **Wave A backend small additions**(items 1-6):`/health` per-component / `KbConfig` multimodal ACTIVE fields / `QueryResponse.crag_*` fields verify / Archive KB / Q6+EvalCache decision(can defer with CTA)
- 🔴 **Wave A backend NEW endpoints for ADR-0025 NEW tabs**(items 7-8):`/kb/{kb_id}/images` + `/chunking-preview`(Wave A KB Detail 8-tab full ship needs them;if absent — ship 5-tab + Images/ChunkingLab disabled affordance with "Tier 1.5 coming" badge — but defeats ADR-0025 acceptance)
- 🔴 **Wave A Access tab(part of ADR-0025)is BLOCKED on ADR-0027 RBAC** — Wave A KB Detail ship 7-tab(`-Access`)+ Access tab disabled affordance "Tier 1.5 RBAC pending Wave C" if Wave C ADR-0027 not yet Accepted

→ **Wave A scope decision**(F4):either(a) Wave A = 7-tab KB Detail(`-Access`),Access deferred to Wave C alongside `/users`;or(b) Wave A = 6-tab KB Detail(`-Access -Chunking Lab`)+ ADR-0027 promoted to Wave A scope(massive Wave A balloon)。**Recommend (a)**:Wave A 7-tab,Access tab disabled affordance,land 一齊 with Wave C(F4 detail)。

### Wave B blockers(W21 cannot start without)

- ✅ **Tier 1 already supported**(11 surfaces):`/eval` full(W17 F3 RAGAs)/ `/traces/[traceId]` full(W16 F5.5)/ `/doc-detail` chunks portion via existing endpoint(but limited)
- 🔴 **Wave B backend NEW endpoints**(items 9-10):`/kb/{kb_id}/docs/{doc_id}` enriched + `/traces` list
- 🟡 Embedding vector preview is polish detail,defer if heavy

→ **Wave B scope**:2 small NEW backend endpoints + frontend-heavy(3 viz modes for trace + 3-pane doc detail)。Independent of Wave C strategic 岔口。

### Wave C blockers(W22 cannot start without)

- 🔴 **ADR-0026 + ADR-0027 Status Accepted**(F6 strategic 岔口 picks)
- 🔴 **Postgres migration for RBAC tables**(Option A/C only — not B which keeps `users.role` column)
- 🔴 **Settings Connections backend group**(Option B/C — Option A defers most)
- 🟡 **Track A IT cred lands**(W16 F1) — if not landed by W22 start,real-MSAL stays feature-flagged,Wave C ships mock+real concurrent per user 岔口 2
- 🟡 **Key Vault SDK wire**(Option B Settings Connections)— new dep,subject to H2 stop-and-ask if Wave C 採 Option B

→ **Wave C is the largest by far**(~5-22 backend days depending on option picks)。F4 strongly recommend Wave C split into sub-phases(C1 = Settings + minimum RBAC / C2 = full Audit log + Per-KB ACL)if Option A or C picked。

### Wave D(Tier 2 — post-Beta Q12)

- 🟣 **`/labs/*` 8 routes — recommend Option C in F5.4** prototype-only,don't ship `frontend/`
- All Tier 2 disabled affordances(Power User / Custom roles / Public KB / Anonymous API keys / Vision captioning / Render PDF pages / Perceptual dedup / Distributed token cache / Reset password / Multi-tenancy / etc.)stay as disabled affordances ship in Wave A-C — promote to active only post-Beta governance Q12 trigger

---

## §5 ADR-impact summary

| ADR | Backend dep | Wave |
|---|---|---|
| ADR-0025 KB Detail 5→8 tabs | items 7+8(`/kb/{kb_id}/images` + `/chunking-preview`)— Images + Chunking Lab tabs | **Wave A**(Access tab depends on ADR-0027 → Wave C) |
| ADR-0026 Settings 6-tab | items 11-13(Connections + Identity & Auth + API Keys — option set scope)| **Wave C**(strategic 岔口 2 pick at F6) |
| ADR-0027 /users Tier 1.5 RBAC | items 14-20(RBAC migration + endpoints + ACL middleware + Per-KB ACL — option set scope)| **Wave C**(strategic 岔口 1 pick at F6;Wave A Access tab BLOCKED on this) |
| ADR-0028 /kb/new 5-step + Multimodal | item 2(`KbConfig` multimodal ACTIVE fields)| **Wave A** |
| ADR-0029 /doc-detail 3-pane | item 9(`GET /kb/{kb_id}/docs/{doc_id}` enriched)| **Wave B** |
| ADR-0030(candidate)Dashboard richer + Trace 3 viz + /traces list | items 1+10(`/health` enrich + `/traces` list)+ frontend polish | Wave A + Wave B |
| ADR-0031(candidate)Chat advanced surfaces | item 22(`/conversations` Beta+ — localStorage Tier 1 OK,server-side Tier 2)| Wave A polish |
| ADR-0032(candidate)Topbar + Sidebar additive | item 21(`/notifications`)+ Workspace switcher disable + Labs section disposition | Wave A polish |

---

## §6 Recommendations to F3 + F4 + F6

1. **F3 ADR-0026 Chris pick at F6** — strongly recommend **Option C hybrid**:Profile + Appearance + Account fully editable(low scope already supported),Connections + Identity & Auth + API Keys = **read-only with "Edit coming Tier 2" affordance**。Backend scope ~3 endpoints vs full editable 27 endpoints。Trade-off:Beta operators still rotate secrets via `.env` + Azure Portal,UI shows status only。
2. **F3 ADR-0027 Chris pick at F6** — strongly recommend **Option B minimal 3-role hard-coded**:`users.role` column on existing `users` table per ADR-0023 + ACL middleware checks role only。NO new tables(`roles` / `groups` / `audit_log` defer Tier 2)。Members tab = read-only listing + invite/suspend actions;Roles tab = read-only matrix;Groups tab = disabled affordance「Tier 2 sync from Entra」;Audit log tab = disabled affordance「Tier 2 audit log」。Backend scope ~5 days vs ~20 days full RBAC。Trade-off:per-KB ACL(Access tab)deferred Tier 2 — Wave A KB Detail ships 7-tab(`-Access`)。
3. **F3 add ADR-0030 OR fold into Wave A scope** — `/health` per-component + `/traces` list + Trace 3 viz are polish-grade,recommend **fold into Wave A scope without separate ADR**(implementation in W20-frontend-wave-a phase plan + small backend changes)。
4. **F3 add ADR-0031 OR fold into Wave A polish** — Conversation History sidebar(Beta+) + 3 citation placement modes are Tier 1 enhancements per technical-highlight Q10 answer;recommend **separate ADR-0031** because Conversation History 需 `/conversations` CRUD if promoted to server-side(per C10 §7)。F6 Chris可 decide Tier 1 localStorage scope。
5. **F3 ADR-0032 NOT needed** — Workspace switcher fix(disable affordance)+ Sidebar Labs section(F5.4)+ NotificationsMenu(item 21)small enough to absorb into Wave A polish without separate ADR。Mention in F5 Tier 2 catalog instead。

→ **Final F3 deliverable**:5 ADRs(0025-0029)stable + ADR-0031 NEW as 6th(Chat advanced surfaces)= 6 total。ADR-0030 + ADR-0032 absorbed into Wave A scope。

→ **Wave C recommendation**:if Chris picks Option B + Option C — **Wave C single phase 5-7 backend days + 3-5 frontend days = ~2 weeks**。If Chris picks Option A + Option B(full + fully editable)— **Wave C split into C1 + C2 sub-phases** to maintain rolling JIT discipline per CLAUDE.md §10。

---

**Next deliverable**:F3 5 ADR drafts(0025-0029)+ ADR-0031(NEW)candidate;F4 Wave breakdown consume F2 + F3。

---
phase: W01-foundation
plan_ref: ./plan.md
status: closed
last_updated: 2026-05-02
---

# Phase W01 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort)。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因。

## F1 — Repo hygiene + Dify reference clone

- [x] Rename `gitignore` → `.gitignore`(critical pattern verify:`.env`、`references/dify/`、`DIFY_PINNED_COMMIT.txt` 都喺度) — commit `9ea18f1`
- [x] `git init` + branch=main + initial commit `chore(repo): initial portfolio scaffold`
- [x] `git clone --depth 1 https://github.com/langgenius/dify.git` to `references/dify/`(retry with `git -c core.longpaths=true restore` after Windows MAX_PATH hit)
- [x] Generate `references/DIFY_PINNED_COMMIT.txt` 寫入 commit SHA(`fe2f7a8920`)
- [x] `git check-ignore references/dify/ references/DIFY_PINNED_COMMIT.txt` 兩者都 ignored

## F2 — Backend FastAPI skeleton

- [x] `backend/pyproject.toml`(Python 3.12+,FastAPI、Pydantic v2、Pydantic Settings、structlog、tenacity、httpx、python-multipart、pyyaml + dev deps)
- [x] `backend/Dockerfile` + `.dockerignore`
- [x] 7 `__init__.py` package marker(backend, api, routes, schemas, observability, storage, tests)
- [x] `backend/api/server.py`(FastAPI app + 8 router includes + `/health`)
- [x] 8 routes:`query.py`、`feedback.py`、`kb.py`、`documents.py`、`chunks.py`、`eval.py`、`debug.py`、`screenshots.py`(18 endpoints,各 raise HTTPException(501) with spec ref)
- [x] 4 schema:`query.py`、`kb.py`、`eval.py`、`feedback.py`(per §4.5)
- [x] `backend/storage/settings.py`(Pydantic Settings,UPPER_SNAKE env var via `case_sensitive=False`)
- [x] `backend/observability/langfuse_tracer.py`(stub structlog JSON config)
- [x] `backend/tests/test_api_skeleton.py`(8 smoke tests,per H6 query.py critical)
- [x] Ruff `check .` clean
- [x] `python -m compileall .` clean
- [ ] **DEFERRED to post-pip-install window** — pytest run
  - W1 D1 blocker(cp314 wheel):**RESOLVED** W1 D2 via Python 3.12.10 install
  - W1 D2 NEW blocker:Ricoh corp proxy 對 PyPI/TUNA wheel >500KB 全部 `IncompleteRead(0 bytes)`
  - Mitigation:P1(VPN/hotspot ops window)或 P2(IT whitelist)— Chris ops decision pending
  - commit ref:`b21a0a2`(skeleton),pytest retry 待 window

## F3 — Frontend Next.js 14 skeleton

- [x] `frontend/package.json`(Next.js 14、shadcn-ui foundation、Tailwind 3.4、Vercel AI SDK、TanStack Query、Zustand、TypeScript 5.7)
- [x] `frontend/tsconfig.json`(strict mode)
- [x] `frontend/next.config.mjs`(App Router,standalone build,API rewrite to `:8000`)
- [x] `frontend/tailwind.config.ts`(uses ekpTokens)
- [x] `frontend/postcss.config.js` + `frontend/Dockerfile` + `.dockerignore` + `.eslintrc.json` + `.prettierrc`
- [x] `frontend/lib/theming/tokens.ts`(neutral grayscale per OQ-Q10 default,W4 designer pass)
- [x] `frontend/lib/api-client.ts`(thin fetch wrapper)
- [x] `frontend/lib/utils.ts`(`cn()` shadcn helper)
- [x] `frontend/app/globals.css` + `app/layout.tsx`
- [x] 6 routes:`/`、`/admin`、`/admin/kb`、`/admin/kb/[id]`、`/eval`、`/debug/[traceId]`
- [x] `pnpm install` 成功(3 min,376 packages)
- [x] `pnpm type-check` clean(after `as const` removal in tokens.ts)
- [x] `pnpm lint` 0 warnings/errors — commit `7589110`

## F4 — Local dev stack

- [x] `docker-compose.yml` `langfuse:2-latest` → `langfuse:2` tag fix(2-latest no longer published)— commit `f7ba973`
- [x] Postgres 16-alpine 起 healthy(port 5432 internal)
- [x] Langfuse v2 起 → `/api/public/health` HTTP 200(image pulled via `docker.io/langfuse/langfuse:2` direct,bypass MCR mirror)
- [x] Azurite via npm fallback(`npm install -g azurite` 376 packages 1 min)
- [x] Azurite Blob/Queue/Table listening at `http://127.0.0.1:10000`-10002
- [ ] **PENDING** — Azurite via Docker(blocked by Ricoh corp DNS intercept on MCR;workaround in place via npm,W2+ if VPN / IT whitelist)

## F5 — Eval set v0 schema validator

- [x] `scripts/__init__.py`
- [x] `scripts/validate_eval_set.py`(stdlib + pyyaml,no pydantic dep)
- [x] Validation rules:total_queries match,duplicate id,oos must `expected_refusal`,non-oos must have `primary_chunk_ids`
- [x] Run `python -m scripts.validate_eval_set docs/eval-set-v0.yaml` → exit 0 OK(after fixed null difficulty handling for oos queries)
- [x] Ruff clean — commit `cc0b90b`

## F6 — Sample manual structure inspector

- [x] `scripts/inspect_docx_structure.py`(stdlib `zipfile` + `xml.etree`)
- [x] Q17:heading style coverage(H1/H2/H3 counts + paragraphs with hardcoded font size)
- [x] Q18:embedded image format inventory(PNG/JPG/WMF/EMF/SVG/HEIC counts)
- [x] CLI:accepts file or directory,edge case(path-not-found / non-docx)handled
- [ ] **BLOCKED on Q2** — Run on 5 sample Ricoh manual,produce Q17/Q18 finding report

## F7 — KB management CRUD impl

- [x] **KB management package**(`backend/kb_management/`)
  - `storage.py`:`KBStorageBackend` Protocol + `InMemoryKBBackend`(W1)+ `KBNotFoundError` / `KBAlreadyExistsError`
  - `service.py`:`KBService` + `get_kb_service()` lru_cache singleton
  - `__init__.py`:public re-exports
  - **Note**:plan §2 寫 `kb_service.py` 單檔,實作改為 3-file package(Protocol-based,W2 swap to Azure AI Search 唔需改 call site)。`§1.3` surgical:scope unchanged
- [x] **Schema**:`KbCreate` input(`backend/api/schemas/kb.py`)
- [x] `POST /kb` create — 201 Created;409 Conflict 若 `kb_id` 已存在
- [x] `GET /kb` list
- [x] `GET /kb/{kb_id}` detail — 404 if not found
- [x] `DELETE /kb/{kb_id}` delete + cleanup(W1 in-memory only;W2 D1 真 cleanup index + Blob container)
- [x] `PATCH /kb/{kb_id}/settings` update — full-replace KbConfig(partial PATCH 留 W2+ 如需)
- [x] **Routes refactor**:`Annotated[KBService, Depends(get_kb_service)]` modern FastAPI pattern(ruff B008 clean)
- [x] **pyproject**:`kb_management*` 加入 setuptools.packages.find include
- [x] **Verification**:ruff check ✅,ruff format ✅,`python -m compileall` ✅
- [ ] **DEFERRED to post-pip-install window** — Unit tests for CRUD(mock storage backend)
  - Reason:pytest 未裝(corp proxy block);verification path 同 F2 deferred,共用同一 ops window 解

## F8 — Docling `.docx` parser PoC

- [ ] **BLOCKED on Q2** — sample manual access
- [ ] Install Docling(pip)— note:Docling Docker image 2GB,但 backend 用 Docling library 直接 install,唔需要 Docker
- [ ] `backend/ingestion/parsers/docx_parser.py` 用 Docling
- [ ] Parse 5 sample,extract heading-aware sections + embedded image inventory + table structure
- [ ] Sanity check report output

## F9 — Azure AI Search index 創建 ✅

- [x] **W1 D2** Q3 endpoint + admin key delivered to root `.env`(commit `09138d4`)
- [x] **W1 D4(2026-05-02)** `backend/indexing/schema.json` extracted as spec §3.6 JSON literal
- [x] HNSW vectorSearch profile `ekp-vector-profile`(m=4 efConstruction=400 efSearch=500 cosine)— in schema
- [x] Semantic config `ekp-semantic-config` — in schema
- [x] `scripts/create_index.py` REST CLI(stdlib `urllib.request`,no SDK / pip dep — bypass R8 corp proxy)
- [x] Index 創建 success:`python -m scripts.create_index create` → HTTP 201(2026-05-02);GET verify → 18 fields + ekp-vector-profile + ekp-semantic-config ✅
- [x] C03 design note `v0-draft → v1-active`(per CC-5)

## F10 — Embedding pipeline first-pass

- [ ] **BLOCKED on Q4** — Azure OpenAI deployment names + endpoint + API key 入 `.env`
- [ ] `backend/generation/azure_openai_client.py` async embedding(text-embedding-3-large,1024d MRL)
- [ ] Smoke test:1 條 sample → 1024d vector
- [ ] Structlog cost log

## F11 — 30 條 synthetic eval set ground truth fill

- [ ] **BLOCKED on Q14** — specific SME labeler name(W1 末 by Chris)+ Q2(chunk_id discovery from sample manual)
- [ ] All 30 main queries `annotation.validated: true`
- [ ] Replace placeholder chunk_id with real ones
- [ ] `docs/eval-set-v1.yaml`(rename from v0 once SME-validated)
- [ ] `python -m scripts.validate_eval_set docs/eval-set-v1.yaml` exit 0

---

## Cross-Cutting

- [x] Decision-form.md updated for 6 critical OQ resolution(Q1-Q4 + Q13 + Q14) — commit `d74fee2`
- [x] `.gitignore` add `.claude/` + checkpoint dev log + topology svg — commit `e3fc338`
- [x] **NEW**:Phase planning framework introduced mid-W1 D1(PROCESS.md + 3 templates + W01 retroactive docs)
- [x] **W1 D2 H5 remediation** — gitignore `docs/11-env-resources-detail/` + relocate Q3+Q4 plaintext secrets to root `.env` + sanitize markdown 為 reference table — commit pending(this batch)
- [x] **W1 D2 Python 3.12.10 install** — winget per-user,resolve W1 D1 R5 risk(cp314 wheel supply)— covered in progress Day 2
- [ ] All deliverables(F7-F11)committed by W1 D5(2026-05-04)
- [x] **W1 D2 OQ sync to `decision-form.md`**:Q3 → `Resolved (pending tier+region W2 D1)`,Q4 → `Resolved (full)`,Q14 → `Resolved (full — Chris Lai self-assigned)`;dashboard table + pending implementation list 同步更新 — commit `dfcafbf`
- [x] **W1 D3 Component Catalog spine**(per Chris strategic call)— commits `220f75a` + `2dc0948` + `99ebf0c`
  - `docs/02-architecture/COMPONENT_CATALOG.md` 12-component spine(C01-C12)+ dependency graph + phase × component heatmap + 7 cross-cutting conventions CC-1..CC-7 + 8 Tier 2 future-slot mapping
  - `docs/02-architecture/components/README.md` design note convention(per CC-5,updated to design-first)
  - `RISK_REGISTER.md` living register extends frozen `architecture.md §8` + adds R8 (corp proxy) + R9 (MCR DNS) + R10 (Q2 delay)
  - `W01-foundation/plan.md` F1-F11 component-tagged(per CC-1)
  - `decision-form.md` 21 OQ dashboard component-tagged(per CC-3)
  - `CLAUDE.md §2` routing 加 catalog + risk register row
- [x] **W1 D3 Component Design Notes batch**(per Chris W1 D3 strategic update)— commits `7737069` + `6b5660a`
  - **CC-5 convention update**:rolling JIT → design-first with v0-draft marker(catalog + components/README updated)
  - **11/12 component design notes** 完成(C11 Beta+ defer to W6/W7):
    - **Batch 1 backend mature**:C12 (v1-active) / C02 (v1-active) / C08 / C06 / C07
    - **Batch 2 forward-looking**:C09 / C10 / C03 / C01 / C04 / C05
  - 共 ~2128 lines,跟 8-section template(internal arch / interfaces / decisions / edge cases / perf / test / Tier 2 hooks / TODO)
  - **C11 Identity & Access** scheduled W6 末 / W7 kickoff per Beta+ scope
- [ ] (Ongoing)Future OQ status changes synced to `decision-form.md` — W2+ Q5/Q11/Q15-21 之 resolution
- [ ] (Ongoing)Future ADR / phase plan / risk update 必 component-tag(per CC-1/2/3/4)
- [ ] (Ongoing)Per-component design note status bumps(v0-draft → v1-active → v2-stable)隨 implementation 進行
- [x] All architectural-adjacent decisions documented as ADR(per CLAUDE.md §5.1 H1)— **W1 全 phase NO ADR triggered**(per retro D4 verdict;all decisions either spec-aligned or implementation-detail-only)
- [x] `progress.md` retro section written **W1 D5 early closeout 2026-05-02**(D4 draft → D5 final fill compressed same-day per Chris session decision)
- [x] `progress.md` frontmatter status flipped to `closed`(D5 closeout commit)
- [x] Phase W02 kickoff trigger noted in retro(W02 plan flipped status `draft → active` D5 closeout commit)
- [x] **D5 early closeout cross-cutting**(this commit):
  - Q3 full Resolved(tier Standard S1 + region eastus2 confirmed by Chris)→ R4 sync `decision-form.md`
  - R8 P1 retest 2026-05-02 → confirmed still blocked,同 W1 D2 同樣 `IncompleteRead(0 bytes read)` pattern → carry to W2 F10
  - G3 Langfuse health degradation NEW finding → W2 carry-over for Chris triage(候選 BUG-001 Sev3)
  - W01 checklist.md frontmatter status closed
  - W02 plan.md / progress.md sign-off mention

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。

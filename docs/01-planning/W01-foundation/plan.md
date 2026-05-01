---
phase: W01-foundation
name: "Foundation Setup"
sprint_week: W1
start_date: 2026-04-30
end_date: 2026-05-04          # planned, 5 工作日
status: active
spec_refs:
  - architecture.md §6.1 W1 row
  - architecture.md §3.3      # multi-format ingestion
  - architecture.md §3.4      # multi-KB
  - architecture.md §4.1-§4.5 # application architecture
  - architecture.md §5.1-§5.7 # UI specifications
  - decision-form.md §1-§4    # 21 OQ
prior_phase: null             # first phase
---

# Phase W01 — Foundation Setup

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-04-30,acting as Stakeholder per session decision)

## 1. Scope

W01 係 EKP Tier 1 嘅 foundation phase。建立 repo + Dify reference + backend FastAPI skeleton + frontend Next.js skeleton + local dev stack(Azurite/Langfuse/Postgres)+ eval set v0 schema validator + sample manual inspector + Docling .docx parser PoC + Azure AI Search index 創建 + first KB CRUD + 30 條 synthetic eval set ground truth fill。

呢個 phase 嘅 critical condition:**所有 6 條 critical OQ(Q1, Q2, Q3, Q4, Q13, Q14)Resolved 之前唔啟動 W2**。**Sprint week origin**:[`architecture.md` §6.1 W1](../../architecture.md)

## 2. Deliverables

### F1 — Repo hygiene + Dify reference clone
- **Component(s)**:**C12** DevOps & Infra(repo + Dify reference setup)
- **Spec ref**:`architecture.md §12.1`,`CLAUDE.md §7`
- **OQ deps**:none
- **Acceptance criteria**:
  - `.gitignore` 包 `references/dify/` + `.env` + `.claude/`
  - `git init` + initial commit done
  - `references/dify/` clone 完(11295 files at pinned commit)
  - `references/DIFY_PINNED_COMMIT.txt` 寫入 SHA
  - 兩者都 gitignored(`git check-ignore` 確認)
- **Effort estimate**:1h
- **Owner**:AI

### F2 — Backend FastAPI skeleton(18 endpoint stubs)
- **Component(s)**:**C08** API Gateway(scaffold);secondary touch **C07** Observability(structlog + Langfuse stub init)
- **Spec ref**:`architecture.md §4.1, §4.4, §4.5`,`CLAUDE.md §3.1, §5.6`
- **OQ deps**:none
- **Acceptance criteria**:
  - 18 endpoints registered across 8 routers per §4.4
  - Pydantic v2 schemas per §4.5
  - Pydantic Settings reading `.env` per .env.example
  - Structlog JSON config(stub Langfuse tracer init)
  - Dockerfile + .dockerignore
  - 8 smoke tests in `tests/test_api_skeleton.py`(per H6 query.py critical)
  - Ruff clean
  - `python -m compileall` clean
  - **(deferred)** pytest run(blocked by Python 3.14 cp314 wheel supply issue)
- **Effort estimate**:3h
- **Owner**:AI

### F3 — Frontend Next.js 14 skeleton(6 routes)
- **Component(s)**:**C09** Admin Console UI(primary 5/6 routes)+ **C10** Chat Interface UI(`/` placeholder pre-W3)
- **Spec ref**:`architecture.md §4.1, §5.1-§5.7`,`CLAUDE.md §3.2`
- **OQ deps**:Q10(default = neutral tokens)
- **Acceptance criteria**:
  - Next.js 14 App Router + TypeScript strict
  - 6 routes:`/`, `/admin`, `/admin/kb`, `/admin/kb/[id]`, `/eval`, `/debug/[traceId]`(`/history`、`/settings` defer to Beta+)
  - `lib/theming/tokens.ts` 100% custom(non-Dify per §5.1)
  - Tailwind 3.4 + PostCSS + autoprefixer
  - `lib/api-client.ts` reading `NEXT_PUBLIC_API_URL`
  - `pnpm install` + `pnpm type-check` + `pnpm lint` 全 pass
- **Effort estimate**:3h
- **Owner**:AI

### F4 — Local dev stack(Azurite + Langfuse + Postgres)
- **Component(s)**:**C12** DevOps & Infra(primary,docker-compose + Azurite)+ **C07** Observability(Langfuse + Postgres backing)
- **Spec ref**:`architecture.md §4.3`,`docs/setup.md §4.2`
- **OQ deps**:none
- **Acceptance criteria**:
  - `infrastructure/docker-compose.yml` 起 Postgres + Langfuse(Azurite Docker route blocked by Ricoh corp DNS intercept on MCR)
  - Azurite via npm fallback(`npm install -g azurite`)healthy at `http://127.0.0.1:10000`
  - Langfuse `/api/public/health` 返 HTTP 200
  - Postgres healthy
- **Effort estimate**:1h(原計 0.5h,corp infra 撞撞撞 +0.5h)
- **Owner**:AI + Chris(start Docker Desktop)

### F5 — Eval set v0 schema validator
- **Component(s)**:**C06** Eval Framework
- **Spec ref**:`architecture.md §6.1 W1`,`docs/eval-set-v0.yaml` step 5e,`docs/eval-methodology.md`
- **OQ deps**:Q14(SME labeler — pending W1 末 specific name,但 schema validator 唔依賴)
- **Acceptance criteria**:
  - `scripts/validate_eval_set.py` 用 stdlib + pyyaml(無 pydantic dep)
  - Validate 規則:total_queries match,no duplicate query_id,oos must `expected_refusal=true`,non-oos must have `primary_chunk_ids`
  - 跑 `python -m scripts.validate_eval_set docs/eval-set-v0.yaml` → exit 0
  - Ruff clean
- **Effort estimate**:1h
- **Owner**:AI

### F6 — Sample manual structure inspector
- **Component(s)**:**C01** Ingestion Pipeline(exploratory tool to inform parser design)
- **Spec ref**:`decision-form.md §3 Q17 + Q18`
- **OQ deps**:Q2(sample manual access — execution blocked,script self 可寫)
- **Acceptance criteria**:
  - `scripts/inspect_docx_structure.py` stdlib only(`zipfile` + `xml.etree`)
  - Cover Q17:heading style coverage 統計
  - Cover Q18:embedded image format inventory
  - CLI 接受 file 或 dir,edge case(path-not-found / non-docx)handled
- **Effort estimate**:1h
- **Owner**:AI

### F7 — KB management CRUD impl(replace 501 stubs)
- **Component(s)**:**C02** Knowledge Base Manager(primary);wired through **C08** API Gateway routes
- **Spec ref**:`architecture.md §3.4, §4.4 #4-8`
- **OQ deps**:Q3(Azure AI Search resource — pending implementation detail,可先做 in-memory mock service for unit test)
- **Acceptance criteria**:
  - `POST /kb` create KB(in-memory or storage backend)
  - `GET /kb` list
  - `GET /kb/{kb_id}` detail
  - `DELETE /kb/{kb_id}` delete
  - `PATCH /kb/{kb_id}/settings` update config
  - Unit tests for CRUD(mock storage)
- **Effort estimate**:4h
- **Owner**:AI

### F8 — Docling `.docx` parser PoC on 5 sample manuals
- **Component(s)**:**C01** Ingestion Pipeline(parser sub-step)
- **Spec ref**:`architecture.md §3.3`
- **OQ deps**:Q1(format ratio,Resolved 40W/30PPT/30PDF),Q2(sample access — pending you 提供 zip / folder)
- **Acceptance criteria**:
  - `backend/ingestion/parsers/docx_parser.py` 用 Docling
  - Parse 5 sample manual,extract:heading-aware sections,embedded image inventory,table structure
  - Report run on 5 sample,output sanity check 報告
- **Effort estimate**:6h
- **Owner**:AI(等 Q2 sample)

### F9 — Azure AI Search index `ekp-kb-drive-v1` 創建
- **Component(s)**:**C03** Indexing Service(first-touch heavy work)
- **Spec ref**:`architecture.md §3.6`
- **OQ deps**:Q3(Azure resource — pending you 提供 endpoint + key 入 `.env`)
- **Acceptance criteria**:
  - Index schema match `architecture.md §3.6` JSON
  - Vector profile `ekp-vector-profile`(HNSW m=4 efConstruction=400 efSearch=500 cosine)
  - Semantic config `ekp-semantic-config`
  - 透過 `az search` CLI 或 SDK script 創建,跑成功
- **Effort estimate**:2h
- **Owner**:AI(等 Q3)

### F10 — Embedding pipeline first-pass(Azure OpenAI text-embedding-3-large)
- **Component(s)**:**C01** Ingestion Pipeline(embedding sub-step)
- **Spec ref**:`architecture.md §3.2`
- **OQ deps**:Q4(deployment names — pending you 提供 入 `.env`)
- **Acceptance criteria**:
  - `backend/generation/azure_openai_client.py` async embedding call
  - Smoke test:1 條 sample text → 1024d vector(MRL truncate from 3072)
  - Cost log 追蹤(structlog)
- **Effort estimate**:3h
- **Owner**:AI(等 Q4)

### F11 — 30 條 synthetic eval set ground truth fill
- **Component(s)**:**C06** Eval Framework(ground truth artifact)
- **Spec ref**:`architecture.md §6.1 W1`,`docs/eval-set-v0.yaml`
- **OQ deps**:Q14(specific SME labeler — Resolved pending name by W1 末)+ Q2(sample access for chunk_id discovery)
- **Acceptance criteria**:
  - `docs/eval-set-v1.yaml`(rename from v0 once SME-validated)
  - All 30 main queries `annotation.validated: true`
  - Real chunk_id replace placeholder
  - Pass `python -m scripts.validate_eval_set docs/eval-set-v1.yaml`
- **Effort estimate**:2-3 工作日 SME effort spread W1-W4
- **Owner**:Chris + SME(per Q13 + Q14 resolved)

## 3. Success Criteria(Phase Gate to W2)

| # | Criterion | Target | Measure | Block W2? |
|---|---|---|---|---|
| G1 | All 11 deliverables 完成 OR explicit deferred | 11/11 | journal closeout retro | Yes |
| G2 | 6 critical OQ(Q1-Q4,Q13,Q14)`Resolved` | 6/6 | `decision-form.md §4` dashboard | Yes |
| G3 | Local dev stack 3/3 services up | 3/3 | `curl /health` + `docker compose ps` | Yes |
| G4 | Backend ruff + frontend lint + type-check 0 errors | All clean | CI / local run | Yes |
| G5 | F8 Docling PoC parses 5 sample without unrecoverable error | 5/5 | F8 report | Yes |
| G6 | F11 ground truth ≥ 30 queries validated | ≥ 30 | F11 eval-set-v1.yaml | Yes |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Q2 sample manual access 滯後 → F8 + F11 block | Medium | High | Chris W1 D2 確認 path;最壞情況用 Ricoh public-domain manual 樣本暫代 |
| R2 | Q14 SME labeler 未 assign → F11 ground truth 唔可 validate | High | High | LLM-judge first pass + Chris verify fallback(per architecture.md §8.1 R2) |
| R3 | Ricoh corp DNS intercept MCR / PyPI cp314 wheel 撞 | Confirmed | Medium | Workaround in-place(npm Azurite,direct docker.io,batch pip install);long-term IT request whitelist |
| R4 | Docling Docker image ~2GB pull 慢 | Medium | Low | F8 day pre-pull;若 corp proxy 卡 MCR 同樣,fallback python-docx + Docling library install via pip |
| R5 | Python 3.14 cp314 wheel supply 持續不穩 | High | Medium | Recommend Chris install Python 3.12(stable wheel ecosystem)— W1 D2 decision |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-04-30 | F1-F6 skeleton + scripts + dev stack | F1, F2, F3, F4, F5, F6 |
| D2 | 2026-05-01 | F7 KB CRUD + start F8(若 Q2 sample 到位) | F7, F8 start |
| D3 | 2026-05-02 | F8 cont + F9 Azure index | F8, F9 |
| D4 | 2026-05-03 | F10 embedding pipeline | F10 |
| D5 | 2026-05-04 | F11 ground truth fill kick + W1 retro prep | F11 start, retro |

## 6. Dependencies on Prior Phase

`N/A — first phase of EKP Tier 1`

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-04-30 | Initial plan(retroactive after Day 1 implementation) | Phase planning framework introduced mid-Day 1;backfill captures Day 1 已執行 deliverables F1-F6 + remaining F7-F11 forward planning | Chris |
| 2026-05-01 | **F2 pytest retry re-deferred** D2 → post-pip-install window;**F7 unit tests deferred** D2 → post-pip-install window | Python 3.12.10 install ✅ resolves W1 D1 cp314 wheel issue,but pip install hits NEW blocker:Ricoh corp proxy 對 PyPI/TUNA wheel >500KB 落 `IncompleteRead(0 bytes)`(tested via pip default、`--retries 10`、TUNA mirror,全部斷流)。P3 pivot path:H5 remediation commit + F7 implementation code 今日推進,F2 + F7 pytest verification 等 P1(VPN/hotspot)或 P2(IT whitelist)window | Chris(P3 approved) |

---

**Lifecycle reminder**:
- 呢份 plan locked after status=active(2026-04-30)
- Status:`active`(W1 D2 起跟 framework 走)
- 重大 deviation 入第 7 節 changelog

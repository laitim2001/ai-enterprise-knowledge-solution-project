---
phase: W08-beta-deploy-sprint2
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active    # flipped draft→active 2026-05-19 W8 D1 kickoff
---

# Phase W08 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 自 2026-05-16 W7 D5 closeout cascade。

---

## Day 0 — 2026-05-16: Kickoff prep(W7 D5 末 closeout cascade same-session)

**Action**:Phase W08 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle;W7 D5 closeout cascade per CLAUDE.md §10 R5)

- Folder `docs/01-planning/W08-beta-deploy-sprint2/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6:Real Entra ID auth integration LIVE switch + Azure Container Apps deploy backend + Azure Static Web Apps deploy frontend + LIVE smoke cascade(F1.7 + F3.5 + F4.5 W7 carry-overs)+ Cost monitoring + user feedback dashboard + Phase Gate closeout + W9 kickoff prep)
- `checklist.md` derived from plan deliverables(~31 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W07-beta-deploy**(per W7 retro § Carry-overs C1-C10):
  - C1 W8 D1 Q11 IT operational cascade trigger(F1.1 — Beta-blocking if W8 D5 仍未 confirm)
  - C2 W8 D2-D3 real msal_provider wire(F1.2 + F1.3 — H2 vendor ask-and-approve cycle 預期 direct approve since msal SDK within Tier 1 vendor scope per architecture.md §3.2)
  - C3 W8 D4 LIVE switch + F1.7 LIVE smoke(F1.4 + F1.5)
  - C4 W8 cost dashboard data source(F5.1 + F5.2)
  - C5 F3.5 + F4.5 LIVE smoke deferred from W7(F4.1 + F4.2)
  - C6 F5.3 Citation card mobile UX 仍 deferred(C10 not yet built)
  - C7 F5.5 Pixel diff snapshots W8 polish window install
  - C8 Documents/chunks/eval/screenshots/debug routes auth wire(F4.4)
  - C9 Plan estimate calibration applied
  - C10 Real Langfuse SDK wire(F5.1)
- **W8 critical path identification**:**Q11 IT operational confirm cascade trigger W8 D1**;F1.1 IT engagement = F1.2-F1.5 cascade gate;若 W8 D5 仍未 confirm → R-B1 escalation Stakeholder + IT manager 三方
- **Beta deploy phase entry**:W7 closes Tier 1 12-week sprint Beta hardening Sprint 1;W8 = Beta deploy Sprint 2(Azure deploy + real Entra ID + LIVE smoke cascade);W9-W10 = Beta internal testing;W11-W12 = staged rollout 25% → 100% production launch per architecture.md §6.1 timeline

### Decisions / OQ summary

- W7 closeout PASS verdict landed(G1'-G7 全 PASS — 8 G's verified;W7 retro 7 sections complete;F1.1 + F1.7 + F3.5 + F4.5 + F5.3 + F5.5 properly deferred with rationale)
- Q11 unchanged decision-level Resolved 2026-05-05(W6 D5 stakeholder approval cycle);W8 D1 IT operational cascade trigger 是 W8 D1 critical path
- W7 commits = 10(W7 D1+D2+D3+D4+D5 progressive batches each `feat` + `docs(planning) backfill` pair)

### Open / blocked

- ⏸ W8 D1 implementation start awaiting Chris W7 closeout sign-off + W8 D1 kickoff approval + Q11 IT operational confirm
- ⏸ W8 plan/checklist status `draft → active` flip W8 D1 trigger

### Commit reference

- W7 D5 closeout commit `_(pending)_`(W08 phase folder included in W7 closeout batch per F6.3 acceptance)

---

## Day 1 — 2026-05-19: W8 phase active flip + F2.1 Dockerfile finalize + F2.2 ACA Bicep spec

**Action**:W8 D1 implementation kickoff — W8 frontmatter `draft → active`(W7 D5 closeout PASS G1'-G7 verdict landed);F2.1 multi-stage Dockerfile + non-root user + HEALTHCHECK;F2.2 ACA backend.bicep declarative spec(no actual deploy this session per Chris infra ownership)。**F1.1 Q11 IT engagement** — external Chris dependency in-progress;non-blocking for F2/F3/F4/F5 dev work per W7 a-revised mock auth strategy preserved。

**Backend(C12)**:
- `backend/Dockerfile` — multi-stage rewrite:
  - Stage 1 `builder` — Python 3.12-slim + uv installs deps into `/opt/venv`;dep manifests copied first for layer cache reuse across code-only changes
  - Stage 2 `runtime` — slim image,non-root `ekp` user UID 10001 / GID 10001(off host typical [1000, 9999] range to avoid bind-mount UID clash);minimal system pkg(`curl` only for HEALTHCHECK probe)
  - HEALTHCHECK `curl -fsS http://127.0.0.1:8000/health` interval=30s timeout=5s start-period=15s retries=3(allows lifespan Azure SDK warm-up)
  - PATH + PYTHONPATH baked;UID-aware COPY chown
  - CLAUDE.md §5.5 H5 — secret bake-in 防止 via .dockerignore + Settings runtime read
- `backend/.dockerignore` — extended with `.env*` + `*.pem` / `*.key` / `*.pfx` H5 enforcement(`.env.example` 留 whitelist)

**Infra(C12)**:
- `infrastructure/aca/backend.bicep` NEW — Container App declarative spec:
  - Internal ingress `external: false`(Front Door + Auth gate upstream)+ targetPort 8000
  - User-assigned Managed Identity for Key Vault Secrets User role
  - 6 secrets via `keyVaultUrl:` references(NEVER plain-text):AZURE_OPENAI_API_KEY / AZURE_SEARCH_ADMIN_KEY / COHERE_API_KEY + 3 Entra ID(TENANT_ID / CLIENT_ID / CLIENT_SECRET)
  - Resources 1 vCPU + 2 GiB(architecture.md §9 cost row)
  - Liveness + Readiness probes both `/health`,separate so slow lifespan 唔 kill replica
  - Autoscale 1-5 replicas;HTTP concurrency target 30(architecture.md §8.1 R5 paired app-level `rate_limit_concurrent=5/user`)
  - `FEATURE_AUTH_MOCK=false` env var(W8 D4 LIVE switch ready;mock dev mode `.env`-only past W8)
- `infrastructure/aca/README.md` NEW — pre-requisite list(Chris infra setup outside W8 D1 AI scope):resource group + ACA managed environment + ACR + Key Vault + Managed Identity + 6 secrets;manual `az deployment group create` reference(production via W8 D2 GHA F2.3)

**Verification**:
- 269/269 backend pytest pass(W7 closeout baseline preserved;Dockerfile changes 屬 build-time,zero runtime regression)
- Bicep spec `az bicep build` syntax-check pending Chris infra session(declarative spec;no `az` CLI invocation this session)
- `.dockerignore` H5 audit:`.env*` + secrets gitignored AND dockerignored;`.env.example` whitelisted

**Karpathy §1 alignment**:
- §1.1 think-before-coding:Dockerfile multi-stage saves runtime image size(builder + uv stripped);non-root UID 10001 chosen to avoid host UID range clash;HEALTHCHECK start-period=15s based on lifespan AzureOpenAIEmbedder + HybridSearcher + Synthesizer + CragGrader concurrent `__aenter__` warm-up time(empirical W4 D1)
- §1.2 simplicity-first:single Bicep file 一個 backend Container App spec(non multi-resource template);declarative-only,no `az deploy` automation this session(W8 D2 F2.3 GHA pipeline cascade);.dockerignore positive-list extension matches root .gitignore §5.5 H5 H1 alignment
- §1.3 surgical:Dockerfile rewrite zero impact to backend code paths(runtime entrypoint identical `uvicorn api.server:app` per W1 baseline);ACA spec lives in dedicated `infrastructure/aca/` folder — not mixed with code
- §1.4 goal-driven:Dockerfile + Bicep both verifiable independently(docker build + az bicep build syntax check);no untestable speculation

**Hard constraints check**:
- H1 architecture lock — ✅ no §3 / §4 component change;Bicep spec implements §6.1 W8 deploy + §8.1 R5 autoscale spec
- H2 vendor lock — ✅ Azure Container Apps + Azure Container Registry + Azure Key Vault + Managed Identity 全屬 architecture.md §3.2 stack(zero new vendor)
- H3 Dify reference — ✅ untouched
- H4 Tier 1 boundary — ✅ no Tier 2 滲入
- H5 security & privacy — ✅ Bicep secrets 全 Key Vault references;Dockerfile + .dockerignore enforced no `.env` bake-in;non-root user runtime
- H6 test coverage — ✅ Dockerfile changes 屬 build-time;backend test suite 269 unaffected

### Decisions / OQ summary
- No OQ change(Q11 unchanged decision-level Resolved 2026-05-05;operational IT engagement F1.1 in-progress external)
- No ADR triggered(Bicep spec + Dockerfile rewrite 屬 architecture.md §6.1 W8 deploy implementation;non-architectural amendment per CLAUDE.md §5.1 H1 boundary)

### Open / blocked
- ⏸ **F1.1 W8 D1 Q11 IT operational confirm cascade trigger** — Chris IT engagement in-progress(Tenant Access + App Registration + Owner Identification per `beta-plan-v1.md §2 W8.F1`);若 W8 D5 仍未 confirm → R-B1 escalation per RISK_REGISTER R14 Stakeholder + IT manager 三方
- ⏸ F1.2 + F1.3 backend / frontend real msal SDK wire — W8 D2-D3 trigger(可以開始 W8 D2 即使 F1.1 仍 pending — msal SDK install + JWT validation skeleton implementation 不需要 real cred;real test 推 F1.5 W8 D4)
- ⏸ F2.3 GHA CI/CD pipeline — W8 D2 trigger
- ⏸ F2.4 Azure Key Vault secrets management — W8 D2-D3 trigger(Chris infra setup pre-requisite per `infrastructure/aca/README.md`)
- ⏸ F2.5 ACA networking + Private Endpoint — W8 D2-D3 trigger
- ⏸ F3 SWA frontend deploy — W8 D3-D4
- ⏸ F4 LIVE smoke cascade — W8 D4
- ⏸ F5 cost dashboard + Langfuse SDK wire — W8 D5
- ⏸ F6 closeout — W8 D5

### Commit reference
- _(W8 D1 commit pending — references progress.md Day 1 + checklist F2.1 + F2.2 ticked + frontmatter active flip)_

---

---

## Day 2 — _(pending)_

---

## Day 3 — _(pending)_

---

## Day 4 — _(pending)_

---

## Day 5 — _(pending)_

---

## Retro(填於 W8 D5 末)

### What worked
_(W8 D5 末 fill)_

### What didn't work / unexpected friction
_(W8 D5 末)_

### Surprises / discoveries
_(W8 D5 末)_

### Carry-overs to W09-beta-internal-testing
_(W8 D5 末)_

### ADR triggers
_(W8 D5 末 — ADR-0013 reservation candidate:msal SDK ask-and-approve outcome OR ACA networking topology decision OR Tier 2 trigger)_

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)
- G1-G7:_(W8 D5 末)_
- **W8 Beta deploy verdict**:_(W8 D5 末)_ → ready for W9 Beta internal testing / require additional polish

### Phase status
- Closeout commit:_(W8 D5 末)_
- Frontmatter status flipped to `closed`:_(W8 D5 末)_
- Phase W09 kickoff trigger:_(W8 D5 末 — W9 plan = real query log collection + UX iteration + Q6 Real query collection owner trigger per architecture.md §6.1 W9 row)_

---

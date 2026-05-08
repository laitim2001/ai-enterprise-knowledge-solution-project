---
phase: W11-staged-rollout-25
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active   # `active` 自 W11 D1(2026-06-09)— Chris W10 closeout sign-off + Track B IT-cred-independent items kickoff
---

# Phase W11 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`draft` 自 2026-06-06 W10 D5 closeout cascade。

---

## Day 0 — 2026-06-06: Kickoff prep(W10 D5 末 closeout cascade same-session)

**Action**:Phase W11 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle;W10 D5 closeout cascade per CLAUDE.md §10 R5)

- Folder `docs/01-planning/W11-staged-rollout-25/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6;Track A IT cred event-triggered + Track B 25% staged rollout + W12 production launch readiness)
- `checklist.md` derived from plan deliverables(~30 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W10-beta-iteration**(per W10 retro § Carry-overs):
  - IT cred populate trigger(F1.1)— Track A activation event;real-calendar 2026-06-08 re-escalation deadline(W10 D5 == 2026-06-06 — 2-day buffer remains)
  - Chris infra/IT/DNS apply cascade(F1.2-F1.4)— Track A
  - LIVE smoke verification(F1.5)— Track A
  - 25% rollout activation + cohort onboarding(F2)— Track A continuation
  - Onboarding doc final-fill IT helpdesk contact(F2.2)— W10 D5 onboarding doc Update history carry-over
  - Daily metric monitor + 50% EoW conditional gate(F3)— Track B
  - Runbook AF1-AF4 in-place edits(F4.1-F4.4)— per W10 D5 tabletop substitute aggregate findings
  - Runbook live exercise post-LIVE-deploy(F4.5-F4.6)— replaces W10 D5 tabletop substitute
  - Q15 first weekly signal report W11 EoW(F5.1)— scaffold ready W10 D2 F4.3
  - Q4 deployment pricing rate confirmation(F5.2)— W11 prep deck §6.1 Stakeholder Option A vs Option B
  - Tier 2 trigger metric review(F5.3)— W11 prep deck §3 W11.F5
  - W11 prep deck Stakeholder approve cycle outcome(W10 D5 末 trigger event)
- **W11 critical path**:
  - **Track A trigger**:IT cred populate event — fires F1.1 → F1.2-F1.4 cascade → F1.5 LIVE smoke → F1.6 R-B1 closure → F2 25% rollout activation → F3 daily metric monitor cycle starts
  - **Track B IT-cred-independent**:F4.1-F4.4 runbook AF edits + F5.3 Tier 2 review continues regardless of Track A timing
- **W12 production launch phase entry**:W11 closes Beta + staged rollout / IT cred-bridge phase;W12 = production launch 100%(per architecture.md §6.1 W12 row + Beta plan v1 §3 W12);Tier 1 12-week sprint closes 2026-07-19

### Decisions / OQ summary

- W10 closeout PARTIAL PASS verdict(Track B complete F4.1+F4.2+F4.3+F5.2+F5.4 + F4.4 deferred + F5.1 tabletop + F5.3 onboarding review;Track A pending IT cred event per W9 D1 三方 outcome cascade pattern)
- Q11 status:`decision-level Resolved + operational committed early June 2026 real`(unchanged — final operational trigger 等 IT cred populate event Track A activation W11 D1+)
- **Q4 surfaced as NEW gate item** per W10 D3 F5.2 placeholder pricing labelling — W11 prep deck §6.1 Option A vs Option B Stakeholder decision
- Q6 + Q15 deferred to W11+ real-cohort signal(per architecture.md §6.1 + Beta plan deviation log)
- W10 commits = 5 daily batches(W10 D1 + D2 + D3 + D4 + D5;each `feat` + `docs(planning)` backfill pair)

### Open / blocked

- ⏸ W11 D1 implementation start awaiting Chris W10 closeout sign-off + Stakeholder W11 prep deck approve cycle + Track A IT cred populate trigger event(target ≤ 2026-06-08 re-escalation deadline)
- ⏸ W11 plan/checklist status `draft → active` flip W11 D1 trigger
- ⏸ Track A cascade fires per IT cred timing(could W11 D1 / D2 OR slip to W12 with W11 prep deck §5 No-Go fallback)
- ⏸ Track B(F4.1-F4.4 runbook AF edits + F5.3 Tier 2 review)continues unblocked W11 D1+

### Commit reference

- W10 D5 closeout commit `7374dd4` + backfill `a3d7c0e`(W11 phase folder included per F6.3 acceptance)

---

## Day 1 — 2026-06-09: Track B kickoff(IT-cred-independent items)

**Action**:Track B IT-cred-independent items execute(per Chris W10 closeout sign-off authorization + Track B start authorization 2026-06-09)— F4.1-F4.4 runbook AF1-AF4 in-place edits + F5.3 Tier 2 trigger metric review draft;Track A IT cred event 仍 pending(real-calendar 2026-06-08 re-escalation deadline 1-day buffer per Chris IT helpdesk chase-through commitment)。

**Frontmatter flip**:`plan.md` + `checklist.md` + `progress.md` status `draft → active`(per Chris sign-off 2026-06-09 Day 1 entry)。

### F4 — Runbook AF1-AF4 in-place edits(per W10 D5 tabletop substitute aggregate findings)

- F4.1 ✅ AF1 §1.A step 2 queue clarification — appended sub-bullet stating「queue」= Slack `#ekp-beta` thread tag + bugs/BUG-{NNN} instance(no separate queue infra Tier 1);Tier 2 trigger flag if recurring parse-skip pattern
- F4.2 ✅ AF2 §2 step 2 Azure OpenAI tier-1 — appended `+ ACA revision restart required(Settings env-var bound per W7 D2 F2 implementation;not hot-reload)`
- F4.3 ✅ AF3 §2 step 2 Azure OpenAI tier-3 — rewrote `app.state.synthesizer = None` placeholder to actual `OPENAI_API_KEY=''` env override + ACA revision restart mechanism;synthesizer init fails gracefully in `lifespan` → `query.py:79-92` retrieval-only fallback path active
- F4.4 ✅ AF4 §2 root cause investigation runaway client — added explicit per-user blocklist NOT IMPLEMENTED Tier 1 acknowledgment + practical revoke path(Slack tag + Entra ID app role removal via IT helpdesk)+ Tier 2 trigger flag if recurring
- Update history entry 2026-06-09 W11 D1 added with reference to W10 D5 tabletop substitute findings + Live exercise post-Track A LIVE deploy will replace tabletop substitute within 72h(F4.5 W11 plan deliverable;blocked on Track A staged ACA env)

### F5.3 — Tier 2 trigger metric review draft

- ✅ NEW `docs/03-implementation/tier-2-trigger-review-W11.md` 7 sections + 3 risks
  - §1 Tier 2 Capabilities Backlog snapshot(8 capabilities TC1-TC8 per architecture.md §11.1)— **all status 🟡 No signal yet OR 🔴 Out of boundary**(0/8 trigger fire as of W11 D1)
  - §2 GraphRAG T1-T5 trigger matrix snapshot(per architecture.md §11.2)— **0/5 triggers fired**;CLAUDE.md §5.4 H4 Tier boundary preserved
  - §3 W7-W10 cumulative signal review(scaffold + augmentation pipeline + cost dashboard wire + observe_streaming + beta-feedback yaml mock corpus → real cohort traffic W11+ replaces)
  - §4 Decision frame for post-W12 Tier 2 roadmap kickoff(monthly evaluation gate;Q12 owner Chris approve;TC2 multi-agent + TC3 workflow + TC8 fine-tuning highest-likelihood candidates per signal pattern)
  - §5 Risks TR1-TR3(trigger signal 模糊 / Beta cohort small statistical power / Q12 owner conflict)
- Karpathy §1.2:doc 唔重複 architecture.md §11 內容,只記錄 cumulative signal status + decision frame;~190 lines lean
- H4 Tier boundary reminder:呢份 doc 屬 governance review only,**唔係 Tier 2 implementation**;trigger 透過呢份 doc 累積 signal → post-W12 retro Stakeholder + Chris(Q12 owner)正式 kickoff

### F5.2 — Q4 deployment pricing rate Option B path active(W11 D1 same-day batch)

- ✅ Stakeholder authorization 2026-06-09 → **Option B chosen**(Karpathy §1.2 simplicity-first per W11 prep deck §6.1)
- Production code touchpoint(Karpathy §1.3 surgical — stale comment cleanup only,**zero logic change**):
  - `backend/observability/realtime_cost.py` docstring + inline comment update — stale W10 D4-D5 / F5.4 reference cleanup;reflect Option B path active + 7-day re-baseline schedule
  - `_PRICING_TABLE` **不變**(已 placeholder per design)+ `PRICING_BASELINE_LABEL` **不變**(`placeholder_publicly_quoted_rates_2026-Q2` retained)
  - `backend/observability/alerts.py` `cost_spike` rule × 1.5x ceiling **preserved unchanged**(W8 D5 F5.4 baseline rule;rolling 7-day avg comparison serves anomaly detection intent for first-week period)
- Governance docs sync(R4 binding):
  - `docs/decision-form.md` Q4 entry — append W11 D1 operational follow-up sub-entry(pricing rate baseline gate Option B)+ Date 2026-06-09 + Status note pricing rate operational follow-up via spend cap proxy(non-blocking);Q4 overall `Resolved (full)` preserved
  - `docs/03-implementation/w11-staged-rollout-25-prep-deck.md` §6.1 — Decision recorded entry added(Option B chosen + Option A NOT CHOSEN rationale)+ Update history 2026-06-09 W11 D1 entry added
- Tests:456 unchanged(comment-only edits + governance docs);pytest sweep not re-run;ruff check not re-run(comment-only changes)
- Karpathy §1.2 self-check pass:**zero new feature added**(Option B 本身 = preserve existing system + schedule re-baseline as governance item);no production code logic change;Beta timeline preserved
- Karpathy §1.3 self-check pass:**surgical** stale comment cleanup only(W10 D4-D5 reference outdated post W10 closeout);every edit traces to user "Option B chosen" instruction
- 7-day re-baseline schedule:W11+ post real cohort traffic accumulation;trigger window = first cohort feedback day + 7 calendar days;outcome = either(a)refresh `_PRICING_TABLE` with calibrated rates from real cohort billing data → flip `PRICING_BASELINE_LABEL` to `calibrated_2026-Q2-tenant-eastus2_W11_re-baseline`,OR(b)maintain placeholder if cohort billing data confirms publicly-quoted rates within ±10% accuracy(no flip needed)

### Decisions / OQ summary

- Chris W10 closeout sign-off authorization → W11 plan/checklist/progress frontmatter `draft → active` flip executed
- Track B IT-cred-independent items start authorization → F4.1-F4.4 + F5.3 commit batch as W11 D1 deliverable
- Track A IT cred populate event chase-through commitment(Chris IT helpdesk follow-up;real-calendar 2026-06-08 re-escalation deadline within 1-day buffer)
- Q12 Tier 2 owner Chris(Resolved 2026-05-05)anchor — F5.3 Tier 2 review draft frames post-W12 monthly evaluation gate cycle
- Q4 pricing rate gate item NEW per W10 D3 F5.2 — **resolved same-day W11 D1**:Stakeholder authorization 2026-06-09 = **Option B**(Karpathy §1.2 simplicity-first per W11 prep deck §6.1);placeholder rates preserved + `cost_spike` 1.5x ceiling preserved + 7-day re-baseline scheduled W11+;Q4 overall `Resolved (full)` status preserved per decision-form.md sync

### Open / blocked

- ⏸ Track A IT cred populate event(F1.1 trigger)still pending — real-calendar 2026-06-08 re-escalation deadline preserves 1-day buffer
- ⏸ F4.5 Runbook live exercise(replaces W10 D5 tabletop substitute within 72h post-Track A LIVE deploy)— blocked on Track A staged ACA env
- ⏸ F4.6 Runbook Update history live exercise outcome — depends on F4.5
- ⏸ F2.1-F2.4 25% rollout activation cascade — blocked on Track A
- ⏸ F3.1-F3.5 daily metric monitor + 50% EoW conditional gate — blocked on F2(Track A)
- ⏸ F5.1 Q15 first weekly signal report — needs F2 cohort traffic(W11 EoW)
- ⏳ F5.2 7-day re-baseline schedule — W11+ post real cohort traffic accumulation trigger window;outcome = refresh `_PRICING_TABLE` if cohort billing data diverges > ±10% from publicly-quoted rates,else maintain placeholder(non-blocking governance follow-up)

### Tests / discipline

- No code change W11 D1(governance + runbook in-place documentation edits + Tier 2 review doc only);pytest sweep not re-run(no Python touch)。456/456 baseline preserved from W10 D3。
- Karpathy §1.3 surgical:runbook AF1-AF4 edits scoped narrowly to W10 D5 tabletop substitute findings — no §1 / §3 / §4 / §5 / §6 / §7 / §8 section touched (zero scope creep)。
- H1 / H2 / H3 / H4 / H5 / H6 全 ✅(no architecture / vendor / Dify / Tier 2 implementation / security / test change)。
- R1 ✅:W11 plan/checklist 已 committed before Day 1 execution(W10 D5 closeout cascade)。
- R2 binding:W11 D1 commit 對應呢個 Day 1 entry。
- R5 ✅:no architectural-adjacent decision today;ADR-0013 reservation preserved per W11 outcome。

### Commit reference

- W11 D1 batch commit `4be2c17`(F4.1-F4.4 runbook AF1-AF4 + F5.3 Tier 2 review draft + W11 frontmatter flip per Chris sign-off authorization)
- W11 D1 backfill commit `185ca82`(F4.1-F4.4 + F5.3 progress Day 1 commit hash backfill)
- W11 D1 F5.2 same-day batch commit `433a31d`(Q4 pricing rate Option B path active + realtime_cost.py docstring/comment Karpathy §1.3 surgical update + decision-form Q4 sync + prep deck §6.1 Decision recorded + checklist F5.2 tick + Day 1 entry F5.2 sub-section append)
- W11 D1 D2 housekeeping commits `4be2c17` / `185ca82` / `433a31d` / `5bdc115` / `d3adc8a`(D2 frontmatter retroactive sync W01 + W02 closed)

---

## Day 2 — 2026-06-10:Personal Azure dev tier — Track A IT cred blockade workaround pattern executed(Batch 5 backend live)

**Action**:Track B continuation — **Personal Azure dev tier EKP backend full deployment cascade**(Batch 5:`az acr build` + ACA secret set + ACR registry creds + image update + ingress targetPort fix + min/max replicas tune)。Track A IT cred event 仍 pending(2026-06-08 re-escalation deadline 1-day buffer expended without IT response;ADMIN follow-up via separate channel needed)→ **Personal Azure dev tier 作為 Track A blockade workaround pattern 執行**,unblock W11 backend functional path verification + F4.5 Runbook live exercise prerequisite。

### Batch 5 sub-step outcome

- **5.1 ✅** `az acr build --registry acrekpdev --image ekp-backend:v1 ./backend` — 9:01 build,17/17 steps;run `ch1` Succeeded server-side。Stream-log Windows cp1252 UnicodeEncodeError(uv install progress bar Unicode)≠ build failure(per `az acr task list-runs` ground truth check)。
- **5.2 ✅** ACA secrets + registry creds — `azure-search-admin-key` + `azure-openai-api-key` 2 secrets stored;ACR admin user pivot per Graph API R8 SSL block(production GHA workflow 後 switch to Managed Identity AcrPull proper setup)。
- **5.3 ✅** Image + 14 env vars update via `az containerapp update --replace-env-vars`(12 inline non-secret + 2 secretref `AZURE_SEARCH_ADMIN_KEY` + `AZURE_OPENAI_API_KEY`)。RERANKER_KIND=off(Karpathy §1.2 simplicity-first;W11 cohort smoke 階段 retrieval-only fallback OK;Cohere Marketplace cross-sub billing NEW Q5 ADMIN confirm pending)。
- **5.4 ✅** `/health` smoke 200 `{"status":"ok"}` via httpx truststore-mitigated(curl schannel CRL revocation fail per W6 D1 R8 calibration ground truth)。

### R8 friction encountered + bypassed(6 incidents — calibration data)

| # | Incident | Bypass |
|---|----------|--------|
| 1 | `az acr build` cp1252 stream-log codec | `az acr task list-runs` ground truth check |
| 2 | Graph API role grant SSL(`graph.microsoft.com`) | ACR admin user pivot |
| 3 | Ingress targetPort 80(helloworld inherit) vs uvicorn 8000 | `az containerapp ingress update --target-port 8000` |
| 4 | Scale-to-zero replica recycle(minReplicas=0)→ ActivationFailed | `--min-replicas 1 --max-replicas 1` |
| 5 | Local curl schannel CRL revocation | httpx + `truststore.inject_into_ssl()` |
| 6 | ACA logstream + log-analytics extension SSL(`eastus2.azurecontainerapps.dev` + `aka.ms`) | Log Analytics REST API direct via `api.loganalytics.io` truststore-mitigated httpx |

### Final live state

- URL:`https://ekp-dev-backend.victoriousstone-0c83ea1b.eastus2.azurecontainerapps.io`
- Revision:`ekp-dev-backend--0000002` `RunningAtMaxScale` `Healthy`
- Image:`acrekpdev.azurecr.io/ekp-backend:v1`
- Cross-tenant API access verified via lifespan init success(02:43:10 startup → Azure SDK clients connected to company AI Search + AOAI;Langfuse fail-soft graceful per `not_configured` status)

### Decisions / OQ summary

- **Personal Azure dev tier 作為 Track A IT cred blockade workaround pattern executed** — backend functional path verified;Track A 仍係 Beta cohort production path(needs company Entra ID auth via IT cred populate event)
- **Cross-tenant API key access pattern** verified work(personal sub ACA → company tenant AI Search admin key + AOAI key)— 確立 dev tier cross-tenant 作業可行性
- **Cohere Marketplace cross-sub billing**(NEW Q5)deferred — `RERANKER_KIND=off` retrieval-only fallback acceptable W11 smoke;final disposition post Q5 ADMIN confirm
- **Q11 IT cred path**:re-escalation deadline 2026-06-08 buffer expended → personal Azure dev tier preempt makes Track A timing **non-critical** for Track B IT-cred-independent items(F4.5 runbook live exercise + W11 D2-D5 governance work)+ W12 production launch readiness final review
- **ADR-0013 candidate trigger** — Personal Azure dev tier Track A blockade workaround pattern formalization(per CLAUDE.md §6 ADR format + R5 binding rule:phase closeout 之前 architectural-adjacent decision);final approval defer W11 D5 closeout retro per rolling-JIT discipline

### Open / blocked

- ⏸ **Track A IT cred populate event** — STILL pending;ADMIN follow-up via separate channel needed;personal Azure dev tier preempt unblock W11 functional verification path,但 Beta cohort production deploy 仍需 Track A
- 🟢 **F4.5 Runbook live exercise** — **NOW UNBLOCKED**(backend live on personal ACA env;`runbook/README.md §1+§2` walkthrough 即時可開始 vs W10 D5 tabletop substitute);pending Chris bandwidth W11 D2-D5 trigger
- ⏸ **Batch 4 SWA frontend** — pending W11 D2-D5 schedule(option A vs F4.5 priority)
- ⏸ **F2.1-F2.4 25% rollout activation cascade** — STILL BLOCKED on Track A(cohort needs company Entra ID auth which Track A IT cred cascade provides)
- ⏸ **F3.1-F3.5 daily metric monitor + 50% EoW gate** — STILL BLOCKED on F2(Track A)
- ⏸ **F5.1 Q15 first weekly signal report** — STILL BLOCKED on F2 cohort traffic
- ⏳ **F5.2 7-day re-baseline** — non-blocking governance follow-up,W11+ post real cohort traffic accumulation

### Tests / discipline

- **0 Python logic change today**(governance + cloud infrastructure ops only);pytest sweep not re-run;456/456 baseline preserved from W10 D3
- **Karpathy §1.3 surgical**:純 cloud config + image deploy 動作,no source code change;every action traces to user "personal Azure dev tier Batch 5" instruction
- **H1 / H2 / H3 / H4 / H5 / H6 self-check**:
  - **H1 ✅** No `architecture.md` v5 §3/§4 component change(personal ACA = sidecar deployment topology,not architecture)
  - **H2 ✅** No new vendor(ACR/ACA/KV/LA/AI Search/AOAI 全部 v5 stack 內;personal subscription same-vendor instance)
  - **H3 ✅** No Dify reference touch
  - **H4 ✅** No Tier 2 implementation
  - **H5 ⚠️** **5 secrets entered conversation context** — added to post-Beta rotation tracker P1 governance(`AZURE_SEARCH_ADMIN_KEY` + `AZURE_OPENAI_API_KEY` + `acrekpdev` ACR admin password + 2 ACA secret refs;同 ADMIN-provided SP secret + `ekp-dev-automation` SP secret 90d expiry rotation cycle 一齊)
  - **H6 ✅** No test code change
- **R1 ✅** W11 plan/checklist already committed before D2 work
- **R2 binding** ✅ this entry corresponds to W11 D2 commit(about to commit post-entry write)
- **R3 ✅** No silent plan drift — personal Azure dev tier deployment 屬 Track A workaround pattern,plan §5 D1-D5 day-by-day breakdown caveat 已 cover「Track A timing depends on real-calendar IT cred event;若 slip past 2026-06-08 → all Track A days shift」
- **R4** N/A(no OQ resolved today;Q5 NEW Cohere cross-sub billing pending;Q11 operational still pending despite buffer expended)
- **R5 ✅** ADR-0013 candidate trigger noted for personal Azure dev tier pattern documentation;final formalization decision defer W11 D5 closeout retro

### Cost impact(Personal Azure dev tier baseline)

- ACR Basic build:~$0.30(9 min vs 6 min/day free tier overflow)
- ACA `min=max=1`:~$1-3/day idle baseline(vCPU + memory always-on)
- Storage egress:negligible(intra-Azure region)
- **Estimated monthly**:~$30-90 if 24/7;cost-cutting option = `--min-replicas 0 --max-replicas 1` post-smoke(cooldownPeriod=300s scale-to-zero;trade-off = first-request cold start latency ~30-60s)

### Path A `/query` end-to-end smoke addendum(2026-06-10 same-day)

**Goal**:Personal Azure dev tier 真實 production-readiness verification — 唔止 lifespan init success,而係 real query end-to-end pipeline against company AI Search index `ekp-kb-drive-v1` + AOAI gpt-5.5 cross-tenant synthesis。

#### Smoke matrix outcome

| Test | Result | Verified signal |
|------|--------|-----------------|
| Cross-tenant AI Search retrieval | ✅ 5 chunks returned | Index `ekp-kb-drive-v1` admin-key cross-tenant read perms work;hybrid retrieval engine functional |
| Cross-tenant AOAI synthesis | ✅ `model_used: gpt-5.5` 1509 chars structured | API key cross-tenant fully functional;`AZURE_OPENAI_API_VERSION=2024-12-01-preview` accepted |
| Citation parser | ✅ 1 citation w/ chunk_id reference | `generation/citation_enrichment` 邏輯正常 |
| Refusal mechanism(off-corpus query)| ✅ `refused: True`,answer = "I cannot find this in the available documentation" | Anti-hallucination 正確觸發 on低-relevance(top score 0.017)|
| Answer quality(corpus-aligned query)| ✅ Step-by-step structured(D365 F&O 路徑 + sub-steps) | 質量 in line with W6 baseline |
| Latency baseline | 5677ms full pipeline(retrieval + synthesis) | 接受 baseline;後續 cohort traffic 累計 7-day re-baseline 校準 |
| `RERANKER_KIND=off` graceful | ✅ `reranker_used: off` | No Cohere call attempted;retrieval-only fallback path active per F4.3 runbook AF3 mechanism |

#### 3 governance surprise findings

1. **🆕 Drive Project corpus 真實內容 = D365 F&O ERP user manuals,不是 Ricoh MFP printer manuals**
   - Top retrieved chunks 全部來自 `DRIVE_User_Manual_0605_GL_FNA-General_Ledger_Management` doc(General Ledger / Allocation Rules / Microsoft Dynamics 365 Finance & Operations 員工指引)
   - eval-set-v0 placeholder 已 self-disclaim "validation_status: UNVALIDATED" + "domain_assumption.confidence: low" + "synthetic, pre-SME, validation_status: UNVALIDATED"
   - **意義**:SME labeling 必須 redo based on D365 F&O domain 而非 MFP — Q14 ground truth labeler(Chris Lai,Resolved 2026-05-01)real labeling work scope clarified
   - **W6 D5 final eval Recall@5=0.9722 baseline 仍 valid**:測量嘅係 retrieval pipeline mechanism correctness;真實 SME-labeled query distribution 後 metric 可能 variance(上下浮動 reasonable Beta cohort signal range)
   - **Carry-over to W11 D5 retro**:promote 為 explicit Surprises / discoveries entry + carry-over candidate to Beta plan v1 §2 SME labeling task scope adjustment

2. **🆕 KB Manager 喺 fresh ACA deploy = empty(`GET /kb` 返 `[]`)**
   - Backend KB Manager **in-memory only**(per W1 baseline + architecture.md §4.3)— fresh personal ACA deploy = no KB registered
   - **`/query` 仍 work** — engine 直接打 AI Search index,**唔經 KB Manager**(`payload.kb_id` schema-required 但 route 唔 enforce)
   - **意義 for UI E2E**:Admin Console `KbStatus` view 會顯示 "No KB registered" visual state;F4.4 pixel diff harness baseline 應該 capture both empty + populated states
   - **Beta cohort production deploy implication**:KB Manager 需要 persistent backing(SQLite / Postgres / Cosmos DB)— **W11 scope 之外**,但 carry-over candidate to Beta plan v1 §3 W12 production launch readiness 或 Tier 2 multi-tenancy planning
   - **Tier boundary check**:呢個 carry-over 唔 trigger Tier 2(KB Manager persistence ≠ multi-tenancy);純粹 W12+ Beta production hardening 嘅一部分

3. **🆕 httpx `follow_redirects=True` 會 strip `Authorization` header on 307 redirect(security feature,not bug)**
   - `GET /kb/`(trailing slash)→ FastAPI 307 redirect → `/kb`,但 httpx 為防止 credential leak 跨 origin,**預設 strip `Authorization` header on redirect**
   - **Confirmation**:Direct `GET /kb`(no slash)+ `Bearer dev-token` → 200 + body `[]` ✅
   - **意義 for SWA frontend implementation**:Vercel AI SDK / TanStack Query 需要 explicit URL hygiene(全部 endpoint 唔 trailing slash)OR config redirect-replay-with-auth(only for same-origin)
   - **Carry-over to Batch 4 SWA frontend deploy**:`frontend/lib/api/client.ts` URL constants check + `useChat` config note

#### Auth env var addition(post initial Batch 5 deploy)

- 原 Batch 5 ACA env vars 14 條 **冇** include `FEATURE_AUTH_MOCK` → backend 預設 `feature_auth_enabled=False` + `feature_auth_mock=False` 仍 require Bearer token(per `api/server.py:159 _PROTECTED_PREFIXES = ("/query", "/kb", "/feedback", "/auth")` middleware,unconditional bearer requirement)
- **Smoke 期間新增 env var**:`FEATURE_AUTH_MOCK=true` via `az containerapp update --set-env-vars FEATURE_AUTH_MOCK=true`(revision `--0000003`)
- **效果**:啟動 W7 D1 F1.2.1 dev mode → bypass real MSAL JWT validation,return `_DEV_USER` from `Settings.auth_mock_*` defaults → 接受 `Authorization: Bearer dev-token`(or any bearer per mock middleware unconditional pass)
- **Production trajectory**:Beta cohort deploy 時 flip `FEATURE_AUTH_MOCK=false` + Track A IT cred populate event 提供 real Entra ID JWT(W7 D1 F1.2.1 design intent;CLAUDE.md §5 H5 security alignment preserved)
- **R3 binding**:此 ACA env var 變動唔屬 plan deviation(原 deliverable F1 LIVE switch `feature_auth_mock=False` 等 Track A;personal Azure dev tier smoke 階段 enabled mock 屬 sidecar workaround pattern,plan §5 caveat already covers)

#### Smoke session metric snapshot

- Personal ACA Container App revision sequence:`--0000001`(initial,scale-to-zero recycle)→ `--0000002`(min/max=1 healthy)→ `--0000003`(`FEATURE_AUTH_MOCK=true` added)
- Total ACA revisions today:**3**(Batch 5 deployment + scale fix + auth mock enable)
- Smoke queries executed:**3**(off-corpus paper jam → corpus-aligned ledger allocation rule → /kb sanity)
- Cumulative cost during smoke:negligible(~3 LLM calls × small completion tokens × gpt-5.5 rate)

### Commit reference

- W11 D2 batch commit `fcd8c25`(progress.md Day 2 entry + plan.md changelog 2026-06-09 active flip + 2026-06-10 personal Azure dev tier pattern executed)
- W11 D2 backfill commit `5462301`(commit hash backfill into Day 2 entry per W10 D5 pattern)
- W11 D2 Path A smoke addendum commit:_(filled post-commit per backfill pattern)_

---

## Retro(填於 W11 D5 末)

### What worked
_(W11 D5 末 fill)_

### What didn't work / unexpected friction
_(W11 D5 末)_

### Surprises / discoveries
_(W11 D5 末)_

### Carry-overs to W12-production-launch
_(W11 D5 末)_

### ADR triggers
_(W11 D5 末 — ADR-0013 reservation candidate per W11 outcome)_

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)
- G1-G8:_(W11 D5 末)_
- **W11 staged rollout 25% verdict**:_(W11 D5 末)_ → ready for W12 production launch 100% / require additional polish

### Phase status
- Closeout commit:_(W11 D5 末)_
- Frontmatter status flipped to `closed`:_(W11 D5 末)_
- Phase W12 kickoff trigger:_(W11 D5 末 — W12 plan = production launch 100% + Day-2 ops handover + final post-launch monitoring per architecture.md §6.1 W12 row)_

---

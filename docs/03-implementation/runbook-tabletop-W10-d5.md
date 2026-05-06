---
artifact: runbook-tabletop-walkthrough
phase: W10-beta-iteration
status: tabletop-substitute        # `tabletop-substitute` 自 W10 D5 2026-06-06(Track A staged ACA env unavailable)
target_live_exercise: W11+ post-Track A IT cred populate trigger
prepared_by: Chris(walkthrough)+ AI(scribe + clarification probe)
related_artifacts:
  - infrastructure/runbook/README.md
  - docs/01-planning/W10-beta-iteration/plan.md §2 F5.1
  - docs/03-implementation/w11-staged-rollout-25-prep-deck.md §5(no-go fallback for runbook exercise)
last_updated: 2026-06-06
---

# Runbook Real-Incident Tabletop Substitute(W10 D5 F5.1)

> **Why tabletop instead of live exercise**:F5.1 W10 plan §2 acceptance requires walking through `runbook/README.md §1 + §2` against staged ACA env;Track A LIVE deploy cascade still pending IT cred populate event(real-calendar W10 D5 = 2026-06-06;target window 2026-06-02 to 2026-06-07;re-escalation deadline 2026-06-08)。Per W11 prep deck §5 No-Go Fallback,**tabletop exercise = approved substitute** when staged ACA unavailable;live exercise within 72h post-Track A LIVE deploy。
>
> **Karpathy §1.2 simplicity-first**:呢份 doc 唔重複 runbook 內容,只記錄(a)tabletop walkthrough findings + (b)inline clarifications surfaced + (c)gaps to re-validate live。
>
> **Re-trigger condition**:Track A IT cred populate event fires → staged ACA env online → live exercise replaces this tabletop substitute within 72h(W11 D1+ scope)。

---

## 1. Tabletop Method

Chris walks through each scenario's 4-step structure(Symptoms → First-line mitigation → Root cause investigation → Rollback / recovery)while AI probes for unclear / missing / hand-wavy steps。Each step gets a verdict:
- ✅ **Clear**:procedure self-contained;oncall can execute without further clarification
- 🟡 **Clarification needed**:procedure references resources / commands that need elaboration before live execution
- 🔴 **Gap**:missing step / decision branch / fallback that must be added before live exercise

**Non-goals for tabletop**:cannot exercise actual `az containerapp exec`,actual Langfuse trace filtering,actual Azure portal navigation。**Live exercise** post-Track A validates these。

---

## 2. Scenario §1 — Document parse failure(walkthrough)

### Symptoms section ✅ Clear

Symptom set complete:Admin Console KB management page status,audit log `audit_action`,Langfuse `stage_failed` event,specific error types(`PageBudgetExceededError` / `DoclingError` / `PptxNotSupportedFormat`)。Oncall can map an incoming alert to scenario §1 within 30 sec。

### First-line mitigation ✅ Clear with 1 clarification

§1.A path(single doc skip)+ §1.B path(全 docs fail)bifurcation is intuitive:
- Step 1 verify scope is **immediately actionable**(check Admin Console for scope counter)
- §1.A path gives non-destructive fallback(`enabled=False` PATCH preserves data for reprocess)
- §1.B path escalates correctly to §6.1(rollback)or §2(API quota path)

🟡 **Clarification surfaced**:**§1.A step 2「Document the doc_id + filename for offline re-process queue」**— where does「offline re-process queue」live?Tabletop verdict:does NOT explicitly exist as a system queue;in practice,oncall logs the doc_id + filename to a Slack `#ekp-beta` thread + opens a `bugs/BUG-{NNN}-doc-parse-skip-{kebab}` instance per PROCESS.md §4 Bug-fix workflow。**Action item to land before live exercise**:add note line in runbook §1.A step 2 — `"queue" = (a) Slack #ekp-beta thread tag + (b) bugs/BUG-{NNN} instance — no separate queue infra exists in Tier 1`。

### Root cause investigation ✅ Clear

Langfuse filter query(`stage=parser.* status=error past 1h`)+ Azure Monitor KQL syntax(`AppTraces | where Properties.stage startswith "parser"`)both executable verbatim。「Common causes」list maps cleanly to architecture.md §8.3 R7 + error-cases-E1-E14.md §E9-E11。

### Rollback / recovery ✅ Clear

Per-doc skip / re-ingest after fix(`POST /kb/{kb_id}/documents/{doc_id}/reindex`)/ mass re-ingest off-peak — three-tier fallback structure good。Cost estimate inline(`~$0.01 per 1k chunks`)useful for Stakeholder sign-off on mass re-ingest。

### §1 verdict ✅ READY for live exercise(post-Track A)
- 1 clarification deferred to runbook §1.A step 2 in-place edit before live run
- All other steps actionable as-is

---

## 3. Scenario §2 — API quota exhaustion(walkthrough)

### Symptoms section ✅ Clear

Audit log signature + Synthesizer log `RateLimitError` + cost dashboard `api_error_rate` rule(architecture.md §7.4)+ Beta cohort UX symptom("Service temporarily unavailable")— full coverage。

### First-line mitigation ✅ Clear with 2 clarifications

Three-quota differentiation correct:
- Azure OpenAI quota:tier-1(rate limit tighten 50→25)+ tier-2(quota increase request)+ tier-3(disable synthesizer fallback to W2 baseline retrieval-only mode per `query.py:79-92`)— this is **Karpathy §1.2 graceful degradation pattern**,exercise PASS
- Cohere quota:env override `Settings.reranker_kind="azure"` + ACA revision restart;Cohere Marketplace auto-refill 1h
- Azure AI Search quota:S1 → S2 OR partition increase(15-30 min provision)

🟡 **Clarification 1**:**「reduce `synthesizer_call` rate by tightening `Settings.rate_limit_per_minute` from 50 → 25」**— is this a hot-reload setting or requires ACA revision restart?Tabletop verdict:`Settings` 透過 env var bind,changes require ACA revision restart per W7 D2 F2 implementation。**Action item**:append to runbook §2 step 2 Azure OpenAI tier-1 — `"+ ACA revision restart required (Settings env-var bound;not hot-reload)"`。

🟡 **Clarification 2**:**「Tier-3 fallback:disable synthesizer(`app.state.synthesizer = None` via deployment env)」**— `app.state.synthesizer = None` cannot be set via env var directly;real path is set `OPENAI_API_KEY=""` to fail synthesizer init in `lifespan` startup → falls through to retrieval-only mode。**Action item**:rewrite tier-3 fallback line to `"Set OPENAI_API_KEY='' env override + ACA revision restart → synthesizer init fails gracefully → app.state.synthesizer stays None → query.py:79 fallback path active"`。

### Root cause investigation ✅ Clear with 1 gap

Cost dashboard + Azure portal metric paths usable。Common causes list comprehensive(Beta cohort burst / runaway client / CRAG loop bug §5)。

🔴 **Gap surfaced**:**「Runaway client(eg. test script in loop)— audit log identify oid + revoke / contact user」**— how does oncall「revoke」the user?Tabletop verdict:no explicit revoke endpoint;practical path is(a)Entra ID app role removal(infrastructure/entra-id Pattern A 8-step)— BUT this requires IT help,5-10 min round-trip + (b)application-side block via `Settings.beta_user_blocklist` env var(does NOT yet exist;Tier 1 application has no per-user blocklist mechanism)。**Action item**:add runbook §2 step 2 Azure OpenAI tier-1 — `"For runaway client identified by oid: (a) Slack #ekp-beta tag user requesting they pause script + (b) Entra ID app role removal via IT helpdesk (5-10 min) — application-side per-user block IS NOT IMPLEMENTED Tier 1 (Tier 2 trigger if recurring)"`。

### Rollback / recovery ✅ Clear

Per-quota mitigation referenced + §6.1 ACA revision swap fallback(>30 min outage)+ post-incident RCA path(`docs/03-implementation/postmortems/INC-{YYYY-MM-DD}-quota-exhaust.md`)— all executable。

### §2 verdict 🟡 PARTIALLY READY for live exercise
- 2 clarifications + 1 gap require runbook in-place edits before live run
- Tier-1 / Tier-2 / Tier-3 fallback structure validated as conceptually sound
- Per-user revoke gap is **Tier 1 limitation acknowledged**(Tier 2 trigger when recurring runaway client signal)

---

## 4. Aggregate Findings

| Item | Section | Severity | Action |
|---|---|---|---|
| AF1 | §1.A step 2 | 🟡 clarify | Append `"queue" = Slack thread + bugs/BUG-{NNN}` note(no separate queue infra Tier 1)|
| AF2 | §2 step 2 Azure OpenAI tier-1 | 🟡 clarify | Append `"+ ACA revision restart required"` to rate limit tighten step |
| AF3 | §2 step 2 Azure OpenAI tier-3 | 🟡 clarify | Rewrite tier-3 fallback to use `OPENAI_API_KEY=''` env override(actual mechanism)instead of「set `app.state.synthesizer = None`」|
| AF4 | §2 root cause investigation runaway client | 🔴 gap | Add explicit「per-user block IS NOT IMPLEMENTED Tier 1;path is Slack ask user pause + Entra ID role removal via IT helpdesk」+ Tier 2 trigger flag |

**Live exercise post-Track A LIVE deploy** must validate AF1-AF4 fixes + execute the actual `az containerapp exec` / Langfuse filter / KQL query commands referenced in the runbook。

---

## 5. Re-trigger Condition for Live Exercise

Live exercise will replace this tabletop substitute when:
1. ✅ Track A IT cred populate event fires(R-B1 closure)
2. ✅ Staged ACA env online + Beta cohort access provisioned
3. ✅ Runbook AF1-AF4 in-place edits landed(per item 4 aggregate findings)
4. ✅ Chris + AI co-coordinate live walkthrough scheduled within 72h post-deploy

Live exercise output → updates `infrastructure/runbook/README.md` Update history with「W11 Dx live exercise outcome」+ corresponding W11 phase progress.md Day-N entry。

---

## 6. Update History

| Date | Change | Author |
|---|---|---|
| 2026-06-06 | Initial tabletop substitute(W10 D5 F5.1)— 2 sections walked + 4 aggregate findings logged | Chris(walkthrough)+ AI(scribe)|
| _(pending)_ | Live exercise outcome | Chris + AI(post-Track A)|

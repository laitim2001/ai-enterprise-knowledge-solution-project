---
phase: W07-beta-deploy
name: "Beta Hardening Sprint 1 — Auth + Rate Limiting + Audit + Mobile Responsive"
sprint_week: W7
start_date: 2026-05-12          # tentative — assumes W6 closed 2026-05-09
end_date: 2026-05-16            # 5 working days
status: closed                  # flipped active→closed 2026-05-16 W7 D5 closeout(G1'-G7 全 PASS verdict per progress.md retro)
spec_refs:
  - architecture.md §6.1 W7 row             # Microsoft Entra ID + rate limiting + React polish + Beta deploy
  - architecture.md §6.2 Beta + Rollout     # W7-W12 timeline
  - architecture.md §7.4 Day-2 Readiness    # Audit logging + observability requirements
  - architecture.md §8 Risk Register        # R5 Azure quota + R-B1 Entra ID delay + R-B5 Shadow AI
  - components/C11-identity.md              # Microsoft Entra ID + MSAL design
  - components/C08-api-gateway.md           # Rate limiting middleware design
  - components/C09-admin-console.md         # Mobile responsive baseline
  - components/C10-chat-interface.md        # Mobile responsive + UX polish
  - components/C12-devops.md                # Deploy scripts + audit logging plumbing
prior_phase: W06-final-eval-demo
related_artifacts:
  - docs/03-implementation/beta-plan-v1.md  # W7-W12 phase breakdown + risk register Beta-specific
  - docs/01-planning/W06-final-eval-demo/artifacts/demo-prep.md  # Q-D1 risk slides
---

# Phase W07 — Beta Hardening Sprint 1(Auth + Rate Limiting + Audit + Mobile Responsive)

> **Plan version**:1.0(draft 2026-05-05 W6 D4 末 closeout prep early-start — rolling JIT)
> **Owner**:Chris(Tech Lead)+ IT(Q11 Entra ID tenant 配合)
> **Approved by**:_(pending Chris W6 D5 closeout sign-off + W7 D1 kickoff approval + Q11 IT confirm)_

## 1. Scope

W07 開啟 **Tier 1 Beta deploy phase**(W7-W12)。**Beta hardening Sprint 1** 焦點:authentication + rate limiting + audit logging + error handling polish + mobile responsive complete — 為 W8 Beta deploy 到 Azure Container Apps + Static Web Apps 鋪路。

**6 deliverables F1-F6**:
- F1 Microsoft Entra ID auth integration(C11)— Q11 decision-level approved W6 D5;**W7 全程 mock auth dev mode**(F1.1 IT engagement + F1.7 LIVE smoke 推 W8 D1+D4);F1.2-F1.6 + F1.7-mock 全 W7 D1-D5 並行 unblocked
- F2 Rate limiting middleware per-user concurrency cap(C08 + C11)— architecture.md §8.1 R5 mitigation
- F3 Audit logging per-query trail(C07)— Langfuse trace audit-tag enrichment
- F4 Error handling polish graceful messages(C08 + C09 + C10)— architecture.md §7.3 E1-E14 edge cases
- F5 Mobile responsive baseline complete(C09 + C10)— architecture.md §6.1 W7 row deliverable
- F6 Phase Gate closeout + W7 retro + W8 kickoff prep

**Pre-condition for W7 promotion**(已 met 2026-05-05 W6 D5 stakeholder approval cycle cascade):
- W6 D5 closeout PASS(structural + Gate 2 PARTIAL PASS confirmed)✅
- Chris W7 D1 sign-off ✅
- ~~Q11 Entra ID tenant access IT confirm~~ — **decision-level approve W6 D5;operational confirm cascade trigger moved W8 D1**(per a-revised mock auth dev mode strategy 2026-05-05;see plan §2 F1 update + plan §7 changelog row)

**Mock auth dev mode strategy(W7 全程,W8 切換 LIVE)**:
- **Q11 IT cred 屬 W8 deploy-time dependency,non W7 dev-time dependency** — MSAL library scaffold + middleware skeleton + login flow UI + token refresh logic 全部可以 with **mock identity provider**(`backend/api/auth/mock_msal.py` returning fixed dummy user identity)做 W7 D1-D5
- **Settings flag**:`feature_auth_mock: bool = False`(default;production gate;W7 dev 設 True;W8 D4 post-IT cred delivery 切回 False LIVE smoke)
- **W7 closeout 用 F1.7-mock**(mock auth bearer end-to-end through middleware → return dummy user identity);**LIVE F1.7 推 W8 D4** post-IT cred delivery — natural deploy-time gate,non-W7-blocking
- **W8 D1 IT engagement trigger**:per `beta-plan-v1.md §2 W8.F1` Azure Container Apps deploy phase entry(architecture aligned — auth LIVE 同 deploy 同期)
- **Saved cost**:eliminates W7 D1 IT engagement bottleneck;W7 全 5 deliverable 並行 unblocked

**Sprint week origin**:[`architecture.md` §6.1 W7](../../architecture.md);[`docs/03-implementation/beta-plan-v1.md` §2 W7](../../03-implementation/beta-plan-v1.md)

## 2. Deliverables(F1-F6)

### F1 — Microsoft Entra ID auth integration(C11)

- **Component(s)**:**C11** Identity & Access(MSAL + Entra ID)+ **C08** API Gateway(auth middleware)+ **C09/C10** UI(login flow + token store)
- **Spec ref**:`architecture.md §6.1 W7`,`components/C11-identity.md`,`beta-plan-v1.md §2 W7.F1`
- **OQ deps**:Q11 Entra ID tenant **decision-level Resolved 2026-05-05**(W6 D5 stakeholder approval cycle);**operational IT cred cascade trigger moved W8 D1**(per a-revised mock auth dev mode strategy);Q9 Sensitivity / CMK Resolved 2026-05-05(default Azure-managed key acceptable W7)
- **Acceptance criteria**:
  - ~~F1.1 IT confirm Ricoh Entra ID tenant access~~ → **DEFERRED W8 D1** — Chris IT engagement(tenant access + app registration + owner identification)moved Beta deploy phase entry per `beta-plan-v1.md §2 W8.F1`;3 deliverables(Tenant Access / App Registration / Owner Identification)same trigger
  - F1.2 MSAL Python SDK + msal-react integration scaffold(`backend/api/auth/` + `frontend/lib/auth/`)— library install + import + middleware skeleton + login flow UI;**唔需要 real cred 即可寫**
  - **F1.2.1 NEW** `backend/api/auth/mock_msal.py` — dev-only middleware returning fixed dummy user identity(`oid` + `preferred_username` + `tid` matching real MSAL JWT claim shape);**`Settings.feature_auth_mock: bool = False`** flag(default False production gate;W7 dev mode set True via `.env`;W8 D4 切回 False LIVE smoke);Karpathy §1.3 surgical preserves C11 component design intent
  - F1.3 Auth middleware on `backend/api/main.py` lifespan — protect `/query/**` + `/kb/**`;`/healthz` + `/livez` 公開;**FastAPI Depends pattern**:`auth_dependency = get_current_user_mock if settings.feature_auth_mock else get_current_user_msal` — single switching point for W8 LIVE
  - F1.4 Login flow UI(C09 Admin + C10 Chat):redirect to Entra ID hosted login → callback → token store;**dev mode UI returns fake bearer "dev-token" via `frontend/lib/auth/mock_msal.ts`** for W7 testing
  - F1.5 Token refresh logic + logout endpoints
  - F1.6 Unit tests:auth middleware reject unauth + valid token allow + expired token reject;mocked MSAL responses
  - ~~F1.7 LIVE smoke:dev tenant Entra ID end-to-end login flow~~ → **DEFERRED W8 D4** — post-IT cred delivery cascade(W8 D1-D3:`AZURE_TENANT_ID` + `AZURE_CLIENT_ID` + `AZURE_CLIENT_SECRET` populate Azure Key Vault → W8 D4:`Settings.feature_auth_mock=False` → real Entra ID redirect flow LIVE smoke);natural deploy-time gate
  - **F1.7-mock NEW W7 closeout substitute** — verify mock auth dev mode end-to-end on local dev server:`Settings.feature_auth_mock=True` + curl `/query` with `Authorization: Bearer dev-token` header → middleware accept → return `_DEV_USER` identity;invalid bearer reject 401;F2 rate limiter use mock `oid` as rate-key successfully;F3 audit log Langfuse trace tag mock `oid` + `tid` visible
- **Effort estimate**:1.5-2 days W7 mock path(W6 C10 calibration LIVE deploy 2x → mock-only 0.7-1x);W8 D1 IT engagement + W8 D4 LIVE switch 各 0.5 day(beta-plan-v1.md W8 budget;non-W7 effort)
- **Owner**:AI(scaffold + tests + mock middleware)+ Chris(W8 D1 IT engagement)
- **Cost expected**:~$0(W7 mock dev mode no cloud spend;real Entra ID Free tier W8 onwards)
- **Blocking**:F2 + F3 用 mock user `oid` + `tid` 完全 unblocked W7;F1.7-mock pass = W7 closeout substitute;F1.7 real LIVE = W8 D4 deploy gating(non-W7-blocking);F6 closeout requires F1.7-mock pass(NOT F1.7 LIVE)

### F2 — Rate limiting middleware per-user concurrency cap

- **Component(s)**:**C08** API Gateway(middleware)+ **C11**(user identity)
- **Spec ref**:`architecture.md §8.1 R5`,`components/C08-api-gateway.md`,`beta-plan-v1.md §2 W7.F2`
- **OQ deps**:none(F1 user identity 提供 rate-key)
- **Acceptance criteria**:
  - F2.1 Token-bucket rate limiter middleware(per-user + per-IP fallback)— configurable via Settings
  - F2.2 Rate limit thresholds:50 req / minute per user + 5 concurrent active queries per user(architecture.md §8.1 R5 spec)
  - F2.3 429 response with Retry-After header on exceed
  - F2.4 Unit tests:burst within budget OK + burst exceed → 429;concurrent cap enforce
  - F2.5 Cost monitoring:rate-limit hit count → Langfuse tag(W8 cost dashboard data source)
- **Effort estimate**:1 day
- **Owner**:AI
- **Cost expected**:~$0(in-process middleware,no external dep)

### F3 — Audit logging per-query trail

- **Component(s)**:**C07** Observability + **C08** API Gateway(audit middleware)+ **C11**(user identity)
- **Spec ref**:`architecture.md §7.4 Day-2 Readiness — Audit log`,`components/C07-observability.md`,`beta-plan-v1.md §2 W7.F3`
- **OQ deps**:none
- **Acceptance criteria**:
  - F3.1 Audit log middleware:tag every Langfuse trace with `user_id` + `request_id` + `audit_action` + `tenant_id`
  - F3.2 Audit-specific tag schema document at `docs/02-architecture/audit-log-schema.md`(NEW)
  - F3.3 Sensitive data redaction:never log full prompt payload to plaintext file(per CLAUDE.md §5.5 H5);Langfuse encrypted-at-rest only
  - F3.4 Unit tests:audit middleware tag presence + redaction sanitization
  - F3.5 LIVE smoke:5 query through dev server → Langfuse trace 顯示 audit tags + request_id traceable
- **Effort estimate**:1 day
- **Owner**:AI
- **Cost expected**:~$0(Langfuse self-host)

### F4 — Error handling polish graceful messages

- **Component(s)**:**C08** API + **C09** Admin Console + **C10** Chat UI
- **Spec ref**:`architecture.md §7.3 E1-E14`,`components/C08-api-gateway.md` error contract,`beta-plan-v1.md §2 W7.F4`
- **OQ deps**:none
- **Acceptance criteria**:
  - F4.1 API error contract:every endpoint return `{"error": {"code", "message", "actionable_hint"}}` shape;NO raw stack trace
  - F4.2 UI error boundary:user-friendly message + "retry" / "report" CTA;NO browser default error page
  - F4.3 14 edge cases mapping(architecture.md §7.3 E1-E14):confirm each surfaces graceful message + log in observability
  - F4.4 Unit tests:5xx + 4xx + timeout each produce contract-compliant response;UI snapshot tests for error boundary
  - F4.5 LIVE smoke:trigger E1(OOS query 拒答)+ E5(LLM timeout retry)+ E12(KB delete during query)→ verify graceful UX
- **Effort estimate**:1 day
- **Owner**:AI
- **Cost expected**:~$0

### F5 — Mobile responsive baseline complete

- **Component(s)**:**C09** Admin Console + **C10** Chat UI
- **Spec ref**:`architecture.md §6.1 W7 row`,`components/C09-admin-console.md` + `C10-chat-interface.md`,`beta-plan-v1.md §2 W7.F5`
- **OQ deps**:Q10 Visual identity(non-blocking,default neutral tokens acceptable W7)
- **Acceptance criteria**:
  - F5.1 Tailwind responsive breakpoints audit:`sm` `md` `lg` `xl` correctness on 4 main views(KB list / KB detail / Chat / Eval Console)
  - F5.2 Mobile-only adjustments:hamburger nav + collapsible sidebars + touch-friendly tap targets
  - F5.3 Citation card mobile UX:full-width vs sidebar adjust;screenshot modal mobile-friendly
  - F5.4 Manual smoke test:Chrome DevTools mobile emulation 5 viewports(320 / 375 / 414 / 768 / 1024 width)
  - F5.5 Pixel diff snapshots committed for regression catch(`frontend/tests/snapshots/`)
- **Effort estimate**:1.5 days
- **Owner**:AI(implementation)+ Chris(visual review)
- **Cost expected**:~$0

### F6 — Phase Gate closeout + W7 retro + W8 kickoff prep

- **Component(s)**:cross-cutting governance
- **Spec ref**:`PROCESS.md §2.3 closeout`,`beta-plan-v1.md §2 W8 Beta deploy preview`
- **OQ deps**:F1-F5 verdict outcomes
- **Acceptance criteria**:
  - F6.1 W7 phase Gate verdict landed(F1-F5 outcomes documented + carry-overs to W8)
  - F6.2 W07 progress.md retro 7 sections complete(per W6 retro structure precedent)
  - F6.3 W08 phase folder kickoff:`docs/01-planning/W08-beta-deploy-sprint2/{plan,checklist,progress}.md` draft(W8 = Azure Container Apps + Static Web Apps + cost monitoring + user feedback dashboard)
  - F6.4 W07 progress.md frontmatter status flipped to `closed`
  - F6.5 OQ Q11 final Resolved sync to `decision-form.md`(Entra ID tenant access confirmed working)
  - F6.6 R-B1 risk status update to `RISK_REGISTER.md`(Entra ID delay → mitigated or active per F1 outcome)
- **Effort estimate**:1 day
- **Owner**:AI(draft)+ Chris(approve)

## 3. Success Criteria(Phase Gate to W08)

| # | Criterion | Target | Measure | Block W8?|
|---|---|---|---|---|
| **G1'** | **F1.7-mock NEW** mock auth dev mode end-to-end smoke | mock pass | F1.7-mock | **Yes**(W7 closeout blocker;substitute for G1)|
| ~~G1~~ | ~~F1 Entra ID auth LIVE smoke pass on dev tenant~~ | LIVE pass | F1.7(W8 D4) | **Moved to W8 D4** Beta deploy blocker(per a-revised mock auth strategy)|
| G2 | F2 rate limiter unit tests + integration smoke | 0/0 fail | F2.4 + F2.5 | Yes |
| G3 | F3 audit log Langfuse trace tags visible | 100% tag coverage | F3.5 | Yes |
| G4 | F4 14 edge cases graceful UX | 14/14 verified | F4.3 + F4.5 | No(some can defer W8) |
| G5 | F5 mobile responsive 5 viewport smoke | 5/5 pass | F5.4 + F5.5 | No(can polish W8) |
| G6 | Backend ruff + frontend lint + type-check 0 errors | All clean | local run | Yes |
| G7 | OQ Q11 Resolved(decision-level — operational IT cred cascade tracked W8) | `Resolved` 2026-05-05 | decision-form.md | **Already met W6 D5** stakeholder approval cycle |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Q11 Entra ID tenant IT delay(W8 D1 trigger per a-revised mock auth strategy) | Medium | High | **W7 全程 mock auth dev mode**(F1.7-mock as W7 closeout);W8 D1 Chris IT engagement trigger per `beta-plan-v1.md §2 W8.F1`;若 W8 D5 仍未 confirm → Beta-blocking R-B1 active monitor → Stakeholder + IT manager 三方 escalation;Karpathy §1.2 simplicity-first decoupled W7 dev from W8 deploy IT bottleneck |
| R2 | MSAL SDK Python + Next.js integration friction | Medium | Medium | Microsoft sample code reference;known good pattern in references/dify/web/app/login(read-only inspiration per CLAUDE.md §5.3 H3);scaffold tests early to catch contract mismatch |
| R3 | Rate limiter affecting demo / Beta legitimate user burst | Low | Medium | Conservative thresholds W7(50 req/min + 5 concurrent);production tuning W8-W10 based on observed real query patterns |
| R4 | Audit log volume overwhelming Langfuse local instance | Low | Low | Self-host Langfuse retention policy 30 day rolling;production move to Langfuse cloud W8+ |
| R5 | Mobile responsive regressing existing desktop layout | Medium | Low | Pixel diff snapshots gate(F5.5);visual review by Chris |
| R6 | R8 Ricoh corp proxy / VPN issue blocks W7 deploy work | High | Medium | Same W2-W6 mitigation:home network or Python httpx probe ground truth(per W6 D1 calibration carry-over W6 C7) |
| R7 | F2 + F3 ordering — rate limiter user-identity dependency on F1 | Medium | Low | Plan F2 + F3 sequential after F1;若 F1 R1 trigger fallback → F2/F3 dev with mock user identity |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-05-12 | F1.2 + F1.2.1 mock middleware scaffold(`backend/api/auth/mock_msal.py` + `frontend/lib/auth/mock_msal.ts` + `Settings.feature_auth_mock` flag)| F1 |
| D2 | 2026-05-13 | F1.3 auth middleware Depends pattern + F1.4 login flow UI(mock bearer)+ F2 rate limiter(use mock `oid` rate-key)| F1, F2 |
| D3 | 2026-05-14 | F1.5 token refresh + logout + F1.6 unit tests + F3 audit logging(use mock `oid` + `tid` tags)| F1, F3 |
| D4 | 2026-05-15 | F4 error handling polish + F5 mobile responsive | F4, F5 |
| D5 | 2026-05-16 | F5 polish + **F1.7-mock end-to-end smoke**(mock auth W7 closeout substitute)+ F6 closeout + W08 kickoff prep | F5, F1, F6 |

## 6. Dependencies on Prior Phase

Carry-overs from `W06-final-eval-demo/progress.md` retro:
- **W6 C1** F2 final eval full-corpus(Chris SME labeling cascade)— W7 background polish if labeling lands
- **W6 C2** F3 subset=20 borderline cluster confirmation — W7+ ad-hoc trigger if stakeholder approves
- **W6 C3** F4 W4/W5 LIVE smoke remainder(PPT E2E + GPT-5.5 latency + Chat UI screenshots)— W7 D1 sync-point with Chris
- **W6 C4** F5.4 demo screenshots / GIF artifacts — W7 polish window post-Chris dev server availability
- **W6 C5** architecture.md §3.2 + §6.3 amendment ticket — W7+ stakeholder approval cycle
- **W6 C6** RAGAs evaluator REFUSAL_PHRASE skip enhancement — W7+ optional polish
- **W6 C7** R8 mitigation update entry to `RISK_REGISTER.md` — W7 D1 housekeeping
- **W6 C8** F3 L3 routing conditional — defer Tier 2(Gate 2 STRONG PASS upgrade trigger 唔 fire)
- **W6 C9** Q-deps for Beta(Q7+Q9+Q10+Q11+Q12)— Q11 W7 critical path;others W7-W8
- **W6 C10** Plan estimate calibration:W7 LIVE deploy 2x;W7 static 0.5x — applied to §2 effort estimates

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-05 | Initial draft(W6 D4 末 closeout prep early-start)| Per PROCESS.md §2.3 rolling-JIT kickoff;status=draft pending Chris W6 D5 closeout sign-off + W7 D1 kickoff approval + Q11 IT confirm | Chris(pending approve to flip active) |
| 2026-05-05 | Status flip `draft → active`(W6 D5 stakeholder approval cycle cascade)| Stakeholder approve 4 points landed(architecture amendment + Q7/Q9/Q10/Q11/Q12 Resolved + Beta plan v1 sign-off);Q11 decision-level approve unblocks W7 active flip;**Q11 IT operational confirm cascade trigger W7 D1**(non-blocking flip — F1.1 fallback mock auth dev mode preserved if IT slips;Beta-blocking only if W7 D5 仍未 confirm)| Stakeholder + Chris(W6 D5 closeout)|
| 2026-05-05 | a-revised mock auth dev mode strategy adopted(同 W6 D5 closeout same-session)| Per Karpathy §1.2 simplicity-first decoupling — Q11 IT cred 屬 W8 deploy-time dependency,non W7 dev-time dependency。MSAL library + middleware + login flow UI + token refresh logic 全部可以 with mock identity provider 寫 W7 D1-D5。F1 acceptance criteria refined:F1.1(IT engagement)+ F1.7(LIVE smoke)推 W8 D1 + W8 D4;F1.2.1(mock_msal.py)+ F1.7-mock(W7 closeout substitute)NEW;G1 → G1' substitute;R1 mitigation refined;day-by-day breakdown re-mapped。**Saved cost**:eliminates W7 D1 IT engagement bottleneck;W7 全 5 deliverable 並行 unblocked;F1.7 LIVE 自然推 W8 D4 deploy-time gate(architecture aligned)。**Architecture impact zero**(per CLAUDE.md §5.1 H1 boundary check — `feature_auth_mock` Settings flag + FastAPI Depends pattern preserves C11 component design intent;non-architectural change)| Chris approve via "執行 (a-revised) — W7 plan + checklist + progress update"|

---

**Lifecycle reminder**:呢份 plan `status=draft`(等 Chris W7 D1 sign-off + Q11 IT confirm flip `active`)。重大 deviation 入第 7 節 changelog。

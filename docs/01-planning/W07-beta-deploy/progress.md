---
phase: W07-beta-deploy
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active     # flipped draft→active 2026-05-05 W6 D5 stakeholder approval cycle cascade
---

# Phase W07 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。
> Status:`active` 自 2026-05-05 W6 D5 stakeholder approval cycle cascade。

---

## Day 0 — 2026-05-05: Kickoff prep(W6 D4 末 closeout prep early-start 同 session)

**Action**:Phase W07 kickoff prep(per PROCESS.md §2.3 rolling-JIT lifecycle + W6 D4 closeout prep early-start per CLAUDE.md §10 R5 — F6 prep buffer for D5)

- Folder `docs/01-planning/W07-beta-deploy/` created
- `plan.md` filled with status=`draft`(6 deliverables F1-F6:Microsoft Entra ID auth integration + rate limiting + audit logging + error handling polish + mobile responsive complete + Phase Gate closeout + W8 kickoff prep)
- `checklist.md` derived from plan deliverables(~33 atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over candidates from W06-final-eval-demo**(per W6 retro § Carry-overs C1-C10):
  - C1 F2 final eval Chris SME labeling cascade → background polish if labeling lands W7
  - C2 F3 subset=20 confirmation → ad-hoc trigger if stakeholder approves
  - C3 F4 W4/W5 LIVE smoke remainder → **W7 D1 sync-point with Chris**(PPT E2E + GPT-5.5 latency + Chat UI screenshots)
  - C4 F5.4 demo screenshots → polish window post-Chris dev server availability
  - C5 architecture.md §3.2 + §6.3 amendment → stakeholder approval cycle vNext
  - C6 RAGAs evaluator REFUSAL_PHRASE skip → optional W7+ polish
  - C7 R8 mitigation update entry to `RISK_REGISTER.md` → **W7 D1 housekeeping**(Python httpx probe ground truth pattern documentation)
  - C8 F3 L3 routing conditional → defer Tier 2(STRONG PASS upgrade trigger 唔 fire)
  - C9 Q-deps for Beta:Q7+Q9+Q10+**Q11 W7 critical path**+Q12 — stakeholder approval cycle for W7-W8 kickoff
  - C10 Plan estimate calibration:LIVE deploy 2x;static 0.5x — applied to W7 plan §2 effort estimates
- **W7 critical path identification**:**Q11 Entra ID tenant access** must IT confirm by W7 D1 — blocks F1.1 → F1.7 cascade。Fallback = mock auth dev mode for D1-D3 development;若 W7 D5 仍未 confirm → F1 LIVE smoke defer W8(Beta-blocking)
- **POC closeout context**:W6 closes Tier 1 12-week sprint POC phase(W1-W6 portion);W7-W8 = Beta deploy(Microsoft Entra ID + rate limiting + React polish + Beta deploy);W9-W10 = Beta internal testing;W11-W12 = staged rollout 25% → 100% production launch per architecture.md §6.1 timeline。

**Status update at W6 D5 closeout cascade(2026-05-05 same-session)**:Stakeholder approve 4 points landed → W6 frontmatter `active → closed` + Q11 decision-level approve(Ricoh 統一 tenant via Entra ID;W7 D1 IT operational confirm cascade trigger;fallback mock auth dev mode preserved per F1.1 if IT slips)→ **W07 status `draft → active` 2026-05-05**(this entry)。

---

## Day 0 cont — 2026-05-05: W7 phase activation post-stakeholder approval cycle

**Action**:W6 D5 stakeholder approval cycle cascade landed → W7 phase activation:

- Stakeholder approval cycle outcome(2026-05-05 same-session):
  - **Approval 1+2** architecture.md §3.2 + §6.3 amendment **APPROVED** → architecture.md v5 → v5.1 increment + ADR-0012 formal record(`docs/adr/0012-cohere-v4-pro-upgrade-and-gate2-partial-pass.md`)
  - **Approval 3** 5 OQ Resolved batch:**Q7 Q9 Q10 Q11 Q12** all `Resolved` 2026-05-05 — Q12 explicit Chris as Tier 2 owner;Q11 decision-level approve unblocks W7 active flip
  - **Approval 4** Beta plan v1 **APPROVED** → `docs/03-implementation/beta-plan-v1.md` status `draft → active`
- W7 plan/checklist/progress frontmatter status `draft → active`(this batch)
- ~~W7 D1 critical path:Q11 IT operational confirm cascade trigger~~ → **a-revised 2026-05-05 same-session**:Chris IT engagement(Deliverable A Tenant Access + B App Registration + C Owner Identification)moved **W8 D1 Beta deploy phase entry**(per `beta-plan-v1.md §2 W8.F1` alignment);W7 D1 implementation start **不再 IT-blocked**

### a-revised mock auth dev mode strategy(2026-05-05 W6 D5 closeout same-session)

**Karpathy §1.1 think-before-coding outcome**:Q11 IT cred 屬 **W8 deploy-time dependency**,non W7 dev-time dependency。MSAL library + middleware + login flow UI + token refresh logic 全部可以 with **mock identity provider**(`backend/api/auth/mock_msal.py` returning fixed dummy user identity)做 W7 D1-D5。

**Strategy details**:
- `Settings.feature_auth_mock: bool = False`(default production gate)— W7 dev set True via `.env`;W8 D4 切回 False post-IT cred delivery
- FastAPI Depends pattern single switching point:`auth_dependency = get_current_user_mock if settings.feature_auth_mock else get_current_user_msal`
- F1.7-mock W7 closeout substitute(verify mock auth end-to-end on local dev server);LIVE F1.7 推 W8 D4 natural deploy-time gate
- F1.2.1 NEW `backend/api/auth/mock_msal.py` dev-only middleware
- W7 plan §1 + §2 F1 + §3 G1' + §4 R1 + §5 day-by-day + §7 changelog row 全部 updated

**Saved cost**:eliminates W7 D1 IT engagement bottleneck;W7 全 5 deliverable 並行 unblocked;F1.7 LIVE 自然推 W8 D4 deploy-time gate。

**Architecture impact zero**(per CLAUDE.md §5.1 H1 boundary check):Settings flag + FastAPI Depends pattern preserves C11 component design intent;non-architectural change。

### Decisions / OQ summary

- Q7 + Q9 + Q10 + Q11 + Q12 — all `Resolved` 2026-05-05 W6 D5 stakeholder approval cycle
- Q11 decision-level Resolved 2026-05-05;**operational IT cred cascade trigger moved W8 D1**(per a-revised mock auth strategy)
- ADR-0012 — formal record landed(architecture.md v5 → v5.1 amendment + Gate 2 PARTIAL PASS verdict)
- Phase status W07 `draft → active` 2026-05-05;W7 plan + checklist + progress a-revised mock auth path landed same-session

### Open / blocked

- ⏸ W7 D1 implementation start ready(non-blocked per a-revised — F1.2 MSAL library scaffold + F1.2.1 mock middleware + F1.3-F1.6 + F2-F5 全部 並行 unblocked)
- ⏸ W8 D1 Q11 IT operational cascade trigger awaiting beta deploy phase entry(per `beta-plan-v1.md §2 W8.F1`)
- ⏸ R-B1 active monitor:W8 D5 仍未 IT confirm → Beta-blocking escalation

### Commit reference

- W6 D5 stakeholder approval cycle cascade commit `b3a63f0`(architecture amendment + ADR-0012 + 5 OQ resolved + beta-plan active + session-start sync + W7 active)
- _(W7 a-revised mock auth path commit pending — references plan + checklist + progress 3-file batch + plan changelog row 2026-05-05 a-revised)_

---

## Day 1 — _(pending W7 D1 implementation start)_

---

## Day 2 — _(pending)_

---

## Day 3 — _(pending)_

---

## Day 4 — _(pending)_

---

## Day 5 — _(pending)_

---

## Retro(填於 W7 D5 末)

### What worked
_(W7 D5 末 fill)_

### What didn't work / unexpected friction
_(W7 D5 末)_

### Surprises / discoveries
_(W7 D5 末)_

### Carry-overs to W08-beta-deploy-sprint2
_(W7 D5 末)_

### ADR triggers
_(W7 D5 末 — ADR-0012 reserved for(a)architecture.md §3.2 amendment formal record stakeholder approval cycle outcome OR(b)Tier 2 reranker swap if real-query distribution diverges)_

### Phase Gate result(per plan.md §3 + architecture.md §7 acceptance)
- G1-G7:_(W7 D5 末)_
- **W7 Beta hardening verdict**:_(W7 D5 末)_ → ready for W8 Azure Container Apps + Static Web Apps deploy / require additional polish

### Phase status
- Closeout commit:_(W7 D5 末)_
- Frontmatter status flipped to `closed`:_(W7 D5 末)_
- Phase W08 kickoff trigger:_(W7 D5 末 — W8 plan = Azure Container Apps + Static Web Apps + cost monitoring + user feedback dashboard + Beta smoke test per architecture.md §6.1 W8 row)_

---

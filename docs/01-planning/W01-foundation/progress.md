---
phase: W01-foundation
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: closed
---

# Phase W01 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — 2026-04-30: Kickoff(retroactive)

**Action**:Phase W01 kickoff,**retroactively documented**(framework 喺 Day 1 中段引入)

- Templates copied from `_templates/`
- `plan.md` filled,status=`active`
- `checklist.md` derived from plan deliverables(F1-F11)
- Carry-over from prior phase:`N/A — first phase of EKP Tier 1`

**Note**:正常 lifecycle Day 0 應該係 phase kickoff、Day 1 起 implementation。本次因 framework 喺 Day 1 中段引入(per Chris guidance),Day 0 entry 同 Day 1 同日(2026-04-30)。Future phases follow 正常 D0 / D1 split。

**Commits relevant**:Phase planning framework setup commit pending(framework files 同呢份 progress 一齊 commit)。

---

## Day 1 — 2026-04-30

### Done

**Pre-framework execution(8:00–14:00 local time approximate)**:
- F1 ✅ Repo hygiene + Dify reference(`9ea18f1` initial commit;Dify clone retry with `core.longpaths=true` after Windows MAX_PATH hit)
- 6 critical OQ resolution(Q1-Q4 + Q13 + Q14)by Chris(`d74fee2`)
- F2 ✅ Backend FastAPI skeleton 26 files(`b21a0a2`)
- F3 ✅ Frontend Next.js 14 skeleton 21 files(`7589110`)
- F5 + F6 ✅ Eval set validator + docx structure inspector scripts(`cc0b90b`)
- Repo follow-up:gitignore `.claude/` + dev log + topology SVG(`e3fc338`)
- F4 ✅ Local dev stack hybrid(Postgres + Langfuse via Docker;Azurite via npm fallback after MCR DNS intercept blocker)— compose tag fix(`f7ba973`)

**Framework introduction(14:00 onwards)**:
- Per Chris's guidance,Phase Planning framework introduced mid-Day 1
- Created `docs/01-planning/PROCESS.md`、3 templates、W01-foundation/{plan,checklist,journal}.md retroactive
- CLAUDE.md §10 Phase Planning Workflow added with rules R1-R5 reference

### Decisions / OQ Resolved

- **OQ-Q1** Resolved:format ratio **40% Word + 30% PPT + 30% PDF**(deviation from default 80/15/5 → W2 PDF + PPT 同等 priority,唔可推到 W3)
- **OQ-Q2** Resolved:stakeholder 提供原檔(direct upload / shared folder / SharePoint)— POC manual upload OK
- **OQ-Q3** Resolved:Azure AI Search service exists(POC stage),pending implementation detail by W2 D1
- **OQ-Q4** Resolved:Azure OpenAI 完整 deployment ready(GPT-5.5 / 5.4 / 5.4-mini / 5.4-nano / embedding small + large),pending exact deployment names + endpoint by W2 D1
- **OQ-Q13** Resolved:Yes — SME allocation
- **OQ-Q14** Resolved (partial):Yes,specific labeler name pending W1 末
- **Decision** — `gitignore` 缺 leading dot 屬 critical issue:H3 + H5 prevention failure;rename 之前 D2 git init,save Dify license risk + secret commit risk
- **Decision** — Azurite Docker pull blocked by Ricoh corp DNS intercept(`mcr.microsoft.com` resolves to `10.160.92.1` internal proxy);workaround = npm-distributed Azurite。Document as long-term infra follow-up
- **Decision** — Python 3.14 cp314 wheel supply persistent issue;defer pytest run to W2 D1。Recommend Chris install Python 3.12 stable env

### Blockers

- 🚫 **Q14 specific labeler name** — Chris W1 末 confirm
- 🚫 **Q2 sample manual delivery** — needed for F8 + F11 + Q17/Q18 execution
- 🚫 **Q3 + Q4 implementation detail** — needed for F9 + F10 .env wiring
- ⚠️ **Python 3.14 cp314 wheel supply** — `pydantic-core` / `httptools` download keeps connection-resetting via PyPI / TUNA mirror。Long-term:Chris install Python 3.12
- ⚠️ **Ricoh corp DNS intercept MCR** — `mcr.microsoft.com` blocked at proxy 10.160.92.1。Long-term:IT whitelist or VPN for Docker workflow

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| F1 | 1 | 1.5 | +0.5h | Windows MAX_PATH on Dify clone |
| F2 | 3 | 3.5 | +0.5h | pyproject setuptools packages.find config + Python 3.14 wheel issue |
| F3 | 3 | 3 | 0 | Clean |
| F4 | 0.5 | 1.5 | +1h | MCR DNS intercept,npm Azurite fallback |
| F5 | 1 | 1 | 0 | Clean(after null difficulty handling) |
| F6 | 1 | 1 | 0 | Clean |
| Framework setup | 0(unplanned) | 1 | +1h | Mid-day pivot per Chris guidance |
| **Total Day 1** | **9.5** | **12.5** | **+3h** | Network supply issues drove most variance |

### Commits

| Hash | Subject |
|---|---|
| `9ea18f1` | chore(repo): initial portfolio scaffold |
| `d74fee2` | docs(decision-form): resolve 6 critical OQ (Q1-Q4, Q13, Q14) |
| `b21a0a2` | feat(api): scaffold FastAPI skeleton with 18 endpoint stubs |
| `7589110` | feat(frontend): scaffold Next.js 14 with shadcn/ui foundation and design tokens |
| `cc0b90b` | feat(eval): add eval-set validator + docx structure inspector scripts |
| `e3fc338` | chore(repo): gitignore .claude/ + checkpoint W1 D1 dev log + add topology SVG |
| `f7ba973` | fix(infra): pin Langfuse image to langfuse:2 (was 2-latest, no longer published) |
| `(pending)` | chore(planning): introduce phase-based rolling planning framework + W01 retroactive |

---

## Day 2 — 2026-05-01

> Status: **EOD update** — H5 remediation + Python 3.12 install + F7 KB CRUD + decision-form Q3/Q4/Q14 sync 全部 committed;F2 pytest retry + F7 unit tests 仍 deferred 到 post-pip-install window(corp proxy block)。3 commits 覆蓋 D2 work。

### Pre-flight checks(D1 末 carry-over,confirmed D2 早段)

- [x] **Q14**:Chris Lai / `chris.lai@rapo.com.hk` ✅
- [ ] **Q2**:仍 pending direct upload from Chris
- [x] **Q3**:endpoint + key delivered via `docs/11-env-resources-detail/` markdown(triggered H5,now relocated to `.env`)
- [x] **Q4**:endpoint + key + 6 deployments delivered same path(同上)
- [x] **Python 3.12**:installed via winget(see Done below)

### Done(by ~16:30 local approx)

**H5 hard-constraint remediation**:
- Trigger:Q3 + Q4 secret values delivered via plaintext markdown in `docs/11-env-resources-detail/`,folder 未 gitignored
- Verified safe state:`git ls-files docs/11-env-resources-detail/` empty + `git log --all -- docs/...` empty → key 從未入 git history
- Remediation:
  - `.gitignore` 加 `docs/11-env-resources-detail/`(line 28-31)
  - Plaintext key 全部 relocate 到 root `.env`(line 18 既 gitignored,verify via `git check-ignore`)
  - Markdown rewrite 為 reference table only(deployment name + `.env` var name,zero plaintext)

**Python 3.12 install**(W1 D1 R5 risk mitigation):
- Initial `winget install Python.Python.3.12` failed:`msstore` source cert mismatch(`0x8a15005e`,Ricoh corp SSL inspection)
- Workaround:`--source winget`(skip msstore enumeration)→ Python 3.12.10 installed per-user
- `py -0` 顯示 3.14 + 3.12 共存
- `backend/.venv` 用 `py -3.12 -m venv` 重建;舊 cp314 venv rename `backend/.venv-py314-backup` 留 rollback

**Pip install attempt**(blocked,trigger P3 pivot):
- `pip install -e backend[dev]`:落 `mypy-1.20.2-cp312-cp312-win_amd64.whl (10.9MB)` → `IncompleteRead(0 bytes read)`
- Retry x10 + timeout 120s:同樣斷流
- TUNA mirror(`pypi.tuna.tsinghua.edu.cn`):503 errors
- Pattern:任何 >500KB wheel 落到 corp proxy → 0 bytes connection broken

### Decisions / OQ Resolved

- **OQ-Q3 Resolved (full)**:endpoint + key + region eastus2(inferred)+ tier default Standard S1 per architecture.md §3.2(W2 D1 confirm)
- **OQ-Q4 Resolved (full)**:endpoint + api version `2024-12-01-preview` + 6 deployments(`gpt-5.5` / `gpt-5.4` / `gpt-5.4-mini` / `gpt-5.4-nano` / `text-embedding-3-small` / `text-embedding-3-large`)
- **OQ-Q14 Resolved (full)**:SME labeler = Chris Lai(`chris.lai@rapo.com.hk`)
- **Decision** — Eval judge default 用 `gpt-5.4-mini`(`gpt-5.5-pro` not deployed POC stage,spec-compliant per CLAUDE.md §5.2 H2 alternative)
- **Decision (P3 pivot,Chris approved)** — pip install 暫時 blocked,F2 pytest verification + F7 unit tests defer 到 post-pip-install window;F7 implementation code 今日推進(no test framework runtime dep)

### Blockers

- 🔴 **Ricoh corp proxy on PyPI/TUNA**:任何 wheel >500KB 落到 `IncompleteRead(0 bytes read)`。Mitigation:P1(VPN / mobile hotspot ops window)或 P2(IT whitelist long-term)
- 🚫 **Q2 sample manual**:仍 pending direct upload。F8 + F11 仍 BLOCKED
- ⚠️ **F2 pytest retry**:cp312 wheel(mypy / pyyaml / 其他大檔)同樣 corp proxy block。Re-defer 到 post-pip-install window
- ⚠️ **F7 unit tests**:同上原因,defer。F7 implementation code 仍按計劃推進

### Actual vs Planned Effort(EOD final)

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| H5 remediation(unplanned)| 0 | 1 | +1h | Q3+Q4 secret 提供方式撞 H5 |
| Python 3.12 install | 0.2 | 0.3 | +0.1h | msstore cert retry |
| `.venv` recreate + pip attempts | 0.2 | 1 | +0.8h | Corp proxy block, P3 pivot |
| F7 KB CRUD impl | 4 | 2.5 | -1.5h | Protocol abstraction + Annotated DI 一次過寫直,unit tests deferred 慳半 |
| Decision-form Q3+Q4+Q14 sync(R4)| 0.3 | 0.3 | 0 | 6 cell edits batch |
| **Total D2** | **4.7** | **5.1** | **+0.4h** | H5 + corp proxy 食咗 ~2h,F7 implementation 慳返 |

### Commits

| Hash | Subject |
|---|---|
| `09138d4` | chore(security): gitignore env-resources folder + W1 D2 H5 closure |
| `c6ca6e3` | feat(kb): impl KB CRUD with in-memory backend (P3: tests deferred) |
| `dfcafbf` | docs(planning): W1 D2 closeout — sync decision-form Q3+Q4+Q14 + journal EOD |

### F7 implementation note

- New package `backend/kb_management/` 3-file(plan §2 寫 `kb_service.py` 單檔,implementation 升級為 Protocol-based package)
- 5 endpoints replace 501 stubs;ruff lint + format + compileall ✅
- Unit tests deferred 與 F2 共用 post-pip-install window
- **R3 plan changelog 唔需要新加 entry**:scope unchanged(in-memory KB CRUD per plan F7),只係 file layout 由 1 file 升級為 3-file package(implementation detail,non-architectural)

---

## Day 3 — 2026-05-01

> Status: **structural pivot day** — D3 從原 plan 嘅 F8/F9 implementation pivoted 到 **component spine introduction**(per Chris W1 D3 strategic call)。F8 + F9 仍 BLOCKED(Q2 + corp proxy);利用 blocker window 完成 EKP 12-component decomposition + 3 個 doc 入主流(catalog / risk register / planning artifact tags)。

### Done

**Block A — Component Catalog spine**(commit `220f75a`):
- `docs/02-architecture/COMPONENT_CATALOG.md`(530 lines)創建,12 components(C01-C12)
- 3-layer doc 分工 lock:`architecture.md`(spec what+why)/ `PROCESS.md`(lifecycle how)/ catalog(structure)
- 7 cross-cutting conventions CC-1..CC-7(future plan / ADR / OQ / risk / design note binding rules)
- 8 個 Tier 2 features 對應 Cn slot(future-proof)
- `docs/02-architecture/components/README.md` rolling JIT design note convention(per CC-5)

**Block B — Existing artifact refactor**(commit `2dc0948`):
- `W01-foundation/plan.md` F1-F11 加 `**Component(s)**` field(per CC-1)
- `decision-form.md` 21 OQ dashboard 加 `Component(s)` column(per CC-3)
- `RISK_REGISTER.md` NEW(per CC-4):living register,extends frozen `architecture.md §8` R1-R7 + 加 component tag + 3 net-new W1 incident risk(R8 corp proxy / R9 MCR DNS / R10 Q2 delay)
- `CLAUDE.md §2` Document Routing 加 2 row(component catalog + risk register routing)

### Decisions

- **Strategic decomposition adopted**:Chris W1 D3 strategic call → introduce 12-component spine(agent-harness analogy)before W2 kickoff;unblock cross-phase / cross-domain visibility(原問題:「閉起雙眼走路」)
- **3-layer doc 分工 lock**:`architecture.md`(spec)/ `PROCESS.md`(lifecycle)/ `COMPONENT_CATALOG.md`(structure)— 三者單一 source-of-truth,zero duplication;component design note(`components/Cn-*.md`)係 catalog row 嘅 expansion
- **Per-component design note rolling JIT**(CC-5):no speculative pre-write,first heavy-touch phase 寫 stub。**Tier 1 內 11/12 component design note 待 W2-W7 first-touch 時補**
- **`architecture.md` frozen invariant 維持**:living evolution(risk + status)入 `RISK_REGISTER.md` 而非編輯 `§8`(per CC-4)
- **Component tagging 強制**(CC-1 / CC-3):W2+ 起所有 phase plan deliverable / OQ / ADR 必須 tag 對應 Cn

### Blockers(unchanged from D2 EOD)

- 🔴 **Ricoh corp proxy on PyPI/TUNA**:仍 active,F2 + F7 unit tests 仍 deferred → R8 living entry
- 🚫 **Q2 sample manual**:仍 pending,F8 + F11 仍 BLOCKED → R10 living entry
- 新增 W1 D3 risk register 補:R8 / R9 / R10 全部入 RISK_REGISTER.md

### Component-lens retrospective on W1 D1-D3 work(per CC-1 retroactive view)

| Deliverable | Status | Component(s) touched |
|---|---|---|
| F1 Repo + Dify(D1)| ✅ | C12 |
| F2 FastAPI skeleton(D1)| ✅(pytest defer) | C08 + C07 |
| F3 Next.js skeleton(D1)| ✅ | C09 + C10 |
| F4 Local dev stack(D1)| ✅ | C12 + C07 |
| F5 Eval validator(D1)| ✅ | C06 |
| F6 docx inspector(D1)| ✅(execution blocked Q2)| C01 |
| F7 KB CRUD impl(D2)| ✅(unit tests defer) | C02 + C08 |
| H5 remediation(D2)| ✅ | C12(infra/secrets governance) |
| Python 3.12 install(D2)| ✅ | C12 |
| OQ Q3+Q4+Q14 sync(D2)| ✅ | (governance,unblocks C03 / C05 / C01 / C06) |
| Component spine introduction(D3)| ✅ | (cross-cutting structural foundation) |

**Component-touch coverage W1 D1-D3**:**8/12 components**(C01 partial, C02 ✅ in-memory, C06 ✅ scaffold, C07 ✅ init, C08 ✅ scaffold, C09 ✅ scaffold, C10 partial scaffold, C12 ✅)。剩 **4 個 component**(C03 / C04 / C05 / C11)需 W2+ first-touch — 跟 catalog phase × component heatmap 一致。

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| Block A Component Catalog + components/README | 3 | 2.5 | -0.5h | Structure clear,12 entries 一氣呵成 |
| Block B Refactor existing artifacts | 2 | 1.5 | -0.5h | 14 parallel edits 一輪過 |
| Block C Journal Day 3(noon)| 1 | 0.5 | -0.5h | Closure simple |
| **Design Note Batch 1**(CC-5 update + 5 backend notes) | 5 | 3.5 | -1.5h | Maturity-first ordering helped;clear spec sections speed |
| **Design Note Batch 2**(6 forward-looking notes) | 8 | 5 | -3h | Spec ref 完整,template-driven |
| **Final Closeout**(this commit) | 0.5 | 0.5 | 0 | — |
| **Total D3 (revised)** | **19.5** | **13.5** | **-6h** | Massive structural day,11/12 design notes shipped |

### Done(afternoon — Design Note Batch per Chris W1 D3 update)

**CC-5 convention update**:從 `rolling JIT` → `design-first with v0-draft marker`(per Chris call to upfront design 11 components 作為 implementation reference contract)。`COMPONENT_CATALOG.md` 同 `components/README.md` 同步更新。

**11/12 component design notes 一日內完成**(C11 Beta+ defer 到 W6 末 / W7 kickoff):

| Batch | Cn | Status | Lines |
|---|---|---|---|
| **Batch 1**(commit `7737069`,backend mature)| C12 DevOps & Infra | v1-active | ~210 |
| | C02 KB Manager | v1-active | ~180 |
| | C08 API Gateway | v0-draft | ~190 |
| | C06 Eval Framework | v0-draft | ~180 |
| | C07 Observability Stack | v0-draft | ~180 |
| **Batch 2**(commit `6b5660a`,forward-looking)| C09 Admin Console UI | v0-draft | ~200 |
| | C10 Chat Interface UI | v0-draft | ~200 |
| | C03 Indexing Service | v0-draft | ~190 |
| | C01 Ingestion Pipeline | v0-draft | ~210 |
| | C04 Retrieval Engine | v0-draft | ~190 |
| | C05 Generation Pipeline | v0-draft | ~200 |
| **Total** | 11 notes | — | **~2128 lines** |

每份 design note 跟 `components/README.md` 嘅 8-section template:
1. Internal Architecture — sub-modules / file structure / pipeline flow
2. Key Interfaces — input / output / side effects(type signatures)
3. Critical Design Decisions — 為何 choose this approach(rationale linking spec / ADR)
4. Edge Cases & Error Handling
5. Performance Characteristics — latency / throughput / cost
6. Test Strategy
7. Future Evolution / Tier 2 Hooks
8. Open Items / TODO

### Commits(updated)

| Hash | Subject |
|---|---|
| `220f75a` | feat(planning): introduce 12-component catalog (EKP module spine) |
| `2dc0948` | refactor(planning): tag W01 plan + decision-form OQ + add RISK_REGISTER.md |
| `99ebf0c` | docs(planning): W1 D3 journal + checklist tick — component spine |
| `7737069` | docs(catalog): batch 1 — 5 backend component design notes (v0-draft) |
| `6b5660a` | docs(catalog): batch 2 — 6 forward-looking design notes (v0-draft) |
| `(this commit)` | docs(planning): W1 D3 final closeout — 11/12 design notes complete |

---

## Day 5 — 2026-05-02 (early closeout per Chris call)

> Status: **W1 phase closeout** — D5 work 因 Chris 2026-05-02 evening session decision compress 入 D4 末日同日執行(原 plan D5 = 2026-05-04 Mon,early closeout 後 W2 D1 仍按 plan = 2026-05-05 Tue)。

### Done

**Pre-flight verification(closeout gate check)**:
- G3 Local stack:🟡 **2/3 healthy** — Postgres ✅(2 days uptime,healthy)+ Azurite ✅(npm fallback,blob endpoint 400 = service alive auth-rejected as expected)+ **Langfuse 🔴 unhealthy**(container Up 2 days but `/api/public/health` connection-reset;`docker compose restart` + `up -d --force-recreate` 同樣 hang 唔生效)。NEW finding 今日 surface,W1 D2 last-verified healthy,degradation 過去 2 日內出現
- G4 Backend ruff:✅ All checks passed
- G4 Backend compileall:✅ Exit 0
- G4 Frontend pnpm lint:✅ No ESLint warnings or errors
- G4 Frontend pnpm type-check:✅ Clean

**Q3 outstanding minor closeout**(per Chris 2026-05-02 confirm):
- Tier:**Standard S1** confirmed(per architecture.md §3.2 default)
- Region:**eastus2** confirmed(matches endpoint hostname inferred W1 D2)
- decision-form.md Q3 status:`Resolved (pending tier+region)` → `Resolved (full)`(R4 sync,this session)

**R8 P1 ops window check**(per Chris confirm yes opportunity):
- Attempted `pip install -e backend[dev]` 2026-05-02 evening
- Result:**Confirmed still blocked** — `IncompleteRead(0 bytes read, 10911340 more expected)` 同 W1 D2 完全相同 pattern。Chris 仍喺 corp network(no VPN/hotspot active 此 session)
- Decision:R8 status unchanged,F2 pytest + F7 unit tests carry to W2 F10(per W02 plan)
- R8 mitigation P1 / P2 仍 pending Chris ops decision in W2

**Phase artifact closeout**:
- W01 progress.md retro section finalized(this entry)
- W01 progress.md frontmatter `status: in-progress → closed`
- W01 checklist.md cross-cutting items tick'd
- RISK_REGISTER.md R8 entry retest result + Langfuse new finding documented
- W02 plan.md flip `status: draft → active`(Chris 2026-05-02 evening sign-off)
- W02 progress.md Day 0 entry updated with sign-off mention

### Decisions / OQ Resolved

- **OQ-Q3 Resolved (full)**:tier Standard S1 + region eastus2 confirmed by Chris 2026-05-02 evening session;decision-form synced(R4)
- **Decision** — early closeout(D5 work compressed into D4 末日同日 2026-05-02):per Chris session decision,non-architectural,plan changelog 唔需要 entry(scope unchanged,只係 timing compress)。原 plan §5 day breakdown D5 date 2026-05-04 改為 effective 2026-05-02;W2 D1 仍按 plan = 2026-05-05 Tue 開始
- **Decision** — Langfuse unhealthy 暫時唔 file BUG-001(per PROCESS.md §1.4 R1.bugfix Bug-fix workflow 需要 Chris 確認 severity)。先 document 為 D5 finding + W2 carry-over,Chris W2 D1 早段 triage:若 reproduce → BUG-001 instance(候選 Sev3 minor degraded);若一次性 → close
- **Decision** — R8 confirmed unchanged after retest;F8 / F10 / F11 carry-overs 仍按 W02 plan 執行,P1 ops window 等 Chris 安排

### Blockers

- 🔴 **R8 Ricoh corp proxy**:retest 確認仍 active,W2 D1 Chris ops decision required(P1 VPN/hotspot OR P2 IT whitelist)
- 🟡 **Langfuse health degradation**(NEW)— W2 D1 早段 Chris triage,若 reproduce 開 BUG-001
- 🟡 **R10 Q2 sample**:partial unblock W1 D4(F6/Q17/Q18 cleared);F8 Docling 仍 W2 D2 plan

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| Pre-flight G3+G4 verify | 0.3 | 0.5 | +0.2h | Langfuse unhealthy investigation surface |
| R8 P1 retest attempt | 0.2 | 0.3 | +0.1h | Same `IncompleteRead` pattern,no progress |
| Q3 confirm + decision-form sync(R4) | 0.2 | 0.2 | 0 | 1 cell + dashboard update |
| W01 retro finalize + status flip | 0.5 | 0.5 | 0 | D4 draft already 80% complete |
| W02 plan flip draft→active + progress sign-off | 0.3 | 0.3 | 0 | 1-line edit each |
| RISK_REGISTER R8 retest + Langfuse note | 0.3 | 0.3 | 0 | 2 small entries |
| Closeout commit | 0.2 | 0.2 | 0 | Single commit batch |
| **Total D5 (compressed)** | **2.0** | **2.3** | **+0.3h** | Langfuse surprise added 0.2h investigation |

### Commits

| Hash | Subject |
|---|---|
| `(this commit)` | docs(planning): W1 closeout retro + W02 plan status=active |

---

## Day 4 — 2026-05-02

> Status: **F9 Path A executed** — Q2 sample manuals 到位 + F9 Azure AI Search index 創建 success(C03 first-touch shifted from W2 D1 → W1 D4 because Q3 unblocked early)。

### Done

**Q2 Sample Inventory**(R10 partial unblock):
- 6 .docx Drive Finance modules uploaded to `docs/06-reference/01-sample-doc/`:AR / AP / FA / CB / GL / BM(380KB-10.6MB,total ~36MB)
- F6 inspector script run on all 6 → Q17/Q18 finding:
  - **Heading style coverage ~3% only**(< 5%)— Drive manuals 用 hardcoded font size 多過 Heading style → C01 ingestion 設計 implication:layout-aware chunker 唔可以單靠 Heading style detect section,需 fallback to font-size heuristic 或 visual layout
  - **890 embedded images aggregate**(868 PNG + 18 SVG + 4 EMF)— PNG dominant ✅,EMF(4)需要 Pillow conversion path(per C01 design note §4 edge case)
  - 6 docs total **5009 paragraphs + 156 tables**

**F9 — Azure AI Search Index 創建**(C03 first-touch):
- `backend/indexing/schema.json` extracted from spec §3.6(18 fields + HNSW + semantic config,literal source-of-truth for index lifecycle)
- `scripts/create_index.py` REST CLI(stdlib only — `urllib.request` per C03 design;no SDK / pip dep,bypass R8 corp proxy)
  - Subcommands:`create` / `get` / `delete --yes`
  - Minimal `.env` loader(no python-dotenv dep)
  - Reads `AZURE_SEARCH_ENDPOINT` + `AZURE_SEARCH_ADMIN_KEY`
- `python -m scripts.create_index create` → **HTTP 201** ✅(2026-05-02 14:xx local)
- `python -m scripts.create_index get` → 18 fields + ekp-vector-profile + ekp-semantic-config ✅
- C03 design note bumped `v0-draft → v1-active`(per CC-5)
- ruff check ✅ + ruff format ✅ + compileall ✅

### Decisions

- **Schema literal as `backend/indexing/schema.json`**(non Python dict in `schemas.py`)— easier diff against spec §3.6 JSON,單一 source of truth,W2 schema validation 可以 direct compare
- **API version `2024-07-01`** stable GA(non preview)— preview API 對 Tier 1 唔需要,stable 更穩定
- **`.env` loader minimal stdlib**(non python-dotenv)— avoid R8 corp proxy block;`os.environ.setdefault` 唔覆蓋 shell-set vars
- **C03 status v0-draft → v1-active**(per CC-5)— design contract validated by real Azure AI Search creation,18 fields + HNSW + semantic config 全部 match;W2 D2 加 `IndexService` wrap class 後可 v1-active → v2-stable

### Blockers(updated)

- 🟡 **R10 Q2 sample**:partial unblock(F6 / Q17 / Q18 cleared);F8 Docling parser 仍 pending W2 D2(plan 內順序)
- 🔴 **R8 Ricoh corp proxy on PyPI**:仍 active,F2 pytest + F7 unit tests 仍 deferred — but R8 mitigation 證明可用 pure stdlib 路徑(F9 today demo)
- 🚫 **Q3 outstanding minor**:tier + region 仍 awaiting Chris confirm(non-blocking,index already created)

### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| Q2 sample inventory + F6 run | 0.5(Q2 unblock arrived)| 0.3 | -0.2h | Inspector pre-built W1 D1 |
| Schema literal extract | 0.5 | 0.3 | -0.2h | Direct copy from spec |
| `create_index.py` impl | 1 | 0.7 | -0.3h | stdlib clean |
| Index creation + verify | 0.3 | 0.2 | -0.1h | First try success |
| C03 design note bump + planning artifact updates | 0.5 | 0.3 | -0.2h | — |
| **Total D4 Path A** | **2.8** | **1.8** | **-1h** | Path A faster than estimated |

### Commits(this turn)

| Hash | Subject |
|---|---|
| `(this commit)` | feat(c03): create AI Search index ekp-kb-drive-v1 via REST CLI (F9) |

---

## Retro(W1 final — early closeout 2026-05-02)

> **Note**:本 retro 原計劃 D5 末(2026-05-04)final fill,因 Chris 2026-05-02 evening session decision early closeout,D5 work compressed 同 D4 末日同日。Status fields 已 final fill。

### What worked

- **3-layer doc decomposition**(spec / lifecycle / structure)— `architecture.md` v5 frozen + `PROCESS.md v2.0` 3-workflow + `COMPONENT_CATALOG.md` 12-component spine + 11 design notes,zero source-of-truth duplication,reader navigation 3-step
- **Component spine introduction(D3)**:解決 Chris 「閉眼走路」嘅 visibility pain;agent-harness style decomposition 12 components 立即令 W2-W12 forward planning more concrete
- **CC-5 design-first with v0-draft marker**(W1 D3 update from rolling JIT)— 11 component design notes 一次寫齊 implementation reference contract,W2 D1 起每個 first-touch component 有現成 design 可依
- **3-workflow framework**(phase / change / bugfix)+ AI auto-classification + R1-R5 binding rules — workflow ambiguity 從此明確,future任何 task 都有 routing
- **Pivot agility**:D2 H5 incident → P3 pivot path → F7 不 block → D4 F9 unblocked early 從 W2 D1 → W1 D4(節省 W2 capacity)
- **Stdlib-first ops paths**:`scripts/inspect_docx_structure.py`(F6 W1 D1)+ `scripts/create_index.py`(F9 W1 D4)用 pure stdlib 喺 R8 corp proxy block PyPI 嘅環境下持續 deliver value

### What didn't work / unexpected friction

- **Ricoh corp infra ecosystem**:cp314 wheel supply(W1 D1)→ MCR DNS intercept(W1 D1)→ corp proxy on PyPI for cp312 wheels too(W1 D2)+ msstore winget cert mismatch(W1 D2)。每個都需要 5-30 min workaround 嘅 R&D。Total D1+D2 ~3h friction。**D5 retest confirmed R8 仍 active**(同樣 `IncompleteRead(0 bytes)` pattern)
- **Spec frozen vs evolving understanding tension**:`journal.md → progress.md` rename 需要 cross-doc reference update(W1 D3 batch 2)— 妥善處理但證明 naming choice 上線後 reverse 有 cost
- **planning artifact chronological vs structural ordering 嘅 tension**:per-phase folder(W01-foundation/)同 per-component folder(components/)兩個 axis,initially 唔清楚邊個 own 邊個 lifecycle event。後期 CC-1 to CC-7 conventions 鎖死(每個 commit / OQ / risk component-tag),但 W1 早期 commits 缺 component tag 屬於 retroactive cleanup work
- **F8 + F11 hard-blocked Q2 / R8** 持續:F8 Docling install 仲撞 R8(Docling Python lib > 500KB total deps),W2 D2 必須先解 R8 P1/P2
- **Langfuse silent health degradation(D5 surface)**:容器 Up 2 days but `/api/public/health` 在 D2 to D5 期間 silently 變 connection-reset。`docker restart` + `docker compose restart` + `docker compose up -d --force-recreate` 全部 hang 唔生效。冇 alerting → 累積 2 日先發現。**Lesson**:G3 health verification 應該 daily morning gate,non end-of-phase gate

### Surprises / discoveries

- **Drive manuals heading style coverage ~3% only**(W1 D4 F6 finding on 6 sample)— spec §3.3 "heading-aware chunking" 假設 Heading style 覆蓋好,但 Drive 文件實際上用 hardcoded font size 多。W2 D2 chunker design 必須加 font-size heuristic fallback,or visual layout detection。Direct implication:C01 design note `v0-draft` §3 Decisions 需要 update reflect this finding when status v0→v1
- **890 embedded images aggregate(868 PNG + 18 SVG + 4 EMF)**— EMF presence 確認 Pillow conversion path 必要(per C01 design §4 edge case)。比預期密集(~150 images per doc avg)— W2 D3 screenshot dedup design 嘅 SHA256 path 將大幅省 Blob storage
- **Catalog convention CC-1..CC-7 over-engineered initially?**— 7 conventions 初看似多,但 D3 末 14 parallel edits(plan F-tag + decision-form OQ + RISK_REGISTER component tag + CLAUDE.md routing)非常 mechanical,證明 conventions 確實 pay off。No regret
- **`architecture.md` v5 frozen 嘅實際 cost very low**:全部 W1 work cite spec section,zero edit needed to spec body;living evolution 入 RISK_REGISTER + design notes + decision-form。Convention 啱 working
- **Python 3.12 vs 3.14 ABI tag 教訓**:Python 3.14 backward-compat at source-code level 唔等於 binary wheel ecosystem ready。CLAUDE.md §3.1 「Python 3.12+」應該收緊為「Python 3.12 LTS」,W1 D2 update 過程已記錄
- **Early closeout viable when D5 work compresses**(D5 surprise):W1 D4 末 Chris 評估 D5 work mostly governance(retro fill + status flip + R4 sync + verification),冇 implementation work,可以 compress 入 D4 末日同日 commit。W2 D1 仍按 plan 2026-05-05 Tue 啟動,timeline 不變。**Pattern**:phase 末 D-final 純 governance 嘅 phase 將來可以 evaluate same-day closeout(non hardcoded calendar)
- **Langfuse silent degradation(D5 surface)**:G3 D2/D3/D4 都 verified PASS,但 D5 retest 顯示 unhealthy 2 days uptime — degradation 喺 D2 之後 silent 出現冇 alert。**Pattern**:future sprint 應該 daily morning quick health check(curl health endpoint × 3 services)而非依靠 phase-end gate verification

### Carry-overs to W02-multi-format-ingestion

| Item | Reason | W2 owner |
|---|---|---|
| **F8 Docling parser PoC**(was W1 D2 plan) | R10 Q2 sample arrived D4 + R8 corp proxy still blocks Docling install | C01 W2 D2(W02 F1)|
| **F10 embedding pipeline first-pass**(was W1 D5 plan) | R8 blocks Azure SDK install(HTTP REST fallback path ready) | C01 W2 D5(W02 F4)|
| **F11 30 條 ground truth fill**(was W1 D5 plan) | Q2 chunk_id discovery 需要 F8 chunker output 先有 chunk_id | C06 W2 D3-D5 spread(W02 F8)|
| **F2 pytest verification**(was W1 D1 deferred) | R8 corp proxy blocks pip install(D5 retest confirmed) | C08 post-R8-unblock window(W02 F10) |
| **F7 unit tests**(was W1 D2 deferred) | 同上 | C02 同上(W02 F10) |
| **R8 mitigation P1/P2 ops decision** | Affects all above;D5 retest 仍 blocked,Chris ops decision required | Chris ops W2 D1 |
| **Q3 outstanding minor**(tier confirm + region confirm) | ✅ **Closed D5**:tier Standard S1 + region eastus2 confirmed by Chris 2026-05-02;decision-form synced | — |
| **R10 full unblock**(F11 chunk_id discovery 嘅 prerequisite — F8 must run first) | Cascade dependency Q2→F8→F11 | C01 → C06 cascade |
| **Langfuse health degradation**(NEW D5 finding) | Container Up 2 days but health endpoint connection-reset;docker restart hang。W2 D1 早段 Chris triage:reproduce → BUG-001(候選 Sev3);若一次性 → close | Chris W2 D1 morning |

### ADR triggers

- **ADR pending trigger**:F9 stdlib REST CLI(non-SDK)approach in `scripts/create_index.py` — implementation choice driven by R8 corp proxy(non-architectural,per CLAUDE.md §5.1 H1 boundary)。**Verdict**:no ADR(implementation detail,interface stable)
- **ADR pending trigger**:CC-5 convention update(rolling JIT → design-first with v0-draft marker)— process convention,not architectural。**Verdict**:no ADR(PROCESS.md self-evolves per its own §10)
- **ADR pending trigger**:`backend/kb_management/` 3-file package(non single-file per F7 plan)— implementation detail per CLAUDE.md §1.3 surgical。**Verdict**:no ADR
- **W1 全 phase NO ADR triggered**;all decisions either spec-aligned or implementation-detail-only

### Phase Gate result(W1 final verdict 2026-05-02 early closeout)

| # | Target | Final verdict |
|---|---|---|
| **G1** | 11/11 deliverables done OR explicit defer | 🟡 **8 done + 3 explicit defer**:F1 ✅ / F2 ✅(pytest defer)/ F3 ✅ / F4 ✅(Langfuse health degraded D5,新 finding)/ F5 ✅ / F6 ✅(execution unblocked D4)/ F7 ✅(unit tests defer)/ F9 ✅(D4 Path A)/ F8 / F10 / F11 explicit deferred to W02。**Pass-with-deferrals** |
| **G2** | 6/6 critical OQ Resolved | ✅ **PASS 6/6**(Q1/Q2 W1 D1 + Q3/Q4/Q14 W1 D2 + Q3 full D5 with tier+region confirm) |
| **G3** | Local dev stack 3/3 up | 🟡 **2/3** — Postgres ✅ + Azurite ✅ + **Langfuse 🔴 unhealthy**(NEW D5 finding,health endpoint connection-reset 2 days,docker compose restart hang)。**Pass-with-finding**;W2 D1 早段 triage 是否 file BUG-001 |
| **G4** | Backend ruff + frontend lint + type-check 0 errors | ✅ **PASS**(verified D2 + D4 + D5) |
| **G5** | F8 Docling parses 5 sample without unrecoverable error | 🔴 **FAIL — explicit defer to W02 F1**(R8 corp proxy + R10 cascade)|
| **G6** | F11 ground truth ≥ 30 queries validated | 🔴 **FAIL — explicit defer to W02 F8**(cascade after F1+F2+F5 chunk_id discovery)|

**Net W2 kickoff readiness**:**Pass-with-deferrals + 1 new finding**。
- 3 explicit defers(F8/F10/F11 → W02)及對應 carry-over 已寫入 W02 plan §6
- 1 new finding(Langfuse health)→ W02 D1 早段 Chris triage,候選 BUG-001
- W2 D1 仍按 plan 2026-05-05 Tue 啟動,early closeout 唔影響 sprint timeline

### Phase status(2026-05-02 early closeout)

- Closeout commit:`(this commit)` `docs(planning): W1 closeout retro + W02 plan status=active`
- Frontmatter status flipped to `closed`:✅ `status: in-progress → closed`
- Phase W02 kickoff trigger:✅ W02 plan flipped `status: draft → active`(Chris 2026-05-02 evening sign-off);W2 D1 = 2026-05-05 Tue 按 plan 啟動 implementation per PROCESS.md §2.3 daily execution lifecycle



---

**End of W01 progress**(in progress)

> **Migration note**(2026-05-01):此 file 由 `journal.md` rename 為 `progress.md` 對齊 `PROCESS.md v2.0` unified naming(per migration commit)。歷史 Day-0 / Day-1 narrative 入面提到 `journal.md` 嘅 wording 屬當時準確記錄,保留不改(同 commit message 嘅 historical preservation 原則)。

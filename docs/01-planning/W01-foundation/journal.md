---
phase: W01-foundation
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress
---

# Phase W01 — Journal

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

**Commits relevant**:Phase planning framework setup commit pending(framework files 同呢份 journal 一齊 commit)。

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
| Block C Journal Day 3 + checklist tick(this commit)| 1 | 0.5 | -0.5h | Closure simple |
| **Total D3** | **6** | **4.5** | **-1.5h** | Spine introduction 比預期 efficient |

### Commits

| Hash | Subject |
|---|---|
| `220f75a` | feat(planning): introduce 12-component catalog (EKP module spine) |
| `2dc0948` | refactor(planning): tag W01 plan + decision-form OQ + add RISK_REGISTER.md |
| `(this commit)` | docs(planning): W1 D3 journal + checklist tick — component spine done |

---

## Retro(寫於 phase 結束 W1 D5 / 2026-05-04)

### What worked

_(填於 phase 結束)_

### What didn't work / unexpected friction

_(填於 phase 結束)_

### Surprises / discoveries

_(填於 phase 結束)_

### Carry-overs to W02-multi-format-ingestion

_(填於 phase 結束)_

### ADR triggers

_(填於 phase 結束 — W1 暫無 architectural-adjacent decision triggering ADR)_

### Phase Gate result

_(填於 phase 結束 — G1-G6 per plan §3)_

### Phase status

_(填於 phase 結束 — closeout commit hash + status flip + W2 kickoff trigger)_

---

**End of W01 journal**(in progress)

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

> Status: **partial mid-day update** — H5 remediation + Python 3.12 install done;F7 implementation pending(start after this commit);F2/F7 pytest verification deferred to post-pip-install window per P3 pivot。

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

### Actual vs Planned Effort(partial,EOD update follow)

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| H5 remediation(unplanned)| 0 | 1 | +1h | Q3+Q4 secret 提供方式撞 H5 |
| Python 3.12 install | 0.2 | 0.3 | +0.1h | msstore cert retry |
| `.venv` recreate + pip attempts | 0.2 | 1+ | +0.8h | Corp proxy block, P3 pivot |
| F7(在跑緊)| 4 | TBD | TBD | Code-only,no unit test 今日 |

### Commits

| Hash | Subject |
|---|---|
| `09138d4` | chore(security): gitignore env-resources folder + W1 D2 H5 closure |
| `(this commit)` | feat(kb): impl KB CRUD with in-memory backend (P3: tests deferred) |
| `(planned EOD)` | docs(planning): W1 D2 journal closeout(decision-form Q3+Q4+Q14 sync etc.)|

### F7 implementation note(this commit)

- New package `backend/kb_management/` 3-file(plan §2 寫 `kb_service.py` 單檔,implementation 升級為 Protocol-based package)
- 5 endpoints replace 501 stubs;ruff lint + format + compileall ✅
- Unit tests deferred 與 F2 共用 post-pip-install window
- **R3 plan changelog 唔需要新加 entry**:scope unchanged(in-memory KB CRUD per plan F7),只係 file layout 由 1 file 升級為 3-file package(implementation detail,non-architectural)

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

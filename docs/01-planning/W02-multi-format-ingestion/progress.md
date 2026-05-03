---
phase: W02-multi-format-ingestion
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress    # in-progress | closed (set on retro signoff)
---

# Phase W02 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — 2026-05-02: Kickoff(prepared during W1 D4)

**Action**:Phase W02 kickoff(per Chris call to prep during W1 D4-D5 capacity)

- Folder `docs/01-planning/W02-multi-format-ingestion/` created
- Templates copied from `_templates/phase/`(v2.0 unified naming `progress.md`)
- `plan.md` filled with status=`draft`(11 deliverables F1-F11,5 carry-overs from W1,Gate 1 R@5 ≥ 80% hard gate per `architecture.md §6.3`)
- `checklist.md` derived from plan deliverables(75+ atomic items)
- `progress.md` Day 0 entry initialized(this file)
- **Carry-over from W01-foundation retro**:
  - F1 Docling parser PoC(was W1 F8;Q2 unblocked D4,R8 still active)
  - F4 embedding pipeline(was W1 F10;HTTP REST fallback path)
  - F8 ground truth fill(was W1 F11;cascade after F1+F2+F5 for chunk_id)
  - F10 unit tests(was W1 F2+F7;R8 hard prerequisite)
  - Q3 outstanding minor cleanup(tier + region confirm)
  - R8 mitigation P1/P2 ops decision

**Status update 2026-05-02**(W1 D5 early closeout):Chris evening session sign-off W1 retro + approve W02 plan → `plan.md` status flipped `draft → active`(per Plan Changelog 2026-05-02 entry)。W2 D1 implementation start 仍按 plan 2026-05-05 Tue,early closeout 唔影響 sprint timeline。

**W1 carry-overs confirmed in W02 plan §6**:F8(W02 F1)/ F10(W02 F4)/ F11(W02 F8)/ F2 pytest(W02 F10)/ F7 unit tests(W02 F10)/ R8 P1/P2 ops decision(Chris W2 D1 morning)/ Q3 outstanding minor ✅ closed D5 / Langfuse health(W2 D1 morning Chris triage,候選 BUG-001)。

**Commits relevant**:
- `0468040` — `chore(planning): W1 D5 prep — retro draft + W02 kickoff (status=draft)`
- `dc7e37f` — `docs(planning): W1 closeout retro + W02 plan status=active`
- `241fa23` — `docs(planning): replace (this commit) placeholders with actual hashes`

---

### Day 0 evening update — 2026-05-02 (W2 D0 prep variant per Chris call)

**Context**:Chris confirmed 解讀 A 嘅 W2 D0 prep variant — implementation 仍按 plan W2 D1 = 2026-05-05 Tue;今日 evening 用 W1 D5 closeout 後嘅剩餘 capacity 處理 W02 D1 啟動之前嘅 critical path unblock(R11 Langfuse + R8 ops decision)。

#### Done

**BUG-001 instance opened**(per PROCESS.md §4.6 step 1-5):
- AI-classified W1 D5 finding `R11 Langfuse health degradation` 為 Bug-fix workflow → propose `report.md` draft → Chris confirm Sev3 + repro accuracy + reporter line(2026-05-02 evening session)
- mkdir `docs/03-implementation/bugs/BUG-001-langfuse-health-degradation/`(first BUG-NNN instance,sequential 001)
- `report.md` filled,status=`triaged`,Sev3,Chris approved
- `checklist.md` derived from `report.md §7` acceptance + investigation hypothesis paths
- `progress.md` Day 1 entry initialized
- **Investigation phase pending**(W2 D0 evening cont 或 W2 D1 morning,跟 Chris 取捨)

**R8 ops timeline confirmed**:
- Chris W1 D5 closeout session indicated R8 P1 VPN/hotspot window 要再等幾日(non today / non W2 D1 = 2026-05-05 Tue)
- W02 plan §6 dependency 維持:F1 Docling parser 需要 R8 unblock 才可以 pip install;若 W2 D2 plan date(2026-05-06)R8 仍 blocked → 觸發 F1 fallback path(python-docx + custom layout extractor per W02 plan §2 F1 acceptance)
- F4 embedding pipeline HTTP REST fallback path 已喺 W02 plan §2 F4 內 documented,bypass Azure SDK pip install,W2 D5 仍可 deliver

#### Decisions / OQ Resolved

- **Decision** — `R11 Langfuse health degradation` 升格為 BUG-001 instance per PROCESS.md §4.6(Bug-fix workflow,Sev3 minor degraded)。RISK_REGISTER R11 entry stays 🔴 Open until BUG-001 fix verify
- **Decision** — W2 D1 implementation start date 仍按 plan 2026-05-05 Tue,today 屬 W2 D0 evening prep(non implementation start)。W02 plan day breakdown unchanged
- **Decision** — F1 fallback path activation contingency 提早 surface:若 W2 D2(2026-05-06)R8 仍 blocked → switch to python-docx + custom layout extractor;W02 plan §2 F1 acceptance criteria 已 cover both paths,non plan changelog
- **No OQ resolved this entry**(R8 ops 仲未 finalize,Q5/Q11/Q15-21 仍 Open per W2 spread)

#### Blockers

- 🔴 **R8 Ricoh corp proxy**:仍 active,Chris ops decision pending(timeline = "再等幾天")。F1 Docling install path 待 W2 D2 重新 evaluate
- 🟡 **BUG-001 investigation phase pending**(R11 root cause TBD)

#### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| BUG-001 triage(report draft + Chris round-trip + mkdir + 3 docs fill)| 0.5 | 0.4 | -0.1h | Template-driven |
| W02 progress D0 evening update(this entry)| 0.2 | 0.2 | 0 | — |
| **Total D0 evening** | **0.7** | **0.6** | **-0.1h** | Pre-investigation only |

#### Commits

| Hash | Subject |
|---|---|
| `c4473b2` | chore(bugfix): open BUG-001 langfuse health degradation (Sev3 triaged) |

---

### Day 0 evening update — 2026-05-03 (R8 mitigation via home network)

#### Done

**R8 unblock investigation + execution**(home network 2026-05-03):
- Chris pivot home network(disconnect GlobalProtect VPN + connect HKBN home WiFi)
- Network diagnostics confirm:default gateway `192.168.50.1` + public IP `119.247.237.123`(HKBN consumer range)+ no GlobalProtect tunnel in route table
- Test pip download mypy 1.20.2 (10.9MB) → ✅ **15.5 MB/s success first-try**(同 W1 D1/D2/D5 期間 corp 網絡 0 bytes read 完全相反)
- **Root cause refined**:R8 真 root cause 唔係 corp proxy 本身,而係 corp VPN(GlobalProtect)SSL inspection / stream-level interception layer。Disconnect VPN + home ISP direct → R8 disappear
- Batch installed all W2 deps:`pip install -e backend[dev]`(dev tools mypy + pytest + ruff)+ `pip install docling`(W2 F1 Docling parser ~100MB)+ `pip install azure-search-documents azure-identity openai`(W2/W3 Azure cloud SDK)
- **All wheels cached locally** — future corp 網絡 install 可用 `--no-index --find-links` from `.venv\Lib\site-packages` cache bypass

**F2 W1 D1 deferred verification unblocked**(commit batch this session):
- `pytest tests/test_api_skeleton.py` first run → **1 collection error**:`NameError: Fields must not use names with leading underscores`(Pydantic v2.13.3 strict naming on `documents.py:19 _file: UploadFile`)
- Investigated:5 stub routes 同樣 pattern — chunks/documents/eval/feedback/query 全部用 `_<name>` prefix suppress unused-arg linter,W1 D1 寫 stub 時 Pydantic v2.x 未 enforce strict 至 instantiation level
- Fix:rename to `payload` / `file`(match kb.py:22 既有 convention)+ 加 `_ = payload` suppress unused-arg → commit `c38710f`
- Re-run pytest → 1 fail:`test_kb_list_route_registered_returns_501` 預期 501 但 returns 200(W1 D2 F7 commit `c6ca6e3` upgrade `/kb` 做 in-memory CRUD;test 寫 W1 D1 stale)
- Fix:update test 為 `test_kb_list_route_returns_empty_in_memory` 預期 200 + empty list → commit `0a2673d`
- Final verify:**8/8 pass**(F2 W1 D1 deferred 完全 closed)

**Risk + Plan artifact updates this session**:
- RISK_REGISTER R8 status:🔴 Open → 🟢 **Mitigated 2026-05-03**(P1 home network)+ root cause refined entry + side-effect findings logged
- W02 checklist F10:`pre-condition R8 mitigated` ✅ + `pip install` ✅ + `pytest 8/8 pass` ✅;F7 unit tests仲 pending(implementation 期間補,non R8 blocker)
- W02 progress.md Day 0 evening cont entry(this entry)

#### Decisions / OQ Resolved

- **Decision** — R8 root cause refined to corp VPN SSL inspection(non corp proxy itself);home network direct = mitigation path verified。RISK_REGISTER R8 status flipped 🔴 → 🟢 mitigated
- **Decision** — Pydantic v2.13.3 strict naming compat fix 屬 trivial bug fix(< 30min,5 routes 一致 pattern,behavior unchanged 仍 raise 501)— per PROCESS.md §1.4 trivial workflow,non BUG-NNN instance(R1.bugfix exception condition met)
- **Decision** — Stale `test_kb_list` 屬 forgotten test sync after F7 implementation,fix in same commit batch(test/api scope)
- **Decision** — F7 unit tests(`tests/kb_management/`)defer 到 W2 D2-D3 KB Manager Azure backend swap 期間一併寫(per W02 checklist F10 partial close)
- **No new OQ resolved**(R8 status update non-OQ)

#### Blockers

- ✅ R8 cleared(P1 mitigated)
- 🟡 F7 unit tests pending W2 implementation 一併寫(non-blocking,W02 plan §6 carry-over轉化為 W02 F10 partial close)
- 🟡 R10 + Q5 + Q11 + Q15-21 仍 unchanged

#### Actual vs Planned Effort

| Item | Planned (h) | Actual (h) | Variance | Note |
|---|---|---|---|---|
| R8 P1 home network attempt + diagnostics | 0.3 | 0.5 | +0.2h | PowerShell `curl` alias confusion + line-wrap retry |
| Batch pip install(dev + Docling + Azure SDK) | 0.5 | 0.3 | -0.2h | Home network fast 15.5 MB/s,5min total |
| Pydantic v2.13 compat fix(5 routes) | 0.5 | 0.4 | -0.1h | grep pattern + 5 parallel Edit batched |
| Stale kb test fix | 0.1 | 0.1 | 0 | 1-line update + docstring |
| RISK_REGISTER + W02 checklist + W02 progress update | 0.3 | 0.3 | 0 | Standard documentation |
| **Total D0 evening 2026-05-03** | **1.7** | **1.6** | **-0.1h** | Surface 2 side-effect bugs but trivial scope |

#### Commits

| Hash | Subject |
|---|---|
| `c38710f` | fix(api): rename _<name> → payload in 5 stub routes (Pydantic v2.13 compat) |
| `0a2673d` | test(api): update kb list test for W1 D2 F7 in-memory impl (no longer 501) |
| `740de4c` | chore(infra): R8 mitigated via home network — F2 W1 deferred unblocked |

---

### Day 0 cont — 2026-05-03 evening: Option A date-shift approved + W2 D1 immediate kick-off

**Context**:Chris call to start W2 D1 immediately — W2 D0 prerequisites all clear(R8 mitigated,Docling installed,F2 W1 verified,BUG-001 closed,Q3 minor closed)。Option A 揀(嚴格 5-working-day shift):D1-D5 整體提早 2 日,D1=2026-05-03 Sun → D5=2026-05-07 Thu。

**Plan artifact updates**(per CLAUDE.md §10 R3 no silent drift):
- `plan.md` frontmatter `start_date: 2026-05-05 → 2026-05-03`,`end_date: 2026-05-11 → 2026-05-07`
- `plan.md` §5 Day-by-Day Breakdown table 同步更新(D1 Sun ... D5 Thu)
- `plan.md` §7 Plan Changelog 加 2026-05-03 entry(Chris approved)
- `plan.md` lifecycle reminder 更新提及 D1 = 2026-05-03 Sun
- `progress.md` Day 1-5 entry headers 同步更新
- `progress.md` retro section header 改 W2 D5 末 / 2026-05-07

**Implementation start**:呢條 entry commit 後,即時 transition 入 Day 1 entry,start F1 Docling parser PoC implementation。

---

## Day 1 — 2026-05-03 (Sun)

_(待 W2 D1 起填 — date shifted 2 days earlier per plan changelog 2026-05-03)_

### Done
### Decisions / OQ Resolved
### Blockers
### Actual vs Planned Effort
### Commits

---

## Day 2 — 2026-05-04 (Mon)

_(同上)_

---

## Day 3 — 2026-05-05 (Tue)

_(同上)_

---

## Day 4 — 2026-05-06 (Wed)

_(同上)_

---

## Day 5 — 2026-05-07 (Thu)

_(同上 + retro draft 開始)_

---

## Retro(填於 W2 D5 末 / 2026-05-07)

### What worked
_(W2 D5 末 fill)_

### What didn't work / unexpected friction
_(W2 D5 末)_

### Surprises / discoveries
_(W2 D5 末)_

### Carry-overs to W03-chat-retrieval-citation
_(W2 D5 末)_

### ADR triggers
_(W2 D5 末)_

### Phase Gate result(per plan.md §3)
- **G1 Gate 1 R@5 ≥ 80%**:_(W2 D5 末 fill — pass/fail + value)_★ critical
- G2-G6:_(W2 D5 末)_

### Phase status
- Closeout commit:_(W2 D5 末)_
- Frontmatter status flipped to `closed`:_(W2 D5 末)_
- Phase W03 kickoff trigger:_(W2 D5 末)_

---

**End of W02 progress**(Day 0 prep stage,daily Day-N entries to follow W2 D1 onwards)

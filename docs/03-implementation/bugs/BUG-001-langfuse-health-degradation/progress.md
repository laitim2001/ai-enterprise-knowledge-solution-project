---
bug_id: BUG-001
report_ref: ./report.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# BUG-001 — Progress

> Investigation → fix → verify timeline。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 1 — 2026-05-02 (W2 D0 prep — triage)

### Done
- BUG-001 instance opened per PROCESS.md §4.6 step 3-5
- `report.md` filled,Sev3 confirmed by Chris W1 D5 closeout session
- `checklist.md` derived from `report.md §7` acceptance + investigation hypothesis paths
- Reproduction confirmed locally(✅ already 5x replication W1 D5 pre-flight)

### Diagnosis update
- Hypothesis options listed in `report.md §6`(可能性 1-4):Langfuse process crash / docker healthcheck no auto-restart / Postgres pool exhaustion / Volume corruption / Docker Desktop daemon unresponsive
- **Investigation pending W2 D0 evening session step**:start with `docker logs --tail 100` + `docker inspect` + Docker Desktop daemon state check

### Decisions
- **Severity Sev3**(per PROCESS.md §4.5):Langfuse 唔係 user-facing feature;observability stack 屬 dev workflow infra
- **Workflow Bug-fix per PROCESS.md §4**:report.md → checklist → progress lifecycle;non Phase work / non Change request
- **R11 RISK_REGISTER entry stays open** until BUG-001 closed;status flip 🔴 → 🟢 at fix verify

### Blockers
- None at triage stage(investigation 可由 AI 即執行,non Chris ops dependency)

### Effort
- Planned:0.5h triage + 0.5h investigation start;Actual triage:0.4h(template fill + Chris confirm round trip)
- Investigation time-box:1h initial(if root cause not surfaced in 1h,re-evaluate scope)

### Commits
| Hash | Subject |
|---|---|
| `(this commit)` | chore(bugfix): open BUG-001 langfuse health degradation (Sev3 triaged) |

---

## Day 1 evening cont — 2026-05-02 (investigation phase 完成)

### Done
- 5 read-only diagnostic commands run(per checklist Investigation section):
  1. `docker logs --tail 50 ekp-langfuse` → silent hang(diagnostic finding,not failure)
  2. `docker inspect ekp-langfuse` → silent hang(same)
  3. `docker version` → 28.5.1 normal(daemon responsive)
  4. `docker system df` → 41GB images / 6.8GB volumes / no exhaustion
  5. `docker ps -a` → ★ orphan container `935ba7f473df_ekp-langfuse`(Created state,3h ago)surfaced
- Postgres healthy independently confirmed(`docker logs --tail 5 ekp-postgres` returns actual log lines)— 排除 Postgres-side root cause 假設
- Status flip:`triaged → investigating`(report.md frontmatter)
- Root cause confirmed in `report.md §6` + report changelog entry

### Diagnosis update
- **Initial hypothesis 4 種 narrowed down to 1**:
  - ❌ 可能性 1(Langfuse v2 known issue):non-disprove,但 secondary cause
  - ❌ 可能性 2(Postgres pool exhaustion):**disproved**(Postgres healthy)
  - ❌ 可能性 3(Volume corruption):**disproved**(`docker system df` 正常)
  - ❌ 可能性 4(Docker Desktop daemon-wide):**disproved**(other commands work)
  - ✅ **Confirmed**:**Daemon IPC corruption specific to ekp-langfuse zombie container** + **orphan container deadlock state**(see report §6)

- 新 finding(non-original hypothesis):**orphan container `935ba7f473df_ekp-langfuse`** from previous failed force-recreate command stuck Created state。雙 container deadlock — old zombie 仲 bound name + port 3000,new orphan 永遠 stuck Created waiting for old removal,而 old removal 撞 IPC hang

### Decisions
- **Fix Path A first(low cost):`docker rm -f --time 0` + clean compose up**(`--time 0` skips graceful stop SIGTERM ack,bypass IPC hang)。Postgres backing volume `langfuse-postgres-data` 獨立於 container lifecycle,destructive `rm -f` 不會 lose 過去 trace history(W1 期間 anyway 冇 produced traces)
- **Fix Path B fallback:Docker Desktop GUI restart**(若 Path A 失敗,~5min disruption to all docker workflows,但 EKP 以外 containers 全 Exited per `docker ps -a`,影響 contained)
- **Post-fix improvement:add `restart: unless-stopped` to docker-compose.yml**(防止 future zombie state no-auto-restart pattern;原 spec 冇 restart policy,係 W1 D1 `f7ba973` 後遺問題)
- **Pause before destructive fix step**:Path A 嘅 `docker rm -f` 屬 destructive(force kill + remove containers)即使 reversible。Per CLAUDE.md "Executing actions with care",surface fix proposal 等 Chris explicit confirm 先 execute Path A

### Blockers
- 🟡 **Awaiting Chris approval** for destructive fix step(Path A `docker rm -f --time 0` × 2 + clean recreate)— low risk(reversible,Postgres volume safe)but courtesy confirm

### Effort
- Investigation phase planned:1h time-box;actual:0.4h(diagnostic batch in parallel + finding fast surface via `docker ps -a` orphan discovery)
- Variance:-0.6h(parallel diagnostic + clear orphan signal saved time)

### Commits
| Hash | Subject |
|---|---|
| `c4473b2` | chore(bugfix): open BUG-001 langfuse health degradation (Sev3 triaged) |
| `(this commit pending)` | chore(bugfix): BUG-001 investigation — root cause confirmed (zombie + orphan deadlock) |

---

## Day 2 — TBD (fix phase)

_(Path A execution + verify,or Path B fallback — 待 Chris approval)_

---

## Closeout(填於 status=closed)

### Root Cause(final)
_(待 investigation 完成填)_

### Fix Summary
_(待 fix 完成填)_

### Regression Test
_(N/A unit test;mitigation = daily morning health check ritual + recovery procedure in C07/C12 design notes)_

### Lessons
_(待 closeout 填)_

### Component design note status updates
_(待 fix landing — C07 / C12 可能 status bump or recovery procedure section 加入)_

---

**End of BUG-001 progress**(in progress)

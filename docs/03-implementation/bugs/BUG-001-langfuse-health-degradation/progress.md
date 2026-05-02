---
bug_id: BUG-001
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
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

## Day 1 evening cont — 2026-05-02 (Path A executed — partial success,escalate Path B)

### Done
- Status flip:`investigating → fixing`
- **Path A.1** `docker rm -f 935ba7f473df_ekp-langfuse` → ✅ exit 0,orphan removed cleanly
- **Path A.2** 3 個 variant 嘗試:
  - `docker rm -f ekp-langfuse` → timeout 90s exit 124
  - `docker stop -t 1 + docker rm` → both timeout exit 124
  - `docker kill -s KILL` → timeout exit 124
- ✅ **Confirmed orphan deadlock theory**:A.1 success(orphan IPC OK)+ A.2 全 fail 證明 zombie 個 daemon-side record 完全 corrupt;orphan 唔 share 同樣 IPC stuck state
- ❌ Path A definitively cannot remove zombie ekp-langfuse via CLI
- Update report.md §6 + checklist Investigation/Fix sections with Path A result
- Status pause:**Path B requires Chris GUI action(Docker Desktop restart),AI 做唔到**

### Diagnosis update
- Initial Path A premise(SIGKILL via `rm -f` bypass IPC)被 disproved by `docker kill -s KILL` test
- Real conclusion:**daemon-side container record corruption 比預期更深** — daemon process 維持該 record 嘅 reference 但無法接受任何 mutation operation;只有 daemon-level recycle(restart Docker Desktop)可以 force daemon flush stale records
- Postgres + Azurite 不受影響(non-corrupt records)— Path B 重啟 daemon 對佢哋只係 transient outage,不 lose data(volumes intact)

### Decisions
- **Escalate Path B** via Chris manual GUI action(Settings → Restart Docker Desktop)— per CLAUDE.md "Executing actions with care",我等 Chris confirm 再 walk through B.1-B.5 sequence
- **Path A.1 partial success kept**(orphan gone)— 不需 reverse,B 之後 fresh init 唔再衝突
- **No status flip to verifying yet**(Path B 仲未 execute,fix incomplete)— `report.md` status remains `fixing`

### Blockers
- 🟡 **Awaiting Chris GUI action**:Docker Desktop Settings → Restart(我 walk-through Path B steps after Chris ready)
- 🟡 R8 + R10 仍 unchanged(orthogonal to BUG-001)

### Effort
- Path A planned:5min;actual:6min(3 variants tested + state verify)
- Variance:+1min(額外 attempt `docker kill -s KILL` 確認 SIGKILL 都 hang)

### Commits
| Hash | Subject |
|---|---|
| `c4473b2` | chore(bugfix): open BUG-001 langfuse health degradation (Sev3 triaged) |
| `9f20236` | chore(bugfix): BUG-001 investigation — root cause confirmed |
| `(this commit pending)` | chore(bugfix): BUG-001 Path A executed — orphan removed, zombie escalates Path B |

---

## Day 1 final — 2026-05-02 (Path B executed,VERIFIED FIXED,closeout same-day)

### Done
- Chris GUI restart Docker Desktop ✅(daemon recycle)
- B.1 verify post-restart:`docker ps -a` 顯示 ekp-langfuse + ekp-postgres `Exited (255) 2 min ago`(zombie cleared)
- B.2 attempt 1:`docker compose up -d`(full)→ ❌ Azurite MCR pull 503(R9 pattern resurfaced)
- B.2 attempt 2:`docker compose up -d postgres langfuse`(skip azurite,npm fallback running)→ ✅ Postgres Healthy + Langfuse Started
- B.3 poll-and-wait Langfuse boot:`until curl -sf ...; do sleep 3; done`(~60s actual)
- B.4 verify HTTP 200:`{"status":"OK","version":"2.95.11"}` returned cleanly
- B.5 sustained 30s re-verify:still HTTP 200
- Status flips:`fixing → done`(report.md frontmatter)+ `in-progress → closed`(checklist + progress frontmatter)
- RISK_REGISTER R11 entry status:🔴 Open → 🟢 Closed 2026-05-02

### Diagnosis update(final)
- **Root cause confirmed final**:Daemon-side container record corruption + Langfuse Node.js zombie process state(non-exit,bypasses Docker `restart: unless-stopped` policy detection)+ orphan container deadlock from previous failed force-recreate
- **`restart: unless-stopped` already-set finding**:docker-compose.yml Langfuse service 早已 set restart policy(per W1 D1)。但 Docker restart policy 只 trigger on **exit code**,zombie process 唔 exit(只 hung)→ 政策 not effective for this failure mode。**Mitigation**:recovery procedure(Path B GUI restart)係實際 mitigation,non architectural fix
- **R9 MCR pattern confirmed persistent**:即使 daemon restart,MCR (`southeastasia.data.mcr.microsoft.com`)仍係 Ricoh corp DNS intercept blocked → 任何 future `docker compose up -d` 起 azurite Docker image 會 503;workaround = `up -d postgres langfuse`(specific services skip azurite)+ 繼續用 npm Azurite fallback

### Decisions(closeout)
- **Postmortem.md defer**:Sev3 encouraged not mandatory;defer to W2 末 retro batch 因 R8/R9/R11 共同屬 Ricoh corp infra ecosystem trio,合 post-mortem 一齊寫 surface 共通 pattern + ops mitigation roadmap
- **C07/C12 design note 更新 deferred to W2 carry-over**(non-blocking for BUG-001 closeout;W2 D1 morning batch update with daily health check ritual + recovery procedure section)
- **`restart: unless-stopped` 不需新增**(已 set per W1 D1)
- **Daily morning health check ritual** finalize:W2 D1 morning routine = `docker ps --format "{{.Names}}: {{.Status}}"` + `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/api/public/health`(2 line check)

### Blockers
- None at closeout(BUG-001 done,W2 D1 morning carry-over items 屬 non-blocking design note polish)

### Effort
- Investigation 0.4h + Path A attempts 0.1h + Path B execution 0.2h + closeout 0.3h = **1.0h total**
- Planned:1h time-box(triage 0.5h + investigation+fix 0.5h);actual:1.4h(triage 0.4h + invest 0.4h + Path A 0.1h + Path B+closeout 0.5h)— +0.4h variance from 額外 Path A.2 retries + Path B MCR retry

### Commits
| Hash | Subject |
|---|---|
| `c4473b2` | chore(bugfix): open BUG-001 langfuse health degradation (Sev3 triaged) |
| `9f20236` | chore(bugfix): BUG-001 investigation — root cause confirmed |
| `e815556` | chore(bugfix): BUG-001 Path A executed — orphan removed, zombie escalates Path B |
| `(this commit pending)` | fix(c07): BUG-001 closed — Path B recovery verified, R11 closed |

---

## Closeout(填於 status=closed)

### Root Cause(final)
**Two-layer failure**:
1. **Layer 1**:Langfuse v2 Node.js process inside container 進入 **zombie state**(non-exit,只 hung — daemon healthcheck 標 unhealthy 但 process 唔 exit)。Docker `restart: unless-stopped` policy 只 trigger on **exit code**,zombie process 唔 exit → policy not effective。
2. **Layer 2**:Daemon-to-zombie-container IPC channel 完全 corrupt(`docker logs` / `inspect` / `restart` / `stop` / `kill -s KILL` 全部 silent hang infinite wait,即使 SIGKILL 都 hang)。Previous user attempt 嘅 `docker compose up -d --force-recreate langfuse` 半成功 created orphan container `935ba7f473df_ekp-langfuse`(Created state)but stuck waiting for zombie removal(which itself hangs)→ 雙 container deadlock state。

### Fix Summary
**Path B Docker Desktop GUI restart**(daemon-level recycle 唯一可行 path,A.1 orphan rm 成功 but A.2 zombie removal 全部 timeout 124 even with SIGKILL)。Recycle 後 daemon flush stale records,zombie 變 `Exited (255)`(killed by daemon),`docker compose up -d postgres langfuse`(skip Azurite MCR-blocked path)成功 fresh init,Langfuse health endpoint 返 HTTP 200 sustained 30s+ stable。Volumes preserved throughout(Postgres data + Langfuse uploads volumes 獨立於 container lifecycle)。

### Regression Test
**N/A unit test**(infrastructure bug,不適合 pytest scope)。
**Substitute mitigation**:Daily morning health check ritual W2+ daily routine —
```bash
docker ps --format "{{.Names}}: {{.Status}}"
curl -s -o /dev/null -w "Langfuse: %{http_code}\n" --max-time 5 http://localhost:3000/api/public/health
```
若 Langfuse health 唔 200 → 早期 detect,Path B recovery procedure ready in `components/C12-devops.md`(W2 D1 morning carry-over to add)。

### Lessons
- **What worked**:
  - Diagnostic batch in parallel(`docker logs` + `inspect` + `system df` + `version` + `ps -a`)quickly surfaced critical orphan container finding(★ central insight via `docker ps -a`)
  - PROCESS.md §4 Bug-fix workflow strictly followed:report.md → confirm severity → mkdir BUG-NNN → investigate → fix attempt → escalate → verify。Process governance prevented "blind retry" rabbit hole
  - **Time-box discipline**:Path A 60-90s timeout per command 防止 infinite hang block AI capacity;TaskStop on stale background tasks recovered context budget
  - Path A → Path B explicit escalation(non auto-pivot)gave Chris transparent visibility on cost/risk before destructive GUI action
- **What slowed us down**:
  - 5 個 stale background docker tasks 喺 W1 D5 期間 stopped 但 belated propagation completion confused initial state assessment 一陣
  - `--time` flag confusion(屬 `docker stop` non `docker rm`)致 Path A.1 第一次 syntax error retry waste 1 attempt
  - Initial hypothesis 4 種(Langfuse v2 issue / Postgres pool / Volume corruption / Daemon-wide)全部 disproved during investigation;real cause(zombie + orphan deadlock)冇喺 hypothesis list,reflect investigation should always include 「`docker ps -a`」first(state snapshot)before specific subcommand poking
- **Patterns to watch for**:
  - **Zombie process state ≠ exit**:Docker `restart: unless-stopped` policy 對 zombie process 唔 effective;Tier 2 升級 Langfuse v3(ClickHouse + Redis topology)可能改變 process model 解 root cause。Watch list:Beta+ phase plan
  - **Daemon-to-container IPC corruption recoverable only by daemon recycle**:Future similar zombie pattern → 立即 escalate Path B GUI restart,non waste time on `docker rm -f` which will hang infinitely
  - **Orphan containers from failed force-recreate**:Always `docker ps -a` after compose up failure to detect orphan stuck Created state
  - **G3 health check 屬 daily routine non end-of-phase**:W1 D5 retro lesson learned 確認 + 加 W2+ daily morning ritual
  - **Stale background task TaskStop discipline**:long-running docker commands 應該 explicit timeout + TaskStop on hang(prevent context bloat from belated completions)

### Component design note status updates(W2 carry-over batch)
- **C07**:no version bump(observability stack design unchanged);**add §4 troubleshooting subsection**:daily morning health check ritual + Path B recovery procedure
- **C12**:no version bump(infra design unchanged);**add §4 troubleshooting subsection**:zombie container + orphan container deadlock recovery via Path B GUI restart;document `docker compose up -d postgres langfuse`(skip azurite per R9)pattern

---

**End of BUG-001 progress**(closed 2026-05-02)

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

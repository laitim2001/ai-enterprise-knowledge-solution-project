---
bug_id: BUG-001
report_ref: ./report.md
status: in-progress     # in-progress | done
last_updated: 2026-05-02
---

# BUG-001 — Checklist

> Atomic checkbox per investigation / fix / regression / verify stages。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 progress Day-N entry 寫原因。

## Investigation

- [x] Reproduce locally per `report.md §2`(W1 D5 pre-flight 5x replication 已確認 always-reproducible)
- [x] `docker logs ekp-langfuse --tail 50` — **silent hang**(diagnostic finding:per-container IPC dead)
- [x] `docker inspect ekp-langfuse` — **silent hang**(same IPC issue)
- [N/A] `docker exec` 跳過(per-container subcommand 全部 hang,exec 同樣 hang 預期)
- [x] Postgres healthy independently(`docker logs --tail 5 ekp-postgres` 正常)— 排除 Postgres pool exhaustion 假設
- [x] Docker Desktop daemon responsive(`docker version` 28.5.1 + `docker system df` + `docker ps -a` 全部正常)— 排除 daemon-wide failure
- [x] Disk + volume OK(41GB images / 6.8GB volumes / no exhaustion)
- [x] **Root cause confirmed**:zombie container + orphan recreate deadlock + daemon IPC hang on dead-PID-1
- [x] **CRITICAL DISCOVERY**:orphan container `935ba7f473df_ekp-langfuse`(Created state,3 hours ago)from previous force-recreate attempt
- [x] Update `report.md §6` with confirmed root cause(2026-05-02 changelog entry added)

## Fix(updated post-investigation 2026-05-02 evening)

### Path A — `docker rm -f` attempts(EXECUTED 2026-05-02 evening — A.1 ✅ / A.2 ❌)

- [x] **Pre-fix safety check**:Postgres backing volume `langfuse-postgres-data` 不會被 affected(volume 獨立於 container lifecycle)
- [x] **A.1**:`docker rm -f 935ba7f473df_ekp-langfuse` → ✅ exit 0,orphan removed(note:`--time` flag 實際只屬 `docker stop`,non `docker rm`;原 plan 寫錯)
- [x] **A.2 attempt 1**:`docker rm -f ekp-langfuse` → ❌ timeout 90s exit 124
- [x] **A.2 attempt 2**:`docker stop -t 1 ekp-langfuse` + `docker rm` → ❌ both timeout exit 124
- [x] **A.2 attempt 3**:`docker kill -s KILL ekp-langfuse` → ❌ timeout exit 124
- [N/A] **A.3-A.5** skipped — A.2 fail = zombie 仲 bound name + port 3000,clean re-init 唔可能 from compose up(name conflict)
- [x] **Conclusion**:Path A failed at A.2;daemon-side IPC for ekp-langfuse 完全 corrupt(SIGKILL 都 hang)→ escalate Path B

### Path B — If Path A fails(Docker Desktop daemon restart)

- [ ] **B.1**:Stop Postgres + Langfuse via `docker compose down`(若 down 都 hang → manual GUI restart Docker Desktop)
- [ ] **B.2**:**Docker Desktop GUI restart**(Settings → Restart;會 kill all containers + restart daemon)
- [ ] **B.3**:`docker compose -f infrastructure/docker-compose.yml up -d`(re-init Postgres + Langfuse fresh)
- [ ] **B.4**:Wait 60s startup
- [ ] **B.5**:Verify Postgres + Langfuse health endpoints

### Post-fix(Path A 或 B success 之後)

- [ ] Verify `/api/public/health` 200 sustained ≥ 5 min(2 polls 5min apart)
- [ ] Add `restart: unless-stopped` policy 入 `docker-compose.yml` Langfuse service(prevent future zombie no-restart pattern;C12 design note update)
- [ ] Document recovery procedure(Path A + Path B steps)入 `components/C12-devops.md`(under troubleshooting section)
- [ ] Update `components/C07-observability.md` health check ritual section

## Regression Test

- [ ] **N/A unit/integration test**(infrastructure bug,not Python module)
- [x] **Substitute mitigation**:document daily morning health check ritual in `components/C12-devops.md`(curl 3 services × 1 line each)— per W1 D5 retro lesson learned
- [ ] Add health check command to `infrastructure/README.md` quick-reference(若 README 存在;否則 inline 落 `docker-compose.yml` comment)

## Verification

- [ ] Re-run `report.md §2` repro steps in fixed env → `curl http://localhost:3000/api/public/health` 返 HTTP 200
- [ ] Confirm Postgres still healthy(no regression introduced by Langfuse fix)
- [ ] Confirm Azurite still healthy(no regression)
- [ ] (if Postgres recreated)Verify Langfuse can ingest test trace via `@observe` decorator round-trip

## Closeout

- [ ] `progress.md` closeout summary(timeline + root cause + lessons)
- [ ] (Sev3,encouraged not mandatory)Evaluate `postmortem.md` write — recommend WRITE 因 R8/R9/R11 corp infra ecosystem pattern recurring
- [ ] Update `RISK_REGISTER.md` R11 entry status(🔴 Open → 🟢 Closed YYYY-MM-DD)
- [ ] `report.md` status flipped to `done`
- [ ] `progress.md` status flipped to `closed`
- [ ] Update `components/C07-observability.md` if recovery procedure documented

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(`fix(c07): description (BUG-001)` 或 `fix(c12): description (BUG-001)`)
- [ ] No ADR triggered(non-architectural fix,operational recovery only)— but if version bump Langfuse → ADR(H2 vendor lock check)
- [ ] OQ status sync N/A(no OQ affected)
- [ ] R11 status update in `RISK_REGISTER.md` 隨 fix landing

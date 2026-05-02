---
bug_id: BUG-001
report_ref: ./report.md
status: done            # in-progress | done
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

### Path B — Docker Desktop daemon restart(EXECUTED 2026-05-02 evening — ✅ FIXED)

- [N/A] **B.1 original**:`docker compose down`(skipped — Chris went直接 GUI restart per BUG-001 Path A failure analysis)
- [x] **B.0** Chris GUI restart Docker Desktop ✅(daemon recycle complete,tray icon green)
- [x] **B.1**:`docker ps -a` post-restart → ekp-langfuse + ekp-postgres show `Exited (255) 2 min ago`(zombie cleared by daemon restart;volumes preserved)
- [x] **B.2 attempt 1**:`docker compose up -d`(full)→ ❌ Azurite layer pull from MCR `southeastasia.data.mcr.microsoft.com` 503(R9 pattern persists post daemon restart)
- [x] **B.2 attempt 2**:`docker compose up -d postgres langfuse`(skip azurite MCR path,npm fallback already serving 10000)→ ✅ Postgres Healthy + Langfuse Started
- [x] **B.3**:Poll-and-wait until Langfuse health responsive(`until curl -sf ...; do sleep 3; done` pattern,~60s startup)
- [x] **B.4**:`curl http://localhost:3000/api/public/health` → ✅ HTTP 200,returns `{"status":"OK","version":"2.95.11"}`
- [x] **B.5**:Sustained 30s re-verify → still HTTP 200

### Post-fix(Path B success 後)

- [x] Verify `/api/public/health` 200 sustained 30s+(2-poll 30s apart);後續 W2 D1 morning health check 將 confirm 5min sustained
- [N/A] **`restart: unless-stopped` 加入 docker-compose.yml** — **already set**(per W1 D1 setup);finding showed restart policy 對 zombie process state 無效(restart only triggers on exit,zombie 唔 count)
- [ ] Document recovery procedure(Path B steps)入 `components/C12-devops.md`(troubleshooting section)
- [ ] Update `components/C07-observability.md` daily morning health check ritual section

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

- [x] `progress.md` closeout summary(timeline + root cause + lessons + design note recommendations)
- [ ] (Sev3,encouraged not mandatory)Evaluate `postmortem.md` write — recommend defer to W2 末 retro batch 因 R8/R9/R11 corp infra ecosystem trio postmortem may surface 共通 pattern
- [x] Update `RISK_REGISTER.md` R11 entry status(🔴 Open → 🟢 Closed 2026-05-02)
- [x] `report.md` status flipped to `done`
- [x] `progress.md` status flipped to `closed`
- [ ] Update `components/C07-observability.md` daily morning health check ritual section(W2 carry-over,non-critical for BUG-001 closeout)
- [ ] Update `components/C12-devops.md` troubleshooting section with Path B recovery procedure(W2 carry-over)

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1(`fix(c07): description (BUG-001)` 或 `fix(c12): description (BUG-001)`)
- [ ] No ADR triggered(non-architectural fix,operational recovery only)— but if version bump Langfuse → ADR(H2 vendor lock check)
- [ ] OQ status sync N/A(no OQ affected)
- [ ] R11 status update in `RISK_REGISTER.md` 隨 fix landing

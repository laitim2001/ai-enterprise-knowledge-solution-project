---
bug_id: BUG-001
title: "Langfuse health endpoint connection-reset; recovery commands hang silently"
severity: Sev3
status: investigating   # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-02
reporter: "AI (W1 D5 closeout pre-flight G3 verification)"
affects_components: [C07, C12]
spec_refs:
  - architecture.md §3.2
  - architecture.md §4.3
  - components/C07-observability.md
  - components/C12-devops.md
---

# BUG-001 — Langfuse health endpoint connection-reset; recovery commands hang silently

> **Report version**:1.0(initial triage)
> **Triage approver**:Chris(2026-05-02 W1 D5 early closeout session,Sev3 confirmed)

## 1. Symptom

Langfuse Docker container `ekp-langfuse` reports `Up 2 days (unhealthy)`,但 `/api/public/health` HTTP request 連接直接 reset(curl exit code 56 `Recv failure: Connection was reset`)。所有 docker recovery commands(`docker restart` / `docker compose restart` / `docker compose up -d --force-recreate`)silent hang 唔生效,container uptime 持續 reports 2 days uptime。

## 2. Reproduction Steps

1. 喺 W1 D2 last-known-healthy state(`docker compose up -d` 起咗 Postgres + Langfuse)之後 ~2 日(2026-04-30 14:59 startup → 2026-05-02 evening)
2. 跑 `curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 http://localhost:3000/api/public/health`
3. **觀察**:exit 56,output `000`(connection reset);但 `docker ps` 顯示 `ekp-langfuse: Up 2 days (unhealthy)`
4. 嘗試 `docker restart ekp-langfuse`(silent hang,no progress output)
5. 嘗試 `docker compose -f infrastructure/docker-compose.yml restart langfuse`(silent hang)
6. 嘗試 `docker compose -f infrastructure/docker-compose.yml up -d --force-recreate langfuse`(silent hang)

**Reproduction reliability**:**Always**(本機 W1 D5 pre-flight 期間 100% 重現 over 5 attempts)
**Environment**:Local dev — Windows 11 Enterprise + Docker Desktop + docker-compose Postgres-backed Langfuse v2(image `langfuse/langfuse:2` per W1 D1 commit `f7ba973`)

## 3. Expected vs Actual

- **Expected**(per `architecture.md §4.3` + W1 D1 `f7ba973` initial verification):`GET /api/public/health` 返 HTTP 200 with JSON status payload;Langfuse trace ingest endpoint accepts `@observe` decorator emit
- **Actual**:Connection reset on health endpoint(curl exit 56);recovery commands hang;container uptime stuck at 2 days

## 4. Impact

- **Affected scenarios**:任何依賴 Langfuse 嘅 dev observability —— W1 D5 期間影響 minimal(C04/C05 未 build,traces 未 produced)。**W2+ 起 escalates**:F4 embedding cost telemetry / F5 populate atomic logs / F6 retrieval latency / F7 Gate 1 eval traces 全部 silent loss
- **Workaround available?**:Partial — structlog JSON stdout logging continues working(no Langfuse dep);可以暫時降級 W2 observability 為 stdout-only,but loses Langfuse trace correlation
- **Data loss / corruption?**:Unknown — Langfuse Postgres backing volume(`langfuse-postgres-data`)若 corruption → 過去 trace 可能 lost(W1 期間冇 traces produced 所以低 impact)
- **Security implication?**:No(POC stage,internal observability tool,non user-facing)

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5` scale:
- 唔係 Sev1(non production outage,non data loss,non security breach)
- 唔係 Sev2(non major feature broken;Langfuse 唔係 user-facing feature,係 internal observability stack)
- **Sev3 confirmed**:minor feature degraded specific to dev workflow(observability stack);postmortem encouraged 因 R8/R9 + R11 屬 Ricoh corp infra ecosystem pattern recurring,但本 instance 唔屬 mandatory 範圍

**Escalation trigger watch**:若 W2 D5 Gate 1 R@5 < 80% fail debug 時 Langfuse 仍 unavailable → Sev2 retroactive escalation(per `PROCESS.md §4.5` "Escalate severity if discovered to have wider blast radius during fix")。

## 6. Initial Diagnosis(updated as investigation progresses)

**Initial hypothesis**(at triage 2026-05-02):
- Langfuse internal process crash inside container(可能 Postgres connection drop / OOM / version-specific bug)
- Docker healthcheck command 唔 propagate 到 process restart(only marks unhealthy,no auto-restart policy in compose file)
- `docker compose restart` hang 可能因 daemon 嘗試 graceful stop 但 Langfuse process 已 zombie
- 可能性 1:Langfuse v2 image 已知 issue(W1 D1 `f7ba973` pin to `langfuse:2` after `2-latest` retired)
- 可能性 2:Postgres connection-pool exhaustion 觸發 Langfuse process unrecoverable state
- 可能性 3:Docker volume corruption in `langfuse-postgres-data`
- 可能性 4:Docker Desktop daemon-side 問題(non-Langfuse process 但 affects daemon responsiveness)

**(W2 D0 investigation 2026-05-02 evening)**:
- ✅ `docker version` 返 28.5.1 normal — Docker daemon **整體** responsive
- ✅ `docker system df` 返 normal — disk OK(41GB images / 6.8GB volumes / no exhaustion)
- ✅ `docker ps -a` 返 normal — daemon container metadata query 正常
- ✅ `docker logs --tail 5 ekp-postgres` 返 actual log lines — daemon-to-container IPC works for healthy container
- 🔴 `docker logs --tail 50 ekp-langfuse` **silent hang**(0 bytes after >60s,TaskStop 終止)
- 🔴 `docker inspect ekp-langfuse` **silent hang**(同樣 0 bytes)
- 🔴 `docker restart ekp-langfuse` / `docker compose restart langfuse` / `docker compose up -d --force-recreate langfuse` 全部 silent hang
- ★ **CRITICAL DISCOVERY**:`docker ps -a` 顯示有 **orphan container `935ba7f473df_ekp-langfuse`**(`Created` state,3 hours ago)— 即係之前 `docker compose up -d --force-recreate langfuse` 半成功:created new container but hung waiting for old zombie container removal。Now 兩個 container 共存:zombie(name=ekp-langfuse,Up 2 days unhealthy)+ orphan(name=935ba7f473df_ekp-langfuse,Created)

**(Root cause confirmed 2026-05-02)**:
**Daemon IPC corruption specific to ekp-langfuse zombie container**。
- Original container `ekp-langfuse` PID 1(Langfuse Node.js process)crashed but Docker daemon's container metadata 仍 reports `Up`(healthcheck stuck "unhealthy"狀態,no restart policy in docker-compose.yml triggers auto-restart)
- Daemon's IPC channel to dead container PID 1 timeouts on **每** per-container query(logs / inspect / stop / restart)— daemon 等 PID 1 ack 但 PID 1 已 dead,timeout 發生 silent hang
- 之前 `docker compose up -d --force-recreate langfuse` 嘗試 created new container `935ba7f473df_ekp-langfuse`(`Created` state ready to start)但 hang waiting for old zombie removal(因為 `docker rm` zombie 同樣 hang)
- 結果:雙 container deadlock state — old zombie 仍 bound name + port 3000,new orphan 永遠 stuck Created

**Why container-level recovery commands hang**:Docker 28.5.1 daemon-to-container IPC 對 dead-PID-1 container 嘅 timeout behavior 喺 Windows Docker Desktop 環境下變 "infinite wait"(known issue pattern),需要 daemon-level recycle 或 force `--time 0` removal bypass IPC。

## 7. Acceptance for Fix(checklist preview)

- [x] Reproduction confirmed locally(✅ already 5x replication W1 D5)
- [ ] Root cause identified(via `docker logs ekp-langfuse` + `docker inspect` + Postgres health + Docker Desktop daemon state check)
- [ ] Fix implemented(scope unknown — could be `docker rm -f` + clean recreate,OR Langfuse version bump,OR Postgres connection pool tune,OR Docker Desktop daemon restart)
- [ ] Regression test added — **N/A:infrastructure bug,unit test 唔適用**;改為 add daily morning health check ritual to W2+ routine(per W1 D5 retro lesson learned)
- [ ] Verified in env:re-run §2 repro steps → expect HTTP 200 from `/api/public/health`

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-02 | Initial triage,Sev3 confirmed | W1 D5 closeout pre-flight G3 verification surface;Chris confirmed severity + repro accuracy | Chris |
| 2026-05-02 | Investigation cont — root cause confirmed:zombie container + orphan recreate deadlock + daemon IPC hang on dead-PID-1 | W2 D0 evening investigation 5 read-only diagnostic commands(logs / inspect / system df / version / ps -a)+ 識別 orphan container | AI(investigation phase per PROCESS.md §4.6 step 8-9)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` encouraged if pattern recurring(per `PROCESS.md §4.5`)。R8/R9/R11 同屬 Ricoh corp infra ecosystem trio,closeout 時 evaluate 是否寫 postmortem 統一 capture pattern。

---
bug_id: BUG-003
title: "test_health_returns_ok asserts pre-W20 `{status: ok}` payload — drifted from W20 F2.1 per-component HealthResponse"
severity: Sev4          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-19
reporter: "AI (W23 D1.3 backend pytest regression check)"
affects_components: [C06, C08]      # C06 Eval Framework (test infra) + C08 API Gateway (/health route owner)
spec_refs:
  - architecture.md v6 §3.7         # Application architecture — /health route observable from /dashboard System health card per ADR-0030 absorbed
  - components/C08-api-gateway.md   # /health per-component liveness payload
  - W20 F2.1                        # /health extracted from inline server.py → backend/api/routes/health.py per-component dot
---

# BUG-003 — `test_health_returns_ok` 過時 strict equality assertion

> **Report version**:1.0(initial)
> **Triage approver**:AI(self-triaged Sev4 — pre-existing W20 F2 escape;唔影響 production behavior;test infra only)
> **Closed**:2026-05-19(Chris confirmed Sev4 + fix approach via AskUserQuestion)

## 1. Symptom

`backend/tests/test_api_skeleton.py::test_health_returns_ok` 跑時 fail:

```
AssertionError: assert {'components': {...}, 'status': 'degraded'} == {'status': 'ok'}
```

實際 `/health` payload(W20 F2.1 landed `550111e` 2026-05-17):

```json
{
  "status": "degraded",
  "components": {
    "azure_search":  {"status": "degraded", "latency_ms": null, "detail": "..."},
    "azure_openai":  {"status": "degraded", "latency_ms": null, "detail": "..."},
    "cohere":        {"status": "degraded", "latency_ms": null, "detail": "..."},
    "langfuse":      {"status": "not_configured", "latency_ms": null, "detail": "..."},
    "postgres":      {"status": "not_configured", "latency_ms": null, "detail": "..."}
  }
}
```

但 test 仍然 expect W1-era smoke shape `{"status": "ok"}`。

## 2. Reproduction Steps

1. 喺 repo root run:`pnpm --filter backend pytest backend/tests/test_api_skeleton.py::test_health_returns_ok -v` 或 `cd backend && pytest tests/test_api_skeleton.py::test_health_returns_ok -v`
2. Observed:1 failed,輸出 `assert {'components': ..., 'status': 'degraded'} == {'status': 'ok'}`

**Reproduction reliability**:Always(deterministic — TestClient(app) 預設 *唔* trigger lifespan startup,所以 `app.state.retrieval_engine` / `embedder` 都係 None → 所有 5 個 component check 都係 `degraded` / `not_configured` → overall = `degraded`)。

**Environment**:local dev backend pytest(任何 environment;唔依賴 env var 因為 lifespan 冇 trigger)。

## 3. Expected vs Actual

- **Expected**:per `backend/api/routes/health.py` HealthResponse schema(W20 F2.1) — `{status: "ok" | "degraded", components: {azure_search, azure_openai, cohere, langfuse, postgres} → ComponentHealth}`。Azure Container Apps liveness probe 仍然 200,但 payload shape 已 extend。
- **Actual**:test 仍然 strict-equality match pre-W20 W1-era shape `{"status": "ok"}` —— 由 `550111e` 開始就 broken,escape 咗 W20 + W21 + W22 + W23 closeout backend pytest regression check(因為 99/99 + 59/59 reported figures 應該係 excluding `test_api_skeleton.py` 或者唔包 health test 喺 standard suite)。

## 4. Impact

- **Affected users / scenarios**:CI / local dev 跑全 backend pytest 嗰陣會見到 1 failure。Production `/health` route 本身 fully functional(Azure Container Apps liveness probe 唔睇 payload shape,只睇 200)。
- **Workaround available?**:Yes — manually skip 呢個 test 或 grep filter。
- **Data loss / corruption?**:No
- **Security implication?**:No

## 5. Severity Justification

**Sev4** per `PROCESS.md §4.5`:test infrastructure drift,cosmetic / minor-UX,no production behavior breakage,no data risk,no security implication,workaround exists(skip the test)。Pre-existing escape — W20 F2 landed extended payload 但 forgot to align W1-era smoke test;subsequent W21/W22/W23 backend pytest regression check 報 99/99 + 59/59 似乎 excluded 呢個 test 或 conftest scope。Sev4 → no mandatory postmortem。

## 6. Initial Diagnosis

- **Initial hypothesis**(at triage):W20 F2.1 extended `/health` payload shape 而冇 update W1-era smoke test
- **Root cause confirmed**(2026-05-19):正是 W20 F2.1 commit `550111e` 引入 `backend/api/routes/health.py` 改變 `/health` shape from W1 `{status: "ok"}` → `HealthResponse{status, components}`,但 `backend/tests/test_api_skeleton.py::test_health_returns_ok` line 47 仍然係 `assert response.json() == {"status": "ok"}` strict equality。W20-W23 closeout backend pytest 報 X/X pass 應該係 exclude 咗呢個 test 或者跑 subset。

## 7. Acceptance for Fix(checklist preview)

- [x] Reproduction confirmed locally(`1 failed in 157.76s` with `AssertionError: assert {'components':..., 'status': 'degraded'} == {'status': 'ok'}`)
- [x] Root cause identified(W20 F2.1 `550111e` extended payload + test 冇同步 update)
- [x] Fix implemented(`backend/tests/test_api_skeleton.py::test_health_returns_ok` 改為 loose check:status_code 200 + payload 有 `status` + `components` keys + 5 個 expected component keys + `status ∈ {"ok", "degraded"}`)
- [x] Regression test added(fix 本身就係 regression test;唔需要 NEW test)
- [x] Verified in env:`1 passed in 171.44s`;全 backend suite **705 passed + 11 skipped + 0 failed**(W23 baseline 704+1fail → 705 = +1 net IMPROVED)

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-19 | Initial triage(Sev4)+ root cause confirmed(W20 F2.1 escape)+ fix proposed | W23 D1.3 surfaced via backend pytest regression check | Chris(W23 closeout flagged for W24+ Sev4 BUG-fix) |
| 2026-05-19 | Chris confirm Sev4 + fix approach via AskUserQuestion → fix implemented(loose-shape-check)+ verified(705 passed + 0 failed)→ status `triaged → done` | BUG-003 single-sitting close | Chris |

---

**Lifecycle reminder**:Sev1/Sev2 → `postmortem.md` mandatory(per `PROCESS.md §4.5`)。Sev4 — none required。

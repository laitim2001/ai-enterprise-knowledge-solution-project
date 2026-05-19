---
bug_id: BUG-003
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
---

# BUG-003 — Progress

## 2026-05-19 — triage + diagnosis + fix + verify + closeout(single sitting)

### Done
- Folder + 3 docs created `docs/03-implementation/bugs/BUG-003-test-health-payload-drift/{report,checklist,progress}.md`(per PROCESS.md §4 + `_templates/bugfix/`)
- Triaged Sev4 — test infra drift,no production impact,workaround = skip the test。Per PROCESS.md §4.5 → no mandatory postmortem。
- Root cause confirmed via `backend/api/routes/health.py` Read:W20 F2.1 commit `550111e` 2026-05-17 extracted `/health` from inline `server.py` `{"status": "ok"}` → 5-component `HealthResponse{status, components}` shape per ADR-0030 absorbed + /dashboard System health card per W19 F2 §3.1 item 1。`backend/tests/test_api_skeleton.py` line 47 strict equality `{"status": "ok"}` 未同步 update。
- Chris confirm Sev4 + fix approach via AskUserQuestion 2026-05-19 → flip status `triaged → investigating`。
- **T1** reproduction:`1 failed in 157.76s` confirmed AssertionError diff(degraded payload vs strict `{"status": "ok"}`)
- **T3** fix landed `backend/tests/test_api_skeleton.py`:loose shape check + 6-line inline comment 解釋 W20 F2.1 extended shape rationale + TestClient 唔 trigger lifespan rationale
- **T4** single-test verify:`1 passed in 171.44s`
- **T5** full backend pytest regression check:**705 passed + 11 skipped + 16 warnings in 275.57s**(W23 baseline 704 pass + 11 skipped + 1 fail → 705 pass + 11 skipped + 0 fail = **+1 net IMPROVED**;no NEW failure)
- **T6** mypy:`test_api_skeleton.py` 我嘅 fix 部分冇 NEW mypy error;pre-existing `tests\test_api_skeleton.py:20 _mock_auth_override` return type 缺漏(W7 D2 era)唔屬於 surgical scope per CLAUDE.md §1.3。104 pre-existing baseline mypy errors across 38 files NOT in scope。

### Decisions
- **Loose shape check, NOT strict equality** — TestClient(app) 預設唔 trigger lifespan startup event(無 `with TestClient(app) as client:` context manager)→ `app.state.retrieval_engine` / `embedder` 都 None → 所有 5 component check fall back to `degraded` / `not_configured` → overall = `degraded`。Strict equality 會 break 喺任何 env state 變化下(例:之後若 conftest 加 lifespan fixture)。Loose check 驗證 shape contract,符合 W1-era smoke test 原意(route registered + 200 + sensible payload)。
- **NOT 加 NEW test** — fix 本身就係 regression test(strict-equality → loose check 就 prevent recurrence);per Karpathy §1.2 simplicity first,唔加 speculative test。
- **NOT touch `/health` route 邏輯** — bug 純 test drift,not production behavior issue;per CLAUDE.md §13 surgical changes 只改 test 文件。
- **NOT fix pre-existing mypy errors** — `_mock_auth_override:20` 缺 return type 同 104 baseline errors 喺 38 files 都係 pre-existing,唔屬於 BUG-003 surgical scope。Per Karpathy §1.3 唔順手 refactor。可另立 BUG-XXX 或 CH-XXX 統一 cleanup(future candidate)。

### Acceptance(report.md §7)
- ✅ Reproduction confirmed locally(1 failed → AssertionError diff)
- ✅ Root cause identified(W20 F2.1 `550111e` escape;TestClient 唔 trigger lifespan)
- ✅ Fix implemented(loose shape check;6-line inline comment 解釋 rationale)
- ✅ Regression test added(fix 本身就係 regression check)
- ✅ Verified in env(705 passed + 11 skipped + 0 failed;+1 net IMPROVED vs W23 baseline)

**Verdict**:BUG-003 **CLOSED 2026-05-19**(Sev4;single-sitting triage + fix + verify + closeout)。

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `fix(api): align test_health_returns_ok with W20 F2 /health extended payload — BUG-003` |

---

**End of BUG-003 progress**

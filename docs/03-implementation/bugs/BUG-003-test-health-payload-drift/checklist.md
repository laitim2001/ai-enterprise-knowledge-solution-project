---
bug_id: BUG-003
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-05-19
---

# BUG-003 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## Fix

- [x] **T1** — Reproduction confirmed locally:`pytest backend/tests/test_api_skeleton.py::test_health_returns_ok -v` → `1 failed in 157.76s` with `AssertionError: assert {'components': ..., 'status': 'degraded'} == {'status': 'ok'}`
- [x] **T2** — Root cause confirmed:W20 F2.1 commit `550111e` extracted `/health` from inline `server.py` `{"status": "ok"}` → `backend/api/routes/health.py` per-component `HealthResponse{status, components}` shape;test line 47 strict equality 未同步 update
- [x] **T3** — `backend/tests/test_api_skeleton.py::test_health_returns_ok` 改為 loose shape check:
  - `assert response.status_code == 200`
  - `payload = response.json()`
  - `assert payload["status"] in {"ok", "degraded"}`
  - `assert set(payload["components"].keys()) == {"azure_search", "azure_openai", "cohere", "langfuse", "postgres"}`
  - 添加 6 行 inline comment 解釋 W20 F2.1 extended shape rationale + TestClient 唔 trigger lifespan → shape contract check NOT strict-equality smoke
- [x] **T4** — `pytest backend/tests/test_api_skeleton.py::test_health_returns_ok -v` → `1 passed in 171.44s`
- [x] **T5** — Full backend pytest run regression check:`pytest backend/tests/ -q` → **705 passed, 11 skipped, 16 warnings in 275.57s**(W23 baseline 704+1fail → 705 = **+1 net IMPROVED**;no NEW failure)
- [x] **T6** — mypy strict check on `test_api_skeleton.py`:0 NEW errors(`tests\test_api_skeleton.py:20 _mock_auth_override return type` = pre-existing W7 D2 era,**唔屬於我嘅 surgical scope** per CLAUDE.md §1.3;104 pre-existing baseline errors across 38 files NOT in scope)

## Cross-Cutting

- [x] Commit references `progress.md` entry;component tag `(api)` 對應 C08 per CC-1
- [x] No ADR(test fix only,no architectural / vendor change — H1+H2 not triggered)
- [x] `report.md` status `triaged → done`;this `checklist.md` status `in-progress → done`;`progress.md` written
- [x] No CLAUDE.md / session-start.md update needed at BUG-003 close;§11 Sev4 BUG-fix carry-over flip CLOSED at session-start sync task #27

---

**Lifecycle reminder**:新加 acceptance item 必先入 `report.md §7`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。

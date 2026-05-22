---
bug_id: BUG-008
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-05-22
---

# BUG-008 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## Fix

- [x] **T1** — Root cause confirmed via crash traceback + uvicorn 原始碼:Windows `ProactorEventLoop` 同 `psycopg` async 不相容;**uvicorn `Server.run()` 用 `asyncio_run(serve(), loop_factory=...)`,`loops/asyncio.py::asyncio_loop_factory` 喺 `win32 and not use_subprocess` hard-code `ProactorEventLoop`** → uvicorn 完全無視 event loop policy(初版「set policy」修法已實測失敗)
- [x] **T2** — `backend/api/server.py`:加 `if __name__ == "__main__":` launcher — `win32` 時 `asyncio.run(uvicorn.Server(uvicorn.Config(app, host, port)).serve(), loop_factory=asyncio.SelectorEventLoop)` 繞過 `Server.run()` 嘅 Proactor `loop_factory`;非 win32 行原狀 `server.run()`(`asyncio`/`sys`/`uvicorn` import 喺 `__main__` block 內,ruff 不 flag)
- [x] **T3** — Backend 啟動指令改 `python -m api.server`;`docs/setup.md` §「Backend dev server」+ §4.3 兩處 `uv run uvicorn ...` → `uv run python -m api.server` + BUG-008 註解。**無 unit test** — launch-mechanism change 無法以 unit test 有意義驗證(per Karpathy §1.2 唔寫 contrived test);acceptance = T4 runtime verify
- [x] **T4** — Runtime verify(主 acceptance):`.env` `DATABASE_URL` 已設、`python -m api.server` 啟動 → lifespan 正常完成、無 `InterfaceError` → `/health` `postgres.status` = `ok` → `ekp` DB tables 自動建立(`CREATE TABLE IF NOT EXISTS` on connect)
- [x] **T5** — Test isolation(scope-folded per Chris「方案 A」2026-05-22 — R3):`.env` `DATABASE_URL`(BUG-007 follow-up Postgres wiring)令 pytest 全 suite 切 Postgres-backed → 8 個 in-memory-assuming test fail(`postgres_not_configured` / `kb_list...in_memory` / 5× `test_auth_self_register`)。NEW `backend/tests/conftest.py`:import 時 `os.environ["DATABASE_URL"]=""`(空 env var 喺 Pydantic precedence 覆寫 `.env` file,先於任何 test module import `api.server` 建 `Settings` lru_cache)→ suite deterministic 行 in-memory;Postgres-path test 用 explicit `Settings(database_url=...)` 不受影響
- [x] **T6** — verify gates:backend `pytest tests/` **0 failed**(T5 conftest isolation 後回復)+ `mypy` `server.py` clean + `ruff` `server.py` 零新 error(committed 29 = current 29 個 E402,屬 `truststore` pre-existing pattern)

## Cross-Cutting

- [x] No ADR — H1(無架構/vendor/storage-layout 改動 — Windows-runtime-compat shim;ADR-0023 Postgres backing 設計不變)+ H2(無新 dependency — `psycopg` 早已喺 §5.2 vendor table)均不觸發
- [x] H5 — `.env` 嘅 `DATABASE_URL`(local-dev Postgres password,同 `docker-compose.yml` 一致,非 secret)唔 commit(`.env` gitignored);無 secret / PII 入 code 或 log
- [x] H7 — N/A(純 backend entry-point change,無 frontend / mockup 影響)
- [x] Commit references `progress.md` entry;component tag `(api)` 對應 C08
- [x] `report.md` status `triaged → done`;此 `checklist.md` status `in-progress → done`;`progress.md` written

## 🚧 Out of scope（不修,per report.md §7）

- 🚧 `psycopg` / `uvicorn` 本身 — third-party,行為正確(psycopg 主動拒絕 Proactor 係 by-design)
- 🚧 Linux 路徑 — `win32` guard 之外零改動,production(Azure Container Apps）不受影響
- 🚧 `--reload` 模式喺 OneDrive 上 WatchFiles worker 輸出捕捉問題 — W22+ 已知 infra issue(`docs/setup.md §8.7`),與此 event-loop bug 無關;backend 暫以 no-`--reload` 運行

---

**Lifecycle reminder**:新加 acceptance item 必先入 `report.md §7`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。

---
bug_id: BUG-008
title: "psycopg async mode crashes backend startup on Windows — ProactorEventLoop incompatible, breaks every ADR-0023 Postgres-backed store"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-22
reporter: "AI — surfaced while wiring DATABASE_URL for Postgres persistence (BUG-007 follow-up ops task)"
affects_components: [C08]   # C08 API Gateway (server.py app entry / lifespan) — impact spans every ADR-0023 Postgres-backed store
spec_refs:
  - ADR-0023                  # Postgres-backed KB/users/RBAC/audit persistent store via psycopg
  - architecture.md §4.1      # FastAPI application entry point
---

# BUG-008 — psycopg async crashes backend startup on Windows (ProactorEventLoop)

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev3**(only the `DATABASE_URL`-set Postgres path is affected, and only on Windows;the default in-memory store path is unaffected — the project ran for weeks that way);**Chris confirmed Sev3 + Bug-fix BUG-008 workflow(report + checklist + progress;Sev3 → no postmortem)via chat 2026-05-22**。

## 1. Symptom

設定 `DATABASE_URL`(啟用 ADR-0023 Postgres-backed store)之後,backend 一啟動就 crash:

```
psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in
async mode. Please use a compatible event loop, for instance by running
'asyncio.run(..., loop_factory=asyncio.SelectorEventLoop(...))'

  File "backend/api/server.py", line 106, in lifespan
    await audit_log_backend.prune_expired(90)
  File "backend/storage/audit_log_postgres.py", line 129, in prune_expired
    async with await psycopg.AsyncConnection.connect(...)
ERROR:    Application startup failed. Exiting.
```

uvicorn process exit code 3。Backend 完全起唔到。

## 2. Reproduction Steps

1. 喺 `.env` 設 `DATABASE_URL=postgresql://...`(任何有效 Postgres,本案 `ekp-postgres` docker)
2. `psycopg[binary]` 已安裝入 `backend/.venv`
3. Windows 環境啟動 backend:`.venv/Scripts/python.exe -m uvicorn api.server:app --port 8000`
4. Observed:lifespan startup 行到 `audit_log_backend.prune_expired(90)` → `psycopg.AsyncConnection.connect()` → `psycopg.InterfaceError` → `Application startup failed. Exiting.`(exit 3)

**Reproduction reliability**:Always(deterministic — Windows 預設 event loop policy 固定係 Proactor)。

**Environment**:Windows 11 + Python 3.12;uvicorn no-`--reload`;`psycopg 3.3.4`。**只限 Windows** — Linux(production / Azure Container Apps)預設 event loop 同 psycopg async 相容,不受影響。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| `DATABASE_URL` 已設時 backend 啟動 | lifespan 正常完成,Postgres-backed store 連得上,`/health` `postgres: ok` | lifespan `psycopg.AsyncConnection.connect()` raise `InterfaceError` → startup failed → exit 3 |
| Windows event loop | psycopg async 需要 `SelectorEventLoop` | Windows 預設係 `ProactorEventLoop`(Python 3.8+ Windows 預設)— psycopg async 拒絕運行 |
| `DATABASE_URL` 未設(in-memory)| 正常 | 正常(不受影響 — 確認非 regression)|

## 4. Impact

- **Affected scenario**:任何喺 **Windows** 上啟用 `DATABASE_URL`(ADR-0023 Postgres persistent backing)嘅 backend。Crash 雖然喺 `audit_log` 嘅 `prune_expired` 先觸發,但**根因影響每一個 Postgres-backed store**(`kb_management` / `api/auth` users+sessions / `storage` RBAC + audit + admin provider/identity)—— 全部用 `psycopg.AsyncConnection`。
- **Workaround available?**:有(降級)— 唔設 `DATABASE_URL` → in-memory fallback,backend 正常;但噉就**冇 Postgres 持久化**(KB metadata restart 即失,正是 BUG-007 follow-up 想解決嘅嘢)。
- **Data loss / corruption?**:No
- **Security implication?**:No
- **Why latent until now**:ADR-0023 Postgres path W17 F1 implement,但 **W17 F1.5b「Postgres-path runtime smoke」因 `pip install psycopg` R8-blocked 而 deferred**(CO17)。psycopg 從未喺 Windows 真正安裝 + 運行過 → 呢個 Proactor 不相容一直無人撞到。2026-05-22 mobile-hotspot 裝好 psycopg + 設 `DATABASE_URL`,第一次真正行 Postgres path 即觸發。

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:預設 config(`DATABASE_URL` 未設)backend 完全正常 —— 項目過去數週都係噉行。Bug 只喺**啟用 Postgres 持久化 + Windows** 嘅組合下出現,且有降級 workaround(in-memory)。非 Sev1/Sev2(預設路徑無 broken、無 data loss、無 security)。但對「Windows dev 上用 Postgres 持久化」嘅 use case 係硬 blocker。Sev3 → **無需 postmortem**。

## 6. Initial Diagnosis（root cause confirmed）

**Confirmed via crash traceback(2026-05-22)**:

- Windows(Python 3.8+)嘅 asyncio 預設 event loop = `ProactorEventLoop`。
- `psycopg` v3 嘅 async 模式(`AsyncConnection`)**唔支援 `ProactorEventLoop`** — connect 時主動 raise `psycopg.InterfaceError`,訊息明示要 `SelectorEventLoop`。
- uvicorn 啟動時根據當前 `asyncio` event loop policy 建 loop。`server.py` / app 從未為 Windows 設 `WindowsSelectorEventLoopPolicy` → uvicorn 攞到 Proactor loop → lifespan 內第一個 psycopg async connect(`audit_log_backend.prune_expired`)即 crash。
- **唔係 psycopg / uvicorn / app 邏輯 bug** —— 係 Windows-specific event-loop-policy 缺失。標準修法(psycopg 官方文件亦如此建議):喺 loop 建立之前 set `WindowsSelectorEventLoopPolicy`。

**Root cause**:`uvicorn` 喺 Windows 用 `ProactorEventLoop` 跑 ASGI app — 同 ADR-0023 嘅 psycopg async store 不相容。**關鍵細節(實作階段確認)**:uvicorn `Server.run()` 用 `asyncio_run(serve(), loop_factory=config.get_loop_factory())`,而 `uvicorn/loops/asyncio.py::asyncio_loop_factory` 喺 `win32 and not use_subprocess` 時 **hard-code 返 `asyncio.ProactorEventLoop`** —— uvicorn **完全唔睇 event loop policy**。所以「import 時 set `WindowsSelectorEventLoopPolicy`」嘅修法無效(初版嘗試已驗證失敗 — uvicorn 嘅 `loop_factory` 直接覆寫)。

**Fix**:喺 `server.py` 加 `if __name__ == "__main__":` launcher,**繞過** `Server.run()` —— 自己 `uvicorn.Server(uvicorn.Config(app, ...))` 再 `asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)`(Windows path;`win32` guard 之外行 `server.run()` 原狀)。Backend 改用 **`python -m api.server`** 啟動(非 `python -m uvicorn api.server:app`)。`SelectorEventLoop` 對本 web app 無功能損失(Azure SDK 行 httpx async / Docling 行 threadpool — 都唔需要 Proactor 獨有嘅 in-loop subprocess);`asyncio.run(..., loop_factory=)` 係 Python 3.12 native(CLAUDE.md §3.1 Python 3.12+ baseline)。

## 7. Acceptance for Fix（checklist preview）

- [ ] Root cause confirmed — Windows `ProactorEventLoop` 同 psycopg async 不相容 **+ uvicorn `Server.run()` 用 `loop_factory` hard-code Proactor(無視 event loop policy)**,via crash traceback + uvicorn 原始碼(`loops/asyncio.py`)
- [ ] `backend/api/server.py` — 加 `if __name__ == "__main__":` launcher:`win32` 時 `asyncio.run(uvicorn.Server(uvicorn.Config(app, ...)).serve(), loop_factory=asyncio.SelectorEventLoop)` 繞過 `Server.run()` 嘅 Proactor `loop_factory`;非 win32 行原狀 `server.run()`
- [ ] Backend 啟動指令改 `python -m api.server`(非 `python -m uvicorn api.server:app`);`docs/setup.md` 同步更新
- [ ] **無 unit test** — fix 屬 launch-mechanism change(`__main__` block 啟動 uvicorn server),unit test 無法有意義驗證(會 contrived);acceptance = 下方 runtime verify(per Karpathy §1.2 唔寫 contrived test)
- [ ] **Runtime verify(= 主 acceptance)** — `DATABASE_URL` 已設、`python -m api.server` 啟動 → lifespan 正常完成、無 `InterfaceError` → `/health` `postgres.status` = `ok` → Postgres-backed store tables 自動建立(`CREATE TABLE IF NOT EXISTS` on connect)
- [ ] **Test isolation(scope-folded per Chris 2026-05-22 — R3 changelog)** — `.env` `DATABASE_URL`(BUG-007 follow-up Postgres wiring)令 pytest 全 suite 切 Postgres-backed → 8 個 in-memory-assuming test fail(`server.py` `__main__` block 唔關事 — import 時不執行;確認 via crash 失敗 test 名 + `test_health_postgres_not_configured` 自身 `monkeypatch.delenv` 被 `Settings` lru_cache 擊敗)。NEW `backend/tests/conftest.py`:import 時 `os.environ["DATABASE_URL"]=""`(空 env var 喺 Pydantic precedence 覆寫 `.env` file,先於任何 test module import `api.server` 建 cached Settings)→ suite deterministic 行 in-memory;Postgres-path test 用 explicit `Settings(database_url=...)` 不受影響
- [ ] verify gates — backend `pytest tests/` **0 failed**(conftest isolation 後回復;`__main__` block import 時不執行 → test-neutral)+ `mypy` `server.py` clean + `ruff` `server.py` 零新 error
- [ ] **Out of scope（不修）**:psycopg / uvicorn 本身(third-party,行為正確);Linux 路徑(`win32` guard 之外零改動);`server.py` 既有 **29 個 E402** ruff error(`truststore` pre-import pattern 引致,pre-existing tech-debt — committed 版本同樣 29,本 fix 零新增;per Karpathy §1.3 唔順手修);`--reload` 模式喺 OneDrive 上 worker 輸出捕捉問題(W22+ 已知 infra issue,與此無關)

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-22 | Initial triage(Sev3)+ root cause confirmed via crash traceback（Windows ProactorEventLoop ⇄ psycopg async 不相容;`server.py` 缺 Windows event-loop-policy）| AI 喺 BUG-007 follow-up 接 Postgres 持久化時撞到 backend startup crash;Chris confirmed Bug-fix BUG-008 + Sev3 | Chris(chat-confirm 2026-05-22)|
| 2026-05-22 | **Fix mechanism refined** — 初版「import 時 set `WindowsSelectorEventLoopPolicy`」實測失敗:uvicorn `Server.run()` 用 `loop_factory` hard-code `ProactorEventLoop`、無視 policy。改為 `server.py` `__main__` launcher + `asyncio.run(serve(), loop_factory=SelectorEventLoop)` 繞過。**Scope folded(R3)**:runtime verify 揭 `.env` `DATABASE_URL` 令 pytest 8 test fail(test-isolation gap),Chris 同意併入 BUG-008 → NEW `tests/conftest.py`。 | uvicorn 原始碼確認 loop_factory 機制;Chris pick「方案 A」folding test-isolation fix into BUG-008 | Chris(chat-confirm 2026-05-22)|

---

**Lifecycle reminder**:Sev3 → `postmortem.md` 不需要(only Sev1/Sev2 mandatory per `PROCESS.md §4.5`)。

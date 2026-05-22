---
bug_id: BUG-008
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed              # in-progress | closed
---

# BUG-008 — Progress

## 2026-05-22 — triage + diagnosis

### Done
- Folder + 3 docs created `docs/03-implementation/bugs/BUG-008-psycopg-windows-event-loop/{report,checklist,progress}.md`(per PROCESS.md §4 — Sev3 → 無 postmortem)
- Triaged **Sev3** — Chris confirmed Sev3 + 3-doc workflow(chat 2026-05-22)。
- **T1 root cause confirmed** — crash traceback:Windows 預設 `ProactorEventLoop` 同 `psycopg` async `AsyncConnection` 不相容;`server.py` 無為 Windows set event-loop-policy → uvicorn 用 Proactor → lifespan `audit_log_backend.prune_expired(90)` 第一個 psycopg connect raise `psycopg.InterfaceError` → startup failed exit 3。
- 確認 latent 原因:W17 F1.5b「Postgres-path runtime smoke」因 `psycopg` R8-blocked deferred(CO17)→ Postgres path 從未喺 Windows 真正 run → bug 一直無人撞;2026-05-22 mobile-hotspot 裝 psycopg + 設 `DATABASE_URL` 後第一次觸發。

### Decisions
- **D1 — fix = `win32`-guarded `WindowsSelectorEventLoopPolicy`**:psycopg 官方建議嘅標準 Windows 修法。喺 `server.py` module import 時 set(uvicorn 由當前 policy 建 loop,所以必須喺 import 階段 set,先於 uvicorn 建 loop)。`sys.platform == "win32"` guard → Linux production / CI 行為零改動。
- **D2 — 放喺 `truststore` block 之後**:`server.py` 開頭已有「import → execute → import」嘅 pre-import setup pattern(`truststore.inject_into_ssl()`,line 7-11)。event-loop-policy block 跟同樣形態擺喺其後,語意一致(都係 process-wide 啟動前設定)。
- **D3 — 唔改 `audit_log_postgres.py` 或其他 store**:crash 喺 audit_log 先觸發,但根因係 process-level event loop policy,**所有** Postgres-backed store 共用。Fix 喺 entry-point set policy 一次過解決全部 — 改個別 store 係治標(per Karpathy §1.2 + §1.3 — 一個 root-cause fix 勝過散落多處)。

### Next
- T2-T6 implementation。

## 2026-05-22 — implementation + verify + closeout

### Done
- **T2 `server.py` launcher** — 加 `if __name__ == "__main__":` block:`win32` 時 `asyncio.run(uvicorn.Server(uvicorn.Config(app, host, port)).serve(), loop_factory=asyncio.SelectorEventLoop)`,繞過 `Server.run()`;非 win32 行原狀 `server.run()`。
- **T3 啟動指令 + setup.md** — backend 改 `python -m api.server`;`docs/setup.md` §「6. Backend dev server」+ §4.3「Run dev server」兩處 `uv run uvicorn ...` → `uv run python -m api.server` + BUG-008 註解。無 unit test(launch-mechanism change)。
- **T4 runtime verify** — `.env` `DATABASE_URL` 已設、`python -m api.server` 啟動 → lifespan 完成、無 `InterfaceError` → `/health` `postgres.status` = **`ok`** → `ekp` DB tables 自動建立(audit_log / groups / group_members / roles / role_permissions / kb_acl 已建,其餘 store 首次用 lazy-create)。
- **T5 test isolation** — NEW `backend/tests/conftest.py`:import 時 `os.environ["DATABASE_URL"]=""`(空 env var 覆寫 `.env`,先於 test module 建 cached Settings)。**+** 3 處 test 自身 `monkeypatch.delenv("DATABASE_URL")` → `monkeypatch.setenv("DATABASE_URL", "")`(`test_health_route.py` ×2 line 170+211 / `test_admin_connections.py` ×1 line 251)—— `delenv` 會令 Settings fallback 去讀 `.env` file,`setenv("","")` 先正確 override。
- **T6 verify gates** — backend `pytest tests/`(見 Verdict)+ `mypy` `server.py` 0 error + `ruff` `server.py` committed 29 = current 29(零新 error)。

### Decisions
- **D1(superseded)** — 初版打算 `server.py` import 時 set `WindowsSelectorEventLoopPolicy`。**實測失敗** → D4。
- **D4 — 改用 `loop_factory` 繞過,非 set policy**:uvicorn `Server.run()` 用 `asyncio_run(serve(), loop_factory=...)`,`loops/asyncio.py::asyncio_loop_factory` 喺 `win32 and not use_subprocess` hard-code `ProactorEventLoop` —— uvicorn **完全無視 event loop policy**。所以 set policy 永遠無效。正解 = `__main__` block 自己 `asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)`,繞過 `Server.run()`。`asyncio.run(loop_factory=)` 係 Python 3.12 native。
- **D5 — `python -m api.server` 取代 `python -m uvicorn api.server:app`**:`python -m uvicorn` 將 uvicorn 設為 `__main__`、由佢建 loop;`python -m api.server` 令 `server.py` 嘅 `__main__` block 控制 loop 建立。`docs/setup.md` 同步更新。無 `--reload`(本來 `--reload` 喺 OneDrive 已知 hang;manual restart 係既有 workflow)。
- **D6 — 無 unit test**:fix 屬 launch-mechanism change,unit test 無法有意義驗證(contrived);acceptance = T4 runtime verify(per Karpathy §1.2)。初版加咗嘅 `test_windows_uses_selector_event_loop_policy`(policy 路線)隨 D4 一併撤回。
- **D7 — `server.py` 既有 29 個 E402 ruff error 不修**:`truststore` pre-import pattern 引致,committed 版本同樣 29(本 fix 零新增)。per Karpathy §1.3 surgical — pre-existing tech-debt 唔順手修。
- **D8 — test isolation scope-folded into BUG-008(per Chris「方案 A」)**:`.env` `DATABASE_URL` 令 pytest suite 切 Postgres-backed → 8 test fail。Chris 同意併入 BUG-008(BUG-008 自身 pytest 閘需要佢)。NEW `conftest.py` 修 6 個;餘 2 個(test 自身 `delenv`)再 `delenv`→`setenv("","")` 修。R3 changelog 已記。

### Acceptance（report.md §7）
- ✅ Root cause confirmed — Windows ProactorEventLoop ⇄ psycopg async 不相容 + uvicorn `loop_factory` hard-code Proactor(無視 policy）
- ✅ `server.py` `__main__` launcher — `loop_factory=asyncio.SelectorEventLoop` 繞過 `Server.run()`
- ✅ 啟動指令 `python -m api.server` + `docs/setup.md` 同步
- ✅ 無 unit test(launch-mechanism change,per Karpathy §1.2)
- ✅ Runtime verify — `python -m api.server` + `DATABASE_URL` → `/health` `postgres: ok`、tables 自動建立
- ✅ Test isolation — `conftest.py` + 3 處 `delenv`→`setenv`
- ✅ verify gates — backend `pytest tests/` **921 passed / 25 skipped / 0 failed**(conftest + delenv→setenv 之後;8→2→0)+ `mypy` `server.py` 0 error + `ruff` `server.py` committed 29 = current 29(零新 error)
- 🚧 Out of scope:psycopg/uvicorn 本身;Linux 路徑;`server.py` 29 E402(pre-existing);`--reload` OneDrive infra issue

**Verdict**:BUG-008 **CLOSED 2026-05-22**(Sev3;single-sitting triage + diagnosis + fix + test-isolation + verify + closeout)。Windows 上 psycopg async 同 uvicorn 嘅 ProactorEventLoop `loop_factory` 不相容 → `server.py` 加 `__main__` launcher,`asyncio.run(server.serve(), loop_factory=asyncio.SelectorEventLoop)` 繞過 `Server.run()`;backend 改 `python -m api.server` 啟動。Runtime verified — `/health` `postgres: ok`、`ekp` DB tables 自動建立。Test-isolation(scope-folded per Chris 方案 A)— NEW `tests/conftest.py` force `DATABASE_URL=""` + 3 處 `delenv`→`setenv`,pytest 由 8 fail 回復 **921 passed / 0 failed**。BUG-007 follow-up 接 Postgres 持久化 **end-to-end 完成** —— 用戶之後 restart backend KB metadata 唔會再失。Sev3 → 無 postmortem。

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `fix(api): launch uvicorn with a Windows-safe SelectorEventLoop for psycopg — BUG-008` |

---

**End of BUG-008 progress**

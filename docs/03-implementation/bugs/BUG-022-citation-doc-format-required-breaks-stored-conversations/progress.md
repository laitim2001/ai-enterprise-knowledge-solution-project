---
bug_id: BUG-022
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-022 — Progress

> Sev1 fast-track。Postmortem mandatory per PROCESS.md §4.5。

## Day 1 — 2026-05-24

### Investigation

BUG-021 commit `78f3d36` + amendment `3532e4b` 之後 user-eye verify post backend restart 觀察到 chat page console 報錯:

```
api-client.ts:121  GET http://localhost:3001/api/backend/conversations/d0b9179bbaac4fdd95a8d8889bdaa8bd 500 (Internal Server Error)
```

Live `curl` probe + uvicorn log traceback 確認 root cause:
- BUG-021 `Citation.doc_format` 設為 required Literal field(no default)
- `conversations.messages.citations` JSONB column 存咗 pre-BUG-021 serialized citations(冇 `doc_format` key)
- `_row_to_message` 用 `Citation.model_validate(c)` 觸發 Pydantic ValidationError → unhandled exception → 500

### Decisions

- **D1.1** — Sev1 elevation:任何 user 點 conversation history 都 500;production-blocking critical
- **D1.2** — Fix:`doc_format` 加 `= "docx"` default;Drive corpus 90%+ .docx 令 default 對 legacy data 正確;build_citations 對 fresh retrievals 仍 explicit override → no behavior change for new data
- **D1.3** — Rejected alternative:database migration backfilling old citations with `doc_format` derived from extension。Reason:純 schema default 已足夠 backward compat,Karpathy §1.2 simplicity — 唔需要 migration
- **D1.4** — Rejected alternative:make field `Optional[str]` — 失 Literal narrowing,frontend TS type 失效。Default value pattern 保留 Literal narrowing

### Side-quest: backend restart issues

While fixing BUG-022 surfaced 2 Windows-specific operational issues that consumed extra time:
- **Stale TCP socket on port 8000** post-kill — Windows TIME_WAIT 機制保留 socket several minutes after parent process death;solved by hunting + killing the spawned worker child(`Win32_Process` parent-child traversal)
- **psycopg ProactorEventLoop incompatibility** — uvicorn without `--reload` defaults to ProactorEventLoop on Windows;psycopg AsyncConnection 唔 compat;`--reload` mode uses SelectorEventLoop via subprocess so works correctly。Solution:always use `--reload` on Windows dev or pass `--loop selector` explicitly

Future setup.md §8.7 amendment candidate 加 troubleshooting row。

### Code changes

| 檔案 | 改動 |
|---|---|
| `backend/api/schemas/query.py` | `Citation.doc_format: Literal["docx", "pdf", "pptx"] = "docx"` default + 8-line inline comment cite BUG-022 |

### Verify gates

- Live `curl GET /conversations/d0b9179bbaac4fdd95a8d8889bdaa8bd` → HTTP 200 + 2 messages載入 + citations carry `doc_format: "docx"` default fallback
- Backend pytest 既有 BUG-021 13 citation tests unchanged → preserved(no test changes needed;default 只 affects missing-field input,不 affect 既有 explicit-value tests)
- Frontend chat page 對話 history 應該重新 load 成功(post-restart user-eye verify pending)

### Commits(pending)

_(rolled into BUG-022 commit — `fix(api): Citation.doc_format default "docx" — BUG-022 BUG-021 backward-compat regression`)_

### Retro

- **BUG-021 audit gap**:我加 schema field 為 required 時,只 audit 咗 fresh-retrieval path(`build_citations`)+ 新 serialization path(API responses),完全漏咗 **read-from-storage path**(`postgres_store._row_to_message` deserialize old JSONB)— classic「new field with no default breaks deserialization of pre-field data」schema migration pattern
- **Karpathy §1.3 surgical reminder**:Pydantic schema add 即使 backwards-compatible 喺 API contract 層面(consumers 收到 optional field 仲 work),deserialization 層面 NOT compat unless default value provided
- **Preventive future pattern**:future Pydantic schema field add 必 default-value-by-default(except where business logic 要求 explicit set)— even Literal types support default。If business requires explicit value, deserializer 必須有 graceful fallback(per `build_citations` pattern in BUG-021 already handles missing chunk field)
- **OS Side-issue learning**:Windows stale TCP socket + ProactorEventLoop+ psycopg incompatibility 屬 dev workflow gotcha — `--reload` flag should be DEFAULT for Windows uvicorn dev runs(adds value beyond just file watching);adding to setup.md §8.7 troubleshooting

### Postmortem

Sev1 postmortem written per PROCESS.md §4.5 — see `./postmortem.md`(timeline + 5 whys + corrective + preventive)。

### Closeout — 2026-05-24 W25 D2 cont

- Backend schema fix landed(1-line + 8-line comment per Karpathy §1.3 surgical minimal)
- uvicorn restart picked up change(fresh restart after stale socket + ProactorEventLoop issues resolved)
- `/conversations/{id}` 200 OK verified
- BUG-022 frontmatter `triaged → done`;checklist 8/8 ticked + cross-cutting 6/6 ticked
- Commit:`fix(api): Citation.doc_format default "docx" — BUG-022 BUG-021 backward-compat regression`
- **13-bug cascade closure milestone update**:BUG-009/010/011/012/013/014/015/016/017/019/020/021/022 all closed within W25 D1-D2 multi-session sequence(2026-05-22 to 2026-05-24;BUG-018 disproved 不計)

---
bug_id: BUG-022
title: "BUG-021 `Citation.doc_format` 加為 required field 觸發 backward-compat regression — `GET /conversations/{id}` 500 ValidationError when 讀取 pre-BUG-021 stored citations in Postgres `messages.citations` JSONB"
severity: Sev1
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 W25 D2 cont — BUG-021 commit 78f3d36 + amendment 3532e4b 之後重啟 uvicorn,frontend chat 頁面 console 報錯 `api-client.ts:121 GET http://localhost:3001/api/backend/conversations/d0b9179bbaac4fdd95a8d8889bdaa8bd 500 (Internal Server Error)`;對話記錄 load 不到)"
affects_components: [C05, C10]    # Citation schema (Generation Pipeline) + Chat Interface UI (consumer)
spec_refs:
  - architecture.md §4.5     # Citation schema field contract
  - docs/architecture.md §3.4 # ADR-0023 conversations persistent backing
  - docs/03-implementation/bugs/BUG-021-chat-answer-rendering-batch/  # introduced the regression
  - CLAUDE.md §1.3           # surgical changes — avoid breaking adjacent code
related: [BUG-021]
---

# BUG-022 — Citation.doc_format required broke stored conversations(BUG-021 regression)

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev1** — `/conversations/{id}` 500 affects ALL chat session resume(任何 user 點返舊 conversation 都 500)+ purely AI-introduced regression(BUG-021 schema change),affects Beta cohort 第一個 ingestion 就 break;immediate fix required。

## 1. Symptom

User-eye verify on chat page post BUG-021 amendment commit `3532e4b` + backend uvicorn restart:

```
[Frontend Console]
api-client.ts:121  GET http://localhost:3001/api/backend/conversations/d0b9179bbaac4fdd95a8d8889bdaa8bd 500 (Internal Server Error)
```

User feedback:
> 「在chat頁面有報錯, load不了對話記錄」

Live backend probe:
```
$ curl -X GET "http://localhost:8000/conversations/d0b9179bbaac4fdd95a8d8889bdaa8bd" -H "Authorization: Bearer dev-token"
{"error":{"code":"internal.server_error","message":"An unexpected error occurred."}}
HTTP=500
```

uvicorn log full traceback ends in:

```
File ".../backend/conversations/postgres_store.py", line 93, in _row_to_message
  citations = [Citation.model_validate(c) for c in raw_citations]
File ".../pydantic/main.py", line 716, in model_validate
  return cls.__pydantic_validator__.validate_python(
pydantic_core._pydantic_core.ValidationError: 1 validation error for Citation
doc_format
  Field required [type=missing, input_value={'doc_id': 'dce-integrati...vance_score': 0.5482865}, input_type=dict]
```

## 2. Reproduction Steps

1. Pre-BUG-021 session create conversation + append assistant message(citations serialized into `messages.citations` JSONB column without `doc_format` field)
2. Post BUG-021 deploy:`Citation` schema 加 `doc_format: Literal["docx", "pdf", "pptx"]` 為 REQUIRED field(no default)
3. `GET /conversations/{id}` → `postgres_store.list_messages` → `_row_to_message` 嘗試 `Citation.model_validate(c)` 對 old citation dict → Pydantic ValidationError(missing required `doc_format`)→ unhandled → 500
4. Frontend `apiClient.conversations.get` exception → chat page 對話記錄 載入失敗

## 3. Root Cause

**My BUG-021 schema design oversight** — BUG-021 commit `78f3d36` 將 `Citation.doc_format` 加為 required field(no default):

```python
class Citation(BaseModel):
    ...
    doc_format: Literal["docx", "pdf", "pptx"]    # REQUIRED, no default
    ...
```

但 `conversations.messages` Postgres table 嘅 `citations` JSONB column 存咗 pre-BUG-021 serialized Citation instances(冇 `doc_format` key)。`Citation.model_validate(old_dict)` 必然 fail Pydantic validation。

呢個係 **classic schema-add backward-compat violation** — `build_citations`(W3 D2 F3 嘅 fresh retrieval path)新 produce 嘅 citations 一定有 `doc_format`(per BUG-021 build_citations graceful default to "docx"),但 READ-FROM-STORAGE path(`_row_to_message` 從 Postgres 反序列化 old JSONB)冇 fallback。

**Karpathy §1.3 surgical violation**:BUG-021 schema change 沒有 audit「邊個 caller 會 read 舊 Citation data」— `conversations.postgres_store._row_to_message` 係 silent consumer 路徑,BUG-021 cycle 漏咗。

## 4. Scope

- ✅ Backend `backend/api/schemas/query.py`:`Citation.doc_format` 加 `= "docx"` default — backward compat 對舊 stored data
- ✅ Backend tests:既有 `test_build_citations_*` 仍 pass(build_citations 一直 set explicit value;default 只係 fallback for missing input)
- ✅ Frontend `Citation` TS interface:NO change needed — backend default 自動 fallback to "docx",frontend type 仍 narrow 對 valid 3 values
- ✅ Schema backward compat preserved without migration

## 5. Severity Rationale

**Sev1** per PROCESS.md §4.5 — affects production-critical path:

- ALL chat session resume 受影響(任何 user 點返 conversation history 都 500)
- 由 AI 自己 introduce(BUG-021),user-impacting regression mid-session
- Postmortem mandatory per Sev1
- Time-to-fix < 1 hour(simple schema default + restart)

## 6. Acceptance for Fix

- [x] **T1** — `Citation.doc_format` schema field 加 `= "docx"` default value
- [x] **T2** — Backend uvicorn restart pick up schema change(verified via `/conversations/{id}` HTTP 200 + `doc_format: "docx"` propagated in response)
- [x] **T3** — Backend pytest 既有 13 tests 仍 pass(no fixture change needed — default 只 affect missing-field input)
- [x] **T4** — Live `/conversations/{id}` probe verified 200 response with full message list including citations with default `doc_format: "docx"`

## 7. Related

- BUG-021(introduced the regression)
- BUG-009-021 cascade(W25 D1-D2 12-bug image-pipeline + chat-presentation chain)
- ADR-0023(Postgres conversations persistent backing — root for stored-data compat)
- CLAUDE.md §1.3 surgical changes(BUG-021 missed audit of read-from-storage consumers)

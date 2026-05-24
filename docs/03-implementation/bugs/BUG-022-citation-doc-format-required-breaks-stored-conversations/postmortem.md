---
bug_id: BUG-022
report_ref: ./report.md
checklist_ref: ./checklist.md
progress_ref: ./progress.md
status: complete
last_updated: 2026-05-24
severity: Sev1
postmortem_required: true
---

# BUG-022 — Postmortem

> Sev1 postmortem per `PROCESS.md §4.5`。Root cause analysis + 5 whys + corrective + preventive。

## TL;DR

BUG-021 commit `78f3d36`(W25 D2 ~17:35)為 `Citation` Pydantic schema 加 `doc_format: Literal["docx", "pdf", "pptx"]` 為 **required field**(no default)。Pre-BUG-021 Postgres `conversations.messages.citations` JSONB column 存咗 serialized Citation instances 冇 `doc_format` key — `_row_to_message` 反序列化時 `Citation.model_validate(c)` 觸發 Pydantic ValidationError → unhandled → 500。User-eye verify 2026-05-24 W25 D2 cont(BUG-021 amendment commit `3532e4b` 之後)console 報錯。

Fix(同 session 內 landed):`doc_format: Literal[...] = "docx"` 加 default value preserve backward compatibility for legacy stored data。Karpathy §1.3 surgical 1-line + 8-line comment;backend pytest unchanged;`/conversations/{id}` HTTP 200 verified post-fix。

## Timeline

| Time(2026-05-24)| Event |
|---|---|
| **W25 D2 ~17:35** | BUG-021 commit `78f3d36` — `Citation.doc_format` Literal field 加 required(no default)|
| **W25 D2 ~17:36** | BUG-021 backend pytest 15/15 pass — fresh-retrieval path(build_citations)graceful fallback 已 cover missing-chunk-field case |
| **W25 D2 ~17:38** | uvicorn restart pick up new schema — `/query` 返 doc_format='docx' OK |
| **W25 D2 ~18:09** | BUG-021 amendment commit `3532e4b`(AnswerBodyMarkdown refactor + ScreenshotModal rewrite)|
| **W25 D2 ~18:30** | User-eye verify on chat page surfaced console error `GET /conversations/{id} 500` |
| **W25 D2 ~18:32** | uvicorn log tail shows `pydantic_core._pydantic_core.ValidationError: 1 validation error for Citation. doc_format: Field required` 喺 `_row_to_message` 路徑 |
| **W25 D2 ~18:33** | Root cause confirmed:BUG-021 schema add 漏咗 read-from-storage path audit;Postgres JSONB column stored pre-BUG-021 data 冇 `doc_format` |
| **W25 D2 ~18:34** | Fix:schema field 加 `= "docx"` default;Karpathy §1.3 surgical(1-line + 8-line comment)|
| **W25 D2 ~18:35-18:50** | uvicorn restart side-quest:Windows stale TCP socket on port 8000 + ProactorEventLoop psycopg incompatibility 耗時 ~15min;最終解決方案 = kill orphan worker child PID via `Win32_Process` parent-child traversal + use `--reload` flag(SelectorEventLoop subprocess path) |
| **W25 D2 ~18:50** | uvicorn ready;`curl GET /conversations/d0b9179bbaac4fdd95a8d8889bdaa8bd` → HTTP 200 + 2 messages + citations carry `doc_format: "docx"` default fallback |

**Time-to-detect**:55 min(BUG-021 commit → user-eye verify reported)
**Time-to-diagnose**:5 min(traceback already in uvicorn log)
**Time-to-fix**:1 min(schema 1-line default add)
**Time-to-verify**:15 min(stale socket + ProactorEventLoop side-quest)
**Total user-visible exposure**:1 hour(local-dev only, no Beta deploy yet)

## 5 Whys

**Why #1**:`GET /conversations/{id}` returns 500 with Pydantic ValidationError?
→ `Citation.model_validate(c)` fails because `c`(JSONB-deserialized dict)缺 required `doc_format` field。

**Why #2**:Why does `c` lack doc_format?
→ Pre-BUG-021 sessions serialized Citation instances 到 Postgres `conversations.messages.citations` JSONB without that field(field 唔存在 schema 內當時)。

**Why #3**:Why did BUG-021 schema add 唔 consider read-from-storage path?
→ BUG-021 audit 集中 fresh-retrieval path:`build_citations`(Citation construction from chunk fields)+ API response serialization(query / chat SSE)。`postgres_store._row_to_message` 反序列化 path 屬 silent consumer:同一 `Citation` schema,但 input source 係 stored JSONB 而非 fresh chunk。Pre-BUG-021 stored data 嘅 schema 同 new schema 唔同 — backward compat gap silent。

**Why #4**:Why was Pydantic default value not the default approach for schema add?
→ BUG-021 D1.4 decision「Backend `Citation` schema add `doc_format: Literal["docx", "pdf", "pptx"]`」focused on **field 加 + Literal narrowing**,缺 default value consideration。Reasoning 喺 BUG-021 retro 寫:「`build_citations` 直接設 explicit value from chunk field;default 唔需要」— 但呢個 reasoning 漏咗「`build_citations` 不是 唯一 deserializer」。

**Why #5**:Why was this miss not caught by W22 anti-pattern catalog or H7 verification?
→ `feedback_design_fidelity.md` patterns D1-D14 都關 frontend / mockup fidelity。Backend schema migration backward-compat 屬不同類別:**「schema field add 必 default-value-by-default unless deserialization path 已有 graceful fallback」**。Catalog 未 cover schema migration patterns。NEW D15 candidate:「Pydantic schema add new required field without considering storage deserialization paths」。

## Root Causes(Layered)

1. **Mechanical**:`Citation.doc_format` 加 required field 無 default value → Pydantic reject missing-field input
2. **Audit gap**:BUG-021 schema change 只 audit fresh-retrieval + API serialization paths;**read-from-storage deserialization path**(postgres_store._row_to_message)silent;Postgres JSONB legacy data 無 forward-migrate
3. **Schema migration discipline gap**:Pydantic schema add 新 field 應 default-value-by-default(令 deserialization graceful);BUG-021 explicit pick required field over default
4. **Catalog gap**:`feedback_design_fidelity.md` D1-D14 cover frontend fidelity / W22 anti-patterns,缺 backend schema migration patterns category
5. **Test coverage gap**:Backend `test_citation_enrichment.py` tests fresh construction path only;**deserialization-from-old-JSONB path 缺 test**;若有 NEW test「Citation.model_validate(legacy_dict_without_doc_format)」會 immediately catch BUG-022 喺 BUG-021 cycle 內

## Corrective Actions(this BUG-022 cycle)

1. ✅ **Schema default add** — `Citation.doc_format: Literal["docx", "pdf", "pptx"] = "docx"`;Karpathy §1.3 surgical 1-line change + 8-line comment cite BUG-022 reasoning
2. ✅ **Backend uvicorn restart with new schema** — Windows-specific side-quest resolved(stale TCP socket + ProactorEventLoop psycopg compat);`/conversations/{id}` HTTP 200 verified
3. ✅ **BUG-022 docs landed** — report + checklist + progress + postmortem(Sev1 mandatory)
4. ✅ **No database migration needed** — schema default 自動 fallback;Drive corpus 90%+ .docx 令 default value 對 legacy data 大概率正確

## Preventive Actions(durable improvements)

1. **Anti-pattern catalog D15 expansion**(future W26+ candidate) — `feedback_design_fidelity.md` add NEW category for backend schema migration:
   - **D15**(候選命名)「Pydantic schema add new required field without considering storage deserialization paths」— BUG-022 evidence;preventive rule = schema field add 必 default-value-by-default unless deserialization path 已有 graceful fallback
2. **Pydantic schema discipline checklist**(future CLAUDE.md §1 Karpathy candidate) — schema add new field workflow:
   - Step 1:Audit all serialization paths(API response、storage write、log)
   - Step 2:Audit all deserialization paths(API request、storage read、cache restore)
   - Step 3:If 任何 deserialization path 可能 see 舊 data without the field → add default value
   - Step 4:Add NEW deserialization test for「legacy dict without new field」scenario(catches future regression)
3. **Test coverage discipline**(future CLAUDE.md §5.6 H6 amendment candidate) — H6 mandatory backend pipeline coverage list 加「schema deserialization backward compat」item;NEW pattern test for each schema field add:`assert ModelClass.model_validate(legacy_dict_missing_field) == ModelClass(...defaults...)`
4. **setup.md §8.7 amendment**(future) — Windows uvicorn dev troubleshooting:
   - Stale TCP socket on port 8000 post-kill — use `Win32_Process` parent-child traversal to find spawned worker children
   - ProactorEventLoop psycopg incompatibility — always use `--reload` flag on Windows dev OR pass `--loop selector` explicitly
5. **W23 R6 recursive scope extension to backend**(future CLAUDE.md §10 R6 candidate) — current R6 covers pre-active-flip plan-text + code-at-active-flip mockup verify。Extend to schema field add:「mockup-side-of-the-mountain audit + schema-deserialization-side-of-the-mountain audit」symmetric requirement

## Lessons Learned

- **Schema add 必 default-value-by-default**:BUG-022 是 textbook Pydantic schema migration regression。Default value 即使 business logic 有 explicit override,仍係 backward-compat safety net for read-from-storage paths
- **「Cascade detection extends past 12 bugs」continues to validate**:BUG-009-021 12-bug cascade + BUG-022 = 13 bugs。Each bug fix unlocks 下一個 visible surface gap detection。BUG-022 specifically surfaced via console error post-deploy — different detection mechanism vs user-eye visual verify(BUG-019/020/021)— **console error detection is a sub-mode of cascade pattern,equally reliable**
- **Windows dev environment side-quest cost**:stale TCP socket + ProactorEventLoop incompatibility 兩個 unrelated issues 喺 BUG-022 fix 時 surface,加埋耗時 15min。Future Windows dev workflow 應該 default `--reload` flag + know stale-socket child-process-killing pattern
- **Sev1 vs Sev2 distinction crystallized**:BUG-019/020/021 都 Sev2(H7 fidelity affecting user-facing surface but workaround exists)。BUG-022 Sev1 elevation because **NO workaround**(any user 點 conversation history 都 500)+ pure regression introduced same session。Severity 差別 reflects user-impact scope + workaround availability
- **Karpathy §1.3 surgical fix shape ideal**:1-line schema change + 8-line comment;BUG-022 fix 不 require 任何 new tests / migration scripts / database changes。Maximum effect minimum code

---

**End of postmortem**

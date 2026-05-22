---
bug_id: BUG-005
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-05-22  # + amendment: quota-429 vs throttle-429
---

# BUG-005 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## Fix

- [x] **T1** — Root cause confirmed via code read:`create_index_for_kb`(`populate.py:207`)/ `delete_index`(`:241`)/ `delete_doc`(`:270`)三個 CH-001 method 無 `@retry`,vs `upload()`(`:146`)有;module docstring(`:7`)claims「tenacity retry on 429/5xx」;`kb.py:109-111` hint 對 429 誤導
- [x] **T2** — `populate.py` NEW `_is_retryable_azure_error(exc)` predicate — `httpx.TransportError` → True;`httpx.HTTPStatusError` → True iff status 429 或 ≥500;其他(含 4xx)→ False
- [x] **T3** — `populate.py` NEW `_azure_lifecycle_retry` shared decorator(`retry_if_exception(_is_retryable_azure_error)` + `stop_after_attempt(3)` + `wait_exponential(1,1,10)` + `reraise=True`)— mirror `upload()` 參數;import 加 `retry_if_exception`
- [x] **T4** — apply `@_azure_lifecycle_retry` 落 `create_index_for_kb` + `delete_index` + `delete_doc`(method body 不變 — `raise_for_status()` 照舊,predicate gate retry)
- [x] **T5** — `populate.py` module docstring line 7「tenacity retry on 429/5xx」更新 — 明確覆蓋 upload + 3 個 CH-001 lifecycle method via 共用 `_azure_lifecycle_retry`
- [x] **T6** — `kb.py` NEW `_index_create_hint(exc)` helper — 429 → throttle+retry+Free-tier 提示 / ≥500 → outage / 400 → kb_id 命名規則 / 其他 → generic;`import httpx` 加咗
- [x] **T7** — `kb.py` `create_kb` 502 detail 用 `_index_create_hint(exc)` 取代固定 kb_id-rules hint
- [x] **T8** — NEW 4 test in `tests/test_populate.py`:`create_index_for_kb` 429-then-201 → retry 成功(put await_count=2);429×3 → 3 attempt 後 raise `HTTPStatusError`;400 → 即刻 raise(await_count=1,不 retry);`delete_index` 429-then-204 → retry 成功(consistency)
- [x] **T9** — backend pytest **912 passed + 11 skipped + 0 failed**(W24c baseline 908 + 4 NEW BUG-005 tests — 0 regression)
- [x] **T10** — `ruff` **All checks passed** on `populate.py` + `kb.py` + `test_populate.py`;`mypy --strict` `populate.py` target-file clean;`kb.py:246` `dict` type-arg + `schemas.py:73` + `psycopg` import-not-found = **pre-existing**(git diff -U0 hunk headers 確認 BUG-005 改動喺 line 20/50/137,唔掂 246)— per Karpathy §1.3 surgical,out of scope 不修

## Cross-Cutting

- [x] Commit references `progress.md` entry;component tag `(indexing)` 對應 C03(populate.py 主改)+ C02(kb.py hint)
- [x] No ADR — H1(無架構/vendor/storage-layout 改動,retry 屬內部 robustness)+ H2(無新 dependency — `tenacity` 已在 `pyproject.toml`)均不觸發
- [x] `report.md` status `triaged → done`;此 `checklist.md` status `in-progress → done`;`progress.md` written
- [x] No CLAUDE.md / session-start.md update needed(Sev3 bug-fix,無 standing-instruction 影響)

## Amendment — quota-429 vs throttle-429（2026-05-22）

> Derived from `report.md §7 Amendment block`。事發 backend log(`bmsjq80kn`)揭示個 429 係 Azure index-quota 硬上限(「Index quota has been exceeded ... Maximum 3」),非 transient throttle → 初版 retry-all-429 對 quota 個案白燒 backoff(~13s)+ hint 誤導。

- [x] **A1** `populate.py` NEW `_is_quota_exceeded(response)` — `"quota"` in response body lowercased
- [x] **A2** `_is_retryable_azure_error` — 429 只在 NOT `_is_quota_exceeded` 時 retryable;5xx + transport error 不變;quota-429 + 其他 4xx → 不 retry
- [x] **A3** `kb.py` `_index_create_hint` — 429 分拆:quota →「刪走無用 index / 升 Standard S1」/ throttle →「等 ~1 分鐘再試」;helper docstring 更新
- [x] **A4** Tests — `test_populate.py` `test_create_index_for_kb_does_not_retry_on_quota_429`(quota-429 → `put.await_count==1`)+ `test_documents_route.py` `test_index_create_hint_distinguishes_quota_throttle_400`(4-case hint unit test,+`import httpx`)
- [x] **A5** Verify — `test_populate.py` + `test_documents_route.py` **50 passed**;backend pytest full suite no regression;ruff All checks passed on touched files;mypy `populate.py` target-clean(`kb.py:253` = 同一 pre-existing `dict` type-arg — BUG-005 前喺 `:246`,amendment 加 7 行後移位,非 amendment 引入)

## 🚧 Out of scope（environmental — 不修,per report.md §4 + §7）

- 🚧 Azure AI Search Free tier 3-index 硬上限 + 持續限流 — 結構性限制,retry 救唔到;需升 Standard S1(architecture.md §3.2 vendor lock 既定 / 隨 Track A IT cred + 正式部署)

---

**Lifecycle reminder**:新加 acceptance item 必先入 `report.md §7`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。

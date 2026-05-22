---
bug_id: BUG-005
title: "CH-001 per-KB index lifecycle methods lack 429/5xx retry — a transient Azure throttle hard-fails KB create"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-22
reporter: "User (Chris) — frontend KB-create test 2026-05-22"
affects_components: [C03, C02]   # C03 Indexing Service (indexing/populate.py) + C02 KB Manager (api/routes/kb.py)
spec_refs:
  - architecture.md §3.6        # index ekp-kb-{kb_id}-v1 schema + population
  - CH-001                      # per-KB index lifecycle (create_index_for_kb / delete_index / delete_doc)
  - ADR-0018                    # multi-KB kb_id propagation — per-KB index name
---

# BUG-005 — CH-001 index lifecycle methods miss the 429/5xx retry

> **Report version**:1.0(initial)
> **Triage approver**:AI(self-triaged Sev3 — core flow defect but a wait+retry workaround exists + the storage record rolls back cleanly;Sev3 → no mandatory postmortem per PROCESS.md §4.5)。Chris confirmed Bug-fix BUG-005 + scope (b) all 3 CH-001 methods + misleading-hint fix via chat 2026-05-22。

## 1. Symptom

前端建立 KB(`drive-sop`)時 502 失敗:

```
Create failed — Azure AI Search index_create_failed for kb_id=drive-sop:
HTTPStatusError: Client error '429 Too Many Requests' for url
'https://azureaisearchtesting.search.windows.net/indexes/ekp-kb-drive-sop-v1?api-version=2024-07-01'
... Check kb_id matches Azure index-name rules: 2-128 chars, lowercase a-z + 0-9 + dashes ...
```

兩個獨立缺陷:

1. **無 retry** — Azure AI Search 回 `429 Too Many Requests`(服務端限流),`IndexPopulator.create_index_for_kb` **即刻 hard-fail**,完全冇 backoff retry。一個本來 backoff 後大機會成功嘅 transient throttle,變成 user-facing 502。
2. **誤導 hint** — `kb.py` 對**所有** `index_create_failed` 一律 append「Check kb_id matches Azure index-name rules…」。`drive-sop` 係完全合法嘅 kb_id;429 同 index 命名完全無關。User 會被引導去 debug 一個唔存在嘅命名問題。

## 2. Reproduction Steps

1. Backend 配置真 Azure AI Search credential(`azureaisearchtesting` — **Free tier**)
2. 前端 `/kb/new` wizard 建立 KB(或連續建立多個 KB 觸發 Free-tier 限流 window)
3. POST `/kb` → `create_index_for_kb` PUT `/indexes/ekp-kb-drive-sop-v1` → Azure 回 429
4. Observed:502 + 上述 error envelope;KB storage record 已被 `kb.py` rollback(`drive-sop` 無殘留)

**Reproduction reliability**:Intermittent on Free tier(視乎 Azure 限流 window — 連續 index 操作後高機會;`coverage`-style「deterministic per-blob within a bad window」)。

**Environment**:local dev backend(`:8000`)+ real Azure AI Search `azureaisearchtesting` **Free tier**(per CO17「Personal Azure dev tier」umbrella — architecture.md §3.2 vendor lock 係 Standard S1,Free tier 屬 dev-only resource)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| 429 處理 | `create_index_for_kb` 收到 429 → backoff retry(對齊 `upload()` + 對齊 module docstring `populate.py:7`「tenacity retry on 429/5xx」)→ transient throttle 多數自動清 | `create_index_for_kb`(`populate.py:207`)**無 `@retry` decorator** → `raise_for_status()` 即刻拋 `HTTPStatusError` → 502 |
| `delete_index` / `delete_doc` | 同樣應該 retry 429/5xx | 同樣**無 `@retry`** — 相同 gap(CH-001 三個新 method 一齊漏) |
| 錯誤 hint | 429/5xx → 提示「Azure throttle/outage,等陣 retry」;只有 400 先提示 check kb_id 命名 | `kb.py:109-111` 對所有 failure 一律 append「Check kb_id matches Azure index-name rules」— 對 429 完全誤導 |

## 4. Impact

- **Affected users / scenarios**:任何透過前端 / API 建立 KB 嘅 user,當 Azure AI Search 短暫限流(或 outage)時 → KB 建立 502 失敗。
- **Workaround available?**:Yes — 等約 1-2 分鐘再試(storage record 已 rollback,重試係乾淨嘅;transient throttle 通常自己清)。
- **Data loss / corruption?**:No — `kb.py` 失敗時 rollback storage record(`create_kb` step-2 failure → `service.delete`)。
- **Security implication?**:No
- **Environmental note(out of scope — 不修)**:`azureaisearchtesting` 係 **Azure AI Search Free tier**。Free tier 限流好狠 + **硬上限只有 3 個 index**。BUG-005 嘅 retry 修正令 EKP 對 *transient* 429 robust(對齊 `upload()`),但 Free tier 嘅**結構性**限制(3-index cap + 持續限流)係 environmental,retry 救唔到 —— 需要升 Standard S1(architecture.md §3.2 vendor lock 既定 / 隨 Track A IT cred + 正式部署落地)。

## 5. Severity Justification

**Sev3** per `PROCESS.md §4.5`:core flow(KB 建立)嘅 functional defect,但有 workaround(wait + retry)、無資料損失(storage rollback 乾淨)、無 security implication、底層 trigger 部分屬 external(Azure throttle)。Sev3 → 無 mandatory postmortem(只有 Sev1/Sev2 需要)。

## 6. Initial Diagnosis（root cause confirmed）

**Confirmed via code read(2026-05-22)**:

- `IndexPopulator.upload()`(`populate.py:146-150`)**有** `@retry`(`retry_if_exception_type((httpx.HTTPStatusError, httpx.TransportError))` + `stop_after_attempt(3)` + `wait_exponential(1,1,10)`)+ method body line 173-174 `if status >= 500 or status == 429: raise_for_status()` 讓 tenacity retry。
- CH-001(2026-05-12)新加嘅三個 per-KB index lifecycle method —— `create_index_for_kb`(`populate.py:207`)、`delete_index`(`:241`)、`delete_doc`(`:270`)—— **全部冇 `@retry` decorator**。三者收到任何 non-success status 就 `raise_for_status()` 即拋。
- Module docstring(`populate.py:7`)明寫「tenacity retry on 429/5xx」作為**模組層級**屬性 —— 但實際只 cover `upload()`。CH-001 加 method 時冇延伸 retry treatment → docstring 與實際不符。
- `kb.py:104-112` 對 `index_create_failed` 一律 append 固定嘅「Check kb_id matches Azure index-name rules」hint —— 該 hint 只對 400(Azure 拒絕 index 名)有意義,對 429(限流)/ 5xx(outage)誤導。

**Fix(per Chris-confirmed scope (b) + hint)**:
- `populate.py` — 加共用 retry predicate `_is_retryable_azure_error`(`httpx.TransportError` + `HTTPStatusError` 中 429 / ≥500;**其他 4xx 不 retry** — caller error retry 只係延遲一個 deterministic failure)+ 共用 `_azure_lifecycle_retry` decorator(mirror `upload()` 嘅 3-attempt / 1-10s exponential),apply 落三個 CH-001 method。method body 不變(`raise_for_status()` 照舊 — predicate gate 邊個 exception 先 retry)。docstring `populate.py:7` 更新明確覆蓋範圍。
- `kb.py` — 加 `_index_create_hint(exc)` helper,按 `httpx.HTTPStatusError` status 分支(429 → throttle+retry+Free-tier-tier 提示 / ≥500 → outage / 400 → kb_id 命名規則 / 其他 → generic),取代固定 hint。

## 7. Acceptance for Fix（checklist preview）

- [ ] Root cause confirmed — 3 CH-001 methods 無 `@retry`(vs `upload()` 有);module docstring claims it;`kb.py` hint 誤導 — **confirmed via code read**
- [ ] **populate.py** — NEW `_is_retryable_azure_error` predicate + `_azure_lifecycle_retry` shared decorator;apply 落 `create_index_for_kb` + `delete_index` + `delete_doc`;module docstring §7 line 更新
- [ ] **kb.py** — NEW `_index_create_hint(exc)` helper(429 / 5xx / 400 / other 分支)取代 `create_kb` 入面固定嘅 kb_id-rules hint;`import httpx`
- [ ] **Test** — NEW test:`create_index_for_kb` 收 429-then-201 → retry 後成功;429×3 → 3 次 attempt 後 raise;非-retryable 400 → 即刻 raise 唔 retry(verify attempt count)
- [ ] backend pytest no regression(baseline 908 passed + 11 skipped)
- [ ] `mypy --strict` clean on `populate.py` + `kb.py`(touched files;pre-existing 豁免不算)
- [ ] `ruff` clean on touched files
- [ ] **Out of scope（不修，environmental）**:Free-tier 3-index 硬上限 + 持續限流 → 需 Standard S1 per architecture.md §3.2 + Track A

### Amendment — quota-429 vs throttle-429（2026-05-22,per Chris confirm post-incident evidence）

初版 fix retry **所有** 429。事發 backend 嘅 log(`bmsjq80kn` background task)揭示 Azure 嘅實際訊息 ——「Index quota has been exceeded ... Maximum number of indexes allowed: 3」—— 即係嗰個 429 係**硬 index-quota 上限**,**唔係** transient throttle。Azure 兩種情況都用 429,但只有 throttle 嗰種 backoff retry 有用;quota 嗰種 retry 純粹白燒 backoff budget(~13s)。

- [x] **A1** `populate.py` NEW `_is_quota_exceeded(response)` — 透過 response body 含 `"quota"` 偵測 quota 上限
- [x] **A2** `_is_retryable_azure_error` — 429 **只在 NOT `_is_quota_exceeded` 時** retryable(5xx + transport error 不變;quota-429 + 其他 4xx → 不 retry)
- [x] **A3** `kb.py` `_index_create_hint` — 429 hint 分拆:quota →「刪走無用 index / 升 Standard S1」;throttle →「等 ~1 分鐘再試」
- [x] **A4** Tests — `test_populate.py` `test_create_index_for_kb_does_not_retry_on_quota_429`(quota-429 → `put.await_count==1`,不 retry)+ `test_documents_route.py` `test_index_create_hint_distinguishes_quota_throttle_400`(hint 4-case unit test)
- [x] **A5** Verify — backend pytest no regression;ruff clean on touched files;mypy `populate.py` target-clean

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-22 | Initial triage(Sev3)+ root cause confirmed via code read(3 CH-001 methods lack `@retry`;`kb.py` hint misleading)+ fix scope (b) all 3 methods + hint per Chris chat-confirm | User(Chris)reported frontend KB-create 429 failure 2026-05-22;Chris confirmed Bug-fix BUG-005 + scope (b) + hint fix + Azure tier = Free | Chris(chat-confirm 2026-05-22) |
| 2026-05-22 | Fix landed + verified → status `triaged → done`。`populate.py` 共用 `_is_retryable_azure_error` predicate + `_azure_lifecycle_retry` decorator apply 落 3 個 CH-001 method;`kb.py` `_index_create_hint(exc)` error-class-aware hint。4 NEW test;backend pytest **912 passed**(908 baseline +4,0 regression);ruff clean;mypy `populate.py` target-clean(`kb.py:246` pre-existing,outside diff)。 | BUG-005 single-sitting close | Chris |
| 2026-05-22 | **Amendment — quota-429 vs throttle-429**(§7 Amendment block A1-A5)。事發 backend log 揭示個 429 係 Azure index-quota 硬上限(「Index quota has been exceeded ... Maximum 3」),非 transient throttle → 初版 retry-all-429 對 quota 個案白燒 backoff + hint 誤導。`_is_quota_exceeded` 偵測 + `_is_retryable_azure_error` 只 retry non-quota 429 + `_index_create_hint` 429 分拆 quota/throttle。+2 NEW test。pytest no regression;ruff clean。 | Chris confirm amendment 2026-05-22(post-incident Azure-message evidence) | Chris |

---

**Lifecycle reminder**:Sev1/Sev2 → `postmortem.md` mandatory(per `PROCESS.md §4.5`)。Sev3 — none required。

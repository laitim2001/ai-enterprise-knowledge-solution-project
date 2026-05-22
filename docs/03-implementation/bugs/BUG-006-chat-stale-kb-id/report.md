---
bug_id: BUG-006
title: "Chat sends a stale legacy-alias kb_id — every query against a real KB 502s (retrieval hits a non-existent index)"
severity: Sev2          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-05-22
reporter: "User (Chris) — frontend chat test 2026-05-22"
affects_components: [C10]        # C10 Chat Interface UI (frontend/app/(app)/chat/page.tsx)
spec_refs:
  - architecture.md §5            # UI Specifications — Chat view
  - ADR-0018                      # multi-KB kb_id → index name; the Tier 1 legacy alias
---

# BUG-006 — Chat sends a stale legacy-alias kb_id

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev2**(core flow — chat against a KB — broken out-of-the-box,no usable workaround);**Chris confirmed Sev2 + Bug-fix BUG-006 workflow(report + checklist + progress + postmortem)via chat 2026-05-22**。Sev2 → mandatory `postmortem.md` per PROCESS.md §4.5。

## 1. Symptom

喺 `/chat` 揀啱個 KB 開始討論時,每一條 query 都 502:

```
API error 502: {"error":{"code":"pipeline.retrieval_failed",
"message":"retrieval failure: HTTPStatusError: Client error '404 Not Found' for url
'https://azureaisearchtesting.search.windows.net/indexes/ekp-kb-drive-v1/docs/search?api-version=2024-07-01'",
"actionable_hint":"The retrieval backend is degraded — retry shortly."}}
```

關鍵:retrieval 打嘅 index 係 **`ekp-kb-drive-v1`**(legacy 預設 index)—— 而唔係用戶實際 KB(`drive-user-manual-1`)對應嘅 `ekp-kb-drive-user-manual-1-v1`。

## 2. Reproduction Steps

1. 建立一個 KB(本案 `drive-user-manual-1`)+ upload 一份文件(`DCE_Integration_Platform_Implementation_Plan.docx`,121 chunks indexed)
2. 去 `/chat`,KB 下拉選單顯示 `drive-user-manual-1`(睇落正常)
3. 打任何 query,送出
4. Observed:**502 `pipeline.retrieval_failed`**,URL = `.../indexes/ekp-kb-drive-v1/docs/search`(404)

**Reproduction reliability**:Always(deterministic)。

**Environment**:local dev frontend(`:3001`)+ backend(`:8000`,real Azure AI Search `azureaisearchtesting`)。

## 3. Expected vs Actual

| 範疇 | Expected | Actual |
|---|---|---|
| Chat 送出嘅 `kb_id` | 用戶選中嘅真實 KB(`drive-user-manual-1`)| `'drive_user_manuals'` —— stale `DEFAULT_KB_ID`(W3 single-KB POC legacy alias)|
| Retrieval index | `ekp-kb-drive-user-manual-1-v1`(存在,121 chunks)| `ekp-kb-drive-v1`(`kb_id_to_index_name` 將 legacy alias `drive_user_manuals` 映射到此 — 該 index 喺 `azureaisearchtesting` 從未建立)→ 404 |
| KB 下拉選單 | 顯示 = 送出 | 顯示 `drive-user-manual-1`(`activeKb` 衍生值正確),但送出 `kbId` state(stale)— **顯示同送出唔一致** |

## 4. Impact

- **Affected users / scenarios**:任何 user 喺 `/chat` 對住一個**真實建立嘅 KB**(任何 kb_id ≠ legacy alias `drive_user_manuals`)發問 → 每條 query 都 502。Chat 係 EKP 嘅核心產品功能。
- **Workaround available?**:**No(無 usable workaround)**。KB 下拉選單喺只有 1 個 KB 時得 1 個 `<option>`,HTML `<select>` `onChange` 只喺值**改變**時觸發 → 用戶無法「重新選」同一個 KB → `onKbChange`/`setKbId` 永遠唔 fire → `kbId` 死鎖喺 stale default。
- **Data loss / corruption?**:No
- **Security implication?**:No

## 5. Severity Justification

**Sev2** per `PROCESS.md §4.5`:核心 user flow(chat against a KB — EKP 嘅 primary product surface)open-the-box 即壞,**無 usable workaround**(下拉選單單一 option 令 `onChange` 永不觸發)。非 Sev1(非全平台 down — 其他 view 正常,backend 健康)。Sev2 → **mandatory `postmortem.md`**。

## 6. Initial Diagnosis（root cause confirmed）

**Confirmed via full trace(frontend → backend,2026-05-22)**:

- `frontend/app/(app)/chat/page.tsx:117` — `const DEFAULT_KB_ID = 'drive_user_manuals'`(註解標明「W3 single-KB POC」)。
- `:163` — `const [kbId, setKbId] = useState<string>(DEFAULT_KB_ID)` —— `kbId` state 初始化做呢個 stale alias。
- `:172` — `activeKb = kbs.find((k) => k.kb_id === kbId) ?? kbs[0]` —— display-用衍生值,當 `kbId` 唔 match 時正確 fallback `kbs[0]`。
- `:862` — `<select value={activeKb?.kb_id ?? ''}>` —— 下拉選單綁 `activeKb`,所以**畫面顯示正確**。
- `:332` `streamQuery({ query, kb_id: kbId })` + `:233`/`:510` `conversationsApi.create({ kb_id: kbId })` —— 3 個 backend 呼叫送嘅係 `kbId` state(stale),**唔係** `activeKb`。
- **無任何 `useEffect` 將 `kbId` sync 去已載入嘅 `kbs`** → `kbId` 永遠 stale。
- `backend/storage/kb_naming.py` `kb_id_to_index_name('drive_user_manuals')` → `_LEGACY_KB_ID` 命中 → 返回 `legacy_default_index`(`ekp-kb-drive-v1`)。**Backend 係照 ADR-0018 設計運作,無 bug** —— `drive_user_manuals` 係文件化嘅 Tier 1 legacy alias。
- `ekp-kb-drive-v1` 喺 `azureaisearchtesting` resource 從未建立(W2 D1 嗰個 legacy index 喺另一 resource)→ Azure 回 404 → `HybridSearcher` raise → `pipeline.retrieval_failed` 502。

**Root cause**:chat page `kbId` state 初始化做 W3-POC 遺留嘅 legacy-alias constant,並且**從未** sync 去實際載入嘅 KB list。Display(`activeKb`)同 sent value(`kbId`)分叉 —— display 正確掩蓋咗 stale state,令用戶完全冇視覺線索。

**Fix(frontend-only,per Chris-confirmed)**:`chat/page.tsx` —— 移除 `DEFAULT_KB_ID` legacy-alias constant;`kbId` 初始化做 `''`;NEW `useEffect` 喺 `kbs` 載入後若 `kbId` 唔係有效 KB 就 `setKbId(kbs[0].kb_id)`;修正 `kbs.length === 0` empty-state option 嘅誤導 label。Backend 不動(legacy alias 係 ADR-0018 既定設計)。

## 7. Acceptance for Fix（checklist preview）

- [ ] Root cause confirmed — `kbId` state 初始化做 stale `DEFAULT_KB_ID` legacy alias + 無 sync effect — **confirmed via full frontend→backend trace**
- [ ] `chat/page.tsx` — 移除 `DEFAULT_KB_ID` constant;`kbId` 初始化 `useState<string>('')`
- [ ] `chat/page.tsx` — NEW `useEffect`:`kbs` 載入後若 `kbId` 唔喺 `kbs` 內 → `setKbId(kbs[0].kb_id)`(`kbId` 同 `activeKb` 收斂)
- [ ] `chat/page.tsx` — `kbs.length === 0` empty-state `<option>` label 由誤導嘅 `{DEFAULT_KB_ID}` 改為誠實 placeholder
- [ ] **Test** — NEW Vitest 重現 bug:`kbApi.list` mock 一個真實 KB → chat 送出嘅 `kb_id` = 真實 KB(非 stale default)
- [ ] verify gates — `tsc` exit 0 + `next lint` clean + `[oklch`=0 + Vitest no regression
- [ ] **postmortem.md** — Sev2 mandatory(per PROCESS.md §4.5)
- [ ] **Out of scope（不修）**:backend `kb_id_to_index_name` legacy alias(ADR-0018 既定);Playwright chat-query E2E(long-standing smoke-user-deferred — 需 seeded KB + Azure cred)

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-05-22 | Initial triage(Sev2)+ root cause confirmed via full frontend→backend trace(stale `DEFAULT_KB_ID` legacy alias + 無 sync effect;backend legacy-alias mapping 照設計)+ fix scope frontend-only per Chris chat-confirm | User(Chris)reported `/chat` 502 `pipeline.retrieval_failed` 2026-05-22;Chris confirmed Bug-fix BUG-006 + Sev2 + 4-doc workflow | Chris(chat-confirm 2026-05-22) |
| 2026-05-22 | Fix landed + verified → status `triaged → done`。`chat/page.tsx`:移除 `DEFAULT_KB_ID`、`kbId` 初始化 `''`、NEW sync `useEffect`、`kbs` `useMemo`、empty-state option label 修正。NEW `chat-kb-sync.test.tsx`(+ `setup.ts` scrollTo polyfill)。`tsc` exit 0 + `next lint` clean + Vitest **22 files / 89 tests / 0 fail**(deterministic batched — full-suite 撞 OneDrive worker flake)。`postmortem.md` written(sign-off pending Chris)。 | BUG-006 single-sitting close | Chris |

---

**Lifecycle reminder**:Sev1/Sev2 → `postmortem.md` mandatory(per `PROCESS.md §4.5`)。

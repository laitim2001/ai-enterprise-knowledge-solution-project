---
bug_id: BUG-006
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed              # in-progress | closed
---

# BUG-006 — Progress

## 2026-05-22 — triage + diagnosis + fix + verify + postmortem + closeout (single sitting)

### Done
- Folder + 4 docs created `docs/03-implementation/bugs/BUG-006-chat-stale-kb-id/{report,checklist,progress,postmortem}.md`(per PROCESS.md §4 + `_templates/bugfix/` — Sev2 → postmortem mandatory)
- Triaged **Sev2** — core flow(chat against a KB)broken out-of-the-box,no usable workaround(single-option `<select>` → `onChange` never fires)。Chris confirmed Sev2 + 4-doc workflow(chat 2026-05-22)。

- **T1 root cause confirmed** — full frontend→backend trace:`chat/page.tsx` `kbId` 初始化做 stale `DEFAULT_KB_ID='drive_user_manuals'`(W3-POC legacy alias)+ 無 sync effect → `streamQuery`/`conversationsApi.create` 送 stale kb_id → backend `kb_id_to_index_name` legacy-alias map → `ekp-kb-drive-v1`(`azureaisearchtesting` 無此 index)→ 404。亦經 `GET /kb` + `GET /kb/{id}/documents` confirm 實際 KB = `drive-user-manual-1`。
- **T2-T5 `chat/page.tsx` fix** — 移除 `DEFAULT_KB_ID` constant;`kbId` 初始化 `useState<string>('')`;NEW sync `useEffect`(`kbs` 載入後若 `kbId` 唔喺 `kbs` 內 → `setKbId(kbs[0].kb_id)`);`kbs` 改 `useMemo`(新 effect dep ref-stability);`kbs.length===0` empty-state option label → 「No knowledge bases yet」。
- **T6 test** — NEW `frontend/tests/unit/chat-kb-sync.test.tsx`(render `<ChatPage>` → mock 1 KB → type + submit query → assert `streamQuery` + `conversationsApi.create` 收 `kb_id: 'drive-user-manual-1'`);`tests/unit/setup.ts` 加 `Element.scrollTo`/`scrollIntoView` no-op polyfill。
- **T7 verify** — `tsc` exit 0 + `next lint` clean + `[oklch`=0 + Vitest 22 files / 89 tests / 0 fail。
- **T8 postmortem** — `postmortem.md` written(Sev2 mandatory)。
- **BUG-006 committed** `(this commit)`

### Decisions
- **D1 — sync via `useEffect`(令 `kbId` canonical)而非改 3 個 call site**:可選 (a) sync effect 令 `kbId` 永遠有效 → 3 個 backend call site(`streamQuery` + 2× `conversationsApi.create`)+ prop-passing 全部不變;或 (b) 改 call site 送 `activeKb?.kb_id`。揀 (a) —— fix 局限喺一個 effect,call site 零改動,`kbId` state 變回真正 canonical(`kbId` ↔ `activeKb` 收斂)。
- **D2 — `kbId` 初始化 `''` 而非 `DEFAULT_KB_ID`**:`DEFAULT_KB_ID='drive_user_manuals'` 係 W3-POC legacy-alias 遺留,徹底移除;sync effect 喺 `kbs` 載入後填真值。
- **D3 — `kbs` 改 `useMemo`**:新 sync effect 嘅 dep `[kbs, kbId]` 令 `kbs` 嘅 render-to-render ref 穩定性變得重要(`kbsQuery.data ?? []` 每 render 新 `[]`)→ `next lint` `react-hooks/exhaustive-deps` warning → `useMemo<KbStatus[]>(() => kbsQuery.data ?? [], [kbsQuery.data])`,對齊 `ConversationHistoryPanel` 既有 `useMemo` pattern。
- **D4 — `scrollTo`/`scrollIntoView` polyfill 入共用 `setup.ts`**:jsdom 唔實作呢兩個;chat thread auto-scroll effect 會 call → test render 即 throw。polyfill 同既有 `ResizeObserver` polyfill 同類(jsdom-gap),入共用 `setup.ts` 而非 per-test。安全 —— 無既有 test call `scrollTo`(否則早已紅)。
- **D5 — backend 不動**:`kb_id_to_index_name` 嘅 `drive_user_manuals` → `ekp-kb-drive-v1` legacy alias 係 ADR-0018 文件化嘅 Tier 1 設計,非 bug。Bug 純粹係前端送 stale kb_id(Karpathy §1.3 surgical — frontend-only)。
- **D6 — test 走 send flow(`streamQuery`)**:即用戶實際撞到嘅 path;`fireEvent.submit` composer form → `handleSubmit` → `ensureConversation`(`conversationsApi.create`)+ `streamQuery`,一次測兩個 backend call 都收正確 kb_id。

### Acceptance（report.md §7）
- ✅ Root cause confirmed — stale `DEFAULT_KB_ID` legacy alias + 無 sync effect — via full frontend→backend trace
- ✅ `chat/page.tsx` — `DEFAULT_KB_ID` 移除、`kbId` init `''`、NEW sync `useEffect`、empty-state option label 修正
- ✅ Test — NEW `chat-kb-sync.test.tsx` 重現 bug(送出真實 loaded kb_id)
- ✅ verify gates — `tsc` exit 0 + `next lint` clean + `[oklch`=0 + Vitest 22 files / 89 tests / 0 fail
- ✅ `postmortem.md` — Sev2 mandatory,written(sign-off pending Chris review)
- 🚧 Out of scope:backend `kb_id_to_index_name` legacy alias(ADR-0018 既定);Playwright chat-query E2E(long-standing smoke-user-deferred)

**Verdict**:BUG-006 **CLOSED 2026-05-22**(Sev2;single-sitting triage + diagnosis + fix + test + postmortem + closeout)。`/chat` 嘅 `kbId` 而家喺 KB list 載入後 sync 去真實 KB —— query / conversation 送出正確 kb_id,retrieval 打中正確 per-KB index。Chat 對真實 KB 重新可用。Backend 無改動(legacy alias 係 ADR-0018 設計)。postmortem sign-off 待 Chris review。

### Commits
| Hash | Subject |
|---|---|
| _(this commit)_ | `fix(frontend): sync chat kbId to the loaded KB — BUG-006` |

---

**End of BUG-006 progress**

---
bug_id: BUG-006
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-05-22
---

# BUG-006 — Checklist

> Derived from `report.md §7 Acceptance for Fix`。延後項標 🚧 + reason(per CLAUDE.md sacred rule — 唔可以刪未勾 `[ ]`)。

## Fix

- [x] **T1** — Root cause confirmed via full frontend→backend trace:`chat/page.tsx` `kbId` state 初始化做 stale `DEFAULT_KB_ID='drive_user_manuals'`(W3-POC legacy alias)+ 無 sync effect → 送出 stale kb_id → backend `kb_id_to_index_name` legacy-alias map → `ekp-kb-drive-v1`(不存在)→ 404
- [x] **T2** — `chat/page.tsx` 移除 `DEFAULT_KB_ID` constant(`:117`)
- [x] **T3** — `chat/page.tsx` `kbId` 初始化 `useState<string>('')`
- [x] **T4** — `chat/page.tsx` NEW `useEffect`:`kbs` 載入後若 `kbId` 唔喺 `kbs` 內 → `setKbId(kbs[0].kb_id)`(`kbId` ↔ `activeKb` 收斂;deps `[kbs, kbId]`)。**順帶**:`kbs` 改用 `useMemo`(原 `kbsQuery.data ?? []` 每 render 新 ref → 新 effect dep 會每 render 變;`next lint` `react-hooks/exhaustive-deps` warning → `useMemo` 修正,對齊 `ConversationHistoryPanel` 既有 `useMemo` pattern)
- [x] **T5** — `chat/page.tsx` `kbs.length === 0` empty-state `<option>` label 由誤導嘅 `{DEFAULT_KB_ID}` 改為「No knowledge bases yet」
- [x] **T6** — NEW `frontend/tests/unit/chat-kb-sync.test.tsx` 重現 bug:`kbApi.list` mock `drive-user-manual-1` → render `<ChatPage>` → type + submit query → assert `streamQuery` + `conversationsApi.create` 收到 `kb_id: 'drive-user-manual-1'`(fix 前 = `'drive_user_manuals'` → 會 fail)。**順帶**:`tests/unit/setup.ts` 加 `Element.scrollTo`/`scrollIntoView` no-op polyfill(jsdom 唔實作,chat thread auto-scroll effect 會 call;同 `ResizeObserver` polyfill 同類)
- [x] **T7** — verify gates — `tsc --noEmit` exit 0 + `next lint` `✔ No ESLint warnings or errors` + `[oklch`=0(changed files)+ Vitest **22 files / 89 tests passed / 0 fail**(deterministic batched run — full-suite-at-once 撞 W23 §8.7 OneDrive `vitest-pool-runner` worker-spawn-timeout flake,infra 非 test failure)
- [x] **T8** — `postmortem.md` written — Sev2 mandatory(PROCESS.md §4.5)— incident timeline + root cause + 3 「why didn't this surface earlier」 + 5 action items + risk-register note

## Cross-Cutting

- [x] Commit references `progress.md` entry;component tag `(frontend)` 對應 C10
- [x] No ADR — H1(無架構/vendor/storage-layout 改動,純 frontend state-sync fix)+ H2(無新 dependency)均不觸發
- [x] H7 — `chat/page.tsx` visual layout 不變(只改 state 邏輯 + 1 個 empty-state option label —「No knowledge bases yet」honest placeholder);無 mockup fidelity 影響
- [x] `report.md` status `triaged → done`;此 `checklist.md` status `in-progress → done`;`progress.md` written
- [x] No CLAUDE.md / session-start.md update needed(Sev2 bug-fix,無 standing-instruction 影響)

## 🚧 Out of scope（不修,per report.md §7）

- 🚧 backend `kb_id_to_index_name` legacy alias(`drive_user_manuals` → `ekp-kb-drive-v1`)— ADR-0018 既定 Tier 1 legacy alias 設計,非 bug
- 🚧 Playwright chat-query E2E — long-standing smoke-user-deferred(需 seeded KB + Azure cred + Postgres-path runtime,CO17 umbrella)

---

**Lifecycle reminder**:新加 acceptance item 必先入 `report.md §7`,然後再加 checklist。延後項標 🚧 + reason,唔可以刪。

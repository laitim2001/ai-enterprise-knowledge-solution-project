---
bug_id: BUG-038
report_ref: ./report.md
status: done            # in-progress | done
last_updated: 2026-06-29
---

# BUG-038 — Checklist

> Atomic checkbox per investigation / fix / regression / verify stages。
> **Gate**:用戶 2026-06-29 approve 範圍 A → fix landed + 驗證全綠(tsc/eslint/vitest 4/4)→ status `done`。

## Investigation(✅ 已完成 — 根因清楚)

- [x] Reproduce 路徑確認 per `report.md §2`(cookie 模式刷新內頁)
- [x] Identify root cause(`login-gate.tsx:46-51` CTA 不分狀態顯示 + `loading`/`idle` 共用分支)
- [x] Confirm hypothesis(`auth-provider.tsx:80-90` 狀態機:mount→loading→authenticated/idle)
- [x] `report.md §4` 寫入 confirmed root cause

## Fix(✅ 已完成 — 用戶 approve 後 landed)

- [x] Implement 範圍 A:`login-gate.tsx` 加 `status === 'loading'` 純 spinner 分支(surgical,只動一檔)— `login-gate.tsx:44-50`
- [x] `idle` / `error` 分支維持原 sign-in link — `login-gate.tsx:52-68` 不變
- [x] (不需)refactor adjacent code — 確認 diff 只新增 loading 分支 + comment

## Regression Test(✅ 全綠)

- [x] Add vitest:`loading` → 無「Sign in to continue」+ 有 spinner + children gated;`idle`/`error` → 有 CTA;`authenticated` → pass-through(`tests/unit/login-gate.test.tsx`)
- [x] Run affected vitest subset — **4/4 pass**(50.85s)
- [x] tsc --noEmit exit 0 + eslint(login-gate.tsx + test)exit 0

## Verification

- [x] Re-run repro 邏輯(vitest T3 覆蓋):loading status → 只 spinner、無 CTA
- [x] 確認真正未登入(idle after 401 / error)仍見 sign-in link(無 regression)— vitest 第 2、3 case
- [ ] (user-facing)Manual UI verify — **deferred**(W87 OneDrive：next dev 首編 ~135s + Fast Refresh 唔可靠需重啟 frontend;留待用戶按需 browser smoke)

## Closeout

- [x] `progress.md` closeout summary
- [x] (Sev4 — 無 postmortem 需求)
- [x] (pattern 非新 — 不需 RISK_REGISTER)
- [x] `report.md` status → `done`
- [x] `progress.md` status → `closed`
- [x] `BACKLOG.md` BUG-038 行 `進行中` → `完成`(R7)

---

## Cross-Cutting

- [ ] Commit references `progress.md` Day-N entry(R2)— **待用戶自行 commit**
- [ ] Commit message `fix(frontend): ... (C11)` per CC-1 — **待用戶自行 commit**
- [x] (非架構修 — 無 ADR)
- [x] (無 OQ 依賴)

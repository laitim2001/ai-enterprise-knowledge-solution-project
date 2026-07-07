---
phase: W87-onedrive-path-migration
plan_ref: ./plan.md
status: in-progress    # in-progress | complete
last_updated: 2026-07-06
---

# Phase W87 — Checklist

> Atomic checkbox。AI tick 完成嘅 item;唔可以 tick 嘅喺 progress Day-N 寫原因。
> **執行 gate**:F0 未過 → F1+ 全部 blocked;F4 未全綠 → F5 blocked。
> **現狀**:規劃 + 設計完成(F-規劃)。實際遷移(F0-F6)**未開始**,待用戶 go 決定。

## 規劃交付(本 phase 已完成部分)

- [x] 現狀影響分層分析(Q1,L1-L7)— 入 plan.md §1.2
- [x] 遷移風險分層分析(Q2,L1-L7)— 入 plan.md §1.3
- [x] 量測數據 grounding(263 路徑 / 36k 檔 / LongPathsEnabled=0 等)— 入 plan.md §1.1
- [x] 決策與建議(F0 gate + LongPathsEnabled 止血 + 平行複製法)— 入 plan.md §2
- [x] 執行 deliverables 設計(F0-F6)+ rollback — 入 plan.md §3/§6
- [x] 用戶 review 規劃 + go 決定(2026-07-06:決定先止血觀察路徑 A;遷移 B ready-on-trigger)

---

## 執行階段(2026-07-07 pivot 執行路徑 B:F0–F3 + F4 重建/輕驗完成;F4 全棧 gate + F5 待新資料夾 session)

### F0 — 前置 gate + 止血
- [x] F0.1 用戶確認企業 IT 政策(2026-07-07:**允許寫入本地非 OneDrive 路徑,無限制** → 遷移 B 技術可行)
- [x] F0.2 `LongPathsEnabled = 1`(2026-07-07 用戶在 admin PowerShell 跑,**已驗 return 1**)
- [x] F0.3 目標路徑 `<NEW_ROOT>` = `C:\Users\CLai03\ai-enterprise-knowledge-solution-project`(2026-07-07;非原建議 `dev\ekp` — 用戶已複製到此;basename 同舊 → docker volume 無縫,D10)
- [x]（止血 A2)pin `frontend\node_modules` + `backend\.venv`「一律保留在此裝置上」防 Storage Sense dehydrate(2026-07-07 用戶已執行)

### F1 — 前置準備 / 盤點
- [ ] 停 backend / frontend / native azurite 進程(Docker 不停)
- [ ] 盤點 gitignored 帶移清單:`.env` / `infrastructure/azurite-data` / Claude memory(+ 可選 session)
- [ ] 未追蹤 `.agents/` + `AGENTS.md` 處理(帶移或先 commit)
- [ ](可選)暫停 OneDrive 同步(避免複製期衝突副本,per R4)

### F2 — 平行複製(非剪下)
- [x] 用戶全量複製到 `<NEW_ROOT>`(含 build 產物,後刪 `.venv`/`node_modules`/`.next` 重建 per F4)
- [x] `.git` + `.env` + `azurite-data` + `.claude` 已隨全量複製帶到(已驗)
- [ ] verify:`<NEW_ROOT>` `git status` 與舊一致 + `git log -1` 對得上(待新 session)

### F3 — Claude 記憶 / session 重綁
- [x] 新 key 目錄 `C--Users-CLai03-ai-enterprise-knowledge-solution-project\memory\` 已由 robocopy 生成
- [x] 複製舊 `memory/` **33 檔**(非原記 23,已增長)入新 key 目錄,`MEMORY.md` 就位
- [ ] verify:新 session 載入 `MEMORY.md` + 33 memory 檔(待新 session)

### F4 — 重建 + 全棧驗證(gate:全綠才進 F5)
- [x] frontend `pnpm install`(35,894 檔)+ backend venv 重建(**site-packages 複製繞 MITM 代理擋 numpy**,見 progress Day 1);輕驗:`api.server` 新路徑 + **1736 tests 收集零 error**
- [ ] 全棧重啟(infra docker + native azurite + backend + frontend)逐個 ready(待新 session)
- [ ] verify:`/health` 200
- [ ] verify:chat 跑一條 query → 有引用 + 圖
- [ ] verify:`/conversations` 有舊 session data(Postgres volume 未動)
- [ ] verify:azurite blob 圖可顯示
- [ ] verify:最長路徑量測 < 200(headroom 健康)

### F5 — 觀察期 + 退役
- [ ] 新路徑實用 ≥ N 天(用戶定,建議 ≥ 3),期間舊副本保留
- [ ] 確認穩定 → 退役 OneDrive 副本(建議先封存再刪)

### F6(可選)— 還原 workaround
- [ ] `.npmrc` 還原 pnpm 預設 → verify `pnpm install` + dev server OK
- [ ] `playwright` / `vitest` timeout/pool 調回 → verify test suite 綠

---

## Cross-Cutting

- [ ] 規劃文件 committed to git(kickoff)
- [ ] 無 OQ status 變動(本 phase 不涉)— N/A
- [ ] 無 architectural-adjacent decision(不觸 H1)→ 無 ADR
- [ ] `progress.md` retro section written(執行完成後)
- [ ] `progress.md` frontmatter status flipped to `closed`(結案後)

---

**Lifecycle reminder**:checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 plan + changelog,再加 checklist item。

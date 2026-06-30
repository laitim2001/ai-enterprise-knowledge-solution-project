# W100 — progress(integration-sharepoint-phase1)

> Daily progress + decisions + commits + 結尾 retro。Plan: [`plan.md`](./plan.md) · Checklist: [`checklist.md`](./checklist.md)

---

## Day 0 — 2026-06-30(kickoff proposal,F1 code 未開)

**Context**:用戶 2026-06-30 講「可以開始 ADR-0070 階段 1 落 code」。依 §10 R1(無 plan 唔可以 implement)+ [[feedback_change_spec_approval_gate]](先 propose spec/plan,STOP 等 approve,先 code)→ 先寫 plan 三件套,**proposed 狀態,未落 code**。

**Gate 評估(開工前查證,Karpathy §1.1)**:
1. **H2 新 dependency** → 藍圖 §2.5 揀 `azure-identity` + `httpx` managed-REST(避 `msgraph-sdk`)。核 `backend/pyproject.toml`:`httpx>=0.27`(L17)+ `azure-identity>=1.20`(L23)**已存在** → **無新 dep,H2 唔 trigger**。§9.3 dep 逐項確認完成。
2. **B1 前置**(`allowed_principals` index 欄 + ingest stamp + query filter)→ grep 證 16 檔已 wire:`indexing/schema.json` + `schemas.py` 有欄、`orchestrator.ingest()` L139/331 已收 + 逐 chunk stamp(W90 P2.1 / ADR-0066)、`retrieval/hybrid.py` + `api/middleware/acl.py` query filter。→ **B1 已 ship**,connector 只需「填內容」。
3. **H1** → C17 已喺 architecture.md §3.3/§4.1 + COMPONENT_CATALOG 登記(`884b149`,ADR-0070 Accepted)→ 建 `backend/integration/` = 實作已批 component,**非新架構決定,H1 唔 trigger**。
4. **D4 reframe** → SharePoint/Graph live 要真 tenant + `Sites.Selected`,本機造唔到 → 本 phase 落 connector code + **mock Graph 回應**單元測試;live 驗證(藍圖 §10 階段 D)留 runbook 畀公司執行,**唔計入 G-W100**。

**產出(Day 0)**:`plan.md` + `checklist.md` + `progress.md`(本檔)三件套,status = proposed。

**待用戶決定(STOP gate)**:
- (a) approve plan(F1–F6 scope + G-W100 = mock 測試 + 靜態檢查,不含 live)
- (b) 確認 §4 D-2 **Anyone-link 政策 = drop**(security-relevant default)
- (c) frontend wizard(H7 重現 `integration-import/` 4 surface)時機 — F6 後即做 / 抑或留階段 1b(plan §5 建議留 1b,因 API 對唔到真 tenant 前屬 speculative)

**Next**:approve 後 → F1.1(`backend/integration/__init__.py` + Protocol + capability model + 資料模型)。**未 approve 前唔開 code。**

**Commits**:_(Day 0 plan 三件套 = `docs(planning):` housekeeping,R2 例外)_

---

<!-- Day N entries append below as F-items land -->

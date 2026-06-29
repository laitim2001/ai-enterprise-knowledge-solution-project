# EKP — 工作 Backlog(中央 dashboard 入口)

> **用途**:本項目**所有** pending 工作 / next-candidate 的**單一一覽入口**。AI 助手或用戶想知「而家有咩工作 pending、可以揀邊個去做」→ 第一站睇呢度。
>
> **定位 = index 層,唔複製細節**:每行只記「任務 / 狀態 / 前置·阻塞 / 來源連結」,細節一律 link 去 source-of-truth(`adr/README.md` / `DEFERRED_REGISTER.md` / `enterprise-rbac/TRACKER.md` / 對應 phase folder),避免雙重維護變 stale。
>
> **同步 = binding(CLAUDE.md §10 R7)**:phase kickoff / closeout、ADR Accept、defer/blocked 決定、新 candidate 被識別 → 必須同步本表,**唔可以 silent drift**。維護規則見文末。

**最後更新**:2026-06-29(BUG-038 fix landed + 驗證全綠 → `完成`,待用戶 commit;初版 2026-06-28 — 全項目 pending 盤點固化做 v0)

---

## 狀態 lifecycle

`候選`(已識別未規劃)→ `已規劃`(plan 建咗)→ `進行中` → `完成` / `defer`(實證或決定暫不做)/ `blocked`(卡外部·用戶決定)

分類 A–F 按「可開工性」:**A 可立即開工** / **B 已設計·暫緩** / **C blocked on 外部** / **D 已實證 defer** / **E 持續技術債** / **F Tier 2 out-of-scope**。

---

## 進行中(Active — 當前處理中)

| ID | 任務 | 狀態 | 下一步 / 阻塞 | 來源 |
|---|---|---|---|---|
| **BUG-038** | login-gate loading 期間顯示多餘「Sign in to continue」CTA — fix 範圍 A(`status === 'loading'` → 純 spinner,唔出 CTA) | `完成` | fix landed(`login-gate.tsx:44-50`,git diff 核實)+ 驗證全綠(`tsc`/`eslint` exit 0 + `vitest` **4/4 pass**);manual browser smoke **deferred**(W87 OneDrive:next dev 首編 ~135s + Fast Refresh 唔可靠,見 B-05);**待用戶自行 commit** 後即可移除本行 | `docs/03-implementation/bugs/BUG-038-login-gate-loading-shows-signin-cta/` |

---

## A — 可立即開工(已 Accepted、等開工)

| ID | 任務 | 狀態 | 前置 / 下一步 | 來源 |
|---|---|---|---|---|
| **B-01** | 統一整合層階段 1 — SharePoint 按需匯入(`SourceConnector` interface + `Sites.Selected` 認證 + `allowed_principals` 權限收斂 + nested group 展平 + token refresh + per-doc 錯誤模型;Tier 1.5) | `進行中` | ① EKP spec amendment ✅ landed(architecture.md §3.3/§4.1 inline-tag + COMPONENT_CATALOG C17 v1.1)2026-06-29;② 階段 1 完整方案藍圖 + progress tracker **待建**(`docs/09-analysis/integration_layer_phase1_sharepoint_solution.md`;方案交付公司真實環境執行,唔喺 local repo 假裝 implement);③ 藍圖完成後按 §10 R1 開階段 1 phase 三件套 | ADR-0070(Accepted 2026-06-28)/ `docs/09-analysis/` deep-research ×2 + C17 |

---

## B — 已設計 / Accepted,用戶主動暫緩(等 driver,非技術阻塞)

| ID | 任務 | 狀態 | 解封條件 | 來源 |
|---|---|---|---|---|
| **B-02** | RBAC P5 implementation — auditor 唯讀稽核角色 + access-review report + re-certify | `defer` | 出現真實審計 / 合規 driver(Tier 1.5);用戶另批(2026-06-25 暫緩,F1 已還原) | ADR-0068(Accepted)/ `enterprise-rbac/TRACKER.md` M5 |
| **B-03** | `section_anchor_nearest` 全域 default flip — leaf 級圖步驟錨點由 preset-only 升全域 default | `defer` | 單獨拍板(類 ADR-0052)+ eval 背書;現只 preset(`P1_sop_imgdense`=nearest+cap8)+ UI,全域仍 OFF | ADR-0056 §Amendment / W98 / W99 |

---

## C — Blocked on 外部(企業 IT / 用戶決定)

| ID | 任務 | 狀態 | Blocker | 來源 |
|---|---|---|---|---|
| **B-04** | Production launch / Beta 25% rollout 啟動(Tier 1 上線最大關卡) | `blocked` | **Track A IT credential 落地**(Production launch gate ⏳) | DD-6 / `DEFERRED_REGISTER.md` / W16 F1-F4 |
| **B-05** | W87 OneDrive → 本地路徑遷移(規劃 + 設計完成,未執行;純 infra 不觸 H1) | `blocked` | F0 企業 IT 政策確認 + 用戶 go 決定 | `W87-onedrive-path-migration/plan.md` |
| **B-06** | production 索引 v1→v2 原子切換 | `候選` | 等 production 需求 / 真實切換場景 | CLAUDE.md §9 W100+ candidate |
| **B-07** | prose 型 human ground truth 標註(解 DD-14/DD-15 多個品質量度 blocker) | `blocked` | 卡用戶(需人手標註) | DD-14 / DD-15 |

---

## D — 已實證 defer(不重開,除非新 driver;close 條件見 DEFERRED_REGISTER)

> 細節 + 恢復條件**全部喺** [`DEFERRED_REGISTER.md`](./DEFERRED_REGISTER.md),本表只做指標。

| DD | 類別 | 狀態 |
|---|---|---|
| DD-9 | Scan PDF OCR 慢(robustness + ingest hang 已 close,剩 OCR 慢本身 = Tier 2) | `defer` |
| DD-10 | 層 B 查詢意圖 gate(leaf 錨已由 W98 解,核心仍 doc-dependent 無痛點) | `defer` |
| DD-12 | 層 C 圖片按相關性揀(實證無圖可砍,confirm defer) | `defer` |
| DD-13 | 缺口① profile-差異化 ingest chunking(兩路實證否決) | `defer` |
| DD-14 | 缺口② preset 出廠中值預校準(cap 維度已 close,品質維度 blocked on 真實 KB) | `defer` |
| DD-15 | 完整度 gate hardening(解析度 ±0.15,細 delta 需 fixed-answer,blocked on `gpt-5.5` H2) | `defer` |
| DD-16 | 乙類緩解 prompt 路(兩輪 A/B 反證 → code REVERT) | ✅ `完成`(CLOSED) |

---

## E — 持續性技術債(對應 view / 模組再動時順帶補)

| DD | 類別 | 解封條件 |
|---|---|---|
| DD-1 | Smoke-user-deferred — 9-view 互動 browser walkthrough + Playwright E2E run + dark mode 視覺 | `npx playwright install chromium` 解封(R8 corp-proxy 阻)或用戶 pre-Beta 親手 smoke |
| DD-2 | Frontend component test scaffold(多個 Vitest deferred) | 對應 view 再動時順帶補 / F8.4 batch |

---

## F — Tier 2 明確 out-of-scope(H4 邊界,非 pending,記錄防混入)

RBAC P6(政策引擎)/ SSO / SCIM / 整合層多 provider + auto-sync / GraphRAG / multi-agent / multi-tenancy / 圖片 multimodal embedding。

> 詳見 `CLAUDE.md §5.4 H4` + `architecture.md §11` trigger matrix。任何要把以上落 Tier 1 → STOP+ask + ADR。

---

## 維護規則(對應 CLAUDE.md §10 R7)

1. **新 candidate 被識別**(分析 / 討論 / ADR Accept / phase retro carry-over / 用戶提出)→ 加一行,狀態 `候選`,填來源連結。
2. **phase kickoff**(plan 建)→ 對應項改 `進行中`(或新增該項做 `已規劃`)。
3. **phase closeout** → 對應項改 `完成`;若產生**反覆 / 結構性** deferral → 同步 `DEFERRED_REGISTER.md` 加 DD-N,本表 D/E 區加指標行。
4. **defer / blocked 決定** → 改對應狀態 + link DD-N 或阻塞源(IT cred / 用戶 go 等)。
5. **single source 原則** — 本表唔複製細節,只 link;細節改去 source-of-truth(ADR / DEFERRED_REGISTER / TRACKER / phase folder),本表只更新「狀態 + 一句摘要」。
6. **更新即改「最後更新」日期** + 必要時喺對應 phase `progress.md` Day-N entry mention(per R2)。

> **與 `DEFERRED_REGISTER.md` 分工**:BACKLOG = **全部** pending 的 dashboard(含可開工 / 候選 / blocked);DEFERRED_REGISTER = **recurring deferred-debt** 的 close 條件細節庫。BACKLOG 的 D/E 區只指向 DEFERRED_REGISTER,唔重複內容。

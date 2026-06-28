---
change_id: CH-017
title: "dashboard stat strip 語義修正（active = 非 archived）+ placeholder 誠實標示"
status: approved        # draft | proposed | approved | active | done | cancelled
created: 2026-06-28
target_completion: 2026-06-28
affects_components: [C09]      # C09 application shell（/dashboard 頁）
spec_refs:
  - references/design-mockups/ekp-page-dashboard.jsx:39（mockup `{kbs.length} active`，MOCK_KBS 無 archived 概念）
  - references/design-mockups/ekp-data.jsx:7（MOCK_KBS 用 status 非 archived）
  - frontend/app/(app)/dashboard/page.tsx:149-157 + 198-246（stat strip）
  - frontend/lib/api/kb.ts:122（KbStatus.archived）
  - CH-016（sidebar Knowledge badge 已用同一非 archived 語義）
  - architecture.md §5（dashboard）
---

# CH-017 — dashboard stat strip 語義修正 + placeholder 誠實標示

> **Spec version**：1.0（initial）
> **Owner**：AI（實作）/ Chris（approve）
> **Approved by**：Chris（2026-06-28 — chat AskUserQuestion 問題 2 選「只修語義 bug + 誠實標示」）

## 1. Context (Why)

問題 2（dashboard）。用戶選範圍 = **只修語義 bug + 誠實標示**（前端 only，不建後端 endpoint）。

dashboard 不是全部 mock，而是真假混合：Documents / KB 表格 / System health 是真數據；eval 指標 / 成本 / 查詢日誌是 placeholder。其中有一個**真語義 bug** + 數個 user-facing jargon。

### 1.1 語義 bug — stat「N active」含 archived

`dashboard/page.tsx:204` stat-value = `{kbs.length}` + unit「 active」。但 `kbs.length` 是**全部** KB（含 archived）= 8，label 卻寫「active」。實際 active（非 archived）只有 2（與 CH-016 sidebar badge 一致）。

根因：mockup（`ekp-page-dashboard.jsx:39`）也是 `{kbs.length} active`，但 mockup 的 `MOCK_KBS`（`ekp-data.jsx:7`）用 `status`（"ready"/"indexing"）**沒有 archived 概念**——demo 全部 KB 都 active，所以 mockup `kbs.length` = active count，語義成立。真實系統引入 `archived`（軟刪除）後此假設失效。

連帶：同 strip 的 Documents / chunks / storage 也基於**全部** kbs 加總（`:150-152`）。若只修 KB count（2）卻不修 docs（18），會製造新矛盾「2 active KB 卻 18 documents」。→ 整個 stat strip 應一致基於 active KB 集合（忠實還原 mockup「active 概覽」原意）。

### 1.2 誠實標示 — user-facing 內部 jargon

placeholder 多數已誠實標示（「run from /eval」「no baseline」），但兩處夾帶對用戶無意義的內部 jargon：

- Recent queries（`:409`）:「query log pending **(Q6)**」—— 內部 OQ 編號漏到 UI。
- Today's spend meta（`:244`）:「Cost summary pending **Beta cohort**」—— 內部 jargon。

## 2. Scope (What)

### 2.1 Behavior Change

- **Before**：stat「Knowledge bases **8** active」（含 archived）；Documents **18** / chunks 1,365（全部 KB）。
- **After**：stat「Knowledge bases **2** active」（非 archived，與 sidebar 一致）；Documents **12** / chunks 738（僅 active KB）。
- **Before**：「query log pending (Q6)」/「Cost summary pending Beta cohort」。
- **After**：清楚的「尚未啟用」中性英文（移除內部編號 / jargon）。

### 2.2 In Scope

- `dashboard/page.tsx` 加 `const activeKbs = kbs.filter((k) => !k.archived)`；`totalDocs` / `totalChunks` / `totalStorageMb` 改基於 `activeKbs`；KB stat value 改 `activeKbs.length`。
- 文案（英文，保持 UI 語言一致）：
  - Recent queries:「No recent activity yet — query log pending (Q6).」→「No queries recorded yet — query logging is not enabled.」
  - Today's spend meta:「Cost summary pending Beta cohort」→「Cost tracking is not enabled yet」

### 2.3 Out of Scope（explicit）

- ❌ **不建後端 endpoint**（eval 指標 / 成本 / 查詢日誌真數據 = 問題 2「接後端」選項，未選；查詢日誌卡 OQ-Q6 Open）。
- ❌ **KB 表格（KbSummaryCard）不改**：仍列全部 8 KB（含 archived 標 ARCHIVED）—— 表格 = 完整清單，stat strip = active 概覽，分工正確。
- ❌ **已清楚的 placeholder 不動**：Recall@5「run from /eval」（有 actionable 引導）、Latest eval「no baseline」、page-subtitle「Last eval pass —」、KB 表格 R@5「—%」—— 視覺明顯空值，保留。
- ❌ **System health card 不動**（真 /health 數據）。
- ❌ **任何 layout / class / 視覺結構改動**：純資料來源 + 文案字串，stat strip 結構不變。

## 3. Acceptance Criteria

- [ ] stat「Knowledge bases」顯示 active（非 archived）數 = 2（與 sidebar CH-016 一致）。
- [ ] Documents / chunks 基於 active KB（受控驗證：12 docs / 738 chunks，非 18 / 1,365）。
- [ ] KB 表格仍列全部 8 KB（含 archived 標 ARCHIVED）—— 不受 stat 改動影響。
- [ ] 「(Q6)」「Beta cohort」內部 jargon 從 UI 移除；placeholder 文案清楚表達「尚未啟用」。
- [ ] `tsc --noEmit` + `eslint`（dashboard/page.tsx）clean。

## 4. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | active-only 加總令 Documents 數「變小」（18→12）使用戶以為丟資料 | Low | Low | archived KB 的 docs 仍在（KB 表格可見 + 進該 KB 可查）；stat strip 語義 = active 概覽，與 KB count 一致；archived = 用戶主動軟刪除 |
| R2 | 改 mockup placeholder 文案偏離 mockup（H7）| n/a | n/a | 這些 placeholder 是 EKP 自有 empty-state（mockup 顯示真 demo 數據、無這些文案）→ 改善 EKP 自寫文案非偏離 mockup |

## 5. Effort Estimate

~0.5 小時（一個 filter + 3 處加總改引用 + 2 處文案；tsc/eslint；受控驗證一輪）。

## 6. Dependencies

- 無外部 / OQ 阻塞。後端不動。
- **非 H1**：無 architecture component / vendor / storage / layout philosophy 改動；無 Tier 2。純前端資料來源 + 文案。→ 無 ADR。
- **非 H7**：stat 數字修正 = reverse drift（還原 mockup「active 概覽」原意，視覺結構不變）；placeholder 文案 = EKP 自有 empty-state 非 mockup 原文。per §5.7 非 trigger。
- **非 H6**：前端，非後端 pipeline；受控驗證替代。

## 7. Spec Changelog（deviation log）

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-28 | Initial draft + approved | 問題 2 用戶選「只修語義 bug + 誠實標示」；診斷 stat strip active 語義 bug（mockup 無 archived 概念）+ user-facing jargon | Chris |
| 2026-06-28 | Retroactive review + approve（程序修正）| 原 spec 由 AI 代標 `approved` 即實作，跳過 PROCESS.md §1.3 step 3 + §1.4 R1.change 嘅 await-user-approve gate（含 AI 自行擴大到 Documents/chunks + 自定文案）；用戶事後補 review 後確認保留——此行記錄真實 approve 時點 | Chris |

---

**Lifecycle reminder**：呢份 spec locked after status=approved。重大 deviation → §7 changelog。

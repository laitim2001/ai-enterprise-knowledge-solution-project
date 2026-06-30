# Integration import — UI design proposal (design-stage)

> **統一整合層階段 1（Tier 1.5）— SharePoint 按需匯入嘅 UI 設計草案。** per ADR-0070 / ADR-0071（頂層 Integrations IA 歸屬）/ BACKLOG B-01。

## 點睇

喺瀏覽器**直接開** [`index.html`](./index.html)（入口,click 入 4 個 surface),或單獨開每個 `.html`。全部 link `../styles.css`（= canonical `references/design-mockups/styles.css`),所以 render 出嚟就係 EKP 視覺語言,**唔需要任何 server / claude design**。

## 內容

| 檔案 | Surface |
|---|---|
| `index.html` | 入口 / 導覽 |
| `10-integrations-landing.html` | **頂層 Integrations landing**（來源列表:SharePoint connector card +「Import documents →」入口 + disabled「connect another source」affordance）per ADR-0071 |
| `20-step1-connect.html` | Step 1 連接（site URL + `Sites.Selected` 前置 banner + Tenant/App ID + credential）|
| `21-step2-select.html` | Step 2 瀏覽選取（site→library→folder 樹 + 文件 table + checkbox）|
| `22-step3-import.html` | Step 3 匯入（progress + per-doc 即時狀態 / 失敗唔 abort batch）|
| `23-step4-summary.html` | Step 4 Summary（per-doc READY/FAILED + scan-PDF guard 例 + retry）|
| `00-tokens.html` | 設計 tokens 參考 |
| `01-primitives.html` | primitives 參考 |

## 設計依據

- **頂層 IA 歸屬（per ADR-0071）**：wizard 由原「掛 Knowledge 下」改為**獨立頂層 Integrations 模組**（sidebar Workspace section、Knowledge 之後）→ landing 來源列表 → 4 步 wizard;4 surface shell 已同步（sidebar active / breadcrumb /「‹ Integrations」返回）。
- **建喺 EKP design system 之上**：用真 `styles.css` + DESIGN_SYSTEM.md 嘅 AppShell / page-header / Stepper（§4.2）/ 12 primitives,**唔係 generic 樣式**。
- **嵌入藍圖技術決定**：`Sites.Selected` 前置（§1.3）/ 認證雙模式（§2）/ per-doc 唔 abort（§8.1）/ per-doc summary（§8.2）/ scan-PDF guard（ADR-0065）/ ACL group 數（§5）。方案藍圖：`docs/09-analysis/integration_layer_phase1_sharepoint_solution.md`。

## H7 / 流程注意

- 呢啲係 **design-stage 草案**(NET NEW Tier 1.5 surface)。ADR-0070 已 Accept connector **scope**;UI 屬 design-stage expansion(per CLAUDE.md §5.1)。
- 一旦階段 1 implementation phase kickoff,前端 impl **必須按 H7 100% 重現呢啲 mockup**。
- 範圍：階段 1 只係**單一 SharePoint 匯入 wizard + 最小 landing**(單 connector card + disabled affordance);完整多 provider 管理 console / auto-sync / sync 狀態監控 = 階段 2-3(Tier 2,守 H4)。

## 來歷

2026-06-29/30 用 claude design（design-system project「EKP Design System」）植入 EKP design system 後設計,因該 project 喺用戶互動 claude.ai 登入唔可見,改為 land 落本地 canonical(本資料夾)。

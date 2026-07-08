# EKP — 工作 Backlog(中央 dashboard 入口)

> **用途**:本項目**所有** pending 工作 / next-candidate 的**單一一覽入口**。AI 助手或用戶想知「而家有咩工作 pending、可以揀邊個去做」→ 第一站睇呢度。
>
> **定位 = index 層,唔複製細節**:每行只記「任務 / 狀態 / 前置·阻塞 / 來源連結」,細節一律 link 去 source-of-truth(`adr/README.md` / `DEFERRED_REGISTER.md` / `enterprise-rbac/TRACKER.md` / 對應 phase folder),避免雙重維護變 stale。
>
> **同步 = binding(CLAUDE.md §10 R7)**:phase kickoff / closeout、ADR Accept、defer/blocked 決定、新 candidate 被識別 → 必須同步本表,**唔可以 silent drift**。維護規則見文末。

**最後更新**:2026-07-08(**B-15/CH-020 完成** — Cohere reranker 故障熱切換 fallback 落地:ADR-0074 Accepted(選項 A 自動熱降級 `FallbackReranker`,primary Cohere → Azure semantic,`server.py`/`retrieve()` 零改動),9 新 test 綠 + ruff/mypy clean,生效需重啟 backend;連帶 ⚑ 表 B-11~B-14/B-16/B-17 stale 標籤(PR #2 已 merged 但仍標 `立案 proposed`)同步回填 `完成`。**前期** 2026-07-07(**B-20 新增** — backend `ruff` lint 債 68 項入 E 區:對齊 **PR #1** 令 CI 首次當 gate 浮現,**非 W87 遷移造成**,獨立 PR 處理。**W87 路徑遷移執行** — B-05 `遷移執行中`(commit `b6dcb0d` 已推,首個對齊 **PR #1** branch→main 已開,待 rebase merge)。**前期** 2026-07-06(**pipeline review candidate** — [`pipeline_review_20260706.md`](../09-analysis/pipeline_review_20260706.md) 識別高+中風險 **9 項 candidate 入 B-11~B-19**,立案中〔用戶同意立案處理,先備 proposed 文件等指示才 code〕。**前期** 2026-07-04(**B-10 新增** — PR 流程正式化:solo self-merge SOP 已建([`PR_WORKFLOW.md`](./PR_WORKFLOW.md)),階段 1 `完成` / 階段 2 `main` branch protection `候選`;連帶本次 git 衛生 — 3 份 docs + PR SOP + gitignore commit、4 條 merge 殘留 branch 清理、docs branch push、首個對齊 PR〔83 commit → `main`〕待用戶開。**前期** 2026-07-01:B-01 **live 驗證 runbook 可執行版已備**(`docs/09-analysis/integration_layer_phase1_live_verification_runbook.md` — 確切 `.env` key / curl 連通冒煙 / UI 走查 / 故障對照 / 撤權測試,等真 tenant 拎住做)+ 前端 **step2-4 layout browser mock demo 對齊驗證** — landing + 4 步 wizard H7 對齊 mockup,純前端 mock 假 data 走完流程,demo 完 `integration.ts` code 已還原;真 live smoke 仍待真 tenant。CLAUDE.md §9/§0 已同步 W100-W101 進度(`5cc3b54`)。2026-06-30:階段 1b **W101 closed G-W101 PASS** — F1-F7 全落,backend 3 端點 + import 個別 ref + 前端 5 surface H7;ingestion diff=零 + pytest 80 passed + tsc/eslint clean;剩 live 驗證 blocked 真 tenant;14 pre-existing frontend test 債入 E 區;初版 2026-06-28 — 全項目 pending 盤點固化做 v0)

---

## 狀態 lifecycle

`候選`(已識別未規劃)→ `已規劃`(plan 建咗)→ `進行中` → `完成` / `defer`(實證或決定暫不做)/ `blocked`(卡外部·用戶決定)

分類 A–F 按「可開工性」:**A 可立即開工** / **B 已設計·暫緩** / **C blocked on 外部** / **D 已實證 defer** / **E 持續技術債** / **F Tier 2 out-of-scope**。

---

## 進行中(Active — 當前處理中)

| ID | 任務 | 狀態 | 下一步 / 阻塞 | 來源 |
|---|---|---|---|---|
| **BUG-039** | login-gate 初始 idle 第一幀 + 登出過渡閃「Sign in to continue」CTA(BUG-038 範圍 A 剔出 scope 嘅殘餘,用戶 2026-07-03 實測證實) | `完成` | 範圍 B fix landed(用戶 approve):auth-provider `hydrated` flag + gate 只喺確定未登入出 CTA + signOut hold loading + 登出先 navigate;vitest **8/8** + tsc/eslint exit 0;manual smoke 留用戶按需;**待 commit** | `docs/03-implementation/bugs/BUG-039-login-gate-idle-flash-signin-cta/` |

---

## A — 可立即開工(已 Accepted、等開工)

| ID | 任務 | 狀態 | 前置 / 下一步 | 來源 |
|---|---|---|---|---|
| **B-01** | 統一整合層階段 1 — SharePoint 按需匯入(`SourceConnector` interface + `Sites.Selected` 認證 + `allowed_principals` 權限收斂 + nested group 展平 + token refresh + per-doc 錯誤模型;Tier 1.5) | `進行中`(backend ✅ / 前端 5 surface ✅ / live blocked 真 tenant) | ①–③ spec amendment + 方案藍圖 + UI mockup ✅(見來源);④ ✅ **階段 1 backend 落地(`W100` closed,G-W100 PASS)**:F1 interface+capability / F2 Graph client(azure-identity+httpx,無新 dep)/ F3 connect·browse·list·fetch / F4 get_principals(transitiveMembers group 級+Anyone-drop+防爆量)/ F5 import service(per-doc 錯誤模型)/ F6 API route+RBAC+production adapter(doc ACL→既有 pipeline,**ingestion 核心零改動**)。**49 新測試 + RBAC 回歸綠**,ruff/mypy clean。commits `67f4f14`/`abfaf1e`/`bfa1d34`/`0499f2d`/`08ce773`/`ff87652`;⑤ **階段 1b 前端 IA 決定 ✅**(2026-06-30):ADR-0071(**Proposed** — 獨立頂層 Integrations 模組;用戶 AskUserQuestion 揀 landing+wizard 形態 + 命名 Integrations)+ mockup 配套改(加 `10-integrations-landing.html` + 4 surface shell 由 Knowledge 改 Integrations 歸屬);⑥ **階段 1b plan active**(`W101-integrations-import-ui`,2026-06-30 approve):ADR-0071 **Accepted** + 7 deliverable(F1 backend browse/list/resolve 端點 + import 個別 ref path / F2-F7 前端 5 surface H7 重現 + nav + API client);#2 credential 唯讀(H5 deviation 用戶確認);⑦ **W101 closed(G-W101 PASS,2026-06-30)**:F1-F7 全落 — backend 3 端點(`resolve-site`/`browse`/`documents`)+ import 個別 ref(`9f2818e`)+ 前端 5 surface H7(`d5dcfc7`/`5611f2e`/`9972a18`/`7545bde`);ingestion diff=零 + pytest 80 passed + tsc/eslint clean;**carry-over**:**live 驗證**(**runbook 可執行版已備** `docs/09-analysis/integration_layer_phase1_live_verification_runbook.md`,等真 tenant + `Sites.Selected`,blocked 外部)+ follow-up principal(org/public/external_group)+ H7 browser smoke(前端 step2-4 layout **已 mock demo 對齊驗證** 2026-07-01,真 live smoke 仍待真 tenant)+ 14 pre-existing frontend test 債(E 區) | ADR-0070(Accepted)/ `W100-integration-sharepoint-phase1/`(plan+progress)/ `docs/09-analysis/` 藍圖+deep-research ×2 / C17 / `integration-import/` mockup |

---

## ⚑ Pipeline 生產健壯性技術債(2026-07-06 pipeline review 識別 · B-11~B-17 已完成,剩 B-18/B-19 候選)

> 來源:[`../09-analysis/pipeline_review_20260706.md`](../09-analysis/pipeline_review_20260706.md)(RAG 查詢 + ingestion 代碼核對)。用戶 2026-07-06 同意立案處理**高(🔴)+ 中(🟠)級**風險(先備 `status: proposed` 文件,等指示才 code);低(🟡)級不在此批。
>
> **2026-07-06 已按推薦框架立案**(①只 Tier 1 緩解 `asyncio.to_thread`,完整佇列另作 Tier 2 候選 ②重疊項指向現有機制 ③每項獨立 folder;用戶立案框架問卷 3 題未答 → 用預設推進,**可調整**)。**B-11~B-17 已備 7 份立案文件**(4 BUG + 3 CH);B-18/B-19 指向現有機制不另開 folder。**B-11~B-17 已全部完成**(B-11~B-14/B-16/B-17 隨 PR #2 merged;B-15/CH-020 於 2026-07-08 完成 + ADR-0074 Accepted);**B-18/B-19 仍 `候選`**(指向現有 ADR-0039/0043,未開工)。

| ID | 風險(review 編號) | 級 | 狀態 | 立案 / 路徑 |
|---|---|---|---|---|
| **B-11** | ingest parse/chunk 同步阻塞事件迴圈(I-R1/I-R2,`asyncio.to_thread` 緩解) | 🔴 | `完成`(PR #2 merged) | [BUG-040](../03-implementation/bugs/BUG-040-ingest-sync-blocks-event-loop/report.md)(完整佇列=Tier 2 候選,另議) |
| **B-12** | 鄰居圖/概覽圖漏 ACL trim → 圖片洩漏(Q-R1) | 🔴 | `完成`(PR #2 merged) | [BUG-041](../03-implementation/bugs/BUG-041-neighbour-image-acl-trim-gap/report.md)(安全) |
| **B-13** | embedding 一次過整 doc 無分批 → 大 doc abort(I-R3) | 🟠 | `完成`(PR #2 merged) | [BUG-042](../03-implementation/bugs/BUG-042-embedding-no-subbatch-large-doc/report.md) |
| **B-14** | <1000 chunks/doc 假設 → delete/restamp 靜默漏尾(I-R7) | 🟠 | `完成`(PR #2 merged) | [BUG-043](../03-implementation/bugs/BUG-043-chunk-pagination-1000-cap/report.md) |
| **B-15** | Cohere 故障無熱切換 → 直接 502(Q-R3) | 🟠 | `完成`(2026-07-08) | [CH-020](../03-implementation/changes/CH-020-cohere-reranker-hot-fallback/spec.md) — ADR-0074 Accepted;`FallbackReranker` 自動熱降級 Azure semantic(選項 A);9 test 綠;生效需重啟 backend |
| **B-16** | ingest ACL fail-open 無告警(I-R4) | 🟠 | `完成`(PR #2 merged) | [CH-021](../03-implementation/changes/CH-021-ingest-acl-fail-open-alert/spec.md) |
| **B-17** | 串流路徑(chat 主路徑)無 CRAG(Q-R2) | 🟠 | `完成`(PR #2 merged,ADR-0073) | [CH-022](../03-implementation/changes/CH-022-streaming-crag-parity/spec.md)(方案 B 純後端信號) |
| **B-18** | 預設雙重 rerank 冗餘(Q-R4) | 🟠 | `候選` | → 推進 ADR-0039(已 Proposed);不另開 folder |
| **B-19** | KB reindex 非原子(I-R8) | 🟠 | `候選` | → 併 B-06 / ADR-0043(已有);不另開 folder |
| **B-21** | born-digital PDF 白行 Docling OCR → parse 慢 ~3x(+~60s 零得着;**2026-07-08 頁面測試發現**,非 2026-07-06 review) | 🟠 | `完成` | [BUG-044](../03-implementation/bugs/BUG-044-pdf-parser-redundant-ocr/report.md)(`do_ocr=False` 預設 + force_scan 保留 OCR;實測 87s→27s) |

---

## B — 已設計 / Accepted,用戶主動暫緩(等 driver,非技術阻塞)

| ID | 任務 | 狀態 | 解封條件 | 來源 |
|---|---|---|---|---|
| **B-02** | RBAC P5 implementation — auditor 唯讀稽核角色 + access-review report + re-certify | `defer` | 出現真實審計 / 合規 driver(Tier 1.5);用戶另批(2026-06-25 暫緩,F1 已還原) | ADR-0068(Accepted)/ `enterprise-rbac/TRACKER.md` M5 |
| **B-03** | `section_anchor_nearest` 全域 default flip — leaf 級圖步驟錨點由 preset-only 升全域 default | `defer` | 單獨拍板(類 ADR-0052)+ eval 背書;現只 preset(`P1_sop_imgdense`=nearest+cap8)+ UI,全域仍 OFF | ADR-0056 §Amendment / W98 / W99 |
| **B-08** | 整合層匯入 browse user-scoped 取捨(Copilot 式 delegated browse vs 現狀 app-only) | `defer` | 分析完成,建議 Option A(維持 app-only)+ D-1 審計切片;revisit trigger = 出現自助 / per-department 匯入需求,或審計方要求 browse 按操作者權限收斂(Option B/C 需 ADR + 改認證模型) | [`integration_import_browse_scope_analysis_20260701.md`](../09-analysis/integration_import_browse_scope_analysis_20260701.md) |
| **B-09** | SharePoint 連接改 UI 配置(credential 搬 `.env` → admin UI + Key Vault) | `完成` | 方向甲落地 **G-W102 gate PASS**(2026-07-01):ADR-0072 Accepted + `ProviderConfig.settings` generic 欄 + 新 `set-secret` 端點(用戶輸入→Key Vault,H5 不 log/回傳)+ 整合層 credential **managed > `.env` fallback**(零回歸)+ 前端 Settings→Connections SharePoint 卡。backend 65 passed / tsc+eslint+mypy(淨新增 0)clean。**carry-over**:live smoke 需重啟 backend + blocked 真 tenant(D4,同 B-01);多 named connection + cert 上載 = follow-up。per-site grant 仍 IT 步驟 | [ADR-0072](../adr/0072-sharepoint-managed-connection.md) · [W102](./W102-sharepoint-connection-config/) |
| **B-10** | PR 流程正式化 — solo self-merge SOP(階段 1)+ 分階段 `main` branch protection(階段 2)+ CODEOWNERS / PR template(階段 3,有協作者時) | 階段 1 `完成`(SOP 已建)/ 階段 2 `候選` | 階段 2 解封 = PR 流程跑順幾個 cycle 後,GitHub 開 `main` branch protection(禁直推 + require `backend-ci` pass + require PR);階段 3 = 有協作者時加 CODEOWNERS / required reviewers / `.github/PULL_REQUEST_TEMPLATE.md` | [`PR_WORKFLOW.md`](./PR_WORKFLOW.md) §7 |

---

## C — Blocked on 外部(企業 IT / 用戶決定)

| ID | 任務 | 狀態 | Blocker | 來源 |
|---|---|---|---|---|
| **B-04** | Production launch / Beta 25% rollout 啟動(Tier 1 上線最大關卡) | `blocked` | **Track A IT credential 落地**(Production launch gate ⏳) | DD-6 / `DEFERRED_REGISTER.md` / W16 F1-F4 |
| **B-05** | W87 OneDrive → 本地路徑遷移(2026-07-07 pivot 執行路徑 B;新路徑 `C:\Users\CLai03\ai-enterprise-knowledge-solution-project`,已逃出 OneDrive) | `進行中(F5 觀察)` | **F4 全棧 gate PASS 10/10**(2026-07-07 新 session:8 KB/3 conv/6 msg + azurite 827 圖 volume 無縫 + `/query` 引用+圖端到端 + 最長路徑 219 + api/venv 指新路徑);待 **F5 觀察 ≥3 天退役 OneDrive**(未過前保留舊副本) | `W87-onedrive-path-migration/progress.md` Day 2 |
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
| (W101 發現) | 14 個**既有** frontend test fail(kb config view:`kb-detail` / `kb-settings-tuning` / `kb-settings-reindex` / `chat-meta-row` render error;**非 W101 引入** — `git diff babccd8 HEAD -- frontend` 證 W101 零 touch 嗰啲 code;單跑穩定 14 fail/9 pass) | 對應 view 再動時順帶修 / 獨立 debt 清理(疑 kb config schema 演進後 test stale) |
| **B-20** | backend `ruff` lint 債 **68 項**(35 `E402` / 12 `UP017` / 7 `F401` / 6 `I001` / 4 `UP037` / 4 `B00x`;2026-07-07 對齊 **PR #1** 令 CI `Ruff lint` 首次真正當 gate 才浮現,**非本次 W87 遷移造成** — 遷移 commit `b6dcb0d` 純 docs)| **獨立分支 + PR**(勿混對齊 PR):`ruff check . --fix` 起手修 **29 個** auto-fixable + 逐個評估 35 `E402`(疑刻意 → `# noqa` 或改結構)+ 4 `B00x`;弄綠非快事故獨立一輪 |

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

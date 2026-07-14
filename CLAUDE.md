# CLAUDE.md — EKP Project Standing Instructions

> **Claude Code:呢份文件係你嘅 standing instructions。每次 session 開始必須先讀,然後再做任何嘢。**
> **本 instruction 採用 Strict Mode**:架構決定一旦 lock 就唔可以單方面改,凡涉及 architectural change 必須 stop and confirm。

---

## 0. Quick Identity Check(每 session 開始 30 秒讀)

| 項目 | Value |
|---|---|
| Project | **Enterprise Knowledge Platform (EKP)** — Tier 1 Foundation |
| First Use Case | Drive Project — Ricoh internal user manuals |
| Primary Spec | `docs/architecture.md` v6 frozen(v5 → v5.1 → v6 amendment W11 D2 cont per ADR-0014/0015 — UI Tier 1 expansion 9 views + hybrid auth model;§3.4 + §3.7 inline-tagged via ADR-0022/0023 W17,doc version held) |
| Phase | Tier 1 Foundation — 原 spec 12-week(POC 6w → Beta 4w → Rollout 2w)實際 trajectory:W1–W11 base + **W12–W15 UI sprint cycle pivot**(v5.1→v6 amendment)+ W17 beta hardening + W18 unified application shell IA。**W18 後 W19+ rolling JIT 持續至 W101**(最近 closed = W101 integrations-import-ui,2026-06-30)— 主線 image-recall(W59-68)+ ADR-0056 per-KB config vision(W72-85)+ enterprise RBAC track(W88-95)+ 完整度 eval gate(W96-97)+ 圖錨 amendment(W98-99)+ **統一整合層(ADR-0070)階段 1 SharePoint 按需匯入(W100 backend + W101 前端,ADR-0071)**。W16 partial 待 Track A IT cred。逐 phase timeline 見 `docs/12-ai-assistant/01-prompts/01-session-start.md` §10 |
| Strict Mode | **ON** — see §5 Hard Constraints |
| Behavioral Baseline | **§1(Karpathy guidelines)** — universal coding mindset,適用於所有 code change |
| Decision Owner(architecture) | Chris(技術 Lead) |
| Decision Owner(scope / business) | Stakeholder(via decision-form.md) |

---

## 1. Behavioral Baseline(Karpathy Guidelines — universal)

> **Source**: `andrej-karpathy-skills` plugin(`karpathy-guidelines`,`alwaysApply: true`)
> **適用範圍**:**所有** code change、review、refactor —— 與 §2–§14 嘅 project-specific rule 並行,優先級僅次於 §5 Hard Constraints。
> **Tradeoff**:呢套 guideline bias toward caution over speed。Trivial task 可以用 judgment,但 non-trivial task 必須跟。

### 1.1 Think Before Coding —— 思考先,寫 code 後

**核心**:Don't assume. Don't hide confusion. Surface tradeoffs.

開始實作之前:
- 把 assumption **明確講出嚟**;唔肯定就問,唔好估
- 如果有多種詮釋,**全部 present**,唔好默默揀一個
- 如果有更簡單做法,**講出嚟**;有需要就 push back
- 唔清楚就 stop,**講明邊度唔清楚**,然後問

呢條同 §13 "When in doubt → ask, don't guess" 互相強化。

### 1.2 Simplicity First —— 最少嘅 code 解決問題

**核心**:Minimum code that solves the problem. Nothing speculative.

- 唔加未要求嘅 feature
- 唔為 single-use code 做 abstraction
- 唔加未 request 嘅 "flexibility" / "configurability"
- 唔處理冇可能發生嘅 error scenario
- 寫咗 200 行但其實 50 行夠 → **重寫**

自我檢查:「senior engineer 會話呢段 over-engineered 嗎?」答 yes 就簡化。

對 EKP 嘅意義:Tier 1 階段 simplicity wins(已喺 §13 寫明,呢條係執行細則)。

### 1.3 Surgical Changes —— 精準改動,只清自己嘅 mess

**核心**:Touch only what you must. Clean up only your own mess.

改 existing code 時:
- **唔好**「順手」改 adjacent code、comment、formatting
- **唔好** refactor 冇 break 嘅嘢
- **Match existing style**,即使你會 prefer 另一種寫法
- 見到無關嘅 dead code → **mention,but 唔好刪**

改動製造嘅 orphan(import / variable / function 因你嘅改動而 unused):
- **要刪**(你製造嘅 mess 自己清)
- **唔好** 刪 pre-existing dead code,除非用戶要求

驗證標準:**每一行改動都要可以 trace 返用戶嘅 request**。

對 EKP 嘅意義:強化 §4.3 "One feature per PR" + §4.4 "Files Claude Code 絕不 touch" —— 呢條係 mindset,§4 係硬規則。

### 1.4 Goal-Driven Execution —— 定義成功標準,loop 到 verify 為止

**核心**:Define success criteria. Loop until verified.

把 task 轉做 verifiable goal:
- "Add validation" → "寫 test for invalid input,然後 make them pass"
- "Fix the bug" → "寫 test reproduce 個 bug,然後 make it pass"
- "Refactor X" → "Refactor 前後 test 都 pass"

Multi-step task 要先講 plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

**Strong success criteria** 等你可以獨立 loop;**weak criteria**(如「make it work」)會逼用戶不斷 clarify。

對 EKP 嘅意義:同 §12 Self-Verification checklist 互補 —— §12 係 task done 嘅 gate,§1.4 係 task start 嘅 framing。

---

**呢套 guideline 生效嘅 signal**:
- Diff 入面 unnecessary change 變少
- 因 over-engineering 而要重寫嘅情況變少
- Clarifying question 出現喺 implementation **之前**,而唔係 mistake 之後

---

## 2. Document Routing(when to read what)

**呢份 CLAUDE.md 唔重複任何 spec 內容**。當你需要做嘢,跟以下 routing 去搵 source of truth:

| 情況 | 必讀文件 | 補充 |
|---|---|---|
| **想知有咩工作 pending / 揀下一個 task 去做** | [`docs/01-planning/BACKLOG.md`](./docs/01-planning/BACKLOG.md)(中央 backlog dashboard) | 全部 pending / 候選 / blocked / defer 一覽 + 狀態;細節 link ADR / `DEFERRED_REGISTER.md` / `enterprise-rbac/TRACKER.md` / phase folder。同步係 binding(§10 R7) |
| **Multi-day phase / sprint work**(任何超 single session implementation) | [`docs/01-planning/PROCESS.md §2`](./docs/01-planning/PROCESS.md) + active phase folder | Per phase plan / checklist / progress — 詳見 §10 |
| **Change to existing feature**(modify behavior, < 3 days) | [`docs/01-planning/PROCESS.md §3`](./docs/01-planning/PROCESS.md) + new instance `docs/03-implementation/changes/CH-{NNN}-{kebab}/` | Pre-doc:**spec.md**(approved by user)→ derive checklist + progress;AI auto-classify per PROCESS.md §1 |
| **Bug-fix**(fix incorrect / broken / regressed behavior) | [`docs/01-planning/PROCESS.md §4`](./docs/01-planning/PROCESS.md) + new instance `docs/03-implementation/bugs/BUG-{NNN}-{kebab}/` | Pre-doc:**report.md**(severity Sev1-Sev4)→ derive checklist + progress;Sev1/Sev2 mandatory postmortem |
| **改 / 新加 component**(明確涉及 EKP 13 modules 之一,C01–C13)| [`docs/02-architecture/COMPONENT_CATALOG.md`](./docs/02-architecture/COMPONENT_CATALOG.md) + 對應 `components/Cn-{kebab}.md`(若已存在)| 識別 component → spec ref + dep + tech + status,再跳去 architecture.md 對應 section 落實作 |
| **Risk-related decision / mitigation update** | [`docs/01-planning/RISK_REGISTER.md`](./docs/01-planning/RISK_REGISTER.md)(living)+ `docs/architecture.md §8`(frozen baseline)| 新 risk / status update 入 living register,§8 不動 |
| Setup local dev environment | `docs/setup.md` | 包括 Azurite、Langfuse、docker-compose、env vars |
| 寫 / 改 backend feature | `docs/architecture.md` §3 + §4 | RAG core + application architecture |
| 寫 / 改 frontend feature(page-level) | **`references/design-mockups/DESIGN_README.md` + `PAGE_INVENTORY.md` FIRST**(high-fidelity click-through HTML prototype + per-route Cn mapping + Tier 1/2 boundary)→ `docs/architecture.md` §5 + Dify ref(see §7) | UI work first stop:open `references/design-mockups/EKP Platform.html` 喺 browser、click 入要實作嘅頁、inspect `ekp-page-*.jsx`;然後再睇 spec §5。Prototype 對 spec 有 3 處 design-stage expansion(KB Detail 5→8 tabs / Settings v1→6 tabs / `/users` NET NEW Tier 1.5)— 屬 proposal,implementation trigger H1 ADR(per §5.1)|
| 揾 class catalog / layout pattern / composite pattern recipe(primitive-level)| **[`references/design-mockups/DESIGN_SYSTEM.md`](./references/design-mockups/DESIGN_SYSTEM.md)** — dev API reference(tokens / 13 primitives index / layout patterns / composite patterns 含 PopMenu viewport-anchored / Stepper / OptionRow / DisabledAffordance / Modal / sync protocol / drift incident log)| §0 quick reference card 一頁睇晒所有 class combo;唔好 grep `styles.css` 再 re-derive。寫 component 之前先睇 §2-§4,寫嘅時候 cross-ref §5 color semantics + §6 interaction states |
| 修 design tokens / mockup CSS class / dark mode override | **[`references/design-mockups/DESIGN_SYSTEM.md` §7 sync protocol](./references/design-mockups/DESIGN_SYSTEM.md)** — 4-layer chain `styles.css → styles-mockup.css → globals.css → tokens.ts` | Token change 跟 §7.1 七步;class change 跟 §7.2 五步;改完 append §7.3 drift incident log;季度跑 §8 health check |
| 加 / 改 API endpoint | `docs/api-contract.md`(W2 末 ready) | 在此之前用 `docs/architecture.md` §4.4 + §4.5 |
| 加 vendor / 換 component | **STOP** — 必須先確認(see §5.2 Hard Constraint H2) | 寫 ADR `docs/adr/`(W2 末 framework ready) |
| 改架構 / 違反 §3 / §4 設計 | **STOP** — 必須先確認(see §5.1 Hard Constraint H1) | 同 |
| 處理 Tango.us / 多 format ingestion | `docs/architecture.md` §3.3 | 注:source 係 Word/PDF/PPT,**不是** Tango |
| Chunking 邏輯 | `docs/architecture.md` §3.3 + §3.5 | layout-aware,not character-based |
| 寫 eval / test | `docs/eval-methodology.md` + `docs/eval-set-v0.yaml`(W1 ready) | RAGAs + 30–50 條 ground truth |
| 涉及 Dify reference | `references/REFERENCE_USAGE.md`(W1 Day 1 setup) | 嚴禁 copy-paste,只可 layout 借鑒 |
| Stakeholder-facing 變動 | `docs/decision-form.md`(W1 ready) | 確認 23 條 OQ status(Q22 NEW W12 D1 per ADR-0014;Q23 Resolved 2026-07-14 Multi-language promote approved per ADR-0075/B-25,implement 待 phase plan) |
| **用戶操作 / 配置 / 調試疑問**(UI 點用、旋鈕做咩、出廠值、benchmark 對照、故障排查)| [`docs/08-user-guide/`](./docs/08-user-guide/README.md)(8 份,2026-06-12 W69-era 快照)| 答用戶操作問題 first stop,唔好憑記憶重新推導旋鈕值;**ADR 改 default 時必須同步其 `03-configuration-reference.md` + `06-benchmarks-and-metrics.md`**(維護規則喺其 README)|
| **Enterprise 權限(RBAC)擴充工作** | [`docs/01-planning/enterprise-rbac/TRACKER.md`](./docs/01-planning/enterprise-rbac/TRACKER.md)(追蹤入口)+ `enterprise-rbac/FINDINGS.md`(單一事實來源)| 2026-06-23 啟動,**做到 W95**:P0 地基 → P2 檢索層文件 ACL → P3 文件級+群組繼承(ADR-0066/0067 Accepted)→ P5 治理設計(ADR-0068 Accepted,**impl 2026-06-25 暫緩等審計 driver,Tier 1.5**);跨 Tier 邊界需 ADR + Chris approve(H1/H4) |
| 評估 GraphRAG / multi-agent / multi-tenancy | **STOP** — 呢啲係 Tier 2,Tier 1 唔做 | See `docs/architecture.md` §11 trigger matrix |
| **生成 pptx / docx / xlsx / pdf 文件**(把 session 內容 / 資料變成 Office / PDF 交付物,同 Claude.ai 網頁版效果)| 透過 Skill tool 用 `document-skills:{pptx\|docx\|xlsx\|pdf}`(Anthropic 官方 plugin,2026-07-04 已裝,同 Claude.ai 同源)| 本機工具鏈已配置(`pptxgenjs` / `docx-js` / `markitdown` / LibreOffice / Poppler / tesseract);**Windows 專屬坑**(User PATH 加咗要重開 session 生效 / 公司 MITM 代理擋大 binary + winget 憑證 / scripted conversion 用 `soffice.com` 非 `soffice.exe`)+ 引擎機制見 memory `project_document_skills_toolchain` |

**Default behavior**:如果你唔確定一個 task 屬邊個 doc 範圍,**ask before guessing**。

---

## 3. Coding Conventions

### 3.1 Backend(Python)

- **Python 3.12+** required
- **Type hints required everywhere**(`mypy --strict` clean)
- **Async by default**(FastAPI、httpx、Azure SDK 全部用 async client)
- **Pydantic v2** for all schemas(see `backend/api/schemas/`)
- **Logging via structlog**(JSON output for Langfuse correlation)
- **Imports**:absolute imports only,no relative imports across modules
- **Function length**:soft cap 50 行,超過要拆
- **Test framework**:pytest + pytest-asyncio
- **Coverage target**:critical pipeline modules ≥ 80%(`backend/pipeline/`、`backend/retrieval/`、`backend/ingestion/`)
- **Linter**:ruff(config in `pyproject.toml`)
- **Formatter**:ruff format

### 3.2 Frontend(TypeScript / Next.js 14)

- **TypeScript strict mode**(no `any`,no `@ts-ignore` 除非有 comment 解釋)
- **App Router only**,no Pages Router
- **Server Components by default**;Client Components 必須有 `"use client"` directive + 解釋 comment
- **CSS-first pivot baseline**(W22 F1 mid-session pivot landed `styles-mockup.css` 1073→1048 lines verbatim adoption from `references/design-mockups/styles.css`):mockup CSS classes drive visual layer baseline(`.btn .card .field .input .label .hint .seg .badge .switch .tabs .table .banner .progress .status-dot .avatar` etc.);**shadcn/ui primitives** consumed only where Radix a11y benefits(Dialog / DropdownMenu / Sheet / Toast / Tabs etc.);**Tailwind utility classes** 限 one-off layout adjustments + responsive breakpoints。「shadcn/ui only」+「Tailwind only」early framing under-represented actual approach;the CSS-first baseline 係 W22 implementation reality(per W22 D1 process meta evidence + `feedback_design_fidelity.md` 5-pattern catalog)
- **Design tokens via `frontend/lib/theming/tokens.ts`** — 絕對唔可以 hardcode 顏色 / spacing
- **修 design tokens / mockup CSS / dark mode 一定要跟 4-layer sync protocol** — `styles.css(canonical)→ styles-mockup.css(verbatim copy)→ globals.css(Tailwind bridge)→ tokens.ts(TS mirror)`;procedure 見 [`references/design-mockups/DESIGN_SYSTEM.md` §7](./references/design-mockups/DESIGN_SYSTEM.md);silent drift 已發生過(W22 F1 `--popover` dark 0.20 vs 0.22 incident),所以呢條 mandatory
- **State management**:React state for local;Zustand for cross-component;**no Redux**
- **Data fetching**:Vercel AI SDK 嘅 `useChat` for streaming;TanStack Query for non-streaming
- **Test framework**:Vitest + React Testing Library
- **Linter**:ESLint(Next.js default + Tailwind plugin)
- **Formatter**:Prettier

#### 3.2.1 Design Fidelity Rule(`references/design-mockups/` 100% reproduction)

> **`references/design-mockups/` 係前端視覺 + 互動嘅 canonical spec。實作必須 100% 重現 mockup,唔可以「大概模仿」。**
>
> **⚠️ 呢條規則 binding level = Hard Constraint H7**(per [§5.7](#57-h7--design-fidelity-constraint),同 H1-H6 同層)。Violate = broken project + STOP+ask trigger。Detail checklist 喺本節;trigger 條件 + Required behavior 喺 §5.7。

前端設計係本項目嘅 critical surface — implementation 對 mockup 必須做到 **完整重現**(complete reproduction),不是 approximate / similar / inspired-by。具體規則:

- **shadcn/ui 規限 *技術*,唔規限 *fidelity***:用 shadcn primitives + Tailwind tokens 係 H2 要求(`references/design-mockups/` 嘅 stripped components 不可 verbatim copy),**但 visual output 必須 pixel-faithful match mockup**。換句話講:用 `<Button>` 唔等於可以改 size / padding / variant —— 要對齊 mockup 入面嗰個 button 嘅實際樣貌。
- **揾 class combo / pattern recipe 之前 first stop = [`DESIGN_SYSTEM.md`](./references/design-mockups/DESIGN_SYSTEM.md)**(dev API reference,W22 F5b session 整合 landed):§0 quick reference card / §2 13-primitive index(`.btn` / `.card` / `.field` / `.input` / `.label` / `.hint` / `.badge` / `.switch` / `.seg` / `.tabs` / `.table` / `.banner` / `.progress` / `.status-dot` / `.avatar` / utility classes)/ §3 layout patterns(`.content` shell / `.page-header` / `.stat-grid` / `.kb-grid` / `.activity-list` / `.app` AppShell)/ §4 composite patterns(**PopMenu viewport-anchored gutter chain** + anti-pattern「DO NOT use Radix DropdownMenu」/ **Stepper 28px circle** wizard / **OptionRow** toggle-row / **DisabledAffordance** Tier 2 boundary / **Modal** / **Chunk inspector**)/ §5 color semantics / §6 interaction state convention(data-active / data-on / data-popmenu-trigger)。**唔好** 直接 grep `styles.css` 或 `ekp-shell.jsx` re-derive — 已 documented 嘅 pattern 重複推導等於 violate Karpathy §1.1 think-before-coding。Mockup spec 同 DESIGN_SYSTEM.md 詮釋衝突時 → mockup spec wins(DESIGN_SYSTEM.md 係 dev convenience layer)。
- **必須逐項對齊**:layout 結構(`<div>` 階層 / flex / grid)、spacing(margin / padding / gap)、typography(`text-*` size / weight / leading)、color tokens(用 mockup 用嘅 token,唔可以「換相近顏色」)、interaction states(hover / focus / active / disabled / loading / empty / error)、responsive breakpoints(sm / md / lg / xl 行為)、a11y affordances(aria-* / role / focus-ring)
- **唔肯定就開 mockup 對住做**:寫 / 改前端 page 之前 + 寫到一半 + 寫完之前,**都應該打開** `references/design-mockups/EKP Platform.html` 嘅對應頁面(URL hash 例:`#kb-detail/drive-manuals`)、inspect 對應 `ekp-page-*.jsx`,逐個 section 對齊。係 routing first-stop(§2)嘅延伸 — 唔係一次性 reference。
- **Mockup detail 不清晰 / 唔可以用 shadcn 重現** → **STOP and ask**,**絕對唔可以自行 approximate**。例:mockup 有一個 custom popover 動效 shadcn 冇 primitive —— 唔好「用 dropdown 代替算」,要 surface 個 gap 等用戶決定(加 primitive / 寫 vanilla / 改 mockup)。
- **Design-stage expansion 例外**:DESIGN_README 標明嘅 3 處 design-stage expansion(KB Detail 5→8 tabs / Settings v1→6 tabs / `/users` Tier 1.5)係 *proposal*,implementation 入 H1 ADR 流程(§5.1);ADR 確認 *scope* 之後,*visual fidelity* 仍然受呢條規則約束。
- **完成前 self-verify**:每個 frontend task done 之前,§12 self-verification checklist 入面嘅「fidelity check」必須過(逐個 element 對齊 mockup;唔啱就 `🚧 deferred` + 記在 progress.md;唔可以靜靜噉差別交)。

**Why**:前端係 user-facing surface,設計細節影響 stakeholder 對產品成熟度嘅判斷。「大概模仿」會累積成 visual drift,W12-W18 UI sprint cycle 已經花咗 4 phase 校正 visual identity(per ADR-0015 + W12 D2 tokens lock)。Mockup 係 single source of truth,re-introduce drift 就係退步。

### 3.3 共通

- **Naming**:
  - Files:`snake_case.py`、`kebab-case.tsx`
  - Variables / functions:`snake_case`(Python)、`camelCase`(TS)
  - Classes / Components:`PascalCase`
  - Constants:`UPPER_SNAKE`
  - Database / Azure Search field:`snake_case`(全小寫)
- **Comments**:解釋 **why**,唔係 **what**(code 自己應該講 what)
- **TODO comments format**:`# TODO(<owner>): <description> [<issue-id>]`
- **絕不 commit**:secret、API key、PII、`.env` 內容、`references/dify/` 任何 file

---

## 4. Git & Workflow Conventions

### 4.1 Branch naming

```
main                          ← protected, 永遠 deployable
feat/<area>-<short-desc>      ← e.g. feat/ingestion-docx-parser
fix/<area>-<short-desc>       ← e.g. fix/retrieval-rrf-edge-case
chore/<short-desc>            ← e.g. chore/update-deps
docs/<short-desc>             ← e.g. docs/api-contract-v1
adr/<adr-number>-<short>      ← e.g. adr/0012-langgraph-deferred
```

### 4.2 Commit message(Conventional Commits)

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:`feat` / `fix` / `chore` / `docs` / `refactor` / `test` / `perf` / `style`
Scope:`ingestion` / `retrieval` / `generation` / `pipeline` / `kb` / `eval` / `api` / `frontend` / `infra`

Example:
```
feat(retrieval): add Cohere Rerank v3.5 client

Wire Cohere via Azure Marketplace billing.
Fallback to Azure built-in semantic ranker on outage.

Refs: docs/architecture.md §3.2
```

### 4.3 PR Rules

- **One feature per PR**,no kitchen-sink PRs
- **PR description 必須**:link to spec section、list test scenario、include screenshots(frontend)
- **Reference Dify**(若有):必須在 PR comment 標 `Reference: dify/<path>`(see §7)
- **Pre-merge checklist**:tests pass、coverage 不降、no linter warning、ADR updated(若 architecture change)

### 4.4 Files & folders Claude Code **絕不** touch

- `.git/`
- `references/dify/`(read-only,license risk)
- `.env`、`.env.local`、any file with credentials
- `infrastructure/secrets/`(若存在)
- `docs/architecture.md` 嘅 §1–§14(content lock,只有 stakeholder approve 後 increment version)

---

## 5. Hard Constraints(Strict Mode)

呢啲 constraint **violate 即係 broken project**。Claude Code 遇到以下情況**必須 STOP and ask**:

### 5.1 H1 — Architectural Change Constraint

**「Architectural change」嘅定義**:任何符合以下其一嘅變動 ——

- 加 / 改 / 刪 `docs/architecture.md` §3(RAG Core)或 §4(Application Architecture)入面提到嘅 component
- 改 vendor / service(e.g. Azure AI Search → Pinecone、Cohere → Voyage 不在 W4 shootout 範圍)
- 改 storage layout(e.g. blob path convention、search index schema)
- 改 multi-KB architecture(e.g. KB-id namespacing rule)
- 改 8 個視 view 嘅其中任何一個嘅 layout philosophy(可以 polish,但唔可以 redesign)
- 加 Tier 2 feature(GraphRAG、multi-agent、multi-tenancy、workflow)入 Tier 1 codebase

**Required behavior**:
1. **STOP** 寫 code
2. 喺 chat 講明:
   - 你想做咩 architectural change
   - 為何 v6 spec 唔啱
   - Proposed 替代方案
3. 等 user 回應「approved + write ADR」先繼續
4. 寫新 ADR 入 `docs/adr/`(format see §6)

**唔屬於 architectural change**(可以自行做):
- Bug fix
- Refactor 內部實作而冇改 interface
- 加 internal helper function
- UI polish(spacing、typography、micro-interaction)
- 加 test
- 加 logging / observability

### 5.2 H2 — Vendor / Dependency Constraint

**Tier 1 嘅 vendor list 已 lock**(see `docs/architecture.md` §3.2 + §14):

| Layer | 已 lock vendor |
|---|---|
| Vector + BM25 | Azure AI Search Standard S1 |
| Embedding | Azure OpenAI text-embedding-3-large |
| Reranker(baseline) | Cohere Rerank v4.0-pro(W6 production lock per ADR-0012 + Q21 Resolved;v3.5 W3 baseline → v4.0-pro same-vendor upgrade;Voyage / ZeroEntropy DROPPED Tier 1) |
| LLM(synthesis) | Azure OpenAI GPT-5.5 |
| LLM(judge) | Azure OpenAI GPT-5.4-mini / GPT-5.5 Pro |
| Document parsing | Docling + python-pptx |
| Image storage | Azure Blob(local: Azurite) |
| Observability | Langfuse |
| Eval | RAGAs |
| Frontend | Next.js 14 + shadcn/ui + Tailwind[^design-system-chain] |
| Backend | FastAPI + uvicorn |
| Persistent storage | Postgres 16 via `psycopg>=3.2`(KB metadata + users/sessions backing per ADR-0023 W17 F1;in-memory fallback when `DATABASE_URL` unset) |
| Email verification | Azure Communication Services Email(per ADR-0014 + Q22 Resolved;`ConsoleEmailProvider` stub when `feature_email_mock=true`) |

**加新 dependency 嘅唯一合法路徑**:
1. STOP and ask
2. 解釋為何現有 stack 唔夠
3. 等 approval
4. 寫 ADR documenting decision

**例外**(可以自行加):
- Pure utility library(e.g. `tenacity` for retry,`structlog` for logging)
- Type stub package(`types-*`)
- Dev dependency(test、linter、formatter)

[^design-system-chain]: **Frontend design system source-of-truth chain** documented in [`references/design-mockups/DESIGN_SYSTEM.md` §7](./references/design-mockups/DESIGN_SYSTEM.md):`styles.css(canonical)→ styles-mockup.css(verbatim copy)→ globals.css(Tailwind bridge)→ tokens.ts(TS mirror)`。任何 layer 修改必須跟 §7.1(token change 7-step)/ §7.2(class change 5-step)/ §7.3(quarterly drift detection + incident log)procedure;silent drift 已發生過(W22 F1 `--popover` dark 0.20 vs 0.22 incident `a385180`),所以 mandatory。

### 5.3 H3 — Dify Reference Constraint

`references/dify/` 係 **read-only reference**,唔係 dependency。

**絕對唔可以做**:
- Copy-paste 任何 Dify code 入 EKP codebase
- Import / require 任何 Dify package
- Fork Dify 或 vendor 一個 Dify instance
- Replicate Dify branding(logo、primary color、marketing copy)

**可以做**:
- Read Dify source 學 layout、interaction、component composition
- Reference Dify API design 作為 endpoint pattern inspiration
- 喺 PR comment 標 `Reference: dify/web/app/components/datasets/...`

詳見 `references/REFERENCE_USAGE.md`(W1 Day 1 setup)。

### 5.4 H4 — Tier Boundary Constraint

**Tier 1 implementation 唔可以包含 Tier 2 feature**,即使你覺得「順手做埋」。

Tier 2 list(`docs/architecture.md` §11):
- GraphRAG / Knowledge Graph
- L4+ multi-agent orchestration
- Workflow / plugin builder
- Multi-tenancy
- Multi-modal retrieval(B 類純圖片搜索)
- Multi-language — **JP UI + content/RAG 翻譯**(en/zh UI chrome 已 promote Tier 1,W103 per ADR-0075;architecture.md §11.1 inline-tagged 2026-07-14)
- Auto-sync from external source
- Custom LLM fine-tuning

**「Tier 2 friendly」係要求**:Tier 1 architecture 必須 modular、extensible、MCP-ready,等 Tier 2 將來可以加。但**任何 Tier 2 feature 嘅 implementation 都係 out of Tier 1 scope**。

### 5.5 H5 — Security & Privacy Constraint

- **絕不 log**:full LLM prompts containing user query payload to plaintext file(只 log to Langfuse,encrypted at rest)
- **絕不 commit**:Azure connection string、API key、Cohere key、Microsoft Entra ID secret
- **絕不 hard-code**:tenant ID、subscription ID、resource name(都 from env var)
- **Secrets management**:POC 用 `.env`(gitignored);Beta+ 用 Azure Key Vault
- **PII handling**:Drive Project 假設無 PII;若 future KB 含 PII,trigger Tier 2 review

### 5.6 H6 — Test Coverage Constraint

以下 module 寫 code **必須同步寫 test**:
- `backend/ingestion/parsers/`
- `backend/ingestion/chunker/`
- `backend/retrieval/`
- `backend/pipeline/query_pipeline.py`
- `backend/pipeline/crag_loop.py`
- `backend/api/routes/query.py`
- `backend/eval/`

UI component test 為 nice-to-have(視 sprint 進度),其他 backend 鼓勵但唔強制。

### 5.7 H7 — Design Fidelity Constraint

**`references/design-mockups/` 係前端視覺 + 互動嘅 canonical spec**(EKP 自有 high-fidelity HTML prototype,**唔係**第三方 reference)。前端 implementation **必須 100% 完整地重現 mockup 效果**,**唔可以「大概模仿」**(approximate / similar / inspired-by 都唔得)。

**H7 trigger 條件**(任何一條符合就 trigger STOP and ask):

- 寫 / 改前端 page、component、layout 嘅 implementation 同對應 mockup(`references/design-mockups/EKP Platform.html#<route>` + `ekp-page-*.jsx`)嘅 **layout 結構 / spacing / typography / color tokens / interaction states / responsive breakpoints / a11y affordances** 任何一項唔對齊
- Mockup detail 不清晰(無法判斷正確視覺 / 互動)
- shadcn/ui 冇對應 primitive 重現 mockup(例:custom popover 動效冇 primitive — 唔可以「用 dropdown 算」)
- Layout philosophy 偏離 mockup(可以 micro-polish spacing / typography,但唔可以 redesign — 同 §5.1 H1「8 view layout philosophy」條件互通)
- Design-stage expansion 例外(DESIGN_README 3 處標明:KB Detail 5→8 tabs / Settings v1→6 tabs / `/users` NET NEW Tier 1.5)以外嘅任何 mockup 偏離

**Required behavior**:
1. **STOP** 寫 code
2. 喺 chat 講明:
   - 你想做咩 deviation 或 unclear 喺邊 mockup spot
   - Mockup 對應位置(URL hash + `ekp-page-*.jsx` line ref)
   - Proposed 處理方案(加 primitive / 寫 vanilla / 改 mockup / `🚧 deferred` + reason)
3. 等 user 決定 — **絕對唔可以自行 approximate**
4. 處理方案如涉及 design-stage expansion ADR-route per §5.1 H1

**唔屬於 H7 trigger**(可以自行做):
- Pure backend / API / schema change(無前端 mockup 對應)
- 加 test / logging / observability(對 visual 無影響)
- Refactor 內部實作(visual output identical pre/post)
- Design-stage expansion 3 處 proposal(per ADR-route — scope confirm 之後仍受 H7 約束)
- 修正 visual drift bug(把 implementation **更貼近** mockup,reverse direction)

**Cross-ref**:detail per [§3.2.1 Design Fidelity Rule](#321-design-fidelity-ruledesign-mockups100-reproduction) 嘅 7-item checklist;self-verify per §12 fidelity check。

**Why**:前端係 user-facing surface,設計細節影響 stakeholder 對產品成熟度嘅判斷。W12-W18 UI sprint cycle 已經花咗 4 phase 校正 visual identity(per ADR-0015 + W12 D2 tokens lock + ADR-0024 W18 IA flip + W19/W20 design-mockups landed)。Mockup 係 single source of truth;re-introduce drift = 退步。User 2026-05-17 explicit framing:「**前端頁面的設計是非常重要的**」+「**100%完整地把mockup 的效果重現出來,而不是大概地模仿**」+「**必須要留意和遵守的規則**」→ binding level promoted 到 H7 hard constraint(同 H1-H6 同層)。

---

## 🚫 工具使用強制紀律（🔴 最高級別 — 零容忍・無例外）

> **來源** merge 事件——大量用 bash `echo`/`cat`/`grep` 拼裝命令 + `{ }` group 重定向,造成嚴重輸出污染(檔案內容重複、亂碼、語意注入),險些 commit 進損壞內容。

**絕對禁止(無任何例外,違反即停手改正)**:

1. ❌ 用 bash/shell 跑 `cat` / `head` / `tail` / `grep` / `find` / `sed` / `awk` 讀檔或搜尋 → **一律改用 Read / Grep / Glob 工具**
2. ❌ 用 `echo` 拼裝輸出、`{ }` group 重定向、多命令混合重定向 → **只用單一命令直接重定向** `cmd > file`,再用 **Read 工具**讀
3. ❌ 靠 bash 即時 stdout 判斷結果 → **寫檔後用 Read 工具讀**

**bash/shell 唯一正當用途**:執行**無專用工具替代**的操作(git、npm、其他 CLI),輸出到檔案時**只用單一命令直接重定向、絕不混 echo**。此為正當用途,非漏洞——禁的是「有替代卻用 bash」,不是「用 bash」本身。

**這不是「避免」,是「禁止」。** 本區優先級屬 binding-strict — 等同 §5 H1–H7 Hard Constraints 與 §11 中文紀律級別(訊息 / 檔案結構紀律同源);違反 = broken-workflow signal,即停手改正。

---

## 6. Architecture Decision Record (ADR) Format

任何違反 H1 / H2 嘅變動,approval 後必須寫 ADR。Format:

```markdown
# ADR-NNNN: <Title>

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded by ADR-MMMM
**Approver**: <Name>

## Context
咩 trigger 呢個決定?咩 constraint?

## Decision
具體做咩?

## Alternatives Considered
睇過咩其他選擇?點解 reject?

## Consequences
- Positive: ...
- Negative: ...
- Neutral: ...

## References
- spec section
- external link
- previous ADR(若 supersede)
```

ADR 文件位置:`docs/adr/NNNN-short-title.md`,NNNN 係 4-digit zero-padded sequential。Index 喺 `docs/adr/README.md`。

頭 11 個 ADR(0001-0011)由 v5 §13.0-§13.11 Decision Log promote 而來,**W2 D5 cont 2026-05-04 batch 創建完成**(§13.10 "Other v3 inherits" 屬 meta-rollup,不單獨 promote)。**新 ADR 由 NNNN=0012 開始**。

---

## 7. Dify Reference Workflow(critical 重複強調)

> **Disambiguation — `references/` 兩個子目錄不同性質**:
> - **`references/dify/`** — **第三方 read-only reference**(license risk;H3 strict no-copy)— 本節 cover
> - **`references/design-mockups/`** — **EKP 自有 high-fidelity HTML prototype**(2026-05-16 landed;design spec for `frontend/`)— 唔受 H3 限制,但**唔可以**直接 copy `ekp-page-*.jsx` stripped components 入 `frontend/`,必須用 shadcn/ui + Tailwind 重寫(per CLAUDE.md §3.2 H2)。入口:`references/design-mockups/DESIGN_README.md` + `PAGE_INVENTORY.md`。Frontend work 之前 **first stop**(per §2 routing)

**Setup**(W1 Day 1):
```bash
mkdir -p references && cd references
git clone --depth 1 https://github.com/langgenius/dify.git
cd dify && git log -1 > ../DIFY_PINNED_COMMIT.txt
```

`.gitignore` 要 include:
```
references/dify/
references/DIFY_PINNED_COMMIT.txt
```

**Daily usage**:
- 寫一個 EKP component 之前,**可以**去 `references/dify/web/` 搵類似 component 學 layout
- **必須**用 EKP 自己嘅 design tokens(`frontend/lib/theming/tokens.ts`),唔可以抄 Dify 顏色
- 喺 PR comment 標明 reference path:`Reference: dify/web/app/components/datasets/documents/list.tsx (layout pattern only)`
- **絕對唔可以**:`cp references/dify/...` to EKP codebase

詳細 policy 見 `references/REFERENCE_USAGE.md`。

---

## 8. Open Questions(影響 Claude Code 決策)

呢 **23 條 OQ**(`docs/architecture.md` §10、`docs/decision-form.md`;Q22 NEW per ADR-0014 hybrid auth W12 D1 — Email Verification Service vendor = ACS;Q23 Resolved 2026-07-14 per ADR-0075/B-25 — Multi-language en/zh Tier 2→Tier 1 promote approved 雙半,implement 待 i18n phase plan)嘅 status 影響你嘅 default behavior:

- 任何 OQ status = **「Open」** → 用 spec 入面標明嘅 default value 繼續做,但**喺 commit message 標**:`Note: depends on OQ-Q<N> default`
- 任何 OQ status = **「Resolved」** → 直接用 resolved value,唔需要 note
- 任何 OQ status = **「Blocked」** → STOP 對應 work item,ask user

**最 critical 嘅 W1 必 resolve OQ**:Q1(format ratio)、Q2(document source access)、Q3(Azure AI Search resource)、Q4(GPT-5.5 deployment)、Q13(ground truth labeler)。其他 OQ 用 default 繼續。**當前 snapshot**(per session-start.md §9):18 Resolved + 5 Open(Q6/Q8/Q15/Q16/Q20 non-blocking default value 繼續;Q23 Resolved 2026-07-14 — Multi-language promote approved 雙半,implement 待 i18n phase plan §10 R1)。

---

## 9. Sprint Awareness

> **此表反映實際 trajectory**(已超出原 spec 12-week)。詳細 phase status / commits / artifacts 看 [`docs/12-ai-assistant/01-prompts/01-session-start.md` §10 + §12](./docs/12-ai-assistant/01-prompts/01-session-start.md)。

| Week | 你嘅 default focus(若無其他 instruction) | Hard cutoff / Status |
|---|---|---|
| W1 | Foundation:FastAPI skeleton、Next.js skeleton、Docling .docx parser、KB CRUD、Eval set v0、Azurite local | ✅ closed 2026-05-02 |
| W2 | Multi-format ingestion + Hybrid retrieval baseline + Admin Console layout | ✅ **Gate 1 PASS R@5=0.9722** 2026-05-04 |
| W3 | Cohere Rerank + GPT-5.5 synthesis + Citation + Chat UI streaming + PPT parser | ✅ closed 2026-05-04 |
| W4 | CRAG L2 + RAGAs eval automation + Reranker shootout(4-way → 2-way per Karpathy §1.2)+ 加 20 條 real query | ✅ closed 2026-05-04(Gate 2 verdict deferred → W5) |
| W5 | Optimization;**conditional** L3 routing(only if Gate 2 全 pass) | ✅ closed 2026-05-04(**Gate 2 PARTIAL PASS** landed W5 D2;L3 NOT triggered) |
| W6 | Final eval + Demo prep + Beta plan + Azure 2-way verify | ✅ closed 2026-05-05(Gate 2 PARTIAL PASS confirmed;Cohere v4.0-pro reaffirmed final;Q21 Resolved) |
| W7-W8 | Microsoft Entra ID auth(mock bridge)+ rate limiting + mobile responsive + Langfuse SDK + cost dashboard + alerts | ✅ closed 2026-05-06 |
| W9-W10 | Beta internal testing prep + C11 dependency_overrides cleanup + cost dashboard real-time wire + W11 governance prep | ✅ closed 2026-05-06 |
| W11 | Staged rollout 25% + Mode B local dev + **UI sprint pivot triggered**(architecture.md v5.1→v6 amendment;ADR-0014 hybrid auth + ADR-0015 UI Tier 1 expansion sister ADRs) | ✅ closed 2026-05-08 |
| **W12–W15 UI sprint cycle(pivot)** | Phase 1 W12 foundation discovery → Phase 2 W13 user-facing views + ADR-0016 scrypt → Phase 3 W14 admin views refactor → Phase 4 W15 polish closeout FINAL + Playwright E2E baseline harness | ✅ all closed 2026-05-09 — **Tier 1 UI sprint cycle FINAL gate PASS WITH SMOKE-USER-DEFERRED CAVEAT** |
| W16 | Beta deploy resume — Track A IT cred + 25% rollout activation + daily metric monitor + backend stub closure cascade | 🟡 **draft / partial**:F5 stub cascade DONE;F1-F4 仍 pending **Track A IT cred populate event + R-B1 closure** |
| W17 | Beta hardening(parallel to W16)— Postgres persistent backing(ADR-0023)+ auth-transport hardening(ADR-0022)+ RAGAs 4-metric integration + ADR-0017 R8 mitigation pattern | ✅ closed 2026-05-10(Gate PASS;🚧 F1.5b + F3.5b R8/Azure-key-bound runtime smoke deferred per CO17) |
| W18 | Unified application shell IA(per ADR-0024)— `<AppShell>` across all authenticated views + URL flatten(`/admin/*`→`/kb/*`)+ `/dashboard` real overview + `/settings` + `<GlobalSearch>` Cmd/Ctrl+K palette + V7 Landing removed | ✅ closed 2026-05-11(Gate PASS WITH SMOKE-USER-DEFERRED CAVEAT) |
| W19–W99 | _occurred — rolling JIT per §10 R1(此表未逐 phase backfill,以 phase folder + session-start.md §10 為準)_ | _image-recall(W59-68,ADR-0054)/ ADR-0056 per-KB config vision(W72-85)/ inline image markers(W70-71)/ enterprise RBAC track(W88-95:P0→P2→P3→P5,ADR-0066/0067/0068)/ 完整度 eval gate(W96-97,ADR-0069 REVERT)/ 圖錨 amendment(W98-99,ADR-0056 §Amendment)_ |
| **W100–W101 integration layer 階段 1** | 統一整合層(ADR-0070)SharePoint 按需匯入 — **W100 backend**(`SourceConnector` interface + SharePoint connector + `get_principals` 權限映射 + import service + RBAC + production adapter,**ingestion 核心零改動**)+ **W101 前端**(ADR-0071 頂層 Integrations 模組 — landing + 4 步 wizard 共 5 surface H7 重現 + 3 browse 端點) | ✅ both closed 2026-06-30(G-W100 + G-W101 PASS;live 端到端 blocked 真 tenant + `Sites.Selected`,D4) |
| W102+ | _not pre-created_ — rolling JIT per §10 R1 | _candidates(多 blocked on external):**整合層 live 驗證 runbook**(真 tenant + `Sites.Selected`,blocked IT)/ **整合層多 provider + auto-sync**(Tier 2,H4 需 ADR)/ Track A IT cred(W16 F1-F4)/ production v1→v2 原子切換 / prose human GT(卡用戶)/ RBAC P5 impl(等審計 driver)/ `section_anchor_nearest` global default flip(另一決定)/ 新 use case_ |

如果 Claude Code session 邊個 week 唔清楚,**ask user "What week / day are we in?"** 之後再做 default focus 對應。Hard gates:Gate 1 ✅ / Gate 2 PARTIAL ✅ / Gate 3 ✅ / Tier 1 UI sprint cycle FINAL ✅ / **Production launch gate ⏳ pending Track A IT cred**。

---

## 10. Phase Planning Workflow

> 配合 §9 Sprint Awareness:每個 sprint week 屬一個 phase,有 dedicated planning artifacts。
> Source of truth:[`docs/01-planning/PROCESS.md`](./docs/01-planning/PROCESS.md)(完整 lifecycle、template、anti-pattern)。

### 10.1 Per-Phase Artifacts(3 docs)

每 phase 喺 `docs/01-planning/W{NN}-{phase-name}/` folder 內建立:
- **`plan.md`** — Phase scope + deliverables + acceptance criteria + risks(kickoff 寫,locked,改要 changelog)
- **`checklist.md`** — Atomic checkbox items per deliverable(daily tick)
- **`progress.md`** — Daily progress + decisions + commits + 結尾 retro(v1.0 嘅 `journal.md` 已 rename per PROCESS.md v2.0)

### 10.2 Binding Rules(R1–R5,process-level constraint)

- **R1**:任何 multi-day implementation 之前必須有對應 phase `plan.md` committed。**無 plan 唔可以 implement → STOP and ask**
- **R2**:Daily commit 必須對應 `progress.md` Day-N entry(`docs(planning):` housekeeping commits 例外)
- **R3**:Plan deviation(scope change / new deliverable / 取消 deliverable)必須 log 入 `plan.md` changelog,**唔可以 silent drift**
- **R4**:OQ resolved → 同步更新 `decision-form.md` AND `progress.md` Day-N entry mention
- **R5**:Phase closeout 之前任何 architectural-adjacent decision(per §5.1 H1)必須寫 ADR
- **R6**:Pre-active-flip 5-step grep verification **recursive scope** — apply 唔單只 to code-at-active-flip-time,**也** to **plan-text itself** at plan kickoff(W23 F3 amendment per W22 D1/D8/D9 3 次 cumulative recursive catch evidence;memory `feedback_design_fidelity.md` 5-pattern catalog)。5 步:**(1)** read plan literal acceptance criteria;**(2)** grep code base / mockup source for referenced files / functions / patterns;**(3)** surface mismatches via Karpathy §1.1 think-before-coding upfront;**(4)** document deviations in plan §7 changelog at plan kickoff(or active-flip);**(5)** adjust acceptance criteria per actual reality。Recursive trigger:plan text 引用 pre-W{N-1} surface / naming / wording(common contamination source per W20→W22 inheritance);catch it 喺 implementation 之前,而非 post-implementation user-eye audit。
- **R7**:任何 pending 工作 / next-candidate 嘅**識別**同**進度變動**必須反映喺 [`docs/01-planning/BACKLOG.md`](./docs/01-planning/BACKLOG.md)(中央 backlog dashboard)。觸發點:**(1)** 新 candidate 被識別(分析 / 討論 / ADR Accept / phase retro carry-over / 用戶提出)→ 加一行(狀態 `候選`);**(2)** phase kickoff(plan 建)→ 對應項改 `進行中`;**(3)** phase closeout → 改 `完成`,有 recurring debt 則同步 `DEFERRED_REGISTER.md`;**(4)** defer / blocked 決定 → 改對應狀態 + link DD-N 或阻塞源。BACKLOG 係 **index 層**,細節唔複製(link ADR / DEFERRED_REGISTER / TRACKER / phase folder),避免雙重維護 stale。**唔可以 silent drift**(同 R3)。維護規則全文喺 BACKLOG.md 文末。

### 10.3 AI Session Start Protocol

每個 Claude session 開始(在 §0 quick identity check 之後),AI **必須順序執行以下 6 步**,先 reply 用戶第一句訊息:

1. 讀 `docs/12-ai-assistant/01-prompts/01-session-start.md`(SITUATION EKP — **13 components C01–C13** / **23 OQ snapshot** / 紀律 9 項 / 權威排序 7-tier / **W1–W18 timeline + W19+ rolling JIT**)
2. 讀 active phase 嘅 `plan.md`(知 scope + acceptance criteria)
3. 讀 active phase 嘅 `checklist.md`(知 next un-checked item;active phase = `git status` + 最新 W{NN}-{name} folder)
4. 讀 active phase 嘅 `progress.md` 最近 3 個 Day-N entries(知 context + blockers + carry-overs)
5. Run `git status --short` + `git log --oneline -5`(知 working tree state)
5b. **若本 session 預期會做 backend restart / eval run / RAGAs eval / Langfuse trace 操作 → 先 pre-flight endpoint health check**(per PC-W33-1 + PC-W34-1,W34 F2.3 audit_log 30s gap + W35 F1.3 Docker stuck 經驗驅動):
   - `Invoke-WebRequest -Uri http://localhost:3000/api/public/health -TimeoutSec 30`(預期 `StatusCode 200` — Langfuse endpoint;若 Docker `unhealthy` flag 但 endpoint 200 OK = timing artifact 不阻擋)
   - `docker exec ekp-postgres psql -U langfuse -d postgres -c "SELECT 1;"`(預期 `1 row` ready_for_query — Postgres handshake)
   - **重要 distinguishing**:Docker `(unhealthy)` container status ≠ endpoint reachability。Docker health check 有 timing artifact(W34 W35 案例 Langfuse `Up X mins (unhealthy)` 但 `/api/public/health` 200 OK with 30s timeout cover warmup)。**以 endpoint 200 為準**,不以 Docker flag 為準。
   - 若 endpoint 唔 reachable → surface 至 user before destructive ops(per CLAUDE.md "Executing actions with care" + destructive 操作 explicit instruction)
6. 唔清楚 / item acceptance criteria 模糊 → ask user(per §13 When in Doubt)

**Compact 後嘅特殊處理**:`/compact` 觸發後 context 重組,AI **必須 re-read 步驟 1–4**。原因:compact summary 對 active session work(commits / tests / files)retain ~95%,但對 standing instructions(§3 **13 components** / §9 **23 OQ snapshot** / §13 紀律 9 項 / 權威排序 7-tier)retention 只有 ~60%,容易令 AI 答出 generic correct 但缺 EKP-specific structure 嘅 reply。Re-read 後唔需主動 summarize(用戶問先講),但要確保下一個 reply 對齊 SITUATION + active phase。

### 10.4 Phase Folder Naming

`W{NN}-{phase-kebab-name}/` 對應 §9 Sprint Awareness 嘅 W{NN} sprint week。
Example:`W01-foundation/`、`W02-multi-format-ingestion/`、`W04-crag-eval-shootout/`、`W18-app-shell-ia/`。**Rolling JIT**:每 phase 喺 kickoff 先建,**唔可以一次過建 W01–W18+**(W19+ 仍未 pre-created,等下一 sprint trigger 先 kickoff)。

### 10.5 Reference

- **Central backlog dashboard**(全部 pending / next-candidate + 進度,per R7):[`docs/01-planning/BACKLOG.md`](./docs/01-planning/BACKLOG.md)
- Workflow source of truth:[`docs/01-planning/PROCESS.md`](./docs/01-planning/PROCESS.md)
- Templates:[`docs/01-planning/_templates/`](./docs/01-planning/_templates/)
- W01 reference example:[`docs/01-planning/W01-foundation/`](./docs/01-planning/W01-foundation/)

---

## 11. Output / Communication Conventions

當你 reply 喺 chat 入面:

- **繁體中文紀律 — Binding Strict Rule(同 H7 design fidelity 同層,user 4 次重複提醒後 escalate)**:
  - **回覆語言**:繁體中文為主 — **包括 markdown table heading / section heading / status verdict word / narrative bullet lead / connector phrase**
  - **唯一可以保留原文嘅 6 類**:(1) 程式碼識別符 (函式 / 類別 / 變數名 如 `emit_stage_metadata`) / (2) 檔案路徑 (`backend/generation/prompt_builder.py`) / (3) API 端點 (`/eval/run`) / (4) commit hash + branch 名 / (5) ADR / spec section 編號 (ADR-0038 / architecture.md §3.5 / H1-H7) / (6) vendor / 產品名 (Cohere / Azure AI Search / Next.js)
  - **Phase Gate verdict 詞** (`PASS` / `FAIL` / `PARTIAL`) 可保留作 vendor convention,**但** narrative 描述要中文(寫「G1 通過」「G2 未達」「Phase Gate 部份通過」配合 verdict word,唔可以「G1 PASS within tolerance」全英文 sentence)
  - **常違反 mapping**(必 translate):「Next」→「下一步」/ 「Status」→「狀態」/ 「Done」→「已完成」/ 「pending」→「待」/ 「ticked」→「已 tick」/ 「verdict」→「判決」/ 「hypothesis」→「假設」/ 「validated」→「驗證」/ 「refuted」→「反證」/ 「lessons learned」→「教訓」/ 「priority queue locked」→「優先順序鎖定」/ 「recovery」→「恢復」
  - **Hard enforcement gate**(per memory `feedback_chinese_primary_replies.md` W27 D3 第 4 次違反 escalation):
    - **每段 reply 之前** think:「呢段 reply 入面所有 non-code 英文 word 是否每個都喺 6 類保留範圍?」非保留範圍 → 立即 translate
    - **每段 reply 完成後** 強制 final self-check — scan 全文,任何 non-code English phrase = violation
    - **違反 binding level = H7 design fidelity** 同層 — task 未完(同「大概模仿」mockup 一樣係 broken project signal)
    - Memory reset 唔再依賴 — **每段 reply** mandatory active self-check,session-internal drift 必須立即 catch
  - **High-risk surface**(累積 4 次違反 surface):Phase closeout summary / Phase Gate verdict report / hypothesis re-evaluation / multi-section markdown reply 任何含 table + bullet + heading 嘅長文都係 high-risk → 寫呢類回覆要 *逐字* 自檢
  - 詳細 anti-pattern + W22 D6 + W26 D5 + W27 D3 cumulative empirical findings 見 memory `feedback_chinese_primary_replies.md`
- **唔好過度 disclaimer**(避免「嗱呢個都係要視乎情況...」呢類 hedging)
- 重要決定要**明確 surface**,唔好 bury 喺長文最後
- Code change 要**說明 what + why**,唔需要重複 code 內容
- 引用 spec 要**標明 section**,e.g. `(per architecture.md §3.5)`
- 遇到 H1–H7 hard constraint trigger,**第一句就要 STOP and explain**

當你寫 code:

- Function / class docstring **必須**(public API)
- Inline comment 解釋 **why**,唔係 **what**
- Error message 要 actionable(「embedding API 5xx」< 「Azure OpenAI embedding endpoint returned 503,suggest retry with exponential backoff」)
- TODO 必須有 owner:`# TODO(chris): wire MSAL middleware after Q11 resolved`

---

## 12. Self-Verification Before Marking Task Done

完成一個 task 之前,**run through 以下 checklist**:

- [ ] 對應 spec 嘅哪個 section?(quote section number)
- [ ] 有冇 violate H1–H7?(若有,即係 task 未完)
- [ ] 有冇 violate §1 Behavioral Baseline?(每行改動 trace 返 user request 嗎?)
- [ ] **Frontend changes only — Design Fidelity check(per §5.7 H7 + §3.2.1)**:有冇打開 `references/design-mockups/EKP Platform.html` 對應頁面對齊?layout / spacing / typography / color tokens / interaction states / responsive / a11y 全部 100% match 咗未?唔啱嘅地方有冇 surface(STOP+ask per §5.7 H7 trigger 或標 🚧 deferred + reason)?**「大概模仿」== H7 violation == task 未完**
- [ ] Test 寫咗未?(若 critical module)
- [ ] Linter / formatter run 過?
- [ ] Commit message follow Conventional Commits?
- [ ] 任何 architectural-adjacent 改動 → ADR 寫咗未?
- [ ] 用咗 Dify reference?在 PR comment 標 source 未?
- [ ] OQ status check:呢個 task 依賴邊條 OQ?status 係咩?
- [ ] Phase checklist 對應 item tick'd?Journal Day-N entry 寫咗未?(per §10 R2)

---

## 13. When in Doubt(default behavior)

| 情況 | Default |
|---|---|
| Spec 同 your idea 衝突 | Spec wins,unless you explicitly raise + get approval |
| Spec 缺乏 detail | Ask user,don't guess |
| 兩種實作方式都 reasonable | 揀**更接近 v4/v5 既有 pattern** 嘅一個 |
| Stakeholder feedback 同 spec 衝突 | STOP — surface the conflict,等 resolution |
| **Mockup vs implementation 唔對齊**(任何一項 — layout / spacing / typography / color / interaction / responsive / a11y) | **STOP per §5.7 H7** — surface deviation + open mockup + propose 處理方案(加 primitive / 寫 vanilla / 改 mockup / `🚧 deferred`)— **絕對唔可以 approximate** |
| **Mockup detail 不清晰** / **shadcn 冇 primitive 重現** | **STOP per §5.7 H7** — surface gap + ask user(加 primitive / 寫 vanilla / 改 mockup) |
| **Mockup vs backend contract 衝突**(e.g. mockup 2-step verify vs backend 3-step 6-digit code — **data contract conflict only**)| **STOP per §4 authority ordering** — architecture.md > design-mockups;backend wins on **field shape / schema / endpoint signature** + 記 plan §7 changelog + visual polish-only migrate(per W20 F7.2 precedent) |
| **Mockup visual element vs backend mode mismatch**(e.g. mockup 4-button seg vs backend `?filter=` supports 3 values)| ⚠️ **§13 backend-wins NOT applicable to visual element removal** — §13 covers data contract conflicts(field shape),NOT visual surface design decisions。Default = **mockup visual fidelity wins**(client-side post-filter / synthesize / fallback);drop visual element only as H7 deviation + STOP+ask per §5.7(per W23 F3 amendment + W22 D6 over-extending precedent;memory `feedback_design_fidelity.md` D6 pattern) |
| Tier 1 / Tier 2 邊界模糊 | Default to Tier 2(out of scope),ask if uncertain |
| Performance vs simplicity trade-off | Tier 1 階段:simplicity wins(2K chunks 無 perf 壓力) |
| Quality vs delivery time trade-off | 4 metric target 唔可以 compromise;UI polish 可以後補 |
| **圖文 recall / 呈現衝突**(原文圖跟隨文字、答案點還原、末尾孤兒圖點處理)| **以原文檔還原為準**(north-star,見 §15)— 原文某段本來有圖跟隨 → recall 嗰段時圖還原到對應位;**唔係圖文 1:1 配對**;**勿以答案文字為中心無腦退底部**(= 改錯方向);末尾孤兒圖**退底部 / 收納前先分甲 / 乙 / 丙**(甲=原文有文字且在答案→還原段旁;乙=答案濃縮冇寫→係答案還原唔夠;丙=逐欄截圖無獨立句→還原章節位)。詳見 memory `principle_source_fidelity_recall` |

---

## 14. Update This File

**呢份 CLAUDE.md 會 evolve**。當以下情況發生,update 呢份 file:

- 加新 vendor / dependency(approved + ADR 寫咗)
- 改 sprint timeline
- 加 / 改 hard constraint
- New OQ resolved
- New convention adopted by team

**Update 規則**:
- 改動必須喺 commit message 標 `docs(claude-md): <change>`
- 重大 update(改 H1–H6 或 §1 Behavioral Baseline)需要 user explicit approve
- 微調(加 routing entry、update sprint week status)可以自行做

---

## 15. North-Star Principle — 圖文還原度(Source Fidelity Recall)

> **用戶 2026-06-20 確立嘅 RAG / 知識系統最根本目的準則。** 同 §1 Behavioral Baseline 一樣 universal,適用於**所有** recall / 圖文呈現 / 完整度相關決策。

**核心**:答案要**忠實還原原文檔本來嘅圖文關係** —— 原文檔某段內容本來有相關圖片跟隨,當嗰段內容被 recall 入答案,嗰啲圖亦應**盡可能還原到答案對應位置**。衡量嘅係「對原文檔圖文鄰接關係嘅還原度 / 忠實度」,**唔係**「每段文字都配圖」(圖文 1:1),亦**唔係**排版美觀。「盡可能」= 唔追求 100%,追求忠實。同理適用純文字:忠實還原原文內容結構,唔好過度濃縮。

**Why**:做到忠實還原,**高完整度 + 準確度係自然結果**,唔係另一個獨立要追嘅 KPI(亦呼應反對「追 100% 完美」—— 要追嘅係忠實還原)。

**執行紀律**:
- 出發點**以原文檔為中心**(原文圖跟邊段 → 答案還原嗰段時圖都還原),**唔好以答案文字為中心**(「有冇答案錨點 → 冇就退底部」會破壞還原 = 改錯方向,用戶 2026-06-20 明確警告)。
- 末尾 / 孤兒圖喺**退底部 / 收納 / 分層呈現之前,必先逐圖分辨**:
  - **甲** 原文有對應文字 + 嗰文字在答案 → 還原到嗰段旁(錨定精度問題,例如現 section-anchor `depth=1` 章節級太粗 → 要 leaf 級)
  - **乙** 原文有對應文字 + 答案冇寫嗰段(synthesizer 濃縮) → 根因 = 答案還原度 < 圖召回度,要令答案更完整重現原文,唔係掃走圖
  - **丙** 原文本來逐欄截圖、無獨立句 → 還原到表格 / 章節標題位即可
- 詳細 + 現狀座標(文字 recall ≈0.97 / 圖召回 ≈1.0 / 圖-文關係靠 W71 marker + W75 section-anchor)見 memory `principle_source_fidelity_recall`。

---

## Appendix A: Quick Reference Card(印出嚟 stick 喺 monitor)

```
EKP Tier 1 — Strict Mode
├─ North-star (RAG 目的, §15): 忠實還原原文檔圖文關係 — 原文段有圖跟隨→recall 嗰段時圖還原對應位; 非1:1; 勿無腦退底部
├─ Behavioral baseline: §1 Karpathy (think → simple → surgical → goal)
├─ Spec: docs/architecture.md (frozen v6)
├─ Stack: Azure AI Search + OpenAI + Cohere + Next.js + FastAPI
├─ Hard Constraints (Strict Mode — STOP+ask on trigger):
│  ├─ H1 — Architectural change (spec §3/§4, vendor swap, storage layout, 8-view layout philosophy)
│  ├─ H2 — Vendor / dependency (locked stack per architecture.md §3.2)
│  ├─ H3 — Dify reference (read-only, never copy code)
│  ├─ H4 — Tier 1 only (NO GraphRAG, NO multi-agent, NO multi-tenancy)
│  ├─ H5 — Security & privacy (no secrets/PII/plaintext-prompt-logging)
│  ├─ H6 — Test coverage (backend pipeline ≥ 80%)
│  └─ H7 — Design fidelity (design-mockups 100% reproduction, NO approximation)
├─ 🚫 工具紀律 (最高級・零容忍): bash 唔讀檔/搜尋 → Read/Grep/Glob; 唔 echo 拼裝/{ } group 重定向 → 單一 cmd > file 再 Read
└─ When in doubt: ask, don't guess
```

---

**End of CLAUDE.md**
**Version 2.5 — 2026-07-13 OQ count 22→23 同步(Q23 NEW)**(用戶要求同步 — decision-form 加咗 Q23〔Multi-language en/zh Tier 2→Tier 1 promote scope decision,Open,per ADR-0075 / B-25〕之後,CLAUDE.md 內所有「22 OQ」引用同步為 23)。具體變動:§2 routing「22 條 OQ」→ 23 + Q23 note / §8 開頭「22 條 OQ」→ 23 + Q23 note / §8 snapshot「17 Resolved + 5 Open」→「17 Resolved + 6 Open〔Q23 NEW〕」/ §10.3 AI Session Start Protocol +「Compact 後特殊處理」兩處「22 OQ snapshot」→「23 OQ snapshot」(CLAUDE.md 共 5 處正文改動)。**Why**:Q23 是 post-W101 新增 scope decision(non-critical,promote 前 Multi-language 維持 Tier 2 defer,唔阻 Tier 1),但 OQ 總數變咗,standing-instruction count 唔同步會令後續 session 讀到 stale 數字。Q23 於 2026-07-14 → **Resolved**(用戶 as Stakeholder scope + Chris 架構雙 approve promote,APAC driver = 內部+外部 both;ADR-0075 → Accepted;§8 snapshot 更新 18 Resolved / 5 Open;**implement 待 i18n multi-day phase plan §10 R1**,Tier 邊界 amendment〔architecture.md §11 Multi-language 移出 Tier 2 + CLAUDE.md §5.4 H4〕留 phase 首 deliverable — **§5.4 H4 list 本 version 未動**)。連帶 `docs/decision-form.md`(Q23 Decision/Status Resolved + §4 dashboard + 2026-07-14 snapshot)+ `session-start.md §9`(22→23 + Q23 移 Resolved section)同步。歷史 changelog(Version 1.4「21→22 OQ」)**不改**,保 audit trail。
**Version 2.4 — 2026-07-10 工具使用強制紀律(bash 讀檔/搜尋一律改 Read/Grep/Glob)**(用戶 merge 事件後 explicit 要求——大量 bash `echo`/`cat`/`grep` 拼裝 + `{ }` group 重定向造成輸出污染,險 commit 損壞內容)。具體變動:§5 Hard Constraints 與 §6 之間新增獨立 top-level section「🚫 工具使用強制紀律」(3 條絕對禁止:bash 讀檔/搜尋 → Read/Grep/Glob;`echo` 拼裝 / `{ }` group 重定向 → 單一命令 `cmd > file` 再 Read;靠 stdout 判斷 → 寫檔後 Read;bash 唯一正當用途 = 無專用工具替代的 CLI + 單一命令重定向)+ Appendix A Quick Reference Card 加一行。**優先級 binding-strict = §5 H1-H7 + §11 中文紀律級別**;用戶原文「§反捏造紀律」reference 因 EKP 無該 section 而 adapt 為 EKP 對應級別。**Why**:工具輸出污染會破壞檔案 / 訊息結構,同 design drift / 中文違反同屬 broken-workflow signal。
**Version 2.3 — 2026-07-04 document-skills 文件生成能力 routing**(用戶裝咗 Anthropic 官方 `document-skills` plugin + 配齊本機工具鏈,要沉澱畀後續 AI session 識用)。具體變動:§2 Document Routing 加一 row「生成 pptx / docx / xlsx / pdf 文件」→ 透過 Skill tool 用 `document-skills:*`,細節指向 memory `project_document_skills_toolchain`。**Why**:文件生成係通用 dev 能力(**非 EKP 產品 vendor,唔入 §5.2 H2**),但本機有 Windows 專屬配置坑(User PATH 生效要重開 session / 公司 MITM SSL 代理擋大 binary + winget 憑證 / scripted conversion 用 `soffice.com` 非 `soffice.exe`)+ 引擎機制(pptx=`pptxgenjs` / docx=`docx-js` / xlsx 靠 LibreOffice 重算)後續 AI 需知先用得順,故 routing 入 CLAUDE.md + 詳情入 memory。
**Version 2.2 — 2026-06-28 中央 backlog dashboard + R7 同步 binding rule**(用戶指出項目無統一 pending 工作記錄 / next-candidate 機制 + 無進度同步易混亂 → 兩輪 AskUserQuestion 揀「新建 BACKLOG.md」+「同步寫入 §10 binding rule」)。具體變動:新建 [`docs/01-planning/BACKLOG.md`](./docs/01-planning/BACKLOG.md)(中央 dashboard — A-F 六類 + 狀態 lifecycle + 維護規則,由 2026-06-28 全項目 pending 盤點固化做 v0)+ §10.2 加 **R7**(pending / next-candidate 識別 + 進度變動必須同步 BACKLOG,4 觸發點,index 層唔複製細節,no silent drift)+ §2 Document Routing 首位加 backlog entry + §10.5 Reference 加 BACKLOG link。**Why**:現有機制碎片化(`DEFERRED_REGISTER.md` 只收 recurring debt / `adr/README.md` 記決定 / 各 track 自己 TRACKER / §9 一句話 candidates),無單一 pending 入口 + 無防 stale 同步機制(盤點時抓到 `enterprise-rbac/TRACKER.md` checkbox + `adr/README.md` index ADR-0045/0046 兩處 stale 為證)。
**Version 2.1 — 2026-06-20 North-Star Principle 圖文還原度 promote**(用戶確立 RAG / 知識系統最根本目的準則:答案忠實還原原文檔本來嘅圖文關係,非圖文 1:1,做到還原自然得高完整度 + 準確度)。具體變動:新增 **§15 North-Star Principle**(universal,同 §1 同層,適用所有 recall / 圖文呈現決策)+ §13 When in Doubt 加「圖文 recall / 呈現衝突」row(以原文檔還原為準,末尾孤兒圖退底部前先分甲 / 乙 / 丙)+ Appendix A Quick Reference Card 加 north-star line + memory `principle_source_fidelity_recall` 新建。**Why**:用戶 2026-06-20 explicit「需要一直都有同步的準則…這是最根本目的準則」+ 揀「升格入 CLAUDE.md」。
**Version 2.0 — 2026-05-25 中文紀律 binding strict rule promote**(W27 D3 第 4 次違反觸發 user explicit「強調保持使用中文對答」request)。具體變動:
- §11 Output / Communication Conventions 第 1 條 bullet rewrite — 由 single-line 描述 expand 為 **multi-section binding rule** 包含:6 類唯一可保留原文範圍 / Phase Gate verdict word 例外 / 常違反 mapping(Next/Status/Done/pending/ticked/verdict/hypothesis/validated/refuted/lessons learned/priority queue locked/recovery)/ **Hard enforcement gate**(每段 reply 之前 + 完成後 mandatory self-check) / **violation binding level = H7 design fidelity 同層**(broken project signal)/ memory reset 唔再依賴
- §11 H1-H6 改 H1-H7(對齊 v1.7 H7 promotion)
- Memory `feedback_chinese_primary_replies.md` append W27 D3 第 4 次違反 empirical findings(累積 4 次違反 surface catalog:Phase closeout summary / Phase Gate verdict / hypothesis re-evaluation / multi-section markdown reply)+ hard enforcement gate strengthening
- **Why promote 至 binding strict 等同 H7**:user 重複 4 次提醒(2026-05-10 第 1 次 / 2026-05-18 W22 F6 第 2 次 / 2026-05-25 W26 第 3 次 / 2026-05-25 W27 第 4 次)+ explicit 要求「強調」+「commit and push」signals binding-level enforcement required;same pattern as v1.7 H7 design fidelity promotion(repeated reminder + explicit framing = elevation to hard constraint level)
**Version 1.9 — 2026-05-19 W22 anti-pattern catalog amendments**(W23 F3 — 3 amendments based on W22 D1+D6+D7+D8+D9 5 個 anti-pattern empirical-finding cumulative cataloged 喺 memory `feedback_design_fidelity.md`)。具體變動:
- §3.2 Frontend conventions 加 NEW bullet **CSS-first pivot baseline** — mockup `styles-mockup.css` 1073→1048 lines verbatim adoption(per W22 F1 mid-session pivot)係 visual layer baseline;shadcn/ui primitives 限 Radix a11y benefits(Dialog / DropdownMenu / Sheet / Toast / Tabs);Tailwind utility 限 one-off layout。原本「shadcn/ui only」+「Tailwind only」early framing under-represented actual approach;CSS-first baseline 係 W22 implementation reality
- §10 加 NEW **R6** Pre-active-flip 5-step grep verification recursive scope — apply 唔單只 to code-at-active-flip-time,**也** to **plan-text itself** at plan kickoff;cite W22 D1(F4 ChatHeader)/ D8(F6 KB cluster)/ D9(F7 observability cluster)3 次 cumulative recursive catch evidence;recursive trigger:plan text 引用 pre-W{N-1} surface / naming / wording(common contamination source per W20→W22 inheritance)
- §13 加 NEW row 區分 **「Mockup vs backend contract 衝突 = data contract conflicts only」**(backend-wins on field shape / schema / endpoint signature)vs **「Mockup visual element vs backend mode mismatch = visual fidelity wins」**(mockup 4-button seg vs backend 3-mode `?filter=` → client-side post-filter / synthesize / fallback;**drop visual element only as H7 deviation + STOP+ask**)— §13 backend-wins authority scope clarified 限 data contract,NOT visual element removal(per W22 D6 over-extending precedent + memory `feedback_design_fidelity.md` D6 pattern)
- memory `feedback_design_fidelity.md` 嘅 5 個 anti-pattern(D1 inherited-W20-surface-not-in-mockup / D6 over-extending-§13-backend-wins-to-drop-visual-element / D7 preserve-pre-W22-UI-not-in-mockup / D8 assumed-permissive-vendor-SDK-cap / D9 plan-text-contamination)係呢 3 條 amendments 嘅 empirical evidence base
**Version 1.8 — 2026-05-18 DESIGN_SYSTEM.md routing landed**(W22 F5b session post-NotificationsMenu portal pattern fix `c3ca1a3` + DESIGN_SYSTEM.md initial draft `c225b95`)。具體變動:
- §2 Document Routing 表加 2 條 NEW row:**「揾 class catalog / layout pattern / composite pattern recipe(primitive-level)」**→ DESIGN_SYSTEM.md §0-§6;**「修 design tokens / mockup CSS class / dark mode override」**→ DESIGN_SYSTEM.md §7 4-layer sync protocol。原「寫 / 改 frontend feature」row scoped 為 page-level(架構決定 vs primitive 用法分流)。
- §3.2 Frontend conventions 加一 bullet 明文 4-layer sync protocol mandatory(reason cite W22 F1 `--popover` dark drift incident)
- §3.2.1 Design Fidelity Rule 加 NEW bullet 列 DESIGN_SYSTEM.md 完整 section 結構(§0 quick reference / §2 13 primitives / §3 layouts / §4 composite patterns 含 PopMenu anti-pattern「DO NOT use Radix DropdownMenu」/ §5 color semantics / §6 interaction states)+ 解 conflict rule(mockup spec > DESIGN_SYSTEM.md dev convenience layer)+ 反 grep-and-rederive 嘅 Karpathy §1.1 cite
- §5.2 H2 Vendor lock table Frontend row 加 footnote `[^design-system-chain]` 指 DESIGN_SYSTEM.md §7 source-of-truth chain
- **Maintenance gap G1-G4 未 close**(executable layer:owner-of-record / schedule integration / drift log auto-update / cross-link enforcement)— user pick「Wave 1 only」per W22 plan §6 carry-over scope。Wave 2(session-start.md sync)+ Wave 3(maintenance executable layer)留 F8 closeout 或 W23+ explicit trigger。
**Version 1.7 — 2026-05-17 design fidelity promoted to H7 hard constraint**(per user explicit framing「**前端頁面的設計是非常重要的**」+「**100%完整地把mockup 的效果重現出來,而不是大概地模仿**」+「**必須要留意和遵守的規則**」= binding level = H1-H6 同層 hard constraint level)。具體變動:
- §5 加 NEW §5.7 H7 — Design Fidelity Constraint(5 條 trigger 條件:layout/spacing/typography/color tokens/interaction states/responsive/a11y 任一唔對齊 + mockup detail 不清晰 + shadcn 冇 primitive 重現 + layout philosophy 偏離 + design-stage expansion 之外偏離);Required behavior(STOP + propose 處理方案 + 等 user 決定,絕對唔可以 approximate);唔屬於 H7 trigger 範圍(pure backend / test / logging / refactor 無 visual 改動 / design-stage expansion proposal ADR-routed / 修 visual drift bug)
- §3.2.1 加 binding-level cross-ref 到 §5.7 H7(detail checklist 喺 §3.2.1;trigger + Required behavior 喺 §5.7)
- §12 self-verification「violate H1–H6」改「violate H1–H7」+ Frontend fidelity check 加 §5.7 H7 trigger reference +「大概模仿 == H7 violation == task 未完」
- §13 When in Doubt 加 3 條 NEW row:Mockup vs implementation 對唔齊 → STOP per H7 / Mockup detail 不清晰 / shadcn 冇 primitive 重現 → STOP per H7 / Mockup vs backend contract 衝突 → STOP per §4 authority ordering = backend wins(per W20 F7.2 precedent)
- Appendix A Hard Constraints section 重組 — H1-H7 all listed(原 freeform 描述 → structured H1-H7 enumeration);H7「Design fidelity (design-mockups 100% reproduction, NO approximation)」明文化
- memory `feedback_design_fidelity.md` cross-ref update 加 [[CLAUDE.md §5.7 H7]]
**Version 1.6 — 2026-05-17 design fidelity rule explicit**(§3.2 加 NEW §3.2.1 Design Fidelity Rule —「`references/design-mockups/` 100% reproduction」明文化:shadcn/ui 規限 *技術*,唔規限 *fidelity*;layout / spacing / typography / color tokens / interaction states / responsive 全部要逐項對齊 mockup;唔肯定就開 `EKP Platform.html` 對住做;mockup detail 不清晰 → STOP+ask,唔可以自行 approximate;design-stage expansion 例外仍受 visual fidelity 約束;Why = 前端 user-facing surface,visual drift 累積就會退步,Mockup 係 single source of truth。§12 self-verification 加一條 frontend-only fidelity check —「大概模仿 == task 未完」)
**Version 1.5 — 2026-05-16 design-mockups landed**(§2 routing「寫 / 改 frontend feature」加 `references/design-mockups/DESIGN_README.md` + `PAGE_INVENTORY.md` first-stop + 3 處 design-stage expansion 標註;§7 標題下加 disambiguation note 區分 `references/dify/`(third-party H3-bound)vs `references/design-mockups/`(EKP 自有 prototype,唔受 H3 但仍受 H2 — 唔可直接 copy stripped components,必須用 shadcn/ui 重寫))
**Version 1.4 — 2026-05-16 housekeeping catch-up for accumulated W18+ state**(§0 spec v5→v6 frozen + Tier 1 trajectory 17-phase footnote;§2 12 modules→13 modules + decision-form 21→22 OQ;§5.1 H1 v5→v6;§5.2 H2 vendor table 加 Postgres ADR-0023 + ACS Email ADR-0014;§8 OQ count 21→22 + Q22 note + 17-Resolved-5-Open snapshot;§9 Sprint Awareness extended W1–W18 + W19+ with actual status / Gate verdicts / closed dates;§10.3 12 components / 21 OQ / W1-W12 → 13 / 22 / W1-W18 + W19+ rolling JIT;§10.4 W01-W12 example → W01-W18+;Appendix A Spec v5→v6)
**Version 1.3 — added §10 Phase Planning Workflow + R1–R5 binding rules; renumbered §11–§14; §2 routing table + §12 self-verification updated**
**Effective: from W1 Day 1**
**Owner: Chris(技術 Lead)**

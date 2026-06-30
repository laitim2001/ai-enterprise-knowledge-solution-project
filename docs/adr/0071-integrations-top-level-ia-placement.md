# ADR-0071: Integrations 作為頂層 IA 模組 — sidebar nav + landing + import wizard 歸屬

**Date**: 2026-06-30
**Status**: Accepted(Chris 2026-06-30 — 用戶 session 行使 decision owner 拍板;H1 sidebar IA 擴展 + H7 配套改 mockup;→ 階段 1b implementation phase W101 解鎖)
**Approver**: Chris(2026-06-30)

> 接 ADR-0070(統一整合層 connector framework)之後嘅**前端 IA placement 決定**。觸 **H1**(application shell IA 結構擴展 — 新增 sidebar 頂層模組,類 ADR-0024)+ **H7**(NET NEW 前端 surface,本 ADR 配套改 mockup)。
> 本 ADR **只定 IA 歸屬 + landing 形態**,唔定 wizard 內部視覺(嗰個喺 ADR-0070 階段 1 mockup 已有);亦唔落 code(階段 1b implementation phase 先)。

## Context

ADR-0070(Accepted 2026-06-28)拍板統一整合層 `SourceConnector` 抽象 + 階段 1 SharePoint 按需匯入,backend 已落地(W100,G-W100 PASS)。階段 1b = 前端匯入 wizard(`references/design-mockups/integration-import/` 4 surface:Connect / Select / Import / Done)。

原 mockup 把 wizard **掛喺 Knowledge 之下**:breadcrumb「Knowledge / Import from SharePoint」+ sidebar「Knowledge」active +「‹ Knowledge」返回掣 —— 即進入點係 Knowledge 頁內一粒「Import from SharePoint」掣。理由係階段 1 範圍窄(單一 provider + 單一匯入動作,概念上同「本地上傳文件入 KB」同類)。

用戶 2026-06-30 review IA 後指出**張力**:既然 ADR-0070 確立嘅係**統一整合層**(橫切平台、未來接多 provider 嘅來源接入層),佢唔應該只係 KB 嘅一個子動作,應有**獨立頂層歸屬**。

**核心決定點**:IA 要反映「**現功能範圍**」(窄 — 單一匯入動作 → 掛 Knowledge 下)定「**平台定位**」(統一整合層 → 獨立頂層)?用戶選後者。

## Decision

採**獨立頂層 Integrations 模組**,landing + wizard 兩層:

1. **sidebar 新增頂層 nav 項「Integrations」**(Workspace section、Knowledge 之後)。對齊 ADR-0024 unified shell IA — sidebar = functional modules,Integrations 加入模組集合。

2. **Integrations landing 頁 = 來源列表**:階段 1b 最小版 = 單張 SharePoint connector card(狀態 badge +「Import documents →」入口)+ 一張 disabled affordance card(「connect another source」,標 Tier 2,代表未來 provider)。體現「來源管理」定位,未來多 provider 自然擴成 connector 列表(零 IA 重構)。

3. **4 步 import wizard 由 Knowledge 子頁改掛 Integrations 之下**:breadcrumb「Integrations / Import from SharePoint」+ sidebar「Integrations」active + 返回指向 Integrations landing。wizard 內部視覺(Stepper / 表單 / 文件 picker / progress / summary)**不變**(ADR-0070 階段 1 mockup 已定)。

4. **Tier 邊界**(守 H4):landing 階段 1b **只**做「單 connector card + import 入口」;**唔做** auto-sync / 多 provider 管理 / sync 狀態監控 / connector 設定 console —— 嗰啲係階段 2-3(Tier 2,per ADR-0070 §7)。disabled affordance 誠實表達階段 1 只有 SharePoint 可用。

5. **route**(實際命名留 impl plan):`/integrations`(landing)+ wizard 掛其下(如 `/integrations/sharepoint/import`)。route flatten 對齊 ADR-0024(無 admin framing)。

6. **H7 序列**:本 ADR 配套先改 mockup(`integration-import/` 加 landing surface + 4 surface shell 由 Knowledge 改 Integrations 歸屬)→ 用戶 review → 階段 1b implementation 必須 100% 重現。

**為何 H1**:新增 sidebar 頂層 nav 項 = application shell IA 結構擴展(模組集合由 ADR-0024/0015 嘅 view set + 1)。8-view layout philosophy **無 redesign**(每個既有 view 不動),但 IA 模組集合擴展值得 ADR 記錄,與 ADR-0024 同層級。

## Alternatives Considered

- **A. 掛 Knowledge 之下**(原 mockup):最簡單、最少改動,import 同本地 upload 同類心智模型。但**未體現「整合層」定位**,將來接多 provider 要重構 IA → 用戶 reject(要平台定位)。
- **C. Settings 下 connector 區**(如 Settings › Integrations):體現「配置 / 來源管理」語義、唔佔頂層,未來易擴成多 provider 列表。但 import 動作放配置區深一層、discoverability 弱 → 不選(用戶要頂層可見)。
- **B-直接 wizard**(頂層 menu 直接入 step1,無 landing):最少 surface。但頂層項直接係一個 4 步 wizard,IA 上唔正統(頂層通常係 landing / list),且多 provider 時仍要補 landing 重構 → 不選。
- **B-landing + wizard**(本決定):頂層 landing(來源列表)→ click 入 wizard。體現平台定位 + 未來擴展自然,代價 = 多一個 landing surface。用戶 2026-06-30 AskUserQuestion 揀此 + 命名「Integrations」。

## Consequences

- **Positive**:體現「統一整合層」平台定位;未來多 provider 自然擴成 connector 列表(零 IA 重構);頂層可見 discoverability 高;landing / wizard 分離符合「來源管理 → 匯入動作」心智模型;route flatten 對齊 ADR-0024。
- **Negative**:多一個 landing surface 要畫 mockup + impl;sidebar 頂層項密度微增(Workspace section 4 項);階段 1b 只有單一 provider → landing 暫時係「單 card + disabled affordance」過渡形態。
- **Neutral**:landing 最小版守 H4(無 auto-sync / 多 provider 管理);架構一次設計 Tier 2-friendly,impl 分階段(同 ADR-0070 §7 一致);wizard 內部視覺零改動。

## References

- ADR-0070(Source Abstraction Framework — parent;本 ADR 定其前端 IA placement)
- ADR-0024(Unified application shell IA — sidebar functional-module IA 先例)
- ADR-0015(UI Tier 1 expansion — view set baseline)
- COMPONENT_CATALOG.md C17(SourceConnector / 整合層 component)
- `references/design-mockups/integration-import/`(階段 1 mockup;本 ADR 配套加 landing + 改 4 surface 歸屬)
- CLAUDE.md §5.1 H1 / §5.7 H7 / §5.4 H4
- BACKLOG B-01(統一整合層階段 1)

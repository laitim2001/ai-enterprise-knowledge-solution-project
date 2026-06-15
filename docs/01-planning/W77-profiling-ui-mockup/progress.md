# W77 progress — profiling UI mockup(ADR-0056 層 A 段③ + OQ-B)

## Day 1 — 2026-06-15(kickoff)

**Context**:W76 開咗 profile 讀取介面(persist + API expose),段③ data 接駁點齊。用戶 review
三層 UI fit 後揀「設計 mockup(H7 正路)」+ AskUserQuestion 揀「Claude Code 直接喺 prototype 手寫」。
本 phase = author ADR-0056 D4 profiling UI mockup 入 `references/design-mockups/`。

**Grounding(plan kickoff)**:
- 現有 prototype = code-based HTML/JSX(`EKP Platform.html` + `ekp-page-*.jsx` + `styles.css` 30KB +
  `ekp-data.jsx` + `DESIGN_SYSTEM.md`)。**唔係 Figma**;新 mockup reuse 現有 13 primitives。
- DESIGN_SYSTEM.md §0-§2 grounding:badge family(success/info/muted/accent/**warning**=amber「re-index
  needed」/error)+ `badge-dot`;tokens 全 `oklch(var(--token))`;--warning 語義 = 需人手介入。
- **4 落點 R6 grep 核實**:L2 = `ekp-page-kb.jsx` Documents table(line 266-307,badge pattern)/
  L3 = `ekp-page-doc-detail.jsx` `DocConfigTab`(line 410,tab strip inspector/config line 66-67)/
  Settings = `ekp-page-settings-tabs.jsx` `tabs` array(line 9-15,6 tabs 加第 7)/ L1 =
  `ekp-page-misc.jsx` `PageUploadWizard` StepExecute(line 63)。

**H7 定位**:author mockup(ADR-0056 OQ-B 既定)= D4 H7 warning 講嘅「實作前先設計 mockup」步驟,
本身唔 trigger H7;但新 mockup 必須 reuse 現有 design system(prototype 內部一致)。

**紀律自檢**:H1 ✅(唔改 IA;現有 page 加 section/欄/tab)/ H2 ✅(prototype stripped components)/
H4 ✅(層 A)/ H7 ✅(author mockup,reuse design system)/ Karpathy ✅(reuse primitives 不發明)。

**Plan 落地**:W77 folder + plan.md(active)+ checklist.md(F1-F6)+ progress.md。

**F1-F2 implement(Day 1)**:
- **F1 mock data**(`ekp-data.jsx`):8 個 indexed doc 加 `profile` object(mirror W76 `DocProfileInfo`:
  profile / confidence / fallback_applied / 13-signal)。signals 同 profiler rule 一致(P1_imgdense
  img_density 0.169-0.188 ≥ 0.15;PDF img_density 0;P3 pptx img_density 0.904)。cover P1_imgdense×3 /
  P1_text×2 / P2_prose / P3_slide_imgdense / 低信心黃旗(security 0.56 + fallback_applied)。indexing /
  failed / queued docs 自然無 profile(L2「未分析」demo)。
- **F2 L2 badge**(`ekp-page-kb.jsx` Documents table):Chunker 欄後加「Profile」欄 + `ProfileBadge` helper
  (PROFILE_LABELS 6 類縮短中文 label + 信心度 %)。低信心 → `badge-warning` 黃旗 + title「建議人手確認」;
  unprofiled → `badge-muted`「未分析」opacity 0.65。reuse 現有 badge/badge-dot/mono/muted primitives,
  零 hardcode 顏色。

**Checkpoint(Day 1)**:F1-F2 後 browser 驗 L2(`8088` http.server,playwright 阻 file://)→ Documents
table profile 欄 render 成功。**用戶 confirm design 方向**(AskUserQuestion):label = 中文縮短(P1 圖密SOP);
L2 方向 OK,繼續 F3-F5。

**F3-F5 implement(Day 1)**:
- **F3 L3 文件畫像**(`ekp-page-doc-detail.jsx` DocConfigTab):scope banner 後加「文件畫像」card —
  `DocProfileBadge`(右上)+ signals 透明展示 `stat-grid`(img_density / list_ratio / max_depth / headings /
  PDF text-layer / paragraphs)+ override `select`(7 類)+ 低信心 `banner-warning` + `ProfileSignal` helper。
- **F4 Settings 分類規則**(`ekp-page-settings-tabs.jsx`):加第 7 tab + `SettingsDocProfiling` —
  profile→preset mapping `table`(7 profile,值對齊 `profile_presets.py` + W75 section cap=5)+ `ThresholdRow`
  (confidence 0.70 / img_density 0.15 / too_small 20,對齊 `profiler.py`)。
- **F5 L1 上載偵測**(`ekp-page-misc.jsx` StepExecute):加 L1「自動文件分類」`banner-info` + 每 indexed
  doc row 顯示偵測 profile badge + 信心度「已自動套對應 preset」+ `UPLOAD_PROFILE_LABELS`。

**F6 browser 驗 + closeout(Day 1)**:
- **L2 / L3 / Settings 三處 browser 肉眼驗成功**(no-cache `8089` server force fresh):Documents profile 欄 /
  文件畫像 card + signals stat-grid / Settings 7 tabs + mapping table,全部視覺對齊現有 UI、console 0 error、零 drift。
- **L1 browser visual DEFERRED**:browser/babel 頑固緩存 stale StepExecute transform(多次 fresh navigate +
  close page + no-cache 8089 server 都攞 old);**disk code grep-verified 正確**(const + banner + per-doc)+
  misc.jsx executed 無 syntax error(StepExecute=function / UPLOAD_PROFILE_LABELS=object)+ 同 L3/Settings 同類
  banner-info/badge primitive(已驗 render)→ 非 code 問題,純 browser 緩存 artifact。
- **方法論教訓(W22 DD-1 系列延伸)**:design-mockups browser 驗要 **no-cache http.server**(SPA hash 切換 +
  browser HTTP cache 會頑固 serve stale jsx;8088 標準 server cached old → 6 tabs 假象;8089 no-cache → 7 tabs 真相)。
  驗證真確性:`window.<Component>.toString()` check edit string 比肉眼可靠(揭穿 cache)。

**Retro(Day 1)**:
- **cross-file const 唯一命名**:3 個 page jsx 各定義 profile label map(`PROFILE_LABELS` / `DOC_PROFILE_LABELS` /
  `UPLOAD_PROFILE_LABELS`)+ badge helper(`ProfileBadge` / `DocProfileBadge`)。EKP Platform.html load 全部 jsx
  入同一 global scope,**同名 const 會 redeclare SyntaxError** → 特登用唯一名避(DRY 讓位 prototype 安全)。
- **reuse primitives 零發明**:全程用既有 badge/badge-warning/card/stat-grid/select/banner/table,零 hardcode
  顏色(全 `oklch(var(--token))`)→ 4 處視覺自動對齊現有 UI(H7 一致兌現)。
- **早 checkpoint 省返工**:F2 後即 browser 驗 + 用戶 confirm label 風格,先做 F3-F5(同風格 propagate)→ 避免
  做晒 4 處先發現 label 要改。
- **mock data 同 backend rule 一致**:ekp-data.jsx signals 對齊 profiler rule(P1_imgdense img_density≥0.15 等)→
  L3 文件畫像顯示 signals 時可信(用戶睇到 0.188 明白點解 P1 圖密)。
- **交棒**:F6.3 PAGE_INVENTORY 說明 deferred;L1 browser visual 留下次 fresh session;段③ mockup 完成 →
  frontend 實作(對齊呢套 mockup)係之後 phase。

**Commits**:
- `8432219` docs(planning): W77 kickoff
- `eb0d354` feat(design): W77 F1-F2 mock profile data + L2 文件列表 badge
- (本次)feat(design): W77 F3-F5 L3 文件畫像 + Settings 分類規則 + L1 上載偵測
- (closeout)docs(planning): W77 closeout

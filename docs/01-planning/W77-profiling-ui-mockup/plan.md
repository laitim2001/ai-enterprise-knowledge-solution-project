# W77 plan — profiling UI mockup(ADR-0056 層 A 段③ + OQ-B)

**Status**: closed(2026-06-15,WITH L1-BROWSER-VISUAL-DEFERRED CAVEAT)
**Kickoff**: 2026-06-15
**Phase 類型**: design mockup(author `references/design-mockups/` profiling UI;非 frontend 實作)
**ADR**: ADR-0056 D4 三層 UI + OQ-B(「profiling UI 需設計 + 加 design-mockups,H7 對齊」)

---

## §1 Context / 緣起

W76 開咗 profile 讀取介面(persist + API expose),段③ 三層 UI 嘅 data 接駁點齊。用戶揀
「設計 mockup(H7 正路)」+「Claude Code 直接喺 prototype 手寫」。本 phase = author ADR-0056
D4 嘅 profiling UI mockup 入 `references/design-mockups/`,為將來 frontend 實作建立 design spec。

**H7 定位**:本 phase 係 **author mockup**(ADR-0056 OQ-B 明文「profiling UI 需設計 + 加
design-mockups」)—— 即 D4 尾 H7 warning 講嘅「實作前先設計 mockup」步驟。author mockup 本身**唔
trigger H7**(H7 係 implementation vs mockup 嘅 deviation)。但新 mockup **必須 reuse 現有
`styles.css` primitives + design tokens**(prototype 內部一致性),否則之後 frontend 對齊會 drift。

**現有 prototype 形態**(grounding):code-based click-through HTML/JSX(`EKP Platform.html` +
`ekp-page-*.jsx` + `styles.css` 30KB tokens/class + `ekp-data.jsx` mock data + `DESIGN_SYSTEM.md`
dev API ref)。新 mockup reuse 現有 13 primitives(badge/card/field/seg/switch/table/banner/...)。

---

## §2 Scope / Deliverables(R6 落點全部 grep 核實)

### F1 — mock profile data(`ekp-data.jsx`)
- 每 doc 加 `profile`(label)+ `profile_confidence` + `signals`(13-field,mirror W76 `DocProfileInfo`)。
- 至少 cover:P1_sop_imgdense(高信心)/ P2_prose / P4_scan / 一個低信心(黃旗 demo)/ 一個 unprofiled(null)。
- **acceptance**:shape 對齊 backend `DocProfileInfo`(profile / confidence / signals)。

### F2 — L2 文件列表 profile badge(`ekp-page-kb.jsx` Documents table,line 266-307)
- Documents table 加「Profile」欄:`badge`(P1=accent-ish / P2=muted / 低信心=`badge-warning` 黃旗)+
  信心度。unprofiled → muted「未分析」。
- **acceptance**:reuse `.badge` family + `badge-dot`;低信心黃旗用 `--warning`;對齊現有 status 欄 badge 風格。

### F3 — L3 文件畫像 section(`ekp-page-doc-detail.jsx` `DocConfigTab` line 410)
- config tab 頂加「文件畫像」`card`:① 偵測 profile + 信心度 badge ② signals 透明展示(img_density /
  list_ratio / max_depth / pdf text-layer 等,用 `stat-grid` 或 key-value rows)③ override 下拉
  `select`(換 profile)④ 低信心 `banner-warning`「待人手確認」。
- 放喺現有 per-doc knobs 之上(profile 解釋「點解套呢個 preset」)。
- **acceptance**:reuse `.card` / `.stat`/`.field`/`.select`/`.banner`;signals 可讀;override 係 `select` primitive。

### F4 — Settings 分類規則 tab(`ekp-page-settings-tabs.jsx` `tabs` array line 9-15)
- 加第 7 tab「文件分類規則」:① profile→preset mapping `table`(6 profile × preset knob 摘要)②
  threshold 可調(`field` + range)③ 每 preset 點開睇 knob。admin 自行調試指揮中心。
- **acceptance**:tab 加入現有 6-tab strip;mapping table reuse `.table`;對齊其他 tab 嘅 `.card` 佈局。

### F5 — L1 上載偵測 banner(`ekp-page-misc.jsx` `PageUploadWizard` StepExecute line 63)
- ingest 完成 step 加「偵測為 P1_sop_imgdense(信心 0.9),已套 X preset」`banner-success` + 即時
  override 連結。
- **acceptance**:reuse `.banner`;對齊現有 wizard step 視覺。

### F6 — wire + browser 驗 + closeout
- 確認 4 處喺 `EKP Platform.html` render(jsx 自動 load;如需 mock data wire 補)。
- **browser 肉眼驗 4 處**(DD-1):開 `EKP Platform.html` → 對應 route → 視覺對齊現有 UI(無 drift)。
- `PAGE_INVENTORY.md` / `DESIGN_README.md` 補 profiling UI 說明(如需)。
- closeout:plan closed + progress retro + memory。

---

## §3 設計原則(H7 一致性)

1. **零 hardcode 顏色** — 全用 `oklch(var(--token))`(badge variant / --warning / --info / --success)。
2. **reuse 現有 primitives** — badge / card / field / select / seg / banner / stat-grid / table;
   唔重新發明 component(DESIGN_SYSTEM.md §2 primitives + §4 composites)。
3. **mockup spec > DESIGN_SYSTEM.md** 衝突時(後者係 dev convenience layer)。
4. **信心度 visualize**:高信心 = 正常 badge;低信心(< threshold)= `badge-warning` 黃旗 + banner「待確認」
   (對齊 --warning「re-index needed」語義 = 需人手介入)。

---

## §4 Non-goals(明確唔做)

- **`frontend/` 實作** — 本 phase 只 author mockup;frontend 對齊係之後 phase。
- **backend** — W76 已做 read surface。
- **LLM tie-break UI** — ADR-0056 D5 保險未實作,UI 不含。
- **config-test 試跑 UI 重做** — 現有 DocConfigTab config-test 已有,profiling 只加畫像 section 喺其上。

---

## §5 Risks

- **R1 4 個 ekp-page jsx 各有現有結構,改動要逐個深入 ground** — 緩解:逐 F implement 時讀對應落點區,
  唔一次過假設(R6 recursive:plan 引用 line 已 grep 核實,但 implement 仍要讀 surrounding context)。
- **R2 信息密度** — 文件畫像 section 13 signals 全展會擠;緩解:主信號(img_density/list_ratio/max_depth/
  pdf text-layer)優先,其餘摺疊或次要。
- **R3 mock data shape drift** — ekp-data.jsx profile shape 要對齊 W76 DocProfileInfo;緩解:F1 對住 schema 寫。

---

## §6 紀律自檢(kickoff)

- **H1** ✅ 唔改 IA/layout philosophy(per ADR-0024 AppShell + 8-tab KB detail);只喺現有 page 加 section/欄/tab。
- **H2** ✅ prototype 用自己 stripped components(per DESIGN_README H2 註);零新 vendor。
- **H4** ✅ profiling 係層 A,無 Tier 2 feature。
- **H7** ✅ **author mockup(ADR-0056 OQ-B 既定),非 implementation;新 mockup reuse 現有 design system 保一致**。
- **Karpathy** ✅ simplicity(reuse primitives 不發明)、surgical(現有 page 加,不推倒)、goal(每 F acceptance + F6 browser 驗)。

---

## §7 Changelog

- 2026-06-15 kickoff — plan active,F1-F6 scope locked;4 落點 R6 grep 核實。
- 2026-06-15 F1-F2 — mock profile data + L2 文件列表 badge(commit `eb0d354`);browser 驗 L2 render 成功;
  用戶 confirm design 方向(中文縮短 label + L2 OK 繼續)。
- 2026-06-15 F3-F5 — L3 文件畫像 section + Settings 分類規則 tab + L1 上載偵測 banner;reuse 既有
  primitives 零 hardcode 顏色(H7 一致);cross-file const 唯一命名避 redeclare。
- 2026-06-15 **F6.2 L1 browser visual DEFERRED**(🚧)— browser/babel 頑固緩存 stale StepExecute transform;
  disk code grep-verified 正確 + 無 syntax error + 同類 primitive 已驗;target 下次 fresh browser session。
- 2026-06-15 **F6.3 PAGE_INVENTORY 說明 DEFERRED**(🚧)— optional doc-sync,留 frontend 實作 phase 或 explicit trigger。
- 2026-06-15 **F5.2 偏離**:plan 寫 `banner-success`,實作改 `banner-info`(ingest running 中非完成,語義更準);
  per-doc detect 用 badge inline 取代「即時 override 連結」(連結去 doc-detail 已有,row 顯示偵測更直接)。
- 2026-06-15 closeout — plan closed WITH L1-BROWSER-VISUAL-DEFERRED CAVEAT,F1-F6 tick(F6.2 L1 + F6.3 🚧),memory append。

# W77 checklist — profiling UI mockup

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。
> 全程 reuse 現有 `styles.css` primitives + `oklch(var(--token))`,零 hardcode 顏色(§3 H7 一致)。

## F1 — mock profile data(`ekp-data.jsx`)

- [x] F1.1 每 indexed doc 加 `profile` object(profile / confidence / fallback_applied / signals 13-field,mirror W76 `DocProfileInfo`);signals 同 profiler rule 一致(P1_imgdense img_density≥0.15 等)
- [x] F1.2 cover P1_sop_imgdense×3 / P1_sop_text×2 / P2_prose / P3_slide_imgdense / 低信心黃旗(security 0.56 fallback)/ unprofiled×4(indexing+failed+queued 自然無)
- [x] F1.3 shape 對齊 backend `DocProfileInfo`(profile / confidence / fallback_applied / signals)

## F2 — L2 文件列表 profile badge(`ekp-page-kb.jsx` Documents table)

- [x] F2.1 讀 Documents table 落點區(line 266-307)現有結構
- [x] F2.2 Chunker 欄後加「Profile」欄:`ProfileBadge` helper(PROFILE_LABELS 6 類縮短 label + 信心度 %);低信心 `badge-warning` 黃旗;unprofiled muted「未分析」
- [x] F2.3 reuse `.badge`/`badge-muted`/`badge-warning`/`badge-dot`/`mono`/`muted`;對齊現有 status/chunker 欄風格

## F3 — L3 文件畫像 section(`ekp-page-doc-detail.jsx` `DocConfigTab` line 410)

- [x] F3.1 讀 DocConfigTab 落點區現有結構(scope banner → tuning card → config-test)
- [x] F3.2 scope banner 後加「文件畫像」card:`DocProfileBadge`(右上)+ signals 透明展示 `stat-grid`(img_density / list_ratio / max_depth / headings / PDF text-layer / paragraphs)
- [x] F3.3 override 下拉 `select`(7 類)+ 低信心 `banner-warning`「待人手確認」+ `ProfileSignal` helper
- [x] F3.4 reuse `.card`/`.stat-grid`/`.stat`/`.field`/`.select`/`.banner-warning`;放 tuning card 之上(解釋「點解套呢個 preset」)

## F4 — Settings 分類規則 tab(`ekp-page-settings-tabs.jsx` `tabs` line 9-15)

- [x] F4.1 讀 tabs array(line 9-16)+ tab body switch 結構
- [x] F4.2 加第 7 tab「文件分類規則」+ `SettingsDocProfiling`:profile→preset mapping `table`(7 profile,值對齊 profile_presets.py + W75 cap=5)+ `ThresholdRow`(confidence 0.70 / img_density 0.15 / too_small 20,對齊 profiler.py)
- [x] F4.3 reuse `.table`/`.card`/`.field`/`.badge`;對齊其他 tab 佈局;**browser 驗 7 tabs + table render 成功**

## F5 — L1 上載偵測 banner(`ekp-page-misc.jsx` `PageUploadWizard` StepExecute)

- [x] F5.1 讀 StepExecute 落點區(line 237)
- [x] F5.2 加 L1「自動文件分類」`banner-info`(W72 profiler 說明)+ 每 indexed doc row 顯示偵測 profile badge + 信心度「已自動套對應 preset」+ `UPLOAD_PROFILE_LABELS`(用 banner-info 非 success — ingest running 中,非完成)
- [x] F5.3 reuse `.banner-info`/`.badge`/`.badge-dot`;對齊現有 wizard step 視覺;**disk code grep 確認正確**(L1 browser visual deferred — 見 F6.2)

## F6 — wire + browser 驗 + closeout

- [x] F6.1 4 處 jsx auto-load 確認(EKP Platform.html line 26/29/33/34;`#settings`→`PageSettingsRich` line 142);F1 mock data wire
- [x] F6.2 **browser 肉眼驗(DD-1)**:**L2**(Documents profile badge)/ **L3**(文件畫像 section + signals stat-grid)/ **Settings**(7 tabs + profile→preset mapping table)三處視覺對齊成功 + console 0 error(no-cache server);🚧 **L1(upload banner)browser visual DEFERRED** — browser/babel 頑固緩存 stale StepExecute transform(多次 fresh navigate + no-cache 8089 server 都攞 old),**disk code grep-verified 正確**(const line 238 + banner 266-270 + per-doc 293-294)+ misc.jsx executed 無 syntax error + 同 L3/Settings 同類 banner-info/badge primitive(已驗 render);target:下次 truly-fresh browser session(清 browser profile cache)
- [ ] 🚧 F6.3 `PAGE_INVENTORY.md` / `DESIGN_README.md` 補 profiling UI 說明 — DEFERRED(optional doc-sync,非阻擋;留 frontend 實作 phase 或 explicit trigger 補;本 phase 核心 = mockup 落地 + 驗證)
- [x] F6.4 closeout:plan closed + progress retro + memory append

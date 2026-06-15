# W78 checklist — profiling frontend 實作

> tick 規則:完成 `→ [x]`;延後 `[ ]` + 🚧 + reason + target(不可刪)。每 commit 對應 ≥1 項(R2)。
> H7-binding:每 F 對齊 `references/design-mockups/` 對應 jsx;reuse 既有 CSS class + `oklch(var(--token))`。

## F1 — TS type 同步(`frontend/lib/api/documents.ts`)

- [x] F1.1 新增 `DocProfileSignals`(13-field mirror backend)+ `DocProfileInfo`(profile/confidence/fallback_applied/signals/profiled_at)
- [x] F1.2 `DocumentSummary` 加 `profile?: string | null` + `profile_confidence?: number | null`
- [x] F1.3 `DocumentDetail` 加 `profile?: DocProfileInfo | null`;`tsc` 0 error ✅

## F2 — L2 文件列表 profile badge(`kb/[id]/page.tsx` `DocumentsTab`)

- [x] F2.1 加 `PROFILE_LABELS`(7 類)+ `ProfileBadge` helper(對齊 mockup ekp-page-kb.jsx:139-159;低信心用 `profile_confidence < 0.7` per §4-1)
- [x] F2.2 Documents table 加「Profile」欄(Tags 後 / Status 前)+ `<ProfileBadge>` cell;reuse `.badge`/`badge-warning`/`badge-muted`/`badge-dot`
- [x] F2.3 unprofiled → `badge-muted`「未分析」;對齊 mockup table 欄風格

## F3 — L3 文件畫像 card(`doc-config-tab.tsx` + parent)

- [x] F3.1 parent `docs/[docId]/page.tsx` line 565 pass `profile={doc.profile}` 落 `DocConfigTab`(props 串接 `DocConfigEditor`)
- [x] F3.2 scope banner 後加「文件畫像」card:`DocProfileBadge`(右上)+ 低信心 `banner-warning`(用 `fallback_applied || confidence < 0.7`)
- [x] F3.3 signals 透明展示 `stat-grid`(img_density / list_ratio / max_depth / headings / pdf 條件 3 項 / paragraphs)+ `ProfileSignal` helper
- [x] F3.4 override `select`(7 類,visual + hint「需 override API 後續」per §4-2)+ profile=null graceful 唔 render;對齊 mockup ekp-page-doc-detail.jsx:453-505

## F4 — Settings 文件分類規則 tab(`settings/page.tsx` + 新 sub-component)

- [x] F4.1 新 `frontend/components/settings/settings-doc-profiling.tsx`:profile→preset mapping `table`(7 profile,值對齊 profile_presets.py + W75 cap=5)
- [x] F4.2 `ThresholdRow`(confidence 0.70 / img_density 0.15 / too_small 20,對齊 profiler.py)+ banner-info;static display per §4-2
- [x] F4.3 `settings/page.tsx` `TABS` 加第 7 entry `doc-profiling`「文件分類規則」+ tab body wire + `<TabBoundary>`;對齊 mockup ekp-page-settings-tabs.jsx:52-147

## F5 — L1 上載偵測 banner(`upload/page.tsx` `StepExecute`)

- [x] F5.1 StepExecute 加「自動文件分類(W72 profiler)」`banner-info` 說明 banner(對齊 mockup ekp-page-misc.jsx:266-273;per-doc 即時 badge adapt per §4-3)
- [x] F5.2 reuse `.banner-info`;放 running banner 後;對齊既有 wizard step 視覺

## F6 — 驗證 + closeout

- [x] F6.1 `pnpm type-check` + `pnpm lint` + `pnpm build` 零 error ✅(15/15 static pages;4 落點 route 全編譯;唯一 warning = pre-existing chat img,與本次無關)
- [ ] 🚧 F6.2 **browser 肉眼驗(DD-1)DEFERRED** — backend + frontend 均 DOWN,browser 驗需起全套 infra(docker postgres + langfuse + azurite + backend venv + frontend dev)+ 現有 KB profile=null 要 re-index 一個 doc 先見「有 profile」視覺(L2 badge / L3 card);三重綠驗(type-check 0 + lint 零新 warning + build ✓ 15/15 pages)已覆蓋 code correctness + H7 用 verbatim 相同 CSS class + mirror mockup JSX 結構 + W77 已 browser 驗過同類 primitive。target:用戶 explicit trigger 起 infra(可順帶 re-index 驗「有 profile」視覺)
- [x] F6.3 closeout:plan closed + progress retro + memory append

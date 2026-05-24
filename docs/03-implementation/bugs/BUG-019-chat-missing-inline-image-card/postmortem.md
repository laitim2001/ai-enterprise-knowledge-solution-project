---
bug_id: BUG-019
report_ref: ./report.md
checklist_ref: ./checklist.md
progress_ref: ./progress.md
status: complete
last_updated: 2026-05-24
severity: Sev2
postmortem_required: true    # PROCESS.md §4.5 — Sev1/Sev2 mandatory
---

# BUG-019 — Postmortem

> Sev2 postmortem per `PROCESS.md §4.5`。Root cause analysis + 5 whys + corrective + preventive。

## TL;DR

W22 frontend presentation rebuild(2026-05-18,per CLAUDE.md §5.7 H7 enforcement)誤判 `InlineImageCard` 為「custom abstraction not matching mockup component breakdown」並 silently 移除,但 mockup `references/design-mockups/ekp-page-chat.jsx` 實際 line 470-498 有 2 處 usage + line 581-617 有完整 function definition。Backend `_proxy_citation_images`(query.py line 182,per BUG-010 W25)正確 wire `Citation.embedded_images[].blob_url` 為 same-origin proxy,但 frontend chat dialogue 無 inline rendering surface — 用戶只能透過右邊 Sources panel `<PanelSourceCard hasImage>` Screenshot button modal popup 開圖,違反 mockup design intent + CLAUDE.md §5.7 H7「100% 完整地把 mockup 的效果重現出來」。

Fix 同 session 內 landed:port mockup function 入 chat/page.tsx + `imageCitations.flatMap(...)` 渲染 per image inline 喺 answer text 之後 + 在 ImageGallery `>=2` collective fallback 之前;file header comment amendment;test assertion 更新對齊新 expected count;3/3 chat-meta-row test pass;backend 13/13 citation pytest preserved。

## Timeline

| Time(2026-05-18 / 2026-05-24)| Event |
|---|---|
| **2026-05-18 W22 D4** | W22 F4 chat presentation rebuild session — 用 mockup-direct rule rebuild `frontend/app/(app)/chat/page.tsx` 對齊 `references/design-mockups/ekp-page-chat.jsx`。Rebuild 過程中 file header comment 寫「`InlineImageCard, CitationPill, FeedbackBar, CragStrip — they were custom abstractions not matching mockup component breakdown`」。**Pre-rebuild verification gap**:5-step pre-active-flip recursive grep(per CLAUDE.md §10 R6 W23 amendment)未對 mockup function-definition matrix verify component classification accuracy;mockup line 581-617 `function InlineImageCard` definition + line 470-498 inline usage 完整存在,但 rebuild session 將其分類為「custom abstraction」並移除 |
| **2026-05-18 W22 closeout** | W22 phase Gate **PASS WITH F8.7+F8.8 TEST-CLEANUP CARRY-OVER**。Per-page H7 7-item self-verify ALL passed(105 cumulative H7 verifies green across 15 routes);per-page user-eye side-by-side verify ALL passed。但**user-eye verify 嘅 visual focus 集中在 layout structure / typography / color tokens / interaction states**,InlineImageCard 屬「conditional render of citation with embedded_images」— 當時 sample query 可能無 image-bearing citation,所以 missing surface 未 surface 為 visual drift |
| **2026-05-22 W25 F1** | W25 F1 ADR-0033 chunker low-value tuning landed,image-bearing chunks 開始通過 chunker 完整流到 index(post-W2 R12 deferred screenshot pipeline 復活)|
| **2026-05-24 W25 D2 morning** | BUG-009/010/011/012/013/014 cascade close + W25 F2 closeout — KB Images tab + frontend rate-limit + screenshot proxy URL chain 全部 wire OK;user 確認 KB Images 顯示 |
| **2026-05-24 W25 D2 ~15:00** | BUG-015/016/017 cascade closure — Document Detail page 3-pane wire(real `<img>` thumbnails + `embedded_images N` badges + cross-section chunker fix)+ Sev2 postmortem;`pytest tests/` 942 pass + 0 fail;user-eye Document Detail page visually verified 8/8 thumbnails correct + 8/8 chunk-section attribution correct |
| **2026-05-24 W25 D2 ~16:00** | User cross-page verify post-Document-Detail confirmation — query「what is high-level architecture」against `sample-document-with-image-1`。 反映:**對話視窗冇 inline 圖片,但 Sources panel screenshot button modal popup 工作**。Screenshots 3 張提交 |
| **2026-05-24 W25 D2 ~16:05** | AI initial probe — `curl /query` print `blob_url[-60:]` truncated:`cb5286ab...png` → 誤判為「raw Azurite SHA256 path」→ propose BUG-018 backend regression(parallel BUG-015 pattern)|
| **2026-05-24 W25 D2 ~16:10** | AskUserQuestion Recommended path:「兩個 BUG 分開 + 順序 fix(BUG-018 backend → BUG-019 frontend)」+「BUG-019 完整 restore per mockup」picks |
| **2026-05-24 W25 D2 ~16:12** | Full URL re-probe corrected misread:`blob_url='/api/backend/kb/sample-document-with-image-1/screenshots/9e9b28abcb5286ab86875f02edc049e3b953295707cd770c15ba8a35dde1c150.png'`(完整 same-origin proxy)→ **BUG-018 disproved not a bug**;backend wiring complete |
| **2026-05-24 W25 D2 ~16:15** | Mockup `ekp-page-chat.jsx` audit confirmed InlineImageCard function definition + 2 usages 完整存在;frontend chat/page.tsx Grep 確認 component 唔存在;file header comment 識別為 misleading |
| **2026-05-24 W25 D2 ~16:30** | BUG-019 docs(report + checklist + progress + postmortem)written;`function InlineImageCard` port from mockup line 581-617 + `MessageRow` 渲染 placement + file header comment amendment + test assertion update |
| **2026-05-24 W25 D2 ~16:40** | `pnpm exec vitest run tests/unit/chat-meta-row.test.tsx` → 3/3 pass;`tsc --noEmit` exit 0;`next lint` clean;`[oklch`=0 preserved;backend `tests/test_citation_enrichment.py + tests/api/test_query_screenshot_proxy.py` 13/13 pass |

**Time-to-detect**:6 days(W22 deploy 2026-05-18 → W25 D2 user-eye verify 2026-05-24);**Time-to-diagnose**:15 min(initial misread → full URL re-probe → mockup audit confirm);**Time-to-fix**:1 hour(diagnose → docs + code + test update + verify gates);**Total user-visible exposure**:6 days(low — no Beta users yet,W22 deploy was local-dev-only;Sev2 severity comes from H7 fidelity regression直接 hide 9-bug image-pipeline cascade 嘅 user-facing 成果)

## 5 Whys

**Why #1**:Chat dialogue 冇 inline image card 顯示(only Sources panel modal popup 工作)?
→ `frontend/app/(app)/chat/page.tsx` 無 `<InlineImageCard>` component definition + 無 render call。

**Why #2**:Why was InlineImageCard removed from chat/page.tsx?
→ W22 F4 chat rebuild session 將 InlineImageCard 同 CitationPill + FeedbackBar + CragStrip 一齊分類為「custom abstractions not matching mockup component breakdown」並 silently delete;file header comment line 47-48 記錄呢個分類 rationale。

**Why #3**:Why did W22 rebuild misjudge InlineImageCard as a custom abstraction?
→ Mockup `ekp-page-chat.jsx` line 581-617 確實有 `function InlineImageCard({title, caption, figure, kind, citation, onOpen})` definition + line 470-498 有 2 處 inline usage 喺 AnswerBody。W22 rebuild session 處理 chat page 時可能集中喺 high-level structure(ChatHeader / ChatThread / MessageRow / SourcesStrip)+ 漏掉 InlineImageCard 嘅 deep-component-level inventory;另外可能 confuse「mockup 用 SyntheticScreenshot placeholder 無 real image」與「component itself is custom abstraction」— 但 mockup component 嘅 *placement intent* + *function shape* 仍然 binding。

**Why #4**:Why did the W22 per-page H7 7-item self-verify + user-eye side-by-side verify not catch this?
→ W22 H7 verify 嘅 visual focus 集中在 layout structure / spacing / typography / color tokens / interaction states / responsive / a11y(7 items per CLAUDE.md §3.2.1 + §5.7)。InlineImageCard 屬「conditional render of citation with embedded_images」— 當時 user-eye verify 嘅 sample state 可能 no image-bearing citation present(W22 期間 W25 F1 chunker fix + screenshot pipeline 未 fully activate,實際 image data 唔 dense)。Conditional-render 缺失喺 zero-data state 下無法 surface — 屬 H7 verification 嘅 inherent data-coverage gap。

**Why #5**:Why does W22 anti-pattern catalog `feedback_design_fidelity.md` 已有 D1+D6+D7+D8+D9 5 patterns 但 missing 呢類 case?
→ D7 = preserve pre-W22 UI **NOT in mockup**(over-preservation)— 反方向 case(remove pre-W22 UI **that IS in mockup**,under-preservation through misjudgment)未 catalog。Catalog 內 patterns 主要 surface from W22 session 內 in-session corrections(D6/D7/D8 都 cite D-N user-eye corrections),少有 long-tail post-W22 regression 觸發。BUG-019 = post-W22 6-day-delay regression detection → 應該 trigger NEW pattern「D11(候選命名)remove pre-W22 UI that IS in mockup」。

## Root Causes(Layered)

1. **Mechanical**:`frontend/app/(app)/chat/page.tsx` 缺 `function InlineImageCard` definition + 缺 render call(W22 silent deletion)
2. **Misjudgment**:W22 rebuild 誤判 InlineImageCard 為「custom abstraction」— 可能因 mockup `<SyntheticScreenshot>` placeholder 同 real-impl `<img>` 嘅 abstraction gap;但 mockup component 嘅 *function shape + placement intent* 仍然 binding per CLAUDE.md §5.7 H7
3. **Process verification gap**:W22 H7 7-item per-page verify focused on visible-state visual fidelity;conditional-render 喺 zero-data state 下無法 surface;data-coverage gap pre-existing in H7 verification protocol
4. **Catalog gap**:`feedback_design_fidelity.md` D1-D9 5-pattern catalog 缺「under-preservation through misjudgment」反向 case(D11 候選命名);long-tail post-W22 regression detection pattern absent
5. **Comment trust gap**:`chat/page.tsx` 自己嘅 file-header comment 寫 InlineImageCard 屬「custom abstraction」— 用 grep 唔會 surface 矛盾;cross-reference mockup 文件 file 至關鍵但 W22 audit 漏掉

## Corrective Actions(this BUG-019 cycle)

1. ✅ **Code fix** — Port `function InlineImageCard({citation, image, citationIdx, figureIdx, onOpen})` from mockup line 581-617 入 `frontend/app/(app)/chat/page.tsx`;adapt `<SyntheticScreenshot>` → real `<img src={image.blob_url} alt={...} />`(BUG-010 / BUG-015 same-origin proxy URL pattern適用)+ 動態 props derived from Citation(title fallback chain / caption sectionPath 串接 / figure sequential)
2. ✅ **Render placement** — `MessageRow` 內 `imageCitations.flatMap(...)` 為每個 imageCitation 嘅每個 embedded image render 1 個 InlineImageCard,放喺 answer text block 之後 + ImageGallery `>=2` collective fallback 之前(per mockup line 470-498 inline-in-answer-body intent)
3. ✅ **File header comment amendment** — Remove「InlineImageCard」from misleading 「abstractions not matching mockup component breakdown」list;加 4-line 解釋 BUG-019 restoration cite mockup line 470-498+581-617 + ImageGallery `>=2` fallback semantics
4. ✅ **Test alignment** — `frontend/tests/unit/chat-meta-row.test.tsx` BUG-007 test assertion 由 `getAllByRole('img').toHaveLength(2)` 改為 `.toHaveLength(4)`(2 InlineImageCard + 2 ImageGallery thumbnails;expected behavior change per BUG-019);comment 加 3-line 解釋 mockup intent
5. ✅ **Verify gates green** — Vitest `chat-meta-row` 3/3 pass / tsc exit 0 / next lint clean / `[oklch`=0 preserved / backend citation pytest 13/13 pass

## Preventive Actions(durable improvements)

1. **Anti-pattern catalog expansion**(future W26+ candidate) — `feedback_design_fidelity.md` 加 D11(候選命名)「remove pre-W22 UI that IS in mockup through misjudgment」pattern;cite BUG-019 為 empirical evidence;cross-ref D7「preserve pre-W22 UI NOT in mockup」作為反方向 case
2. **H7 verification protocol amendment**(CLAUDE.md §5.7 future candidate) — 加 8th item「conditional-render component inventory」:per-page rebuild MUST grep mockup file for all `function X` definitions + cross-check `frontend/.../page.tsx` 有對應 component;data-coverage gap mitigation via mockup function-matrix verify(non-data-dependent)
3. **Comment trust pattern**(future CLAUDE.md §1 Karpathy candidate) — Self-attribution comment(file header「X is custom abstraction」claim)在 H7 audit 期間必須 against mockup verify;不可信賴 file 自我描述 — 必須 cross-reference canonical mockup source
4. **Pre-active-flip R6 recursive scope extension**(future CLAUDE.md §10 R6 amendment candidate) — current R6 = read plan literal + grep code base + surface mismatch + plan §7 changelog + adjust acceptance。Extend with **R6.5 mockup function-matrix verify**:rebuild plan 必須 enumerate mockup function definitions + cross-check vs rebuild target
5. **Diagnostic full-URL discipline**(applicable broadly) — Debug helper print full value first,再 highlight relevant slice;truncation 應該明示 + warn root-cause-investigation context（Karpathy §1.1 think-before-coding empirical lesson）

## Lessons Learned

- **Comment self-attribution unreliable for H7 audit**:`frontend/.../page.tsx` 自我描述「X is custom abstraction」唔可信 — 必須 cross-reference mockup canonical source。Future H7 audit pattern:對 frontend file comment claim 一律 against mockup verify
- **Conditional-render visual regression escape H7 7-item verify**:current 7 items(layout / spacing / typography / color tokens / interaction states / responsive / a11y)assume visible-state coverage;conditional render 喺 no-data state 下無法 surface。H7 protocol 需要加 8th item「conditional-render component inventory」mitigation
- **Mockup function-matrix > component-tree audit**:rebuild session 集中喺 high-level component tree(ChatHeader / ChatThread / MessageRow)容易 miss deep-conditional component(InlineImageCard)。Mockup file grep `function [A-Z]` exhaustive enumeration 應該係 pre-rebuild mandatory step
- **Cascade detection pattern reliability extends past 9-bug streak**:BUG-009-017 + 019 = 10 bugs all surfaced by end-to-end user-eye verify on prior fix's output。Pattern continues to validate — backend pytest + tsc + lint 無法 substitute browser-level smoke;cascade 結構 helps systematic surface
- **Sev2 elevation worthwhile for H7 fidelity regression**:postmortem mandate per PROCESS.md §4.5 forced 5-whys analysis surfaced preventive actions(anti-pattern catalog expansion + H7 protocol amendment + mockup function-matrix audit)— Sev3 informal retro 唔會 crystallize 呢類 process-level improvement
- **Backend wiring vs frontend presentation orthogonality**:`_proxy_citation_images`(BUG-010 W25 backend)完美 wire,frontend 完全不知情而 silently regress。Cross-layer status 必須 surface via user-eye verify — automated test 各 layer 獨立 green 不等於 end-to-end OK

---

**End of postmortem**

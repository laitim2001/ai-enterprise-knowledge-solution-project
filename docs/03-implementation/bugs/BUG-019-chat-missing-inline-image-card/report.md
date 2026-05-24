---
bug_id: BUG-019
title: "Chat 對話視窗冇 inline image card — W22 strict-fidelity rebuild 移除 `<InlineImageCard>` (mockup ekp-page-chat.jsx line 470-498 + 581-617),用戶見唔到 inline 圖片,只能透過 Source panel modal popup 開圖"
severity: Sev2
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 W25 D2 — 9-bug image-pipeline cascade closure verify session;確認 Document Detail page 3 fix(BUG-015/016/017)visually correct 後 user-eye verify chat page 嘗試 query 「what is high-level architecture」,觀察到對話視窗無 inline 圖片顯示,反而打開右邊 sources panel 後點選 Screenshot button 先彈出 modal popup;對應 mockup `ekp-page-chat.jsx` line 470-498 + 581-617 嘅 InlineImageCard inline 設計缺失)"
affects_components: [C10]    # Chat Interface UI
spec_refs:
  - architecture.md §5.4     # Chat View spec
  - architecture.md §4.5     # Citation contract (embedded_images propagation)
  - references/design-mockups/ekp-page-chat.jsx  # H7 canonical visual spec (line 470-498 inline usage + 581-617 function definition)
  - CLAUDE.md §5.7           # H7 Design Fidelity Constraint
related: [BUG-009, BUG-010, BUG-011, BUG-012, BUG-013, BUG-014, BUG-015, BUG-016, BUG-017]
---

# BUG-019 — Chat dialogue 缺 InlineImageCard — W22 rebuild 移除 mockup component

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev2** per CLAUDE.md §5.7 H7 — design fidelity violation discovered post-W22 rebuild;直接打破 user-facing visual surface,屬 H7「不可以大概模仿」嘅 regression。BUG-009/010/011/012/013/014/015/016 cascade 全部 close 後 visually surface — 同 BUG-017 同層 cascade-detection mechanism。

## 1. Symptom

User 喺 Chat page query「what is high-level architecture」against `sample-document-with-image-1` KB,response 帶 citations including `n_chunk-0011`(section「4. High-level architecture」,1 embedded image post-BUG-017 fix)。對話視窗顯示:

- ✅ AI synthesis answer text 正常出
- ✅ Footer 顯示「2 citations」(假設無「· N with screenshots」suffix 顯示,因為 imageCitations=1 但 implementation conditional 係 `length > 0` should display — 待驗證 imageCitations.length 實際值)
- ❌ **答案文字之後完全冇 inline image card 顯示**
- ❌ 用戶要打開右邊 Sources sidebar panel,搵到嗰個 citation card,再點「Screenshot」button → 開 modal popup 先見到圖片

Mockup `references/design-mockups/ekp-page-chat.jsx` line 470-498 明確要求 InlineImageCard inline 喺 answer body 內:
```jsx
{/* ── Inline image card #1 ── */}
<InlineImageCard
  title="Posting definitions screen — exchange rate type field"
  caption="Citation [1] · Section 4.2 Multi-Currency Setup"
  figure="figure 1"
  ...
  onOpen={() => onOpenScreenshot(cit1)} />
```

而 `function InlineImageCard` 完整 definition 喺 line 581-617。

## 2. Reproduction Steps

1. 確保 backend `/query` 已 wire `_proxy_citation_images`(per BUG-010 / query.py line 182,verified W25 D2 live probe:`blob_url='/api/backend/kb/{kb_id}/screenshots/{sha}.png'` 完整 same-origin proxy)
2. Ingest `sample-document-with-image-1` (post-BUG-017 chunker fix → 88 chunks,8/8 correct picture attribution)
3. 打開 `http://localhost:3001/chat`,select KB `sample-document-with-image-1`
4. Type query「what is high-level architecture」+ Send
5. **Expected**:對話視窗 answer text 之後出現至少 1 個 inline image card(per mockup line 470-498 pattern),展示 chunk 內嵌嘅 screenshot
6. **Actual**:對話視窗 only show text + footer + (sidebar mode) right Sources panel
7. 唯一可以見圖嘅路徑 = 打開 Sources panel → 點 PanelSourceCard 嘅 Screenshot button → modal popup

## 3. Root Cause

`frontend/app/(app)/chat/page.tsx` 嘅 W22 strict-fidelity rebuild session(per W22 5-pattern empirical-finding catalog `feedback_design_fidelity.md`)移除咗 `<InlineImageCard>` component,並在 file header comment(line 47-48)寫:

```
* InlineImageCard, CitationPill, FeedbackBar, CragStrip) — they were custom
* abstractions not matching mockup component breakdown. (ImageGallery — ...
```

呢個 comment 屬 **misunderstanding** — mockup `ekp-page-chat.jsx`:
- line 470-498 — 2 處 `<InlineImageCard>` usage inline 喺 AnswerBody
- line 581-617 — `function InlineImageCard({title, caption, figure, kind, citation, onOpen})` 完整 function definition

InlineImageCard **明確係 mockup component**,not「custom abstraction」。W22 rebuild 誤判 component 屬性 → 移除咗呢個 inline rendering,所以即使 backend `embedded_images` 已 wire 正確,frontend 對話視窗都無 surface。

呢個係 **W22 D7 anti-pattern 嘅 reverse case**(D7 = preserve pre-W22 UI **NOT in mockup**;呢度 = **remove pre-W22 UI that IS in mockup**)。

`<ImageGallery>` (`>=2` images) + `<SourcesStrip>` + `<PanelSourceCard>` 都仍然保留並 work,但都唔 cover「single image inline visible 喺對話視窗主流」嘅 user expectation。

## 4. Scope

- ✅ Backend:NO change(BUG-010 `_proxy_citation_images` + `Citation.embedded_images` 完整 wire,W25 D2 live probe verified)
- ❌ Frontend `frontend/app/(app)/chat/page.tsx`:NEED port `<InlineImageCard>` function from mockup + render imageCitations sequentially after answer text + before ImageGallery / SourcesStrip
- ❌ Frontend file header comment line 47-48:NEED amend — remove「InlineImageCard」from「not matching mockup component breakdown」list(misleading)

## 5. Severity Rationale

**Sev2** per CLAUDE.md §5.7 H7 Design Fidelity Constraint:

- H7 trigger:「**寫 / 改前端 page、component、layout 嘅 implementation 同對應 mockup 任何一項唔對齊**」+「**Mockup detail 不清晰(無法判斷正確視覺 / 互動)**」+「**Mockup 偏離**」
- 影響 user-facing chat surface,user 主要 query workflow 內無 inline 圖片
- 9-bug image-pipeline cascade(BUG-009-017)花咗 W25 D1-D2 投入解決圖片 surface;呢個 frontend regression 隱藏咗成個 backend chain 嘅成果
- 直接打破 W25 phase「image-association deep-fix」嘅 user-visible 目標
- Sev2 elevation vs Sev3 因為:不單係 cosmetic polish,而係 functional rendering surface 缺失;但 NOT Sev1 因為 workaround 存在(Sources panel screenshot button)

## 6. Acceptance for Fix

- [ ] Port `function InlineImageCard` from `references/design-mockups/ekp-page-chat.jsx` line 581-617 入 `frontend/app/(app)/chat/page.tsx`
- [ ] Adapt mockup `<SyntheticScreenshot kind={kind} compact />` → real `<img src={image.blob_url} alt={image.alt_text} />`(BUG-010 / BUG-015 proxy URL pattern 適用 — Citation.embedded_images[0].blob_url 已係 same-origin proxy)
- [ ] Adapt mockup hard-coded props → 動態 derive from Citation:
  - `title` = `image.alt_text` (fallback `citation.chunk_title` or `'Screenshot'`)
  - `caption` = `Citation [${citation.idx}] · ${citation.section_path.join(' › ')}`
  - `figure` = `figure ${imageIdx}`(sequential count)
  - `onOpen` = wire to 既存 `onOpenScreenshot` handler(modal popup,同 PanelSourceCard 一樣)
- [ ] Render placement:answer text block 之後 + ImageGallery / SourcesStrip 之前;為每個 `imageCitations` element render 1 個 `<InlineImageCard>`
- [ ] 保留 `<ImageGallery>` `>=2` gate(per mockup line 354-357 — mockup 兩者並存,InlineImageCard 為 each + ImageGallery 為 collective list)
- [ ] File header comment line 47-48 移除「InlineImageCard」from misleading list
- [ ] H7 per-page verification:對齊 mockup line 470-498 + 581-617(視覺 + 互動 + props 完整對應)
- [ ] Vitest unit test:render 1+ imageCitations 應該見 InlineImageCard,onOpen click 觸發 onOpenScreenshot
- [ ] User-eye runtime verify:re-query「what is high-level architecture」應該見 inline image card 對話視窗內(BUG-019 fix 後 final visual confirmation)

## 7. Related

- BUG-009-017 cascade(W25 D1-D2 image-pipeline 9-bug closure)
- ADR-0031 Option B(W20 F3 server-side Conversation History + advanced chat surfaces — 原本含 InlineImageCard;W22 rebuild regression session 後 implementation status 偏離)
- CLAUDE.md §5.7 H7 Design Fidelity Constraint
- `feedback_design_fidelity.md` memory(W22 5-pattern empirical-finding catalog — 呢 bug 加多 1 個 pattern「D11 misjudge mockup component as 'custom abstraction'」候選)
- W22 phase `progress.md` Day-1 F4 chat rebuild session(若有 file-level review,確認 W22 commit 對 InlineImageCard 嘅 specific decision rationale)

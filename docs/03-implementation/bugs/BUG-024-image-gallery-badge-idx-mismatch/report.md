---
bug_id: BUG-024
title: "ImageGallery thumbnail 嘅 numeric badge 用 subset position `i+1`,同 ScreenshotModal `latestAssistantCitations.findIndex+1` + CitationPill numbering 不一致 — user 見「外面 1,內面 2」"
severity: Sev3
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 W25 D2 cont — 試 referenced screenshot 點擊發現 outside badge `1` vs modal header idx `2`)"
affects_components: [C10]    # Chat Interface UI
spec_refs:
  - architecture.md §5.5      # Chat view layout
  - references/design-mockups/ekp-page-chat.jsx:621-664 # ImageGallery "Referenced screenshots"
  - CLAUDE.md §5.7 H7         # Design fidelity (numbering must match across surfaces)
related: [BUG-019, BUG-020, BUG-021]
---

# BUG-024 — ImageGallery thumbnail badge idx 同 ScreenshotModal / CitationPill 不一致

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev3** — 視覺不一致,user 困惑「點解我 click `1` 嘅 thumbnail,modal header 卻 show `2`」;但唔 break 功能,citation context 仍 reachable。Sev3 per PROCESS.md §4.5(visual / cosmetic / minor UX confusion;no Sev2 postmortem)。

## 1. Symptom

User report:
> 「另外reference screenshot 在外面顯示是1 - Referenced screenshots 1, 但是點進去之後, 顯示為 2 - 2
>  4. High-level architecture
>  DCE_Integration_Platform_Implementation_Plan · chunk #11」

解析:
- **外面**(`ImageGallery` thumbnail):numeric badge top-left 顯示 `1`,header「Referenced screenshots [1]」(count)
- **內裡**(`ScreenshotModal`):header idx badge 顯示 `2`
- **互相矛盾**:user expectation = thumbnail badge `1` ↔ modal idx `1` 對應同一 screenshot

## 2. Reproduction Steps

1. 開 `/chat`,選擇 KB 有 image 嘅 KB(例:`sample-document-with-image-1`)
2. 輸入查詢令 retrieval 取多於 1 個 citation,而其中某 citation 唔係第 1 個 position 但有 embedded image
3. ImageGallery section 「Referenced screenshots」彈出 1 個 thumbnail,badge 顯示 `1`(因為 imageCitations 入面 position 0)
4. Click thumbnail
5. ScreenshotModal 開啟,header badge 顯示 `2`(因為 latestAssistantCitations 入面 position 1)
6. **觀察**:1 ≠ 2,user 困惑

## 3. Root Cause

`frontend/app/(app)/chat/page.tsx`:

**ImageGallery thumbnail badge**(line 1828):
```tsx
{citations.map((c, i) => {
  // ...
  <span style={{ /* badge */ }}>{i + 1}</span>
  // i = position in `citations` prop = imageCitations subset
})}
```

**ScreenshotModal idx**(line 522-526):
```tsx
idx={(() => {
  const found = latestAssistantCitations.findIndex(
    (c) => c.chunk_id === modalImage.citation.chunk_id,
  );
  return found >= 0 ? found + 1 : modalImage.citation.chunk_index + 1;
})()}
// found = position in `latestAssistantCitations` = full citations
```

兩個 idx 計算 base 唔同:**imageCitations subset** vs **full citations array**。

**範例**:assistant response 有 3 citations,其中只第 2 個(`latestAssistantCitations[1]`)有 embedded image。
- `imageCitations = [latestAssistantCitations[1]]`(length 1)
- ImageGallery thumbnail badge = `0 + 1 = 1`
- ScreenshotModal idx = `1 + 1 = 2`
- 結果:外面 `1`,內面 `2` ❌ 不一致

**Canonical numbering**:per mockup `ekp-page-chat.jsx`,所有 surface(CitationPill inline / SourcesStrip footer / ImageGallery thumbnail / ScreenshotModal header / PanelSourceCard sidebar)numeric badge 應該 reference 同一個 citation idx — 即 `latestAssistantCitations` position + 1。因為 CitationPill = 1, 2, 3, ... 喺 answer body 順序出現,user 期望 cross-reference 「screenshot 2」 同 「pill 2」 指向同一 citation。

ImageGallery 一直 mistakenly 用 subset position,呢個 bug 自 BUG-019 ImageGallery restore + BUG-021 `>=1` unification 都 inherit 落嚟 — 之前因為 imageCitations subset 通常同 full citations 順序一致(image-bearing chunks 常排前),visual mismatch 罕見 surface;呢次 query response shape 令 subset position 0 vs full position 1 露白。

## 4. Scope

- ✅ Frontend `frontend/app/(app)/chat/page.tsx`:
  - `ImageGallery` 加 `allCitations: Citation[]` prop(full message.citations)
  - Thumbnail badge `{i + 1}` → `{allCitations.findIndex(a => a.chunk_id === c.chunk_id) + 1}`
  - Callsite(line 1256)pass `allCitations={message.citations}`
- ✅ ScreenshotModal idx 計算 unchanged — 已用 findIndex+1
- ✅ CitationPill numbering unchanged — `idx={i + 1}` over `latestAssistantCitations` direct iteration
- ✅ Mockup fidelity preserved(numbering convention 同 mockup `ekp-page-chat.jsx` line 621-664 一致)

## 5. Severity Rationale

**Sev3** per PROCESS.md §4.5 —

- Visual inconsistency only,功能 reachable(click thumbnail 仍正確開個 modal 顯示對應 image + citation context)
- User UX confusion + 不符 numbering convention
- No data loss,no security implication,no workflow blocker
- Postmortem NOT required per PROCESS.md §4.5 Sev3

## 6. Acceptance for Fix

- [x] **T1** — `ImageGallery` 加 `allCitations: Citation[]` prop;thumbnail badge computed via `allCitations.findIndex(a => a.chunk_id === c.chunk_id) + 1`(`?` defensive fallback if miss)
- [x] **T2** — Callsite(MessageRow inside)pass `allCitations={message.citations}`
- [ ] **T3** — Reproduce step verify:ImageGallery thumbnail badge `N` ↔ ScreenshotModal header badge `N`(same N for same chunk_id)— pending user-eye refresh + re-query test
- [x] **T4** — `tsc --noEmit` exit 0 + `next lint` clean(only pre-existing `<img>` warning unrelated)

## 7. Related

- BUG-019(InlineImageCard restore — same image cluster session)
- BUG-020(CitationPill restore + ImageGallery / SingleScreenshotStrip)
- BUG-021(ImageGallery `>=2` → `>=1` unification — bug latent inherited from this gate change but surface depends on data shape)
- CLAUDE.md §5.7 H7 — numbering must match across surfaces per mockup convention

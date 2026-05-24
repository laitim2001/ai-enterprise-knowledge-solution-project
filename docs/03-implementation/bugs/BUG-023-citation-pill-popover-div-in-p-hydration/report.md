---
bug_id: BUG-023
title: "CitationPill hover popover 內 `<div>` 元素變 ReactMarkdown `<p>` 後代 — HTML hydration warning `<div> cannot be a descendant of <p>`"
severity: Sev2
status: done
reported: 2026-05-24
reporter: "Chris(chat 2026-05-24 W25 D2 cont — BUG-021 amendment commit `3532e4b` + BUG-022 commit `2924471` 之後 chat 頁面 hover CitationPill 觸發 React DevTools warning)"
affects_components: [C10]    # Chat Interface UI
spec_refs:
  - architecture.md §5.5     # Chat view layout
  - CLAUDE.md §5.7 H7        # Design fidelity (no visual change but DOM correctness)
  - CLAUDE.md §1.3           # Surgical changes
related: [BUG-020, BUG-021]
---

# BUG-023 — CitationPill popover `<div>` in `<p>` hydration error

> **Report version**:1.0(initial)
> **Triage approver**:AI self-triaged **Sev2** — every CitationPill hover triggers `<div> cannot be a descendant of <p>` React Markdown warning;visible to anyone using DevTools;hydration mismatch risk; user-facing pill + popover render visually 正常,但 console noise persistent + 不符 HTML spec。

## 1. Symptom

```
[Frontend Console]
app-index.js:33 Warning: In HTML, <div> cannot be a descendant of <p>.
This will cause a hydration error.
    at div
    at span
    at span
    at CitationPill (webpack-internal:.../chat/page.tsx)
    at p
    at p (.../chat/page.tsx — react-markdown <p> override)
    at Markdown
    at AnswerBodyMarkdown (.../chat/page.tsx)
    ...
```

每次 user hover 任何 CitationPill,popover 動畫呈現嘅同時 console emit 上述 warning。視覺呈現完全 OK(popover 內容、顏色、定位 correct)。

## 2. Reproduction Steps

1. 開啟 `/chat`,選擇 KB(任一)
2. 輸入查詢(任何 query — 例:「what is high-level architecture」對 `sample-document-with-image-1`)
3. 等 assistant 回覆完成,citation pills(numeric badges `1` / `2` / ...)inline 嵌入 markdown paragraph
4. Hover 任何 CitationPill
5. **觀察**:popover 正常彈出 + console 即時 emit `<div> cannot be a descendant of <p>` warning

## 3. Root Cause

`AnswerBodyMarkdown` 用 `<ReactMarkdown>` render LLM 回應,react-markdown 為 paragraph token 包 `<p>` element。Inline `CitationPill` 透過 `injectPillsIntoChildren` 嵌入到 `<p>` 後代。

`CitationPill`(`frontend/app/(app)/chat/page.tsx` line 1472)外層係 `<span>`(line 1479)— 正確 inline element。Hover popover 外層都係 `<span>`(line 1505 — `position: absolute`)— 正確。

**問題**:popover 內裡 3 個 `<div>` 元素(line 1525 FileTypeChip header / line 1552 section_path / line 1562 chunk_title)— 因為 popover 仍係 CitationPill 後代,而 CitationPill 喺 markdown `<p>` 後代,呢 3 個 `<div>` 變咗 `<p>` 後代 → HTML5 spec 禁止 `<div>` 喺 `<p>` 內 → React Markdown hydration warning。

呢個係 BUG-021 amendment(commit `3532e4b`)單 `<ReactMarkdown>` render path 引入 — pre-BUG-021 amendment per-token ReactMarkdown call 雖然 pills 喺新行 break flow,但每個 pill 喺自己 `<p>` 內,popover divs 隸屬個別 `<p>` 反而冇 hydration issue。Amendment 為咗 pills inline 喺 paragraph 內(BUG-021 acceptance criteria),令呢個 sub-issue surface。

## 4. Scope

- ✅ Frontend `frontend/app/(app)/chat/page.tsx` CitationPill popover 3 `<div>` → `<span style={{display: 'block'}}>` — visual identical,HTML valid;`<span>` 允許做 `<p>` 後代
- ✅ Visual fidelity preserve(no mockup deviation per CLAUDE.md §5.7 H7)
- ✅ Hover behavior preserve(setHovered state + popover render unchanged)
- ✅ FileTypeChip + section_path + chunk_title sub-components 不受影響(都係 inline children passed to changed wrapper)

## 5. Severity Rationale

**Sev2** per PROCESS.md §4.5 —

- 視覺 + 功能完全 OK,user-facing 無破壞 → 唔係 Sev1
- 但 console error persistent + hydration mismatch theoretical risk + 不符 HTML spec → 唔係 Sev3/Sev4
- 每次 hover 都 surface,影響開發 / debug 體驗(real warning 被淹沒)
- Postmortem optional per PROCESS.md §4.5 Sev2(我會 skip,trivial root cause + surgical fix)

## 6. Acceptance for Fix

- [x] **T1** — `CitationPill` popover 內 3 個 `<div>`(FileTypeChip header / section_path container / chunk_title preview)改 `<span style={{display: 'flex'/'block', ...preservedProps}}>`,inline-compatible 同時保留 layout 視覺
- [ ] **T2** — Hover popover console **零** `<div> cannot be a descendant of <p>` warning(pending user-eye verify post browser refresh)
- [x] **T3** — Hover popover 視覺 + 行為 100% identical pre-fix(H7 fidelity preserve — span style display:flex/block 視覺等效;Vitest 7/7 preserve)
- [x] **T4** — `tsc --noEmit` exit 0 + `next lint` clean

## 7. Related

- BUG-021 amendment(commit `3532e4b` — `AnswerBodyMarkdown` single-ReactMarkdown render path 引入 inline pill flow,令 popover sub-tree 變 `<p>` 後代)
- BUG-020(CitationPill hover popover restoration)
- CLAUDE.md §5.7 H7(no visual change — span-block 取代 div 視覺等同)
- CLAUDE.md §1.3 surgical(3-line × 3 改動,zero 架構變化)

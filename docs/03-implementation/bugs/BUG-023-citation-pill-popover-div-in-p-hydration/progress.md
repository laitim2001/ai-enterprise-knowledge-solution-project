---
bug_id: BUG-023
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-023 — Progress

> Sev2 surgical fix per Karpathy §1.3。Postmortem optional per PROCESS.md §4.5 — skip,trivial mechanism。

## Day 1 — 2026-05-24

### Investigation

User-eye verify post BUG-021 amendment commit `3532e4b` + BUG-022 commit `2924471` chat 頁面 hover CitationPill 觸發:

```
Warning: In HTML, <div> cannot be a descendant of <p>.
This will cause a hydration error.
    at div
    at span
    at span
    at CitationPill (.../chat/page.tsx)
    at p
    at p (.../chat/page.tsx)
    at Markdown
    at AnswerBodyMarkdown
```

Source inspection `frontend/app/(app)/chat/page.tsx` CitationPill function(line 1472)confirmed:
- 外層 `<span>`(line 1479)+ popover 外層 `<span>`(line 1505)— 兩層都係 inline element ✅
- Popover 內 3 個 `<div>`(line 1525 FileTypeChip header / line 1552 section_path / line 1562 chunk_title)— 直接 cause

ReactMarkdown 為 paragraph 包 `<p>`,`CitationPill` 透過 `injectPillsIntoChildren` 嵌入 `<p>` 後代;popover divs 連帶變咗 `<p>` 後代 → HTML5 spec violation。

### Decisions

- **D1.1** — Sev2 elevation:console warning persistent + hydration risk;但視覺 + 功能完全 OK 唔到 Sev1。Postmortem optional per Sev2 → skip(trivial root cause + surgical fix,no preventive pattern 值得 catalog 入 `feedback_design_fidelity.md`)。
- **D1.2** — Fix Option (A) span-block selected over Option (B) Portal — Karpathy §1.3 surgical 3-line × 3 改動 vs Portal 要 createPortal + ref + JS bounding rect computation;span-block visual + behavior identical;Portal over-engineered for popover that doesn't suffer overflow:hidden clipping。
- **D1.3** — Span `style={{display: 'flex' / 'block'}}` works correctly;`<span>` 可以 set 任何 `display` value via inline style(HTML semantic vs CSS layout independent)— line 1525 header 保 `display: 'flex'` 結構 unchanged,只係 outer tag div → span。

### Code changes

| 檔案 | 改動 |
|---|---|
| `frontend/app/(app)/chat/page.tsx` | CitationPill popover 內 3 `<div>` → `<span>` + 適配 inline comment cite BUG-023 |

### Verify gates

- Hover CitationPill in `/chat` → console zero `<div> cannot be a descendant of <p>` warning(post-fix verify)
- Hover popover visual fidelity preserved(side-by-side verify)
- `tsc --noEmit` exit 0
- `next lint` clean

### Commits

(pending — 1 commit:`fix(chat): CitationPill popover div→span:block — BUG-023 hydration warning`)

### Retro

- **Cascade detection extends to console warnings**:BUG-019 → BUG-020 → BUG-021 → BUG-022 visual / functional cascade;BUG-023 surface via DevTools console hover — new cascade detection mechanism(complement BUG-022 console-error-detection sub-mode per BUG-022 postmortem lessons)。
- **HTML spec compliance Karpathy §1.1 think-before-coding miss**:BUG-021 amendment design phase 應該 audit「popover divs 會 nested where in DOM」— 但因為 popover 用 absolute positioning,視覺上 「飛出嚟」,容易誤以為脫離 `<p>` ancestor,實際 DOM tree 仍係 descendant。Lesson:**absolute positioning ≠ DOM ancestry decoupling** — HTML spec apply on DOM tree,not visual rendering。
- **No preventive catalog entry**:trivial sub-pattern,unlikely cumulative;don't pollute `feedback_design_fidelity.md` 5-pattern catalog with sub-pattern noise per memory file discipline。

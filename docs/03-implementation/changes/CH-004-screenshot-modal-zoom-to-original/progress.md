---
change_id: CH-004
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# CH-004 — Progress

> Daily progress + retro。

## Day 1 — 2026-05-24

### Done

**T1-T6 ScreenshotModal zoom feature**:

- Added `isZoomed: boolean` useState at ScreenshotModal function top
- Added `useEffect` ESC keydown handler — registers on `isZoomed=true` mount,cleanup on flip/unmount → zero risk of leaked listener
- Image inside 2-col layout:`onClick={() => setIsZoomed(true)}` + `cursor: 'zoom-in'` affordance
- Conditional zoom overlay rendered as fragment sibling of outer dialog(z-index 200 over modal z-index 100):dark backdrop + viewport-capped image + dual close mechanisms(backdrop / image click / ESC)
- 8-line block comment cite CH-004 + spec §1.3 rationale + R1 ESC handler scoped guarantee

**Verify gates(automated)**:

- `pnpm exec tsc --noEmit` → exit 0
- `pnpm exec next lint` → clean(only pre-existing line 1673 `<img>` warning unrelated to CH-004)
- `pnpm exec vitest run tests/unit/chat-meta-row.test.tsx` → 7/7 pass(no regression)

### Decisions

- **D1.1** — `objectFit: 'contain'` over strict natural-pixel + scroll → simpler UX,大圖 viewport-cap;真 1:1 pixel + scroll 留 future enhancement(per spec §2.2 out-of-scope)
- **D1.2** — Inline JSX overlay(non-Portal)over `createPortal` from `react-dom` → ScreenshotModal z-index 100,zoom overlay z-index 200 already wins stacking context;Portal 過度 architectural,Karpathy §1.2
- **D1.3** — ESC keydown via `useEffect` scoped to `isZoomed=true` → 不影響 underlying modal(no ESC handler)+ 不 leak listener post-unmount
- **D1.4** — No new test(per spec §4.2)— Sev3-equivalent enhancement,manual user-eye verify acceptable;automated coverage 既有 chat-meta-row 7/7 preserve

### Verify gates(automated, T7-T9)

- T7 ✅ tsc exit 0
- T8 ✅ next lint clean
- T9 ✅ Vitest 7/7

### User-eye verify(T10-T12 — deferred, post-commit)

- [ ] T10 — click image → zoom overlay appears
- [ ] T11 — click backdrop / image / ESC → unmount,underlying modal preserved
- [ ] T12 — cursor affordances:zoom-in modal,zoom-out overlay

### Blockers

無。

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| T1-T6 implementation | 1-2 | ~0.5 | -0.5 to -1.5(localized scope + Karpathy §1.3 surgical pattern) |
| T13-T14 docs + commit | 0.5 | ~0.3 | -0.2 |

Compression factor ~3-5×(consistent with W25 D1+D2 micro-task pattern)。

### Commits

(pending — 1 commit:`feat(chat): ScreenshotModal zoom-to-original — CH-004`)

### Retro

- **Karpathy §1.3 surgical ideal scope**:6-7 line state + useEffect + inline overlay JSX + 8-line comment = ~30 line LOC change;maximum effect minimum code;`createPortal` / pinch gesture / multi-zoom level 全 over-engineered,user 唔 ask 唔做(spec §2.2 explicit out-of-scope)
- **Z-index hierarchy stays implicit**:200 = arbitrary > 100;若 future Cmd+K palette / toast 衝突,可往上推 250 / 300;暫無 collision,Karpathy §1.2 唔提前 budget hierarchy convention
- **User progressive disclosure pattern**:default 2-col layout(mockup-faithful)preserved + zoom on demand = best-of-both ergonomics + inspection workflow;mockup 唔禁 zoom 屬 design-stage expansion 空間(per H7 spirit + ADR-0025 / 0026 等 design-stage expansion 先例)

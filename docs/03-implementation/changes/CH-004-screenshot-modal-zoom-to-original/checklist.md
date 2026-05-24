---
change_id: CH-004
spec_ref: ./spec.md
status: done
last_updated: 2026-05-24
---

# CH-004 — Checklist

> Derived from `spec.md §3 Acceptance Criteria` + §4 Implementation Plan。

## Implementation

- [x] **T1** — `ScreenshotModal` add `const [isZoomed, setIsZoomed] = useState(false);` at function top
- [x] **T2** — `ScreenshotModal` add `useEffect` ESC keydown handler scoped to `isZoomed=true`(register window listener on mount,cleanup on flip/unmount;`e.stopPropagation()` defensive)
- [x] **T3** — Image inside 2-col layout:`onClick={(e) => { e.stopPropagation(); setIsZoomed(true); }}` + `cursor: 'zoom-in'` style;`e.stopPropagation()` to prevent backdrop onClose race
- [x] **T4** — Return wrapped in fragment `<>...</>` + sibling conditional `{isZoomed && <ZoomOverlay />}` after outer dialog `</div>`
- [x] **T5** — Inline ZoomOverlay JSX:dark backdrop `oklch(0 0 0 / 0.92)` + z-index 200 + image natural size capped via `objectFit: 'contain' maxWidth/Height: 100%` + dual-close(backdrop / image click / ESC)
- [x] **T6** — Block comments cite CH-004 spec §1.3 rationale + R1 ESC scoped guarantee + spec §2.2 strict 1:1 pixel deferral note

## Verification

- [x] **T7** — `pnpm exec tsc --noEmit` exit 0
- [x] **T8** — `pnpm exec next lint` clean(only pre-existing line 1673 `<img>` warning unrelated)
- [x] **T9** — `pnpm exec vitest run tests/unit/chat-meta-row.test.tsx` 7/7 pass(no regression)

## User-eye verify(deferred, post-commit)

- [ ] **T10** — Click image in ScreenshotModal → zoom overlay appears at higher z-index(over 2-col modal)
- [ ] **T11** — Click backdrop OR image OR press ESC → zoom overlay unmounts,underlying 2-col modal preserved + clickable
- [ ] **T12** — Cursor affordance:modal image hover = `zoom-in`;zoom backdrop + image hover = `zoom-out`

## Closeout

- [x] **T13** — `progress.md` Day 1 entry + retro
- [ ] **T14** — Commit:`feat(chat): ScreenshotModal zoom-to-original — CH-004`
- [x] **T15** — Update `spec.md` frontmatter `approved → done` post-commit

---

## Cross-Cutting

- [x] **C1** — H1 architectural change:N/A
- [x] **C2** — H2 vendor change:N/A
- [x] **C3** — H5 security:N/A
- [x] **C4** — H6 test coverage:既有 Vitest 7/7 preserved;no new test added(per spec §4.2 rationale)
- [x] **C5** — H7 design fidelity:2-col mockup baseline 100% preserved;zoom = NEW affordance on top(design-stage expansion spirit)
- [x] **C6** — Commit references progress entry per CLAUDE.md §10 R2(will tag on commit)

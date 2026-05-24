---
change_id: CH-004
title: "ScreenshotModal click-image-to-zoom — full-resolution overlay layer above existing 2-col dialog"
status: done              # draft | proposed | approved | active | done | cancelled
created: 2026-05-24
approved: 2026-05-24
completed: 2026-05-24
target_completion: 2026-05-24
affects_components: [C10]    # Chat Interface UI
spec_refs:
  - architecture.md v6 §5.5                 # Chat citation surface
  - references/design-mockups/ekp-page-chat.jsx:1068-1121  # ScreenshotModal 2-col mockup (W22 + BUG-021 amendment baseline)
  - CLAUDE.md §5.7 H7                       # Design fidelity — zoom is NEW affordance on top, NOT mockup deviation
  - CLAUDE.md §1.2 / §1.3                   # Karpathy simplicity + surgical
related: [BUG-021, BUG-023, BUG-024]
---

# CH-004 — ScreenshotModal zoom-to-original feature

> **Spec version**:1.0(initial)
> **Owner**:AI(implementer)/ Chris(approver)
> **Approved by**:Chris(chat 2026-05-24 — pick (a)「兩個都做」implies CH-004 approved + proceed)

---

## 1. Context (Why)

### 1.1 Trigger

User chat 2026-05-24 W25 D2 cont:
> 「原來現在點進去圖片之後, 因為有了右邊的內容, 所以圖片反而縮小了, 會看不清楚, 可以加一個功能, 在點擊圖片後可以放大到原圖大小的嗎?」

**Background**:BUG-021 amendment commit `3532e4b`(W25 D2)將 ScreenshotModal 由 single-pane 重 build 為 mockup-faithful 2-col layout(image left ~1.6fr / side panel ~1fr with section_path / chunk_id / chunk_title preview / Open in Document Detail link)per `references/design-mockups/ekp-page-chat.jsx:1068-1121`。Visual fidelity restoration 對齊 mockup,**但** 副作用係 image 被壓縮到 ~62% modal width(1.6 / (1.6+1) = 0.615);若原 image resolution 高,user 睇唔清細節。

### 1.2 Why a feature(not Bug-fix)

- **Mockup-compliant baseline**:current 2-col layout 係 H7 mockup-faithful(per BUG-021 amendment design intent)— 唔係 bug、唔係 visual drift。
- **Enhancement on top**:zoom = NEW affordance on top of preserved mockup 2-col layout — 屬 design-stage enhancement(per CLAUDE.md §5.7 H7 「design-stage expansion 例外」spirit:mockup 唔禁 zoom 功能,user-pick add 屬 progressive enhancement)。
- **PROCESS.md §1 classification**:`"add Y option"` signal = **Change**(not Bug-fix, not Trivial — has UI state + new overlay component + ESC handler)。

### 1.3 Why NOT just enlarge modal default size

- Mockup 2-col layout 係 the canonical citation-context view(section_path + chunk_id + Open-in-Doc-Detail link 為 inspection workflow design)— 預設大佔 viewport 會破壞「modal 上下文 + 可關閉返回 chat」UX flow。
- Zoom-on-click = progressive disclosure pattern(預設 minimal,需要時 user click to escalate)— fits read-then-inspect workflow without compromising default ergonomics。

---

## 2. Scope

### 2.1 In scope

- `frontend/app/(app)/chat/page.tsx`:`ScreenshotModal` 加 `isZoomed` state + click-image handler + conditional zoom overlay layer
- Zoom overlay:full-viewport fixed-position dark backdrop + image rendered at natural size(`maxWidth: 100%` + `maxHeight: 100%` + `objectFit: contain` 避免 super-wide image overflow viewport — practical compromise vs strict natural pixel)
- Close mechanism:click anywhere on backdrop OR press ESC OR click image again
- Z-index hierarchy:zoom overlay `z-index: 200` > existing modal `z-index: 100`(zoom 蓋過 modal but stay below browser dev overlay)
- Cursor affordance:image in 2-col modal `cursor: 'zoom-in'`;zoomed image + backdrop `cursor: 'zoom-out'`
- Accessibility:zoom overlay `role="dialog" aria-modal="true"`;ESC handler;focus 退回 underlying modal close button

### 2.2 Out of scope

- Pan/pinch zoom gestures(touch device extensions — Tier 2)
- Multi-step zoom levels(50% / 100% / 200% / fit — over-engineered for ScreenshotModal use case)
- Image rotation / annotation(KB-image-library tool scope,not chat citation viewer)
- Server-side image preview generation / thumbnails(already exist — current proxy serves full-res image directly per BUG-009 `screenshot_proxy_url`)
- Touch-device tap-to-zoom alternative gestures(mouse-first PoC scope)

### 2.3 Behavior contract

| Surface | Pre-CH-004 | Post-CH-004 |
|---|---|---|
| Hover over image in modal | Plain cursor | `cursor: zoom-in` |
| Click on image in modal | (no effect) | Zoom overlay mounts at z-index 200 |
| Zoom overlay backdrop | (didn't exist) | `oklch(0 0 0 / 0.92)` dark, click → close |
| Zoom overlay image | (didn't exist) | Natural-size `objectFit: contain` capped at viewport;`cursor: zoom-out` |
| Press ESC in zoom overlay | (no effect) | Zoom overlay unmounts;underlying modal preserved |
| Press ESC in modal(no zoom) | (no effect — modal X button only) | (unchanged — out-of-scope CH-004) |

---

## 3. Acceptance Criteria

- [x] **AC1** — `ScreenshotModal` 加 `isZoomed: boolean` state;default `false`;click image setter `setIsZoomed(true)`
- [x] **AC2** — Zoom overlay 條件 render(`{isZoomed && <ZoomLayer />}`);overlay = `position: fixed inset: 0` + dark backdrop + `z-index: 200`
- [x] **AC3** — Image inside overlay:`maxWidth: 100%` + `maxHeight: 100%` + `objectFit: 'contain'`(viewport-capped natural size)
- [x] **AC4** — Click backdrop OR image OR press ESC → `setIsZoomed(false)`(unmount overlay,underlying 2-col modal preserved)
- [x] **AC5** — Cursor affordances:modal image `cursor: 'zoom-in'`;zoom overlay backdrop + image `cursor: 'zoom-out'`
- [x] **AC6** — Accessibility:zoom overlay `role="dialog" aria-modal="true" aria-label="..."`;ESC keydown handler scoped to overlay mount(useEffect register/cleanup)
- [x] **AC7** — H7 fidelity preserve:2-col modal default layout 100% unchanged(zoom = NEW layer ON TOP,no mockup baseline modification)
- [x] **AC8** — `tsc --noEmit` exit 0 + `next lint` clean
- [x] **AC9** — Vitest `chat-meta-row.test.tsx` 7/7 preserve(zoom feature scope unrelated to meta-row tests)

---

## 4. Implementation Plan

### 4.1 Code change(`frontend/app/(app)/chat/page.tsx` ScreenshotModal function)

1. Add `const [isZoomed, setIsZoomed] = useState(false);` at top of function
2. Add `useEffect` for ESC keydown handler scoped to `isZoomed` truthy state(cleanup on unmount/state-flip)
3. Image `<img>` inside 2-col layout:add `onClick={() => setIsZoomed(true)}` + `cursor: 'zoom-in'` style
4. After outer dialog `<div onClick={onClose}>` closing,add sibling conditional `{isZoomed && <ZoomOverlay />}`(rendered as part of ScreenshotModal return — outer fragment wrapper)
5. ZoomOverlay inline JSX:
   - Outer `<div role="dialog" aria-modal="true" aria-label="..." onClick={() => setIsZoomed(false)} style={...}>`(z-index 200, dark backdrop, fixed inset 0, flex center, cursor zoom-out, padding 16)
   - Inner `<img src={image.blob_url} alt="..." onClick={(e) => { e.stopPropagation(); setIsZoomed(false); }} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', cursor: 'zoom-out' }} />`

### 4.2 No test added(Sev3-equivalent enhancement scope)

- Vitest `chat-meta-row.test.tsx` 唔 cover ScreenshotModal interactions(out of meta-row + ImageGallery scope)— preserve 7/7 unchanged
- New test 需要 elaborate mock(useState + mock image url + DOM event simulation)— per Karpathy §1.2 simplicity,feature 屬 progressive UI affordance,manual user-eye verify acceptable
- 真有 regression 風險係 zoom overlay 影響 underlying modal — manual verify 確認

### 4.3 Verify gates(no automated test)

- Manual user-eye verify:click image → zoom overlay appear at higher z;click backdrop / image / ESC → unmount;underlying 2-col modal preserved + clickable

---

## 5. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | ESC keydown handler 衝突 underlying modal ESC handler(若 modal 自己有 ESC handler)| Low | Low | Inspect ScreenshotModal pre-fix — current code 無 ESC handler;CH-004 ESC scoped to `isZoomed=true` only → 不影響 modal close(modal close 仍由 X button + backdrop click) |
| R2 | Z-index 200 collide other floating UI(toast / Cmd+K palette)| Low | Low | Toast typically z-50 or z-1000;Cmd+K is `<GlobalSearch>` 自己 layer;200 預留中 — 若衝突 可調 250 / 300 |
| R3 | Big image(超 4K width)overflow viewport even with objectFit:contain | Low | Low | `objectFit: contain` 保證 fit-to-viewport,即使「原圖大小」implementation = viewport-capped;若真要 1:1 pixel + scroll,Future enhancement(out of scope CH-004) |
| R4 | Modal 內 React Portal 需要 escape stacking context | Low | Low | ScreenshotModal `z-index: 100`,zoom 200 > 100 already wins stacking — no Portal needed unless 將來 nested dialog conflict |

---

## 6. Related

- BUG-021 amendment commit `3532e4b` — established 2-col ScreenshotModal baseline that this CH-004 enhances on
- BUG-023 + BUG-024 commit `250fdc6` — same chat page surface follow-up batch
- CLAUDE.md §5.7 H7 — visual fidelity for 2-col preserved;zoom = progressive enhancement on top
- CLAUDE.md §1.2 / §1.3 — simplicity(no Portal / no pinch gesture)+ surgical(state + overlay + cursor + ESC handler localized to ScreenshotModal function)
- W25-image-association-deep-fix — same session as Day 2 cont presentation cluster(BUG-019-024 cascade)

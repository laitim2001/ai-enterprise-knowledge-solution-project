---
bug_id: BUG-019
report_ref: ./report.md
status: done
last_updated: 2026-05-24
---

# BUG-019 — Checklist

> Derived from `report.md §6 Acceptance for Fix`。Sev2 H7 fidelity regression。

## Investigation

- [x] **T1** — Backend `/query` live probe verified `citations[].embedded_images[].blob_url` 完整 same-origin proxy URL(`/api/backend/kb/{kb_id}/screenshots/{sha}.png`);backend wiring confirmed working post-BUG-010 + BUG-015 cascade
- [x] **T2** — Mockup `references/design-mockups/ekp-page-chat.jsx` audit:line 470-498(2 處 InlineImageCard usage inline 喺 AnswerBody)+ line 581-617(`function InlineImageCard` definition);mockup intent = inline image card per imageCitation,並存 ImageGallery `>=2` collective list
- [x] **T3** — `frontend/app/(app)/chat/page.tsx` file header comment line 47-48 identified as misleading — InlineImageCard 被 mis-classified 為「custom abstraction not matching mockup component breakdown」但實際係 mockup component

## Fix — Code

- [x] **T4** — `frontend/app/(app)/chat/page.tsx`:NEW `function InlineImageCard({citation, image, citationIdx, figureIdx, onOpen})` 加在 ImageGallery function 之前(line 1311-1316 comment 區域之前);ported from mockup line 581-617;`<SyntheticScreenshot>` → real `<img src={image.blob_url} alt={image.alt_text || title}>` 對齊 BUG-010 same-origin proxy URL;props 動態 derived(title fallback chain / caption sectionPath 串接 / figure sequential)
- [x] **T5** — `MessageRow` 內 line 1174 區域:`imageCitations.flatMap(...)` 為每個 imageCitation 嘅每個 embedded image render 1 個 `<InlineImageCard>`,placement 在 answer text 之後 + 在 ImageGallery `>=2` gate 之前(對應 mockup line 470-498 inline-in-answer-body intent)
- [x] **T6** — Wire `onOpen={() => onOpenScreenshot(c, image)}` 用既存 modal popup handler(同 PanelSourceCard 一樣 wire `<ScreenshotModal>`)
- [x] **T7** — File header comment line 46-50 amendment:remove「InlineImageCard」from misleading 「abstractions not matching mockup component breakdown」list + 加 4-line 解釋 BUG-019 restoration cite mockup line 470-498+581-617 + ImageGallery `>=2` fallback semantics

## Tests

- [x] **T8** — `frontend/tests/unit/chat-meta-row.test.tsx` BUG-007 test assertion 由 `getAllByRole('img').toHaveLength(2)` 改為 `.toHaveLength(4)`(2 InlineImageCard + 2 ImageGallery thumbnails;per BUG-019 expected behavior change);comment 加 3-line 解釋 mockup intent
- [x] **T9** — `pnpm exec vitest run tests/unit/chat-meta-row.test.tsx` → **3/3 pass**;隔離 chat-kb-sync + kb-detail + register tests 都 pass(in stash-pop verify)— OneDrive worker-timeout flakiness pre-existing per W23 D2.4 finding(setup.md §8.7),非 BUG-019 introduced

## Verification

- [x] **T10** — `pnpm exec tsc --noEmit` → exit 0
- [x] **T11** — `pnpm exec next lint` → clean(only 1 pre-existing `@next/next/no-img-element` warning on `<img>` element,跟 BUG-015 ImageThumb 既存 pattern 一致 — Next.js `<Image />` 需要 loader config 處理 same-origin proxy,Karpathy §1.2 simplicity wins)
- [x] **T12** — `grep '\[oklch' frontend/app/(app)/chat/page.tsx` → **0 hits**;milestone preserved through BUG-019 changes
- [x] **T13** — Live `/query` probe pre-fix:`citations[].embedded_images[0].blob_url='/api/backend/kb/sample-document-with-image-1/screenshots/9e9b28abcb5286ab86875f02edc049e3b953295707cd770c15ba8a35dde1c150.png'`(verified W25 D2 backend wiring correct;same-origin proxy → frontend 直接 fetch 攞到 bytes per BUG-010 / BUG-013 / BUG-014 chain)

## Runtime Verify

- [ ] 🚧 **T14** — Explicit user-eye runtime verify on chat page InlineImageCard 渲染 + onOpen modal popup 工作 — consolidated 喺 post-commit walkthrough(per BUG-009-017 cascade pattern)

## Closeout

- [x] **T15** — `progress.md` closeout summary + Day 1 entry + retro
- [x] **T16** — `postmortem.md` Sev2 mandatory per PROCESS.md §4.5
- [x] **T17** — `report.md` status `triaged → done`;`checklist.md` `in-progress → done`
- [x] **T18** — Commit + push

---

## Cross-Cutting

- [ ] **C1** — H1 architectural change:N/A(no spec §3/§4 component change — pure presentation restoration per mockup)
- [ ] **C2** — H5 security:N/A
- [ ] **C3** — H6 test coverage:frontend chat NOT in mandatory backend pipeline coverage list;但 Vitest unit test 加(T8)為 BUG-fix regression seed
- [ ] **C4** — H7 design fidelity:THIS BUG = H7 regression fix;per-page verify gate must pass(mockup line 470-498 + 581-617 對齊)
- [ ] **C5** — Commit references progress entry per R2
- [ ] **C6** — Memory `feedback_design_fidelity.md` 加 D11 pattern「misjudge mockup component as 'custom abstraction'」候選(待 postmortem 結論再 confirm pattern 命名)

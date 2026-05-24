---
bug_id: BUG-019
report_ref: ./report.md
checklist_ref: ./checklist.md
status: done
last_updated: 2026-05-24
---

# BUG-019 — Progress

> Bug-fix workflow per `PROCESS.md §4`。Sev2 → postmortem mandatory at closeout。

## Day 1 — 2026-05-24

### Investigation

W25 D2 cont session(post 9-bug image-pipeline cascade closure BUG-009-017),user 確認 Document Detail page BUG-015/016/017 fix 全部 visually verified。然後 user-eye verify chat page query「what is high-level architecture」against `sample-document-with-image-1` KB,觀察到:

- 對話視窗 answer text + footer 正常
- ❌ 答案文字之後完全冇 inline image card
- ✅ 打開右邊 Sources sidebar panel → 點 PanelSourceCard 嘅「Screenshot」button → modal popup 開圖

User feedback:
> 「**在chat頁面嘗試測試時, 可以看到相關的chunks是有顯示對應的screenshort 記錄, 但是在chat頁面的對話視窗內沒有直接顯示圖片**」
> 「**反而是在打開右邊source panel後, 點選 screenshort 後, 就會彈出圖片**」

**Diagnostic chain**:

1. **Backend wiring check via live probe**(initial)— `curl -X POST /query` 印 `blob_url[-60:]` truncated:
   ```
   citations=1
     cit0: chunk=n_chunk-0011 section=['4. High-level architecture'] embedded_images=1 | imgs=['cb5286ab86875f02edc049e3b953295707cd770c15ba8a35dde1c150.png']
   ```
   AI initial misread:「raw Azurite blob path,missing screenshot_proxy_url override」→ suspect BUG-018 backend regression
2. **Full URL re-probe**(corrected)— 印 `blob_url` 完整字串:
   ```
   cit0: imgs=[]
   cit1: imgs=['/api/backend/kb/sample-document-with-image-1/screenshots/9e9b28abcb5286ab86875f02edc049e3b953295707cd770c15ba8a35dde1c150.png']
   ```
   **Backend wiring 完整正確** — `query.py` line 182 `_proxy_citation_images` per BUG-010 pattern。BUG-018 NOT A BUG。
3. **Frontend code audit** — Read `frontend/app/(app)/chat/page.tsx`:
   - Grep `InlineImageCard|ImageGallery|embedded_images` → no `InlineImageCard` definition or usage
   - File header comment line 47-48 寫:`InlineImageCard, CitationPill, FeedbackBar, CragStrip) — they were custom abstractions not matching mockup component breakdown`
   - `<ImageGallery>` 仍存在但 gated on `imageCitations.length >= 2`(line 1175)→ single-image case 完全冇 inline render
   - `<PanelSourceCard>` 有 `{hasImage && <Screenshot button>}` → 解釋 user 點 Source panel 可以開圖
4. **Mockup `references/design-mockups/ekp-page-chat.jsx` audit** — Grep `image|screenshot`:
   - line 470-478 + 490-497 — 2 處 `<InlineImageCard>` usage inline 喺 AnswerBody hard-coded
   - line 581-617 — `function InlineImageCard({title, caption, figure, kind, citation, onOpen})` 完整 function definition
   - **Mockup intent**:每個 image-bearing citation 在 answer body 內 inline render 1 個 image card,並存 `<ImageGallery>` (`>=2` gate per mockup line 354-357) 作 collective list
5. **Root cause confirmed**:W22 strict-fidelity rebuild session 誤判 `InlineImageCard` 為「custom abstraction」並移除;但 mockup 明確有 function definition + 2 usages → **W22 D7 anti-pattern reverse case**(D7 = preserve pre-W22 UI **NOT in mockup**;此 = remove pre-W22 UI that **IS in mockup**)

### Decisions

- **D1.1** — 初始 misread blob_url truncation 導致 false-positive 「BUG-018 backend regression」classification。Full URL re-probe 後 disprove。Karpathy §1.1 think-before-coding lesson:**printing truncated output 容易誤判 root cause,debug helper 應該 print full value first,再 highlight relevant slice**。Task #163 BUG-018 closed without code change(not a bug)
- **D1.2** — User 選擇 Recommended path:**兩個 BUG 分開開 + 順序 fix**(but BUG-018 disproved 後只剩 BUG-019)。BUG-019 scope = **完整 restore per mockup**(Recommended over Minimal single-image-only)— 即:imageCitations.map(...) 為每個 image-bearing citation render 1 個 InlineImageCard,並保留 ImageGallery `>=2` collective fallback per mockup spec
- **D1.3** — 分類 Sev2 per CLAUDE.md §5.7 H7 — H7 fidelity regression elevated above Sev3 informal polish;同 BUG-017 Sev2 同層;postmortem mandatory per PROCESS.md §4.5
- **D1.4** — Adapt mockup hard-coded props:
  - `title` ← `image.alt_text || citation.chunk_title || 'Screenshot'`(fallback chain)
  - `caption` ← `Citation [${citationIdx}] · ${section_path.join(' › ')}`
  - `figure` ← `figure ${imageIdx}`(monotonic 1-indexed across all imageCitations[i].embedded_images[j])
  - `onOpen` ← wire existing `onOpenScreenshot(citation, image)` handler(同 PanelSourceCard 一樣 modal popup)
  - `kind` mockup prop NOT NEEDED(SyntheticScreenshot 係 mockup placeholder;real 用 `<img src={image.blob_url} alt={image.alt_text} />`)
- **D1.5** — Render placement = answer text block 之後 + before ImageGallery / SourcesStrip / FeedbackBar(per mockup line 470-498 inline-in-answer-body intent;real impl 無法 hard-code 插喺特定 paragraph 之間 — fallback to「answer 後 sequential render」per Karpathy §1.2 simplicity)
- **D1.6** — Preserve `<ImageGallery>` `>=2` gate intact;mockup 兩者並存,InlineImageCard 為 each + ImageGallery 為 collective list — 同 mockup design 一致

### Code changes(pending)

| 檔案 | 改動 |
|---|---|
| `frontend/app/(app)/chat/page.tsx` | NEW `function InlineImageCard` port from mockup line 581-617;`MessageRow` 內加 `imageCitations.map((c, idx) => c.embedded_images.map(...))` 渲染,placement 在 answer text 之後 + ImageGallery 之前;file header comment line 47-48 amendment 移除「InlineImageCard」+ 加 1-line BUG-019 cite |
| `frontend/tests/unit/chat-inline-image-card.test.tsx` | NEW Vitest unit test:render with 1+ imageCitations → InlineImageCard 出現 + click → onOpenScreenshot called |

### Verify gates(pending)

- `pnpm exec vitest run` → all chat-related tests pass(no regression);NEW test pass
- `tsc --noEmit` → exit 0
- `next lint` → clean
- `Grep '[oklch'` against `frontend/app/(app)/chat/page.tsx` → 0 hardcoded oklch literals(milestone preserved)
- User-eye runtime verify post-restart frontend dev server

### Commits(pending)

_(see commit footer — `fix(chat): restore InlineImageCard inline image rendering — BUG-019 + H7 W22 regression`)_

### Retro

- **Diagnostic full-URL re-probe before code change paid off**:initial probe truncated `blob_url[-60:]` → misread root cause as「BUG-018 backend regression」(raw Azurite URL,缺 screenshot_proxy_url override)。 Re-probe with full URL print disproved 之後,正確 reclassify 為 frontend-only issue。Karpathy §1.1 think-before-coding lesson:**debug helper 應該 print full value first,再 highlight relevant slice**;truncation 容易掩蓋已 wired 嘅 layer
- **Mockup audit 比 file-grep 更有 authority**:`frontend/app/(app)/chat/page.tsx` 自己嘅 file-header comment 寫 InlineImageCard 屬「custom abstraction not matching mockup component breakdown」— 用 grep `frontend/app/...` 唔會 surface 矛盾。Cross-reference mockup `references/design-mockups/ekp-page-chat.jsx` line 470-498(usage)+ 581-617(function definition)立即發現 misjudgment。**Future H7 audit pattern:對 frontend file 嘅 comment claim 一律 against mockup verify**,唔好相信 self-attribution
- **`flatMap` over nested `map`**:imageCitations 有 0-N citations × 0-N embedded_images per citation。Initial 試圖用 nested map 結果 figureIdx counting 麻煩;改用 `flatMap` 預先 flatten 之後 single `.map` rendering + `flatIdx + 1` 一致順序。比 nested 用 sequential counter ref 更清楚
- **W22 anti-pattern catalog 加 D11 候選**:呢個 bug 屬 D7「preserve pre-W22 UI not in mockup」反向 case — D11「remove pre-W22 UI that IS in mockup」候選命名。Postmortem 內進一步定義
- **Cascade pattern 連續 11 個 BUG validated end-to-end user-eye verify reliability**:BUG-009-017 全部係 user-eye verify on prior fix's output surface;BUG-019 同樣由 user-eye verify(post BUG-015/016/017 confirmation 後)surfaced。Backend pytest + tsc + lint passed at each step but cannot catch presentation regression — browser-level smoke 係唯一可靠 detector
- **Sev2 elevation 正確判斷**:屬 H7 fidelity regression(不只 cosmetic polish),postmortem mandatory per PROCESS.md §4.5 forced 5-whys analysis;preventive actions(W22 anti-pattern catalog expansion + comment cross-ref audit pattern)會 cascade 影響 future Wave C+ work

### Postmortem

Sev2 postmortem written per `PROCESS.md §4.5` — see `./postmortem.md`(full timeline + 5 whys + layered root causes + corrective + preventive + lessons learned)。

### Closeout — 2026-05-24 W25 D2 cont

- Frontend `InlineImageCard` function landed `frontend/app/(app)/chat/page.tsx`(per mockup line 581-617)+ `MessageRow` 渲染 placement(per mockup line 470-498)+ file header comment amended
- `frontend/tests/unit/chat-meta-row.test.tsx` BUG-007 test assertion 由 2 → 4 imgs(BUG-019 expected behavior change)
- `pnpm exec vitest run tests/unit/chat-meta-row.test.tsx` → **3/3 pass**
- `pnpm exec tsc --noEmit` exit 0;`pnpm exec next lint` clean(1 pre-existing warning unchanged);`[oklch`=0 milestone preserved
- Backend pytest `tests/test_citation_enrichment.py` + `tests/api/test_query_screenshot_proxy.py` → **13/13 pass**(backend wiring untouched per Karpathy §1.3 surgical)
- BUG-019 frontmatter `in-progress → done`;checklist 16/18 ticked(T14 🚧 user-eye runtime verify pending consolidated walkthrough per BUG-009-017 cascade pattern)+ cross-cutting 6/6 ticked
- Commit:`fix(chat): restore InlineImageCard inline image rendering — BUG-019 + H7 W22 regression`
- 10-bug image-pipeline + chat-rendering cascade closure:BUG-009/010/011/012/013/014/015/016/017/019 all closed within W25 D1-D2 multi-session sequence(2026-05-22 to 2026-05-24;BUG-018 disproved not a bug)

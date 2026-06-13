# W71 — progress(inline-image-interleave)

## Day 1 — 2026-06-13

### Kickoff + R6 grounding
- 用戶對 W70 AC4 判決拍板:「W71 go(chat 文字+圖片交織 render)」。
- R6 plan-text grounding(發現記 plan 頭注 + §7 changelog):
  - mockup 三段行號(`AnswerBody:443-500` / `InlineImageCard:581-618` /
    `ImageGallery:621-664`)全部核實無誤;
  - **`InlineImageCard` 前端已存在**(`chat/page.tsx:1697`,BUG-019 restore 對齊
    mockup)— W71 scope 收窄做「移位 + 解析層」,唔係起新元件;
  - 末尾卡堆現狀 = `:1282-1292` `cappedImages.map`(BUG-026 A deduped list);
    surviving 圖集 = `dedupeCitationImages` + `selectInlineImages`;
  - `⟦CITn⟧` citation placeholder pipeline(`AnswerBodyMarkdown:1437+`)= 交織
    實作現成 precedent;
  - copy 按鈕(`:2371`)係未 wire 視覺 stub — DD-8 影響面收窄(手動 select-copy
    攞 DOM 文字天然乾淨)。
- 三件套建立(plan / checklist / progress),plan status = active。
- 下一步:F1 解析層(`parseInlineImageMarkers` + membership + dup strip +
  vitest)。

### F1 — 解析層 ✅
- `lib/chat/inline-image-markers.ts`:`COMPLETE_MARKER_PATTERN` 加 capture group
  攞 marker body(`\[IMG#([^\]\s]*)\]`;strip 照用 `.replace(…, '')` 唔受影響)+
  `imageMarkerKey(checksum)`(sha8 = 前 8 hex,keying 集中)+ `InlineSegment`
  型(text / image)+ `parseInlineImageMarkers(text, validSha8)`。
- **語義**:valid+new marker → 斷段出 image segment;sha8 ∉ validSha8(capped
  out / decorative-filtered / malformed / 幻覺)→ strip 並把前後文字併入同一 run
  (用 running buffer,唔 flush);同一 sha8 第二次(dup)→ strip(anchored set)。
  空 validSha8 → 單 text 段且文字 == `stripInlineImageMarkers(text)`(零回歸路)。
- **streaming 唔郁**:`stripInlineImageMarkers` 原封不動;parse 只完成態用(避免
  版面跳動,module note 寫明)。F2 串流期間照行 strip 單塊 render。
- vitest 14 新(27 passed 全綠)/ tsc 0 / eslint 0 / prettier clean。
- 下一步:F2 render 層(`AnswerBodyMarkdown` 按 segments 交織 reuse 現有
  `InlineImageCard` + 末尾堆改 un-anchored only + figure 連續編號;R1 技術路徑
  二選一決定記 progress + H7 fidelity check)。

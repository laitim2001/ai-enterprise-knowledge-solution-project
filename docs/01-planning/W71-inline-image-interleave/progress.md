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

### F2 — render 層(交織)✅
- **R1 決策(關鍵)**:睇 W70 saved answer 實況 — 標記係喺**深層巢狀 step list
  內**(`1. **AR04...** [IMG#55224e29]` / `  2. Set the parameter. [IMG#6dd75fad]`),
  唔似 mockup `AnswerBody` 嗰種「平層 3 步 list + 之後一張卡」。
  - ❌ **segments-split**(F1 segment 各自 render separate ReactMarkdown):會打散
    巢狀 list 嘅 `1./1.1/1.1.1` 編號(每段變 fresh list)。
  - ❌ **path(a)lift-to-block**:成個程序係**一個**巢狀 list,把卡提升到 block
    邊界 = 全部卡 clump 喺 list 之後,完全失去 per-step 交織意義。
  - ✅ **採 path(b)refined**:`[IMG#sha8]` → `⟦IMG:sha8⟧` placeholder(經 F1
    `parseInlineImageMarkers` 決定 membership + dedup,валid+first→placeholder,
    其餘 strip)→ **單一** ReactMarkdown 保留全巢狀結構 → `p`/`li` override
    `harvestImageTokens` 抽 token + render `InlineImageCard` 喺 block 層。
    `<figure>` 入 `<li>` 係合法 flow content(BUG-023 限制只係 `<div>`-in-`<p>`),
    入 `<p>` 用 fragment-sibling(卡喺段後,對齊 mockup `:470/490`「卡喺 block 間」)。
- **分區 + figure 編號**:`planAnchoredImages(content, capped)`(放 `citation-images.ts`,
  用 F1 parse + `imageMarkerKey`)→ `inlineBySha8`(anchored,figure = marker 序)
  + `trailing`(un-anchored,figure 接續)。**單一計算**,AnswerBodyMarkdown 同
  末尾堆共用,編號零跳號。
- **末尾堆**:`cappedImages.map` → `trailingImages.map`(只 render un-anchored;
  anchored 唔重複,ADR-0055 顯示語意)。`ImageGallery` 全量總覽 + `totalCount`
  完全唔郁。
- **零回歸**:streaming 或 knob OFF(無標記)→ `inlineBySha8` 空 → `interleave`
  false → 行原 `stripInlineImageMarkers` + 全 `cappedImages` trailing = pre-W71
  bit-identical。
- **placement 微妙位**(記低,F4 肉眼覆核):標記喺有子 list 嘅父 step 上時,卡
  render 喺該 `<li>` 所有內容(含子 list)之後 — 喺正確 step 內但喺子步之後。
  Tier 1 可接受(mockup 無呢個 case);F4 覺得礙眼先調。
- **Tests**:`planAnchoredImages` 7 條(無標記全 trailing / 單 anchor / marker 序
  定 figure / dup anchor 一次 / 非 surviving sha8 ignore / 無 checksum 必 trailing /
  連續編號)入 `citation-images.test.ts`;render smoke 3 條新檔
  `chat-inline-image-interleave.test.tsx`(標記變 figure 卡 + 無爛字 + gallery 全量 /
  membership strip 無爛卡 / 無標記 = pre-W71)。
- **Gates**:tsc 0 / eslint 0(唯一 warning `<img>` pre-existing)/ prettier clean;
  vitest 隔離 74 全綠(含 chat-meta-row img-count 無回歸);full suite 8 fail 全
  `Test timed out in 5000ms`(超載並行 flake,environment setup 795s),逐個隔離 pass
  (register / chat-meta-row 已驗)。
- 下一步:F3(DD-8 copy 按鈕 wire strip 文字 + backend RAGAs answer 路徑 strip)。

### F3 — DD-8 copy 路徑 ✅
- **copy 按鈕**(前端):`FeedbackBar` 本來係 unwired stub(只有 `<Copy>` icon,
  無 onClick)。加 `content` prop + `handleCopy` —
  `navigator.clipboard.writeText(answerToCopyText(content))`;新 `answerToCopyText`
  strip `[IMG#…]`(`stripInlineImageMarkers`)+ `[chunk-…]` citation 標記 → copy
  出乾淨 prose(渲染見到嘅文字,非 raw token)。clipboard 不可用(insecure
  context / denied)→ try/catch 吞,按鈕不變;`copied` state 令 title 暫轉「Copied」。
- **RAGAs answer**(backend):新 `backend/generation/inline_image_markers.py`
  `strip_inline_image_markers`(lenient `\[IMG#[^\]\s]*\]`,與前端
  `lib/chat/inline-image-markers.ts` 對稱,放 generation 因 marker 係該層概念 +
  `prompt_builder._MARKER_RULE` 喺度)。入 `ragas_evaluator.py` 兩個評分點:
  `_ascore_all`(strip 一次 → faithfulness `response` + answer_relevancy
  `response` + reference fallback 共用)+ config-test `_eval`(strip 後再判空)。
  knob-ON 答案標記不再當 unsupported claim 污染 faithfulness。
- **Tests**:backend 7 strip(單/多/畸形/citation 不碰/fast-path/空/marker-only
  strip 後空)+ ragas_runner 13 = 20 passed;ruff + mypy strict clean。前端 copy
  render test(streamQuery 答案含 `[IMG#a1b2c3d4]` + `[chunk-chunk-1]` → click
  copy → `clipboard.writeText` 收文字 `[IMG#`/`[chunk-` 皆無、prose 保留);
  interleave suite 4 passed;tsc 0 / eslint 0 / prettier clean。
- **DD-8 close**:DEFERRED_REGISTER 由結構性表移去「已 Close」表(證據記低);
  export 路徑(目前無 backend export 端點)future 沿用同一 helper,不在此 close 範圍。
- 下一步:F4(knob ON 實跑 drive-images-1 肉眼核交織 + 九 query report-級 sanity +
  AC1-AC6 自評)。

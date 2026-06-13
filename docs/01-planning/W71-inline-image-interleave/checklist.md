# W71 — checklist(inline-image-interleave)

## F1 — 解析層
- [x] `lib/chat/inline-image-markers.ts` 加 `parseInlineImageMarkers(text, validSha8)` → `InlineSegment[]`(text / image)+ `imageMarkerKey(checksum)` helper(sha8 = checksum 前 8 hex,keying 集中一處)
- [x] membership 驗證:sha8 ∉ validSha8 → strip 並合併前後文字(無空卡);同一 sha8 第二次出現 → strip(dup dedup,anchored set);malformed body 同 capped-out 同一條 strip 路
- [x] streaming 行為不變(`stripInlineImageMarkers` 原封不動;parse 只用於完成態,module note 寫明)
- [x] vitest 14 新(2 imageMarkerKey + 12 parse:membership / dup 至多 anchored 一次 / 相鄰標記 back-to-back / 無標記退化單 text 段 / 空 membership == strip 結果 / 首標記無空前段 / 完成態尾截當字面);現有 13 strip tests 全綠(共 27 passed);tsc 0 / eslint 0 / prettier clean

## F2 — render 層(交織)
- [x] `AnswerBodyMarkdown` 交織:**R1 決策 = placeholder + 單一 ReactMarkdown + block 層注入**(`[IMG#sha8]`→`⟦IMG:sha8⟧` 經 F1 parse 決定 membership/dedup,`p`/`li` override `harvestImageTokens` 後 render `InlineImageCard`)— 因真實標記喺深層巢狀 step list 內,segments-split 會打散巢狀編號;path(a)lift-to-block 會把全部卡 clump 喺成個 list 之後。`<figure>` 入 `<li>` 合法(BUG-023 限制只係 `<div>`-in-`<p>`),入 `<p>` 用 fragment-sibling
- [x] 末尾 inline 卡堆改 `trailingImages`(un-anchored only;`planAnchoredImages` 分區)
- [x] figure 編號全答案連續(anchored 先 marker 序、trailing 後 doc 序;`planAnchoredImages` 單一計算)
- [x] `ImageGallery` 全量總覽不變(`cappedImages` + `totalCount` 唔郁);knob OFF / 無標記 → `inlineBySha8` 空 → strip 路 + 全 trailing = pre-W71 bit-identical
- [x] tsc 0 / eslint 0(唯一 warning = `<img>` pre-existing)/ vitest 74 隔離全綠(planAnchoredImages 7 + interleave render 3 + chat-meta-row img-count 無回歸);full suite 8 fail 全部 `timed out 5000ms` 超載 flake,隔離逐一 pass;H7 fidelity:`InlineImageCard` 元件原樣 reuse、卡擺位對齊 mockup `AnswerBody`(卡喺答案流 block 之間)

## F3 — DD-8 copy 路徑
- [x] copy 按鈕 wire:`FeedbackBar` 加 `content` prop + `handleCopy`(`navigator.clipboard.writeText(answerToCopyText)`;`answerToCopyText` strip `[IMG#…]` + `[chunk-…]` → 乾淨 prose;clipboard 不可用 try/catch 吞);render test click → clipboard 收乾淨文字
- [x] backend RAGAs answer 評分路徑 strip 標記:`backend/generation/inline_image_markers.py` `strip_inline_image_markers`(lenient,與前端對稱)入 `ragas_evaluator.py` `_ascore_all`(faithfulness + answer_relevancy + reference fallback)+ config-test `_eval`;7 strip pytest + mypy strict clean
- [x] DEFERRED_REGISTER DD-8 → 已 Close(證據:backend 20 passed / 前端 copy render test / tsc 0 / eslint 0;export 路徑 future 同一 helper)

## F4 — 驗證(knob ON 實跑)
- [ ] drive-images-1 實跑肉眼核:標記位置出卡 / 末尾無重複 / gallery 全量 / 無爛字無空卡
- [ ] 九 query 報告級 sanity(標記全消費;可用 `scripts/run_marker_placement.py` 答案 + 前端 parse 對拍)
- [ ] AC1-AC6 自評記 progress

## F5 — 收爐
- [ ] user-guide 同步(02/03 提交織顯示行為 + DD-8 caveat 解除)
- [ ] memory 更新(`project_inline_image_markers_w70` 接力位 close)+ plan closeout + retro

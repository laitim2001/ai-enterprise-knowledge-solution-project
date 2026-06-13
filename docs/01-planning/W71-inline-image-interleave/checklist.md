# W71 — checklist(inline-image-interleave)

## F1 — 解析層
- [x] `lib/chat/inline-image-markers.ts` 加 `parseInlineImageMarkers(text, validSha8)` → `InlineSegment[]`(text / image)+ `imageMarkerKey(checksum)` helper(sha8 = checksum 前 8 hex,keying 集中一處)
- [x] membership 驗證:sha8 ∉ validSha8 → strip 並合併前後文字(無空卡);同一 sha8 第二次出現 → strip(dup dedup,anchored set);malformed body 同 capped-out 同一條 strip 路
- [x] streaming 行為不變(`stripInlineImageMarkers` 原封不動;parse 只用於完成態,module note 寫明)
- [x] vitest 14 新(2 imageMarkerKey + 12 parse:membership / dup 至多 anchored 一次 / 相鄰標記 back-to-back / 無標記退化單 text 段 / 空 membership == strip 結果 / 首標記無空前段 / 完成態尾截當字面);現有 13 strip tests 全綠(共 27 passed);tsc 0 / eslint 0 / prettier clean

## F2 — render 層(交織)
- [ ] `AnswerBodyMarkdown` 按 segments 交織:text 段照現有 markdown + citation pipeline,image 段 render 現有 `InlineImageCard`(R1 技術路徑二選一,決定記 progress)
- [ ] 末尾 inline 卡堆改 un-anchored only(anchored 圖唔重複;ADR-0055 顯示語意)
- [ ] figure 編號全答案連續(anchored 先、un-anchored 後)
- [ ] `ImageGallery` 全量總覽不變;knob OFF 答案 render 零回歸
- [ ] tsc 0 / eslint 0 / vitest 綠;H7 fidelity check(mockup `ekp-page-chat.jsx:443-500` 對齊)

## F3 — DD-8 copy 路徑
- [ ] copy 按鈕 wire:`navigator.clipboard` + strip 後文字(vitest)
- [ ] backend RAGAs answer 評分路徑 strip 標記(pytest)
- [ ] DEFERRED_REGISTER DD-8 → 已 Close(記證據)

## F4 — 驗證(knob ON 實跑)
- [ ] drive-images-1 實跑肉眼核:標記位置出卡 / 末尾無重複 / gallery 全量 / 無爛字無空卡
- [ ] 九 query 報告級 sanity(標記全消費;可用 `scripts/run_marker_placement.py` 答案 + 前端 parse 對拍)
- [ ] AC1-AC6 自評記 progress

## F5 — 收爐
- [ ] user-guide 同步(02/03 提交織顯示行為 + DD-8 caveat 解除)
- [ ] memory 更新(`project_inline_image_markers_w70` 接力位 close)+ plan closeout + retro

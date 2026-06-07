---
bug_id: BUG-034
report_ref: ./report.md
---

# BUG-034 — Fix Checklist

> 逐項 atomic;done 後 `→[x]`,未做標 🚧 + 理由(per CLAUDE.md sacred rule)。

## Finding A — conversation kb_id 對齊(C10 frontend)
- [x] FA1 — `handleSubmit` 內 capture `reusedConversation = activeConvId != null`(ensureConversation 之前)
- [x] FA2 — 重用舊對話時 `conversationsApi.update(convId, { kb_id: kbId })`(fire-and-forget)
- [x] FA3 — PATCH 後 `queryClient.invalidateQueries(['conversations'])` 令列表標籤即時更新(加 `useQueryClient`)
- [x] FA4 — 新建對話路徑(`ensureConversation` create)維持以當前 kbId 持久化(已正確;`reusedConversation` guard 避免冗餘 PATCH)

## Finding B — list_chunks 帶 doc 欄位(C04 retrieval)
- [x] FB1 — `hybrid.py:list_chunks` `$select` 加 `doc_id,doc_title,doc_format`
- [x] FB2 — `list_chunks` 返回 dict 加 `doc_id` / `doc_title` / `doc_format`(fallback 空字串)
- [x] FB3 — docstring 更新列明新欄位(additive,no behaviour change;`ChunkSummary` extra='ignore' → /chunks route 無 regression)

## Finding C — citation 0.000 relevance 顯示(C10 frontend;用戶重測後新發現)
- [x] FC1 — `formatRelevance(score)` 新增於 `lib/chat/citation-images.ts`(`score>0 ? toFixed(3) : '—'`)
- [x] FC2 — `chat/page.tsx` 4 處 score 顯示(1580/2087/2257/2593)改用 `formatRelevance`
- [x] FC3 — score bar(2074)score=0 已係 0% 空條,無需改

## Tests
- [x] T1 — frontend `chat-bug034.test.tsx`:載入綁 kb-a 對話 → 切 kb-b → send → assert `update(convId,{kb_id:'kb-b'})`;另測 fresh create 唔 PATCH。2/2 pass
- [x] T2 — backend `test_bug034_list_chunks_doc_fields.py`:$select 含 3 欄位 + 返回 dict 含 + legacy fallback 空字串。3/3 pass
- [x] T3 — covered by T2(source-level)+ live V3(neighbor citation 帶 doc_id end-to-end)
- [x] T4 — frontend `citation-relevance-format.test.ts`:score 0 → `—`、真分數 → toFixed(3)、tiny 正分 → 真分數。3/3 pass

## Verification
- [x] V1 — frontend tsc exit 0 + eslint 0 error(1 pre-existing `<img>` warning)+ vitest chat-bug034+033 4/4 pass
- [x] V2 — backend pytest 68 passed(bug034 + chunks_listing + hybrid + citation_expansion/images)+ ruff clean + mypy hybrid.py clean
- [x] V3 — Live:重啟 backend(~110s)→ `/query` drive-images-1 GL → **11/11 citation 有 doc_id**;Playwright 真 browser → 對話 kb_id dce→drive-images-1 **PASS**
- [x] V4 — citation[1] 行為不變(reranked-search 路徑未改);concise / 無 expansion 路徑 additive-only 無 regression

## Verification (Finding C)
- [x] VC1 — frontend tsc exit 0 + eslint 0 error(1 pre-existing `<img>` warning)+ vitest 7/7(3 format + 2 bug034 + 2 bug033)
- [ ] VC2 — Live:`drive-images-1` GL query → expansion citation 顯示 `—`、reranked 顯示分數(用戶重測或 Playwright)

## Closeout
- [x] C1 — report.md status(verifying;Finding C 待 live confirm)→ done after VC2;progress.md addendum
- [x] C2 — component design note bump(C10 chat / C04 retrieval list_chunks)
- [ ] C3 — commits 對應 Day-N(R2);ff-merge 入 main(待用戶確認問題2+3 OK)

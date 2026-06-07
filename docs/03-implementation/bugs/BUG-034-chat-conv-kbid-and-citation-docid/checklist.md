---
bug_id: BUG-034
report_ref: ./report.md
---

# BUG-034 — Fix Checklist

> 逐項 atomic;done 後 `→[x]`,未做標 🚧 + 理由(per CLAUDE.md sacred rule)。

## Finding A — conversation kb_id 對齊(C10 frontend)
- [ ] FA1 — `handleSubmit` 內 capture `hadConv = activeConvId != null`(ensureConversation 之前)
- [ ] FA2 — 重用舊對話(`hadConv`)時 `conversationsApi.update(convId, { kb_id: kbId })`(fire-and-forget)
- [ ] FA3 — PATCH 後 `queryClient.invalidateQueries(['conversations'])` 令列表標籤即時更新(加 `useQueryClient`)
- [ ] FA4 — 新建對話路徑(`ensureConversation` create)維持以當前 kbId 持久化(已正確,確認 no-op)

## Finding B — list_chunks 帶 doc 欄位(C04 retrieval)
- [ ] FB1 — `hybrid.py:list_chunks` `$select` 加 `doc_id,doc_title,doc_format`
- [ ] FB2 — `list_chunks` 返回 dict 加 `doc_id` / `doc_title` / `doc_format`(fallback 空字串)
- [ ] FB3 — 確認 retrieval_engine.py docstring 列嘅欄位一致(no behaviour change,additive)

## Tests
- [ ] T1 — frontend `chat-bug034.test.tsx`:載入綁 kb-a 對話 → 切 kb-b → send → assert `update(convId,{kb_id:'kb-b'})` 被呼叫
- [ ] T2 — backend `list_chunks` test:mock Azure 回應 → assert 返回 dict 含 `doc_id` / `doc_title` / `doc_format`
- [ ] T3 — backend(若有現成 citation_expansion / build_citations 整合 test):neighbor citation 帶 doc_id(否則 T2 already covers source)

## Verification
- [ ] V1 — frontend tsc exit 0 + eslint 0 new error + vitest 相關檔 0 regression
- [ ] V2 — backend pytest 相關檔(retrieval / citation)pass + ruff + mypy(改檔)0 新 error
- [ ] V3 — Live:`drive-images-1` 新對話切 KB 後問 GL → `conversation.kb_id` 對齊 + 所有 citation 帶 doc_id
- [ ] V4 — 確認對 concise / 無 expansion 路徑無 regression(citation[1] 行為不變)

## Closeout
- [ ] C1 — report.md status → done;progress.md closeout
- [ ] C2 — component design note bump(C10 chat / C04 retrieval list_chunks)
- [ ] C3 — commits 對應 Day-N(R2);ff-merge 入 main(用戶決定)

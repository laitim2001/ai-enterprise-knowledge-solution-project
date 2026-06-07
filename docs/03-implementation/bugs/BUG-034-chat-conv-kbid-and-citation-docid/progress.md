---
bug_id: BUG-034
report_ref: ./report.md
checklist_ref: ./checklist.md
status: in-progress     # in-progress | closed
---

# BUG-034 — Progress

> Investigation → fix → verify。每 commit 對應 Day-N(R2)。

---

## Day 1 — 2026-06-07

### Context
W56 後續,新建圖片 KB `drive-images-1`(6 DRIVE 手冊、827 截圖)畀用戶喺 chat 測圖。用戶測試報 3 問題:(1) 圖片 recall 相關性、(2) 對話綁錯 KB、(3) citation 顯示文件/段落唔正確。用戶選「先修 2+3」;問題1 retrieval 調優另案。

### Diagnosis(triage 時即 root-caused,後端數據實證)
- **Finding A**:後端 `conversation.kb_id=dce-integration-images-1` 但 citations `doc=drive-user-manual-0605-gl-...`(drive-images-1)→ 對話 kb_id 只 create 時 capture,切 KB 不 sync(`handleNewChat:590` / `ensureConversation:281`)。
- **Finding B**:citation[1] 有 doc_id,[2..11] 空(但 chunk_id embed 咗 doc)→ `hybrid.py:list_chunks` `$select`(:526)缺 `doc_id/doc_title/doc_format`,expansion neighbor 落 `build_citations:95` 即空。

### Decisions
- 問題1 圖片相關性 **out-of-scope**(per 用戶選擇)→ 另案 per-KB retrieval 調優 + domain 驗證。
- Finding A 用「送訊息時若重用舊對話 → PATCH kb_id」(最 surgical;新建路徑已正確,加 `hadConv` guard 避免冗餘 PATCH)。
- Finding B 喺 source(`list_chunks` $select)修(additive,順帶修好 doc_title 顯示),非喺 expansion 物化點 inject(後者只補 doc_id 且唔 fix doc_title）。
- 兩 finding 合一 BUG instance(同 chat 一次測試 / 同 Sev3 / 皆 surgical;跨 C10+C04 層,接受 — 同屬「chat 答案 metadata 完整性」)。

### Blockers
- 無。

### Effort
- Planned ~1-2h;Actual:_(填)_

### Commits
| Hash | Subject |
|---|---|
| _(待)_ | docs(bug): BUG-034 kickoff |

---

**End of BUG-034 progress (Day 1 in-progress)**

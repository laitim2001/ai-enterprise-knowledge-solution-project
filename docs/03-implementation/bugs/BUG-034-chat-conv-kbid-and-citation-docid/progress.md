---
bug_id: BUG-034
report_ref: ./report.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
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
| `9ec4520` | docs(bug): BUG-034 kickoff(report + checklist + progress)|
| `961b1c4` | fix(chat): conversation kb_id re-bind + list_chunks doc identity |
| _(closeout)_ | docs(bug): BUG-034 closeout(checklist/progress/report done + C10/C04 notes)|

---

## Closeout — 2026-06-07

### Root cause(both confirmed + live-verified)
- **A(C10)**:對話 kb_id 只喺 create 時 capture(`handleNewChat:590` eager create / `ensureConversation:281` 重用不更新)→ 切 KB 後 query 用新 kbId 但記錄 kb_id 停喺舊值。後端實證 `conversation.kb_id=dce` 但 citations `doc=drive-…gl`。
- **B(C04)**:`hybrid.py:list_chunks` `$select`(:526)缺 `doc_id/doc_title/doc_format` → citation expansion 由 `list_chunks` 物化嘅 neighbor citation 落 `build_citations:95` 即空。

### Fix
- **A**:`chat/page.tsx` handleSubmit capture `reusedConversation = activeConvId != null`;重用時 `conversationsApi.update(convId,{kb_id:kbId})` + `queryClient.invalidateQueries(['conversations'])`(加 `useQueryClient` import)。新建路徑已正確(create 用當前 kbId),guard 避免冗餘 PATCH。
- **B**:`hybrid.py:list_chunks` `$select` + 返回 dict 加 `doc_id/doc_title/doc_format`(additive;docstring 更新)。順帶修好 doc_title 顯示。

### Verification
- frontend:tsc 0;eslint 0 error(1 pre-existing `<img>` warning);vitest chat-bug034(2)+ chat-bug033(2)= 4/4 pass。
- backend:pytest 68 passed(test_bug034_list_chunks_doc_fields 3 + chunks_listing + hybrid_section_path + citation_expansion + citation_image_neighbors);ruff clean;mypy hybrid.py clean。
- **Live(重啟 backend ~110s)**:
  - Finding B:`POST /query` drive-images-1「How do I post a journal entry in General Ledger?」→ **11/11 citations 有 doc_id + doc_title**(修前只 [1] 有)。
  - Finding A:Playwright 真 browser → 載入綁 dce 對話 → 切 selector 去 drive-images-1 → send → `conversation.kb_id` = **drive-images-1**(PASS;修前停喺 dce)。

### Lessons
- **分歧 bug 要睇兩端**:UI 顯示「對話 KB」同實際 query 用嘅 KB 可以分歧;持久值正確還原 ≠ 持久值本身正確(BUG-033 只修還原,源頭錯漏網)。
- **projection 缺欄位係 silent 失真**:`$select` 漏 `doc_id` 唔會報錯,只係下游 `f.get("doc_id","")` 靜靜變空 → 要對住真實 citation data 先睇得出。
- **Additive projection 安全**:`ChunkSummary` Pydantic v2 預設 `extra='ignore'`,加 select 欄位對 /chunks route 無 regression(已 grep 確認 consumer)。
- **Live 驗證雙路徑**:backend 改動(無 --reload)必須重啟先生效;前端改動 next dev HMR 自動;Playwright fresh context 證實 deployed bundle 行為(避免重蹈 BUG-033「fix 啱但 browser cache 舊」混淆)。

### Effort
- Planned ~1-2h;Actual ~1.5h(含 backend restart + 雙路徑 live verify)。

### Component design note status updates
- C10 Frontend Chat:amendment + last_updated 2026-06-07(conversation kb_id 送訊息時 re-bind)
- C04 Retrieval:amendment + last_updated 2026-06-07(`list_chunks` 投影 doc identity 欄位)

### Out-of-scope carry-over(明確,未刪)
- 問題1 圖片 recall 相關性(retrieval 錨定 sub-section 3.1.5 + 圖片擴展闊度 prefix_depth=1=整章)→ 另案 per-KB retrieval 調優 + domain 驗證(用 `drive-images-1` 進階檢索調節 panel 收窄 `citation_neighbour_section_path_prefix_depth` / `citation_expansion_window`,同用戶一齊驗證正確段落)。

### Branch
- `fix/chat-kb-bind-and-citation-docid`;待用戶確認 ff-merge 入 main + push。

---

## Addendum — 2026-06-07(用戶重測後 Finding C)

> 用戶 hard-refresh 重測:**問題2(Finding A)確認 OK**;問題3 嘅 doc_id(Finding B)已修(tooltip 顯示文件名),但仍覺「對應內容唔正確」。實地抽數據揭新根因 → 加 Finding C。

### Finding C — citation 0.000 relevance 顯示(C10)
- **根因**:GL query 13 citation 入面只有 2 個有真分數,其餘 11 個 = `0.000`(citation expansion 補嘅 neighbor,`citation_expansion.py` 寫死 `score=0.0`)。前端 4 處 `relevance_score.toFixed(3)` 照顯示「0.000」→ 似零相關 / 壞咗。
- **修復**:`formatRelevance(score)`(`lib/chat/citation-images.ts`,`score>0?toFixed(3):'—'`);`chat/page.tsx` 4 處(1580/2087/2257/2593)改用;score bar score=0 已係空條無需改。純前端 display-only。
- **測試**:`citation-relevance-format.test.ts` 3/3;chat-bug034+033 回歸 4/4;tsc 0;eslint 0 error。
- **commit**:`_(Finding C)_`。
- **待**:VC2 live confirm(用戶重測或 Playwright)→ 然後 re-close。

### 問題1 / expansion 闊度調優(out-of-scope 本 BUG)
- 數據顯示問題1「圖片 p31 唔係 p20-28」主要係 **reranker 錨定 §3.1.5(後段)做主命中**,圖片跟錨點;單純收窄 expansion 闊度未必郁錨點。
- 屬 per-KB retrieval 調優 + domain 驗證(runtime config on `drive-images-1`,非 code bug)→ 另案實驗,同用戶一齊驗證 completeness/focus 取捨。

### Commits(addendum)
| Hash | Subject |
|---|---|
| _(Finding C)_ | fix(chat): BUG-034 Finding C — em-dash for expansion-citation sentinel score |

---

**End of BUG-034 progress (Finding C verifying)**

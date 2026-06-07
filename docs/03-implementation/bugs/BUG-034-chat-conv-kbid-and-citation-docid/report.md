---
bug_id: BUG-034
title: "Chat: conversation persists stale kb_id (shows wrong KB) + expanded citations lose doc_id"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: done            # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-06-07
reporter: "Chris (end-user testing on chat page, drive-images-1 KB)"
affects_components: [C10, C04]   # C10 Frontend Chat UI (Finding A) · C04 Retrieval list_chunks (Finding B)
spec_refs:
  - architecture.md §5 (frontend chat surface)
  - architecture.md §3.7 (citation post-hoc expansion)
  - frontend/app/(app)/chat/page.tsx
  - backend/retrieval/hybrid.py (list_chunks)
  - backend/generation/citation_enrichment.py (build_citations)
---

# BUG-034 — Chat conversation binds stale kb_id + expanded citations lose doc_id

> **Report version**:1.0(initial)
> **Triage approver**:Chris(2026-06-07 — chat 測試發現,選「先修 2+3 兩個 bug」)

兩個獨立、同喺 chat 一次測試(`drive-images-1` 圖片 KB)發現嘅 bug,合併一個 BUG instance 修。原始測試報告 3 個問題;問題1(圖片 recall 相關性)屬 retrieval 調優,**另案處理**,不在本 BUG 範圍。

## 1. Symptom

- **Finding A(對話綁錯 KB)**:喺左側 Conversations 揀返一個對話時,頂部 KB selector 顯示嘅 KB **唔係實際 query 用嗰個**。實測兩個今日新建嘅對話都顯示 `dce-integration-images-1`,但答案內容明顯嚟自 `drive-images-1`(DRIVE GL 逐步 + 38 截圖)。
- **Finding B(citation 空 doc_id)**:答案返回嘅 citations 入面,只有第 1 個(主命中)有 `doc_id`,其餘(citation post-hoc expansion 補嘅 aux citations)`doc_id` **全部係空字串** → 前端 citation pill 連結斷、顯示嘅對應文件/段落唔正確。

## 2. Reproduction Steps

**Finding A**:
1. 開 `/chat`,KB selector 預設停喺第一個 KB(`dce-integration-images-1`)。
2. 「New chat」(eager create,對話以當前 kbId = dce 持久化),或選一個舊對話。
3. 切 selector 去 `drive-images-1`,問 GL 問題,Send。
4. **Observed**:答案啱(用 drive-images-1),但對話記錄持久化嘅 `kb_id` 仍係 dce;再點返該對話,selector 還原成 dce(錯)。

**Finding B**:
1. 對任何啟用 citation expansion 嘅 KB(全域 `enable_citation_post_hoc_expansion=true`)問會觸發擴展嘅問題。
2. **Observed**:assistant 訊息 citations[2..N] 嘅 `doc_id=''`(但 chunk_id 入面 embed 咗 doc)。

**Reproduction reliability**:Always(兩者皆穩定重現)

**Environment**:local dev,frontend `localhost:3001`,backend `localhost:8000`,KB `drive-images-1`

## 3. Expected vs Actual

**Finding A**
- **Expected**:對話持久化嘅 `kb_id` = 實際攞嚟 query 嗰個 KB;切 KB 後送訊息,對話 KB 跟住對齊;再開該對話 selector 顯示正確 KB。
- **Actual**:`conversation.kb_id` 只喺建立嗰刻 capture 一次,之後切 KB 唔更新 → 持久值同 query 用嘅 KB 分歧。後端實證:`conversation.kb_id=dce-integration-images-1` 但 citations `doc=drive-user-manual-0605-gl-...`。

**Finding B**
- **Expected**:每個 citation(包括 expansion 補嘅)都帶正確 `doc_id` / `doc_title`,pill 可連去對應文件。
- **Actual**:expansion aux citations `doc_id=''`、`doc_title=''`。後端實證:citation[1] 有完整 doc_id;[2..11] 空,但 chunk_id 含 `..._doc-drive-user-manual-0605-gl-..._chunk-00NN`。

## 4. Impact

- **Affected**:所有 chat 用戶。
  - Finding A:切 KB 後對話標籤 + 還原皆錯;若無為意,可能對住「以為係 KB-A」嘅對話發問但實際 query KB-B(correctness 風險,可手動 re-select)。
  - Finding B:citation pill 連結斷 + 顯示源頭文件/段落唔正確(usability + trust 下降)。
- **Workaround**:Finding A = 每次手動確認 selector;Finding B = 無。
- **Data loss / corruption?**:No(持久值「錯」但可改寫;無資料毀壞)
- **Security implication?**:No

## 5. Severity Justification

**Sev3** per PROCESS.md §4.5:影響 usability + 一個 recoverable correctness risk(Finding A 發錯 KB),citation 顯示失準(Finding B),但有 workaround、無資料損失、核心檢索/生成正常。非 Sev2(無 broad 數據完整性破壞)、非 Sev4(多過純 cosmetic)。

## 6. Initial Diagnosis(root cause confirmed 2026-06-07)

**Finding A — confirmed root cause**:`chat/page.tsx` 對話 `kb_id` **只喺建立嗰刻 capture**:
- `handleNewChat`(:590)`conversationsApi.create({ kb_id: kbId })` —— eager create,kbId = 當時預設 kbs[0]。
- `ensureConversation`(:281-290)`if (activeConvId) return activeConvId;` —— 重用舊對話時**唔更新** kb_id。
- `handleSubmit`(:390-391)`streamQuery({ kb_id: kbId })` —— query 用當前 kbId。
→ 重用對話 + 切 KB 時,query 用新 kbId 但對話記錄 kb_id 唔變 → 分歧。BUG-033 Finding A 只修「載入時還原持久值」,但持久值由源頭就錯。

**Finding B — confirmed root cause**:`backend/retrieval/hybrid.py` `list_chunks`(:500-563)嘅 `$select`(:526-529)同返回 dict(:542-554)**冇 `doc_id` / `doc_title` / `doc_format`**。citation expansion(`citation_expansion.py:332-343`)由 `engine.list_chunks` 物化 neighbor `RetrievedChunk`,落到 `build_citations`(`citation_enrichment.py:95`)`f.get("doc_id","")` 即空。主命中由 reranked search 嚟(有 doc_id),所以只有 citation[1] 正常。

## 7. Acceptance for Fix(checklist preview)

- [ ] Finding A 重現 + root cause 確認(create-only kb_id;切 KB 不 sync)
- [ ] Finding A fix:送訊息時若重用舊對話,`conversationsApi.update(convId, { kb_id: kbId })` 對齊 + invalidate 對話列表
- [ ] Finding B 重現 + root cause 確認(list_chunks $select 缺 doc 欄位)
- [ ] Finding B fix:`list_chunks` $select + 返回 dict 加 `doc_id` / `doc_title` / `doc_format`
- [ ] Regression test(Finding A:切 KB 送訊息 → update 帶新 kb_id;Finding B:list_chunks 返回含 doc_id)
- [ ] backend pytest + ruff + mypy(改檔)0 新 error;frontend tsc + lint + vitest 0 regression
- [ ] Live 驗:新對話切 KB 後 `conversation.kb_id` 對齊 query KB + 所有 citation 帶 doc_id

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-07 | Initial triage + 雙 finding root cause 確認 | chat 測試發現(drive-images-1);後端數據實證分歧 + 空 doc_id | Chris |

---

**Out-of-scope(明確)**:問題1 圖片 recall 相關性(retrieval 錨定 sub-section + 圖片擴展闊度)→ 屬 per-KB retrieval 調優 + domain 驗證,另案;對話跨多 KB 嘅產品語意(切 KB 是否該開新對話)→ Tier 1 採「最近 query KB = 對話 KB」,深層產品決定另議。

---

## Finding C addendum(2026-06-07 — 用戶重測後新發現)

> 用戶重測:問題2(Finding A)確認 OK;問題3 嘅 doc_id(Finding B)已修(tooltip 而家顯示文件名),但 citation tooltip 大部分顯示 **`0.000`** relevance → 仍覺「對應內容唔正確」。實地抽數據確認新根因。

### Symptom(C)
一個 GL query 13 個 citation 入面,**只有 2 個有真實 relevance_score**(reranked 主命中),**其餘 11 個 = `0.000`**。

### Root cause(C — confirmed)
citation post-hoc expansion(`citation_expansion.py:332-343`)補入嘅 neighbor chunk 用 sentinel `score=0.0`(從未獨立 rerank)。前端 4 處 `citation.relevance_score.toFixed(3)`(`chat/page.tsx` 1580/2087/2257/2593)照樣顯示「0.000」→ context citation 睇落似「零相關 / 壞咗」,尤其同 section 隔籬有真分數。

### Fix(C)
新增 `formatRelevance(score)`(`lib/chat/citation-images.ts`):`score > 0 ? toFixed(3) : '—'`(真 Cohere rerank score 實際上永不剛好 0,故 `score>0` 可靠分辨 reranked vs expansion neighbor)。4 處顯示改用呢個 helper。純前端、display-only。

### Acceptance(C)
- [x] expansion citation(score=0)tooltip / panel / modal 顯示 `—` 而非 `0.000`
- [x] 真 reranked citation 仍顯示 3 位小數分數
- [x] `formatRelevance` unit test;tsc + lint + vitest 0 regression
- [x] Live(數據模擬)+ 用戶 chat 重測確認 OK(2026-06-07)

### Out-of-scope(C)
問題1 圖片 recall 相關性 + expansion 闊度調優 → 見 Finding D(下)結果:**圖片 ORDERING 屬 presentation,已修;retrieval RELEVANCE 仍不改**。

---

## Finding D addendum(2026-06-07 — 問題1 診斷後,presentation 修法)

> 用戶確認問題1「圖片應 p20-28、返咗 p31」。實地診斷:**唔係 recall 缺失,係排序**。

### Diagnosis(D)
GL03「post a journal entry」程序 = §3.1.3 GL03-1 Create General Journal(~p20-28,24 圖)→ §3.1.4 Approve → §3.1.5 GL03-3 Post the Journal(~p31,16 圖)。兩段圖**都返咗**(答案 §3.1.3 20 張 + §3.1.5 14 張),但 reranker 將 §3.1.5「Post」排第一(query 字眼「post」直接 match),`dedupeCitationImages` 按 citation/relevance order 排 → **gallery + inline cards lead 住 §3.1.5(p31)**,用戶一眼見 p31。

### Fix(D)— 用戶選「按文件次序排圖」
`dedupeCitationImages`(`lib/chat/citation-images.ts`)輸出加一個 stable sort,key = 圖片自己嘅 `source_section`(`imageSectionPath`)→ 圖片按 DOCUMENT 次序排(§3.1.1 → 3.1.3 → 3.1.4 → 3.1.5),程序由 Create(p20-28)順住落 Post(p31)。numeric badge(citationIdx)仍錨 citation 位置;只改 render order。純前端 presentation,**不改 retrieval**。

### Acceptance(D)
- [x] gallery + inline cards 按 section document 次序排(Create 先於 Post)
- [x] 同 section 圖片保持原(citation)次序(stable)
- [x] unit test;tsc + lint + vitest 0 regression
- [x] Live(數據模擬:頭 8 張 §3.1.5→§3.1.1/§3.1.3)+ 用戶 chat 重測確認 OK(2026-06-07)

### 仍然 out-of-scope
Retrieval RELEVANCE 本身(reranker 點解偏好 §3.1.5、要唔要改 rerank_k / query reformulation / low-value flag)**不改** —— text 答案已完整覆蓋全程序,圖片排序已解決 UX;深層 rerank 調優屬獨立 retrieval 課題,有需要先另案。

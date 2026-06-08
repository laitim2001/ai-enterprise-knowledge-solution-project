---
change_id: CH-008
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
---

# CH-008 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-08

### Context
接 BUG-034 問題1 底層診斷。Finding D(圖按文件次序,presentation)已 merge;但純 rerank top-8 證 reranker 揀錯章節(§5.1.3 GL05 #1、§2.1.x GL02 #3/#4,GL03-Create 沉 #5-8),因為 reranker 只餵 `chunk_text`、section heading 又 generic 重複。74-chunk Cohere rerank A/B 實驗(2026-06-07)PASS:加 section context 後 off-topic 清走、GL03 升頂 7/8。用戶選全套(rerank + embedding,要 re-index)。

### Done
- (kickoff)ADR-0045 寫(Proposed)+ 入 ADR index;CH-008 spec(approved)+ checklist + progress committed(R1.change + R5 滿足)。
- (pending I1-I7 + re-index + eval + closeout)

### Decisions
- 全域 contextual retrieval(非 per-KB);format = `" > ".join(section_path) + "\n" + chunk_text`;section_path 空 → fallback 純 chunk_text(零 regression)。
- Stored `chunk_text` 維持原文(citation/listing/Finding D 不受影響);只 embedding 向量 + rerank document 加 context。
- 本期只 re-index `drive-images-1`(有真實 source、in-place、唔佔 Free-tier 新槽);其他 KB 多 stub source,另議。

### Blockers
- 無。

### Effort
- Planned ~0.5-1 day;Actual:_(填)_

### Commits
| Hash | Subject |
|---|---|
| _(待)_ | docs(adr+change): ADR-0045 + CH-008 kickoff |

---

## Day 2 — 2026-06-08

### Context
ADR-0045 Chris Accept → code 解 gate(H1)。落 I1→I3 + tests + I7 docs。

### Done
- **I1** `retrieval/contextual.py` `build_contextual_document(section_path, chunk_text)` — `" > ".join` + `\n` + text;空/None/whitespace-only path → fallback 純 chunk_text。
- **I2** `cohere.py:94` rerank documents 用 helper(+ docstring 更新 §3.2/§3.6 ref)。
- **I3** `orchestrator.py:153` embed input 用 helper(`embed_inputs`);stored `ChunkRecord.chunk_text=spec.chunk_text` 原文不變(line 212)。
- **I4/T1-T3** `tests/test_contextual_retrieval_ch008.py`(4 helper + 1 cohere + 1 orchestrator = 6 新 test)。
- **I7a** architecture.md §3.6 加 CH-008 amendment block(rerank document + embedding input = section context + chunk_text;stored chunk_text 不變;Azure semantic 注入不適用解釋)。
- **I7b** C04(rerank)+ C01(embedding input)design note bump。
- **V1** pytest 27 passed(ch008 6 + reranker 9 + orchestrator 12)+ ruff all pass + mypy 改檔 0 新 error(17 個 pre-existing 全喺 docling parsers / base.py / schemas.py 等未 touch 檔)。

### Decisions
- **C03→C01 修正**(R6 plan-text contamination):embedding input 改喺 `ingestion/orchestrator.py` = C01 Ingestion,非 C03 Indexing;spec 原寫「C03 Ingestion」component 名張冠李戴。`affects_components` 改 `[C04, C01, C03]`(C03 只係 §3.6 doc 文字)。
- **I2b deviation → 🚧 待 Chris**:`azure_semantic.py` 唔砌 document list(re-issue semantic search,排序由 `ekp-semantic-config` 決定)→ 無 document 可注入;Azure semantic 非 production reranker(Cohere H2 lock)+ chat 行 semantic OFF。建議 drop(經 I3 embedding re-index 間接受惠);真正注入需改 index schema(額外 H1,Karpathy §1.2 reject)。

### Verification(Day 2 下半,環境就緒後)
- **Pre-flight**(per session-start 5b):Langfuse `/api/public/health` 200 + Postgres `SELECT 1` OK + azurite :10000 live。
- **Backend restart**:舊 backend(PID 780 child / 50736 venv parent,改 code 前啟動)停;venv python `-m api.server`(`HYBRID_USE_SEMANTIC_RANKER=false`)重啟,60s `/health` 200(全 component ok 含 cohere + azure_search)。
- **V2 re-index** `drive-images-1` DONE:6/6 reindexed,0 skipped,0 failed,369 chunks(I3 contextual embedding 生效)。
- **V3 AC4 PASS**:query「How do I post a journal entry in General Ledger?」top-8 —
  - rerank=true(contextual,production):#1-#7 全部 GL03「Processing Journal Vouchers」(3.1.x)、#8 GL05 Journal Reversal(唯一 off-topic);對照 ADR 實驗純 chunk_text baseline(#1 GL05 / #3-4 GL02)→ off-topic 清走、GL03 升頂 7/8 live 確認。
  - rerank=false(候選池):re-index 前 #8 = AR03(跨文件洩漏);re-index 後 AR03 清走、GL03 佔比 4→5/8 → embedding(I3)改善候選池本身。
- **V4 AC5 = 接設計+live 證據**(Chris 確認):full RAGAs eval **環境性 blocked** —— `/eval/run` 硬編 drive_user_manuals(index 已 drop)+ eval-set-v0 = W1 MFP placeholder synthetic(非 DRIVE corpus);corpus-matched eval(w42diag → test-kb-20260530-1)該 index 都已 drop。所有 eval-baseline KB index 喺 Free-tier 3-slot 下已 drop。改以 ① fallback bit-identical unit test ② strictly-more-context 設計 ③ live DRIVE retrieval-test 改善 三項收 AC5。

### Blockers / Carry-over
- 🚧 **V5 chat live 驗**(用戶動作):待用戶喺 chat UI 問 GL「post a journal entry」確認答案錨 GL03 + 圖由 Create 章節行先。
- 🚧 **C1 / C3 closeout**:spec status → done + ff-merge 入 main,待 V5 + 用戶 merge go。
- ADR-0045 Proposed → **Accepted**(Chris 2026-06-08);README index 同步(C2 ✅)。
- I2b **DROPPED**(Chris 2026-06-08)。

### Effort
- Planned ~0.5-1 day;Actual:I1-I7 + tests ~實作完成(Day 2 上半)。

### Commits
| Hash | Subject |
|---|---|
| 328e579 | docs(adr+change): ADR-0045 + CH-008 kickoff |
| 9af448e | feat(retrieval): contextual retrieval — section-context inject (I1-I3+tests+docs) |
| 07a8c7a | docs(change): CH-008 V2-V4 verification — AC4 PASS live + AC5 接設計+live 證據 + I2b dropped |
| _(closeout)_ | docs(change): CH-008 closeout — V5 文字維度 PASS + 圖片維度 split + ff-merge |

### V5 + Closeout(Day 2 收尾,2026-06-08)
- **V5 文字維度 PASS**(用戶 chat live + `/query` 重現):GL「post a journal entry」答案 **13/13 citation 全部 GL03 §3.1.x**(Overview / System Instruction,chunk_index 24-36 順序),零 off-topic。CH-008 文字 rerank + embedding 目標**徹底達成**。
- **圖片維度 split 到新工作**:用戶 V5 揭三個圖片問題 —— ① 裝飾燈泡 icon surface 成 figure(ingestion 抽晒所有 embedded image,無裝飾過濾;所有圖 `width=0 height=0` 無法用尺寸 filter)② `INLINE_IMAGE_CAP=8`(BUG-031)截斷令後段 figure 入 Image Library ③ 無 query-相關性排圖。**呢三項全部 = deferred problem 1 圖片維度,非 CH-008 文字 scope**(所有圖 source_section 正確喺 GL03,非 recall 錯)。Chris 2026-06-08 決定:先 merge CH-008、圖片另開新 BUG/CH。
- **C1/C2/C3 closeout 完成**:spec status → done;ADR-0045 Accepted;ff-merge 入 main。

### Retro
- **What went well**:74-chunk A/B 實驗先行驗證根因 → ADR 信心高;helper 抽得乾淨(rerank + embedding 共用);fallback bit-identical 保零 regression;live retrieval-test 即時證 AC4。
- **Surprises / R6 catches**:(1) I2b azure_semantic 唔砌 document list(spec text 假設錯)→ dropped;(2) `affects_components` C03→C01 component 名張冠李戴;(3) eval-set-v0 = W1 MFP placeholder 非 DRIVE corpus + 所有 eval-baseline KB index 在 Free-tier 3-slot 下已 drop → full RAGAs eval 環境性 blocked,AC5 改接設計+live 證據。三個都係 plan-text contamination,kickoff 階段未 catch,實作時先發現。
- **Carry-over → 新工作**:圖片質素(裝飾過濾 + 尺寸記錄 + 相關性排序 + cap 策略)= deferred problem 1,另開 spec/診斷。

---

**End of CH-008 progress (CLOSED 2026-06-08 — 文字維度全綠 + ff-merge;圖片維度 split 到新工作)**

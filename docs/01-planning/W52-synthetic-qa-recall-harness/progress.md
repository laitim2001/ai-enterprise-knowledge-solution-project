# W52 — Synthetic-QA Recall Harness · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-06

### Context / kickoff
W51 closed + pushed(`037da22`,completeness proxy「涵蓋章節數」誠實標明非 recall)。決策 7 三期(W49 band / W50 length-bias caveat / W51 coverage proxy)全收。用戶 pick W52 起點 = **兩者合一(synthetic-QA 做 ingestion eval 指標)**。

### 決策
- **AskUserQuestion(W52 起點)**:Chris 揀 **兩者合一** → split 成 **W52 = synthetic-QA recall 基建** → **W53 = reindex strategy 比較**(rolling JIT,W52 收尾先 kickoff,不預寫)。
- **Key design lock**(plan §2):self-supervised synthetic recall(source chunk = ground-truth)→ **reuse EvalRunner strict-mode**(零新 recall 數學)+ judge client pattern(gpt-5.4-mini + patch_for_gpt5,無 cred → None graceful)+ chunk 枚舉(list_documents→list_chunks→fetch_by_chunk_ids,zero C03 modification)。**誠實 framing**:synthetic 非人手 ground-truth recall(R1)。offline 工程閘 → backend-only → **無 H7**。無新 ADR/vendor/dep。

### R6 grep 驗證(plan kickoff)
- `EvalRunner` strict-mode(`runner.py:166-173`)現成:`validated AND acceptable_ids AND not startswith("kb-drive_doc-M0")` → `|retrieved ∩ acceptable| / |acceptable|`。synthetic entries `acceptable_chunk_ids=[source]` + `validated=True` + 真 index chunk_id(唔撞 placeholder prefix)→ strict 生效。
- `make_faithfulness_evaluator` + `patch_for_gpt5`(`ragas_evaluator.py:201/41`)現成 judge client pattern → QA generator 沿用,零新 client 架構。
- chunk 枚舉:`engine.list_documents` + `list_chunks`(返 chunk_id+section_path,**故意唔返 chunk_text**)+ `fetch_by_chunk_ids`(**無 select clause → 返全 fields 含 chunk_text**,hybrid.py:153/426/500)→ list→sample→fetch 攞 text,zero C03 modification。
- **無 plan-text contamination**:plan 引用 function/field/line grep 對齊現 code(R6 recursive scope 過)。

### Done
- F0 R1 phase 三件套建立(plan/checklist/progress);Phase Gate G1-G4 定義

### Blockers / carry-over
- 無 blocker。live judge run 對 Azure 屬 smoke-deferred(judge cred + indexed KB + Free-tier 402 繞;整合由 F3 stub 全測)。

### Commits
- (pending F0 commit)

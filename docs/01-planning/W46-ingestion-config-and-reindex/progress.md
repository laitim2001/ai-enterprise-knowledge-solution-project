# W46 — UI Ingestion Config + Real KB-Level Reindex · Progress

> Daily progress + decisions + commits + 結尾 retro。每 daily commit 對應 Day-N entry(R2)。

---

## Day 1 — 2026-06-04

### Context / kickoff
W45 closed + pushed(`c3d60bb`)。用戶揀 W46 candidate = **UI 開放 ingestion 配置 + 真 KB-level reindex(dev 層)**(roadmap「後續候選」)。

### R6 grep 驗證(plan kickoff)— 揭真 blocker
Explore agent + 親自核實揭出:roadmap [AUDIT-C]「dev 層 iterate docs → reuse doc-level reindex」**估計過樂觀**。真 blocker:
- **原始檔冇存**(已核實):系統只有一個 blob container(`ekp-kb-{kb_id}-screenshots`),**冇 source-document container**。ingest stream 落 tempfile、`finally` 即刪。真 reindex(改 chunk_strategy / 圖數 cap → 重切)要 re-parse 原檔 → 冇原檔做唔到。doc-level reindex 靠用戶 re-upload;KB-level(`kb.py:252-280`)係純 stub(假 task_id + note pending Track A)。
- **mockup locked design**(H7):`ekp-page-kb.jsx:744-815` 將 `embedding_model` / `chunk_strategy` 設 disabled + hint「changing requires re-index」。改 mockup 解鎖 = H7 STOP+ask。

### 決策
- **AskUserQuestion(scope)**:Chris 揀 **Option 4「原始檔儲存 + UI 一次過(大 W46)」** —— 完整自助 loop(backend storage + frontend unlock + 真 reindex)。
- **H1 批准 → ADR-0043**(original-file blob storage + 真 KB-level reindex):NEW `ekp-kb-{kb_id}-sources` container + ingest best-effort persist + KB-reindex iterate `list_documents` 由 source re-ingest + `_run_ingest_pipeline` refactor(接受 file path/bytes)+ production-preserve(pre-W46 doc skip+report)。v1→v2 原子切換 + embedding_model unlock = out-of-scope。
- **H7 frontend = 獨立 design sub-gate**:F3 frontend GATED on H7 mockup design 確認(unlock `chunk_strategy` + 圖數 cap + Reindex UX;`embedding_model` 維持 locked)。design-first 改 mockup per ADR-0024 precedent。

### Done
- F0.1 ADR-0043 Accepted(H1 backend 方向)`docs/adr/0043-*.md`
- F0.2 ADR README index 加 0043 row + next → 0044
- R1 phase 三件套建立(plan/checklist/progress)

### Commits
- _(pending — F0 ADR + plan kickoff commit)_

### Next
- **F0.3 H7 mockup design proposal**(surface 畀 Chris 確認 → 解鎖 F3)
- F1 source-document blob 儲存(backend,H1-approved,可即動)→ F2 pipeline refactor + 真 KB-reindex

### Blockers / carry-over
- **F3 frontend GATED on F0.3 H7 design 確認**(§5.7)。F1/F2 backend H1-approved 可即動。
- R4 live reindex verify 需 Azure + backend(pytest 覆蓋邏輯;live 可後評)。

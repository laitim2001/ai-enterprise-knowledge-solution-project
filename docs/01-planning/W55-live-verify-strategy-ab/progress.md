# W55 — Live Verify chunk-strategy recall harness · Progress

> Daily progress + decisions + commits + 結尾 retro。

---

## Day 1 — 2026-06-06

### Context / kickoff
W54 closed + pushed(`a5f6121`,controlled A/B harness)。用戶 explicit「開始執行 controlled A/B + heading_aware live eval 對真 KB(smoke-deferred 實證)」。

### Pre-flight 環境快照(think-before / §10.3 step 5b)
- docker:`ekp-postgres` healthy + `ekp-langfuse` unhealthy(per memory:Docker flag ≠ endpoint down)
- 起 azurite native(bg)+ backend(venv python,`HYBRID_USE_SEMANTIC_RANKER=false` 繞 Free-tier 402)→ `/health` 200 ~80s,**全 component OK**(azure_search/azure_openai/cohere/langfuse/postgres)→ Azure cred 齊

### Pre-flight 發現(決定路徑 — R6 think-before)
1. **現有 9 個 indexed KB 全部冇 `-sources` container**(`ekp-kb-{kb_id}-sources`)→ `run_kb_reindex` 由 `-sources` re-parse 會 skip 晒 → rich KB(drive_user_manuals 6-doc/369-chunk 等)**跑唔到 reindex-based 比較**。根因:W46 source-store 2026-06-05 先 landed,之前 ingest 嘅 KB 冇存原始檔。
2. 只有 `test-kb-20260531-v1` 有 1 source blob(`w47-ar-verify`;2-doc KB 中得 1)→ 不適合乾淨比較。
3. **原始 DRIVE manuals 喺 `docs/06-reference/01-sample-doc/`**(AR 10MB / FA 8MB / AP 7MB / GL 6.8MB / CB 1.8MB / BM 0.4MB + DCE + smoke)→ **ingest fresh KB 經 W46 source-store 存原始檔** → reindex 跑得。
4. 用戶清空 Azure Search index(Free-tier 3-index cap)騰空 → in-place reindex 同一 KB 只用 1 index,綽綽有餘。

### 決策(Chris AskUserQuestion 2026-06-06)
- 用戶 context:「azure ai search 還是 free tier,最多 3 個 index,已刪舊 index 方便重新執行測試」→ 清場叫執行。
- AI pick(推薦 Option 1):**一份中型 DRIVE manual 開 fresh KB** = **CB(Cash & Bank,1.8MB)**;KB id `w54-live-ab-1`。理由:最輕 real 多-section,end-to-end 最快 + Azure 成本最低,仍足夠 chunking 信號;若信號弱明講 + 建議換大 doc。

### Done(F0)
- F0 R1 phase 三件套建立;Phase Gate G1-G4 定義;pre-flight 發現 + 決策記低

### Commits
- `<pending>` F0 kickoff

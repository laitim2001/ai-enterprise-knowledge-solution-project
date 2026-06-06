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

### F1 ingest fresh KB(同日)
- `POST /kb` 建 `w54-live-ab-1`(index `ekp-kb-w54-live-ab-1-v1` provisioned;extract_embedded_images=false 純文字快 ingest)
- multipart upload CB docx(`curl.exe -F "file=@<path>"`,PS 5.1 冇 -Form)→ **28 chunks**,images 0
- 驗(scratch,truststore-injected):`-sources` 1 blob ✓(reindex 前提);section_path **10/10 non-empty 真階層**(「1 The Scope of this Document」→「1.1 Process Overview」/「2 CB01. Create and Delete Checks」→「2.1.3 System Instruction…」)✓ controlled A/B 文字錨點前提
- **坑記低**:ad-hoc Azure SDK scratch 撞 SSL CERTIFICATE_VERIFY_FAILED(corporate proxy self-signed)→ 必須 `import truststore; truststore.inject_into_ssl()` 喺頂部(系統 SSL 唔信任;backend/CLI 已有)

### F2 跑 W54 controlled A/B(同日)— live-path bug 發現 + 修
- **第一次跑 exit 1**:`asyncio.run(_amain())` 用 Windows default **ProactorEventLoop**,但 lifespan `audit_log_postgres.prune_expired` 用 **psycopg** → `InterfaceError: Psycopg cannot use the 'ProactorEventLoop'`。`api/server.py __main__` 有 win32 `loop_factory=asyncio.SelectorEventLoop` guard,**CLI(smoke-deferred 從未 live 跑)冇**。
- **Bug 1 fix(非 architectural,plan §2 最小修)**:CLI `main()` win32 → `asyncio.run(_amain(args), loop_factory=asyncio.SelectorEventLoop)`(mirror server.py)。
- **Bug 2(第二次跑揭)**:`UnicodeEncodeError '→'` —— CLI print 用咗 `→`/`—`,Windows console cp1252 編碼唔到(runtime 約束本身講明「用 `->` 代 `→`」;W53 CLI print 全 ASCII = 我引入嘅偏差)。Fix:print glyph 改 ASCII(`->` / `--`)+ launch 設 `PYTHONIOENCODING=utf-8` belt-and-suspenders。
- **第三次跑 exit 0 ✓ — live 實證成功**。

### F2 live 實證結果(2026-06-06,fresh KB `w54-live-ab-1`,seed 0,top-k 5,sample 30→11 passages)
| strategy | recall@5 | chunks | scored | errored |
|---|---|---|---|---|
| layout_aware(=auto)| 1.0000 | 28 | 11 | 0 |
| heading_aware | 1.0000 | **33** | 11 | 0 |

best(keyword-recall)= layout_aware(tie → first)。shared eval-set:`reports/controlled-ab-shared-seed0.yaml`(11 text-anchored QA,judge gpt-5.4-mini)。Sample QA(質素高、真實、section-anchored):CA001「In the bank reconciliation process, what is recorded when the transaction is matched…」kw=[Bank Reconciliation / Record transactions / Record adjusted entries](錨 §1.2 Process List);CA002「…delete a check number record, and which check status…」。

### F2 誠實解讀(R1)
1. **pipeline 完整 live 跑通(G2 ✓)**:build shared QA(11)→ reindex layout_aware(28)→ score → reindex heading_aware(33)→ score → 報告。W54 controlled A/B machinery 由 smoke-deferred **正式 live-verified**。
2. **chunking 真分化(validate ADR-0044)**:layout_aware 28 vs heading_aware **33**(+18%)。heading_aware **no-merge** policy 喺 CB manual 多細 subsection(「2.1.3 System Instruction…」)下保留更多細 chunk → 比 layout_aware(merge tiny)**更多** chunk。即 heading_aware 真係結構性唔同(W53 ADR-0044 live 證實),方向 = no-merge 主導(非 no-split 主導,因該 doc 細 section 多過大 section)。
3. **recall 兩者飽和 1.0 → 無辨別力(R2 materialize)**:小 corpus(28-33 chunks)+ `fetch_k=50` >> chunk 數 → **全 corpus 入候選池** → Cohere rerank top-5 幾乎必中 keyword → recall 觸頂。**呢個係 corpus-size artifact,非 strategy 屬性**。要 recall 真辨別 strategy,需 **`fetch_k < 總 chunk 數` 嘅大 corpus**(大 doc 或多-doc KB),令檢索真要篩選。**單 mid-size manual recall 軸量唔到差異**(誠實:chunk-count 軸有差,recall 軸飽和)。

### F3 closeout(同日)
- **W53 self-retrievability cross-check(F3.2)→ 🚧 deferred**。理由:(a) recall 已飽和(小 corpus ceiling)→ W53 喺同一 KB 重跑只會 reconfirm artifact,marginal value 低 + 額外 judge 成本;(b) W53 CLI `run_strategy_recall_comparison.py` 有**同款 event-loop latent bug**(+ W52 `run_synthetic_recall.py` 同),需同樣 fix —— 未 live-verify 唔應用 unverified fix。**記為 carry-over**:下次大-corpus live run 時一併修 W53/W52 CLI event-loop guard(mirror 本期 live-verified 嘅 W54 fix)。
- **建議(交用戶)**:若要 recall 軸真辨別 heading_aware vs layout_aware,re-run 喺**大 corpus**(全 6-doc DRIVE rebuild 或大 manual AR/GL,令 fetch_k=50 < 總 chunk)。本期已證 pipeline + chunking 分化;recall 辨別需更大 corpus。
- KB 最終狀態:`w54-live-ab-1` 留喺 heading_aware(33 chunks)—— fresh test KB 非 demo,可接受(plan R4)。

### Commits
- `<pending>` F0 kickoff + `<pending>` F1-F2 ingest+live-run+CLI-fixes

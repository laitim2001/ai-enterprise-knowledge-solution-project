# W56 — Large-corpus controlled A/B recall · Progress

> Daily progress + decisions + commits + 結尾 retro。承 W54/W55 誠實 framing。

---

## Day 1 — 2026-06-06

### F0 — Phase kickoff

**Context**:W55 把 controlled A/B(`run_controlled_ab_comparison.py`)live-verified,但用小 corpus(CB manual 28-33 chunks)→ recall 飽和 = corpus-size artifact(fetch_k=50 >> 總 chunk → recall 觸頂 1.0,唔辨別 strategy)。用戶 2026-06-06 explicit「執行 W56 大 corpus re-run」,AskUserQuestion 揀「**全 6-doc DRIVE rebuild**」。

**Pre-flight 發現(think-before / R6)**:

1. **Azure Search live index 直接查(`scripts/_scratch_list_indexes.py` → SearchIndexClient.list_index_names())= 1 個**:
   ```
   endpoint = azureaisearchtesting.search.windows.net
   live_index_count = 1
     - ekp-kb-w54-live-ab-1-v1  (W55 CB manual, 33 chunks)
   ```
   → **Free-tier 3-cap:1 used / 2 free**。
2. **`drive_user_manuals` KB metadata 係 stale**:`GET /kb` 返 archived=false / 6 docs / 369 chunks,**但其 index 唔喺 Azure live list**(已被清);且 last_indexed 2026-06-04 < W46 source-store(2026-06-05)→ **冇 `-sources` container** → `run_kb_reindex` download 唔到原始檔 → skip 晒。**不可 reuse**(同 W55 blocker)。
3. → W56 **必須 ingest fresh KB**(post-W46 → `-sources` 自動存)→ reindex / A/B / W53 跑得通。
4. fresh KB = **1 個 index**(in-place reindex 跨 2 strategy 同一 index)→ 開完 **2 used / 1 free**,完全喺 3-cap budget 內,**不需刪任何 index**。

**決策**:
- corpus = **全 6-doc DRIVE rebuild**(AR `0601` / AP `0602` / CB `0604` / FA `0603` / BM `0606` / GL `0605`,~369 text chunks,辨別力最強)。
- **image extraction OFF**(`extract_embedded_images=false` + `slide_screenshots=false`)— 純文字 keyword-recall 測試唔需要圖,慳 1487-screenshot 成本/時間;chunk 數不受影響(screenshots 同 text chunks 分開計)。
- KB id = `w56-drive-ab-1`,index `ekp-kb-w56-drive-ab-1-v1`。

**CLI 診斷(F3 預備,think-before)**:
- **W53** `run_strategy_recall_comparison.py`:有 truststore inject,但 **line 143 缺 win32 SelectorEventLoop guard** + 用 `lifespan(app)` → psycopg audit-log prune → **一定中 ProactorEventLoop+psycopg bug**(同 W55 修嗰個 identical pattern,高信心可套同款 fix)。
- **W52** `run_synthetic_recall.py`:缺 win32 guard,**但唔用 lifespan / 唔掂 postgres**(直接砌 embedder+searcher,line 66-80)→ **未必中** event-loop bug。**先 run 觀察先決定修不修**(Karpathy §1.1 不盲套 unverified fix)。

**Pre-flight infra**:backend `/health` 200(全 component OK,azure_search/azure_openai/cohere/langfuse/postgres);working tree 乾淨(只 local-only `01-session-start.md` + 5 他-session `live-*.png`)。origin/main = HEAD,0/0。

**Commits**:(F0 commit 待 add)

---

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

**Commits**:`dc69c58` docs(planning): W56 F0 kickoff

---

### F1 — Ingest fresh KB(6 DRIVE manuals)

**F1.1**:`POST /kb` 建 `w56-drive-ab-1`,index `ekp-kb-w56-drive-ab-1-v1` provisioned;config 確認 `extract_embedded_images=false` + `slide_screenshots=false` + chunk_strategy=auto + default_top_k=50 + default_rerank_k=5。

**F1.2**:sequential multipart upload(`curl.exe -F`,images off)— **6 docs 全成功,無 AP timeout**(舊 drive_user_manuals AP 曾 embed APITimeoutError,今次 images off 令 embed 負載輕咗 → 過):

| Module | 檔案大小 | chunks_emitted | images |
|---|---|---|---|
| BM (0606) | 0.4MB | 16 | 0 |
| CB (0604) | 1.8MB | 28 | 0 |
| GL (0605) | 6.8MB | 74 | 0 |
| FA (0603) | 8MB | 78 | 0 |
| AP (0602) | 7MB | 83 | 0 |
| AR (0601) | 10MB | 90 | 0 |
| **總計** | | **369** | **0** |

KB status:`total_documents=6 / total_chunks=369 / total_screenshots=0 / failed_documents=[]`。**369 >> fetch_k=50** ✓(對返舊 drive_user_manuals 嘅 369,證 ingest 一致)。

**F1.3**(scratch `_scratch_verify_kb.py` 驗,不入 git）:
- **`-sources` container `ekp-kb-w56-drive-ab-1-sources` = 6 blobs**(每 doc 一個,reindex 前提 ✓)。
- **section_path sample 12/12 non-empty**,真階層(`['1 The Scope of this Document', '1.1 Process Overview – Diagram']` 等,controlled A/B 文字錨點前提 ✓)。
- **R3 確認**:部分 chunk section_path 係純 heading 無 doc-title prefix(如 `['1 The Scope of this Document', ...]`)→ 跨 doc 同名 section 會 collide(`build_shared_eval_set` group by `tuple(section_path)` 會 merge 跨 doc)。**controlled 性質不受影響**(frozen set 對兩 strategy 同一套),只係 lexical-proxy caveat 更響(F4 記)。

**Commits**:`26495ee` docs(planning): W56 F1 ingest

---

### F2 — 跑 W54 controlled A/B(大 corpus,核心)

CLI `run_controlled_ab_comparison.py --kb-id w56-drive-ab-1 --strategies layout_aware heading_aware --sample 30 --top-k 5`(env `HYBRID_USE_SEMANTIC_RANKER=false` + `PYTHONIOENCODING=utf-8`,background ~15 分鐘)→ **exit 0**,無 live-path bug(W55 已修嘅 CLI 直接 reuse)。

```
W54 controlled shared-question A/B recall comparison
  KB: w56-drive-ab-1   shared Qs: 30   seed: 0   top-k: 5
  eval-set: controlled-ab-W54-w56-drive-ab-1-seed0
  strategy          recall@k   chunks  scored  errored
  layout_aware        0.9917      369      30        0
  heading_aware       0.9850      415      30        0
  best (keyword-recall): layout_aware
```

**F2.3 核心驗證 — 誠實解讀**:

1. ✅ **recall 軸唔再完全飽和**:W55 小 corpus(28-33 chunks)= **1.0 / 1.0**(觸頂,零辨別);W56 大 corpus(369/415 chunks)= **0.9917 / 0.9850**(**兩個都 < 1.0 + 有 delta**)→ corpus-size saturation artifact **被打破/減低**(G3 達成方向)。

2. ⚠️ **但辨別力仍弱,gap 喺 noise floor 之內**:兩 strategy 都 ~0.99,delta 僅 **0.67pp**(layout 0.9917 vs heading 0.9850 → 30 題中 layout 多約 0.2 題份量嘅 keyword)。n=30 synthetic + keyword-containment lexical proxy 之下,**唔足以宣稱 layout_aware 確定優於 heading_aware**。`best` 只當相對信號,非裁決。

3. 💪 **更穩健嘅信號 = chunk-count 分化**:layout_aware **369** vs heading_aware **415** chunks(+12.5%)。heading_aware no-merge → 更多更細 chunk,**live 再證 ADR-0044**(同 W55 CB 的 28 vs 33 同方向,跨 6-doc 放大)。layout_aware 415→369 與 auto ingest 369 一致(auto 對呢批 docs 解析近 layout_aware)。

4. 📌 **要 recall 軸強辨別需要**:更狠 metric(strict chunk-id **人手** ground truth,非 lexical proxy)或更低 top-k(top-k=3/1 收窄槽位)→ carry-over eval-set-v1 SME。本期用 reindex 重跑換 top-k 成本高(每次 2× reindex),不做。

**caveat(承 W54/W55 + 新增）**:controlled(同一 frozen 30-QA 跨兩 strategy,消 W53 per-config confounding)BUT 仍 synthetic(LLM 出題+keywords)+ keyword-containment **lexical proxy**;且 **R3 multi-doc section_path collision**(跨 manual 同名 section merge)令 lexical-proxy caveat 更響(部分 QA 由跨 doc 合併 passage 生成)—— 但對兩 strategy 同等作用,relative signal 仍有效。

**Commits**:`8ee1322` feat(eval): W56 F2 A/B

---

### F3 — 修 + verify W53/W52 CLI event-loop bug

**F3.1 — W53 bug verify-then-fix(W55「不盲套 unverified fix」立場）**:

1. **先跑 unfixed 觀察**(`--sample 5` cheap)→ **crash 確認**,traceback 準確指向:
   ```
   backend/api/server.py:124  lifespan -> await audit_log_backend.prune_expired(90)
   backend/storage/audit_log_postgres.py:129  psycopg.AsyncConnection.connect
   psycopg.InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode.
       Please use ... loop_factory=asyncio.SelectorEventLoop(...)
   ```
   crash 喺 lifespan startup(未到 reindex,KB 未郁)。同 W55 一模一樣。
2. **套 fix**:`scripts/run_strategy_recall_comparison.py` main() 加 win32 `loop_factory=asyncio.SelectorEventLoop` guard(mirror W55 `run_controlled_ab_comparison.py` verified pattern;`sys` 已 import)。ruff check 通過;我加嘅行已 format-clean(pre-existing 長行未郁 per Karpathy §1.3 surgical,本來就唔 format-clean,我冇 introduce 新 failure)。
3. **重跑 fixed**(`--sample 30 --top-k 5`,background ~15 分鐘)→ **0 psycopg crash + exit 0**,跑完全程 2× reindex + per-config QA → **fix 驗證成功**。

**F3.2 — W53 self-retrievability cross-check(close W55 deferred F3.2)**:
```
W53 chunk-strategy self-supervised recall:
  strategy          recall@k   chunks  sample  errored
  layout_aware        0.9667      369      30        0
  heading_aware       0.9333      415      30        0
  best (self-retrievability): layout_aware
```
**方法學三角驗證(本期最有價值嘅發現)**:
- W54 controlled(shared frozen QA)gap = **0.67pp**(0.9917 vs 0.9850);W53 self-retrievability(per-config confounded QA)gap = **3.3pp**(0.9667 vs 0.9333)。
- W53 gap 大過 W54 **正正係 per-config confounding 放大**:heading_aware 更多更細 chunk(415)→ 自生 QA 嘅 answer keyword 更散 → self-retrieval recall 較低。W54 用同一 frozen set 消除呢個 confounding → 更誠實嘅細 gap。
- → **實證 W54 controlled 設計嘅價值**(confounded 方法會誇大 strategy 差異)。兩法方向一致(layout_aware 略前),chunk-count 369 vs 415 跨兩 run 一致(reindex 穩定)。
- W55 deferred 嘅原因(recall 飽和 → 重跑低 value)已由大 corpus 解除:W53 recall 0.93-0.97 非飽和,cross-check 有實質信息。

**F3.3 — W52 verify(`run_synthetic_recall.py`)**:
- 直接 run(`--index ekp-kb-w56-drive-ab-1-v1 --sample 30 --top-k 5`,不 reindex,cheap)→ **exit 0,0 crash**。
- **W52 不需修**:W52 唔用 `lifespan(app)`(直接砌 embedder+searcher,line 66-80,唔掂 postgres)→ 唔行 audit-log prune → 唔中 ProactorEventLoop+psycopg bug。印證靜態分析。Karpathy §1.3 surgical:**不加多餘 guard**(W52 未 break)。
- incidental:W52 strict Recall@5 = **0.7667**(mode breakdown strict 30 / keyword 0)vs W53 heading_aware strict 0.9333。差距主因 W52 嘅 bare searcher **無 reranker**(log `reranked=False`),W53/W54 用 lifespan engine **有 Cohere rerank**(`reranked=True`);加上 LLM 出題 stochasticity。→ **再證 synthetic recall 數字有 noise,唔好過度詮釋**(robust 信號仍係結構性 chunk-count 分化)。artifacts:`reports/w56-w52-synthetic-set.yaml` + `reports/w56-w52-recall.yaml`。

**F3.4 — 其他 live-path bug**:無。W54 / W53(fixed)/ W52 三個 CLI 全 exit 0,除 W53 event-loop guard 外無其他 live-path bug。3 個 smoke-deferred CLI 至此全部 live-exercised(W55 修 `run_controlled_ab_comparison.py`;W56 修 `run_strategy_recall_comparison.py` + 確認 `run_synthetic_recall.py` 不需修)。

**Commits**:`191a1f8` fix(eval): W56 F3 W53 guard + cross-check

---

### F4 — 結果記錄 + closeout

**收尾驗證**:
- eval test suite(controlled_comparison + strategy_comparison + synthetic_qa)= **20 passed**,0 regression(我只改 driver script,未改任何 tested module)。
- ruff check `run_strategy_recall_comparison.py` 通過;我加嘅 win32 guard 行已 format-clean(pre-existing 長行未郁 per Karpathy §1.3)。
- mypy:7 個 `import-not-found`(api.* / eval.* / storage.* runtime path-injection,mypy 靜態跟唔到)= pre-existing 跨模組 limitation(W55 reference 同款)→ **我改檔零新 error**。
- scratch script(`_scratch_list_indexes.py` / `_scratch_verify_kb.py`)已刪,不入 git。

**Phase Gate G1-G5**:

| # | Criterion | Verdict | 證據 |
|---|---|---|---|
| G1 | 6-doc fresh ingest + sources + section_path | **PASS** | 369 chunks(>>50)/ 6 source blobs / section_path 12/12 / 0 failed / 無 AP timeout |
| G2 | W54 A/B CLI 跑通 end-to-end | **PASS** | exit 0,兩 strategy recall + chunk 數 assemble |
| G3 | recall 軸辨別 strategy(消 W55 saturation)| **PASS(誠實 caveat)** | saturation 打破(1.0/1.0 → 0.9917/0.9850 兩個 <1.0 + delta);**但辨別力弱**(0.67pp gap 喺 noise floor,不宣稱 winner);強辨別需 strict ground truth |
| G4 | W53/W52 event-loop bug 修+verify | **PASS** | W53 verify-then-fix(crash 確認 → guard → 重跑 exit 0);W52 verify = 不需修 |
| G5 | 結果誠實解讀 | **PASS** | controlled-but-synthetic+lexical + multi-doc collision + 三角驗證 + synthetic recall noise caveat |

→ **Phase Gate = PASS**(G3 帶誠實 caveat:saturation 已破但辨別力弱)。

**R5 recheck(architectural-adjacent → ADR?)**:無。唯一 code change = W53 CLI win32 guard(driver,非 §3/§4 component / 非 vendor / 非 storage layout)→ 非 architectural → **無 ADR**(正確)。ingest/reindex = data ops 非 architectural。recall-discrimination 發現 = methodology observation,feed eval-set-v1(future),非架構決定。

**Day 1 Retro**:
- **做得好**:(1) 大 corpus 一次 ingest 6-doc 無 AP timeout(images off 減 embed 負載,驗證 W55 partial-acceptable 預案其實唔需用);(2) recall 軸成功脫離飽和(核心目標達);(3) **三角驗證發現**(W53 confounded gap 3.3pp > W54 controlled gap 0.67pp)實證 controlled 設計價值,係本期最高 signal;(4) verify-then-fix 紀律守住(W53 先觀察 crash 再 fix;W52 觀察 pass 後不盲加 guard);(5) 3-index budget 全程守住(查 Azure 確認,非靠 metadata)。
- **學到**:(1) recall@5 喺 369 chunks 仍近天花板 → keyword/strict synthetic 都唔夠狠,**真要辨別 strategy 必須 human ground truth 或更低 top-k**;(2) synthetic recall 有 run-to-run noise(W52 strict 0.7667 vs W53 0.9333,部分 reranker 有無、部分 LLM 出題);(3) heading_aware 跨 6-doc 放大 chunk 分化(415 vs 369,+12.5%)穩定再證 ADR-0044。
- **carry-over(W57+ 候選)**:(a) **eval-set-v1 human ground-truth recall**(strict chunk-id SME 標註,終極脫離 synthetic+lexical proxy);(b) lower-top-k 實驗(top-k=1/3 收窄槽位睇辨別力,但需 re-reindex 成本);(c) production default flip 仍待用戶決定(out-of-scope 本期);(d) Azure index cleanup 決定(見下)。

**Infra / 3-index budget 收尾狀態**:
- Azure Search **2 used / 1 free**:`ekp-kb-w54-live-ab-1-v1`(W55 CB)+ `ekp-kb-w56-drive-ab-1-v1`(本期,heading_aware 415 chunks,留住方便 W57+ top-k 實驗 / eval-set-v1)。**全程冇刪任何 index,守住 Free-tier 3-cap**。
- backend(8000)+ azurite(10000)背景運行。

**Commits**:`<F4 closeout commit>`(本 progress + checklist tick + plan status→closed + roadmap 修訂史)

---

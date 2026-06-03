# W44 — Chunker Image-Density Deep Fix · Progress

> Daily progress + decisions + commits;結尾 retro。

---

## Day 0 — 2026-06-03(kickoff,F0 gate pending)

### 做咗乜
- **三方 roadmap audit 收斂**(本 session)→ 用戶 pick (a) 開 W44 深度優先。
- **根因 live-verify**:Read `layout_aware.py` 全文,確認圖洪 ingestion 根因 = 圖按 section accumulator pile-on,text flush(`:207` hard-cap / `:213-218` soft-target)**唔 reset** `image_positions`,`_build_text_chunk:248` copy 全部 + `_merge_adjacent_shorts:323` concat → 圖密短 section 單 chunk carry 全部圖(實測 `ci=15=57`,memory #7)。全 file 零 per-chunk 圖數 cap。
- **doc-level reindex 非 stub** 確認(`documents.py:786-884`,真刪 + `_run_ingest_pipeline`)→ W44 驗證唔卡 Track A([AUDIT-B])。
- **ADR-0041 draft 建立**(Status: Proposed)+ ADR README index 更新(0041 row + next=0042)。
- **W44 plan / checklist / progress 建立**(R1 plan-before-implement)。

### 決定
- 切法 recommended = **A(image-aware flush + `max_images_per_chunk` soft cap)**,Alternatives B(sub-heading)/ C(image-anchored)/ D(hybrid)/ runtime-cap-only(W43 已做,不足)記 ADR-0041。**最終切法 + cap default 待 F0 gate Chris 拍板(決策 2)**。
- **F1+ code GATED on F0 gate**(H1 per §5.1 — chunker §3.3 change + re-index)。本日只 docs housekeeping。

### F0 gate — PASS 2026-06-03
Chris(AskUserQuestion)揀 **切法 D(混合:sub-heading 細分 + image cap 兜底)** + `max_images_per_chunk` default **8**(對齊前端 `INLINE_IMAGE_CAP=8`)+ approve H1 + ADR-0041 Proposed→Accepted。F1 code gate open。
- 切法 D 實際 scope(Karpathy §1.1 surface):heading 細分**已由現有 chunker 處理**,W44 重心 = image pile-on 修 + `_should_merge` image-guard + cap force-split;**唔重寫 heading 邏輯**(避免 over-build)。
- ⚠️ cap default 8 ≠ ADR-0037/0040 OFF-default,但對正常文件 no-op、只 cap flood、且 re-index 後先生效(影響面限圖密 chunk,intentional)。

### Blockers / carry-over
- Top risk(R6 已記 plan §4):重切改變所有 chunk 邊界 → eval no-regression gate(G3/G4)必過。

### Commits
- `e5d8830` docs(planning): W44 kickoff — ADR-0041 draft + phase artifacts(F0.1)
- `c219dfa` docs(adr): W44 F0 gate PASS — ADR-0041 Accepted(切法 D + cap 8)

---

## Day 1 — 2026-06-03(F1 + F2 — chunker 切法 D code + test)

### 做咗乜
- **F1 chunker 切法 D**(`layout_aware.py`):① `_reset_images_on_flush`(text flush 按 doc_order 分配圖,修 `:207` pile-on 根因)② `_force_flush_images`(image cap 8 force-split,延續 section_path)③ `_should_merge` image-count guard(防 ADR-0033 merge re-pile)④ `_flush_text_section` residual-image guard(force-split 後殘圖唔丟)。全部 gated on `max_images_per_chunk is not None` → cap=None 完全 bit-identical(pre-W44 pile-on)。
- **Settings**:`chunker_max_images_per_chunk: int | None = 8`;`server.py:99` startup 傳落 injected chunker(override seam)。
- **F2 test**(`test_chunker.py` +6):force-split / no-image-loss / cap=None pile-on / merge image-guard / residual flush / under-cap no-op。

### 驗證
- **pytest 30 passed**(6 新切法 D + 24 既有 regression 全綠 — ADR-0033 merge + BUG-017 image isolation 零 regression)。
- **ruff**:我新增 code clean(`layout_aware` reformatted)。`server.py` E402 ×30(truststore import pattern)+ `test_chunker` `import pytest` F401 = **pre-existing 非本次引入**(git diff 證 server 只改 line 99;test 純 append + 0 `pytest.` 用法),按 Karpathy §1.3 不刪。
- **mypy --strict**:我新增 method/field clean;17 pre-existing errors(parsers docling stub + `layout_aware` 既有 `object→ParagraphItem/Table` assign)非本次引入。

### Blockers / 下一步
- **F3 re-index + F4 eval 待做** — 需 backend venv restart 載新 chunker code(`python -m api.server` 無 reload)+ doc-level reindex 圖密文件 + eval no-regression(G3/G4)。涉及 stateful + eval ~18min。
- ⚠️ 重切 risk(R6):chunker 改變所有 chunk 邊界 → G3/G4 必過先算 PASS。

### Commits
- `8145656` feat(ingestion): W44 F1+F2 chunker image-density deep fix(切法 D)
- `64b78f6` docs(planning): roadmap A-E audit calibration(順手 commit,另一 session work)

---

## Day 1 cont — F3 re-index G1/G2 PASS

- **pre-flight** ✅ Langfuse 200 / Postgres SELECT 1 / backend venv restart(kill PID 18552 venv + 43128 system-python dual-process → venv cold start ready ~100s,全 component ok,新 chunker 載入)。
- **F3 reindex** AR `test-kb-20260531-v1`(doc `drive-user-manual-0601-ar-fna-ar-management-v0-03`)via doc-level reindex(`documents.py` real pipeline,[AUDIT-B] 證唔卡 Track A):68→**90 chunks**(force-split +22),223 img uploaded / 30 deduped。
- **G1 PASS**:max per-chunk 圖數 **57 → 8**(diag `_w44diag_imgcount.py` 讀 index)。
- **G2 PASS**:分佈 baseline 多 mega(57/27/25/23/18/16/14/12/12/11)→ 重切後 0 個 >8、22 chunks at cap 8、dist 集中 ≤8;223 unique 全保留(per-chunk 總和 252 ≥ 223,無丟失;278→252 = pile-on cross-chunk dup 亦消除)。
- **下一步 F4**:reindex `drive_user_manuals`(含 AR + 5 模組)→ `/eval/run` 30q no-regression(G3 R@5 / G4 RAGAs)對比 W43 baseline(recall 1.0/faith 0.9956/corr 0.8489/0 attention)。throwaway diag script `_w44diag_imgcount.py` F4 後刪。

---

## Day 1 cont — F4 撞 eval-harness decay → 全 rigor 重建 track(user pick)

### drive 重建(連圖,新 chunker)
PATCH drive config `extract_embedded_images: false→true`(揭 W43 drive 0 圖 = text-only config,非 azurite)。6 doc doc-level reindex 連圖(AP 第一次 embed Azure transient timeout,POST retry 即成):drive **287→369 chunks** / total 圖 **0→1012** / max per-chunk **8**(diag confirm force-split 守 cap)。

### eval run 結果(eval-set-v1-draft 55q,~30min wall)
recall_at_5 0.8848 / faith 0.8583 / corr 0.7061(47 eval / 3 errored)。表面 vs W43 baseline 顯著跌,但**根因 = eval-harness decay,非切法 D**:
1. **Cohere rerank 401**(Q008/Q030/Q038)— eval 連打 47 query 觸 Azure Cohere rate-limit → retrieval/rerank fail → empty context → recall/faith 假跌。單 query Q019/Q030(eval 中 401)重跑 healthy(cohere-v4.0-pro,5-11 cit)→ 證 transient rate-limit,非 key。
2. **eval-set-v1-draft = DRAFT,Q14 SME validation pending(自 W2)**:55q 全部 `acceptable_chunk_ids` empty + `expected_answer_keywords` 0 + `validated:false`。recall 喺 empty-GT 下 unreliable(W43 recall 1.0 都係 empty-GT fallback)。

### 切法 D no-regression — 三源證實(非 RAGAs aggregate)
- G1/G2 圖洪 57→8 硬證
- pytest text token 邊界 cap=None/under-cap bit-identical(force-split 只新增 image-carrier chunk,唔改既有 text chunk)
- 單 + 3 sanity query(AP 圖密 14cit / GL 13cit / Budget 11cit,跨模組)retrieval 全 healthy → image-carrier chunk 冇 push out 真 content

### 決定(user AskUserQuestion ×3 → 全 rigor 重建)
gold RAGAs no-regression 需:(1) SME-validated GT(Q14,Chris pick) + (2) before-baseline 重建(舊 chunker cap=None,現已 reindex 走) + (3) Cohere throttle。User pick **全 rigor 重建(跨多 session)**。F4 擴展 gold-eval rigor sub-track(F4.4-F4.9),原 F4.1-F4.3 superseded。工具齊:`scripts/discover_chunk_ids.py` + `scripts/validate_eval_set.py`。**SME block point F4.6**:Chris pick 30 main acceptable_chunk_ids — AI 做唔到 gold GT。

### Commits
- `ada4100` docs(planning): F3 G1/G2 PASS(之前)
- `d2485ae` docs(planning): F4 eval-harness decay finding + rigor track pivot

---

## Day 1 cont — F4.4 Cohere rate-limit throttle/retry(eval infra)

### 做咗乜
- **根因 ground**:eval 兩個 query loop(`runner.py:_evaluate_query` recall + `orchestrator.py:build_ragas_samples` RAGAs)都 call `engine.retrieve` → reranker。`cohere.py:78` 已有 3-retry/~7s tenacity backoff,但 eval 連打 47 query 觸發嘅 Azure rate-limit window 超過 7s + **query 間零 spacing** → retry 耗盡仍拋 401(misleading rate-limit signal,單 query healthy)。
- **修法(eval-only,唔掂 production reranker per F4.4 plan scope)**:新 `backend/eval/throttle.py` `retrieve_with_throttle()` = ① per-query throttle spacing(env `EVAL_RETRIEVE_THROTTLE_S` default 1.0s,call-time 讀,主修避 burst)② 外層 `AsyncRetrying` longer-backoff(`wait_exponential(2, min=2, max=30)` × default 5 attempts,**只** retry 401/429/`TransportError`,真 4xx/generic error 即 reraise 唔燒 attempt)。`runner.py` + `orchestrator.py` 兩 loop 改用 helper;`conftest.py` 設 throttle=0(test 唔 sleep)。
- **`tenacity` 既有重用 dep**(H2 ✅ 無新增);Karpathy §1.2 唔改 production `cohere.py`(scope 守)。

### 驗證
- **pytest 41 passed**(test_eval_throttle +7 新 + test_eval_runner/ragas/endpoints 34 既有 0 regression)。
- ruff:新增 5 file all clean。mypy --strict:`throttle.py` 本身 0 error(13 error 全 transitive import pre-existing — `retrieval_engine.py`/`observe.py`/`reranker/base.py`,非本次引入,同 W44 F1 既有一致)。

### Blockers / 下一步
- **F4.5**:跑 `scripts/discover_chunk_ids.py` 生成 30 main candidate chunk_ids(我做)→ 交 **F4.6 SME block**(Chris pick `acceptable_chunk_ids` + `validated:true`,AI 做唔到 gold GT)。
- F4.4 default 1.0s throttle × 47 query × 2 loop ≈ +94s eval wall(RAGAs judge ~30min 主導,可接受)。F4.7/F4.8 重建 eval 時 backend env 可調 `EVAL_RETRIEVE_THROTTLE_S` override。

### Commits
- `4b23494` feat(eval): W44 F4.4 eval-only retrieve throttle + rate-limit backoff

---

## Day 1 cont — F4.5 GT discovery rework + run → R3 deviation(GT 類型)

### 做咗乜
- **F4.5 ground 揭兩問題**(Karpathy §1.1 + R6 recursive plan-text 自檢):
  1. `discover_chunk_ids.py` **W2-stale** — `engine.retrieve(query, top_k)` 缺 ADR-0018 mandatory `kb_id`(`retrieval_engine.py:124` 無 default)→ 跑會 `TypeError`;硬編 eval-set-v0 + default index。
  2. **更核心(plan 內在矛盾)**:chunk_id GT 係 **chunker-specific** — cap=None(F4.7)同 cap=8(F4.8)re-chunk 出唔同 chunk 邊界(AR doc +22 sub-chunk,編號全 shift),cap=8 force-split sub-chunk 喺 cap=None index 根本唔存在 → 單一 `acceptable_chunk_ids` set 無法 valid score 兩個 index。F4.9「同 GT 唯一變 cap」對 chunk_id GT 做唔到。
- **STOP+ask → user pick 內容導向 GT(keyword + optional reference_answer)**:chunker-agnostic → 兩 re-chunk 用同一套 GT(keyword-mode recall + RAGAs context_recall)valid 比較;順帶永久修 eval-set-v1-draft empty-GT(Q14 自 W2 pending)。
- **R3 deviation**:checklist F4.5-F4.9 語義 + plan §7 changelog 更新(chunk_id strict → content-based)。
- **discover script rework**:修 `kb_id`(ADR-0018,per-query override + `kb_id_to_index_name` 解析 per-KB index)+ argparse(--eval-set/--kb-id/--out/--top-k)+ 輸出改 surface top-k chunk_text preview(300 char)+ section_path + chunk_title 輔助 SME 寫 keyword。`RetrievalEngine(embedder, searcher)` 無 wire reranker → hybrid-only → **無 Cohere 401 burst 風險**。
- **跑** → `reports/eval-set-v1-draft_gt_candidates.yaml`:**50 main query**(非估算 30)× top-8,**0 error / 0 empty top_k**,index `ekp-kb-drive-v1`,~50s wall。

### 驗證
- ruff:`discover_chunk_ids.py` clean。報告結構:每 query 有 `current_expected_keywords` + `discovered_top_k`(chunk_id/doc_id/section_path/chunk_title/score/300-char preview)— 對 SME 寫 keyword/reference 充分。

### Blockers / 下一步
- **F4.6 = 🚧 Chris SME block**(hand off):為 50 main query 寫 `expected_answer_keywords`(+ optional `reference_answer`)+ `annotation.validated:true`,基於 `reports/eval-set-v1-draft_gt_candidates.yaml` 嘅 top-8 preview。AI 做唔到 gold GT。
- F4.6 完成後我做 F4.7(cap=None reindex + eval)/ F4.8(cap=8 + eval)/ F4.9(隔離對比 + gate verdict)。

### Commits
- `d2e1b36` chore(eval): W44 F4.5 GT discovery rework + run(content-based GT pivot)
- `f8ff53a` docs(planning): F4.6 handoff note(報告 gitignored/local + regenerable)

---

## Day 1 cont — F4.6a AI 草擬 GT proposal(分工:AI 草擬→Chris 複核)

### 做咗乜
- User 困惑「F4.6 具體做咩」→ 用 Q001 真實例子拆解 + 提出更輕分工 **AI 草擬→Chris 複核**(取代「Chris 由零寫 50 條」)。User pick 此分工。
- 讀晒 `reports/eval-set-v1-draft_gt_candidates.yaml` 50 query × top-3 chunk(用 throwaway condenser 壓成 600 行精華,已刪)。逐條 propose 收緊嘅 `expected_answer_keywords`(3-4 個同一正確 section 內共現嘅具體詞:function 名/選單路徑/section code 如 AR01/FA06,避免 generic「AR」「customer」零分辨力)+ 1 句 `reference_answer`。
- 輸出 `docs/01-planning/W44-chunker-image-density-deep-fix/F4.6-gt-proposal.md`(由 gitignored reports/ 移入 phase folder = tracked,hand-off 跨 session durable)。
- **Flag 分佈 🟢30 / 🟡11 / 🔴9**:
  - 🟢 語料有清晰對應 section,信心高。
  - 🟡 query 模糊/跨模組但有合理 section。
  - 🔴(Q042/Q043/Q045/Q046/Q047/Q048/Q049/Q050/Q054)troubleshooting/跨模組 synthesis,語料覆蓋弱 → **正正係 F4 eval below-threshold 嗰批**,證明係 **eval-set query 設計問題(W4 synthetic user-collected query 問語料無答嘅嘢)非 chunker regression** —— 呼應 F4 finding。

### 誠實邊界
- AI 唔係 Ricoh D365 財務 SME;proposal keyword 由 retrieved 文字+section 結構推導,反映「邊段答到」但「咩係*正確*答案」需 Chris domain 把關。`validated:true` 仍由 Chris 確認 → gold 成立。

### Blockers / 下一步
- **F4.6b = 🚧 Chris 複核**(對 proposal ✅剔/✏️改/❌剔,🔴 嗰 9 條決定 keyword vs `expected_refusal`)→ 我 apply 入 eval-set + flip validated → 接 F4.7。

### Commits
- (F4.6a commit 見下)

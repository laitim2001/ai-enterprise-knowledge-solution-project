# W44 — Chunker Image-Density Deep Fix · Plan

> **性質**:single-phase implementation(Tier 1,純 process 軸)。
> **錨點**:ADR-0041(**Proposed** — F0 gate 待 Chris confirm H1 + 決策 2 切法 + Accept)+ ROADMAP-per-kb-tunable-config.md §3 W44 + [AUDIT-A/B/E]。
> **Kickoff**:2026-06-03(W43 closeout 後,深度優先 per roadmap §6)。
> **Owner**:Chris(技術 Lead)。
> **狀態**:`active`(F0 gate PASS 2026-06-03 — 切法 D + cap 8;F1 code gate open)。

---

## §1 Phase Scope

解 W43 留低嘅圖洪水 **ingestion-bound 根因**(ADR-0040 R6 catch 5 split-out):圖密但 text 短嘅 section 被切成單一 chunk carry 全部圖(實測 `ci=15=57`)。令圖片**隨 `doc_order` 分配落 sub-chunk + 加 per-chunk 圖數 soft cap**,使檢索攞到嘅 citation chunk 圖數受控、per-image section 更精準。

**唔做(out-of-scope,見 §6)**:per-KB 化圖數 cap(W44 暫全域 knob)/ 真 KB-level reindex pipeline(W45)/ vision 語意揀圖(Tier 2)/ sub-heading 細分(切法 B,視 eval 結果再升)。

---

## §2 Deliverables

| ID | Deliverable | 說明 |
|---|---|---|
| **F0** | H1 STOP+ask gate | Present ADR-0041 H1 boundary + 決策 2 切法選項 + 風險(重切影響 recall)→ Chris confirm + Accept → ADR Proposed→Accepted。**F1+ GATED on F0 PASS**。 |
| **F1** | Chunker 切法 D(混合) | `layout_aware.py`:**(A 核心)** text flush 同步 reset `image_positions`(修 `:207`/`:213-218` pile-on)+ `max_images_per_chunk` soft cap **8** force-split(延續 `section_path`,prev/next 連續);**(D 第二支柱)** `_should_merge` 加 image-count guard(merge 後超 cap 唔 merge)防圖密短 sub-section 合併;新 `Settings.chunker_max_images_per_chunk=8` knob(`None`/0 = preserve)。**唔重寫 heading 邏輯(已存在),守 simplicity**。 |
| **F2** | Chunker unit test(H6 mandatory) | 新 image-flush + cap-split 邏輯 test + 既有 ADR-0033 merge / BUG-017 sibling-guard **無 regression** test。 |
| **F3** | Re-index + presentation 驗證 | 用現成 doc-level reindex(`documents.py:786-884`,[AUDIT-B])對圖密文件重切;確認最大 single-chunk 圖數 ≤ cap + 圖分佈改善。 |
| **F4** | Eval no-regression gate(top risk) | R@5 + RAGAs(faithfulness/correctness)前後對比,確認重切**唔降** retrieval 質素(R6 適用)。 |
| **F5** | Closeout | plan/checklist/progress flip + retro + ADR-0041 validation note + architecture.md §3.3 amend(inline-tag 沿 §3.4/§3.7 precedent)+ session-start §10 W44 row + roadmap §3 W44 done。 |

---

## §3 Acceptance Criteria + Phase Gate

| Gate | Criterion | 量度 |
|---|---|---|
| **G1** | 圖密文件重切後最大 single-chunk 圖數 ≤ **8**(cap default per F0) | 直接讀重切後 index `embedded_images_json` count |
| **G2** | 圖分佈改善(per-chunk 圖數 p95 顯著下降 vs 重切前) | 重切前後 chunk 圖數分佈對比 |
| **G3** | **無 retrieval regression**:R@5 唔跌(±tolerance) | `/eval/run` recall_at_5 前後對比 |
| **G4** | **無答案質素 regression**:RAGAs faithfulness/correctness 唔跌(±tolerance) | `/eval/run` 4-metric 前後對比 |
| **G5** | Chunker unit test 全 pass(新 + 既有無 regression)+ 守 §3.3 layout-aware(唔變 character-based)+ H4(無 vision relevance) | pytest + code review |

**Gate verdict policy**:全 G PASS → **PASS**;G3/G4 marginal MISS(< tolerance,measurement-experiment)→ **PARTIAL**(Chris 拍板);G3/G4 顯著 regression → **FAIL**(回退 + 重評切法)。tolerance 沿 W26-W28 RAGAs ±2pp 慣例,F0 確認。

---

## §4 R6 Pre-active-flip 5-step Verification(Day 0,plan-text 自檢)

1. **讀 plan literal acceptance criteria** — done(§3 G1-G5)。
2. **Grep code base / mockup**:根因引用 `layout_aware.py:146/207/213-218/248/323` — **已 live-verify**(本 session Read 全文確認 image pile-on + 零圖數 cap);doc-level reindex `documents.py:786-884` 非 stub — **已 verify**;ImageRef.source_section stamp(BUG-026)機制 — memory #3 + indexing/schemas.py 確認。
3. **Surface mismatch(Karpathy §1.1)**:⚠️ 切法 A force-split 可能切斷語意步驟(step + 截圖跨 chunk)→ F0 gate 必須 surface + 由 eval(G3/G4)把關;cap default 未定 = 決策 2。
4. **Document deviation(§7 changelog)**:F0 gate 結果(切法 + cap default)落 §7。
5. **Adjust acceptance criteria**:cap 具體值待 F0 拍板後回填 G1。

**Recursive trigger 檢查**:plan-text 無引用 pre-W43 stale surface — 全部錨點(ADR-0041 / roadmap [AUDIT] / memory #7/#8)皆 2026-06 當期 + code live-verified。✅ 無 contamination。

---

## §5 H1 Assessment(STOP+ask 必經)

**H1 trigger 確認**(CLAUDE.md §5.1):
- ✅ 改 `architecture.md §3.3` chunking philosophy(image-attach 邏輯 + per-chunk 圖數 cap)
- ✅ 需 re-index 先生效(改 storage 內容,雖非 schema)
- ✅ 改 chunker 屬 §3 RAG Core component(C01 ingestion)

→ **F1 code 必須 F0 gate(Chris confirm + ADR Accept)後先開**。本 plan + ADR-0041 draft commit 屬 docs housekeeping(R1 plan-before-implement),**未** implement。

**H4 邊界守護**:W44 只做位置/章節切分(Tier 1 上限);vision 語意揀圖明確 out-of-scope(§6)。

**H6**:chunker ∈ `backend/ingestion/chunker/` → F1 必同步 F2 test(mandatory)。

---

## §6 Out-of-scope / Carry-over

- 🚧 **per-KB 圖數 cap**(降 `chunker_max_images_per_chunk` 落 `KbConfig`)→ 後期,沿 ADR-0040 模式;W44 守 simplicity 先全域 knob。
- 🚧 **真 KB-level reindex pipeline + v1→v2 原子切換**(W45,觸 Track A production 層,per [AUDIT-C])。
- 🚧 **切法 B sub-heading 細分 / 切法 D 混合** → 若 W44 eval(G3/G4)顯示切法 A 語意切斷則升(ADR-0041 Alternatives 已記)。
- 🚫 **vision / 視覺內容語意揀圖**(Layer C 深層)= Tier 2 H4 邊界(per [AUDIT-E]),需新 ADR + stakeholder。

---

## §7 Changelog

- **2026-06-03 kickoff**:plan + ADR-0041 draft(Proposed)建立;F0 gate pending Chris confirm H1 + 決策 2 切法 + Accept。
- **2026-06-03 F0 gate PASS**:Chris 揀**切法 D(混合:sub-heading 細分 + image cap 兜底)** + `max_images_per_chunk` default **8**(對齊前端 `INLINE_IMAGE_CAP=8`)+ approve H1 + ADR-0041 Accept。G1 cap 回填 8;F1 deliverable 對齊切法 D(加 `_should_merge` image-guard);狀態 draft→active。
- **2026-06-03 F1+F2+F3 done**:切法 D code(commit `8145656`)+ pytest 30 passed;F3 reindex AR `test-kb-20260531-v1` G1/G2 PASS(max 57→8,commit `ada4100`)。
- **2026-06-03 F4 deviation(R3)**:單次 eval 撞 **eval-harness decay**(Cohere 連打 rate-limit 401 + eval-set-v1-draft Q14 SME-validation pending empty-GT + before-baseline reindex 走)→ RAGAs aggregate(recall 0.8848/faith 0.8583)唔可信。切法 D no-regression 改由**三源證實**(G1/G2 硬證 + pytest text bit-identical + 單/3 sanity query healthy)。**User pick 全 rigor 重建** → F4 擴展 gold-eval rigor sub-track(F4.4 Cohere throttle / F4.5 discover candidates / F4.6 SME GT[Chris block] / F4.7 cap=None before / F4.8 cap=8 after / F4.9 隔離對比),原 F4.1-F4.3 superseded。**跨多 session**,F4.6 需 Chris SME pick 30 main `acceptable_chunk_ids`。順帶:drive config `extract_embedded_images` false→true(修 W43 0 圖)+ drive 重建 287→369 chunks/0→1012 圖/max 8。

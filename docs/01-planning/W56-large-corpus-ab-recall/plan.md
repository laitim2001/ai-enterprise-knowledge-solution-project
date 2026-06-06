---
phase: W56-large-corpus-ab-recall
name: "Large-corpus controlled A/B — recall 軸真辨別 strategy(消 W55 saturation artifact)+ 修/verify W53/W52 CLI event-loop bug"
sprint_week: W56
start_date: 2026-06-06
end_date:
status: active
spec_refs:
  - W54 (controlled_comparison.py — controlled A/B,本期跑大 corpus)
  - W55 (run_controlled_ab_comparison.py live-verified;本期換大 corpus 消 recall saturation)
  - W53 (run_strategy_recall_comparison.py — 缺 win32 guard,本期修+verify;順帶 close W55 F3.2 deferred self-retrievability cross-check)
  - W52 (run_synthetic_recall.py — 缺 win32 guard,但不用 lifespan/psycopg,本期 run 先 verify 再決定修不修)
  - W46 / ADR-0043 (run_kb_reindex + source_store — fresh KB 經 -sources 存原始檔)
  - ADR-0044 (heading_aware vs layout_aware chunk strategy)
prior_phase: W55-live-verify-strategy-ab
combined_vision: "W55 把 controlled A/B live-verified,但小 corpus(28-33 chunks << fetch_k=50)令 recall 飽和 = corpus-size artifact,唔辨別 strategy。本期換大 corpus(全 6-doc DRIVE,~369 chunks >> fetch_k=50)令 recall 軸真辨別;順帶修 W53/W52 CLI 同款 event-loop latent bug + close W55 F3.2 deferred cross-check"
---

# Phase W56 — Large-corpus controlled A/B recall(辨別 strategy)+ W53/W52 CLI 修

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-06 — explicit「執行 W56 大 corpus re-run」;AskUserQuestion 揀「全 6-doc DRIVE rebuild」)

## 1. Scope

把 W55 已 live-verified 嘅 controlled A/B 由 **小 corpus(saturated)** 換成 **大 corpus**,令 recall 軸真正辨別 layout_aware vs heading_aware;**順帶**修 + verify W53/W52 兩個 CLI 同款 event-loop latent bug。

**Pre-flight 發現(think-before / R6)**:
1. **Azure Search live index 直接查 = 1 個**(`ekp-kb-w54-live-ab-1-v1`,W55 CB)→ **2 free slot**(Free-tier 3-cap)。
2. **`drive_user_manuals` KB metadata 係 stale**:metadata archived=false / 369 chunks,但其 index **唔喺 Azure 上**(已被清);且 last_indexed 2026-06-04 < W46 source-store(06-05)→ **冇 `-sources`** → reindex 跑唔到。**不可 reuse**。
3. 所以 W56 **必須 ingest fresh KB**(post-W46 → `-sources` 自動存)→ reindex 跑得 → A/B + W53 跑得通。
4. fresh KB = **1 個 index**(in-place reindex 跨 strategy 同一 index)→ 開完 **2 used / 1 free**,完全喺 Free-tier 3-cap budget 內,**不需刪任何 index**。

**Chris 決策**:corpus = **全 6-doc DRIVE rebuild**(AR/AP/CB/FA/BM/GL,~369 text chunks,辨別力最強)。**image extraction OFF**(純文字 keyword-recall 測試唔需要圖,慳 screenshot 成本/時間;W55 CB 亦是純文字)。

**本期交付**:
- ingest fresh KB `w56-drive-ab-1`(6 DRIVE manuals,images off)→ 驗 total_chunks >> fetch_k=50 + sources 存到 + section_path 有值。
- 跑 W54 `run_controlled_ab_comparison.py --strategies layout_aware heading_aware` → recall 報告。**核心驗證:recall 軸依家辨別**(recall < 1.0 或 strategy delta 出現 = 消咗 W55 saturation artifact)。
- 修 + verify W53/W52 CLI event-loop bug:W53 套 win32 SelectorEventLoop guard(mirror W55 reference)+ full run(順帶 close W55 F3.2 deferred self-retrievability cross-check,依家非 saturated);W52 直接 run(cheap,不 reindex)先 verify 再決定修不修(不盲套 unverified fix)。
- 誠實解讀(controlled but synthetic + lexical proxy;multi-doc section_path collision 新 caveat;recall 辨別 vs W55 saturation 對比)。

**Out-of-scope**:人手標註 ground-truth recall(eval-set-v1 SME,另議);per-document scope;production v1→v2 default flip;改任何現有 KB(只 ingest 新 KB)。

**Sprint origin**:W55 carry-over「大 corpus re-run 令 recall 軸辨別 strategy + 修 W53/W52 同款 event-loop bug」;Chris 2026-06-06 explicit pick「全 6-doc DRIVE rebuild」。

## 2. Key Design / Execution Notes

- **W53 修**:line 143 `asyncio.run(...)` → win32 加 `loop_factory=asyncio.SelectorEventLoop`(identical pattern 已喺 W55 `run_controlled_ab_comparison.py` verified)。高信心:W53 用 `lifespan(app)` → psycopg audit-log prune → 同款 ProactorEventLoop incompatibility。
- **W52 修(conditional)**:W52 **不用 lifespan / 不掂 postgres**(直接砌 embedder+searcher)→ 未必中 event-loop bug。**先 run 觀察**;只有實際 break 先加 guard(Karpathy §1.1 surgical,不應用 unverified fix)。
- **KB**:`w56-drive-ab-1`,6 docs via API multipart(`curl.exe -F`;PS 5.1 冇 `-Form`),sequential upload。config:chunk_strategy=auto / extract_embedded_images=false / slide_screenshots=false。
- **402 繞**:backend 已設 `HYBRID_USE_SEMANTIC_RANKER=false`(Free-tier semantic cap)。
- **unicode 繞**:CLI run 加 `PYTHONIOENCODING=utf-8`(cp1252 console crash)。
- **成本知情**:真 Azure OpenAI embedding — ingest(~369 chunk × 1)+ W54 A/B(2× reindex)+ W53(2× reindex)= ~4× re-embed + ingest;judge(gpt-5.4-mini ~30 QA × 多次生成);bounded by 單 KB text-only(images off)。reindex sequential、耗時(慢非 hang,只輪詢)。
- **AP timeout 風險**:舊 drive_user_manuals AP 模組曾 embed APITimeoutError → 若 fresh ingest AP 再 fail,5 docs(~300 chunks)仍 >> fetch_k=50 → **partial ingest 可接受**(G1 唔 fail,記低)。
- **無新 vendor/dep**;judge 維 gpt-5.4-mini。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance**:plan/checklist/progress committed(R1);pre-flight 4 發現 + 決策(6-doc / images off / 2 free slot)記 progress
- **Owner**:AI

### F1 — Ingest fresh KB(6 DRIVE manuals)
- **Acceptance**:`POST /kb` 建 `w56-drive-ab-1`(images off)→ sequential multipart upload 6 docs → ingest;total_chunks >> fetch_k=50(target ≥200;AP timeout → partial 可接受,記低)+ `-sources` 有 docs(reindex 前提)+ section_path 有值(controlled A/B 文字錨點前提)
- **Owner**:AI

### F2 — 跑 W54 controlled A/B(大 corpus,核心)
- **Acceptance**:`run_controlled_ab_comparison.py --kb-id w56-drive-ab-1 --strategies layout_aware heading_aware --sample 30 --top-k 5` 跑通 → 報告(per strategy recall + chunk 數 + best)捕捉入 progress;**核心:recall 軸辨別**(recall < 1.0 或 strategy delta 出現,消 W55 saturation;若仍飽和則明標原因);frozen eval-set YAML 落 reports/
- **Owner**:AI

### F3 — 修 + verify W53/W52 CLI event-loop bug
- **Acceptance**:(a) W53 套 win32 SelectorEventLoop guard + full run 跑通 exit 0 → 順帶 close W55 F3.2 deferred self-retrievability cross-check(per strategy recall,非 saturated);(b) W52 直接 run(cheap)→ 若 break 套同款 guard,若 pass 記「不需修」;(c) 任何其他 live-path bug 最小修記 changelog(非 architectural)
- **Owner**:AI

### F4 — 結果記錄 + closeout
- **Acceptance**:progress 記 W54 A/B + W53 cross-check 結果 + 誠實解讀(controlled-but-synthetic+lexical;multi-doc section_path collision caveat;recall 辨別 vs W55 saturation 對比)+ 所有 bug/fix;Phase Gate + retro + checklist tick / 🚧;R5 recheck;doc-sync(roadmap 修訂史 + session-start §10 local-only)
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Block closeout? |
|---|---|---|---|
| G1 | 6-doc fresh ingest 成功 + sources 存到 + section_path 有值 | total_chunks >> 50(≥200;AP partial 可接受)+ -sources blob + section_path | Yes |
| G2 | W54 controlled A/B CLI 跑通 end-to-end(同一 frozen set 跨 2 strategy)| 報告 assemble + 兩 strategy recall 數 | Yes |
| G3 | recall 軸辨別 strategy(消 W55 saturation)| recall < 1.0 或 strategy delta 出現;若仍飽和明標原因 | Yes |
| G4 | W53/W52 event-loop bug 修+verify(W53 guard+run;W52 run 先驗)| 兩 CLI 結局記低 + 最小修(非 architectural)| Yes |
| G5 | 結果誠實解讀(controlled-but-synthetic+lexical;multi-doc collision caveat;辨別 vs 飽和對比)| progress review | Yes |

## 5. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | AP 模組 embed timeout(舊 drive_user_manuals 試過)| Med | Low | partial ingest 可接受(5 docs ~300 chunks 仍 >> 50);記低;非 phase fail |
| R2 | 4× reindex + ingest 大 corpus → embedding 成本/時間重 | High | Low | 單 KB text-only(images off);sequential 慢非 hang 只輪詢;若過慢 surface |
| R3 | multi-doc section_path collision(build_shared_eval_set section-path-only grouping merge 跨 doc 同名 section)| Med | Low | methodology caveat(令 controlled-but-lexical caveat 更強)非 fail;記低 |
| R4 | Free-tier 402 / Azure 成本 | Med | Low | semantic off + images off;單 KB bounded |
| R5 | W53/W52 CLI 其他 live-path bug(從未 live 跑全)| Med | Med | 逐步跑;最小修記 changelog;非 architectural(→ STOP per H1)|

## 6. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-06 | Initial plan | W56 kickoff;Chris explicit「執行大 corpus re-run」+ AskUserQuestion 揀「全 6-doc DRIVE rebuild」。Pre-flight 查 Azure = 1 live index/2 free;drive_user_manuals metadata stale 不可 reuse → fresh 6-doc KB(images off) | Chris |

---

**Lifecycle reminder**:大 corpus live verification + 2 個 CLI latent-bug 修。W53 guard = mirror W55 verified pattern(高信心);W52 先 run 後修(不盲套)。誠實解讀承 W54/W55 framing(controlled-but-synthetic+lexical)+ 新增 multi-doc section_path collision caveat。CLI 其他 live-path bug 最小修(architectural → STOP per H1)。

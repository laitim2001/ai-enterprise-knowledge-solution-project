---
phase: W55-live-verify-strategy-ab
name: "Live Verification — W53/W54 chunk-strategy recall harness 對真 KB(smoke-deferred 實證)"
sprint_week: W55
start_date: 2026-06-06
end_date:                     # set at closeout
status: active
spec_refs:
  - W54 (controlled_comparison.py — controlled A/B,本期 live 驗證)
  - W53 (strategy_comparison.py — self-retrievability,本期可選 cross-check)
  - W46 / ADR-0043 (run_kb_reindex + source_store — reindex 由 -sources re-parse)
  - backend/eval/controlled_comparison.py + scripts/run_controlled_ab_comparison.py (本期實跑)
prior_phase: W54-controlled-ab-recall-comparison
combined_vision: "W52/W53/W54 harness 一直 smoke-deferred(judge cred + indexed KB + 原始檔 + 402 繞);本期把 controlled A/B(layout_aware vs heading_aware)真正跑一次,產出 live 實證"
---

# Phase W55 — Live Verification:chunk-strategy recall harness 對真 KB

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-06 — explicit「開始執行 controlled A/B + heading_aware live eval 對真 KB」;清空 Azure Search index 騰空 Free-tier 3-cap)

## 1. Scope

把 W54 **controlled A/B**(W53 嚴謹版)由 smoke-deferred 變 **真跑一次**,產出 live 實證:layout_aware vs heading_aware 喺真 KB 上嘅 keyword-mode recall。

**Pre-flight 發現(think-before / R6 — 決定路徑)**:
1. **現有 9 個 indexed KB 全部冇 `-sources` container**(W46 source-store 2026-06-05 先 landed,之前 ingest 嘅 KB 冇存原始檔)→ `run_kb_reindex` download `-sources` re-parse 會 skip 晒 → **rich KB(drive_user_manuals 等)跑唔到 reindex-based 比較**。
2. 只有 `test-kb-20260531-v1` 有 1 個 source blob(2-doc KB 中得 1 個)→ 不適合乾淨比較。
3. **原始 DRIVE manuals 喺 `docs/06-reference/01-sample-doc/`**(6 份 + DCE + smoke)→ **ingest fresh KB 會經 W46 source-store 存原始檔** → reindex 跑得 → 乾淨 live 比較。
4. 用戶清空 Azure Search index(Free-tier 3-cap)→ in-place reindex 同一 KB 只用 **1 個 index**,綽綽有餘。

**Chris 決策**:Option 1 — **一份中型 DRIVE manual 開 fresh KB**(CB Cash & Bank 1.8MB;最輕 real 多-section,bounded 成本,足夠 chunking 信號)。

**本期交付**:
- ingest fresh KB `w54-live-ab-1`(CB manual)→ 驗 chunks indexed + sources 存到。
- 跑 W54 `run_controlled_ab_comparison.py --strategies layout_aware heading_aware` → 捕捉 recall 報告(**live 實證**)。
- 記錄結果 + 任何 live-path bug(CLI 從未 live 跑過)+ 誠實解讀(controlled but synthetic + lexical proxy)。
- (可選,若 clean)W53 `run_strategy_recall_comparison.py` self-retrievability cross-check。

**Out-of-scope**:人手標註 ground-truth recall(W55+ 另議);per-document scope;production v1→v2;改任何現有 KB(只 ingest 新 KB)。

**Sprint origin**:W54 carry-over「controlled A/B live eval 對真 KB(smoke-deferred)」;Chris 2026-06-06 explicit pick。

## 2. Key Design / Execution Notes

- **無新 code**(預期):純跑已 ship 嘅 W54/W53 harness + CLI;若 live-path 有 bug → 最小修(記 changelog;若 architectural → STOP per H1)。
- **KB**:`w54-live-ab-1`,doc = `DRIVE_User Manual_0604(CB)…v0.02.docx`(1.8MB)。ingest via API multipart(`curl.exe -F`;PS 5.1 冇 `-Form`)。
- **402 繞**:backend 起動已設 `HYBRID_USE_SEMANTIC_RANKER=false`(Free-tier semantic cap)。
- **成本知情**:真實 Azure OpenAI embedding(ingest + 2× reindex re-embed)+ judge(gpt-5.4-mini ~30 passage QA 生成)+ recall retrieve(~30Q × 2 strategy);bounded by 單 mid-size doc。
- **reindex in-place**:sequential,KB 留喺最後 strategy(heading_aware)狀態 —— offline eval 操作,可接受(fresh KB 非 demo)。
- **無新 vendor/dep**;judge 維 gpt-5.4-mini。

## 3. Deliverables

### F0 — Phase kickoff
- **Acceptance**:plan/checklist/progress committed(R1);pre-flight 4 發現 + 決策記低
- **Owner**:AI

### F1 — Ingest fresh KB(CB manual)
- **Acceptance**:`POST /kb` 建 `w54-live-ab-1` → multipart upload CB docx → ingest 成功(`total_chunks > 0`)+ `-sources` container 有該 doc(reindex 前提)+ section_path 有值(controlled A/B 文字錨點前提)
- **Owner**:AI

### F2 — 跑 W54 controlled A/B(live 實證)
- **Acceptance**:`scripts/run_controlled_ab_comparison.py --kb-id w54-live-ab-1 --strategies layout_aware heading_aware --sample <N> --top-k 5` 跑通 → 報告(per strategy recall + chunk 數 + best)捕捉入 progress;frozen eval-set YAML artifact 落 reports/;任何 live-path bug 記低
- **Owner**:AI

### F3 — 結果記錄 + closeout(+ 可選 W53 cross-check)
- **Acceptance**:progress 記 live 結果 + 誠實解讀(controlled but synthetic + lexical proxy;信號強弱)+ 任何 bug/fix;(可選)W53 self-retrievability cross-check;Phase Gate + retro + checklist tick / 🚧;R5 recheck
- **Owner**:AI

## 4. Success Criteria(Phase Gate)

| # | Criterion | Target | Block closeout? |
|---|---|---|---|
| G1 | fresh KB ingest 成功 + sources 存到 + section_path 有值 | total_chunks>0 + -sources blob + section_path | Yes |
| G2 | W54 controlled A/B CLI 跑通 end-to-end(同一 frozen set 跨 2 strategy)| 報告 assemble + 兩 strategy recall 數 | Yes |
| G3 | live-path bug(若有)記低 + 最小修(非 architectural)| 報告完整 | Yes |
| G4 | 結果誠實解讀(controlled but synthetic + lexical proxy;信號強弱明標)| progress review | Yes |

## 5. Risks

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | CLI live-path bug(從未 live 跑;reindex/lifespan/Request shim/score_fn)| Med | Med | 逐步跑;bug 最小修記 changelog;非 architectural |
| R2 | CB doc section 太少 → 兩 strategy chunking 近乎一樣 → recall 無信號 | Med | Low | 明標信號弱 + 建議換大 doc(AR/GL);非 phase fail(pipeline 通 = G2 達)|
| R3 | Free-tier 402 / Azure 成本 / embed timeout(AR 試過 timeout)| Med | Low | 用 mid-size CB(非 10MB AR);semantic off;單 doc bounded |
| R4 | reindex 留 KB 喺中間 strategy 狀態 | Low | Low | fresh KB 非 demo;sequential 接受;closeout 記最終 strategy |

## 6. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-06 | Initial plan | W55 kickoff;Chris explicit「執行 controlled A/B live eval 對真 KB」。Pre-flight 揭現有 KB 全冇 sources → ingest fresh KB(CB manual)路徑;用戶清 Azure index 騰 Free-tier 3-cap | Chris |

---

**Lifecycle reminder**:純 live verification — 預期無新 code;CLI live-path bug 最小修(architectural → STOP per H1)。誠實解讀 controlled-but-synthetic+lexical(承 W54 framing)。

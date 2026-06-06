# W55 — Live Verify chunk-strategy recall harness · Checklist

> Atomic items。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> 純 live verification(預期無新 code);CLI live-path bug 最小修;誠實解讀 controlled-but-synthetic+lexical(承 W54)。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress committed(R1);pre-flight 4 發現(現有 KB 冇 sources / test-kb-v1 得 1 source / 原始 manuals 喺 docs/06-reference / 用戶清 index Free-tier 3-cap)+ 決策(Option 1 CB manual fresh KB)記 progress

## F1 — Ingest fresh KB(CB manual)
- [ ] F1.1 `POST /kb` 建 `w54-live-ab-1`
- [ ] F1.2 multipart upload CB docx(`curl.exe -F`)→ ingest 成功(`GET /kb/{id}` total_chunks>0)
- [ ] F1.3 驗 `-sources` container 有該 doc(reindex 前提)+ chunks 有 section_path(controlled A/B 文字錨點前提)

## F2 — 跑 W54 controlled A/B(live 實證)
- [ ] F2.1 `scripts/run_controlled_ab_comparison.py --kb-id w54-live-ab-1 --strategies layout_aware heading_aware --sample <N> --top-k 5` 跑通
- [ ] F2.2 捕捉報告(per strategy recall + chunk 數 + best)入 progress;frozen eval-set YAML 落 reports/
- [ ] F2.3 任何 live-path bug 記低 + 最小修(非 architectural;architectural → STOP per H1)

## F3 — 結果記錄 + closeout
- [ ] F3.1 progress 記 live 結果 + 誠實解讀(controlled but synthetic + lexical proxy;chunking 信號強弱)
- [ ] F3.2 (可選,若 clean)W53 `run_strategy_recall_comparison.py` self-retrievability cross-check
- [ ] F3.3 Phase Gate G1-G4 + retro + R5 recheck(若有 code 改 → §3/§4 touch?)+ checklist tick / 🚧 + doc-sync(roadmap/session-start live 實證記低,若適用)

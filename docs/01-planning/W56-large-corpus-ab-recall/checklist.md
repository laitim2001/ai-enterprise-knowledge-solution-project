# W56 — Large-corpus controlled A/B recall + W53/W52 CLI 修 · Checklist

> Atomic items。不可刪未勾項(只 `[x]` 或標 🚧 + reason）。
> 大 corpus live verification + 2 個 CLI latent-bug 修;誠實解讀承 W54/W55(controlled-but-synthetic+lexical)+ multi-doc collision caveat。

## F0 — Phase kickoff
- [ ] F0.1 plan/checklist/progress committed(R1);pre-flight 4 發現(Azure 查 1 live index/2 free / drive_user_manuals metadata stale 不可 reuse / fresh KB 必須 / 1 KB=1 index 喺 budget 內)+ 決策(6-doc rebuild / images off)記 progress

## F1 — Ingest fresh KB(6 DRIVE manuals)
- [ ] F1.1 `POST /kb` 建 `w56-drive-ab-1`(index `ekp-kb-w56-drive-ab-1-v1` provisioned;config chunk_strategy=auto / extract_embedded_images=false / slide_screenshots=false)
- [ ] F1.2 sequential multipart upload 6 docs(AR/AP/CB/FA/BM/GL;`curl.exe -F`)→ ingest;記每 doc chunk 數 + 任何 fail(AP timeout = partial 可接受)
- [ ] F1.3 驗 total_chunks >> fetch_k=50(target ≥200)+ `-sources` 有 docs(reindex 前提)+ chunks section_path 有值(controlled A/B 文字錨點前提)

## F2 — 跑 W54 controlled A/B(大 corpus,核心)
- [ ] F2.1 CLI 跑通 exit 0(`--kb-id w56-drive-ab-1 --strategies layout_aware heading_aware --sample 30 --top-k 5`)
- [ ] F2.2 報告捕捉入 progress:per strategy recall@5 + chunk 數 + best;frozen eval-set `reports/controlled-ab-shared-seed0.yaml`
- [ ] F2.3 **核心驗證**:recall 軸辨別 strategy(recall < 1.0 或 strategy delta 出現 = 消 W55 saturation artifact;若仍飽和則明標原因 + 對比 W55)

## F3 — 修 + verify W53/W52 CLI event-loop bug
- [ ] F3.1 W53 `run_strategy_recall_comparison.py` 套 win32 SelectorEventLoop guard(mirror W55 reference;line 143)→ full run 跑通 exit 0
- [ ] F3.2 W53 順帶 close W55 F3.2 deferred self-retrievability cross-check(per strategy recall 記 progress;依家非 saturated)
- [ ] F3.3 W52 `run_synthetic_recall.py` 直接 run(cheap,不 reindex)→ verify event-loop path;若 break 套同款 guard,若 pass 記「不需修」(不盲套 unverified fix)
- [ ] F3.4 任何其他 live-path bug 記低 + 最小修(非 architectural → STOP per H1)

## F4 — 結果記錄 + closeout
- [ ] F4.1 progress 記 W54 A/B + W53 cross-check + W52 verify 結果 + 誠實解讀(controlled-but-synthetic+lexical;multi-doc section_path collision caveat;recall 辨別 vs W55 saturation 對比)+ 所有 bug/fix
- [ ] F4.2 Phase Gate G1-G5 verdict + retro + R5 recheck(只改 script → 非 §3/§4 → 無 ADR;若觸 architectural → ADR)+ checklist tick / 🚧 + doc-sync(roadmap 修訂史 + session-start §10 local-only)

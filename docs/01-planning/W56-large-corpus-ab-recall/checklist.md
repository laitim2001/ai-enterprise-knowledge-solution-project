# W56 — Large-corpus controlled A/B recall + W53/W52 CLI 修 · Checklist

> Atomic items。不可刪未勾項(只 `[x]` 或標 🚧 + reason）。
> 大 corpus live verification + 2 個 CLI latent-bug 修;誠實解讀承 W54/W55(controlled-but-synthetic+lexical)+ multi-doc collision caveat。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress committed(R1);pre-flight 4 發現(Azure 查 1 live index/2 free / drive_user_manuals metadata stale 不可 reuse / fresh KB 必須 / 1 KB=1 index 喺 budget 內)+ 決策(6-doc rebuild / images off)記 progress

## F1 — Ingest fresh KB(6 DRIVE manuals)
- [x] F1.1 `POST /kb` 建 `w56-drive-ab-1`(index `ekp-kb-w56-drive-ab-1-v1` provisioned;config chunk_strategy=auto / extract_embedded_images=false / slide_screenshots=false)
- [x] F1.2 sequential multipart upload 6 docs(AR/AP/CB/FA/BM/GL;`curl.exe -F`)→ ingest;**6 docs 全成功無 AP timeout**;BM16/CB28/GL74/FA78/AP83/AR90 = 369 chunks
- [x] F1.3 驗 total_chunks=369 >> fetch_k=50 + `-sources` 6 blobs(reindex 前提)+ section_path 12/12 non-empty 真階層;R3 multi-doc collision 確認(F4 記)

## F2 — 跑 W54 controlled A/B(大 corpus,核心)
- [x] F2.1 CLI 跑通 exit 0(`--kb-id w56-drive-ab-1 --strategies layout_aware heading_aware --sample 30 --top-k 5`;W55 已修 CLI 直接 reuse 無新 bug)
- [x] F2.2 報告捕捉入 progress:layout_aware 0.9917/369chunks、heading_aware 0.9850/415chunks、best=layout_aware;30 shared QA;frozen `reports/controlled-ab-shared-seed0.yaml`(version controlled-ab-W54-w56-drive-ab-1-seed0)
- [x] F2.3 **核心驗證**:recall 唔再飽和(W55 1.0/1.0 → W56 0.9917/0.9850 兩個 <1.0 + delta = saturation 打破)BUT 辨別力弱(0.67pp gap 喺 noise floor;不宣稱 winner);穩健信號 = chunk-count 分化 369 vs 415 再證 ADR-0044;強辨別需 strict ground truth/更低 top-k → eval-set-v1 carry-over

## F3 — 修 + verify W53/W52 CLI event-loop bug
- [x] F3.1 W53 bug verify-then-fix:先跑 unfixed 確認 crash(psycopg ProactorEventLoop @ lifespan startup)→ 套 win32 SelectorEventLoop guard(mirror W55;ruff clean)→ 重跑 fixed exit 0 + 0 crash = 驗證成功
- [x] F3.2 W53 self-retrievability cross-check(close W55 deferred):layout 0.9667 / heading 0.9333;**三角驗證**:W53 gap 3.3pp > W54 gap 0.67pp = confounding 放大 → 實證 W54 controlled 設計價值
- [x] F3.3 W52 直接 run exit 0 + 0 crash → **不需修**(不用 lifespan/psycopg → 唔中 event-loop bug;Karpathy §1.3 不加多餘 guard);incidental:W52 無 reranker strict 0.7667 vs W53 有 rerank 0.9333 → 再證 synthetic recall 有 noise
- [x] F3.4 其他 live-path bug = 無;3 個 smoke-deferred CLI 至此全部 live-exercised(W55 修 controlled_ab;W56 修 strategy_recall + 確認 synthetic_recall 不需修)

## F4 — 結果記錄 + closeout
- [x] F4.1 progress 記 W54 A/B + W53 cross-check + W52 verify + 誠實解讀(controlled-but-synthetic+lexical;multi-doc collision caveat;recall 辨別 vs W55 saturation;三角驗證;synthetic noise)+ 所有 bug/fix
- [x] F4.2 Phase Gate G1-G5 = **PASS**(G3 帶誠實 caveat)+ retro + R5 recheck(W53 driver guard 非 §3/§4 → 無 ADR)+ checklist tick + doc-sync(roadmap 修訂史 + session-start §10 W56 row local-only);20 eval test passed 0 regression;scratch 已刪

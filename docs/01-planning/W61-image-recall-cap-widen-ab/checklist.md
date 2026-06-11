# W61 — checklist(cap 放寬軸 A/B)

> Atomic checkbox per deliverable。daily tick。對應 plan.md F1–F5。

## F1 — pre-flight + baseline(cap=20)
- [x] pre-flight:azurite 10000 LISTEN / Langfuse `/api/public/health` 200 / Postgres `SELECT 1` / backend `/health` 200
- [x] `GET /kb/drive-images-1` 確認現 config(`max_images_per_answer=20` + DD-4 三旋鈕 `false/10/1`)
- [x] 確保 backend 於 documented env(`SYNTHESIZER_REQUEST_TIMEOUT_S=180` / `HYBRID_USE_SEMANTIC_RANKER=false`);重啟完成(無 multi-session collision,單一 venv dual-process;fresh backend healthy ~60s)
- [x] 跑 A 臂 baseline(cap=20)→ `reports/image_recall_ar_cap20.yaml`
- [x] AC1:9/9 scored + Q001/Q036 無 timeout error + mean 0.574 ≈ 0.572 ✅

## F2 — cap=40 ×2
- [x] `GET /kb/drive-images-1` 取現 config(full KbConfig)
- [x] `PATCH /kb/drive-images-1/settings`(full replacement,只改 `max_images_per_answer=40`)
- [x] `GET readback` 確認 `max_images_per_answer=40` + DD-4 仍 `false/10/1` → GATE PASS
- [x] 跑 run 1 → `reports/image_recall_ar_cap40_r1.yaml`(9/9)
- [x] 跑 run 2 → `reports/image_recall_ar_cap40_r2.yaml`(9/9)

## F3 — cap=60 ×2
- [x] `PATCH /kb/drive-images-1/settings`(full replacement,只改 `max_images_per_answer=60`)
- [x] `GET readback` 確認 `max_images_per_answer=60` + DD-4 仍 `false/10/1` → GATE PASS
- [x] 跑 run 1 → `reports/image_recall_ar_cap60_r1.yaml`(9/9;首跑 bg `bzz5c96ek` 全 502 transient → 重跑 bg `bwldkgnwq` 成功)
- [x] 跑 run 2 → `reports/image_recall_ar_cap60_r2.yaml`(9/9)

## F4 — 復原 cap=20
- [x] `PATCH /kb/drive-images-1/settings`(full replacement,`max_images_per_answer=20`)
- [x] `GET readback` 確認 `max_images_per_answer=20`(+ DD-4 三旋鈕仍 `false/10/1` + neighbour 18 + return_images True)→ RESTORE PASS

## F5 — 分析 + doc-sync
- [x] per-query recall / precision / **returned_count** 跨 20/40/60 三臂對比表(progress.md F5)
- [x] AC3 cap-binding 判決:returned 升向 cap=40 後 plateau 26–33(cap=20 binding,40→60 零增長 → 真天花板 = upstream 供給,部分反證 W59)
- [x] AC4 recall/precision 判決:cap-bound +0.09~+0.17 / precision 不崩 / 對照 3 條完美持平
- [x] 結論落 rollup §4.5(W61 落地 block + §5 優先順序更新)
- [x] progress.md retro + Phase closeout

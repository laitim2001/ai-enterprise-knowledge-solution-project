# W60 Checklist — 圖片召回 config A/B(DD-4 前後)

## F1 — B 臂(post-DD-4 現 default)
- [x] pre-flight:azurite(port 10000)+ index `drive-images-1` populated(B 臂 9/9 出非零數確認 index ok)
- [x] pre-flight:Langfuse `/api/public/health` 200 + Postgres(`/health` 5 component 全 ok)
- [x] 確認 `settings.py` DD-4 三旋鈕環境變數名(無 `env_prefix` + `case_sensitive=False` → field 名大寫)
- [x] 重啟 backend(venv python;`HYBRID_USE_SEMANTIC_RANKER=false` + `SYNTHESIZER_REQUEST_TIMEOUT_S=180`;**無** DD-4 override = post-DD-4 default;ready ~120s)
- [x] 跑 `run_image_recall` → `reports/image_recall_ar_postdd4.yaml`
- [x] B 臂 9/9 scored(mean recall 0.609 / precision 0.977)

## F2 — A 臂(pre-DD-4)
- [x] 重啟 backend(加 `ENABLE_PARENT_DOC_RETRIEVAL=false` + `CITATION_EXPANSION_MAX_AUX=2` + `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=0`;ready ~132s)
- [x] 跑 `run_image_recall` → `reports/image_recall_ar_predd4.yaml`
- [x] A 臂 9/9 scored(mean recall 0.572 / precision 0.982)
- [x] **sanity**:A 臂 0.572 ≈ 0.5715(重現 W59 baseline → DD-4 唯一變數,非 confounding;AC2 PASS)

## F3 — A/B 對比分析
- [x] per-query recall/precision delta 表(9 query)→ progress.md
- [x] mean recall/precision delta(0.572→0.609 = +3.7pp)
- [x] 失敗分類變化(A.cap 0 反應 / B.≤cap 0 反應 / **C.Q005 section miss +0.28 由 DD-4 解**)
- [x] 結論寫 progress.md

## F4 — doc-sync
- [x] rollup §4.5 加 DD-4 對 image-recall 實證結論(W60 A/B 落地段)+ §5 第 3 項 + 提議③ 更新
- [N/A] ~~DEFERRED_REGISTER §4.5 未盡更新~~ → §4.5 未盡(prose)= phase-local 一次性,per 維護規則留 progress.md + rollup,不入 recurring-class 冊
- [x] plan.md status → closed + changelog

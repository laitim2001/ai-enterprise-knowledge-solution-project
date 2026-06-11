# W60 Checklist — 圖片召回 config A/B(DD-4 前後)

## F1 — B 臂(post-DD-4 現 default)
- [ ] pre-flight:azurite(port 10000)+ index `drive-images-1` populated
- [ ] pre-flight:Langfuse `/api/public/health` 200 + Postgres `SELECT 1`
- [ ] 確認 `settings.py` DD-4 三旋鈕環境變數名(查 `model_config` env_prefix)
- [ ] 重啟 backend(venv python;`HYBRID_USE_SEMANTIC_RANKER=false` + `SYNTHESIZER_REQUEST_TIMEOUT_S=180`;**無** DD-4 override = post-DD-4 default)
- [ ] 跑 `run_image_recall` → `reports/image_recall_ar_postdd4.yaml`
- [ ] B 臂 9/9 scored

## F2 — A 臂(pre-DD-4)
- [ ] 重啟 backend(加 `ENABLE_PARENT_DOC_RETRIEVAL=false` + `CITATION_EXPANSION_MAX_AUX=2` + `CITATION_EXPANSION_SECTION_PATH_PREFIX_DEPTH=0`)
- [ ] 跑 `run_image_recall` → `reports/image_recall_ar_predd4.yaml`
- [ ] A 臂 9/9 scored
- [ ] **sanity**:A 臂 mean recall ≈ 0.5715(重現 W59 baseline;偏離大 → STOP 查 confounding per R1)

## F3 — A/B 對比分析
- [ ] per-query recall/precision delta 表(9 query)
- [ ] mean recall/precision delta
- [ ] 失敗分類變化(A.cap 天花板 5 / B.≤cap 3 / C.Q005 section miss 在 DD-4 前後點變)
- [ ] 結論寫 progress.md

## F4 — doc-sync
- [ ] rollup §4.5 加 DD-4 對 image-recall 實證結論
- [ ] DEFERRED_REGISTER §4.5 未盡更新(A/B done,prose 🚧)
- [ ] plan.md status → closed + changelog

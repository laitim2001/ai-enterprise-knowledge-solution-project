# W47 — Reindex Live Verification · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **Verification phase** — 揭 defect → classify per PROCESS.md(Sev → BUG-NNN),唔順手大改。

## F0 — Phase kickoff
- [x] F0.1 plan/checklist/progress 三件套建立 + committed(R1)

## F1 — Dev infra bring-up + pre-flight
- [ ] F1.1 azurite 起(native Plan B `--blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0 --location infrastructure/azurite-data --skipApiVersionCheck`)
- [ ] F1.2 backend 起(`backend\.venv\Scripts\python.exe`)— 只輪詢 `/health`(startup 慢非 hang)
- [ ] F1.3 Azure AI Search reachable + index scheme `ekp-kb-{kb_id}-v1` 確認(Free-tier;`HYBRID_USE_SEMANTIC_RANKER=false` 繞 402)
- [ ] F1.4 pre-flight:Langfuse `/api/public/health` 200 + Postgres `SELECT 1`(Docker unhealthy flag ≠ endpoint down)

## F2 — Seed + source-persist 驗證
- [ ] F2.1 建 test KB(`Bearer dev-token`)+ 上載含圖文件(`curl.exe -F "file=@"` multipart)
- [ ] F2.2 核 `-sources` container 有 blob(name=`doc_id`,metadata `original_filename`)
- [ ] F2.3 記 baseline:chunk 數 + 每 chunk 圖數

## F3 — Reindex core 驗證(真重切)
- [ ] F3.1 改 per-KB config(`chunker_max_images_per_chunk` 8→3 經 `PATCH /kb/{id}/settings`)
- [ ] F3.2 `POST /kb/{id}/reindex` → 核 summary `{documents_total, documents_reindexed, reindexed, skipped_no_source, failed, chunks_total}` 數字
- [ ] F3.3 核 reindex 後 chunks 真按**新** config 重切(cap 3 → force-split:chunk 數↑ / 每 chunk 圖數 ≤3)
- [ ] F3.4 control:無改 config reindex idempotent(chunk 數穩定,無 regression)

## F4 — Edge path 驗證
- [ ] F4.1 pre-W46 / 人手刪 source 嘅 doc → `skipped_no_source` report,no crash
- [ ] F4.2 archived KB → `POST /kb/{id}/reindex` 返 403

## F5 — Frontend live UI click-through(stretch,唔 block closeout)
- [ ] F5.1 `next dev` → Settings → Reindex 卡 → confirm modal → summary banner live(infra 許可;否則 🚧 deferred + reason)

## F6 — Doc-sync + closeout
- [ ] F6.1 R4 status 更新:W46 plan §4 R4 → RESOLVED + roadmap + session-start §10 carry-over verified(+ RISK_REGISTER 若有對應)
- [ ] F6.2 live 發現記 progress.md;defect → BUG-NNN(PROCESS.md)
- [ ] F6.3 Phase Gate G1-G6 評估 + verdict + retro
- [ ] F6.4 checklist 全 tick / 🚧 標記 + session-start W47 closed + W48+ rolling JIT

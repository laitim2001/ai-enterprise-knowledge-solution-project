# W46 — UI Ingestion Config + Real KB-Level Reindex · Checklist

> Atomic items per deliverable。不可刪未勾項(只 `[x]` 或標 🚧 + reason)。
> **F3 frontend GATED on F0 H7 design 確認**(§5.7)。

## F0 — ADR-0043 + H7 design gate
- [x] F0.1 ADR-0043 寫成 Accepted(H1 backend 方向)
- [x] F0.2 ADR README index 加 0043 row + next available → 0044
- [ ] F0.3 H7 mockup design proposal surface 畀 Chris 確認(unlock 範圍 + Reindex UX + warning modal)→ 確認後解鎖 F3

## F1 — Source-document blob 儲存(backend)
- [ ] F1.1 `storage/kb_naming.py` 加 `kb_id_to_source_container(kb_id)` → `ekp-kb-{kb_id}-sources`
- [ ] F1.2 ingest 成功後 best-effort upload 原檔(blob `{doc_id}{ext}`);失敗 log warning 唔 fail
- [ ] F1.3 既有 upload / doc-reindex 行為不變(只多 best-effort step)
- [ ] F1.4 mypy --strict clean

## F2 — Pipeline refactor + 真 KB-level reindex(backend)
- [ ] F2.1 `_run_ingest_pipeline` 抽 core 接受 file path/bytes(UploadFile + stored-blob 共用)
- [ ] F2.2 `POST /kb/{kb_id}/reindex` stub → 真(iterate list_documents → source 攞檔 → delete+re-ingest)
- [ ] F2.3 同步 summary `{reindexed, skipped_no_source, failed, chunks_total}`
- [ ] F2.4 pre-W46 無 source 嘅 doc skip + report(唔 crash)
- [ ] F2.5 mypy --strict clean

## F3 — Frontend:Settings unlock + Reindex UX(GATED on F0.3)
- [ ] F3.1 mockup `ekp-page-kb.jsx` Settings tab 更新:unlock `chunk_strategy` + 圖數 cap + Reindex KB 按鈕 + warning modal
- [ ] F3.2 frontend `kb/[id]/page.tsx` SettingsTab 100% match 更新後 mockup(H7 fidelity)
- [ ] F3.3 wire `POST /kb/{kb_id}/reindex` + reindex summary 顯示
- [ ] F3.4 `embedding_model` 維持 locked
- [ ] F3.5 tsc + lint clean + `[oklch`=0 preserved

## F4 — Tests(H6)
- [ ] F4.1 source-storage test(helper / best-effort persist / 失敗唔 fail)
- [ ] F4.2 KB-reindex test(iterate + re-ingest / skip-no-source / refactored 兩路徑)
- [ ] F4.3 既有 `test_kb_reindex` / `test_documents_*` / `test_orchestrator` / `test_screenshots` 0 regression
- [ ] F4.4 frontend Vitest(SettingsTab unlock + reindex trigger)
- [ ] F4.5 ruff clean

## F5 — Doc-sync
- [ ] F5.1 architecture.md §3.5/§4.4/§4.6 inline ADR-0043 amendment + §5.5 Settings note
- [ ] F5.2 roadmap §3「後續候選」→ ✅ done(+ DESIGN_SYSTEM.md 若加 modal pattern)
- [ ] F5.3 session-start §10 W46 row

## F6 — Closeout
- [ ] F6.1 Phase Gate G1-G6 評估 + verdict
- [ ] F6.2 progress.md retro + carry-overs
- [ ] F6.3 session-start §10 W46 closed + W47+ rolling JIT
- [ ] F6.4 checklist 全 tick / 🚧 標記

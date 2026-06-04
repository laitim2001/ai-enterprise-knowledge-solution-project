# W45 — Per-KB Ingest-Time Chunker Image Cap · Checklist

> Atomic items per deliverable。Daily tick;不可刪未勾項(只 `[x]` 或標 🚧 + reason)。

## F0 — ADR-0042 gate
- [x] F0.1 ADR-0042 寫成 Accepted(`docs/adr/0042-per-kb-ingest-time-chunker-image-cap.md`)
- [x] F0.2 ADR README index 加 0042 row + next available → 0043

## F1 — KbConfig 加 per-KB cap 欄位
- [ ] F1.1 `KbConfig`(`backend/api/schemas/kb.py`)加 `chunker_max_images_per_chunk: int | None = None`
- [ ] F1.2 Docstring 解語意(None=inherit 全域 / 正整數=per-KB cap / per-KB 不能設無 cap)
- [ ] F1.3 確認經既有 `PATCH /kb/{kb_id}/settings` 可設(無新 endpoint)

## F2 — Ingest-time wiring
- [ ] F2.1 `server.py` expose `app.state.make_ingestion_chunker`(callable `int | None -> Chunker`);保留全域 singleton
- [ ] F2.2 `documents.py` `_run_ingest_pipeline` 解析 `cap_override` + None→singleton / 設值→factory
- [ ] F2.3 `_IngestionDeps` thread factory(route 同 concrete class 解耦)
- [ ] F2.4 mypy --strict clean(新 wiring)

## F3 — Tests(H6)
- [ ] F3.1 cap 解析 test:None→singleton / N→per-ingest cap=N force-split
- [ ] F3.2 back-compat test:無 key 嘅 KbConfig → None → inherit(G7)
- [ ] F3.3 factory test:`make_ingestion_chunker(N)` cap=N / `(None)` 無 cap
- [ ] F3.4 既有 `test_chunker` / `test_orchestrator` / `test_documents_*` 0 regression
- [ ] F3.5 ruff clean

## F4 — Doc-sync
- [ ] F4.1 `architecture.md §3.3` inline ADR-0042 amendment(per-KB cap resolution)
- [ ] F4.2 `architecture.md §4.5` inline ADR-0042 amendment(KbConfig 新欄)
- [ ] F4.3 `ROADMAP-per-kb-tunable-config.md` §3 W44 carry-over「per-KB 圖數 cap」標 done + W45 row update

## F5 — Closeout
- [ ] F5.1 Phase Gate G1-G5 評估 + verdict
- [ ] F5.2 progress.md retro + carry-overs
- [ ] F5.3 session-start.md §10 W45 row + W46+ rolling JIT
- [ ] F5.4 checklist 全 tick / 🚧 標記

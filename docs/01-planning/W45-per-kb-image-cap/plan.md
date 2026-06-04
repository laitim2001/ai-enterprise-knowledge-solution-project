---
phase: W45-per-kb-image-cap
name: "Per-KB Ingest-Time Chunker Image Cap"
sprint_week: W45
start_date: 2026-06-04
end_date: 2026-06-05          # planned, may slip with changelog log
status: active
spec_refs:
  - architecture.md §3.3 (layout-aware chunker — per-chunk image cap)
  - architecture.md §4.5 (KbConfig schema)
  - ADR-0042 (per-KB ingest-time chunker image cap)
  - ADR-0040 (per-KB config-scope model — extended to ingest-time here)
  - ADR-0041 (W44 chunker image-density deep fix — 全域 cap, made per-KB here)
prior_phase: W44-chunker-image-density-deep-fix
---

# Phase W45 — Per-KB Ingest-Time Chunker Image Cap

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-04 AskUserQuestion 批准 H1 + ADR-0042 + None 語意「None=繼承,正整數=cap」)

## 1. Scope

把 W44 / ADR-0041 落地嘅全域 chunker 圖數 cap(`Settings.chunker_max_images_per_chunk=8`)**per-KB 化** —— `KbConfig` 加 `chunker_max_images_per_chunk: int | None = None`(`None`=inherit 全域 / 正整數=該 KB cap),令圖密 vs 圖疏 KB 各用度身訂做切分密度,互不干擾。延伸 ADR-0040 per-KB config-scope model(原 query-time only)到 **ingest-time**。

**窄 scope**:backend `KbConfig` 欄 + ingest wiring(chunker factory + `_run_ingest_pipeline` 解析)+ test + doc-sync。新欄位經**既有** `PATCH /kb/{kb_id}/settings` 即可設,**唔加新 endpoint**;**UI 暴露**(ingestion config 自助面)= roadmap W45 較大 candidate,**不在本 phase**。

**Sprint week origin**:roadmap `ROADMAP-per-kb-tunable-config.md` §3 W44 carry-over「per-KB 圖數 cap 降 KbConfig」+ ADR-0042

## 2. Deliverables

### F0 — ADR-0042 gate ✅ DONE
- **Spec ref**:ADR-0042
- **Acceptance criteria**:
  - ✅ ADR-0042 Accepted(Chris 批准 H1 + None 語意)
  - ✅ ADR README index 更新(next available → 0043)
- **Owner**:AI / Chris

### F1 — KbConfig 加 per-KB cap 欄位
- **Spec ref**:`architecture.md §4.5` + ADR-0042 §Decision #1
- **OQ deps**:無
- **Acceptance criteria**:
  - `KbConfig`(`backend/api/schemas/kb.py`)加 `chunker_max_images_per_chunk: int | None = None` + docstring 解語意(None=inherit / +int=cap / per-KB 不能設無 cap)
  - Field 經既有 `PATCH /kb/{kb_id}/settings`(KbConfig-only patch)可設(無新 endpoint)
- **Effort estimate**:0.5h
- **Owner**:AI

### F2 — Ingest-time wiring(chunker factory + 解析)
- **Spec ref**:`architecture.md §3.3` + ADR-0042 §Decision #2-#3
- **Acceptance criteria**:
  - `server.py` expose `app.state.make_ingestion_chunker`(callable `int | None -> Chunker`);全域 singleton `app.state.ingestion_chunker` 保留(inherit 路徑 + 既有 caller)
  - `documents.py` `_run_ingest_pipeline` 解析 `cap_override = kb_config.chunker_max_images_per_chunk`;`None` → 用 `deps.chunker`(singleton,零 construct);設咗值 → factory 砌 per-ingest chunker
  - `documents.py` 保持同 concrete `LayoutAwareChunker` class 解耦(只 call factory)
- **Effort estimate**:1.5h
- **Owner**:AI

### F3 — Tests(H6 — ingestion 路徑)
- **Spec ref**:CLAUDE.md §5.6 H6
- **Acceptance criteria**:
  - cap 解析 test:`cap_override=None` → singleton;`cap_override=N` → per-ingest chunker cap=N(force-split @ N)
  - back-compat test:無 `chunker_max_images_per_chunk` key 嘅 KbConfig reconstruct → `None` → inherit(G7 production-preserve)
  - factory test:`make_ingestion_chunker(N)` 砌出 cap=N 嘅 chunker,`make_ingestion_chunker(None)` = 無 cap
  - 既有 `test_chunker` / `test_orchestrator` / `test_documents_*` 0 regression
- **Effort estimate**:1.5h
- **Owner**:AI

### F4 — Doc-sync
- **Spec ref**:CLAUDE.md §2 routing + R4
- **Acceptance criteria**:
  - `architecture.md §3.3`(chunker)+ §4.5(KbConfig)inline-tagged ADR-0042 amendment(沿用 §3.4/§3.7 inline 先例,doc version held)
  - `ROADMAP-per-kb-tunable-config.md` §3 W44 carry-over「per-KB 圖數 cap」標 done + W45 row update
  - 無 OQ 變動(本 phase 唔涉 OQ)→ decision-form.md 不動
- **Effort estimate**:0.5h
- **Owner**:AI

### F5 — Closeout
- **Spec ref**:PROCESS.md §2 + §10 R2/R5
- **Acceptance criteria**:
  - Phase Gate G1-G5 評估 + verdict
  - progress.md retro + checklist 全 tick / 🚧 標記
  - session-start.md §10 W45 row update + W46+ rolling JIT
- **Effort estimate**:0.5h
- **Owner**:AI

## 3. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block phase closeout? |
|---|---|---|---|---|
| G1 | KbConfig 加 cap 欄 + back-compat | None default → inherit bit-identical | pytest back-compat test | Yes |
| G2 | per-KB cap=N ingest → chunker force-split @ N | cap honoured | pytest cap-resolution test | Yes |
| G3 | inherit(None)ingest → 全域 default 8 | singleton reuse | pytest test | Yes |
| G4 | pytest pass + ruff + mypy clean + 0 regression | all green | `pytest` + `ruff` + `mypy` | Yes |
| G5 | ADR-0042 Accepted + doc-sync | §3.3/§4.5 amended | grep inline tag | Yes |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | None 語意撞車(inherit vs 無cap)| — | Med | 已由 Chris 拍板 None=inherit(ADR-0042);test 斷言兩路徑 |
| R2 | per-ingest chunker construct 成本 | Low | Low | inherit 路徑 reuse singleton(零 construct);tiktoken 全域 cached |
| R3 | documents.py 耦合 concrete chunker class | Low | Low | factory 落 app.state,route 只 call factory |
| R4 | live doc-level reindex verify 需 Azure index + backend(R8/Track A adjacent)| Med | Low | pytest 覆蓋邏輯;live verify nice-to-have,可 🚧 deferred |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables targeted |
|---|---|---|---|
| D1 | 2026-06-04 | F0 ADR gate(done)+ F1 schema + F2 wiring + F3 tests | F0, F1, F2, F3 |
| D2 | 2026-06-05 | F4 doc-sync + F5 closeout | F4, F5 |

## 6. Dependencies on Prior Phase

Carry-over from `W44-chunker-image-density-deep-fix/progress.md` retro:
- per-KB 圖數 cap(降 KbConfig)— **本 phase 直接交付**
- 全域 cap 機制(ADR-0041 `max_images_per_chunk` + 切法 D)已落地 — 本 phase reuse,只加 per-KB resolution
- W20 F4.2 `kb_config` 已 thread 到 ingest(`documents.py:556-582`)— wiring 缺口只剩 chunker per-KB 化

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-04 | Initial plan | W45 kickoff post-W44 closeout;Chris 批准 H1 + ADR-0042 | Chris |

---

**Lifecycle reminder**:呢份 plan locked after status=active。重大 deviation 入第 7 節 changelog,小 detail 變動可直接 inline edit。

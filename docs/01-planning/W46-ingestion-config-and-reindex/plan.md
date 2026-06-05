---
phase: W46-ingestion-config-and-reindex
name: "UI Ingestion Config + Real KB-Level Reindex (Original-File Storage)"
sprint_week: W46
start_date: 2026-06-04
end_date: 2026-06-05          # actual close (D2; F2+F3 both landed early)
status: closed
spec_refs:
  - architecture.md §3.3 (chunker) + §3.5 (ingestion pipeline) + §4.4 (KB reindex endpoint) + §4.6 (blob storage)
  - architecture.md §5.5 (KB Detail Settings tab)
  - ADR-0043 (original-file blob storage + real KB-level reindex)
  - ADR-0042 / ADR-0041 / ADR-0040 (per-KB config — this phase makes ingestion knobs applicable)
prior_phase: W45-per-kb-image-cap
---

# Phase W46 — UI Ingestion Config + Real KB-Level Reindex

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-04 AskUserQuestion 揀「原始檔儲存 + UI 一次過(大 W46)」批准 H1 backend 方向 → ADR-0043;**H7 frontend mockup unlock = 獨立 design sub-gate**,frontend code 前另需確認)

## 1. Scope

完成自助 ingestion-config loop 嘅缺失環節 —— 令 W42/W45 已開嘅 per-KB chunk config(`chunk_strategy` / 圖數 cap)可由 **UI 觸發 reindex apply 落 existing KB**。R6 grep 揭真 blocker = **原始檔冇存**(非 Track A):真 reindex 要 re-parse 原檔,但系統唔存原檔(只存 chunks + screenshots)。

**兩個架構 gate**:
- **H1(backend,已批准 → ADR-0043)**:加 source-document blob 儲存 + 把 KB-level reindex stub 串成真(iterate docs → 由 stored original re-ingest)。
- **H7(frontend,獨立 design sub-gate)**:Settings tab 解鎖 `chunk_strategy` + 圖數 cap + 加「Reindex KB」UX —— mockup 而家 locked,改 mockup 需 design 確認(§5.7),frontend code GATED。

**Out-of-scope**:v1→v2 原子切換(Track A)、`embedding_model` unlock(re-embed 較重,另起)、async reindex task queue、config-test 加 ingestion 軸(W47+)。

**Sprint week origin**:roadmap `ROADMAP-per-kb-tunable-config.md` §3「後續候選」(原 W45 UI ingestion 配置 + 真 reindex)+ ADR-0043

## 2. Deliverables

### F0 — ADR-0043 + H7 design gate
- **Spec ref**:ADR-0043 + §5.7 H7
- **Acceptance criteria**:
  - ✅ ADR-0043 Accepted(H1 backend 方向)+ README index(next → 0044)
  - ✅ H7 mockup design proposal Chris 確認(F0.3:unlock `chunk_strategy` + 圖數 cap + Reindex UX/modal;`embedding_model` 維 locked)→ F3 解鎖
- **Owner**:AI / Chris

### F1 — Source-document blob 儲存(backend)
- **Spec ref**:ADR-0043 §Decision #1-#2 + architecture.md §4.6
- **Acceptance criteria**:
  - NEW `storage/kb_naming.py` helper `kb_id_to_source_container(kb_id)` → `ekp-kb-{kb_id}-sources`
  - ingest 成功後 best-effort upload 原檔落 source container(blob name `{doc_id}{ext}`);失敗 log warning 唔 fail ingest
  - 既有 upload / doc-reindex 路徑行為不變(只多一個 best-effort step)
- **Effort estimate**:3h
- **Owner**:AI

### F2 — `_run_ingest_pipeline` refactor + 真 KB-level reindex(backend)
- **Spec ref**:ADR-0043 §Decision #3-#4 + architecture.md §4.4
- **Acceptance criteria**:
  - `_run_ingest_pipeline` 抽 core 接受 file path/bytes(UploadFile + stored-blob 兩路徑共用)
  - `POST /kb/{kb_id}/reindex` stub → 真:iterate `list_documents` → 由 source container 攞原檔 → delete+re-ingest 同 doc_id → 同步 summary `{reindexed, skipped_no_source, failed, chunks_total}`
  - 冇 stored original 嘅 pre-W46 doc → skip + report(唔 crash)
- **Effort estimate**:4h
- **Owner**:AI

### F3 — Frontend:Settings unlock + Reindex UX(GATED on F0 H7 confirm)
- **Spec ref**:§5.5 + §5.7 H7
- **Acceptance criteria**:
  - mockup(`ekp-page-kb.jsx` Settings tab)更新:unlock `chunk_strategy` + 圖數 cap + 「Reindex KB」按鈕 + warning modal(design-first per ADR-0024 precedent)
  - frontend `kb/[id]/page.tsx` SettingsTab 100% match 更新後 mockup(H7 fidelity)+ wire `POST /kb/{kb_id}/reindex` + reindex summary 顯示
  - `embedding_model` 維持 locked
- **Effort estimate**:5h
- **Owner**:AI(design 確認後)

### F4 — Tests(H6 backend + frontend)
- **Spec ref**:§5.6 H6
- **Acceptance criteria**:
  - source-storage test(helper naming / ingest persist best-effort / 失敗唔 fail ingest)
  - KB-reindex test(iterate + re-ingest / skip-no-source report / refactored pipeline 兩路徑)
  - 既有 `test_kb_reindex` / `test_documents_*` / `test_orchestrator` / `test_screenshots` 0 regression
  - frontend Vitest(SettingsTab unlock + reindex trigger)
- **Effort estimate**:3h
- **Owner**:AI

### F5 — Doc-sync
- **Acceptance criteria**:
  - architecture.md §3.5/§4.4/§4.6 inline ADR-0043 amendment + §5.5 Settings ingestion-config note
  - roadmap §3「後續候選」→ ✅ done + DESIGN_SYSTEM.md(若加 modal/新 pattern)
  - session-start §10 W46 row
- **Effort estimate**:1h
- **Owner**:AI

### F6 — Closeout
- **Acceptance criteria**:Phase Gate G1-G6 + retro + checklist tick / 🚧;session-start W47+ rolling JIT
- **Owner**:AI

## 3. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | source container helper + ingest 持久化原檔 | best-effort persist | pytest | Yes |
| G2 | KB-level reindex 真 iterate + re-ingest;pre-W46 skip+report | real, no crash | pytest | Yes |
| G3 | `_run_ingest_pipeline` refactor 兩路徑共用 + 0 regression | bit-identical existing | pytest | Yes |
| G4 | frontend unlock 100% match 更新後 mockup + reindex wired | H7 fidelity | mockup 對齊 + Vitest | Yes |
| G5 | pytest + ruff + mypy + frontend lint/build clean | all green | CI commands | Yes |
| G6 | ADR-0043 Accepted + H7 design 確認 + doc-sync | done | grep + review | Yes |

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | H7 mockup design 未確認就動 frontend | — | High | F3 GATED on F0 H7 confirm;design-first 改 mockup |
| R2 | in-place reindex 不一致窗口 | Med | Med | 接受(dev 層);v1→v2 原子切換留 Track A |
| R3 | source-upload best-effort 失敗 → doc 不可 reindex | Med | Low | reindex report skip_no_source;doc-level re-upload 可補 |
| R4 | live reindex verify 需 Azure + backend(R8/Track A adjacent)| Med | Low | ✅ **RESOLVED 2026-06-05 via W47**(live end-to-end PASS:source persist + cap 8→3 重切 90→133 + skipped_no_source + archived 403;W46 reindex 零 defect)。frontend UI click-through 🚧 carry W48+(non-blocking)|
| R5 | 大 KB 同步 reindex 慢(blocking)| Low | Low | Tier 1 接受;progress streaming 後補 |

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-04 | F0 ADR-0043 + plan + H7 design proposal + F1 source storage | F0, F1 |
| D2 | 2026-06-05 | F2 pipeline refactor + 真 KB-reindex + F4 backend tests | F2, F4(backend)|
| D3 | 2026-06-06 | F3 frontend(post H7 confirm)+ F4 frontend test + F5 doc-sync + F6 closeout | F3, F4(fe), F5, F6 |

## 6. Dependencies on Prior Phase

Carry-over from `W45-per-kb-image-cap/progress.md` retro(roadmap W46+ candidates):
- UI 開放 ingestion 配置 + 真 KB-level reindex(本期直接交付)
- W45 per-KB 圖數 cap + W43 retrieval config 已開後端;本期解決「apply 落 existing KB」缺口
- R4 live reindex verify(W45 deferred)→ 本期 backend 真 reindex 後可再評

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-04 | Initial plan | W46 kickoff;Chris 揀 Option 4 全 scope + 批准 H1 → ADR-0043;H7 frontend sub-gate | Chris |
| 2026-06-05 | F2.1 deviation:plan 原寫「抽 `_run_ingest_pipeline` core」實際用 BytesIO-UploadFile adapter 復用現成 pipeline(更 surgical,零 working-path regression)| Karpathy §1.3 | AI |
| 2026-06-05 | F5.1 落點 §3.4 而非 plan 標 §3.5(chunk record schema 不變,storage layout 在 §3.4)| accuracy | AI |
| 2026-06-05 | status active → closed;end_date 06-06→06-05(D2 早收,F2+F3 同日 landed)| Phase Gate G1-G6 PASS(R4 live-verify 🚧 deferred) | AI |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**F3 frontend GATED on F0 H7 design 確認**(§5.7 — mockup 係 canonical spec)。

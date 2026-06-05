---
phase: W47-reindex-live-verification
name: "Live End-to-End Verification of W46 KB-Level Reindex (R4 carry-over)"
sprint_week: W47
start_date: 2026-06-05
end_date: 2026-06-07          # planned, may slip with changelog log
status: active
spec_refs:
  - ADR-0043 (original-file blob storage + real KB-level reindex)
  - architecture.md §3.4 (sources container + reindex) + §4.4 #19 (POST /kb/{id}/reindex) + §4.6 (re-sync)
  - architecture.md §5.5.5 (KB Detail Settings unlock + Reindex UX)
  - W46-ingestion-config-and-reindex/plan.md §4 R4 (deferred live-verify carry-over)
prior_phase: W46-ingestion-config-and-reindex
---

# Phase W47 — Live End-to-End Verification of W46 KB-Level Reindex

> **Plan version**:1.0(initial)
> **Owner**:Chris(Tech Lead)
> **Approved by**:Chris(2026-06-05 AskUserQuestion 揀 W47 方向 = R4 live reindex 端到端驗證)

## 1. Scope

收 W46 唯一 carry-over(R4):**實機驗證** W46 啱 ship 嘅 KB-level reindex 真係 end-to-end work —— pytest + vitest 只覆蓋邏輯,本期驗證 **live 整條路徑**(原始檔 persist → download → in-place delete+reingest → 新 config 真重切 + summary 正確)。

**呢個係 verification phase,唔係 feature build**。主軸 = 跑起本機 dev infra(azurite + backend + Azure AI Search index)+ 用真文件行 reindex + 核對結果。

**核心驗證問題**:
1. Ingest 後原始檔有冇真係 persist 落 `ekp-kb-{kb_id}-sources`(metadata `original_filename`)?
2. `POST /kb/{kb_id}/reindex` 真係 iterate 全 doc、由 source download、in-place delete+reingest?summary `{documents_total, documents_reindexed, reindexed, skipped_no_source, failed, chunks_total}` 數字啱唔啱?
3. 改 per-KB config(圖數 cap / chunk_strategy)→ reindex 後 chunks 有冇真係按**新** config 重切(e.g. cap 8→3 → force-split 觀察到 chunk 數 / 每 chunk 圖數變)?
4. Edge:pre-W46 無 source 嘅 doc → `skipped_no_source`;archived KB → 403。

**Out-of-scope**:production v1→v2 原子切換(Track A);async task queue;新 feature。**若 live 驗證揭 defect** → per PROCESS.md classify(Sev → BUG-NNN),唔喺本 verification phase 順手大改(surgical;trivial fix 可,architectural → STOP+ADR)。

**Sprint week origin**:W46 plan §4 R4 deferred carry-over + roadmap W47+ candidate(2026-06-05 Chris pick)

## 2. Deliverables

### F0 — Phase kickoff
- **Acceptance criteria**:plan/checklist/progress 三件套 committed(R1)
- **Owner**:AI

### F1 — Dev infra bring-up + pre-flight
- **Spec ref**:setup.md;runtime memory(azurite native Plan B / backend venv / loaded-machine startup)
- **Acceptance criteria**:
  - azurite 起(native Plan B `--blobHost 0.0.0.0 ... --skipApiVersionCheck`,docker MCR 503 → native per ADR-0017 R8/R9)
  - backend 起(`backend\.venv\Scripts\python.exe`,系統 Python 缺 truststore)— 只輪詢 `/health`(startup 慢非 hang,timeout ≥10s)
  - Azure AI Search reachable + index scheme `ekp-kb-{kb_id}-v1`;UI hybrid 撞 Free-tier 402 → `HYBRID_USE_SEMANTIC_RANKER=false`
  - pre-flight:Langfuse `/api/public/health` 200 + Postgres `SELECT 1`(PC-W33-1/PC-W34-1;Docker unhealthy flag ≠ endpoint down)
- **Owner**:AI

### F2 — Seed + source-persist 驗證
- **Spec ref**:ADR-0043 §Decision #1-#2;`source_store.py`
- **Acceptance criteria**:
  - 建 test KB(mock auth `Bearer dev-token`)+ 上載 1 份含圖文件(multipart `curl.exe -F "file=@"`,PS 5.1 冇 `-Form`)
  - 核 `-sources` container 有 blob(name=`doc_id`,metadata `original_filename`)— azurite blob 列舉 / download 比對
  - 記 baseline:chunk 數 + 每 chunk 圖數
- **Owner**:AI

### F3 — Reindex core 驗證(真重切)
- **Spec ref**:ADR-0043 §Decision #3-#4;`run_kb_reindex`
- **Acceptance criteria**:
  - 改 per-KB config(e.g. `chunker_max_images_per_chunk` 8→3 經 `PATCH /kb/{id}/settings`)
  - `POST /kb/{id}/reindex` → 核 summary `{documents_total, documents_reindexed, reindexed[], skipped_no_source[], failed[], chunks_total}` 數字 vs 實際
  - 核 reindex 後 chunks 真按**新** config 重切(cap 3 → force-split 觀察 chunk 數↑ / 每 chunk 圖數 ≤3)
  - control:無改 config 嘅 reindex 應 idempotent(chunk 數穩定,無 regression)
- **Owner**:AI

### F4 — Edge path 驗證
- **Acceptance criteria**:
  - pre-W46 無 source 嘅 doc(或人手刪 source blob 模擬)→ `skipped_no_source` report,reindex 唔 crash
  - archived KB → `POST /kb/{id}/reindex` 返 403
- **Owner**:AI

### F5 — Frontend live UI click-through(stretch)
- **Spec ref**:§5.5.5;`<ReindexCard>`
- **Acceptance criteria**(若 infra 許可 — vitest 已覆蓋 wiring,本項 bonus):
  - `next dev` 起 → Settings → Reindex 卡「Trigger re-index now」→ confirm modal → summary banner live 顯示
  - 🚧 若 infra 唔配合可 deferred(注明)
- **Owner**:AI

### F6 — Doc-sync + closeout
- **Acceptance criteria**:
  - R4 status 更新:W46 plan §4 R4 → RESOLVED;roadmap + session-start §10 carry-over 標 verified;若有 RISK_REGISTER 對應 entry 同步
  - 任何 live 發現 → progress.md 記;defect → BUG-NNN(PROCESS.md)
  - Phase Gate G1-G6 + retro + checklist tick / 🚧
- **Owner**:AI

## 3. Success Criteria(Phase Gate)

| # | Criterion | Target | Measure | Block closeout? |
|---|---|---|---|---|
| G1 | dev infra up + pre-flight green | azurite + backend /health 200 + Azure Search reachable | health check | Yes |
| G2 | 原始檔 live persist 落 `-sources` | blob exists + metadata original_filename | azurite 列舉 | Yes |
| G3 | reindex 真重切 + summary 正確 | chunks 按新 config 重切;summary 數字啱 | curl + chunk 核對 | Yes |
| G4 | skip(no-source)+ 403(archived)路徑 | no crash + correct report/status | curl | Yes |
| G5 | live 發現全部 triage(無 unhandled defect)| 已 classify | review | Yes |
| G6 | R4 doc-sync RESOLVED + closeout | done | grep + review | Yes |

> **G5(frontend live UI)= stretch,唔 block closeout**(vitest 已覆蓋 wiring;infra 唔配合可 🚧 deferred)。

## 4. Risks(Phase-Specific)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | azurite docker MCR perma-503(ADR-0017 R8/R9)| High | Med | native Plan B(`--skipApiVersionCheck`,memory `project_loaded_machine_startup_infra_recovery`)|
| R2 | loaded machine backend startup 慢(~10min 重度 contention)| Med | Low | 慢非 hang;只輪詢 /health,別提前殺進程(memory `project_backend_venv_dual_process`)|
| R3 | Azure Search Free-tier semantic 1000/月 cap / 402 | Med | Med | `HYBRID_USE_SEMANTIC_RANKER=false` 繞;reindex 唔靠 semantic |
| R4 | live 驗證揭 W46 reindex defect | Med | Med | 正係本期目的;classify → BUG-NNN;trivial inline / architectural STOP+ADR |
| R5 | backend venv 雙進程坑(誤殺 child)| Low | Med | `sys.prefix` 判 venv,以 port 8000 LISTEN PID 為準(memory `project_backend_venv_dual_process`)|

## 5. Day-by-Day Breakdown(rough)

| Day | Date | Focus | Deliverables |
|---|---|---|---|
| D1 | 2026-06-05 | F0 kickoff + F1 infra bring-up | F0, F1 |
| D2 | 2026-06-06 | F2 source-persist + F3 reindex core 驗證 | F2, F3 |
| D3 | 2026-06-07 | F4 edge + F5 frontend stretch + F6 doc-sync/closeout | F4, F5, F6 |

## 6. Dependencies on Prior Phase

Carry-over from `W46-ingestion-config-and-reindex/plan.md §4 R4`(live reindex verify deferred):
- W46 backend(`source_store` + `run_kb_reindex`)+ frontend(`<ReindexCard>`)已 ship + pytest/vitest green;本期 = live end-to-end 證。
- 測試 KB 慣例:index `ekp-kb-{kb_id}-v1`;mock auth `Bearer dev-token`;backend 必 `backend\.venv\Scripts\python.exe`;azurite native `--skipApiVersionCheck`(memory).

## 7. Plan Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-05 | Initial plan | W47 kickoff;Chris 揀 R4 live reindex 端到端驗證 | Chris |

---

**Lifecycle reminder**:plan locked after status=active。重大 deviation 入第 7 節 changelog。**Verification phase** — 若揭 defect,per PROCESS.md classify(Sev → BUG-NNN),唔喺本期順手大改(Karpathy §1.3 surgical)。

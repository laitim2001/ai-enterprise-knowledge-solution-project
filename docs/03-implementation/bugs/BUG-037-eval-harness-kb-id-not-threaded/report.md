---
bug_id: BUG-037
title: "Eval harness 無法針對非預設 KB — CLI run_ragas_eval 缺 required kb_id 而 crash + /eval API hardcode kb_id"
severity: Sev3          # Sev1 | Sev2 | Sev3 | Sev4 (per PROCESS.md §4.5)
status: triaged   # triaged | investigating | fixing | verifying | done | wont-fix
reported: 2026-06-09
reporter: "Claude (AI) — 起於 CH-011 AC6 eval 無法執行 (task_ecd4f8bd)"
affects_components: [C06]
spec_refs:
  - architecture.md §4.4   # eval endpoints #15-16
  - ADR-0018               # multi-KB invariant (kb_id required on retrieve/search)
---

# BUG-037 — Eval harness kb_id 無 thread 通（CLI crash + API hardcode）

> **Report version**:1.0(initial)
> **緣起**:用戶 2026-06-09 揀「先修 eval harness」（task_ecd4f8bd）作為 per-doc config 平台 enabler。CH-011 AC6（drive-images-1 圖片順序 eval）一直 deferred 因 harness 無法針對該 KB 跑。

## 1. Symptom

Eval harness 只能對 `drive_user_manuals`（Tier 1 baseline）跑,**無法針對任何其他 KB**（如 `drive-images-1` for CH-011 AC6,或未來 per-doc config 試跑 KB）：

- **CLI `scripts/run_ragas_eval.py`**:一 run 即 crash。Line 136 `engine.retrieve(query=sample.question, top_k=5)` **缺 `kb_id`**,而 `RetrievalEngine.retrieve(self, query, kb_id, top_k, ...)`（`retrieval_engine.py` L121-124）嘅 `kb_id` 係 **required positional**（ADR-0018 multi-KB invariant）→ `TypeError: retrieve() missing 1 required positional argument: 'kb_id'`。
- **API `/eval/run` + `/eval/shootout`**（`backend/api/routes/eval.py` L135 / L205）:`kb_id="drive_user_manuals"` **hardcoded**,`EvalRunRequest` / `EvalShootoutRequest` 無 `kb_id` field → 無法 override。

## 2. Reproduction Steps

**CLI（hard crash）**:
1. `backend/.venv/Scripts/python.exe -m scripts.run_ragas_eval --eval-set docs/eval-set-v0.yaml --subset 2`
2. **觀察**:pipeline 行到 `engine.retrieve(...)` 即 `TypeError`(missing `kb_id`)→ 頂層 driver swallow → `FAIL: TypeError: ...` exit 1。

**API（無 crash,但鎖 KB）**:
1. `POST /eval/run {"eval_set_id": "eval-set-v0"}` → 永遠對 `drive_user_manuals` 跑,無 `kb_id` 參數可傳。

**Reproduction reliability**:Always（CLI 簽名 mismatch 確定性;API hardcode 確定性）。

**Environment**:local dev（backend venv :8000;CLI 需 Azure OpenAI + AI Search live key）。

## 3. Expected vs Actual

- **Expected**:eval harness（CLI + API）可指定 `kb_id`,對任意 KB 跑 Recall@5 + RAGAs;預設保持 `drive_user_manuals`(production-preserve)。
- **Actual**:CLI crash;API 鎖死 `drive_user_manuals`。

## 4. Impact

- **Affected**:任何「對非預設 KB 做 eval」嘅工作流 —— CH-011 AC6（圖片順序/完整性 regression eval）+ 未來 per-doc config 平台（Gap A / P2）config-test eval。
- **Workaround**:無（CLI 直接 crash;API 無 override seam）。
- **User / prod impact**:無（純 dev / eval 工具,未到 Beta/Prod）。
- **Data loss / security**:No。

## 5. Severity Justification

**Sev3**:dev / eval 工具 broken,阻塞 eval 驗證工作流（CH-011 AC6 + per-doc config 量化驗證),但**無 user-facing / data / prod 影響**,亦非核心 chat surface。非 Sev2(無品質 regression 落到用戶眼前)。Sev3 → **無 mandatory postmortem**(per PROCESS.md §4.5;只 Sev1/Sev2 強制)。

## 6. Initial Diagnosis

- **CLI 根因**:`run_ragas_eval.py` 寫於 W4(ADR-0018 multi-KB invariant 之前),當時 `retrieve()` 無需 kb_id。ADR-0018(W16)令 `retrieve(query, kb_id, top_k)` 嘅 `kb_id` 變 required positional,但 CLI 從未更新 → 簽名 mismatch crash。HybridSearcher 構造用 `settings.azure_search_default_index`(legacy default),但 `search(kb_id)` 會 `kb_id_to_index_name(kb_id, legacy_default_index=self.index_name)` 動態 resolve per-KB index(`hybrid.py` L352)→ **只需把 kb_id 傳通,index 自動正確**。
- **API 根因**:`/eval/run`(L135)+ `/eval/shootout`(L205)hardcode `kb_id="drive_user_manuals"`(Tier 1 single-KB Q7 baseline 當時刻意簡化);`EvalRunRequest` / `EvalShootoutRequest` 無 `kb_id` field。
- **非 H1**:只 thread 一個 ADR-0018 已確立嘅參數 + 加 request field,無 architecture / vendor / storage / component-existence 改動 → 無 ADR(per CLAUDE.md §5.1 H1 例外:internal fix + 既有 interface 補回)。

## 7. Acceptance for Fix（checklist preview）

- [ ] CLI:`--kb-id`(default `drive_user_manuals`)+ `engine.retrieve(query=..., kb_id=..., top_k=5)` → crash 消失,可對 `drive-images-1` 跑
- [ ] API:`EvalRunRequest` / `EvalShootoutRequest` 加 `kb_id: str = "drive_user_manuals"`;route 用 `payload.kb_id` 取代 hardcode
- [ ] Production-preserve:default 仍 `drive_user_manuals`(bit-identical 舊行為)
- [ ] Test:API kb_id 透傳 + CLI kb_id 傳入 retrieve(H6 eval 覆蓋)
- [ ] Verify:CLI `--kb-id drive-images-1 --subset 2` 唔 crash(到 retrieve;Azure key 缺時 graceful exit 而非 TypeError)+ pytest 綠

## 8. Report Changelog

| Date | Change | Reason | Approver |
|---|---|---|---|
| 2026-06-09 | Initial triage(Sev3)+ 診斷 | 用戶揀修 eval harness(enabler);CH-011 AC6 阻塞 | Chris |

---

**Lifecycle reminder**:Sev3 → 無 mandatory postmortem(per PROCESS.md §4.5)。

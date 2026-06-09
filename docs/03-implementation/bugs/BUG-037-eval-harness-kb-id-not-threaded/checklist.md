---
bug_id: BUG-037
report_ref: ./report.md
status: done     # investigating | fixing | verifying | done
last_updated: 2026-06-09
---

# BUG-037 — Checklist

> 逐項 atomic;done → `→[x]`,未做標 🚧 + 理由。Sev3 → 無 mandatory postmortem。

## Investigation
- [x] I1 — CLI crash 根因:`run_ragas_eval.py` L136 `engine.retrieve(query=, top_k=)` 缺 required `kb_id`(ADR-0018)→ TypeError
- [x] I2 — API hardcode:`/eval/run` L135 + `/eval/shootout` L205 `kb_id="drive_user_manuals"`;request schema 無 `kb_id`
- [x] I3 — HybridSearcher `search(kb_id)` 動態 resolve index(`kb_id_to_index_name`,`hybrid.py` L352)→ 只需 thread kb_id,index 自動正確,**無需改 searcher 構造**
- [x] I4 — 非 H1(thread 既有 ADR-0018 參數 + 加 request field;無 architecture/vendor/storage 改)→ 無 ADR

## Fix
- [x] F1 — API:`EvalRunRequest` + `EvalShootoutRequest` 加 `kb_id: str = "drive_user_manuals"`(`backend/api/routes/eval.py`)
- [x] F2 — API route:`run_eval` + `run_shootout` 用 `payload.kb_id` 取代 hardcode `"drive_user_manuals"`
- [x] F3 — CLI:`scripts/run_ragas_eval.py` 加 `--kb-id`(default `drive_user_manuals`)+ `_build_samples_via_pipeline` thread kb_id 落 `engine.retrieve(query=..., kb_id=kb_id, top_k=5)`
- [x] F4 — Test:`test_eval_endpoints.py` 加 kb_id 透傳 assert;CLI retrieve kb_id 傳入 assert(H6 eval 覆蓋)

## Verify
- [x] V1 — pytest 14 passed(`test_eval_kb_id_bug037` 6 + `test_eval_endpoints` 8);**backend ruff check + format clean**(eval.py + test）。**Tooling notes**:① `scripts/run_ragas_eval.py` 有 pre-existing E402(truststore-before-import）+ F401(`json` unused）+ 手寫 compact arg 風格 → scripts/ 唔喺 backend ruff gate(backend/pyproject.toml 只覆蓋 backend/）,我加嘅 `--kb-id` block 跟足現有風格,按 Karpathy §1.3 surgical 不 mass-reformat pre-existing 檔。② mypy --strict(`--explicit-package-bases`,因 `backend/__init__.py` 令 per-file dual-base）= **31 pre-existing error 跨 10 檔(eval 模組一直非 --strict-clean）;零個喺我改嘅行** —— `api/routes/eval.py` 嘅 3 個(L74 `_engine_or_503` Any-return / L144+218 `ragas_evaluator` object-vs-Callable）全屬未掂過嘅既有碼;我加嘅 `kb_id: str` field + `kb_id=payload.kb_id` 全 str-typed clean
- [x] V2 — CLI 唔再 TypeError(unit test `test_cli_build_samples_threads_kb_id_into_retrieve` 直接 assert retrieve 收到 kb_id;比 live run 更可靠 — live 無 Azure key 會喺 key check graceful exit 觸唔到 retrieve)
- [ ] 🚧 V3 — `/eval/run {"kb_id":"drive-images-1"}` live backend 透傳:**deferred** — 需 Azure key + Free-tier semantic 繞過;unit test 已覆蓋透傳邏輯,留待真跑 CH-011 AC6 eval 時順驗(target phase = Gap C C-2 / CH-011 AC6）

## Closeout
- [x] C1 — report status → done;commit `5a2c3ae`(branch `fix/eval-harness-kb-id`)+ ff-merge → main
- [x] C2 — unblock 記錄:CH-011 AC6 eval(`--kb-id drive-images-1` / `{"kb_id":"drive-images-1"}`)+ 未來 per-doc config-test eval 解鎖(task_ecd4f8bd 可關)

---
change_id: CH-006
spec_ref: ./spec.md
checklist_ref: ./checklist.md
status: closed          # in-progress | closed
---

# CH-006 — Progress

> Day-N entries + closeout。每 commit 對應 Day-N mention(R2)。

---

## Day 1 — 2026-06-06

### Context
W56 後續 live 診斷(KB `w56-drive-ab-1`):procedural 問題(GL03 post journal)recall 已完整(parent_doc → 14/14 chunks),但 chat 答案仍係 6 步摘要。Scratch 證實根因 = synthesis prompt Rule 3「target <= 150 words」cap;放寬 → gpt-5.5 即吐完整逐 sub-step。用戶揀 per-KB「答案詳細度」config 路線。spec draft→approved(Chris chat「Approve」)。

### Done
- (kickoff)spec.md status draft → **approved**(Chris)+ checklist + progress committed(R1.change 滿足)。
- **Backend I1-I6 + T1-T3 完成**:Settings 全域預設 + KbConfig.answer_detail + EffectiveConfig resolve + prompt_builder concise/detailed 雙變體(`.replace()` 派生)+ synthesizer detail_level + query.py 兩路 + CRAG re-synth wiring。**14 個 CH-006 test 全綠**;52 個相關 test 通過。
- **Frontend I7-I8 + T4 完成**:kb.ts KbConfig type 加 `answer_detail`;SettingsTab「Retrieval config」card 加 `.seg` 控件(沿用 chunk_strategy 視覺 → H7 一致)+ state/dirty/buildConfigBody wired。vitest 6/6(+2 CH-006)+ 相關 4 檔 7 test 0 regression;tsc exit 0;eslint clean。
- (pending V1-V3 verification + closeout)

### Decisions
- 預設 `concise` = 現行 prompt 逐字不變 → **零 regression**;`detailed` opt-in per-KB。
- **prompt_builder 重構策略**:rename 變數(body 不郁)+ `.replace()` 派生 detailed(只換 Rule 3)→ 零 rule 重複、零 drift、concise 保證 byte-identical(Karpathy §1.3 最 surgical)。
- 保留 `SYSTEM_PROMPT` 別名 = concise → 唔破現有 import/test(CH-005 substring 斷言全過)。
- I2 scope 收窄:config_test DraftRetrievalConfig **不加** answer_detail（synthesis knob 非 retrieval;config-test panel 仍用 KB saved/global = concise）。
- CRAG re-synth 一併 thread detail_level(一致性)。
- `default_rerank_k` → chat wiring gap **明確另案**(唔混入本 CH)。

### Notes (pre-existing, 非 CH-006)
- `test_synthesizer.py::test_synthesize_invokes_engine_fetch_expansion...` 喺 **clean checkout(git stash 驗)一樣 fail** → pre-existing citation-expansion 失敗,**唔關 CH-006**;按 Karpathy §1.3 唔喺本 CH 修(另案)。
- `effective_config.py` 喺 HEAD 已 format-dirty(`max_images_per_answer` block)→ pre-existing debt,唔郁(我加嘅 block 已 format-clean)。
- mypy:我改 3 檔零 error;6 個 error 喺其他模組(langfuse/observe/retrieval_engine)= pre-existing baseline。

### Blockers
- 無。

### Effort
- Planned:~0.5–1 day;Actual:_(填)_;Variance:_

### Commits
| Hash | Subject |
|---|---|
| _(待)_ | docs(change): CH-006 kickoff |

---

## Closeout — 2026-06-07

### Acceptance verification(spec.md §3)
- ✅ `KbConfig.answer_detail` round-trip(POST/GET/PATCH;預設 None)
- ✅ `None`/`concise` → 現行 150-字 prompt(byte-identical rename;現有 substring test 全過)
- ✅ `detailed` → 放寬 prompt;**live GL03 3531 字逐 sub-step**(含 Excel 上載分支)
- ✅ EffectiveConfig resolve 次序 per-query > per-KB > global
- ✅ `/query` + `/query/stream` 兩路 + CRAG re-synth 採用 effective `answer_detail`
- ✅ SettingsTab `.seg` 控件 → PATCH 持久化;沿用 chunk_strategy 視覺(H7 一致延伸)
- ✅ pytest 80 passed(14 CH-006 + 相關)；frontend vitest 6/6 + tsc + lint
- ✅ live 對照:detailed 3531 字 vs concise 722 字(non-regression)

### Effort
- Planned ~0.5–1 day;Actual ~半日(single session)。

### Lessons
- **做得好**:診斷分層清晰(retrieval recall vs synthesis verbosity 兩個獨立根因,逐一 live 證);prompt 重構用 rename + `.replace()` 派生 → concise 保證 byte-identical、零 drift(Karpathy §1.3 最 surgical);CRAG re-synth 一併 thread 確保一致;走足正式 Change 流程(spec approve → impl → test → live verify → closeout)。
- **意外/摩擦**:(1) backend 無 `--reload` → live 驗證需 restart(killed dual-process tree 26792+44216);(2) restart 首次從 repo root launch 撞 `ModuleNotFoundError: ingestion` → 須 cwd=backend;(3) bash `/tmp` vs Windows-python `/tmp` 路徑不一致 → 改用單一 urllib script;(4) 撞到 pre-existing `test_synthesize_invokes_engine_fetch_expansion` 失敗,git-stash 證實非本 CH。
- **carry-over**:`default_rerank_k` → chat wiring gap(chat 寫死唔送 top_k,KB 設定無效)—— 獨立 CH/Bug 待開。

### Component design note status updates
- C05 Generation:v1-active(amendment + last_updated 2026-06-07;synthesis answer-detail prompt 變體)
- C02 KB Manager:v2-stable(amendment + last_updated 2026-06-07;`answer_detail` config 欄位)

### Commits
| Hash | Subject |
|---|---|
| `c460cd9` | CH-006 kickoff(spec approved + checklist + progress) |
| `6172173` | backend — per-KB answer detail(C05+C02)|
| `038a6a1` | frontend — answer detail seg control(C02)|
| _(closeout)_ | closeout(progress/checklist/spec done + C05/C02 notes + ROADMAP)|

### Final KB state
- `w56-drive-ab-1` 留喺 **detailed**(用戶對程序手冊嘅 intent;chat 即時可見完整逐步)。可隨時喺 Settings tab `.seg` 切回 concise。

---

## Retro addendum — 2026-06-07(CH-007 期間發現,post-closeout)

> 由 [[../CH-007-per-kb-top-k-rerank-wiring/spec.md|CH-007]] 跑 query-pipeline 完整 test suite 時揭發:**CH-006 landing 其實唔完整**,有兩層 latent bug 互相遮蔽,本 CH 嘅 V1「80 passed」從未覆蓋到。已於 CH-007 內恢復(commit `6ab7adc`),此處補 retro 記錄根因 + 教訓。

### 漏網兩層(互相遮蔽)
1. **4 個 route-test mock 漏改 `detail_level`**:CH-006 令 `query.py` route 無條件傳 `synthesize(..., detail_level=effective.answer_detail)`,但只更新咗部分 test mock。`test_query_per_kb_config.py` / `test_config_test_route.py` / `test_observe_query_route.py` / `test_e1_e5_e12_smoke.py` 4 個 `_MockSynth.synthesize` 簽名冇收 `detail_level` → 打 route 時 `TypeError` → 502。
2. **`ConfigTestResult.resolved_config` type 容唔落 `answer_detail: str`**:CH-006 為 `EffectiveConfig` 加 `answer_detail: str`,但 `config_test.py` 的 `resolved_config: dict[str, int | bool | None]` 冇放寬 → `asdict(effective)` 帶 str 入去 → `ValidationError`。

### 點解 CH-006 V1 走漏
- 第 1 層 502(`synthesize` TypeError)發生喺 `return ConfigTestResult(...)` **之前**,遮蔽咗第 2 層。
- CH-006 V1 實際只跑 `prompt_builder` / `synthesizer` / `effective_config` / `crag` 等**唔打 route mock** 的檔(該批答案 80 passed 真實),從未跑呢 4 個 route-test 檔 → 兩個 bug 都漏網。

### 教訓
- 改 pipeline 入口簽名(新增**無預設**或**無條件傳遞**的 kwarg)時,要 grep 晒**所有** route-test mock 同步;單靠跑「相關」子集 test 會走漏 route-level 檔。
- Pydantic response model 的 union type(如 `resolved_config`)隨上游 dataclass 加欄位要同步放寬,否則 `asdict` 序列化會喺 runtime 先爆。
- **驗收 gate 應跑覆蓋該 route 的完整 test 檔集**,唔好只跑 feature-local 檔。

### CH-007 恢復內容(commit `6ab7adc`)
- 4 檔 mock `synthesize` 加 `detail_level: str = "concise"`(對齊 ship 的真簽名)。
- `ConfigTestResult.resolved_config` type 放寬至 `dict[str, int | bool | str | None]`。
- 恢復後全 suite **113 passed / 0 fail**。CH-006 行為本身正確,純屬 test-coverage + schema-type 漏網。

---

**End of CH-006 progress**

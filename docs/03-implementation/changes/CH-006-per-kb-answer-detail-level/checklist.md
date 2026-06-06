---
change_id: CH-006
spec_ref: ./spec.md
status: in-progress     # in-progress | done
last_updated: 2026-06-06
---

# CH-006 — Checklist

> Atomic items derived from `spec.md` §3 acceptance criteria。AI tick 完成 item;唔可以 tick 嘅喺 progress Day-N 寫原因。

## Implementation — Backend (C02 config + C05 prompt)

- [ ] I1 `Settings.synthesis_answer_detail: str = "concise"` 全域預設(storage/settings.py)
- [ ] I2 `KbConfig.answer_detail: Literal["concise","detailed"] | None = None`(schemas/kb.py)+ config_test DraftRetrievalConfig 對應欄位(若 harness 需要)
- [ ] I3 EffectiveConfig 加 `answer_detail` + `_resolve_effective_config` resolve 次序(KB > 全域 > "concise")
- [ ] I4 `prompt_builder.py`:`SYSTEM_PROMPT` 改名/保留為 concise variant(逐字不變)+ NEW `SYSTEM_PROMPT_DETAILED`(放寬 Rule 3:無字數上限 + 逐 sub-step + nested 編號 + 唔壓縮;Rule 1/2/4-8 不變)+ `build_prompt(..., detail_level="concise")` 揀 prompt;保留 `SYSTEM_PROMPT` 別名 backward-compat
- [ ] I5 `synthesizer.synthesize` + stream 變體加 `detail_level` 參數 → 傳落 `build_prompt`
- [ ] I6 `query.py` execute_query_pipeline 把 `effective.answer_detail` 傳落 synthesizer(`/query` + `/query/stream` 兩路)

## Implementation — Frontend (C02 SettingsTab)

- [ ] I7 `kb/[id]/page.tsx` SettingsTab advanced-tuning panel 加 `answer_detail` 控件(concise/detailed,沿用既有 OptionRow/select 視覺;H7 — 對齊 panel 視覺語言,撞 mockup gap 則 STOP)
- [ ] I8 `lib/api/kb.ts` KbConfig type + default 加 `answer_detail`;save→PATCH 帶上

## Tests (H6 — generation + config)

- [ ] T1 `test_prompt_builder`:concise variant 含「150」cap 字眼;detailed variant 不含 + 含「do not summarize」類指令;`build_prompt(detail_level=...)` 揀啱
- [ ] T2 KbConfig `answer_detail` round-trip + EffectiveConfig resolve 次序(KB>global>default)
- [ ] T3 synthesizer 傳遞 detail_level 落 build_prompt(unit / mock)
- [ ] T4 frontend vitest:控件 render + 預設值 + onChange→PATCH payload

## Verification

- [ ] V1 Run spec.md §3 acceptance:`backend/.venv/Scripts/python.exe -m pytest backend/tests/test_prompt_builder.py backend/tests/test_synthesizer*.py backend/tests/test_kb*.py -q`(+ 相關)全綠 0 regression
- [ ] V2 ruff + ruff format + mypy(改檔零新 error)+ frontend tsc + lint + vitest
- [ ] V3 Live 驗:`w56-drive-ab-1` 設 detailed → chat 問 GL03 → 逐 sub-step;設返 concise → 6 步摘要(對照);non-regression 確認預設 concise 不變

## Cross-Cutting

- [ ] X1 Each commit references progress Day-N(R2)+ component tag(C05/C02)
- [ ] X2 非 architectural → 無 ADR(R5 recheck;確認無 §3/§4 component 增刪/vendor swap)
- [ ] X3 components/C05-*.md + C02-*.md design note bump(若存在;per CC-5)
- [ ] X4 progress closeout summary + frontmatter status → closed
- [ ] X5 doc-sync:ROADMAP 修訂史 + session-start §10(local-only)

---

**Lifecycle reminder**:新加 item 必須先入 spec §2/§3 + changelog,再加 checklist。

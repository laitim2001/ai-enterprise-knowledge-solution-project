---
change_id: CH-006
spec_ref: ./spec.md
status: in-progress     # in-progress | done
last_updated: 2026-06-06
---

# CH-006 — Checklist

> Atomic items derived from `spec.md` §3 acceptance criteria。AI tick 完成 item;唔可以 tick 嘅喺 progress Day-N 寫原因。

## Implementation — Backend (C02 config + C05 prompt)

- [x] I1 `Settings.synthesis_answer_detail: str = "concise"` 全域預設(storage/settings.py)
- [x] I2 `KbConfig.answer_detail: Literal["concise","detailed"] | None = None`(schemas/kb.py);config_test DraftRetrievalConfig **不加**(synthesis knob,非 retrieval;config-test 用 KB saved/default = concise,scope 收窄記 progress)
- [x] I3 EffectiveConfig 加 `answer_detail: str` + PerQueryOverrides + resolve(KB > 全域 > "concise";str `or` chain 因 `_resolve` int-bound)
- [x] I4 `prompt_builder.py`:rename → `SYSTEM_PROMPT_CONCISE`(body 逐字不變)+ `SYSTEM_PROMPT = SYSTEM_PROMPT_CONCISE` 別名 + `SYSTEM_PROMPT_DETAILED = CONCISE.replace(_RULE_3_CONCISE, _RULE_3_DETAILED)`(只換 Rule 3,零 rule 重複/drift)+ `_system_prompt_for(detail_level)` + `build_prompt(..., detail_level="concise")`
- [x] I5 `synthesizer.synthesize` + `synthesize_stream` 加 `detail_level: str = "concise"` → 傳落 `build_prompt`
- [x] I6 `query.py` execute_query_pipeline 兩路(`/query` line 261 + `/query/stream` line 457)+ CRAG `refine` re-synth(crag.py 424)都傳 `effective.answer_detail`

## Implementation — Frontend (C02 SettingsTab)

- [x] I7 `kb/[id]/page.tsx` SettingsTab「Retrieval config」card 加 `answer_detail` `.seg` 控件(concise/detailed,**沿用 chunk_strategy 既有 `.seg` + 綠色 Edit icon 視覺** → H7 一致延伸,非新 mockup 元素;state + configDirty + buildConfigBody wired)
- [x] I8 `lib/api/kb.ts` KbConfig type 加 `answer_detail?: 'concise'|'detailed'|null`(沿用 W43 optional 模式,DEFAULT 不加 = inherit)

## Tests (H6 — generation + config)

- [x] T1 `test_answer_detail_ch006`:concise 含「150」;detailed 不含 + 含「do not summarize」+「no word limit」+ 只 Rule 3 變(其餘 rule 保留)+ alias=concise + `build_prompt(detail_level)` 揀啱
- [x] T2 KbConfig `answer_detail` round-trip + 拒 bad value + EffectiveConfig resolve 次序(per-query>KB>global>default)
- [x] T3 synthesizer `detail_level="detailed"` → captured system message == SYSTEM_PROMPT_DETAILED(mock client）
- [x] T4 frontend vitest(kb-settings-tuning +2):seg 兩 option render + 切 detailed→save→`patchSettings` payload `answer_detail:'detailed'`;6/6 pass + 相關 4 檔 7 test 0 regression

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

---
phase: W58
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: active     # active | closed
---

# W58 — Progress

> Day-N entries + closeout retro。

---

## Day 1 — 2026-06-09

### Done
- W57 / P2a(per-doc 配置後端)merged 落 main(`0bed3b7`)後,用戶揀 kickoff P2b(per-doc 配置 UI)。
- **H7 決策(AskUserQuestion)**:doc-detail mockup 無 config 面 → 用戶揀**路徑 A —— 先擴 mockup**(最守 H7)。
- Ground 現況:doc-detail 頁(913 行)= 3-pane chunk inspector 無 config 面;`KbTuneGroup`/`KbTuneKnob`/
  `ConfigTestPanel` inline 喺 `kb/[id]/page.tsx`(未抽出);無 per-doc config API client。
- 讀 KB SettingsTab mockup pattern(`ekp-page-kb.jsx` L744-1177):`TabKbSettings` + `KbTuneGroup`×3 +
  config-test panel + `KbTuneKnob`/`KbTuneGroup`/`KbTestResultCard`/`KbTestMetric` helper → mirror source。

### Decisions
- Phase W58 = P2b UI;**F2-F4 gated on F1 mockup user-review**(守 H7,唔 approximate)。
- doc-detail 加 tab strip(Chunk inspector + Per-doc 配置)= design-stage expansion → ADR-0051。
- 只暴露 post-retrieval 旋鈕(per ADR-0050);繼承語意 = 繼承 KB(非全域)。

### F1 mockup review + F2-F4 build(Day 1 cont)
- **F1.5 H7 gate PASS**:用戶 2026-06-09 approve mockup → ADR-0051 Accepted → F2-F4 解鎖。
- **F2**:`lib/api/doc-config.ts`(get/put/delete/list,`DocConfig` 鏡 backend)+ `ApiClient.put`(additive)+ `config-test.ts` 加 `enable_chapter_overview_pin` + `doc_id`。
- **F3**:self-contained `doc-config-tab.tsx`(deviation from R2:唔抽 KB 頁元件,§1.3;建 `DocTuneKnob`/`DocTuneGroup`/`DocSwitchKnob`/`DocConfigResultCard` mirror KB pattern + 「繼承 KB」framing)+ doc-detail `page.tsx` 加 tab strip(inspector wrap 視覺不變 + config tab)。
- **F4**:`doc-config-tab.test.tsx` **4 passed**;KB regression(kb-detail-tabs/kb-settings-reindex/kb-detail)**全綠**;tsc/eslint/prettier clean。
- **H7 fidelity 偏差 + 解決**:config-test 用 `draft_config` 預覽(非 mockup 暗示 `doc_id` scope)→ answer_detail 不在預覽(經儲存 real-query 生效);**mockup 2 句文字已對齊 frontend** = single source of truth。

### Decisions(cont)
- F3 self-contained over extract(R2 deviation,§1.3 零 KB-page touch)。
- config-test draft_config 機制 over doc_id scope(免 backend 改動 + 更清晰 A/B;answer_detail 預覽列 documented limitation)。

### Blockers
- 無(待 V 可選 live 視覺驗 + 用戶 closeout 決策)。

### Commits
| Hash | Subject |
|---|---|
| `bf7769d` | docs(planning): W58 kickoff — per-doc config UI + doc-detail mockup |
| _(pending)_ | feat(frontend): W58 per-doc config UI(F2-F4) |

---

**End of W58 progress(Day 1)**

---
phase: W43-per-kb-tunable-retrieval-config
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: draft       # draft | active | closed — flips active 只在 0.5 gate PASS 後
---

# Phase W43 — Progress

> Daily progress + 結尾 retro。每 commit 對應一個 Day-N entry(R2;`docs(planning):` housekeeping commits 例外）。
> **本 phase 仍 draft** — F1+ GATED on F0 0.5 STOP+ask(H1 confirm + ADR-0040 Accept + stakeholder scope)。Day 0 之後嘅 Day-N 留待 gate PASS 後填。

---

## Day 0 — 2026-06-01: F0 Kickoff + draft + review amendments

**Origin**:W42 closeout 後 rolling JIT(§9 W19+)。Trigger = 2026-06-01 AR 文件(`test-kb-20260531-v1`)smoke 揭全域 retrieval 配置同**內容格式耦合** + 用戶 foundational vision(per-KB user-tunable config + on-platform test-loop)。

### Done(F0 — 規劃,非 code)
- `plan.md` v1.0 draft 起草(MVP runtime-only scope:chunker / Fork B / per-doc / version history defer W44+)
- `docs/adr/0040-per-kb-tunable-retrieval-config-scope.md` DRAFT(Proposed)+ ADR README index row
- §5 H1 assessment(config 解析由全域 → per-KB 優先序鏈 = **H1-adjacent**,需 ADR-0040 + stakeholder scope)
- §4 R6 Day 0 recursive verification 6 catch(後加第 7 catch — 見下）
- `checklist.md` + `progress.md`(本文件)Day 0 — **完成 0.4**

### Review amendments(2026-06-01 chat,plan v1.0 → v1.1,draft 階段非 active deviation)
本 session review 後加嘅 5 點(全記 plan §7 changelog):
1. **eval-blindness keystone(§4 catch 7)** — `drive_user_manuals` 30-query RAGAs eval 喺激進配置下 PASS,但同一配置爆 flood → RAGAs 量文字質素、量唔到 presentation(圖/citation/marker 數)。可信信號 = RAGAs + presentation counters 雙軸。G5/F4.2 改雙軸 + eval set 須含窄 how-to query。
2. **G2/F4.3 對稱** — AR 側補「how-to 答案仍正確完整(faithfulness/correctness 不退)」,唔淨數 citation。
3. **BUG-031(`508f979`)對齊** — `max_images_per_answer` = BUG-031 前端 `INLINE_IMAGE_CAP=8` 嘅後端 per-KB 版;後端為主、前端 fallback;pill-grouping 正交不動。
4. **F2.6 harness 信號可信 mini-gate** — F3 GATED on it:先驗證量度(counters 分得開 / RAGAs 印證盲點 / variance 唔蓋過差異)後 build UI。
5. **KB id drift fix** — `test-kb-20260531-1` → `test-kb-20260531-v1`(4 處)。

### Decisions / OQ
- 決定:MVP = runtime-only;圖洪水深層修(ingestion-bound,證偽實驗證)split out W44+ ADR-0041。
- 決定:Fork B(query-intent gate)defer — 證偽實驗顯示 AR 未證明需要(避免 over-engineer per Karpathy §1.2)。
- OQ:本 phase **無 OQ 變更**(decision-form.md 無需同步)。

### Blockers / Gates(open)
- ⛔ **0.5 F1 GATE** — F1 code 之前需 user STOP+ask confirm:H1 boundary + ADR-0040 Proposed → Accepted + stakeholder scope(0.2)簽。**未過 gate,F1+ 一律唔開工。**
- 0.2 stakeholder scope 確認 — pending(architecture 擴張需 owner 簽)。

### Commits
- `267a46c` — `docs(planning): W43 F0 draft (plan + ADR-0040) + 2026-06-01 review amendments`(plan v1.1 + ADR-0040 Proposed + README row + 5 點修訂)
- `<this commit>` — `docs(planning): W43 F0 0.4 — checklist + progress Day 0`

---

_(Day 1+ 留待 0.5 gate PASS 後填 — 未過 gate 不開 F1 code。)_

---

**End of W43 progress(Day 0 — F0 draft,GATED)**

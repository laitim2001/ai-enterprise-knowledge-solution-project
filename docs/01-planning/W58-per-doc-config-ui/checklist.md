---
phase: W58
plan_ref: ./plan.md
status: active     # active | closed
last_updated: 2026-06-09
---

# W58 — Checklist

> 逐項 atomic;done → `[x]`,未做標 🚧 + 理由。Plan locked 2026-06-09(路徑 A 先擴 mockup)。

## Setup
- [x] S1 — ADR-0051 寫 + Proposed(mockup review 後 Accepted)+ README index
- [x] S2 — plan / checklist / progress committed(kickoff commit)

## F1 — 擴 doc-detail mockup(H7 gate)
- [x] F1.1 — `ekp-page-doc-detail.jsx` 加 tab strip:[Chunk inspector](現有 pipeline strip + image strip + 3-pane,wrap 入 `tab==="inspector"` fragment,視覺不變)+ [Per-doc 配置](新);mirror KB `.tabs`/`.tab` pattern
- [x] F1.2 — per-doc config 面(`DocConfigTab`):`answer_detail`(繼承 KB/concise/detailed 3-way seg)+ Citation expansion `DocTuneGroup` + Neighbour images + 圖片上限 `DocTuneGroup`(只 post-retrieval 旋鈕;`DocTuneKnob`/`DocTuneGroup`/`DocSwitchKnob` mirror KbTune*)
- [x] F1.3 — 繼承 KB / 已覆寫(此文件)badge + 還原至 KB affordance + scope 註(per-query > per-DOC > per-KB > 全域 · ADR-0050,banner + footer)+ 檢索入口旋鈕 explanatory card(KB-level only,IcShield)
- [x] F1.4 — per-doc config-test 面(`DocTestResultCard`/`DocTestMetric` mirror;A/B = 此文件 vs 繼承 KB;`POST /kb/{kb}/config-test · doc_id`;length-bias caveat)。babel JSX parse OK
- [x] F1.5 — **用戶 review mockup(H7 gate)PASS**(2026-06-09 approve)→ ADR-0051 Accepted,F2-F4 解鎖

## F2 — API client(F1 approved 2026-06-09)
- [x] F2.1 — `frontend/lib/api/doc-config.ts`:get/put/delete/list per-doc config(`DocConfig` type 鏡 backend);加 `ApiClient.put` 方法(additive)
- [x] F2.2 — `config-test.ts` 加 `enable_chapter_overview_pin` + `doc_id`(additive,backend 已有)

## F3 — 砌 doc-detail config tab(F1 approved)
- [x] F3.1 — **deviation from R2**:建 self-contained `doc-config-tab.tsx`(`DocTuneKnob`/`DocTuneGroup`/`DocSwitchKnob`/`DocConfigResultCard` mirror KB pattern,「繼承 KB」framing)而非抽 KB 頁元件 —— §1.3 唔掂 3174 行 KB 頁 + mockup 本身分開 Doc*/Kb* + framing 不同(記 plan §7 changelog)
- [x] F3.2 — doc-detail `page.tsx` 加 tab strip(inspector wrap 入 fragment 視覺不變 + config tab)+ render `<DocConfigTab>`,逐元素 mirror approved mockup
- [x] F3.3 — wire CRUD(load via `docConfigApi.get` + save via `put`)+ config-test(draft_config 機制,見 F4 fidelity note)

## F4 — Test + fidelity(F3 done)
- [x] F4.1 — `tests/unit/doc-config-tab.test.tsx`(4 test:render 全 section / inherit→save disabled / override answer_detail→已覆寫+save enabled / save PUTs config)。**4 passed**
- [x] F4.2 — §12 H7 fidelity self-check:逐元素對齊 approved mockup。**一處偏差**:config-test 機制由 mockup 暗示嘅 `doc_id` scope 改為 `draft_config` 預覽(免 backend 改動 + 「proposed-doc vs 繼承 KB」A/B 更清晰);`answer_detail` 不在 `DraftRetrievalConfig` → 試跑預覽唔覆蓋(經「儲存」real-query 生效,W57 dominant-doc 解析覆蓋)→ **mockup 2 句文字已對齊 frontend**(single source of truth)。既有 KB SettingsTab test(kb-detail-tabs/kb-settings-reindex/kb-detail)全綠 = 零回歸(R2 守)。tsc/eslint/prettier clean

## Closeout
- [ ] C1 — plan/checklist/progress closed;progress retro
- [ ] C2 — ff-merge → main(用戶確認);platform design doc §7 P2b 標 done

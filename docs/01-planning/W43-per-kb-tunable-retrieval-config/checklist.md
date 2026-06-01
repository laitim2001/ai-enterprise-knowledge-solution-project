---
phase: W43-per-kb-tunable-retrieval-config
plan_ref: ./plan.md
status: draft       # draft | active | closed — F1+ GATED on F0 0.5 STOP+ask (H1 confirm + ADR-0040 Accept + stakeholder scope)
last_updated: 2026-06-01
---

# Phase W43 — Checklist

> Atomic checkbox(每 item ≤ 1–2 hour effort),鏡像 `plan.md` §6 + §2 F-phase。
> AI tick 完成嘅 item;唔可以 tick 嘅 item 喺 `progress.md` Day-N entry 寫原因。
> **F1+ 全部 GATED** — 喺 0.5 STOP+ask(H1 confirm + ADR-0040 Accept + stakeholder scope)之前,**唔可以 tick 任何 F1+ code item**。

## F0 — 規劃 + ADR-0040 起草 + stakeholder scope gate

- [x] 0.1 `plan.md`(v1.1 — initial draft + 2026-06-01 review amendments)
- [x] 0.3 `docs/adr/0040-per-kb-tunable-retrieval-config-scope.md` DRAFT(Proposed)
- [x] 0.4 `checklist.md`(本文件)+ `progress.md` Day 0
- [ ] 0.2 **stakeholder scope 確認**(architecture 擴張,非 bugfix → owner 簽 scope)
- [ ] **0.5 STOP+ask user confirm H1 boundary + ADR-0040 Accept + scope(F1 GATE)** ⛔

## F1 — 配置模型 + 解析(GATED on 0.5)

- [ ] F1.1 `KbConfig` 加 ~12 runtime 旋鈕 `Optional` 欄位(`None` = inherit 全域)
- [ ] F1.2 `EffectiveConfig` resolver(per-query > per-KB > 全域 default）
- [ ] F1.3 `/query` 路徑改用 resolved config(parent_doc + neighbour-images wire)
- [ ] F1.4 `/chat` SSE stream 路徑改用 resolved config
- [ ] F1.5 `synthesizer.py` `expand_citations`(sync + stream)收 resolved config(per §4 catch 2 — 唔係 query.py）
- [ ] F1.6 `max_images_per_answer` cap apply(+ 同 BUG-031 `508f979` 前端 `INLINE_IMAGE_CAP=8` 對齊:後端 per-KB 為主、前端 fallback；pill-grouping 正交不動）
- [ ] F1.7 storage 持久化(Postgres + in-memory)+ 既有 KB migration-default(ADR-0028 先例,`None` = 沿用全域,零 breaking）
- [ ] F1.8 tests(resolver 優先序 / 三 wire point honor / back-compat bit-identical)+ ruff + mypy

## F2 — 平台 full-pipeline 試跑 harness

- [ ] F2.1 full-pipeline config-test 端點(draft config override;擴 V4 retrieve-only → full pipeline per §4 catch 3)
- [ ] F2.2 multi-run(N=3-5)+ variance band 聚合(per 證偽發現④ ~20% figure 波動)
- [ ] F2.3 metrics 輸出（answer / citation count / figure count raw+dedup / latency / variance / 每 citation section+圖數）
- [ ] F2.4 (可選)draft config vs 已存 config A/B 對照
- [ ] F2.5 tests
- [ ] **F2.6 harness 信號可信 mini-gate(F3 GATE;per §4 catch 7)** — aggressive vs conservative 實跑:(a) presentation counters 分得開 (b) 純 RAGAs 分唔開印證盲點 (c) variance band 唔蓋過 (a) 差異 ⛔

## F3 — UI(前端;受 H7 約束;**GATED on F2.6 PASS**)

- [ ] F3.1 **mockup 確認** / STOP+ask if design-mockups 缺對應 spec(§5.7 H7）
- [ ] F3.2 KB Settings 配置面（分組旋鈕 檢索/引用/圖片 + 進階收合 + ingestion 欄位「需重新索引」badge）
- [ ] F3.3 試跑面板（query + multi-run + metrics + variance band）
- [ ] F3.4「儲存到此 KB」persist
- [ ] F3.5 frontend tests

## F4 — 驗證 + 收尾

- [ ] F4.1 Pre-flight（§10.3 5b — Langfuse /health 200 + Postgres SELECT 1）
- [ ] F4.2 cross-doc eval no-regression（**雙軸 per §4 catch 7** — RAGAs faithfulness/recall AND presentation counters；eval set **必須含窄 how-to query**）
- [ ] F4.3 **G2 decisive proof**（AR 保守 ≤3 cit **且答案仍正確完整** + DCE 完整性 同時成立、冇改全域）
- [ ] F4.4 governance（who-can-edit admin/KB-owner + audit reuse ADR-0027 audit_log）
- [ ] F4.5 cross-doc sync（plan/checklist/progress + session-start §10 W43 row）+ ADR-0040 final status + W44+ candidate（chunker ADR-0041）
- [ ] F4.6 commit + push

---

## Cross-Cutting

- [ ] 所有 deliverable committed to git
- [ ] OQ status 變更反映入 `docs/decision-form.md`（預期 N/A — 本 phase 無 OQ 變更；若有則同步）
- [ ] architectural-adjacent 決定 documented as ADR（ADR-0040 covers config-scope；chunker 圖洪水深層修 → W44+ ADR-0041）
- [ ] `progress.md` retro section written（phase 結束填）
- [ ] `progress.md` frontmatter status flipped to `closed`
- [ ] Phase W44+ kickoff trigger noted in retro（chunker ADR-0041 / per-doc scope / Fork B）

---

**Lifecycle reminder**:呢份 checklist 隨 plan deliverables 衍生。新加 deliverable 必須先入 `plan.md` + §7 changelog,再加 checklist item。**F1+ tick 之前必須過 0.5 gate。**

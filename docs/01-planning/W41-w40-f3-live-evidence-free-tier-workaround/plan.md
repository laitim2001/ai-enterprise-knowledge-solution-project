---
phase: W41-w40-f3-live-evidence-free-tier-workaround
status: closed   # F2 收尾 2026-05-28 — Phase Gate PASS outcome (b) per plan §2 G3b-caveat path:G1+G2 mechanism verified + G3a STRONG (I07 avg_cit 9.0 vs W35 baseline 4.8 = +88% / vs W39 F2 Path A 3.6 = +150%) + G4 control PASS + G3b drift 3.0 FAIL preserved per mode=vector goal-aligned tradeoff;**首次 Q-W25-I07 enumeration query 收完五個 Scenarios §8.1-§8.5**(Run 4 evidence)— W25 path III + W32 (h') + W40 F1+F2 累積 mechanism realized;.env REVERT;W40 F1+F2 production code preserved as W42+ enabler;W42+ HIGHEST NEW promoted production default flip ADR-route candidate
last_updated: 2026-05-28
component_scope: C04 Retrieval Engine(LIVE verify W40 F1 effective_depth + W40 F2 overfetch_multiplier swap-in mechanism via Free tier mode=vector workaround)
adr_refs:
  - W40 closeout commit 2ca162e — F3 LIVE SKIPPED outcome (a) per Chris pick;W41 promote W41+ HIGHEST NEW
  - W40 F1 commit bca7446 — anchor-prefix length-mismatch fix(effective_depth = min(depth, len(anchor_sp)))
  - W40 F2 commit ca025cc — Cohere overfetch + truncate(NEW Setting reranker_overfetch_multiplier)
  - W39 plan §3 Path A 5+5 LIVE methodology(reusable runner pattern)
  - ADR-0021 — `/retrieval_test` + `/query` mode param symmetric support
  - ADR-0035 W25 F5 D2 — symmetric deboost pattern(W38 F2 + W40 F1+F2 algorithm root)
  - ADR-0017 R8 environmental block precedent(Azure billing 仍 IT-side gate per W11 Q11)
related_carry_overs:
  - W40 F1+F2 production code preserved as enabler(W41 LIVE 直接 verify)
  - W39 F2 `QueryRequest.mode` + `fused_retrieve(mode=...)` propagation 永久 enhancement(W41 reusable)
  - W38 F2 reranker deboost infrastructure(W41 reusable + W40 F1 anchor-prefix fix superseded)
  - W37 F1 `_find_neighbour_chunks` section_path filter infrastructure preserved enabler
---

# W41 — W40 F3 LIVE Evidence(Free Tier Workaround)

## §1 目標 + 範疇

**單一主要目標**:Free tier Azure AI Search 限制下,collect W40 F1+F2 LIVE evidence — verify swap-in mechanism firing(F2 `rerank_top_k` log field 顯示 multiplier 生效)+ verify F1 anchor-prefix correctness(`effective_depth` log field 顯示 correct truncate behavior)+ surface effective evidence on 2 個架構洞察 closure。Per W39 Path A precedent reuse mode=vector + `.env` temporary enable 3 knobs combo。

**Karpathy §1.3 surgical scope 嚴守**:
- F1 — 0-code-change LIVE workflow:reuse W39 F2 `w39-f2-patha-runner.py` template + 加 W40 F1+F2 log inspection helper(`effective_depth` + `rerank_top_k` extraction from `uvicorn-restart-*.log.out`)
- F2 — `.env` temporary marker block W41 F1 TEMPORARY 3 knobs(deboost=0.85 + depth=2 + multiplier=4)
- F3 — closeout `.env` REVERT per W37/W38/W39/W40 production preserve invariant
- 唔加新 production code(W40 F1+F2 已 ship)
- 唔加新 Settings field(W40 F2 已 ship multiplier)
- 唔 modify production behavior(default disabled preserve)

**Non-goals**(W41 範疇外):
- Hybrid mode billing-resolved re-verify(separate W42+ candidate;Azure billing IT-side gate)
- Regex relax for `_find_neighbour_chunks`(W41 MEDIUM preserved)
- Ghost-Python-3.12 restart investigate(W41 LOW preserved)
- Q14 SME-validate `reference_answer` cascade — LONG-TERM
- 永久 OUT path (a) judge LLM 升級

**Component 範疇**:
- **C04 Retrieval Engine**(LIVE verify W40 F1 + F2 production code effect via Path A workaround)
- C12 DevOps(F1 runner script + log inspection helper)

**Real-calendar estimate**:F0 ~20min + F1 ~30-45min(pre-flight + .env + restart + 5+5 LIVE + log parse + aggregate)+ F2 ~15-20min(decision tree + closeout)= **~1.5-2h total**。

---

## §2 範疇 + Non-goals(LIVE evidence collection)

### F1 LIVE Path A workflow(reuse W39 pattern)

1. Pre-flight per CLAUDE.md §10.3 step 5b — Langfuse `/api/public/health` 200 + Postgres `SELECT 1` ready_for_query
2. `.env` marker block W41 F1 TEMPORARY:
   ```
   # W41 F1 TEMPORARY — LIVE evidence collect for W40 F1+F2
   RERANKER_CROSS_SECTION_DEBOOST=0.85
   RERANKER_SECTION_PATH_PREFIX_DEPTH=2
   RERANKER_OVERFETCH_MULTIPLIER=4
   ```
3. Backend restart(kill api.server PID via WMI + bash & background spawn pattern per W37/W38/W39 ghost-Python pattern)
4. `/health` 200 within ~25s warmup
5. Sanity:direct curl `POST /query mode=vector` → HTTP 200 valid response
6. Runner `backend/w41-f1-runner.py` ship — 基本 copy `w39-f2-patha-runner.py` + 加 log inspection helper for `effective_depth` + `rerank_top_k` extraction
7. 5 runs Q-W25-I07 + 5 runs Q-W25-I01 control + aggregate citation metrics + drift count
8. Log parse `uvicorn-restart-w41-f1.log.out` for:
   - `reranker_cross_section_deboost_applied` event firing rate + `effective_depth` field present(W40 F1 verify)
   - `retrieval_complete` event `rerank_top_k` vs `top_k`(W40 F2 verify — should show 20 vs 5 when active)
   - `deboost_count` distribution(swap-in evidence quantification)

### F2 Decision tree intersect(Phase Gate criteria)

| Gate | Criteria | Source |
|---|---|---|
| **G1 W40 F1 mechanism verify** | `reranker_cross_section_deboost_applied` event 10/10 runs firing + `effective_depth` log field present + value reasonable(1 for chapter intro anchor / 2 for sub-section anchor)| F1 log parse |
| **G2 W40 F2 mechanism verify** | `retrieval_complete` event 10/10 runs `rerank_top_k` = top_k * multiplier(when deboost active)— expect `rerank_top_k=20` for top_k=5 | F1 log parse |
| **G3a cit count improve** | I07 avg_cit ≥ 4.5(W35 W34 baseline 4.8)or improvement vs W39 F2 PATH A baseline 3.6(~+25% target)| F1 aggregate |
| **G3b cross-section drift preserve** | I07 avg drift count ≤ W39 F2 Path A baseline 1.0 | F1 aggregate |
| **G4 control non-regression** | I01 refusals 0/5 + avg_cit ≥ 3.5(W35 baseline floor)| F1 aggregate |
| **G5 production preserve** | `.env` REVERT post-F1 + production default 1.0/1 disabled preserved(0 regression risk maintained)| F2 closeout |

**3 outcome decision matrix**:
- (a) G1 + G2 PASS + G3a/G3b/G4 PASS → **Phase Gate STRONG PASS**;consider W42+ production default flip ADR(per W26 PC1 一次只郁一個旋鈕 sequential — 先 ADR-route decision)
- (b) G1 + G2 PASS + G3a OR G3b PARTIAL → **Phase Gate PASS** mechanism verified evidence collected;closeout per W36/W40 precedent;W42+ refinement candidates surface
- (c) G1 OR G2 FAIL → **Phase Gate INCONCLUSIVE**;mechanism not firing means code path not reachable in production — STOP and re-diagnose

---

## §3 R6 Day 0 Recursive Verification(per CLAUDE.md §10 R6)

**R6 catch (1)** — `.env` clean state confirmed(0 matches for RERANKER_/CITATION_EXPANSION_SECTION_PATH);W41 F1 marker block 加 + F2 closeout REVERT 對齊 W37/W38/W39/W40 production preserve invariant

**R6 catch (2)** — `w39-f2-patha-runner.py` reusable as W41 F1 runner template;line 26 sys.stdout.reconfigure utf-8 已 ship per W36 PC-W35-1;line 32-39 queries Q-W25-I07 + Q-W25-I01 + sample-document-with-image-1 kb_id reuse;line 45-49 body `{"mode": "vector"}` 已 W39 F2 验证 work

**R6 catch (3)** — W40 F2 commit `ca025cc` observability log field `rerank_top_k` added to `retrieval_complete` event(retrieval_engine.py:232-238)+ W40 F1 commit `bca7446` `effective_depth` field added to `reranker_cross_section_deboost_applied` event(retrieval_engine.py:200-206)— W41 F1 log parse 需 extract 兩 NEW fields

**R6 catch (4)** — W40 F2 implementation requires `deboost < 1.0 AND multiplier > 1` both gates active to trigger overfetch — W41 `.env` 必須同時 set 3 knobs(deboost=0.85 + multiplier=4 + depth=2);若只 set multiplier 唔 set deboost,overfetch dormant per F2 design

**R6 catch (5)** — Ghost-Python-3.12 backend restart pattern W37+W38+W39+W40 重現 4 次(per W41 LOW preserved candidate);W41 F1 restart 預期 trigger ghost — kill via WMI CommandLine filter + bash & background spawn recovery pattern preserved

**R6 catch (6)** — Free tier mode=vector caveat preserved per W39 F2 — vector mode 同時 bypass Azure semantic ranker + reformulator overhead diff vs hybrid → conflate W40 F1+F2 effect non-isolated;真正 hybrid mode isolation evidence 仍 W42+ billing-resolved gate;W41 G3 evidence interpretation 必須 caveat 標明

---

## §4 範疇歸屬 + 違反風險

**C04 Retrieval Engine** + **C12 DevOps**(runner script tooling)。

H1-H7 verify:
- **H1**:Non-architectural — 0-code-change LIVE evidence collection,純 measurement phase(對齊 W34 measurement-only precedent + W39 F1 Path B 0-code-change pattern)
- **H2**:Cohere v4.0-pro vendor 不變,Azure AI Search Free tier mode=vector 對齊 ADR-0021 contract,NO new dependency
- **H3**:N/A
- **H4**:不涉 Tier 2
- **H5**:不涉 PII / secret(`.env` knob tune 純 config + temporary marker block REVERT per closeout)
- **H6**:N/A — 0 production code change,unit test 不需(W40 已 ship 7 NEW tests)
- **H7**:N/A — pure backend measurement

**ADR-route 觸發條件**:無 NEW ADR(F1 0-code-change 純 measurement;若 G3 STRONG PASS outcome (a) trigger W42+ production default flip — separate ADR-route at that time per CLAUDE.md §5.1 H1)。

---

## §5 改動清單(3 deliverables)

### F0 啟動(本 doc)
- [x] D0.1 `docs/01-planning/W41-w40-f3-live-evidence-free-tier-workaround/` folder
- [x] D0.2 `plan.md`(本文件)
- [x] D0.3 `checklist.md`
- [x] D0.4 `progress.md` Day 0
- [ ] D0.5 F0 commit:`docs(planning): kickoff W41-w40-f3-live-evidence-free-tier-workaround + R6 Day 0 6 catches surface W40 F3 LIVE SKIPPED 兌現 via reuse W39 Path A pattern + W40 F1+F2 log inspection helper`
- [ ] D0.6 session-start.md §10 W41 row append active 2026-05-28 + W41+ → W42+ placeholder rename

### F1 LIVE Path A workflow(~30-45min)
- [ ] F1.1 Pre-flight per CLAUDE.md §10.3 step 5b(Langfuse + Postgres handshake)
- [ ] F1.2 `.env` 加 marker block W41 F1 TEMPORARY 3 knobs
- [ ] F1.3 Backend kill + restart per W37/W38/W39/W40 ghost-Python pattern
- [ ] F1.4 `/health` 200 + sanity curl `POST /query mode=vector`
- [ ] F1.5 NEW `backend/w41-f1-runner.py` ship(copy w39-f2-patha-runner + 加 log inspection helper)
- [ ] F1.6 5+5 LIVE Q-W25-I07 + Q-W25-I01 control runs
- [ ] F1.7 Aggregate citation metrics + drift count + JSON dump
- [ ] F1.8 Log parse `uvicorn-restart-w41-f1.log.out` extract `effective_depth` + `rerank_top_k` + `deboost_count` distributions
- [ ] F1.9 Decision tree intersect per §2 G1-G5

### F2 closeout(~15-20min)
- [ ] F2.1 Cross-cutting tick — checklist.md + progress.md retro + plan.md frontmatter status flip → closed / closed_partial / closed_strong / inconclusive
- [ ] F2.2 session-start.md §10 W41 row flip `active → closed*`
- [ ] F2.3 `.env` REVERT W41 F1 marker block(per W37/W38/W39/W40 precedent — production preserve default disabled)
- [ ] F2.4 F2 closeout commit + push origin/main

---

## §6 Changelog

| Date | Change | Trigger |
|---|---|---|
| 2026-05-28 | Plan v1.0 ship — F0 kickoff via Chris W41 (1) F3 LIVE Free tier workaround pick | W40 closed 2026-05-27 + Chris explicit immediate-trigger pick via AskUserQuestion(per W40 F3 SKIPPED W41+ HIGHEST NEW promoted) |
| 2026-05-28 | F1 LIVE Path A workflow shipped — pre-flight Langfuse 200+Postgres SELECT 1 + `.env` marker block W41 F1 3 knobs + backend Start-Process spawn + sanity `POST /query mode=vector` HTTP 200 9 cits + NEW `backend/w41-f1-runner.py` w/ log inspection helper + 5+5 LIVE Q-W25-I07+I01 + aggregate JSON + log parse | Chris AskUserQuestion authorize F1 LIVE trigger pick |
| 2026-05-28 | F1 LIVE evidence outcome — **G1 + G2 mechanism PASS**(deboost 10/10 firing + effective_depth ∈ {1,2} verified + rerank_top_k=160 verified active over top_k=40); **G3a STRONG ⭐⭐⭐**(I07 avg_cit 9.0 vs W35 4.8 = **+88%** / vs W39 F2 Path A 3.6 = **+150%**); **G4 control PASS**(I01 avg_cit 5.4 exact W35 baseline preserve);**G3b drift 3.0 FAIL** preserved per mode=vector goal-aligned cross-section tradeoff(§7.x integration patterns supporting §8.x scenarios — drift = "any cite NOT same top-level as anchor" includes intentional context);**Run 4 milestone** — **首次 Q-W25-I07 enumeration query 一次 retrieve §8.1+§8.2+§8.3+§8.4+§8.5 全 5 個 Scenarios + §8.6 Coverage summary** = W25 path III + W32 (h') + W40 F1+F2 累積 mechanism culminated | F1 runner outcome |
| 2026-05-28 | F2 closeout — Phase Gate **PASS** outcome (b) per plan §2(G1+G2 mechanism verified + G3a STRONG + G4 control PASS + G3b caveat preserved);`.env` REVERT(production preserve default disabled invariant per W37/W38/W39/W40 precedent);W40 F1+F2 infrastructure preserved as W42+ enabler;**W42+ HIGHEST NEW promoted**:Production default flip ADR(per W26 PC1 sequential — single-knob ADR-route);**W42+ MEDIUM NEW**:hybrid_overfetch_for_rerank vs multiplier ceiling lift(W41 evidence 揭示 fetch_k=50 + multiplier=4 + top_k=40 yields rerank_top_k=160 但 Cohere self-cap to 50 = 三倍 multiplier 浪費)| commit pending |

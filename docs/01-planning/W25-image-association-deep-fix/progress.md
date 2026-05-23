---
phase: W25-image-association-deep-fix
plan_ref: ./plan.md
checklist_ref: ./checklist.md
status: in-progress    # in-progress | closed
---

# Phase W25 — Progress

> Daily progress + 結尾 retro。
> 每 commit 必須對應一個 Day-N entry mention(R2 binding rule per PROCESS.md §5)。

---

## Day 0 — 2026-05-23: Kickoff

### Trigger

BUG-009 / BUG-010 / BUG-011 cascade 接通晒 screenshot upload + counter + private-blob proxy + KB Images tab 真縮圖 render —— 但 chat citation **仍從未帶圖**。Investigation memo `docs/03-implementation/image-chunk-retrieval-investigation-2026-05-23.md` 揭示 root cause two-pronged(H1 image chunks 被 60% low_value filter 掃走 / H2 vocab-overlap 輸畀 TOC chunk);AskUserQuestion 用戶揀 **Path III phase-level full optimization**(D3 + D4 + D2 + D1)= 完整解決圖文關聯問題,非單 band-aid。

### Action

**Phase W25 kickoff per CLAUDE.md §10 R1**:

- **F0.1** `docs/01-planning/W25-image-association-deep-fix/` folder created
- **F0.2** `plan.md` filled 1.0 + status `active`:
  - §1 Scope:圖文關聯 deep-fix,目標 = chat answer cite 對 section → citation 帶對 section images
  - §2 Deliverables F1-F7 atomic + acceptance criteria
  - §3 Phase Gate G1-G6 hard pass conditions
  - §4 Risks R1-R7 with mitigation
  - §5 Day-by-day ~20 calendar days(actual collapse predicted 3-7× per W12-W18 / W20-W24 pattern)
  - §6 Dependencies from W24c-users-rbac(R8 + R6 + smoke-user-deferred allowance inherited)
  - §7 Changelog v1.0 + R6 Day 0 amendment(see R6 catch below)
  - §8 5 Locked Design Decisions per user defaults
  - §9 Component Impact Map(C01 + C04 + C05 + C06)
- **F0.3** `checklist.md` derived from plan §2(F0-F7 atomic items + Cross-cutting C1-C7)
- **F0.4** `progress.md` Day 0 entry init(this entry)

### R6 Pre-Active-Flip Recursive Grep Verification

**Applied at Day 0 plan kickoff,scope = plan-text 自己**(per CLAUDE.md §10 R6 + W23 F3 amendment + memory `feedback_design_fidelity.md` D9 plan-text-contamination pattern)。Catch upfront before any F1+ active-flip。

**Grep targets** + **findings**:

| # | Plan-text reference | Grep finding | Action |
|---|---|---|---|
| (i) | `low_value_floor` 100 → 60 chunker constant | `layout_aware.py:35 _TOKEN_LOW_VALUE_FLOOR = 100`(module constant)+ `:69 low_value_floor: int = _TOKEN_LOW_VALUE_FLOOR`(class param default)+ `architecture.md §3.3 soft floor` cite | Plan-text **correct**;F1.2.1 change 落 module constant level + ADR-0033 cite §3.3 amendment |
| (ii) | `hybrid_searcher.py` filter stage | Actual file = `backend/retrieval/hybrid.py`(no `_searcher` suffix)| Plan-text **inaccurate naming** — Edit applied to plan §7 changelog;F5 implementation reference 修正為 `hybrid.py` |
| (iii) | "filter 階段加 condition `low_value=true` AND `embedded_images_json` non-empty → retain weight × 0.7" | **Actual filter mechanism** = Azure Search server-side OData `_DEFAULT_FILTER = "enabled eq true and low_value_flag eq false"`(`hybrid.py:4 + :41`) —— **NOT Python `if` filter** | **Major plan amendment** — D2 implementation 要由 server-side filter → client-side post-filter Python override(filter clause 去掉 low_value_flag + 加 Python post-filter)+ **可能觸 H1**(改 §3.6 retrieval policy mechanism interface)→ F5.1.2 CH-003 spec drafting 必先 surface H1 trigger 風險畀 Chris 決定(CH-003 alone vs CH-003 + co-ADR-0035)。Plan §2 F5 + §7 changelog 已 amend |
| (iv) | `eval-set-v0.yaml` 位置 | Actual location = `docs/eval-set-v0.yaml`(NOT `backend/eval/`)| Plan-text **already correct**(F2.2.1 reference 「`eval-set-v0.yaml` 6 samples」without path prefix);no amendment needed |

**R6 catch evaluation**:呢個 R6 application 早期 catch 咗 1 個 major plan-text contamination(iii)+ 1 個 minor naming(ii),F1 / F5 active-flip 之前已 amend 完。**Cumulative R6 occurrences across phases**:W22 D1 + D8 + D9 + W23 (formalized) + W24c (~100 cumulative findings)+ W25 Day 0(4 findings catch upfront)= ongoing empirical validation of R6 recursive-scope value。

### Decisions(Day 0)

- **D0.1** — Phase folder naming `W25-image-association-deep-fix/`:user-approved chat 2026-05-23(a)
- **D0.2** — F1→F2→F3→F4→F5→F6→F7 sequence:user-approved chat 2026-05-23(b);rationale per plan §2 — D3 first(F1)because chunker change conditions D2/D4 behaviour;D4 second(F3)because retrieval-level optimization needs chunker stable;D2+D1 last(F5)because safety net on top of D3+D4 lift
- **D0.3** — 5 locked design defaults per user chat 2026-05-23(c):eval-v0 + image queries / dev-only re-ingest / floor 100→60 + adjacent-short-merge / P95<5s hard cap / D2 weight × 0.7 — all locked in plan §8
- **D0.4** — **D2 H1 boundary re-examination**(per R6 finding iii)— F5.1.2 spec drafting 必先 surface H1 trigger 風險畀 Chris 決定。**Default assumption(temporary)**:H1 NOT triggered(filter mechanism shift 屬 implementation detail not spec-interface),但 confirm 喺 F5.1.2;若 H1 triggered → CH-003 + co-ADR-0035 mandatory
- **D0.5** — **ADR numbering plan**:ADR-0033(D3 chunker low-value tuning)+ ADR-0034(D4 query expansion / RAG-fusion)+ potential ADR-0035(D2 retrieval filter mechanism,if H1 trigger confirmed F5)。Next available 0033 per `docs/adr/README.md` "Next NNNN" section(0030 + 0032 deliberately SKIPPED per W19 F2 absorb decision)

### Blockers

無。所有 F1-F7 work AI-controllable;唔依賴 Track A IT cred populate event(per plan §6 W17 beta-hardening parallel-track precedent)。

### Actual vs Planned Effort

| Deliverable | Planned (h) | Actual (h) | Variance |
|---|---|---|---|
| F0 kickoff(plan + checklist + progress + R6 verify + kickoff commit)| 4-6 | ~3 | -1 to -3(R6 grep efficient,plan structure clear ahead-of-time)|

### Commits

_(見 commit footer — `chore(planning): kickoff W25 image-association-deep-fix`)_

### Carry-overs from W24c-users-rbac

Per session-start.md §11 W24c CLOSED block — **none directly for W25**:
- W24c 屬 Wave C3 RBAC frontend/backend,scope independent from retrieval/chunker
- Cross-phase pattern inheritance:R8 corp-proxy(若 F3 需要新 dep)/ R6 recursive scope(已 applied above)/ smoke-user-deferred allowance(F6 manual user-test = user pre-Beta scope per W12-W18 / W20-W24 pattern)

---

**End of Day 0 entry** — F1 active-flip kickoff next session

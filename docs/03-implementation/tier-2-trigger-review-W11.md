---
artifact: tier-2-trigger-review
phase: W11-staged-rollout-25
status: draft                       # `draft` 自 W11 D1 governance review;`active` 喺 Stakeholder W12 production launch retro 後;`closed` 喺 Tier 2 roadmap kickoff 之後
prepared_by: AI(governance review draft)+ Chris(Tier 2 owner per Q12 Resolved)
target_review_date: post-W12 production launch retro(2026-07-19+)
related_artifacts:
  - architecture.md §11 Tier 2 Roadmap(post W12,trigger-driven)
  - docs/03-implementation/w11-staged-rollout-25-prep-deck.md §3 W11.F5
  - docs/03-implementation/beta-plan-v1.md §3 W12 Tier 2 roadmap kickoff prep
  - docs/decision-form.md(Q12 Tier 2 owner Resolved 2026-05-05)
last_updated: 2026-06-09
---

# Tier 2 Trigger Metric Review — W11 D1 Governance Review Draft

> **Purpose**:per W11 plan F5.3 — governance review of Tier 2 capability triggers based on W7-W10 cumulative signal + post-W12 Tier 2 roadmap kickoff decision frame。
>
> **Karpathy §1.2 simplicity-first**:呢份 doc 唔重複 architecture.md §11 內容,只記錄(a)current trigger signal status(W7-W10 cumulative)+(b)gap analysis vs Tier 2 capabilities backlog +(c)decision frame for post-W12 Tier 2 roadmap kickoff。
>
> **H4 Tier boundary reminder**:呢份 doc 屬 **governance review only**,**唔係 Tier 2 implementation**。任何 Tier 2 capability 實際實作仍 out of Tier 1 scope,trigger 透過呢份 doc 累積 signal 後 → post-W12 retro Stakeholder + Chris(Q12 owner)正式 kickoff。
>
> **Re-trigger condition**:每月 update — Beta cohort signal accumulation + Stakeholder feedback round + production traffic distribution shift。

---

## 1. Tier 2 Capabilities Backlog Snapshot(per architecture.md §11.1)

| # | Capability | Trigger Condition(per spec) | W11 D1 Signal Status | Effort Est. |
|---|---|---|---|---|
| TC1 | **GraphRAG / Knowledge Graph** | 詳見 §11.2 T1-T5 matrix(滿足 ≥ 3 條 + Chris approve) | 🟡 **No signal yet**(Beta cohort traffic 未啟動;query log 為空) | 2-3 個月 |
| TC2 | **L4+ Multi-agent orchestration** | 真實 query log 顯示 > 10% 屬「跨 KB synthesis + tool use」 | 🟡 **No signal yet**(single-KB scope confirmed Tier 1;cross-KB 唔 applicable until multi-KB rollout) | 2 個月 |
| TC3 | **Workflow / Plugin builder** | 業務側要求 customizable pipeline per KB | 🟡 **No signal yet**(Stakeholder W6 D5 approval cycle 未提及 customizable pipeline 需求) | 2-3 個月 |
| TC4 | **Multi-tenancy** | 第二個 organization 用同一 platform | 🔴 **Out of Tier 1 boundary**(per Q9 + architecture.md §11;Tier 1 single-tenant Ricoh) | 1.5 個月 |
| TC5 | **Multi-modal retrieval(B 類純圖片搜索)** | Production 顯示 > 5% 純圖片 query | 🟡 **No signal yet**(W2 D3 image format snapshot per Q18 — PNG/JPEG dominant 但 query 行為待 Beta 觀察) | 1.5 個月 |
| TC6 | **Multi-language(JP / ZH)** | 業務側擴 APAC | 🟡 **No signal yet**(Drive Project Tier 1 = Ricoh Japan internal 但 manual 主要英文;APAC 擴展屬 Tier 2 業務決定) | 1 個月 |
| TC7 | **Auto-sync from external source** | Production 顯示 manual upload 係 ops bottleneck | 🟡 **No signal yet**(W7-W10 manual upload 量低 — Beta cohort scope < 250 docs) | 1 個月 |
| TC8 | **Custom LLM fine-tuning** | Generic LLM 喺 domain term 顯著弱 | 🟡 **No signal yet**(GPT-5.5 baseline 未顯示 domain term 弱點;eval-set v0 R@5=0.9722 LIVE post-truststore mitigation) | 視情況 |

**Summary**:8/8 capability backlog items 全部 status `🟡 No signal yet` or `🔴 Out of boundary` — **無一 trigger fire**。Expected — Tier 1 12-week sprint phase + Beta cohort traffic 未啟動,signal accumulation window 落 W11+ post-Track A LIVE deploy。

---

## 2. GraphRAG T1-T5 Trigger Matrix Snapshot(per architecture.md §11.2)

進入 Tier 2 GraphRAG 評估嘅 5 條 trigger,**滿足至少 3 條** + Chris(Q12 Resolved 2026-05-05 owner)approve:

| # | Trigger | 量度方法 | W11 D1 Status | Notes |
|---|---|---|---|---|
| T1 | Corpus scale > 10,000 chunks | Index size | 🔴 **NOT FIRED**(`ekp-kb-drive-v1` ~2,000 chunks W4 D1 baseline;Beta cohort 加 manual 後 ~3,000-5,000 expect)| Tier 1 Drive Project corpus < 5,000 chunks expected ceiling |
| T2 | Real query log 顯示 > 15% 屬「跨文檔 entity relationship reasoning」 | Query classifier on 1-month production log | 🟡 **NO SIGNAL YET**(Beta cohort query log 為空;W11+ accumulate)| Q15 weekly signal report scaffold(W10 D2 F4.3)= input source for monthly aggregation |
| T3 | Tier 1 hybrid + rerank 喺 multi-hop query Recall@5 < 80% | Eval set with 20+ multi-hop ground truth | 🟡 **NO MULTI-HOP EVAL SET**(eval-set v0 = single-hop pattern + 20 borderline cluster Q011-Q020;multi-hop ground truth W11+ candidate)| Eval-set augmentation pipeline(W10 D1 F4.2)= delivery mechanism for multi-hop set |
| T4 | Stakeholder 明確要求「列出所有 X 相關嘅 Y」呢類 query | Business requirement doc | 🟡 **NO SIGNAL YET**(W6 D5 Stakeholder approval cycle 未提及 entity relationship query)| W11+ Beta cohort feedback round 觀察 |
| T5 | 有 dedicated 0.5 FTE 維護 ontology / graph schema | Resource commitment | 🔴 **NOT COMMITTED**(Tier 1 staffing single-person Chris;W11+ secondary oncall add per beta-plan-v1.md §3 W9 staffing trigger)| Q12 Tier 2 owner = Chris approve trigger;FTE 投入屬 post-W12 staffing decision |

**Aggregate**:**0 / 5 triggers fired** as of W11 D1。Expected — Tier 1 boundary preserves single-hop hybrid pipeline,GraphRAG 屬 architecture.md §11 trigger-driven post-W12 decision per CLAUDE.md §5.4 H4。

**Decision per spec**:**< 3 triggers → 唔做 GraphRAG**(節省 ROI 不清晰嘅工作量)。

---

## 3. W7-W10 Cumulative Signal Review

### 3.1 Signal sources actively wired(W7-W10 cumulative,W11+ continues)

| Source | Trigger window | Wire status | Feed into |
|---|---|---|---|
| Q15 weekly signal report scaffold(`backend/observability/weekly_signal_report.py`)| W10 D2 F4.3 ✅ | Scaffold 完整 + 33 tests pass | T2 query classification(post real cohort traffic)|
| Eval-set augmentation pipeline(`backend/eval/eval_set_augmentor.py`)| W10 D1 F4.2 ✅ | Pipeline 完整 + 28 tests pass + dedup + dry-run | T3 multi-hop ground truth augmentation |
| Cost dashboard real-time wire(`backend/observability/realtime_cost.py`)| W10 D3 F5.2 ✅ | 4-status graceful degradation + pricing baseline label | TC5 image-query cost signal(if PNG/JPEG ratio > 5%)|
| `observe_streaming` SSE flow capture | W10 D1 F4.1 ✅ | Async-iterator passthrough wrapper + 17 tests | T2 query intent classification(streaming response cost attribution)|
| Beta feedback yaml(`docs/03-implementation/beta-feedback-W9-W10.yaml`)| W10 D2 mock corpus | NEW W11+ real cohort feedback replaces mock | T4 Stakeholder requirement signal aggregation |

### 3.2 Signal sources pending Beta cohort traffic(W11+ trigger window)

- **Real query log accumulation**(Q6 deferred → W11+ real-cohort signal):base for T2 + T3 + T4 + TC2 + TC5 monthly aggregation
- **Cohort feedback intake**(F2.3 Slack `#ekp-beta`):base for TC3(customizable pipeline)+ TC6(language)+ TC7(auto-sync)signal
- **Production traffic distribution shift**(post-50% rollout EoW + W12 100% rollout):base for TC1(corpus scale post-cohort doc upload)
- **Domain term retrieval quality**(TC8 trigger):base for fine-tuning signal — W11+ eval-set augmentation 加 real cohort query 後再 evaluate

---

## 4. Decision Frame for Post-W12 Tier 2 Roadmap Kickoff

per beta-plan-v1.md §3 W12,Tier 2 roadmap kickoff prep 屬 **W12 production launch retro 之後**。本 review draft 為 input source。

### 4.1 Tier 2 evaluation gate(monthly post-W12)

每個 Tier 2 capability 喺 monthly review 評估:
1. **Trigger signal status**:🔴 NOT FIRED / 🟡 ACCUMULATING / 🟢 FIRED
2. **ROI vs effort**(per architecture.md §11.1 effort estimates;1-3 個月 capability-dependent)
3. **Resource commitment**(Q12 owner Chris approve + dedicated FTE if applicable)
4. **Sequencing dependency**(eg. multi-tenancy → multi-language;graph schema → GraphRAG)

### 4.2 Highest-likelihood Tier 2 candidates(初步 ranking,等 Beta cohort signal refine)

per W7-W10 cumulative signal pattern + Tier 1 architecture extensibility:

1. **TC2 Multi-agent**(low-risk if cross-KB use case 浮面)— W11+ Beta cohort query 觀察「跨 KB synthesis」signal;Tier 1 single-KB scope 內可 prep MCP-ready architecture(per architecture.md §11 Tier 2 friendly 要求)
2. **TC3 Workflow / Plugin builder**(high-value if business 提)— W11+ Stakeholder feedback 觀察 customizable pipeline 需求;Tier 1 modular pipeline architecture preserves extensibility
3. **TC1 GraphRAG**(low-likelihood Tier 1 corpus scope)— corpus scale T1 trigger 預期不會 fire(Drive Project < 5,000 chunks ceiling);保留為 future Ricoh 全 corpus 擴展 trigger
4. **TC8 Custom LLM fine-tuning**(post-quality-signal)— W11+ eval-set augmentation 觀察 domain term 弱點;若 generic GPT-5.5 喺 Ricoh 產品術語顯著弱 → fine-tuning ROI 評估
5. **TC4 Multi-tenancy**(Q9 boundary preserved)— Tier 1 single-tenant Ricoh confirmed;**out of trigger window** until 第二個 organization signal

### 4.3 Decision-making sequence

W12 production launch retro 後:
- **Step 1**:本 review draft active flip(W12 retro 同步 Stakeholder + Chris approve)
- **Step 2**:Monthly Tier 2 capability evaluation cycle established(per Q12 owner Chris monthly governance review)
- **Step 3**:每滿足 trigger condition + ≥ 3 條 GraphRAG triggers(if applicable)→ ADR-NNNN Tier 2 capability kickoff(per CLAUDE.md §5.1 H1 + §6 ADR format)
- **Step 4**:Tier 2 implementation phase plan(separate from Tier 1 sprint cadence;rolling JIT continues)

---

## 5. Risks / Caveats

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| TR1 | Tier 2 trigger signal 模糊 → Stakeholder 推 ambitious capability without trigger fire | Medium | High | 本 review draft + monthly evaluation gate(§4.1)provides explicit signal-driven decision frame;CLAUDE.md §5.4 H4 Tier 1 boundary discipline preserved |
| TR2 | Beta cohort signal 量不足(small cohort < 250 users)→ Tier 2 trigger evaluation 缺 statistical power | Medium | Medium | W12 100% rollout(post-staged 25% → 50% → 100%)expands signal base;Q15 weekly signal report scaffold cumulative aggregation 補 small-cohort gap |
| TR3 | Q12 Tier 2 owner Chris 同 Tier 1 maintenance 工作 conflict | Low | Medium | post-W12 staffing trigger(beta-plan-v1.md §3 W9 secondary oncall add)+ Tier 2 implementation phase 屬 separate sprint cadence |

---

## 6. References

- `docs/architecture.md §11.1` Tier 2 Capabilities Backlog
- `docs/architecture.md §11.2` GraphRAG / KG Trigger Matrix
- `docs/architecture.md §11.3+` Tier 2 friendly architecture extensibility
- `docs/decision-form.md` Q12 Tier 2 owner(Chris;Resolved 2026-05-05)
- `docs/03-implementation/w11-staged-rollout-25-prep-deck.md §3 W11.F5`
- `docs/03-implementation/beta-plan-v1.md §3 W12` Tier 2 roadmap kickoff prep
- `backend/observability/weekly_signal_report.py`(W10 D2 F4.3 scaffold;feeds T2)
- `backend/eval/eval_set_augmentor.py`(W10 D1 F4.2 pipeline;feeds T3)
- `CLAUDE.md §5.4` H4 Tier boundary constraint
- `CLAUDE.md §6` ADR format(future Tier 2 kickoff trigger ADR-NNNN)

---

## 7. Update History

| Date | Change | Author |
|---|---|---|
| 2026-06-09(W11 D1)| Initial draft governance review | AI(F5.3 W11 plan deliverable per W11 prep deck §3 W11.F5)|
| _(pending)_ | Stakeholder + Chris W12 production launch retro approve | Chris + Stakeholder |
| _(pending)_ | Monthly Tier 2 evaluation gate cycle launch | Chris(Q12 owner) |

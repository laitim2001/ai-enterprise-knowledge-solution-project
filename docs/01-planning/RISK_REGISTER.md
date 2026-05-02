---
artifact: risk-register-living
version: 1.0
status: active
last_updated: 2026-05-02
spec_baseline: docs/architecture.md §8 (frozen v5)
catalog_anchor: docs/02-architecture/COMPONENT_CATALOG.md
---

# EKP Risk Register(Living)

> **Purpose**:living risk register。`docs/architecture.md §8` R1-R7 frozen baseline 喺 spec 內;本 file extends 嚟加 **component tag**(per CC-4 in COMPONENT_CATALOG.md)+ W1+ implementation 撞到嘅 **net-new risks**(R8+)+ **status evolution**(spec frozen 之後嘅活 mitigation log)。
>
> **Update authority**:任何 R1-R7 mitigation status update / 新 risk(R8+)入呢度。`architecture.md §8` 永遠不動,直到 v5 → v6 spec increment。

---

## 1. Risk Index(at-a-glance)

| ID | Risk | Source | Severity | Component(s) | Mitigation status |
|---|---|---|---|---|---|
| **R1** | Shadow AI displacement | §8.1 | 🔴 Critical | C09 + C10 | 🟡 Active(moat strategy + Beta measure) |
| **R2** | Ground truth labeling slips W4 | §8.1 | 🔴 Critical | C06 | 🟢 Resolved per Q14(Chris Lai self-assigned + LLM-judge fallback) |
| **R3** | Cohere via Azure Marketplace procurement delay | §8.2 | 🟠 High | C04 | 🟡 Active(W3 fallback = direct API + corp card) |
| **R4** | LLM hallucination on tables / structured content | §8.2 | 🟠 High | C05 + C01 | 🟡 Active(citation-required prompt + retrieval threshold + table-heavy eval queries) |
| **R5** | Azure OpenAI quota insufficient at peak | §8.2 | 🟠 High | C05 + C01 | ⚠️ Open(W1 同 MS account team pre-negotiate;quota TPM 為 Q4 outstanding minor)|
| **R6** | Cohere outage during demo / Beta | §8.3 | 🟡 Lower | C04 | 🟢 Hot fallback(Azure built-in semantic ranker)config flag ready |
| **R7** | Document source format edge case | §8.3 | 🟡 Lower | C01 | 🟡 Designed(parser fail-graceful + Admin Console flag)|
| **R8** ★ | **Ricoh corp proxy blocks PyPI large wheels** | W1 D1+D2 incident;D5 retest confirmed | 🟠 High | C12 (primary) + impacts C01 / C06 / C08 | 🔴 Open — D5 retest 2026-05-02 confirmed same `IncompleteRead(0 bytes read, 10911340 more expected)` pattern,no progress;pending P1(VPN/hotspot ops window)or P2(IT whitelist long-term)|
| **R9** ★ | **MCR DNS intercept on Docker image pull** | W1 D1 incident | 🟡 Medium | C12 | 🟢 Mitigated(Azurite npm fallback + docker.io direct path);long-term IT whitelist desirable |
| **R10** ★ | **Q2 sample manual delivery delay** | W1 D1 OQ partial | 🟠 High | C01 (primary) + C06 (chunk_id discovery) | 🟡 Active(W1 D4 partial unblock:6 docs arrived,F6/Q17/Q18 cleared;F8 Docling 仍 W2 D2 plan)|
| **R11** ★ | **Langfuse health endpoint degradation**(NEW)| W1 D5 closeout finding 2026-05-02 | 🟡 Medium pending triage | C07 + C12 | 🔴 Open(pending W2 D1 Chris triage)— container Up 2 days but `/api/public/health` connection-reset;`docker compose restart` + `up -d --force-recreate` hang。**Triage path**:reproduce → BUG-001 instance(候選 Sev3 minor degraded);若一次性 → close。**Lesson learned**:G3 daily morning health check 應 added to W2+ daily routine(non-end-of-phase only)|

★ = net-new from W1 implementation,not in `architecture.md §8`

---

## 2. Risks Inherited from `architecture.md §8`(R1-R7)

> 以下 entries 喺 spec frozen baseline 之上加 living mitigation tracking。Spec text 不重複,只記 status evolve。

### R1 — Shadow AI Displacement
| Field | Value |
|---|---|
| **Component(s)** | **C09** Admin Console UI + **C10** Chat Interface UI(adoption surface)|
| **Severity** | 🔴 Critical(High likelihood × High impact)|
| **Source** | `architecture.md §8.1` |
| **Original mitigation**(spec) | Moat = permissioned internal data + audit trail + Ricoh-specific context;Beta phase displacement measure;W9 pulse survey;onboarding 講清楚 differentiation |
| **Living status** | 🟡 Active — Beta phase metrics design 留 W6 demo deck 補。Pulse survey template TBD W8 |
| **Active actions** | (W1 暫無 active item;W6 demo prep 階段 surface)|
| **Decay date / review** | W6 demo + W9 Beta pulse survey |

### R2 — Ground Truth Labeling Slips W4
| Field | Value |
|---|---|
| **Component(s)** | **C06** Eval Framework |
| **Severity** | 🔴 Critical(Medium likelihood × High impact)|
| **Source** | `architecture.md §8.1` |
| **Original mitigation**(spec) | W1 D1 secure dedicated labeler;30 條 synthetic baseline W1 完成;LLM-judge first pass + human verify |
| **Living status** | 🟢 **Resolved structurally W1 D2** — Chris Lai 自身擔任 SME labeler(per OQ-Q14 full Resolution),fallback `LLM-judge first pass + Chris verify` 已對齊 spec |
| **Residual risk** | Chris bandwidth(multi-role)— 30 條 synthetic 仍要 W1-W4 spread,如撞 D-job 可能 slip |
| **Decay date / review** | W2 D5 Gate 1 prep 末 verify ground truth fill 進度 |

### R3 — Cohere via Azure Marketplace Procurement Delay
| Field | Value |
|---|---|
| **Component(s)** | **C04** Retrieval Engine |
| **Severity** | 🟠 High(Medium × Medium)|
| **Source** | `architecture.md §8.2` |
| **Original mitigation**(spec) | W1 Day 1 procurement initiate;fallback = direct API + corp card;W4 mini-shootout 後 production 走 Marketplace |
| **Living status** | 🟡 Active — Q5 Cohere procurement Path A vs B 仍 Open(`decision-form.md`)。W3 D1 latest fallback decision needed |
| **Active actions** | W2 末 confirm Q5 path resolution before W3 D1 |
| **Decay date / review** | W3 D1(Cohere wire,latest)|

### R4 — LLM Hallucination on Tables / Structured Content
| Field | Value |
|---|---|
| **Component(s)** | **C05** Generation Pipeline + **C01** Ingestion Pipeline(chunk strategy 影響 table 完整性)|
| **Severity** | 🟠 High(Medium × Medium)|
| **Source** | `architecture.md §8.2` |
| **Original mitigation**(spec) | Citation-required prompt(force quote chunk_id);retrieval-grounded refusal threshold;eval set 加入 5 條 table-heavy query |
| **Living status** | 🟡 Active — citation prompt 設計 W3 D1 落實;5 條 table-heavy query 將喺 W4 加入 eval set v1 |
| **Decay date / review** | W4 Gate 2(faithfulness metric 包 table query)|

### R5 — Azure OpenAI Quota Insufficient at Peak
| Field | Value |
|---|---|
| **Component(s)** | **C05** Generation + **C01** Ingestion(embedding API 同樣食 quota)|
| **Severity** | 🟠 High(Low likelihood × High impact)|
| **Source** | `architecture.md §8.2` |
| **Original mitigation**(spec) | Pre-negotiate Q3 quota with MS account team;application-side rate limit;multi-deployment region fallback |
| **Living status** | ⚠️ Open — quota TPM 屬 Q4 outstanding minor(per `decision-form.md` W1 D2 sync)。Application rate limit 待 W7+(C11 + C08 wiring)。Region fallback 暫無 secondary deployment |
| **Active actions** | W6 Beta prep 末 verify quota + design rate limit middleware skeleton |
| **Decay date / review** | W6 Beta plan;W7 Beta hardening |

### R6 — Cohere Outage During Demo / Beta
| Field | Value |
|---|---|
| **Component(s)** | **C04** Retrieval Engine |
| **Severity** | 🟡 Lower(Low × Medium)|
| **Source** | `architecture.md §8.3` |
| **Original mitigation**(spec) | Hot fallback Azure built-in semantic ranker;config flag 切換 |
| **Living status** | 🟢 Designed — Azure built-in semantic ranker 已喺 spec §3.2 列為 alternative;feature flag 設計 W3 D2 期間整合 |
| **Decay date / review** | W3 D2(reranker abstraction in C04)|

### R7 — Document Source Format Edge Case
| Field | Value |
|---|---|
| **Component(s)** | **C01** Ingestion Pipeline |
| **Severity** | 🟡 Lower(Medium × Low)|
| **Source** | `architecture.md §8.3` |
| **Original mitigation**(spec) | Parser fail-graceful + Admin Console 顯示 flagged doc;edge case E9-E11 already cover;manual fallback workflow W7+ |
| **Living status** | 🟡 Designed — parser implementation pending W2 D2 F8(Docling)。W2 D5 sanity check 5 sample 後 surface edge case 比例 |
| **Decay date / review** | W2 D5(F8 sanity report);W7 manual fallback design |

---

## 3. Net-New Risks from W1 Implementation Experience(R8+)

### R8 ★ — Ricoh Corp Proxy Blocks PyPI Large Wheels

| Field | Value |
|---|---|
| **Component(s)** | **C12** DevOps & Infra(primary)— impacts any pip install,直接 affect C01(Docling)/ C06(RAGAs)/ C08(test deps) |
| **Severity** | 🟠 High(Confirmed × Medium impact — every dev install blocked)|
| **First observed** | 2026-04-30(W1 D1)cp314 wheel(`pydantic-core` / `httptools`)→ 2026-05-01(W1 D2)cp312 wheel(`mypy 10.9MB` / `pyyaml` / etc)|
| **Pattern** | 任何 wheel >500KB 落 `IncompleteRead(0 bytes read)` connection broken |
| **Tested workarounds(failed)** | pip default index、`--retries 10 --timeout 120`、TUNA mirror `pypi.tuna.tsinghua.edu.cn`(503),全部斷流 |
| **Mitigation in place** | None resolved。F2 pytest verification + F7 unit tests deferred to post-pip-install window |
| **P1 short-term** | Chris VPN / mobile hotspot 5-10 min ops window,backend `.venv` 一次過 install 完整 deps |
| **P2 long-term** | Open Ricoh IT ticket whitelist `pypi.org` + `files.pythonhosted.org`(同 R9 MCR 一齊 escalate) |
| **Active blockers** | F2 pytest verification、F7 unit tests、未來任何 W2+ pip install(Docling、RAGAs、Cohere SDK、Voyage SDK)|
| **Decay date / review** | P1 完成即 close;P2 IT response timeline TBD |

### R9 ★ — MCR DNS Intercept on Docker Image Pull

| Field | Value |
|---|---|
| **Component(s)** | **C12** DevOps & Infra |
| **Severity** | 🟡 Medium(Confirmed × Low impact, mitigated)|
| **First observed** | 2026-04-30(W1 D1)`mcr.microsoft.com` resolves to `10.160.92.1`(internal proxy),Azurite Docker pull 撞 503 |
| **Mitigation in place** | 🟢 Azurite via npm distribution(non-Docker)+ docker.io direct path for Langfuse |
| **Long-term action** | IT whitelist `mcr.microsoft.com`(同 R8 一齊 IT escalate)or VPN |
| **Affected workflow** | 任何 future MCR-hosted image(e.g. Azure CA deploy 階段 W7+)|
| **Decay date / review** | W7 cloud deploy 之前必須 resolve(否則影響 production deploy pipeline)|

### R10 ★ — Q2 Sample Manual Delivery Delay

| Field | Value |
|---|---|
| **Component(s)** | **C01** Ingestion Pipeline(primary)+ **C06** Eval Framework(chunk_id discovery for ground truth fill)|
| **Severity** | 🟠 High(Medium × High — F8 + F11 entire blocked)|
| **First observed** | 2026-04-30(W1 D1 OQ-Q2 partial Resolved:path confirmed = direct upload, but specific delivery pending)|
| **Mitigation in place** | 🟡 W1 D4 partial unblock:6 .docx Drive Finance modules uploaded `docs/06-reference/01-sample-doc/`(AR/AP/FA/CB/GL/BM,~36MB total)— F6/Q17/Q18 cleared,890 images aggregate(868 PNG + 18 SVG + 4 EMF)|
| **Active blockers(remaining)** | F8 Docling .docx parser PoC(W2 D2 plan)+ F11 30 條 ground truth chunk_id replacement(W2 D3-D5 cascade after F1+F2+F5)|
| **Escalation** | ✅ Already arrived W1 D4(6 sample uploaded local) |
| **Backup plan** | (no longer needed — sample arrived)|
| **Decay date / review** | W2 D2(F8 start);F8 success → R10 close after sanity report on 6 sample |

---

### R11 ★ — Langfuse Health Endpoint Degradation(NEW W1 D5 Finding)

| Field | Value |
|---|---|
| **Component(s)** | **C07** Observability Stack(primary)+ **C12** DevOps & Infra(container)|
| **Severity** | 🟡 Medium pending triage(if confirmed Sev3 minor degraded → BUG-001 instance)|
| **First observed** | 2026-05-02(W1 D5 closeout pre-flight G3 verification)|
| **Symptom** | Container `ekp-langfuse` reports `Up 2 days (unhealthy)`,但 `curl http://localhost:3000/api/public/health` 連接 reset(exit code 56 `Recv failure: Connection was reset`)|
| **Last verified healthy** | W1 D2 EOD(per `09138d4` commit context;F4 acceptance criteria initial pass)|
| **Recovery attempts** | `docker restart ekp-langfuse`(silent hang)/ `docker compose restart langfuse`(silent hang)/ `docker compose up -d --force-recreate langfuse`(silent hang)— 3 attempts 全部 docker daemon 唔 respond,container 仲係 reports `Up 2 days` uptime |
| **Mitigation in place** | 🔴 None yet — recovery 嘗試全 hang。Postgres healthy + Azurite healthy unaffected,只係 Langfuse trace ingest 影響(POC 階段觀測性 degraded,not critical for W1 implementation work which 已 done) |
| **Triage path** | W2 D1 Chris morning triage:(a) reproduce + 確認 root cause → file BUG-001 instance(候選 Sev3 minor degraded:trace ingest down,non production user-facing);(b) 若一次性 → close R11,document recovery procedure in C07 design note。**Per PROCESS.md §1.4 R1.bugfix**:bugfix workflow 開 instance 必有 `report.md` + Chris confirm severity |
| **Lesson learned** | G3 health check 喺 phase end gate 屬 too late;W2+ daily morning quick health 3-services curl check 應加入 daily routine(non end-of-phase only)|
| **Decay date / review** | W2 D1 morning Chris triage(blocking — if unresolved,W2 implementation traces 將無 Langfuse capture)|

---

## 4. Risk Review Cadence(per `architecture.md §8.4`)

- **W1 D5**(2026-05-04):risk register review @ team retro,確認 Critical mitigation initiated + R8/R10 status update
- **W3 末**:mid-POC re-assessment(R2 / R3 / R8 critical)
- **W6 demo deck**:含 risk register update(stakeholder transparency)
- **Beta+ (W7+)**:每週 risk review,新 risk 加入呢個 register(R11+)

---

## 5. Maintenance Protocol

| Operation | How |
|---|---|
| **Add new risk** | Append `R{N+1}` entry in §3,update §1 Index table,bump frontmatter `last_updated` |
| **Status change**(mitigation evolve)| Edit relevant entry's `Living status` row + `Decay date`,bump frontmatter `last_updated` |
| **Spec-level new risk**(would belong to §8) | NOT possible during frozen v5。 Log here as `Rn>7`,surface to spec increment if v5 → v6 ever needed |
| **Resolve / close risk** | Mark `Living status` 🟢 + add `Closed YYYY-MM-DD` to entry;keep entry for audit trail |
| **Component re-tag** | Edit `Component(s)` field(if catalog evolution affects mapping)|

**Commit type**:`docs(risks): <change>`

---

**End of RISK_REGISTER.md v1.0**
**Effective**:from W1 D3(2026-05-01)
**Owner**:Chris(技術 Lead)

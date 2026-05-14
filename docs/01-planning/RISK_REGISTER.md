---
artifact: risk-register-living
version: 1.0
status: active
last_updated: 2026-06-10
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
| **R3** | Cohere via Azure Marketplace procurement delay | §8.2 | 🟠 High | C04 | 🟢 Resolved 2026-05-04(Q5 Path A Azure Marketplace;7-14d procurement parallel with W3 D1-D2 scaffold) |
| **R4** | LLM hallucination on tables / structured content | §8.2 | 🟠 High | C05 + C01 | 🟡 Active(citation-required prompt + retrieval threshold + table-heavy eval queries) |
| **R5** | Azure OpenAI quota insufficient at peak | §8.2 | 🟠 High | C05 + C01 | ⚠️ Open(W1 同 MS account team pre-negotiate;quota TPM 為 Q4 outstanding minor)|
| **R6** | Cohere outage during demo / Beta | §8.3 | 🟡 Lower | C04 | 🟢 Hot fallback(Azure built-in semantic ranker)config flag ready |
| **R7** | Document source format edge case | §8.3 | 🟡 Lower | C01 | 🟡 Designed(parser fail-graceful + Admin Console flag)|
| **R8** ★ | **Ricoh corp proxy blocks PyPI large wheels + cloud HTTPS SSL inspection** | W1 D1+D2 incident;D5 retest;2026-05-03 partial mitigation;**2026-05-04 permanent fix** | 🟠 High | C12 (primary) + impacts C01 / C06 / C08 | 🟢 **Mitigated 2026-05-04 via `truststore` package**(P2 permanent fix superseding P1 home network);Microsoft enterprise Python pattern,使 Python TLS 用 Windows Cert Store(corp root CA via GPO already trusted there)— Python SDK / urllib / httpx 全 cloud HTTPS work under VPN;P1 home network 仍 fallback if Windows Cert Store somehow misses CA |
| **R9** ★ | **MCR DNS intercept on Docker image pull** | W1 D1 incident | 🟡 Medium | C12 | 🟢 Mitigated(Azurite npm fallback + docker.io direct path);long-term IT whitelist desirable |
| **R10** ★ | **Q2 sample manual delivery delay** | W1 D1 OQ partial | 🟠 High | C01 (primary) + C06 (chunk_id discovery) | 🟡 Active(W1 D4 partial unblock:6 docs arrived,F6/Q17/Q18 cleared;F8 Docling 仍 W2 D2 plan)|
| **R11** ★ | **Langfuse health endpoint degradation**(NEW)| W1 D5 closeout finding 2026-05-02 | 🟡 Medium(triaged Sev3 → escalated BUG-001 instance) | C07 + C12 | 🟢 **Closed 2026-05-02**(BUG-001 Path B Docker Desktop GUI restart + clean compose up postgres+langfuse,Langfuse `/api/public/health` HTTP 200 verified sustained)。Mitigation:Path B recovery procedure documented in BUG-001 + W2 carry-over to C07/C12 design notes;daily morning health check ritual added W2+。BUG-001 closed same-day 2026-05-02 |
| **R12** ★ | **Azurite SDK signature mismatch**(NEW W2 D3) | W2 D3 F3 sanity testing 2026-05-05 | 🟡 Medium | C12 (primary) + C01 (impacts F3 screenshot upload local verification) | 🟡 Active — Azurite 3.35 (npm latest) + azure-storage-blob 12.20-12.28 SharedKey signature canonicalized-resource path mismatch(Azurite computes `/devstoreaccount1/devstoreaccount1/`,SDK signs with mismatched canonical resource → 403 AuthorizationFailure on all blob operations including get_account_information)。**Mitigation**:F3 implementation correct per architecture spec,unit-tested via mocks(9/9 pass);live verification deferred to W7+ cloud Azure Blob deploy(no emulator path);post-Gate 1 W3+ alternative = try Docker-pulled Azurite (different image) OR Azurite from Microsoft official GitHub master branch (newer than npm release)|
| **R13** ★ | **truststore depends on Ricoh corp root CA in Windows Cert Store** | W2 D5 cont 2026-05-04(R8 mitigation side-effect awareness)| 🟢 Low(operational accepted)| C12 (primary) | ⚫ **Accepted 2026-05-04** — `truststore.inject_into_ssl()` 信任 OS trust store 而非 `certifi`。**Dependency chain**:Ricoh IT GPO push corp root CA into Windows Cert Store → Windows updates trigger refresh → `truststore` 即生效。**Failure modes**:(a)Workstation 唔 join Ricoh AD domain → corp CA absent → cloud HTTPS fail(自帶 fallback:disconnect VPN go home network)。(b)Corp CA rotation by Ricoh IT 後 Windows GPO 未推送 → 短暫 fail until Windows update。(c)Linux / macOS dev workstation 唔有 GPO push → 需 manual install corp CA into OS trust store(W7+ cloud deploy worker uses managed identity,no proxy issue)。**Decay**:呢 risk 對 Tier 1 dev workstation 有效,Tier 2 production 用 Azure managed identity bypasses 全部 cert chain |
| **R14** ★ | **R-B1 Q11 Entra ID tenant operational delay**(NEW W6 D5 / W7 D5;**W8 D5 escalated;W9 D1 三方 outcome → de-escalated**;**W11 D2 cont 2026-06-10 critical-path reclassified — UI sprint pivot decoupling**)| W6 D5 stakeholder approval cycle decision-level Resolved 2026-05-05;W7 全程 a-revised mock auth dev mode decoupling;operational cascade trigger W8 D1;W8 D5 closeout escalation;**W9 D1 三方 alignment session outcome**:Option B-extended(IT 預期 early June 2026 real-calendar deliver)+ Pattern A confirmed + domain `ekp-beta.ricoh.com` confirmed;**W11 D2 cont 2026-06-10**:Track A IT cred event 2026-06-08 re-escalation deadline buffer expended without IT response;Personal Azure dev tier sidecar workaround pattern executed(Batch 5 backend live);UI quality gap surface → W12 production-launch pivoted to W12-W15 UI Tier 1 expansion sprint cycle → R-B1 closure timing **decoupled from W11 closeout** + **reclassified W16+ Beta cohort production deploy critical path** | 🟡 **Medium**(timeline 仍 IT-dependent;mock auth + personal Azure dev tier bridges interim;cohort production deploy reclassified to post-UI-sprint W16+)| C11(primary)+ C09 + C10(login flow UI)+ C12(infra deploy gating)| 🟡 **Active monitor with critical-path reclassified W11 D2 cont 2026-06-10**(原 W11 critical path → 現 W16+ Beta cohort production deploy critical path):**Trigger 唔再 W11 closeout block**(W11 closed early 2026-06-10 W11 D2 cont evening per stakeholder authorization;Phase Gate PARTIAL PASS landed)。Mitigation preserved + **expanded**:(a)W7 a-revised mock auth dev mode decoupling unchanged;(b)W11 D2 personal Azure dev tier sidecar pattern proves cross-tenant API key access viable + dev workflow unblocked even if IT cred slip continues;(c)W12-W15 UI sprint cycle 唔需要 Track A LIVE deploy(local dev workflow + personal Azure dev tier sidecar 已足夠)— UI quality polish 喺 cosmetic 唔受 Track A timing 影響;(d)Track A IT cred event 仍 stake 為 W16+ Beta cohort production deploy 必要前置條件(企業 SSO + audit + role assignment cascade)。**Re-escalation trigger**:若 real-calendar 2026-07-15 前仍未 IT deliver → 🟡 → 🔴 cycle re-engage Stakeholder + IT manager(2026-06-08 deadline 已 expended buffer 但 critical path 已 reclassified;新 deadline 預估 W15 closeout 末 == ~2026-07-04 前需要 IT cred ready 為 W16+ Beta cohort production deploy 啟動 prerequisite);具體 deadline 待 W15 closeout 時 W16+ phase plan 實際 timing 確認。**Decay**:R-B1 closes 🟢 when IT cred populated to Key Vault + F1.5+F1.7 LIVE smoke PASS + ACA/SWA apply complete(predicted ~project W16+ Beta cohort production deploy phase post UI sprint cycle complete)|

★ = net-new from W1+ implementation,not in `architecture.md §8`

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
| **Living status** | 🟢 **Resolved 2026-05-04**(Q5 → **Path A Azure Marketplace**)— Chris signoff W3 D1。Procurement 預期 7-14 工作日 turnaround,W3 D1-D2 scaffold(reranker Protocol + CohereReranker REST client + factory + tests)同 procurement 並行;wire-into-RetrievalEngine 等 Chris .env populate post Marketplace deployment ready。Path B(direct API + corp card)保留 fallback config-flag selector。 |
| **Active actions** | (1)Chris W3 D1 起 initiate Marketplace deployment;(2)AI W3 D1-D2 land scaffold + tests;(3)Chris populate `.env` Marketplace endpoint + key 後 → AI wire RetrievalEngine + live retrieval verification |
| **Decay date / review** | W3 D2-D3(Cohere wire complete + first live retrieval batch)。W4 reranker shootout 評估 Marketplace vs direct API ergonomics(non blocker for Tier 1) |

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

### R8 ★ — Ricoh Corp Proxy Blocks PyPI Large Wheels + Cloud HTTPS SSL Inspection(MITIGATED 2026-05-04 via truststore)

| Field | Value |
|---|---|
| **Component(s)** | **C12** DevOps & Infra(primary)— impacts any pip install,直接 affect C01(Docling)/ C06(RAGAs)/ C08(test deps) |
| **Severity** | 🟠 High(Confirmed × Medium impact — every dev install blocked)|
| **First observed** | 2026-04-30(W1 D1)cp314 wheel(`pydantic-core` / `httptools`)→ 2026-05-01(W1 D2)cp312 wheel(`mypy 10.9MB` / `pyyaml` / etc)|
| **Pattern** | 任何 wheel >500KB 落 `IncompleteRead(0 bytes read)` connection broken |
| **Tested workarounds(failed)** | pip default index、`--retries 10 --timeout 120`、TUNA mirror `pypi.tuna.tsinghua.edu.cn`(503),全部斷流 |
| **Root cause refined 2026-05-03** | 真 root cause **不是 corp proxy 本身**,而係 **corp VPN(GlobalProtect)tunnel SSL inspection layer** — disconnect VPN + 走 home network(HKBN ISP)直接 = R8 完全 disappear。Network diagnostics 確認:home network default gateway `192.168.50.1`、public IP `119.247.237.123`(HKBN consumer range)、mypy 10.9MB download @ 15.5 MB/s success first-try。**Hypothesis update**:corp VPN endpoint security做 stream-level interception(可能 CrowdStrike / Defender for Endpoint / Zscaler-style SSL re-encrypt)stream timeout limit 對 large wheel 嘅 chunked HTTP response 唔友好 |
| **Mitigation in place** | 🟢 **P2 truststore permanent fix(applied 2026-05-04 W2 D5 cont)** — `truststore` package + `truststore.inject_into_ssl()` at top of every cloud-touching entry point(`backend/api/server.py` + `scripts/run_populate_sanity.py` + `scripts/run_gate1_eval.py` + `scripts/run_embedder_smoke.py` + `scripts/discover_chunk_ids.py` + `scripts/create_index.py`)。Microsoft enterprise pattern:Python TLS 改用 Windows Cert Store(corp root CA already pushed via GPO)→ Azure HTTPS 全部 cert verify pass。VPN active 都 work。Per CLAUDE.md §5.2 H2 utility-lib 例外。**P1 home network 仍 fallback** if truststore somehow miss CA。Pip install large wheel under VPN仍未 retest — assumption 係 P2 同樣 unblock pip,因 root cause(SSL inspection)同;若 future install 仍 fail,P1 home network 仍 available |
| **Active blockers** | ✅ All cleared:Live populate(6 docs / 329 chunks) + Gate 1 verdict(R@5=0.9722) ran successfully under VPN with truststore 2026-05-04 |
| **P3 long-term(deferred)** | Open Ricoh IT ticket whitelist `pypi.org` + `files.pythonhosted.org`(同 R9 MCR 一齊 escalate)— pip layer 仍 needs upstream fix(see "P2 limitation" below) |
| **P2 truststore limitation(W2 D5 cont 後段 retest 2026-05-04)** | ❌ **truststore does NOT cover pip-install layer**:retest installed `pytest-cov` 222KB under VPN failed with same `IncompleteRead(0 bytes)` pattern as original R8。Root cause:**pip uses its own bundled `certifi` cert bundle**,independent of Python runtime `ssl` module that truststore patches。Cloud HTTPS(Azure / OpenAI SDK)under VPN ✅(truststore work);pip install under VPN ❌(P1 home network 仍係 唯一 path)。Future pip install 必須 disconnect VPN |
| **Side-effect findings** | (W1 D2 / 2026-05-03)(1)Pydantic v2.13.3 strict naming rule rejects `_<name>` body model parameters(W1 D1 stub pattern)→ 5 routes patched commit `c38710f`;(2)W1 D2 F7 KB CRUD impl 將 `/kb` 由 501 stub upgrade 做 200 in-memory backend → 8/8 smoke tests pass post-fix。(W2 D5 cont / 2026-05-04)(3)R13 NEW awareness — truststore depends on Windows Cert Store + Ricoh GPO corp CA push;Linux / macOS dev workstation requires manual CA install |
| **W6 D1 calibration update(2026-05-05)** | **Pre-flight probe ground truth refinement**:original W2 R8 mitigation conservatively used `curl probe HTTP 000 + CRYPT_E_NO_REVOCATION_CHECK` as VPN-disconnect trigger — **W6 D1 verified `curl schannel CRL revocation failure ≠ Python httpx failure`**。**Root cause**:curl on Windows uses **schannel TLS stack** which does strict CRL/OCSP revocation check by default;Python httpx uses **OpenSSL** which does NOT do strict CRL/OCSP check by default(even via truststore Windows cert store inject)。**Implication**:LIVE Python script work(C04 retrieval / C05 generation / C06 eval drivers)may proceed under VPN even when `curl` returns HTTP 000 — verified W6 D1 LIVE Azure 2-way RAGAs run + W6 D2 prompt tuning A/B + W6 D5 subset=20 confirmation 全部 successful through VPN active state。**SOP refinement**:future cloud-bound LIVE work pre-flight should use **Python httpx probe via project venv truststore stack** as ground truth(`backend/.venv/Scripts/python.exe -c "import truststore; truststore.inject_into_ssl(); import httpx; r = httpx.post(<target_url>, ...)"`);curl schannel probe alone unreliable for Python pipeline reachability。**Saved emotional cost**:eliminates false-positive STOP / VPN disconnect cascade when Python work would have proceeded fine。Added W7 carry-over for `RISK_REGISTER` entry update + future-contributor onboarding doc |
| **Decay date / review** | ✅ Mitigated 2026-05-04 via truststore;**W6 D1 SOP refinement landed 2026-05-05**(curl ≠ Python TLS stack semantics distinction);R13 corp-CA-dependency dimension tracked separately;P3 pip-install retest desirable W3 D1 |

### R9 ★ — MCR DNS Intercept on Docker Image Pull

| Field | Value |
|---|---|
| **Component(s)** | **C12** DevOps & Infra |
| **Severity** | 🟡 Medium(Confirmed × Low impact, mitigated)|
| **First observed** | 2026-04-30(W1 D1)`mcr.microsoft.com` resolves to `10.160.92.1`(internal proxy),Azurite Docker pull 撞 503 |
| **Recurrence log** | **2026-05-14**(post-W18 service-start)— `docker compose up -d azurite` 重撞:layer blob `1a142d512ad8` from `southeastasia.data.mcr.microsoft.com` `503 Service Unavailable` mid-stream × 2 consecutive attempts(同一 SAS URL,SAS expiry 未過,排除 token-expiry 原因)。Native npm fallback **re-verified effective** in the same session;cross-recorded as ADR-0017 occurrence #6 |
| **Mitigation in place** | 🟢 Azurite via npm distribution(non-Docker)+ docker.io direct path for Langfuse — re-verified 2026-05-14;`infrastructure/azurite-data/` 路徑與 docker volume mount 100% interchangeable;Backend `AZURE_BLOB_CONNECTION_STRING` 同 `.env` 設定唔需要改;`docker-compose.yml` Azurite service header + `docs/setup.md §8.1` 各有 Plan B pointer per ADR-0017 §"Plan B realised — Azurite via native npm" |
| **Long-term action** | IT whitelist `mcr.microsoft.com`(同 R8 一齊 IT escalate)or VPN |
| **Affected workflow** | 任何 future MCR-hosted image(e.g. Azure CA deploy 階段 W7+)|
| **Decay date / review** | W7 cloud deploy 之前必須 resolve(否則影響 production deploy pipeline);native npm fallback 對 local dev sufficient,production CI 階段 IT mirror / whitelist 仍 mandatory |

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

### R12 ★ — Azurite SDK Signature Mismatch(NEW W2 D3 Finding — Mitigated via Mock + Cloud Deferral)

| Field | Value |
|---|---|
| **Component(s)** | **C12** DevOps & Infra(primary)+ **C01** Ingestion Pipeline(impacts F3 local sanity verification only) |
| **Severity** | 🟡 Medium |
| **First observed** | 2026-05-05(W2 D3 F3 screenshot uploader sanity smoke testing) |
| **Symptom** | All `azure-storage-blob` operations against Azurite return 403 AuthorizationFailure(get_account_information / list_containers / upload_blob / get_blob_properties)。Tested SDK versions 12.20.0 / 12.24.1 / 12.28.0,Azurite 3.35.0(npm latest);`--skipApiVersionCheck` + `--loose` flags 都 ineffective;multiple x-ms-version 嘗試(2019-12-12 → 2025-07-05)全 fail |
| **Root cause confirmed** | Azurite debug log 顯示 SharedKey signature 計算嘅 canonicalized-resource path = `/devstoreaccount1/devstoreaccount1/`(account name 重複 prepended on URL path),vs SDK signs with `/devstoreaccount1/?...`(accord per current SharedKey signing spec)。HMAC-SHA256 mismatch causing 403。Even with absolute well-known Azurite default key + connection string format,signature differs |
| **Fix applied / planned** | (a)F3 unit tests use AsyncMock for BlobServiceClient(9/9 tests pass,validating code correctness);(b)Sanity script `scripts/run_screenshot_pipeline_sanity.py` deferred — write but skip live run for W2 baseline;(c)Real cloud Azure Blob has no canonicalized-resource bug — W7+ cloud deploy will provide live verification |
| **Mitigation in place** | 🟡 Active — F3 code-complete + mock-tested。Code does not need refactor since architecture per spec;Azurite emulator local-only blocker。Workaround for any local visual verification:Azure Storage Explorer or `az storage` CLI (untested per W2 baseline scope cap) |
| **Lesson learned** | (1)Azurite 3.35.0 npm distribution may have signature regression with newer SDK versions;(2)Local-emulator bugs ≠ production bugs — cloud deploy is verification layer(architecture.md §8 R5 W7+ already implies this);(3)For Tier 1 W2-W6 POC,F3 sanity gap acceptable risk since image storage 不影響 Gate 1 retrieval(R@5 ≥ 80% based on text + embedding only) |
| **Decay date / review** | W7+ cloud Azure Blob deploy first sanity test verify R12 disappears in production cloud;若 Tier 2 multi-tenancy 階段 local Azurite 仍要 reliable,trigger Azurite GitHub upstream PR or Docker image trial |

---

### R13 ★ — truststore Depends on Ricoh Corp Root CA in Windows Cert Store(NEW W2 D5 cont — ACCEPTED 2026-05-04)

| Field | Value |
|---|---|
| **Component(s)** | **C12** DevOps & Infra(primary,cross-cuts every cloud-touching entry point) |
| **Severity** | 🟢 Low(operational accepted)|
| **First observed** | 2026-05-04(W2 D5 cont — surfaced as side-effect of R8 mitigation P2 path)|
| **Mechanism** | `truststore.inject_into_ssl()` 改 Python TLS 用 OS trust store(Windows Cert Store)。**Dependency chain**:Ricoh IT GPO push corp root CA → Windows Cert Store contains corp CA → `truststore`(via Python ssl module)信 corp proxy 簽嘅 cert → cloud HTTPS verify pass。Browser / Office / Outlook 一直行同一條 chain |
| **Failure modes** | (a)Workstation 唔 join Ricoh AD domain → corp CA absent in Windows Cert Store → cloud HTTPS fail。Fallback:disconnect VPN,go home network direct;(b)Corp CA rotation by Ricoh IT before Windows GPO refresh → 短暫 fail until next Windows update sync;(c)Linux / macOS dev workstation 唔有 Windows GPO push → 需 manual install corp CA into OS trust store(Ubuntu `/etc/ssl/certs/`、macOS Keychain);(d)Container / Azure CA worker pod 唔 join domain → Azure managed identity bypasses cert chain entirely(Tier 2 production scenario,no truststore needed) |
| **Mitigation in place** | ⚫ Accepted — 文檔化 R13 awareness,non active mitigation。R8 自動 fallback path(home network)remains available as Plan B if truststore broken in any failure mode |
| **Lesson learned** | (1)Enterprise Python TLS 唔用 `certifi` bundle 是 well-known pattern(同 `pip-system-certs` 等 alternative 同類);(2)truststore 屬 utility-lib per CLAUDE.md §5.2 H2 例外,non vendor change non architectural change;(3)切勿 `verify=False` bypass — 即使 dev workstation 安全,commit 入 codebase leak to其他 dev / CI / Beta+ deploy(已 documented in W2 D5 cont decision section) |
| **Decay date / review** | W7+ cloud deploy 階段 — production worker pod 用 managed identity,truststore 仍對 dev workstation 有效但 production 不 affected。Tier 2 multi-tenancy / scale-out 階段如果加 Linux dev environment,trigger manual CA install procedure update |

---

### R11 ★ — Langfuse Health Endpoint Degradation(NEW W1 D5 Finding — CLOSED 2026-05-02)

| Field | Value |
|---|---|
| **Component(s)** | **C07** Observability Stack(primary)+ **C12** DevOps & Infra(container)|
| **Severity** | 🟡 Medium(triaged Sev3 → BUG-001 instance per PROCESS.md §4 Bug-fix workflow)|
| **First observed** | 2026-05-02(W1 D5 closeout pre-flight G3 verification)|
| **Symptom** | Container `ekp-langfuse` reports `Up 2 days (unhealthy)`,但 `curl http://localhost:3000/api/public/health` 連接 reset(exit code 56)|
| **Last verified healthy** | W1 D2 EOD(per `09138d4` commit context;F4 acceptance criteria initial pass)|
| **Root cause confirmed** | (a)Langfuse Node.js process 進入 zombie state(non-exit,Docker `restart: unless-stopped` policy 唔 trigger because zombie 唔 exit);(b)Daemon-to-zombie-container IPC channel completely corrupt — `docker rm -f` / `docker kill -s KILL` 全部 timeout infinite wait;(c)Previous failed force-recreate 留低 orphan container `935ba7f473df_ekp-langfuse`(Created state)stuck waiting for zombie removal → 雙 container deadlock |
| **Fix applied** | BUG-001 Path B(Docker Desktop GUI restart by Chris)+ `docker compose up -d postgres langfuse`(skip azurite due R9 MCR intercept)+ verify HTTP 200 sustained;Path A `docker rm -f`(orphan only)成功 but zombie removal 全 fail |
| **Mitigation in place** | 🟢 **Closed 2026-05-02**:Recovery procedure(Path B)documented in BUG-001 progress.md + W2 D1 morning carry-over to add subsection in C07 + C12 design notes troubleshooting。Daily morning health check ritual added to W2+ daily routine |
| **Lesson learned** | (1)G3 health check 屬 daily routine non end-of-phase only;(2)`restart: unless-stopped` 對 zombie process state 無效(Docker only triggers on exit);(3)Future similar zombie pattern → 立即 escalate Path B GUI restart,prevent wasted time on `docker rm -f` infinite hang;(4)`docker ps -a` 永遠係 daemon issue 第一個 query(catch orphan containers from failed force-recreate)|
| **Decay date / review** | ✅ Closed 2026-05-02(BUG-001 closed same-day);R8/R9/R11 corp infra ecosystem trio postmortem 計劃 W2 末 retro batch surface 共通 pattern |

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

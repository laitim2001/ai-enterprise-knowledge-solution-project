# EKP Production Launch Runbook(W9 D2 — W11-W12 milestone prep)

> Per architecture.md §7.4 Day-2 Readiness Checklist runbook spec + W9 plan §2 W11 production launch readiness scope。
> **Owner**:Chris(on-call lead)+ AI(initial draft per Karpathy §1.2 simplicity-first;Beta cohort 經驗 W9-W10 後 refine)
> **Status**:**Initial draft 2026-05-27 W9 D2**;refined post-Beta cohort signal W11-W12;mature post-production launch real-incident exercise W12+
> **Audience**:on-call rotation(Chris primary;TBD secondary post W9-W10 staffing)

## Purpose

EKP Beta 階段(W9-W12)+ production launch(W11-W12)期間,呢份 runbook 係 oncall **第一接觸文件**:遇到 incident 時 30 秒內知道:
1. **Symptom 對應邊個 scenario**(下文 5 sections)
2. **第一步 mitigation**(stop the bleeding)
3. **Root-cause investigation pointer**(Langfuse / structlog / Azure portal where to look)
4. **Rollback path**(if mitigation fails)

5 個 incident scenario 對應 architecture.md §7.4 Day-2 Readiness Checklist:
- [§1 Document parse failure](#1-document-parse-failure)
- [§2 API quota exhaustion](#2-api-quota-exhaustion)
- [§3 Index corruption](#3-index-corruption)
- [§4 Reranker outage](#4-reranker-outage)
- [§5 CRAG loop bug](#5-crag-loop-bug)

Cross-cutting:
- [§6 Rollback procedures](#6-rollback-procedures)
- [§7 Cred rotation emergency](#7-cred-rotation-emergency)
- [§8 Escalation matrix](#8-escalation-matrix)

---

## 1. Document parse failure

### Symptoms
- Admin Console KB management page:document upload status `failed` 或 `partial`
- Audit log:`audit_action="POST /kb/{kb_id}/documents"` + `status_code=502`
- Langfuse trace:`stage_failed` event for `parser.docx_parse` / `parser.pdf_parse` / `parser.pptx_parse`
- Specific docs surface error type:`PageBudgetExceededError` / `DoclingError` / `PptxNotSupportedFormat`

### First-line mitigation(stop the bleeding,< 5 min)
1. **Verify scope** — is this 1 doc OR all docs嘅 issue?
   - 1 doc → §1.A path(per-doc skip;don't escalate)
   - All docs 同時 fail → §1.B path(infrastructure fault;escalate)
2. **§1.A path**(single doc skip):
   - Mark doc `enabled=False` in Admin Console(via PATCH `/kb/{kb_id}/chunks/{chunk_id}`)
   - Document the doc_id + filename for offline re-process queue
     - **Note(W11 D1 AF1 clarification per W10 D5 tabletop substitute)**:no separate queue infrastructure exists in Tier 1。「Queue」 = (a) Slack `#ekp-beta` thread tag the doc_id + filename + (b) open `bugs/BUG-{NNN}-doc-parse-skip-{kebab}` instance per PROCESS.md §4 Bug-fix workflow。Tier 2 trigger:dedicated re-process queue infra if Beta signal shows recurring parse-skip pattern
   - Continue serving Beta cohort(其他 docs unaffected)
3. **§1.B path**(全 docs fail = infrastructure issue):
   - Check Azure Container Apps `/health` endpoint via `az containerapp exec`
   - If `/health` 都 fail → ACA replica issue → §6.1 rollback(swap to previous active revision)
   - If `/health` OK → Azure OpenAI / Docling network issue → §2 path

### Root cause investigation
- **Langfuse**:filter trace `stage=parser.*` `status=error` past 1h;cluster by error_type
- **structlog**:Azure Monitor Log Analytics KQL:`AppTraces | where Properties.stage startswith "parser"`
- **Common causes**:
  - **PDF scan + handwriting**(architecture.md §8.3 R7)— Docling table+text模式 fail;upgrade to OCR mode OR manual fallback workflow
  - **PPT 純動畫 / SmartArt**(R7)— python-pptx 唔處理動畫;flag in Admin Console
  - **Word 內嵌 SmartArt + equation**(R7)— Docling fallback to text-only
  - **File too large**(>50MB)— architecture.md §3.3 default;verify Settings + size check
  - **Encoding issues**(corrupted Unicode)— flag for re-export from source

### Rollback / recovery
- **Per-doc skip**:Admin Console disable chunk(non-destructive;data preserved for re-process)
- **Re-ingest after fix**:POST `/kb/{kb_id}/documents/{doc_id}/reindex` once root cause patched
- **Mass re-ingest**:if 大量 docs 受影響 → schedule batch re-ingest off-peak;monitor via `/observability/cost-summary`(re-embed cost ~$0.01 per 1k chunks)

### Spec ref
- architecture.md §3.3 layout-aware ingestion + §8.3 R7 format edge case
- error-cases-E1-E14.md §E9 / §E10 / §E11 parser failure modes

---

## 2. API quota exhaustion

### Symptoms
- Audit log:`audit_action="POST /query"` + `status_code=429` 或 `502` over 5-minute window > 5%
- Synthesizer log event:`error_type=RateLimitError` from `synthesizer_call`
- Cost dashboard alert:`api_error_rate` rule fires(architecture.md §7.4)
- Beta cohort users report "Service temporarily unavailable" / blank answers

### First-line mitigation(stop the bleeding,< 10 min)
1. **Identify which quota**(Azure OpenAI? Cohere? Azure AI Search?):
   - `RateLimitError` 由 `openai` SDK → Azure OpenAI quota
   - `429` from Cohere endpoint → Cohere Marketplace quota
   - `429` from `azure_search_*` → Azure AI Search S1 query quota
2. **Apply per-quota mitigation**:
   - **Azure OpenAI quota exhausted**:
     - Tier-1 immediate:reduce `synthesizer_call` rate by tightening `Settings.rate_limit_per_minute` from 50 → 25(application-side per-user limit;architecture.md §8.2 R5)+ **ACA revision restart required**(W11 D1 AF2 clarification:`Settings` env-var bound per W7 D2 F2 implementation;not hot-reload)
     - Tier-2 1-2 hour:Azure portal → Azure OpenAI resource → Quotas → request emergency quota increase(SLA varies)
     - Tier-3 fallback(W11 D1 AF3 rewrite per W10 D5 tabletop substitute):set **`OPENAI_API_KEY=''` env override + ACA revision restart** → synthesizer init fails gracefully in `lifespan` startup → `app.state.synthesizer` stays `None` → `query.py:79-92` retrieval-only fallback path active(W2 baseline preserved);application-state mutation not env-settable directly。**🔴 W11 D2 LIVE EXERCISE WARNING(2026-06-10)**:**AF3 mitigation as written DOES NOT work as documented**。Live exercise outcome:both `AZURE_OPENAI_API_KEY=''`(Option A,revision `--0000005`)→ 503 retrieval-engine-missing,AND `AZURE_OPENAI_DEPLOYMENT_LLM_PRIMARY=invalid-name`(Option B,revision `--0000007`)→ 502 synthesis-failure-DeploymentNotFound;**neither achieves documented retrieval-only fallback**。Root cause:`server.py:64` lifespan gate `if settings.azure_openai_api_key and settings.azure_search_admin_key:` wraps **BOTH** retrieval engine + synthesizer construction;synthesizer constructor itself 唔 validate deployment name(404 surface only at first /query call)。**Production AF3 reliability claim DOES NOT hold under current code**。**Operational impact**:if real production AOAI quota exhaustion + oncall follows AF3 → service goes 503/502 outage instead of degraded retrieval-only mode → WORSE outcome than runbook documents。**Fix required pre-Beta cohort cutover**:code change separating lifespan gates(retrieval engine only需`AZURE_SEARCH_ADMIN_KEY` + embedder;synthesizer construction wrapped in try/except → graceful fallback to `app.state.synthesizer = None` while retrieval engine survives)。**ADR-0013 candidate trigger** consolidated with Personal Azure dev tier pattern formalization;defer W11 D5 closeout retro per rolling-JIT R5。**Until code fix lands,oncall MUST NOT use AF3 path** — instead escalate to Tier-2 emergency quota increase OR §6.1 ACA revision swap to last-known-good
   - **Cohere quota exhausted**:
     - Immediate:`Settings.reranker_kind = "azure"` env override(switch to Azure built-in semantic ranker — architecture.md §3.2 R6 hot fallback)+ ACA revision restart
     - Recovery:Cohere Marketplace quota typically auto-refills 1h;contact account team if persistent
   - **Azure AI Search quota exhausted**:
     - Less common;S1 SKU has 1000 q/s baseline
     - Check Azure portal → AI Search resource → Metrics → Search QPS
     - Scale: S1 → S2(15-20 min provision)OR partition增加(15-30 min)

### Root cause investigation
- **Cost dashboard**(`/observability/cost-summary`):check `langfuse_status` — if `wired`,use Langfuse generations API to plot per-minute call rate
- **Azure portal**:OpenAI resource → Metrics → "Provisioned Tokens Per Minute"  / "Tokens Per Minute (Standard)"
- **Common causes**:
  - **Beta cohort burst**(unanticipated demand)— scale quota OR tighten per-user rate limit
  - **Runaway client**(eg. test script in loop)— audit log identify oid + revoke / contact user。**W11 D1 AF4 gap acknowledgment per W10 D5 tabletop substitute**:application-side per-user blocklist IS NOT IMPLEMENTED Tier 1(no `Settings.beta_user_blocklist` mechanism)。Practical revoke path = (a)Slack `#ekp-beta` tag user requesting they pause script(immediate)+ (b)Entra ID app role removal via IT helpdesk(5-10 min round-trip per Pattern A 8-step)。**Tier 2 trigger flag** if recurring runaway client signal — application-side per-user blocklist worth implementing
  - **CRAG loop bug**(§5)— grader 反覆 trigger correction;check `crag_trigger_rate` alert

### Rollback / recovery
- Per-quota mitigation steps above
- If full outage > 30 min → §6.1 ACA revision swap to last-known-good
- Post-incident:RCA in `docs/03-implementation/postmortems/INC-{YYYY-MM-DD}-quota-exhaust.md`

### Spec ref
- architecture.md §8.2 R5 Azure OpenAI quota insufficient + §8.1 R5 application rate limit
- components/C05-generation.md(synthesizer fallback)+ C04-retrieval.md(reranker fallback)

---

## 3. Index corruption

### Symptoms
- `/query` returns 200 OK but `retrieved_chunks` 不 relevant for known-good queries(eval-set v0 baseline regress)
- Hybrid search returns 0 chunks for queries that previously worked
- Azure AI Search portal:index document count mismatch vs Admin Console source-of-truth count
- Specific symptom:eval set R@5 drops > 20pp from W6 baseline 0.9722

### First-line mitigation(stop the bleeding,< 30 min)
1. **Verify corruption scope**:
   - Run `backend/eval/runner.py` against eval-set-v0(quick smoke vs baseline)
   - Compare Azure AI Search document count(via portal)vs Admin Console KB count
2. **Switch to backup index alias**(if alias swap configured per architecture.md §7.4 "Index alias 切換可 rollback"):
   - Currently `ekp-kb-drive-v1` is canonical;backup alias `ekp-kb-drive-v0` retains W2 baseline state
   - Update `Settings.azure_search_default_index = "ekp-kb-drive-v0"` env override → ACA revision restart
   - Beta cohort serves last-known-good corpus while investigation proceeds
3. **Stop ingestion**:Admin Console block new uploads to halt cascade(if corruption from bad ingest)

### Root cause investigation
- **Common causes**:
  - **Bad embeddings deployment**(eg. text-embedding-3-large model swap without re-index)— check Azure OpenAI resource for deployment changes
  - **Bad chunker change**(eg. PR landed without eval pass)— `git log` chunker module + correlate timing
  - **Azure AI Search service maintenance**(rare;Azure announces in advance)— check Azure status page
  - **Concurrent ingest race**(multiple uploads same KB)— check audit log for overlap
  - **Schema drift**(field added/removed without re-index)— compare `backend/indexing/schema.json` vs current index schema via portal

### Rollback / recovery
- **Index alias swap**(if configured)— immediate fallback
- **Re-ingest from source**:nuclear option — drop+recreate index;re-ingest all docs from Blob storage source-of-truth(per architecture.md §3.4 ingestion pipeline)
  - Cost:~$0.01 per 1k chunks(text-embedding-3-large)
  - Latency:~30 min for 2k-chunk corpus(W4 D1 baseline)
- **Restore from snapshot**:Azure AI Search 唔 support full snapshot/restore in S1 SKU;**Tier 2** for SKU upgrade

### Spec ref
- architecture.md §3.4 indexing service + §7.4 "Re-index SOP per KB" + Day-2 Readiness "Index alias 切換可 rollback"
- components/C03-indexing.md

---

## 4. Reranker outage

### Symptoms
- `synthesizer_call` log event:`reranked=False` despite `Settings.reranker_kind=cohere`
- Audit log:`status_code=502` for `/query` requests
- Cohere endpoint check:`curl -I {cohere_endpoint}` returns 5xx 或 timeout
- Cohere Marketplace status page indicator

### First-line mitigation(stop the bleeding,< 5 min)
1. **Hot fallback to Azure built-in semantic ranker**:
   - `Settings.reranker_kind = "azure"` env override → ACA revision restart(zero-downtime swap;~30s)
   - `azure_semantic_config_name` already populated `ekp-semantic-config`(W5 D1 verified)
   - Beta cohort experience:slight relevance regression(architecture.md §3.2 R6;W4 shootout faith Δ -11.76pp)but **service preserved**
2. **OR drop reranking entirely**(更激進):
   - `Settings.reranker_kind = "off"` → hybrid-only(W2 baseline behaviour preserved per architecture.md §3.4)
   - Larger relevance regression(W2 R@5=0.9722 baseline);use only if Azure semantic ranker also unavailable

### Root cause investigation
- **Cohere status page**:https://status.cohere.com(Marketplace 通常 mirror direct API status)
- **Marketplace metrics**:Azure portal → Cohere Marketplace endpoint → Metrics → Failure rate
- **Network path**:check ACA → Cohere endpoint via `az containerapp exec` curl
- **Common causes**:
  - **Cohere outage**(architecture.md §8.3 R6 — typical recovery < 1h)
  - **Marketplace billing issue**(unpaid invoice;check procurement;Tier-1 path vs Tier-2 escalation)
  - **API key rotation issue**(check Key Vault `cohere-api-key` secret value;regenerate if expired)
  - **Network egress block**(Ricoh corp proxy intermittent — R8 mitigation pattern;truststore should handle)

### Rollback / recovery
- Hot fallback to Azure semantic ranker(immediate)
- Once Cohere recovers:flip `Settings.reranker_kind = "cohere"` back via env;ACA revision restart
- **No data corruption** — reranker is **stateless** layer over hybrid;rollback truly zero-cost

### Spec ref
- architecture.md §8.3 R6 + §3.2 vendor table + §3.4 retrieval pipeline
- components/C04-retrieval.md(reranker fallback design)
- W4 reranker shootout postmortem in W4 retro

---

## 5. CRAG loop bug

### Symptoms
- Cost dashboard alert:`crag_trigger_rate > 50%` over 1-hour window(architecture.md §7.4)
- Latency p95 > 30s alert fires
- Audit log:`/query` `status_code=200` but `crag_iterations >= 1` 比例異常高
- User-facing:answers come back slow + sometimes incoherent(double-synthesis artifacts)

### First-line mitigation(stop the bleeding,< 10 min)
1. **Disable CRAG immediately**:
   - `Settings.crag_max_reformulations = 0` env override → ACA revision restart
   - All `/query` requests skip CRAG loop;return initial synthesis directly(query.py:110-125 already gates on `crag_loop is not None and payload.enable_crag`)
   - Beta cohort experience:slight relevance regression on borderline queries but **latency restored**
2. **OR raise CRAG threshold**(less aggressive):
   - `Settings.crag_confidence_threshold = 0.85`(was 0.70 per W5 D2 fine-tune)→ less triggering
   - Tradeoff:less correction triggered → fewer borderline-rescue benefits

### Root cause investigation
- **Langfuse generations**(post W9 D2 `observe_llm_async` upgrade):filter `stage=crag.refine` past 1h;histogram `triggered=True` ratio
- **Cost spike correlation**:CRAG L2 doubles synthesizer cost when triggered + adds GPT-5.4-mini grader cost;check `/observability/cost-summary` for daily spend deviation
- **Common causes**:
  - **Bad eval-set 引致 grader threshold drift**(W5 C1 carry-over)— grader trained on Q014 OOS pattern returning faith=0
  - **Real query distribution shift**(W9-W10 Beta cohort signal)— borderline queries 變多 → trigger rate 自然升
  - **GPT-5.4-mini deployment regression**(Microsoft model update without notice)— check Azure OpenAI deployment version
  - **REFUSAL_PHRASE detection bug**(W6 C6 carry-over)— grader scores refused answers as low confidence;cycle into infinite re-correction(though `max_corrections=1` limits)

### Rollback / recovery
- CRAG disable mitigation above
- Re-tune `crag_confidence_threshold` based on real query distribution(W9-W10 cohort signal)
- W5 D2 baseline value:0.70(empirical fine-tune via W5 plan F2)
- Long-term:per-KB threshold(Tier 2 STICKY column trigger if Beta signals diverge per OQ Q21)

### Spec ref
- architecture.md §3.5 CRAG L2 design + §7.4 alert spec
- components/C05-generation.md CRAG loop wiring
- W4 plan F1 CRAG L2 baseline + W5 plan F2 threshold fine-tune

---

## 6. Rollback procedures

### 6.1 ACA revision swap to last-known-good

ACA Bicep deploy creates immutable revisions;rollback = swap traffic to previous active revision。

```bash
# Manual swap via az CLI
az containerapp revision list \
  --name ekp-beta-backend \
  --resource-group ekp-beta-rg \
  --query "[?properties.active].{name:name, createdTime:properties.createdTime}" \
  -o table

# Identify previous LKG revision (older active timestamp)
# Then swap traffic 100% to LKG
az containerapp revision set-mode \
  --name ekp-beta-backend \
  --resource-group ekp-beta-rg \
  --mode multiple

az containerapp ingress traffic set \
  --name ekp-beta-backend \
  --resource-group ekp-beta-rg \
  --revision-weight <LKG-REVISION>=100 <CURRENT-REVISION>=0
```

GHA workflow `.github/workflows/backend-deploy.yml` 已 configured `workflow_dispatch + rollback=true` flag swaps traffic non-destructively。

**Time to recovery**:< 60s(traffic swap is instantaneous on Azure side;DNS unchanged;cred unchanged)。

### 6.2 Bicep deploy rollback

If ACA revision swap insufficient(eg. networking config bad):

```bash
# Re-deploy previous Bicep template version
git checkout <PREVIOUS-LKG-COMMIT>  # eg. last verified-working main
az deployment group create \
  --resource-group ekp-beta-rg \
  --template-file infrastructure/aca/backend.bicep \
  --parameters @infrastructure/aca/parameters.beta.json
```

**Caution**:Bicep deploy is **declarative replace**;may delete/recreate resources。Time:~5-10 min for ACA;~2 min for KV reference update。

### 6.3 SWA frontend rollback

SWA built-in revision management(per `frontend-deploy.yml`):

```
GHA repo → Actions → frontend-deploy.yml → Re-run with previous commit SHA
```

OR Azure portal:`Static Web App → Environments → Production → Source` 重設 to LKG commit。

### 6.4 DNS rollback

If `ekp-beta.ricoh.com` DNS issue:
- **CNAME revert**:Ricoh corp DNS team — change CNAME target back to W7 baseline(internal staging URL)or remove DNS entry temporarily
- **TTL caveat**:Ricoh corp DNS TTL typically 5min-1h;recovery time depends
- Local hosts override testing:add `127.0.0.1 ekp-beta.ricoh.com` to dev workstation `/etc/hosts` for emergency cohort access

### 6.5 Index alias rollback

Per §3 if `ekp-kb-drive-v1` corrupt:
- `Settings.azure_search_default_index = "ekp-kb-drive-v0"` env override → ACA revision restart
- (Requires `ekp-kb-drive-v0` backup alias maintained — confirm in W11 D1 deploy checklist)

---

## 7. Cred rotation emergency

### Scenario:secret leaked / Azure cred exposed

**Immediate steps(< 30 min)**:

1. **Revoke leaked cred**:
   - Azure OpenAI:Azure portal → resource → Keys and endpoint → Regenerate Key 1 (or Key 2 if 1 in use)
   - Cohere:Cohere portal → API keys → Revoke + regenerate
   - Azure AI Search admin key:Azure portal → resource → Keys → Regenerate primary
   - Entra ID client secret(Pattern B only):Azure portal → app reg → Certificates & secrets → Delete + new secret
2. **Update Key Vault**:
   ```bash
   az keyvault secret set \
     --vault-name ekp-beta-kv \
     --name azure-openai-api-key \
     --value <NEW-KEY>
   ```
3. **Restart ACA(picks up new secret reference)**:
   ```bash
   az containerapp revision restart \
     --name ekp-beta-backend \
     --resource-group ekp-beta-rg \
     --revision <CURRENT-REVISION>
   ```
4. **Verify**:`/health` 200 + sample `/query` 200(Beta-time only — avoid LLM spend before cohort hours)
5. **Post-incident**:
   - RCA:how was cred exposed?(commit log scrub / log file leak / unauthorized access)
   - Update `docs/03-implementation/postmortems/INC-{YYYY-MM-DD}-cred-leak.md`
   - Reset cohort access if user account compromised(Entra ID admin)

### Rotation cycle(non-emergency)
- Per `infrastructure/keyvault/README.md` rotation SOP:6-month cycle for Cohere + Entra ID client secret;Azure OpenAI keys rotated annually
- Document rotation date in Key Vault secret `expires_on` field

---

## 8. Escalation matrix

| Severity | Symptoms | First responder | Escalate to | SLA |
|---|---|---|---|---|
| **P1 critical** | Full service outage(Beta cohort cannot login OR /query 0% success rate)| Chris(oncall lead) | IT manager(if Entra ID)+ Azure account team(if quota / cred)| Page within 15 min |
| **P2 warning** | Partial degradation(latency p95 > 30s OR error rate > 5% OR reranker outage)| Chris(oncall) | Cohere account team(if reranker)| Respond within 1h |
| **P3 info** | Slow drift signal(cost spike > 1.5x avg OR CRAG trigger > 50%) | Chris(daily review)| - | Best-effort within 1 day |

**Beta phase note**:on-call rotation 仍 single-person(Chris)— W11+ post-cohort onboarding 加 secondary oncall(per beta-plan-v1.md §3 W9 staffing trigger)。

**Communication channels**:
- Beta cohort:Slack `#ekp-beta`(W9 onboarding cycle setup)
- IT escalation:Ricoh corp IT helpdesk + dedicated Entra ID admin contact(established W9 D1 三方 session)
- External vendors:Cohere account team email + Azure account team(MS sales contact)

---

## 9. Reference quick-links

| Topic | Path |
|---|---|
| Architecture spec | `docs/architecture.md` §3 RAG core + §7.4 Day-2 Readiness + §8 Risk Register |
| ACA deploy | `infrastructure/aca/README.md` + `backend.bicep` + `networking.bicep` |
| Key Vault SOP | `infrastructure/keyvault/README.md`(6 secrets + rotation) |
| Entra ID app registration | `infrastructure/entra-id/README.md`(Pattern A 8-step) |
| SWA custom domain | `infrastructure/swa/README.md`(DNS + apex caveat) |
| Observability | `infrastructure/observability/README.md`(Langfuse SDK + cost dashboard + alerts) |
| Risk register | `docs/01-planning/RISK_REGISTER.md`(R8 truststore + R12 Azurite + R14 R-B1 + R5 quota) |
| OQ status | `docs/decision-form.md`(Q11 operational + Q21 reranker + Q5 Cohere procurement) |

---

## 10. Update history

| Date | Change | Reason |
|---|---|---|
| 2026-05-27(W9 D2)| Initial draft | architecture.md §7.4 Day-2 Readiness Checklist runbook spec + W9 plan §2 W11 production launch readiness scope;Karpathy §1.2 simplicity-first single-file 5-scenario coverage |
| 2026-06-09(W11 D1)| AF1-AF4 in-place edits per W10 D5 tabletop substitute aggregate findings | F4.1-F4.4 — AF1 §1.A step 2 queue clarification(no separate queue infra Tier 1)+ AF2 §2 tier-1 ACA revision restart note + AF3 §2 tier-3 `OPENAI_API_KEY=''` rewrite + AF4 §2 runaway client per-user revoke gap acknowledged + Tier 2 trigger flag。Live exercise post-Track A LIVE deploy 將 replace W10 D5 tabletop substitute within 72h(F4.5 W11 plan deliverable) |
| 2026-06-10(W11 D2)| **F4.5 Live exercise executed against personal Azure dev tier ACA env** — replaces W10 D5 tabletop substitute(per W11 plan §F4.2 acceptance:within 72h post-LIVE-deploy;personal Azure dev tier 作為 Track A IT cred blockade workaround pattern unblocked exercise prerequisite)| **F4.5 outcome** — AI solo walkthrough §1 + §2 against personal ACA env(`ekp-dev-backend--0000003-0000006` revision sequence)。**Verified LIVE**:**AF2 ACA revision restart mechanism**(`RATE_LIMIT_PER_MINUTE=25` env override → revision `--0000004` Activating 36s → RunningAtMaxScale 103s,~1.7 min total restart cycle)+ §1 `/health` via `az containerapp exec`(WebSocket through `management.azure.com`,R8 corp proxy bypass viable)。**Narrative-walked + drift findings**:**🔴 AF3 critical mechanism drift** — runbook 寫「synthesizer init fails gracefully → query.py:79-92 retrieval-only fallback path active」but actual mechanism `server.py:64` lifespan gate `if settings.azure_openai_api_key and settings.azure_search_admin_key:` wraps **BOTH retrieval engine AND synthesizer**;removing `AZURE_OPENAI_API_KEY` env var → BOTH `app.state.retrieval_engine = None` AND `app.state.synthesizer = None` → `/query` returns `503 pipeline.synthesis_failed` "RetrievalEngine not initialized"(`query.py:_engine_or_503` line 39-49 fires BEFORE synthesizer fallback path)→ **AF3 mitigation as written DOES NOT achieve retrieval-only degraded mode**。**Operational impact**:if real production AOAI quota exhaustion oncall follows AF3 → service goes to 503 outage instead of degraded retrieval-only(WORSE than expected outcome)。**Action required**:either(a)code fix separating lifespan gates so OPENAI_API_KEY removal only affects synthesizer construction(not retrieval engine),or(b)runbook AF3 rewrite to use alternative trigger mechanism(e.g.,`AZURE_OPENAI_DEPLOYMENT_LLM_PRIMARY=invalid-deployment-name` so synthesizer construction throws but retrieval engine OK — needs LIVE verify)。**AF1 + AF4 narrative-walked**:NIL drift — text consistent with current Tier 1 implementation gaps(Slack `#ekp-beta` channel cascade等 Beta cohort onboarding;Entra ID role removal等 Track A LIVE switch)。**Drift finding 2**:`az containerapp logs show` blocked by R8 corp proxy(`eastus2.azurecontainerapps.dev` data plane)— alternative = Log Analytics REST API via httpx truststore-mitigated(W11 D2 morning batch proven path);應 add 至 §2 Root cause investigation steps as fallback。**Drift finding 3 minor**:AF3 verbiage 寫「synthesizer init fails gracefully」technically inaccurate — actual mechanism 係 lifespan gate skip(net outcome 同樣 synthesizer = None,但 verbiage 可微調更精確 e.g.「lifespan gate skips synthesizer construction」)。**Carry-overs**:(1) **W11 D5 retro Carry-overs** — AF3 mitigation rewrite OR code fix(P2 governance,impact production AF3 reliability);(2) **架構 H1 boundary check** — code fix(separating lifespan gates)= H1 architectural-adjacent,需 ADR-0013 candidate trigger 收入(per CLAUDE.md §6 + R5);(3) **§2 Root cause investigation 加 LA REST API fallback note** — minor doc enhancement,defer Beta cohort onboarding cascade window。Live exercise commit reference:`20f7f56`(W11 D2 F4.5 outcome + AF3 critical drift surfaced)|
| 2026-06-10(W11 D2 cont)| **F4.5 C2 AF3 Option B verify** — invalid LLM deployment name trigger LIVE test | **Option B verified NOT viable** — `AZURE_OPENAI_DEPLOYMENT_LLM_PRIMARY=invalid-deployment-name-z9z9` env override(revision `--0000007` Activating 36s → RunningAtMaxScale 92s)→ POST /query returned **502 `pipeline.retrieval_failed`** "synthesis failure: NotFoundError: 404 DeploymentNotFound"。Mechanism analysis:lifespan gate passes(both API keys still valid)→ synthesizer constructor + `__aenter__()` 唔 validate deployment name(只係 store string + setup HTTP client)→ first /query call surfaces 404 → `query.py:113-117` catches exception → wraps as 502 synthesis failure。**Net outcome**:both Option A + Option B FAIL to achieve documented retrieval-only fallback;`query.py:96-109` synthesizer-is-None fallback ONLY fires if lifespan gate fails,but that gate ALSO disables retrieval engine causing 503。**Verdict**:**no env-var-only path to AF3 documented retrieval-only fallback**;code fix required(separate lifespan gates OR try/except wrap synthesizer construction)。**W11 D5 retro decision narrowed**:no need to argue Option A vs Option B — Option A code fix is唯一 viable path;ADR-0013 candidate trigger firmly anchored on splitting lifespan gates pattern。Restore commit reference: AZURE_OPENAI_DEPLOYMENT_LLM_PRIMARY=gpt-5.5 (revision `--0000008` healthy + /query 200 verified) + §2 AF3 W11 D2 LIVE EXERCISE WARNING callout added。Commit reference:`4e390e6`(W11 D2 F4.5 C2 AF3 Option B verified NOT viable) |

**Lifecycle reminder**:呢份 runbook 喺 Beta 階段(W9-W12)+ production launch 後會持續 evolve。每個 real incident 結束 → postmortem in `docs/03-implementation/postmortems/INC-{YYYY-MM-DD}-*.md` + 對應 section update here。**新 scenario 必須先入 architecture.md §7 acceptance section 確認 spec coverage,再加 runbook entry**(per CLAUDE.md §5.1 H1 boundary check)。

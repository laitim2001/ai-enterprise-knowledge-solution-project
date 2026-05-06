---
phase: W08-beta-deploy-sprint2
plan_ref: ./plan.md
status: active
last_updated: 2026-05-19
---

# Phase W08 — Checklist

> Atomic checkbox(每 item ≤ 0.5–2 hour effort per W6 C10 calibration:LIVE deploy days × 2;static days × 0.5)。
> Status:`draft` 自 2026-05-16 W7 D5 closeout cascade。
> 全 unchecked 至 W8 D1 implementation start。

## F1 — Real Entra ID auth integration LIVE switch(C11)

- [ ] **CRITICAL Q11 IT** F1.1 W8 D1 IT engagement:Chris confirm Tenant Access + App Registration + Owner Identification(Ricoh 統一 tenant)— W7 a-revised mock auth fallback preserved if IT slips
- [ ] F1.2 W8 D2-D3 backend `msal` Python SDK install + `python-jose` JWT verification(JWKS fetch + signature + audience/issuer + expiry);新 dep ask-and-approve cycle
- [ ] F1.3 W8 D2-D3 frontend `@azure/msal-react` install + PublicClientApplication + MsalProvider + redirect flow on `frontend/lib/auth/msal_provider.ts`
- [ ] F1.4 W8 D4 LIVE switch:`Settings.feature_auth_mock=False` + `NEXT_PUBLIC_AUTH_MOCK=false`;real Entra ID redirect flow exercise
- [ ] F1.5 W8 D4 F1.7 LIVE smoke(W7 carry-over):dev tenant Entra ID end-to-end login flow on local dev server
- [ ] F1.6 W8 D4 unit tests:JWKS mock + valid signed JWT 200 + expired 401 + audience mismatch 401 + issuer mismatch 401
- [ ] AZURE_TENANT_ID + AZURE_CLIENT_ID + AZURE_CLIENT_SECRET 從 .env 移到 Azure Key Vault;Settings reads via Managed Identity

## F2 — Azure Container Apps deploy backend(C12)

- [x] F2.1 Dockerfile finalize backend — **W8 D1 done 2026-05-19** — `backend/Dockerfile` multi-stage(builder uv venv + runtime slim)+ non-root user `ekp` UID 10001 + HEALTHCHECK `/health` interval=30s start-period=15s;`.dockerignore` H5 enforcement(`.env*` + `*.pem` / `*.key` / `*.pfx` ignored;`.env.example` whitelisted)
- [x] F2.2 Azure Container Apps spec — **W8 D1 done 2026-05-19** — `infrastructure/aca/backend.bicep` declarative spec:internal ingress + 1 vCPU/2GB + autoscale 1-5 HTTP concurrency target 30(§8.1 R5)+ User-assigned Managed Identity + 6 Key Vault secret references + Liveness + Readiness probes;`infrastructure/aca/README.md` pre-requisite list + manual deploy reference
- [ ] F2.3 GHA CI/CD pipeline:test → ruff → docker build → ACR push → ACA deploy revision → smoke;rollback via revision swap
- [ ] F2.4 Azure Key Vault secrets management(全 keys 移到 Key Vault;Settings via Managed Identity)
- [ ] F2.5 ACA networking:internal ingress with Private Endpoint to Azure AI Search;public ingress for `/health` + auth endpoints

## F3 — Azure Static Web Apps deploy frontend(C12)

- [ ] F3.1 SWA build pipeline GHA workflow:`next build` → SWA deploy(staging slot)+ env vars wire
- [ ] F3.2 Custom domain DNS(`ekp.ricoh.com` 或 staging subdomain — owner confirm W8 D1)
- [ ] F3.3 Auth integration sync:msal-react redirect URI + post-logout URI register in Entra ID app registration(blocked on F1.1)
- [ ] F3.4 SPA route fallback(`staticwebapp.config.json`)for Next.js App Router

## F4 — LIVE smoke cascade(W7 carry-overs)

- [ ] F4.1 F3.5 LIVE smoke(W7 carry-over):5 query through dev server → Langfuse trace 顯示 audit tags + request_id traceable
- [ ] F4.2 F4.5 LIVE smoke(W7 carry-over):trigger E1 + E5 + E12 → verify graceful UX
- [ ] F4.3 W4/W5 LIVE smoke remainder(W6 C3):PPT E2E + GPT-5.5 latency baseline + Chat UI screenshots
- [ ] F4.4 Documents/chunks/eval/screenshots/debug routes auth wire(W7 D2 字面 scope 之外)cascade per beta-plan-v1.md §2 W8.F1

## F5 — Cost monitoring + user feedback dashboard(C07)

- [ ] F5.1 Real Langfuse SDK wire(replace `langfuse_tracer.py:4` W1 stub with actual SDK init + flush hooks)
- [ ] F5.2 Cost dashboard build:Azure OpenAI + Cohere + Blob + AI Search daily spend(architecture.md §7.4 alert spec)
- [ ] F5.3 User feedback loop wire:`/feedback` endpoint → Langfuse comment field;Admin Console feedback view
- [ ] F5.4 Alerts:p95 latency > 30s + API error > 5% + cost spike + CRAG trigger rate > 50%

## F6 — Phase Gate closeout + W8 retro + W9 kickoff prep

- [ ] F6.1 W8 phase Gate verdict landed
- [ ] F6.2 W08 progress.md retro 7 sections complete
- [ ] F6.3 W09 phase folder kickoff:`docs/01-planning/W09-beta-internal-testing/{plan,checklist,progress}.md` draft
- [ ] F6.4 W08 progress.md frontmatter status flipped to `closed`
- [ ] F6.5 R-B1 risk status update(Entra ID delay → mitigated or active per F1 outcome)
- [ ] F6.6 OQ Q11 final operational Resolved sync to `decision-form.md`

---

## Cross-Cutting

- [ ] Each commit references `progress.md` Day-N entry(R2)
- [ ] Component tag in commit message per CC-1
- [ ] OQ status sync to `decision-form.md`(R4)— Q11 W8 D1 critical
- [ ] Risk register update if R-B1(Entra ID delay)status changes
- [ ] CLAUDE.md §5.5 H5 security check:no secret commit;Cohere/Azure key 移到 Azure Key Vault;Entra ID client secret 走 Key Vault(Beta+)
- [ ] H2 vendor lock check:msal SDK 屬 Tier 1 vendor scope per architecture.md §3.2 — direct approve 預期(non-architectural addition);若 friction surface ADR-0013 candidate

---

**Lifecycle reminder**:呢份 checklist 衍生自 `plan.md` deliverables。新加 deliverable 必須先入 plan + changelog,然後再加 checklist item。

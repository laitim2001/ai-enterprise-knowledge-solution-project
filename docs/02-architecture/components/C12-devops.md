---
component: C12
name: DevOps & Infra
catalog_ref: ../COMPONENT_CATALOG.md#c12--devops--infra
spec_refs: [architecture.md §4.3, architecture.md §9, docs/setup.md]
status: v1-active
last_updated: 2026-05-01
---

# C12 — DevOps & Infra Design Note

> **Status**:`v1-active` — W1 local stack 已 implemented(Postgres + Langfuse + Azurite via npm fallback)。W7+ cloud deploy + CI/CD 仍 forward-looking。
>
> **Owner**:AI(scripts)+ Chris(Azure tenant + corp IT escalation)

---

## 1. Internal Architecture

C12 spans **3 layers** depending on phase:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 — CI/CD Pipeline(W7+,not yet built)            │
│  GitHub Actions:test → build → push image → deploy       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  LAYER 2 — Cloud Deploy(W7+,not yet built)              │
│  Azure Container Apps + Bicep IaC + Azure Container       │
│  Registry + Azure Key Vault(secrets W7+)                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│  LAYER 1 — Local Dev Stack(W1 ✅ implemented)             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ docker-compose.yml                                   │   │
│  │ ├─ postgres:16-alpine(internal port 5432)          │   │
│  │ └─ langfuse/langfuse:2(port 3000)                  │   │
│  │                                                      │   │
│  │ azurite(npm-installed,non-Docker fallback per R9)  │   │
│  │ └─ Blob/Queue/Table on 10000-10002                  │   │
│  │                                                      │   │
│  │ backend/.venv(Python 3.12.10 per W1 D2 R5 fix)    │   │
│  │ frontend/node_modules(pnpm 376 packages)           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**File layout**:
```
infrastructure/
├── docker-compose.yml          ← Postgres + Langfuse
├── azurite-data/               ← npm Azurite local data(gitignored)
├── postgres-data/              ← Postgres volume(gitignored)
├── langfuse-uploads/           ← Langfuse upload cache(gitignored)
└── (Bicep templates W7+)

backend/Dockerfile              ← FastAPI prod image(W7+ used by Azure CA)
backend/.dockerignore
backend/.venv-py314-backup/     ← Old venv kept for rollback
backend/.venv/                  ← Active venv (Python 3.12.10)

frontend/Dockerfile             ← Next.js prod image(W7+)
frontend/.dockerignore

.env / .env.example             ← Secrets + config (root level)
```

---

## 2. Key Interfaces

### Inputs
- `infrastructure/docker-compose.yml` — service definitions
- `.env` — secrets + config(consumed by Postgres / Langfuse / backend / frontend)
- `backend/pyproject.toml` — Python deps spec
- `frontend/package.json` — Node deps spec
- (W7+) `infrastructure/bicep/*.bicep` — IaC templates
- (W7+) `.github/workflows/*.yml` — CI/CD pipeline

### Outputs
- Running services on local ports(Postgres 5432 internal,Langfuse 3000,Azurite 10000-10002,FastAPI 8000,Next.js 3000 dev)
- (W7+) Azure Container Apps deployment URL
- (W7+) GitHub Actions run results(pass/fail per PR)

### Side effects
- Local: Docker daemon write to `infrastructure/postgres-data/` + `langfuse-uploads/`,Azurite write to `infrastructure/azurite-data/`
- (W7+) Cloud: Azure resource provisioning(CA / ACR / Key Vault),GitHub Actions runner spin

---

## 3. Critical Design Decisions

| Decision | Rationale |
|---|---|
| **docker-compose.yml 用 langfuse:2 tag(非 2-latest)** | `2-latest` 已停 publish(W1 D1 撞 → fix commit `f7ba973`)。Pin major version,minor 自動 update |
| **Azurite via npm fallback,非 Docker image** | Ricoh corp DNS 攔截 `mcr.microsoft.com`(R9)。`npm install -g azurite` 用 `registry.npmjs.org` 不撞攔截。Azure SDK API 100% 兼容 |
| **Postgres 用 named volume,Langfuse uploads 用 bind mount** | Postgres 做 persistent state 用 named volume 方便 backup;Langfuse uploads 用 bind mount 易 inspect |
| **Backend `.venv` 用 Python 3.12 而非 3.14**(W1 D2 R5 fix)| Python 3.14 cp314 wheel ecosystem 未成熟(pydantic-core / httptools / ML deps lag)。3.12 LTS,wheel supply 完備。詳見 RISK_REGISTER R8 |
| **W7+ Bicep over Terraform** | Azure-native,MS support,Ricoh enterprise alignment。Tradeoff:vendor lock-in(but Tier 1 already locked H2)|
| **W7+ Azure Container Apps over AKS** | App scale needs ≤ ~50 RPS POC + ~500 RPS Beta;CA serverless model 比 AKS 簡單 80%,cost 低 50%。Tier 2 multi-tenancy may revisit |
| **Secrets:.env(POC)→ Azure Key Vault(Beta+)** | Per CLAUDE.md §5.5 H5;Beta+ 自動切 |

---

## 4. Edge Cases & Error Handling

| Edge case | Mitigation |
|---|---|
| **Docker Desktop 唔 start**(W1 D1 撞)| docker-compose 命令 fail-graceful;suggest user `Start-Service docker` Windows 或 manual start。`README.md` setup section document |
| **Corp proxy block MCR**(R9 Confirmed)| Workaround in place:Azurite npm + docker.io direct path for Langfuse;long-term IT whitelist desirable W7 之前 |
| **Corp proxy block PyPI 大檔**(R8 Confirmed)| Workaround pending P1(VPN/hotspot)or P2(IT whitelist)。Active blocker for any pip install |
| **Port conflict**(5432 / 3000 / 10000)| docker-compose port mapping configurable via `.env`;document in setup.md |
| **`.env` missing on first clone** | Pydantic Settings 提供 default,但 secrets empty → 501 at use site(per `backend/storage/settings.py`)。`.env.example` 喺 root,提示 cp 手動 |
| **Azurite data corruption**(rare)| Stop + `rm -rf infrastructure/azurite-data/` + restart Azurite |
| (W7+) **Azure quota exhausted on deploy** | Bicep deployment fail at provision step → CI/CD `azure/login` action surface + Slack alert |

---

## 5. Performance Characteristics

| Metric | W1 Local | W7+ Cloud target |
|---|---|---|
| Stack startup time | ~30s(Postgres + Langfuse + Azurite cold start)| ~3 min cold(Azure CA scale-from-zero)|
| Postgres write throughput | ~1000 TPS local SSD | ~5000 TPS Azure Premium SSD |
| Langfuse trace ingest | ~100 traces/sec | ~10,000 traces/sec(cluster mode Tier 2)|
| Azurite Blob throughput | ~100 MB/s local SSD | N/A(switched to real Azure Blob in cloud)|
| FastAPI cold start | ~2s | ~5s Azure CA scale-from-zero |
| Memory(local stack)| Postgres ~80MB,Langfuse ~200MB,Azurite ~50MB,FastAPI ~150MB | Per-container limits set in CA config |

---

## 6. Test Strategy

| Layer | Test type | When |
|---|---|---|
| Local stack health | `docker compose ps` + `curl http://localhost:3000/api/public/health` | W1 D1 manual ✅;W2+ smoke test script |
| Backend / frontend smoke | `python -m compileall` + ruff + pnpm lint + type-check | W1 D1 ✅(post-pip-install:pytest 8 smoke tests F2 deferred)|
| (W7+) deployment smoke | GitHub Actions workflow runs `curl /health` post-deploy | W7+ |
| (W7+) infra integration | Bicep what-if + deploy to staging slot | W7+ |

**No mocks for infra layer**(per CLAUDE.md feedback memory if applicable)— always test against real local stack。

---

## 7. Future Evolution / Tier 2 Hooks

| Tier 2 feature | C12 evolution |
|---|---|
| **Multi-region deploy**(HA) | Bicep template 加 secondary region;Azure Front Door for traffic split |
| **Multi-tenancy** | Azure CA scale rule per tenant;separate ACR repo per tenant; Key Vault per-tenant secrets segregation |
| **Auto-sync from external source** | Azure Container Apps Jobs 加入 docker-compose / Bicep,scheduled trigger |
| **Cluster mode for Langfuse**(handle Beta+ trace volume)| Langfuse cluster docker-compose v2 + Postgres replica;or migrate Langfuse self-host → Langfuse Cloud(SaaS) |
| **Disaster recovery** | Postgres backup automation;Azure Recovery Services Vault for ACR images |

---

## 8. Open Items / TODO

- [ ] **R8 mitigation P1 or P2**(corp proxy on PyPI)— blocks W2+ pip-based work
- [ ] **R9 long-term IT whitelist** for `mcr.microsoft.com`(Azurite Docker fallback restore)
- [ ] **W7 Bicep template scaffold** — defer to W6 末 prep
- [ ] **W7 GitHub Actions workflow scaffold** — defer to W6 末 prep
- [ ] **Azure Key Vault wiring**(replace `.env`)— W7+
- [ ] **`backend/.venv-py314-backup/` removal** — once W2 D5 confirms 3.12 stable,可刪 backup folder

---

**Cross-refs**:
- Catalog: [`../COMPONENT_CATALOG.md#c12--devops--infra`](../COMPONENT_CATALOG.md#c12--devops--infra)
- Risks: [`../../01-planning/RISK_REGISTER.md`](../../01-planning/RISK_REGISTER.md) R8 / R9
- Setup: [`../../setup.md`](../../setup.md)(local dev step-by-step)
- Spec: `architecture.md §4.3`(local stack)+ `§9`(Beta+ deploy)

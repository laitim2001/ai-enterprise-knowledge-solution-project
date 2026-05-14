# EKP — Local Dev Environment Setup

> **目的**:由 zero 到可以喺本地跑起 EKP backend + frontend,連得到 Azure AI Search、Azure OpenAI、Cohere reranker。
> **目標時間**:**熟手 ~10 分鐘**(已有 Azure resources)/ **新人 ~45–60 分鐘**(由 provision Azure 開始)
> **適用版本**:Spec v5(2026-04-27)
> **最後更新**:2026-04-27

---

## 0. 點用呢份文件

呢份文件分**三條 path**,揀啱嗰條跟住做:

| 你係邊種 reader | 跟邊條 path |
|---|---|
| 熟手,Azure resources 已 provisioned | **§1 Pre-flight check** → **§2 Quick path** → 完 |
| 新人,要由 zero 開始 | **§1** → **§3 Azure provisioning** → **§4 Local dev** → **§5 `.env`** → **§6 Cohere** → **§7 Verification** |
| 遇到問題 | **§8 Troubleshooting** |
| 已 setup 過,而家想 update | **§9 Re-setup / update** |

---

## 1. Pre-flight Checklist

### 1.1 Local Software

| Tool | Min Version | Check |
|---|---|---|
| Docker Desktop | 20.10+ | `docker --version` |
| Docker Compose | v2.0+ | `docker compose version` |
| Python | 3.12+ | `python3 --version` |
| `uv`(recommended)or `pip` | uv 0.4+ | `uv --version` |
| Node.js | 20.0+ | `node --version` |
| `pnpm`(recommended)| 9.0+ | `pnpm --version` |
| Git | 2.30+ | `git --version` |
| Azure CLI(optional 但 helpful)| 2.60+ | `az --version` |

### 1.2 Azure Tenant Access

需要由 IT / Stakeholder 確認:

- [ ] Azure subscription ID(寫低)
- [ ] Resource group name(可以用 existing 或新開,e.g. `rg-ekp-poc-eastasia`)
- [ ] Region:**East Asia / Southeast Asia**(near APAC users)/ 或 **East US**(若 GPT-5.5 deployment 喺嗰邊)
- [ ] Permissions:`Contributor` on resource group(provision)、`Cognitive Services OpenAI User`(call OpenAI)、`Search Index Data Contributor`(call AI Search)、`Storage Blob Data Contributor`(call Blob)

### 1.3 External Services

- [ ] Cohere API key(direct or via Azure Marketplace)— 詳見 §6
- [ ] Microsoft Entra ID app registration(**Beta 階段先要,POC 階段 skip**)
- [ ] GitHub repo access(EKP 主 repo)

### 1.4 Document Source Access

- [ ] Drive Project 100 manuals 嘅 access(SharePoint URL / Drive folder / network share path)— 對應 OQ-Q2,W1 Day 1 必須 confirm

---

## 2. Quick Path(熟手 ~10 分鐘)

假設你已有 §1.1–1.4 全部 ready。

```bash
# 1. Clone repo
git clone <repo-url> ekp && cd ekp

# 2. Setup Dify reference(read-only)
mkdir -p references && cd references
git clone --depth 1 https://github.com/langgenius/dify.git
git -C dify log -1 --format="%H %ci" > DIFY_PINNED_COMMIT.txt
cd ..

# 3. Configure environment
cp .env.example .env
# 編輯 .env:Azure endpoints、keys、Cohere — 詳見 §5

# 4. Local services(Azurite + Langfuse + Postgres)
docker compose -f infrastructure/docker-compose.yml up -d

# 5. Initialize Azure AI Search index
cd backend
uv sync
uv run python -m scripts.init_azure_search_index

# 6. Backend dev server
uv run uvicorn api.server:app --reload --port 8000 &

# 7. Frontend
cd ../frontend
pnpm install
pnpm dev   # http://localhost:3001
```

**Verify everything works**:跳到 §7。

如果 Quick Path 任何一步 fail → §8 Troubleshooting。

---

## 3. Azure Resources Provisioning(新人 path)

呢個 section 假設你由 zero 開始 provision Azure resources。

### 3.1 推薦做法:Azure CLI script

```bash
# 設定變量
RG=rg-ekp-poc-eastasia
LOCATION=eastasia
SUBSCRIPTION_ID=<your-subscription-id>

# Login
az login
az account set --subscription $SUBSCRIPTION_ID

# Create resource group
az group create -n $RG -l $LOCATION
```

### 3.2 Azure AI Search(Standard S1)

```bash
SEARCH_NAME=ekp-search-poc

az search service create \
  --name $SEARCH_NAME \
  --resource-group $RG \
  --sku standard \
  --partition-count 1 \
  --replica-count 1 \
  --semantic-search standard

# 取 admin key(放入 .env)
az search admin-key show \
  --service-name $SEARCH_NAME \
  --resource-group $RG \
  --query primaryKey -o tsv

# 取 endpoint
echo "https://${SEARCH_NAME}.search.windows.net"
```

> **Note**:Standard S1 base price ~USD 75/月。Tier 1 規模(2K chunks、5 QPS peak)
> Basic tier 都頂得順,但 **Standard tier 先包 semantic ranker** —— W4 mini-shootout
> 嘅其中一個對照組(`reranker_azure_native`)需要佢。

### 3.3 Azure OpenAI

Azure OpenAI 嘅 service creation 需要 quota approval(因 region / model availability 限制),如未有 access 請先申請 quota:

```bash
# Service creation(若已有可 skip)
AOAI_NAME=ekp-openai-poc

az cognitiveservices account create \
  --name $AOAI_NAME \
  --resource-group $RG \
  --kind OpenAI \
  --sku S0 \
  --location $LOCATION \
  --yes

# 取 endpoint + key
az cognitiveservices account show \
  --name $AOAI_NAME \
  --resource-group $RG \
  --query properties.endpoint -o tsv

az cognitiveservices account keys list \
  --name $AOAI_NAME \
  --resource-group $RG \
  --query key1 -o tsv
```

**Deploy 三個 model**(W1 critical):

```bash
# Embedding
az cognitiveservices account deployment create \
  --name $AOAI_NAME --resource-group $RG \
  --deployment-name text-embedding-3-large \
  --model-name text-embedding-3-large \
  --model-version <latest-version> \
  --model-format OpenAI \
  --sku-name Standard \
  --sku-capacity 50

# Synthesis LLM
az cognitiveservices account deployment create \
  --name $AOAI_NAME --resource-group $RG \
  --deployment-name gpt-5-5 \
  --model-name gpt-5.5 \
  --model-version <version> \
  --model-format OpenAI \
  --sku-name Standard \
  --sku-capacity 100

# CRAG judge LLM(便宜)
az cognitiveservices account deployment create \
  --name $AOAI_NAME --resource-group $RG \
  --deployment-name gpt-5-4-mini \
  --model-name gpt-5.4-mini \
  --model-version <version> \
  --model-format OpenAI \
  --sku-name Standard \
  --sku-capacity 50
```

> ⚠️ `gpt-5.5` model name 同 deployment 細節**待 Q4 confirm**(deployment 可能用 dash 而非 dot,e.g. `gpt-5-5`)。
> 確認後喺 `.env` 嘅 `AZURE_OPENAI_DEPLOYMENT_*` var 填具體 name。

### 3.4 Azure Blob Storage

```bash
STORAGE_NAME=ekpstoragepoc$RANDOM   # 必須 globally unique

az storage account create \
  --name $STORAGE_NAME \
  --resource-group $RG \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot

# Create container for screenshots
az storage container create \
  --name ekp-kb-drive-screenshots \
  --account-name $STORAGE_NAME \
  --auth-mode login

# 取 connection string(放 .env)
az storage account show-connection-string \
  --name $STORAGE_NAME \
  --resource-group $RG \
  --query connectionString -o tsv
```

### 3.5 Azure Key Vault(Beta+ ready,POC 可後補)

```bash
KV_NAME=ekp-kv-poc

az keyvault create \
  --name $KV_NAME \
  --resource-group $RG \
  --location $LOCATION

# Grant your user access(POC dev)
az keyvault set-policy \
  --name $KV_NAME \
  --upn <your-email> \
  --secret-permissions get list set delete
```

### 3.6 Provisioning Checklist

完成後應該有以下 5 個 resource:

- [ ] Azure AI Search(`ekp-search-poc`)+ admin key
- [ ] Azure OpenAI(`ekp-openai-poc`)+ key + 3 個 deployment(`text-embedding-3-large`、`gpt-5.5`、`gpt-5.4-mini`)
- [ ] Azure Blob Storage(`ekpstoragepoc...`)+ connection string + container `ekp-kb-drive-screenshots`
- [ ] Resource group(`rg-ekp-poc-eastasia`)
- [ ] (Optional)Azure Key Vault

預計 monthly cost(POC):**~USD 95**(AI Search S1 + Blob + dev compute);加 OpenAI / Cohere 嘅 token cost ~USD 100–150。詳見 [`architecture.md` §9](./architecture.md)。

---

## 4. Local Dev Environment

### 4.1 Repo + Dify Reference Setup

```bash
git clone <ekp-repo-url> ekp && cd ekp

# Dify reference(read-only,gitignored)
mkdir -p references && cd references
git clone --depth 1 https://github.com/langgenius/dify.git
git -C dify log -1 --format="%H %ci" > DIFY_PINNED_COMMIT.txt
cd ..

# 確認 .gitignore include references/dify/
grep -q "references/dify" .gitignore || echo "references/dify/" >> .gitignore
```

> ⚠️ **Strict Mode reminder**:`references/dify/` 係 read-only。任何時候**唔可以**
> `cp` 或 import Dify code 入 EKP codebase。詳見 [`references/REFERENCE_USAGE.md`](../references/REFERENCE_USAGE.md)
> 同 [`CLAUDE.md` §4.3 H3](../CLAUDE.md)。

### 4.2 Docker Compose Stack

`infrastructure/docker-compose.yml` 含 4 個 service:

| Service | Port | Purpose |
|---|---|---|
| **azurite** | 10000–10002 | Local Azure Blob emulator |
| **postgres** | 5432 | Langfuse 嘅 backend store + EKP persistent backing(KB Manager + users / sessions — dedicated `ekp` database,per ADR-0023)|
| **langfuse** | 3000 | Self-host observability(traces) |
| **(optional)pgadmin** | 5050 | Postgres UI(debug 用) |

> **EKP `ekp` database**(W17 F1 — ADR-0023):`infrastructure/postgres-init/01-create-ekp-db.sql` 喺 postgres container 首次啟動時自動 `CREATE DATABASE ekp`。已有 volume(冇重建)就手動建一次:
> ```bash
> docker compose -f infrastructure/docker-compose.yml exec postgres createdb -U langfuse ekp
> ```
> 然後喺 `backend/.env` 設 `DATABASE_URL=postgresql://langfuse:langfuse_local_dev_only@localhost:5432/ekp` —— `KBService`(`make_kb_backend`)+ `users_repo`(`make_users_store`)就改用 Postgres,KB / 帳號 restart 唔再清空。**唔設 `DATABASE_URL` → 維持 in-memory fallback**(W1 行為,本機 dev / CI 不變;table 由 backend `CREATE TABLE IF NOT EXISTS` 自建,無 migration step)。

```bash
# Start
docker compose -f infrastructure/docker-compose.yml up -d

# Verify
docker compose -f infrastructure/docker-compose.yml ps

# Logs
docker compose -f infrastructure/docker-compose.yml logs -f langfuse

# Stop(保留 volume)
docker compose -f infrastructure/docker-compose.yml stop

# Tear down(清晒 data)
docker compose -f infrastructure/docker-compose.yml down -v
```

**Verify Azurite**:

```bash
# Should respond with XML
curl -i "http://127.0.0.1:10000/devstoreaccount1?comp=list"
```

**Verify Langfuse**:打開 `http://localhost:3000`,初次需要 create local admin account。

### 4.3 Backend Setup

```bash
cd backend

# Install dependencies(uv 推薦,faster than pip)
uv sync                        # 讀 pyproject.toml + uv.lock

# 或者用 pip
# pip install -e ".[dev]"

# Initialize Azure AI Search index
uv run python -m scripts.init_azure_search_index --kb-id drive_user_manuals

# Run dev server
uv run uvicorn api.server:app --reload --port 8000

# 應該見到:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Application startup complete.
```

### 4.4 Frontend Setup

```bash
cd frontend

# Install
pnpm install

# Dev server
pnpm dev

# 應該見到:
# ▲ Next.js 14.x.x
# - Local:        http://localhost:3001
# - Environments: .env.local
```

### 4.5 Verify Backend ↔ Frontend connectivity

```bash
# Backend health
curl http://localhost:8000/health
# 預期:{"status":"ok","azure_search":"connected","azure_openai":"connected", ...}

# Frontend → Backend(經 browser console 或者 curl)
curl http://localhost:8000/kb
# 預期:[](空 array,因為仲未 ingest doc)
```

---

## 5. `.env` Configuration

### 5.1 完整 Template

EKP 用**單一 `.env`(repo root)**。Backend 嘅 `Settings`(`backend/storage/settings.py`)用絕對路徑讀呢份 file,所以**唔需要** `backend/.env` symlink — `uvicorn api.server:app` 由 repo root、由 `backend/`、由 test runner 啟動都一樣讀到。Frontend 用 `NEXT_PUBLIC_*` prefix subset(`frontend/.env.local`,Next.js 慣例;可以由 repo-root `.env` 揀相關 var copy 過去,或直接放 `frontend/.env.local`)。

> 仍想用 symlink?可以 —— 若 `backend/.env` 存在,佢會 **override** repo-root 嗰份(per-invocation override 用)。但唔係必須。

`.env.example`(repo 入面)內容如下,setup 時 copy 為 `.env` 並填入真實 value:

```bash
# ============================================================================
# EKP Environment Configuration
# Copy this to .env and fill in your values
# DO NOT commit .env to git
# ============================================================================

# ----------------------------------------------------------------------------
# Azure AI Search
# ----------------------------------------------------------------------------
AZURE_SEARCH_ENDPOINT=https://ekp-search-poc.search.windows.net
AZURE_SEARCH_ADMIN_KEY=<from-az-search-admin-key-show>
AZURE_SEARCH_DEFAULT_INDEX=ekp-kb-drive-v1

# ----------------------------------------------------------------------------
# Azure OpenAI
# ----------------------------------------------------------------------------
AZURE_OPENAI_ENDPOINT=https://ekp-openai-poc.openai.azure.com
AZURE_OPENAI_API_KEY=<from-az-cognitiveservices-account-keys-list>
AZURE_OPENAI_API_VERSION=2025-04-01-preview

# Deployment names(pending Q4 — 確認你 deploy 嘅 actual deployment name)
AZURE_OPENAI_DEPLOYMENT_EMBEDDING=text-embedding-3-large
AZURE_OPENAI_DEPLOYMENT_LLM_PRIMARY=gpt-5-5
AZURE_OPENAI_DEPLOYMENT_LLM_JUDGE=gpt-5-4-mini
AZURE_OPENAI_DEPLOYMENT_LLM_EVAL_JUDGE=gpt-5-5-pro

# Embedding config
EMBEDDING_DIMENSION=1024            # MRL truncate from 3072

# ----------------------------------------------------------------------------
# Azure Blob Storage
# ----------------------------------------------------------------------------
# Local dev:用 Azurite emulator(default key 係 well-known constant)
AZURE_BLOB_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEhGzF0ePEMoxLdF8Ok2j3pgnT88t1MUSzJGdu/XpGV1KZL3Y7gLXnUMNm5zlcA==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;
AZURE_BLOB_CONTAINER_SCREENSHOTS=ekp-kb-drive-screenshots

# Cloud(POC / Beta+):用 real Azure Blob,replace 上面
# AZURE_BLOB_CONNECTION_STRING=<from-az-storage-account-show-connection-string>

# ----------------------------------------------------------------------------
# Cohere Rerank(direct API,W3 critical)
# ----------------------------------------------------------------------------
COHERE_API_KEY=<from-cohere-dashboard>
COHERE_RERANK_MODEL=rerank-v4.0-pro    # ADR-0012 W6 production lock

# ----------------------------------------------------------------------------
# (W4 only)Voyage / ZeroEntropy for reranker shootout
# ----------------------------------------------------------------------------
VOYAGE_API_KEY=
ZEROENTROPY_API_KEY=

# ----------------------------------------------------------------------------
# Langfuse(self-host)
# ----------------------------------------------------------------------------
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=<after-creating-langfuse-project>
LANGFUSE_SECRET_KEY=<after-creating-langfuse-project>

# ----------------------------------------------------------------------------
# CRAG / Pipeline tuning
# ----------------------------------------------------------------------------
CRAG_CONFIDENCE_THRESHOLD=0.70
CRAG_MAX_REFORMULATIONS=1
HYBRID_TOP_K_RETRIEVAL=50
RERANK_TOP_K=5

# ----------------------------------------------------------------------------
# Feature flags
# ----------------------------------------------------------------------------
FEATURE_L3_ROUTING_ENABLED=false       # W5 stretch
FEATURE_AUTH_ENABLED=false             # Beta+

# ----------------------------------------------------------------------------
# Frontend(NEXT_PUBLIC_* 會暴露俾 browser)
# ----------------------------------------------------------------------------
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=EKP
NEXT_PUBLIC_DEFAULT_KB_ID=drive_user_manuals

# ----------------------------------------------------------------------------
# Logging / Debug
# ----------------------------------------------------------------------------
LOG_LEVEL=INFO                          # DEBUG / INFO / WARNING / ERROR
ENVIRONMENT=local                       # local / poc / beta / production
```

### 5.2 Sensitive vs Non-sensitive

| 類別 | Vars | Local 處理 | Beta+ 處理 |
|---|---|---|---|
| **Sensitive** | `*_API_KEY`、`*_ADMIN_KEY`、`*_CONNECTION_STRING`、`LANGFUSE_SECRET_KEY` | `.env`(gitignored) | Azure Key Vault |
| **Non-sensitive** | `*_ENDPOINT`、`*_DEPLOYMENT_*`、`FEATURE_*`、`NEXT_PUBLIC_*` | `.env` | App Configuration / env var |

⚠️ **絕對唔可以**:
- `git add .env`
- 喺 commit message 出現任何 key
- 將 sensitive var 用 `NEXT_PUBLIC_*` prefix(會暴露 browser)
- Hardcode 任何 secret 落 source code

詳見 [`CLAUDE.md` §4.5 H5](../CLAUDE.md)。

---

## 6. Cohere Rerank Setup

Cohere v4.0-pro(W6 production lock per ADR-0012;v3.5 W3 baseline 已 upgrade)有兩條 onboarding path,**揀啱嗰條跟做**:

### 6.1 Path A:Direct API(POC W3 quickest start)

1. 去 [https://dashboard.cohere.com/](https://dashboard.cohere.com/) sign up
2. Trial tier 有 free quota(對 POC eval set 嘅 30–50 條 query 完全夠 W4 跑)
3. 拎 API key → 填入 `.env` 嘅 `COHERE_API_KEY`
4. **Production billing**:用 corporate card / pay-as-you-go(~USD 2 per 1K rerank requests)

**Pros**:5 分鐘搞掂,W3 唔 block
**Cons**:Procurement 唔正規,billing 唔對齊 Azure

### 6.2 Path B:Azure Marketplace(Beta+ recommended)

1. 喺 Azure Portal 搵「Cohere Rerank」喺 Marketplace
2. Subscribe → Cohere 會 issue Azure-Marketplace-bound API key
3. Billing 直接歸入 Azure subscription
4. 拎 API key → 填入 `.env` 嘅 `COHERE_API_KEY`

**Pros**:Procurement 對齊、billing 集中、SOC compliance 過關
**Cons**:可能要 IT / Finance approval(7–14 日)

### 6.3 Recommended Strategy

- **W1–W6 POC**:用 **Path A**(direct API + corporate card)
- **W3 並行 initiate Path B**(同 procurement / IT 開單)
- **Beta(W7+)**:切到 Path B,`.env` 嘅 `COHERE_API_KEY` swap 為 Azure Marketplace key

呢個策略避免 Cohere procurement delay(R3 risk in `architecture.md` §8.2)block 住 W3 critical path。

---

## 7. Verification(setup 真係成功嗎)

完成 setup 後跑呢套驗證 sequence:

### 7.1 Health Check

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

預期 output:
```json
{
  "status": "ok",
  "components": {
    "azure_search": "connected",
    "azure_openai": "connected",
    "azure_blob": "connected",
    "cohere": "connected",
    "langfuse": "connected"
  },
  "version": "0.1.0"
}
```

如果任何 component `status = "error"` → §8 Troubleshooting。

### 7.2 KB CRUD

```bash
# Create KB
curl -X POST http://localhost:8000/kb \
  -H "Content-Type: application/json" \
  -d '{"kb_id": "test_kb", "name": "Test KB", "description": "Verification"}'

# List KBs
curl http://localhost:8000/kb

# Delete
curl -X DELETE http://localhost:8000/kb/test_kb
```

### 7.3 Embedding 端到端

```bash
# 經 backend 試 call Azure OpenAI embedding
curl -X POST http://localhost:8000/debug/embed-test \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello EKP"}'
```

預期返回 1024-dim vector。

### 7.4 Frontend ↔ Backend

打開 `http://localhost:3001`,應該見到 EKP chat UI(empty state)。Open browser DevTools Network tab → 確認 frontend 真係 call 到 `localhost:8000`。

### 7.5 Langfuse Trace

任何 API call 完成後,去 `http://localhost:3000` 應該見到 trace record。如果見唔到 → check `.env` 嘅 `LANGFUSE_*` keys。

---

## 8. Troubleshooting

### 8.1 Docker / Azurite

| 症狀 | 原因 | 解決 |
|---|---|---|
| `port 10000 already in use` | 其他 Azure tool 用緊 | `lsof -i :10000` 搵出 process kill;或者改 `docker-compose.yml` 嘅 port mapping |
| Azurite 容器一啟即 exit | Volume permission | `docker compose down -v && docker compose up -d`(清 volume 重來) |
| 連得到 Azurite 但 Blob upload fail | Account name / key 同 default 唔同 | 用 default `devstoreaccount1` + well-known key,**唔好**改 |
| `docker compose up -d azurite` 失敗 `503 Service Unavailable` / `httpReadSeeker: failed open` mid-blob 喺 `mcr.microsoft.com` | R8/R9 corp proxy 截 MCR layer blob CDN(`southeastasia.data.mcr.microsoft.com`)— see ADR-0017 occurrence #6 + RISK_REGISTER R9 | **Plan B (b) native npm**:`npm install -g azurite`(一次過,如未裝)→ `azurite --blobHost 0.0.0.0 --queueHost 0.0.0.0 --tableHost 0.0.0.0 --location infrastructure/azurite-data --silent`(host-side background)。data dir 同 docker volume mount 100% interchangeable;`AZURE_BLOB_CONNECTION_STRING` 唔需改 |

### 8.2 Azure OpenAI

| 症狀 | 原因 | 解決 |
|---|---|---|
| `404 model not found` | Deployment name 唔啱 | Azure Portal → OpenAI resource → Model deployments,核對實際 deployment name(可能係 `gpt-5-5` 而非 `gpt-5.5`)|
| `429 rate limit` | TPM quota 唔夠 | Reduce concurrent calls;申請 quota increase(Q5 Azure quota risk) |
| `403 access denied` | RBAC 唔 enough | 你個 user 需要 `Cognitive Services OpenAI User` role |
| Embedding response 係 3072d 而非 1024d | 冇 pass `dimensions` parameter | Backend code check `embedder.create(input=..., dimensions=1024)` |

### 8.3 Azure AI Search

| 症狀 | 原因 | 解決 |
|---|---|---|
| Index 創建 fail `unauthorized` | Admin key 錯 | `az search admin-key show` 重新拎 |
| Hybrid query empty result | Index field schema 唔啱 | `python -m scripts.verify_search_index` 對比 schema |
| Semantic ranker 唔 work | Tier 唔啱 | Standard S1+ 先支援(Basic tier 冇)|

### 8.4 Cohere

| 症狀 | 原因 | 解決 |
|---|---|---|
| `401 unauthorized` | API key 錯 / expired | Cohere dashboard 重 issue |
| `Region not supported` | Cohere 對某啲 region 有限制 | 改用 Azure Marketplace path,或 fallback 到 Azure built-in semantic ranker |
| Quota 爆 | Trial tier 限 | 升 paid tier;W4 shootout 預留 budget |

### 8.5 Frontend

| 症狀 | 原因 | 解決 |
|---|---|---|
| `Module not found: shadcn/ui` | shadcn 唔係 npm package,要用 CLI 加 | `pnpm dlx shadcn@latest add button card`(每個 component 個別 add) |
| CORS error | Backend 冇 enable CORS for `localhost:3001` | Backend `api/server.py` add `CORSMiddleware` allow `localhost:3001` |
| Streaming response 唔 work | SSE proxy 問題 | Next.js dev server 唔會 proxy SSE,frontend 應該直接 call `localhost:8000`,唔可以經 Next.js API route relay |

### 8.6 Backend

| 症狀 | 原因 | 解決 |
|---|---|---|
| 所有 auth-gated route 503 / `IndexPopulator None` / `feature_auth_mock` 仍係 `False` 即使 `.env` 已設啱 | `.env` 冇被讀到 — 通常因為 backend 由 `backend/` CWD 啟動,但 `.env` 喺 repo root | **由 2026-05-13 起唔再係問題**:`backend/storage/settings.py` 嘅 `env_file` 已 pin 去 repo-root `.env` 嘅絕對路徑(CWD-independent),由邊度啟動都讀到。`.env` 永遠係 repo root 嗰份(`.env.example` 隔離);若 `backend/.env` 同時存在,佢會 *override* repo-root 嗰份(symlink / per-invocation override 用)。舊版本嘅 workaround(由 repo root 起 + `--env-file ../.env` + `backend/.env` symlink)已唔需要 |
| Docling 第一次 parse 一份 `.pdf` 慢幾分鐘(`POST /kb/{kb}/documents` duration ~4 分鐘)| 首次觸發 Docling 下載 layout / OCR models(RapidOCR PP-OCRv4 + docling-layout-heron + docling-models,~hundreds MB,from HuggingFace + ModelScope)| 等;只係 cold-start 一次。Tier 1 ingest 係 synchronous(background-task ingestion 屬 Tier 2 per CH-001 spec §2.4)|
| Docling Docker image pull 慢 | First-time download ~2GB | 等;考慮 pre-build image 放公司 internal registry |
| `python-docx` parse fail on complex equation | OOXML edge case(see E9) | Parser 應該 fallback 到 text representation,唔 abort |
| Langfuse trace 唔出現 / `/query` 嘅 `trace_id` 係空 string | `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` 未配(`.env` 可能只有 `LANGFUSE_HOST`)| Langfuse UI(`http://localhost:3000`)create project → 拎 public + secret keys → 填入 `.env`。未配時 `langfuse_sdk_status: not_configured`,`/query` graceful-degrade(`trace_id` 空),`/debug/trace/{id}` 只能驗 degrade path,`/feedback` 對 nonexistent trace → 400 |

---

## 9. Re-setup / Update Workflow

### 9.1 Pull latest changes

```bash
git pull
cd backend && uv sync     # update Python deps
cd ../frontend && pnpm install   # update Node deps
```

### 9.2 Re-init Azure AI Search index(若 schema 改)

```bash
# 注意:會 drop 現有 index 同所有 chunks
cd backend
uv run python -m scripts.init_azure_search_index --kb-id drive_user_manuals --force
```

### 9.3 Reset local Azurite

```bash
docker compose -f infrastructure/docker-compose.yml down -v
docker compose -f infrastructure/docker-compose.yml up -d
```

### 9.4 Update Dify reference(每季)

```bash
cd references/dify
git pull
cd ..
git -C dify log -1 --format="%H %ci" > DIFY_PINNED_COMMIT.txt

# Team review:Dify 有冇重大 design change 影響 EKP UI 借鑒?
```

### 9.5 Rotate secrets

| Secret | Rotation cadence | How |
|---|---|---|
| Azure Search admin key | 每 90 日 | `az search admin-key renew` |
| Azure OpenAI key | 每 90 日 | `az cognitiveservices account keys regenerate` |
| Cohere key | 每 180 日 | Cohere dashboard regenerate |
| Langfuse keys | 每 90 日 | Langfuse UI rotate |

POC 階段可以較 lax,Beta+ 必須 enforce。

---

## 10. Environment-specific Notes

### 10.1 Local(this guide 主要對象)

- Blob = Azurite
- Langfuse = self-host docker
- 其他 = real Azure cloud(因為冇 emulator)

### 10.2 POC Cloud(W6 demo)

- Blob = real Azure Blob(`ekp-kb-drive-screenshots`)
- Container Apps deploy backend
- Streamlit / Next.js dev server hosted on dev VM
- 暫無 auth(內部 demo)

### 10.3 Beta+(W7–W12)

- 全 cloud
- Microsoft Entra ID auth on
- Static Web Apps host frontend
- Key Vault store all secrets
- Private Endpoint for Azure AI Search(若 R5 / R9 trigger)

---

## 11. 常見問題:setup 完整啟動需要幾耐?

| Scenario | 預估時間 |
|---|---|
| 熟手 + Azure resources 已存在 + Cohere key 已有 | ~10 分鐘 |
| 熟手 + 由零 provision Azure(用 CLI script) | ~30 分鐘 |
| 新人 + 需要 IT 配合 provision Azure + 等 quota approval | 1–3 個工作日 |
| 新人 + 完全無 Azure 經驗 | 半日(讀完呢份文件 + 跑 step by step) |

如果你嘅 setup 過 1 小時都跑唔起,**唔好 self-debug 過頭**,直接 escalate 畀 Chris 或團隊 channel。

---

## 12. Reference

- 主架構規格:[`architecture.md`](./architecture.md)
- Claude Code 行為規則:[`../CLAUDE.md`](../CLAUDE.md)
- Open Question 待 resolve:[`decision-form.md`](./decision-form.md)(W1 ready)
- Eval 方法:[`eval-methodology.md`](./eval-methodology.md)(W1 ready)
- Dify reference policy:[`../references/REFERENCE_USAGE.md`](../references/REFERENCE_USAGE.md)

---

**Setup guide version**:1.0
**Effective**:from W1 Day 1
**Owner**:Chris(技術 Lead)
**Last verified**:2026-04-27

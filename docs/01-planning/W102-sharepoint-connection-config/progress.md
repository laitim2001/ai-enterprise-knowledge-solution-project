# W102 Progress — SharePoint 連接 UI 配置

## Day 1 — 2026-07-01(kickoff）

**Context**:用戶 2026-07-01 測試 pushback「`.env`-only credential 唔現實」+ 更正 H5 誤解 → 提案甲/乙/丙(推薦甲）→ 用戶 AskUserQuestion 揀甲 + approve W102 plan → kickoff。

**已做**:
- BACKLOG B-09 → `進行中`。
- 讀通 admin connections 全 surface(`schemas/admin.py` / `admin_provider_storage.py` / `admin_provider_postgres.py` / `routes/admin/connections.py` / `storage/key_vault.py`)—— 確認:9 provider seed / `ProviderConfig` 無 provider-specific 非 secret 欄 / Postgres 用顯式欄(非 generic JSONB blob) / Key Vault provider 經 `request.app.state.key_vault_provider` / rotate-secret 係 app-生成(SharePoint 需用戶輸入 → 要新 set-secret 能力)。
- F1 ADR-0072 寫好(`Accepted`）—— 5 決定 lock(category integration / generic `settings` 欄 / set-secret 能力 / 來源優先序 managed>.env / 單連接）。

**設計決定(ADR-0072 lock）**:
- 非 secret config(tenant/client-id/credential_type)→ 新 generic `ProviderConfig.settings: dict`（Postgres JSONB + ALTER ADD COLUMN IF NOT EXISTS）。
- secret → Key Vault `set_secret` via 新 `POST /admin/connections/{id}/set-secret`（H5:不 log / 不回傳真值）。
- 整合層 credential 來源 managed > `.env` fallback（零回歸）。

**Next(F2 起）**:backend schema + storage（settings 欄 + SharePoint seed）→ F3 set-secret 端點 → F4 整合層來源 → F5-F6 前端 → F7 測試 → F8 文件。

**Decisions / OQ**:無新 OQ。H2 無新 dep（Key Vault + Graph + azure-identity 已在）。

---

## Day 1（cont）— F1-F8 implementation 完成 + G-W102 gate PASS

**已落地（全 8 deliverable）**:
- **F1** ADR-0072（Accepted）+ README index。
- **F2** `ProviderCategory` 加 `integration` + `ProviderConfig.settings` generic 欄 + `ProviderPatch.settings` + `sharepoint` seed（第 10 provider）+ Postgres `settings JSONB` 欄（ALTER ADD COLUMN IF NOT EXISTS，零遷移）+ roundtrip + PATCH Jsonb。
- **F3** 核心 `POST /admin/connections/{id}/set-secret`（用戶輸入 secret → `KeyVaultProvider.set_secret` 寫 Key Vault，回 masked，**H5 value 絕不 log/回傳**，`from None` 斷 chain）+ audit `connection_set_secret`。
- **F4** 整合層 `_managed_sharepoint_credentials`（讀 settings + Key Vault）+ `_sharepoint_credentials_or_503` **managed > `.env` fallback**；4 route 傳 `request`；503 訊息更新。
- **F5** 前端 `admin.ts`（型別 + `setSecret`）+ `settings-connections.tsx`（`integration` 分組 + `SharePointConfig` 卡:tenant/client-id + set-secret password 輸入，沿用既有 primitives H7 一致）。
- **F6** `_probe_sharepoint` config-state（not_tested/degraded/ok）+ 前端共用 test 按鈕。
- **F7** `test_sharepoint_managed_connection.py`（11 test）+ 修 3 個 nine→ten。
- **F8** runbook §2 加 UI 配置路徑；checklist/progress/BACKLOG。

**驗證（G-W102 gate）**:
- backend **65 passed**（integration route 16 + admin connections + 新 11 + audit log），0 fail。
- 前端 `tsc` exit 0 / `eslint` exit 0 / `admin-schemas.test.ts` exit 0。
- `mypy` 淨新增 error = 0（audit Literal 已修；6 個 `_ensure_schema_and_seed` psycopg 型別債 = pre-existing）。
- `ruff` 淨新增非 UP017 違規 = 0（UP017 跟同檔案既有 `datetime.now(timezone.utc)` style）。
- ingestion 核心 diff = 零。

**Retro**:
- **What went well**:既有 `/admin/connections`（ADR-0026）+ Key Vault `set_secret` + Settings surface 令甲成擴充非重做；managed>`.env` fallback 零回歸；set-secret（用戶輸入）vs rotate（app 生成）嘅區別喺落 plan 過程先揪出。
- **踩過**:漏咗 backend `audit_log.py` action Literal（頭先只加前端）→ mypy 揪返；Postgres f-string 內 `{}` 要 escape 做 `{{}}`。
- **教訓**:改共用 schema（admin provider）要同步 InMemory + Postgres + roundtrip + PATCH Jsonb + 前後端型別 + audit Literal 五處，漏一即 mypy/test 揪。

**Carry-over**:
- **live 端到端 smoke**:running backend 需**重啟**先 pick up 新端點（memory `project_stale_backend_no_reload`）；真 SharePoint 連通仍 blocked 真 tenant（D4，同 W100/W101）。
- 前端組件 test（deferred，plan「視進度」）+ user-guide 連接章節（optional）+ 生產 cert 上載 + 多 named connection（follow-up）。

**狀態**:W102 implementation 完成，G-W102 test gate PASS。

---

## Day 1（cont 2）— Live smoke（重啟 backend + mock auth，真 Postgres）

重啟 backend（帶新 code + `FEATURE_AUTH_MOCK=true` 供 curl）後逐端點 live 驗（真 Postgres admin backend + EnvVarProvider Key Vault）:

- **捉到真 bug + 修**:`admin_provider_postgres.py` seed `existing = {r[0] for r in ...}` —— 連接用 `dict_row`，`fetchall()` 返 dict，`r[0]` → `KeyError: 0`。**既有 latent bug**（seed 對已有 rows 嘅表），加第 10 provider 觸發 seed-insert 分支先 surface；**InMemory 單元測試冚唔到 Postgres 路**。修 `r[0]` → `r["provider_id"]`。
- Live 結果（修後全通）:**10 provider**（sharepoint category=integration）/ test 空→`not_tested` / **PATCH settings 持久化 Postgres**（exercise `settings JSONB` ALTER 欄）/ **set-secret 回 masked `***9999`，value 無洩漏（H5 ✅）** / test 齊→`ok` / GET roundtrip settings+masked 持久 / **resolve-site 用 managed creds 打真 Entra → `AADSTS90002 Tenant not found`（唔再 not-configured 503）→ managed 路端到端證明**（真連通需真 tenant D4）。

**教訓（追加）**:admin provider Postgres 路無單元測試覆蓋（測試用 InMemory）→ dict_row 索引 bug 潛伏;live smoke 對 running-server + 真 DB 路係必要驗證層。Postgres 路 test 覆蓋 = carry-over（需 test DB 基建）。

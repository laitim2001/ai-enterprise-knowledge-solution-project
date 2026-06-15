// ekp-page-settings-tabs.jsx — extends /settings with tabbed sub-pages
// Profile / Appearance / Providers / API Keys / Account
// Replaces the thin v1 PageSettings with a richer settings hub.
// Backend integration: provider credentials currently in .env; this surface
// represents the planned UI-driven configuration (KeyVault-backed for prod).

function PageSettingsRich({ theme, onToggleTheme, initialTab }) {
  const [tab, setTab] = useState(initialTab || "profile");
  const tabs = [
    { id: "profile",    label: "Profile",       icon: IcUsers },
    { id: "appearance", label: "Appearance",    icon: IcSparkles },
    { id: "connections",label: "Connections",   icon: IcLink },
    { id: "identity",   label: "Identity & Auth", icon: IcShield },
    { id: "api-keys",   label: "API Keys & Quotas", icon: IcKey },
    { id: "account",    label: "Account",       icon: IcShield },
    { id: "doc-profiling", label: "文件分類規則", icon: IcLayers },  // W77 / ADR-0056 段③
  ];

  return (
    <div className="content">
      <div className="content-narrow" style={{ maxWidth: 1080 }}>
        <div className="page-header">
          <div>
            <h1 className="page-title">Settings</h1>
            <p className="page-subtitle">Profile · theme · all external service connections · Entra ID + MSAL config · API quotas. <b>Zero hardcoded credentials</b> — every endpoint, secret, and connection string is managed here and persisted in Azure Key Vault.</p>
          </div>
        </div>

        <div className="tabs">
          {tabs.map((t) => {
            const Ic = t.icon;
            return (
              <div key={t.id} className="tab" data-active={tab === t.id} onClick={() => setTab(t.id)}>
                <Ic size={14} /> {t.label}
              </div>
            );
          })}
        </div>

        {tab === "profile"     && <SettingsProfile />}
        {tab === "appearance"  && <SettingsAppearance theme={theme} onToggleTheme={onToggleTheme} />}
        {tab === "connections" && <SettingsConnections />}
        {tab === "identity"    && <SettingsIdentity />}
        {tab === "api-keys"    && <SettingsApiKeys />}
        {tab === "account"     && <SettingsAccount />}
        {tab === "doc-profiling" && <SettingsDocProfiling />}
      </div>
    </div>
  );
}

// W77 / ADR-0056 層 A 段③ — 文件分類規則(admin 自行調試指揮中心):profile→preset 映射 +
// 偵測 threshold。值對齊 backend ingestion/profile_presets.py(W73)+ W75 section cap=5 +
// ingestion/profiler.py threshold(W72)。
function SettingsDocProfiling() {
  const PRESETS = [
    { profile: "P1 圖密SOP", id: "P1_sop_imgdense", cap: 80, neighbour: "開 · 40", marker: "開", anchor: "section · cap 5", detail: "detailed" },
    { profile: "P1 文字SOP", id: "P1_sop_text", cap: 20, neighbour: "開 · 10", marker: "開", anchor: "—", detail: "detailed" },
    { profile: "P2 散文", id: "P2_prose", cap: 12, neighbour: "關", marker: "關", anchor: "—", detail: "detailed" },
    { profile: "P3 圖密簡報", id: "P3_slide_imgdense", cap: 40, neighbour: "開 · 20", marker: "開", anchor: "—", detail: "concise" },
    { profile: "P3 文字簡報", id: "P3_slide_text", cap: 12, neighbour: "關", marker: "關", anchor: "—", detail: "concise" },
    { profile: "P4 掃描", id: "P4_scan_imgdense", cap: 20, neighbour: "關", marker: "關", anchor: "—", detail: "concise" },
    { profile: "P5 表單", id: "P5_form", cap: 8, neighbour: "關", marker: "關", anchor: "—", detail: "concise" },
  ];
  return (
    <div style={{ display: "grid", gap: 16 }}>
      <div className="banner banner-info">
        <IcLayers size={15} style={{ color: "oklch(var(--info))", flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13 }}>
            <b>文件分類規則</b> — 系統 ingest 時用 rule-based profiler(W72)偵測文件 profile,自動套對應 recall preset。
          </div>
          <div className="text-xs muted" style={{ marginTop: 2 }}>
            呢度係自動規則嘅指揮中心:調 profile→preset 映射 + 偵測 threshold · ADR-0056 層 A · LLM 退選用保險
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Profile → preset 映射</h3>
            <div className="card-desc">每個偵測 profile 套邊套 recall/render preset。改呢度影響所有新 ingest 文件(現有要 re-index)。</div>
          </div>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Profile</th><th className="col-num">圖上限</th><th>鄰近圖</th>
                  <th>inline marker</th><th>section 錨定</th><th>詳細度</th><th className="col-shrink"></th>
                </tr>
              </thead>
              <tbody>
                {PRESETS.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <span className="badge badge-muted"><span className="badge-dot" /> {p.profile}</span>
                      <div className="text-xs muted mono">{p.id}</div>
                    </td>
                    <td className="col-num mono">{p.cap}</td>
                    <td className="text-xs">{p.neighbour}</td>
                    <td className="text-xs">{p.marker}</td>
                    <td className="text-xs">{p.anchor}</td>
                    <td><span className="badge badge-muted">{p.detail}</span></td>
                    <td className="col-shrink"><button className="btn btn-ghost btn-xs">編輯</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">偵測 threshold</h3>
            <div className="card-desc">調 profiler 分類門檻。低於信心門檻 → fallback 保守 preset + 標「待人手確認」。</div>
          </div>
        </div>
        <div className="card-body" style={{ display: "grid", gap: 12 }}>
          <ThresholdRow label="低信心門檻(confidence)" value="0.70" hint="低於此 → 黃旗 + fallback 保守 preset" />
          <ThresholdRow label="P1 圖密門檻(img_density)" value="0.15" hint="≥ 此 + depth≥3 + list_ratio≥0.3 → P1 圖密SOP" />
          <ThresholdRow label="too_small 段落門檻" value="20" hint="少於此段落數 → too_small(唔路由,繼承上層)" />
        </div>
        <div className="card-footer">
          <div className="text-xs muted">改 threshold 只影響將來 ingest · ADR-0056 D2 rule v3</div>
          <button className="btn btn-primary btn-sm">儲存規則</button>
        </div>
      </div>
    </div>
  );
}

function ThresholdRow({ label, value, hint }) {
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label">{label}</label>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <input className="input" defaultValue={value} style={{ maxWidth: 110 }} />
        <span className="text-xs muted">{hint}</span>
      </div>
    </div>
  );
}

function SettingsProfile() {
  return (
    <div className="card">
      <div className="card-header"><h3 className="card-title">Profile</h3></div>
      <div className="card-body" style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 16 }}>
        <div className="avatar avatar-lg">CL</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600 }}>Chris Lai</div>
          <div className="text-sm muted">chris.lai@ricoh.com · Workspace Admin</div>
          <div className="text-xs muted mono" style={{ marginTop: 4 }}>Entra ID SSO · session active · last login 2026-05-15 08:42 UTC</div>
        </div>
        <button className="btn btn-secondary btn-sm" disabled>Edit profile <span className="badge badge-muted" style={{ marginLeft: 6 }}>Tier 2</span></button>
      </div>
    </div>
  );
}

function SettingsAppearance({ theme, onToggleTheme }) {
  return (
    <div className="card">
      <div className="card-header"><h3 className="card-title">Appearance</h3></div>
      <div className="card-body">
        <div className="row" style={{ padding: "4px 0" }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, fontSize: 13.5 }}>Theme</div>
            <div className="text-xs muted">Warm Charcoal (light) / Warm Neutral Dark (dark) · 100% oklch tokens</div>
          </div>
          <div className="seg">
            <button className="seg-btn" data-active={theme === "light"} onClick={() => theme === "dark" && onToggleTheme()}>Light</button>
            <button className="seg-btn" data-active={theme === "dark"} onClick={() => theme === "light" && onToggleTheme()}>Dark</button>
          </div>
        </div>
        <div className="hr" />
        <div className="row" style={{ padding: "4px 0" }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, fontSize: 13.5 }}>Language</div>
            <div className="text-xs muted">JP / ZH support is Tier 2 — disabled per ADR-0024 (see Labs · Multi-Language preview)</div>
          </div>
          <select className="select" disabled><option>English</option></select>
        </div>
      </div>
    </div>
  );
}

// ── Connections — ALL external services (LLM / Search / Storage / Identity / Infra) ─
function SettingsConnections() {
  const categories = [
    {
      id: "llm",
      label: "LLM & Embedding",
      icon: IcCpu,
      providers: [
        {
          id: "azure-openai", name: "Azure OpenAI", role: "LLM + Embedding + Judge",
          endpoint: "https://ricoh-rapo.openai.azure.com",
          region: "Japan East",
          status: "healthy",
          last_check: "2026-05-15T14:38:00Z",
          fields: [["endpoint", "Endpoint URL"], ["key", "API key"], ["deployment_default", "Default deployment"]],
          deployments: [
            { name: "gpt-5.5",                 type: "llm",   tier: "S2", capacity_tpm: 240000, used_pct: 0.42, status: "active" },
            { name: "gpt-5.4-mini",            type: "llm",   tier: "S1", capacity_tpm: 120000, used_pct: 0.18, status: "active" },
            { name: "gpt-5.5-pro-judge",       type: "judge", tier: "S1", capacity_tpm: 60000,  used_pct: 0.08, status: "active" },
            { name: "text-embedding-3-large",  type: "embedding", tier: "S1", capacity_tpm: 350000, used_pct: 0.62, status: "active" },
          ],
        },
        {
          id: "cohere", name: "Cohere", role: "Rerank",
          endpoint: "https://api.cohere.com",
          region: "Global",
          status: "healthy",
          last_check: "2026-05-15T14:38:00Z",
          fields: [["endpoint", "Endpoint URL"], ["key", "API key"]],
          deployments: [
            { name: "rerank-v4.0-pro",  type: "rerank", tier: "Production", capacity_tpm: 50000, used_pct: 0.31, status: "active", locked: true, lock_reason: "ADR-0012 production lock" },
            { name: "rerank-v3.5",      type: "rerank", tier: "Standby",    capacity_tpm: 50000, used_pct: 0,    status: "standby", label: "Baseline" },
          ],
        },
      ],
    },
    {
      id: "search-storage",
      label: "Search & Storage",
      icon: IcDatabase,
      providers: [
        {
          id: "azure-ai-search", name: "Azure AI Search", role: "Vector + BM25 hybrid index (per-KB)",
          endpoint: "https://ekp-search.search.windows.net",
          region: "Japan East",
          status: "healthy",
          last_check: "2026-05-15T14:37:00Z",
          fields: [
            ["endpoint",   "Endpoint URL"],
            ["admin_key",  "Admin key (read+write)"],
            ["query_key",  "Query key (read-only · for end users)"],
            ["service_tier","Service tier"],
            ["replicas",   "Replicas"],
            ["partitions", "Partitions"],
            ["semantic_enabled", "Semantic search · cohere-v4.0-pro alongside"],
          ],
          meta: [
            ["Service tier",   "Standard S1"],
            ["Replicas",        "1"],
            ["Partitions",      "1"],
            ["Indexes",         "5 active · ekp-kb-*-v1"],
            ["Total docs",      "9,767 chunks"],
            ["Total vector storage", "38.7 MB"],
            ["Index name pattern", "ekp-kb-{kb_id}-v{version}"],
            ["Semantic config", "ekp-semantic-config (enabled)"],
          ],
        },
        {
          id: "azure-blob", name: "Azure Blob Storage", role: "Screenshot images · per-KB container",
          endpoint: "https://ekpbeta.blob.core.windows.net",
          region: "Japan East",
          status: "healthy",
          last_check: "2026-05-15T14:37:00Z",
          fields: [
            ["account_name", "Storage account name"],
            ["auth_mode",    "Auth mode (managed identity / SAS / conn string)"],
            ["conn_string",  "Connection string (when SAS mode)"],
            ["default_tier", "Default access tier"],
          ],
          meta: [
            ["Account name",   "ekpbeta"],
            ["Auth mode",       "Managed Identity (production)"],
            ["Containers",      "5 active · ekp-kb-*-screenshots"],
            ["Total objects",   "590 images · 4 deduplicated"],
            ["Total size",      "1.7 GB"],
            ["Container pattern","ekp-kb-{kb_id}-screenshots"],
            ["Soft delete",     "Enabled · 14d retention"],
            ["CORS allowed origin", "https://ekp-beta.ricoh.com"],
          ],
        },
        {
          id: "postgres", name: "Azure Database for PostgreSQL", role: "KB metadata + sessions + feedback",
          endpoint: "ekp-pg.postgres.database.azure.com:5432",
          region: "Japan East",
          status: "healthy",
          last_check: "2026-05-15T14:37:00Z",
          fields: [
            ["host",           "Host"],
            ["port",           "Port"],
            ["database",       "Database name"],
            ["auth_mode",      "Auth mode"],
            ["ssl_mode",       "SSL mode"],
            ["pool_size",      "Connection pool size"],
          ],
          meta: [
            ["Host",            "ekp-pg.postgres.database.azure.com"],
            ["Database",        "ekp"],
            ["SSL mode",        "require"],
            ["Auth mode",       "Managed Identity (no password)"],
            ["Pool size",       "20 (per replica)"],
            ["Schemas",         "knowledge_bases · users · sessions · feedback · queries"],
            ["Migration version", "v17 (W17 F1 ADR-0023)"],
            ["Backup retention","7d daily snapshots"],
          ],
        },
        {
          id: "azurite", name: "Azurite (local dev emulator)", role: "Replaces Azure Blob in dev when AZURE_STORAGE_USE_AZURITE=true",
          endpoint: "http://127.0.0.1:10000",
          region: "Local",
          status: "dev-only",
          last_check: null,
          note: "Used in local dev when corp DNS intercepts MCR. npm fallback per R3 mitigation. Not active in production.",
          fields: [
            ["enabled",  "Enable in this environment"],
            ["endpoint", "Local endpoint"],
          ],
        },
      ],
    },
    {
      id: "observability",
      label: "Observability",
      icon: IcActivity,
      providers: [
        {
          id: "langfuse", name: "Langfuse", role: "10-stage trace + cost telemetry · self-hosted",
          endpoint: "https://langfuse.ekp-beta.ricoh.com",
          region: "Self-hosted (Container Apps)",
          status: "healthy",
          last_check: "2026-05-15T14:38:00Z",
          fields: [
            ["host",       "Host"],
            ["public_key", "Public key"],
            ["secret_key", "Secret key"],
            ["flush_interval", "Trace flush interval"],
          ],
          meta: [
            ["Version",          "v2.x self-host"],
            ["Backing store",    "Postgres (shared instance)"],
            ["Frontend URL env", "NEXT_PUBLIC_LANGFUSE_URL"],
            ["Trace flush",      "Every 1s or 100 events"],
            ["Retention",        "30 days · then aggregate"],
          ],
        },
        {
          id: "structlog", name: "structlog", role: "JSON stdout logging · forwarded to App Insights",
          endpoint: "stdout (App Insights collector)",
          region: "—",
          status: "healthy",
          last_check: "2026-05-15T14:38:00Z",
          fields: [
            ["level",  "Log level"],
            ["format", "Format (json / console-pretty)"],
            ["app_insights_key", "App Insights instrumentation key"],
          ],
        },
      ],
    },
    {
      id: "email",
      label: "Email & Messaging",
      icon: IcInbox,
      providers: [
        {
          id: "azure-acs", name: "Azure Communication Services", role: "Email verification (C13) + future notifications",
          endpoint: "https://ekp-acs.communication.azure.com",
          region: "Japan East",
          status: "healthy",
          last_check: "2026-05-15T14:35:00Z",
          fields: [
            ["connection_string", "Connection string"],
            ["sender_address",    "From address"],
            ["mock_in_dev",       "Use ConsoleEmailProvider in dev (feature_email_mock)"],
          ],
          meta: [
            ["Sender",          "noreply@dev.ekp-beta.ricoh.com"],
            ["Templates",        "verify-email · password-reset (Tier 2)"],
            ["Lazy SDK import", "Yes (per ADR-0017 corp-proxy mitigation)"],
          ],
        },
      ],
    },
    {
      id: "infra",
      label: "Infrastructure",
      icon: IcCloud,
      providers: [
        {
          id: "container-apps", name: "Azure Container Apps", role: "Backend + Frontend hosting (managed K8s)",
          endpoint: "ekp-prod-env.gentleocean-9f4b2c1d.japaneast.azurecontainerapps.io",
          region: "Japan East",
          status: "healthy",
          last_check: "2026-05-15T14:36:00Z",
          fields: [
            ["env_name",       "Environment name"],
            ["resource_group", "Resource group"],
            ["subscription_id","Subscription ID"],
            ["registry",       "Container registry"],
            ["scale_min",      "Min replicas"],
            ["scale_max",      "Max replicas"],
          ],
          meta: [
            ["Environment",     "ekp-prod-env"],
            ["Resource group",  "rg-ekp-prod-jpe"],
            ["Subscription",    "ekp-beta · subscription_id 9f4b…b1c4"],
            ["Apps",            "ekp-backend (v0.18.0) · ekp-frontend (v0.18.0)"],
            ["Backend scale",   "2–10 replicas · HTTP scaler · 100 RPS / replica"],
            ["Frontend scale",  "1–5 replicas · HTTP scaler · 200 RPS / replica"],
            ["Registry",        "ekpbeta.azurecr.io"],
            ["Custom domain",   "ekp-beta.ricoh.com (managed cert)"],
          ],
        },
        {
          id: "key-vault", name: "Azure Key Vault", role: "Persistent secret store · all credentials referenced here resolve through this",
          endpoint: "https://ekp-kv.vault.azure.net",
          region: "Japan East",
          status: "healthy",
          last_check: "2026-05-15T14:38:00Z",
          fields: [
            ["vault_url",  "Vault URL"],
            ["access_mode","Access mode (RBAC / access policy)"],
            ["soft_delete","Soft delete enabled"],
          ],
          meta: [
            ["Vault name",      "ekp-kv"],
            ["Soft delete",      "Enabled · 90d retention"],
            ["Access",           "Managed Identity (backend + frontend)"],
            ["Secrets stored",   "14 (LLM keys × 4 · DB password · ACS conn · Langfuse keys × 2 · etc.)"],
            ["Rotation policy",  "90d auto-reminder · manual rotation via UI"],
          ],
        },
      ],
    },
  ];

  return (
    <div className="col" style={{ gap: 14 }}>
      <div className="banner banner-info">
        <IcSparkles size={14} style={{ color: "oklch(var(--info))" }} />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>Every external connection is managed here</div>
          <div className="text-xs muted">
            LLM keys · Azure AI Search · Blob Storage · Postgres · Langfuse · ACS Email · Container Apps · Key Vault · Azurite (dev). All secrets resolve through Key Vault at runtime · no <span className="mono">.env</span> values used in production · changes are audit-logged.
          </div>
        </div>
        <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> Test all</button>
      </div>

      {categories.map((cat) => <ConnectionCategory key={cat.id} category={cat} />)}
    </div>
  );
}

function ConnectionCategory({ category }) {
  const [collapsed, setCollapsed] = useState(false);
  const Ic = category.icon;
  return (
    <div>
      <div onClick={() => setCollapsed(!collapsed)} style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "6px 10px", marginBottom: 8, marginTop: 8,
        cursor: "default",
      }}>
        <Ic size={14} className="muted" />
        <span className="nav-section-label" style={{ padding: 0 }}>{category.label}</span>
        <span className="text-xs muted">· {category.providers.length} service{category.providers.length > 1 ? "s" : ""}</span>
        <div className="spacer" />
        <IcChevRight size={12} className="muted" style={{ transform: collapsed ? "none" : "rotate(90deg)", transition: "transform 0.15s" }} />
      </div>
      {!collapsed && (
        <div className="col" style={{ gap: 10 }}>
          {category.providers.map((p) => <ServiceCard key={p.id} provider={p} />)}
        </div>
      )}
    </div>
  );
}

function ServiceCard({ provider }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="card">
      <div className="card-header" style={{ cursor: "default" }} onClick={() => setExpanded(!expanded)}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flex: 1 }}>
          <div style={{
            width: 32, height: 32,
            background: "oklch(var(--muted))",
            border: "1px solid oklch(var(--border))",
            borderRadius: "var(--radius-sm)",
            display: "grid", placeItems: "center",
            fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 11,
            flexShrink: 0,
          }}>
            {provider.name.split(" ").map((w) => w[0]).slice(0, 2).join("")}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <h3 className="card-title" style={{ fontSize: 13.5 }}>{provider.name}</h3>
              {provider.status === "healthy"  && <span className="badge badge-success"><span className="badge-dot" /> HEALTHY</span>}
              {provider.status === "dev-only" && <span className="badge badge-muted">DEV ONLY</span>}
              {provider.status === "disabled" && <span className="badge badge-muted">DISABLED</span>}
            </div>
            <div className="text-xs muted">
              {provider.role} · <span className="mono">{provider.endpoint}</span> · {provider.region}
            </div>
          </div>
        </div>
        <div className="row">
          <button className="btn btn-ghost btn-icon btn-xs" onClick={(e) => e.stopPropagation()}><IcRefresh size={12} /></button>
          <IcChevRight size={13} className="muted" style={{ transform: expanded ? "rotate(90deg)" : "none" }} />
        </div>
      </div>
      {expanded && (
        <>
          <div className="card-body" style={{ padding: 16 }}>
            {provider.note && (
              <div style={{ padding: "8px 10px", background: "oklch(var(--muted) / 0.4)", borderRadius: "var(--radius-sm)", fontSize: 12, marginBottom: 12, color: "oklch(var(--foreground) / 0.85)", lineHeight: 1.5 }}>
                <IcSparkles size={11} style={{ verticalAlign: "-2px", marginRight: 4 }} />
                {provider.note}
              </div>
            )}

            {provider.fields && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: provider.meta?.length || provider.deployments?.length ? 16 : 0 }}>
                {provider.fields.map(([id, label]) => (
                  <div key={id} className="field" style={{ marginBottom: 0 }}>
                    <label className="label" style={{ fontSize: 12 }}>{label}</label>
                    {id.includes("key") || id === "conn_string" || id === "connection_string"
                      ? <ApiKeyInput defaultValue={`${provider.id}_${id}_•••••••••••••••••••••`} />
                      : id === "endpoint" || id === "host"
                        ? <input className="input mono" defaultValue={id === "host" ? provider.endpoint.split(":")[0] : provider.endpoint} style={{ fontSize: 11.5 }} />
                        : <input className="input mono" placeholder={label} style={{ fontSize: 11.5 }} />}
                  </div>
                ))}
              </div>
            )}

            {provider.meta && (
              <>
                <div className="text-xs muted mono" style={{ marginBottom: 6, letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 600 }}>
                  Service metadata
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, padding: "10px 12px", background: "oklch(var(--muted) / 0.4)", borderRadius: "var(--radius-sm)", fontSize: 12 }}>
                  {provider.meta.map(([k, v]) => (
                    <div key={k} style={{ display: "flex", gap: 8, padding: "3px 0" }}>
                      <span className="muted" style={{ minWidth: 130 }}>{k}</span>
                      <span className="mono" style={{ flex: 1, color: "oklch(var(--foreground))" }}>{v}</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>

          {provider.deployments && (
            <div style={{ borderTop: "1px solid oklch(var(--border))" }}>
              <div style={{ padding: "10px 16px", background: "oklch(var(--muted) / 0.3)", display: "flex", alignItems: "center" }}>
                <span className="text-xs muted mono" style={{ letterSpacing: "0.04em", textTransform: "uppercase", fontWeight: 600 }}>
                  Deployments · {provider.deployments.length}
                </span>
                <div className="spacer" />
                <button className="btn btn-ghost btn-xs"><IcPlus size={11} /> Add deployment</button>
              </div>
              <table className="table">
                <thead>
                  <tr>
                    <th>Deployment</th>
                    <th>Type</th>
                    <th>Tier</th>
                    <th className="col-num">TPM cap</th>
                    <th className="col-num">Used</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {provider.deployments.map((d) => (
                    <tr key={d.name}>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <span className="mono" style={{ fontSize: 12, fontWeight: 500 }}>{d.name}</span>
                          {d.locked && <span className="badge badge-accent"><IcShield size={9} /> LOCKED</span>}
                          {d.label && <span className="badge badge-muted">{d.label}</span>}
                        </div>
                        {d.lock_reason && <div className="text-xs muted" style={{ marginTop: 2 }}>{d.lock_reason}</div>}
                      </td>
                      <td><span className="badge badge-muted">{d.type}</span></td>
                      <td className="col-mono">{d.tier}</td>
                      <td className="col-num">{(d.capacity_tpm / 1000).toFixed(0)}k</td>
                      <td className="col-num">
                        <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
                          <div style={{ width: 48, height: 4, background: "oklch(var(--muted))", borderRadius: 999, overflow: "hidden" }}>
                            <div style={{ width: `${d.used_pct * 100}%`, height: "100%", background: d.used_pct > 0.8 ? "oklch(var(--destructive))" : d.used_pct > 0.5 ? "oklch(var(--warning))" : "oklch(var(--success))" }} />
                          </div>
                          <span className="mono text-xs" style={{ width: 32, textAlign: "right" }}>{(d.used_pct * 100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td>
                        {d.status === "active"  && <span className="badge badge-success"><span className="badge-dot" /> ACTIVE</span>}
                        {d.status === "standby" && <span className="badge badge-muted"><span className="badge-dot" /> STANDBY</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="card-footer">
            <div className="text-xs muted mono">
              {provider.last_check ? `Last health check ${window.formatRelative(provider.last_check)}` : "Not connected · dev fallback"}
            </div>
            <div className="row">
              <button className="btn btn-ghost btn-xs"><IcRefresh size={11} /> Test connection</button>
              <button className="btn btn-ghost btn-xs"><IcEdit size={11} /> Edit YAML</button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ── Identity & Auth — Entra ID, App Registration, MSAL, Roles ──────────────
function SettingsIdentity() {
  return (
    <div className="col" style={{ gap: 14 }}>
      <div className="banner banner-info">
        <IcShield size={14} style={{ color: "oklch(var(--info))" }} />
        <div style={{ flex: 1, lineHeight: 1.55 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>Entra ID + MSAL configuration</div>
          <div className="text-xs muted">
            Authentication via Microsoft Entra ID (formerly Azure AD). Hybrid mode per ADR-0022: Entra ID SSO + self-register fallback · httpOnly cookie + CSRF double-submit + /auth/refresh.
          </div>
        </div>
      </div>

      {/* Tenant */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Entra ID tenant</h3>
          <span className="badge badge-success"><span className="badge-dot" /> CONFIGURED</span>
        </div>
        <div className="card-body" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Tenant ID</label>
            <input className="input mono" defaultValue="f8b1c4d9-3a7e-4b2c-9f4b-2c1d4e7f2056" style={{ fontSize: 12 }} />
            <div className="hint">Ricoh corporate Entra tenant</div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Tenant domain</label>
            <input className="input mono" defaultValue="ricoh.onmicrosoft.com" style={{ fontSize: 12 }} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Authority URL</label>
            <input className="input mono" defaultValue="https://login.microsoftonline.com/f8b1c4d9-…" style={{ fontSize: 12 }} disabled />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Cloud instance</label>
            <select className="select"><option>Azure Public Cloud</option><option>Azure Government</option><option>Azure China 21Vianet</option></select>
          </div>
        </div>
      </div>

      {/* App registration */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">App registration</h3>
            <div className="card-desc"><span className="mono">ekp-beta-app</span> · enterprise application in Entra ID</div>
          </div>
          <button className="btn btn-secondary btn-sm"><IcLink size={11} /> Open in Azure Portal ↗</button>
        </div>
        <div className="card-body" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Application (client) ID</label>
            <input className="input mono" defaultValue="b9e2a4d8-7c1f-4a3b-8e9d-1c4f2b5a6e7c" style={{ fontSize: 12 }} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Client secret <IcShield size={10} style={{ verticalAlign: "-1px", color: "oklch(var(--warning))" }} /></label>
            <ApiKeyInput defaultValue="entra_client_secret_•••••••••••••••" />
            <div className="hint">Expires 2026-12-15 · 90d rotation reminder</div>
          </div>
          <div className="field" style={{ gridColumn: "1 / -1", marginBottom: 0 }}>
            <label className="label">Redirect URIs (web)</label>
            <div className="col" style={{ gap: 4 }}>
              {[
                "https://ekp-beta.ricoh.com/auth/callback",
                "http://localhost:3001/auth/callback (dev)",
              ].map((u) => (
                <div key={u} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <input className="input mono" defaultValue={u} style={{ fontSize: 11.5, height: 28 }} />
                  <button className="btn btn-ghost btn-icon btn-xs"><IcX size={11} /></button>
                </div>
              ))}
              <button className="btn btn-ghost btn-xs" style={{ width: "fit-content" }}><IcPlus size={11} /> Add redirect URI</button>
            </div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">API permissions (scopes)</label>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              {["User.Read","openid","profile","email","offline_access"].map((s) => <span key={s} className="badge badge-muted">{s}</span>)}
            </div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Sign-in audience</label>
            <select className="select" defaultValue="single">
              <option value="single">Single tenant (this Entra org only)</option>
              <option value="multi" disabled>Multi-tenant (Tier 2 multi-tenancy)</option>
            </select>
          </div>
        </div>
      </div>

      {/* MSAL config */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">MSAL & session</h3>
          <div className="card-desc">httpOnly cookie + CSRF · per ADR-0022</div>
        </div>
        <div className="card-body" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Token cache strategy</label>
            <select className="select" defaultValue="memory"><option value="memory">In-memory (per-replica)</option><option value="distributed">Distributed (Redis · Tier 2)</option></select>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Session TTL</label>
            <input className="input mono" defaultValue="7d" style={{ fontSize: 12 }} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Refresh token rotation</label>
            <input className="input mono" defaultValue="24h" style={{ fontSize: 12 }} />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">CSRF token rotation</label>
            <input className="input mono" defaultValue="1h" style={{ fontSize: 12 }} />
          </div>
          <div className="field" style={{ gridColumn: "1 / -1", marginBottom: 0 }}>
            <label className="label">Cookie settings</label>
            <div style={{ padding: "8px 10px", background: "oklch(var(--muted) / 0.4)", borderRadius: "var(--radius-sm)", fontFamily: "var(--font-mono)", fontSize: 11.5, color: "oklch(var(--foreground) / 0.85)", lineHeight: 1.6 }}>
              Set-Cookie: ekp_session=…; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=604800
            </div>
          </div>
        </div>
      </div>

      {/* Role mapping */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Role mapping</h3>
            <div className="card-desc">Map Entra security groups → EKP roles · Tier 1 has 3 roles · Tier 2 adds Power-user</div>
          </div>
          <button className="btn btn-secondary btn-sm"><IcPlus size={13} /> Add mapping</button>
        </div>
        <div className="card-body card-body-tight">
          <table className="table">
            <thead><tr><th>EKP role</th><th>Entra group</th><th>Group ID</th><th className="col-num">Members</th><th className="col-shrink"></th></tr></thead>
            <tbody>
              <tr>
                <td><span className="badge badge-accent">Workspace Admin</span></td>
                <td><span className="mono text-xs">grp-ekp-admins</span></td>
                <td><span className="mono text-xs muted">a7f4…b1c4</span></td>
                <td className="col-num">3</td>
                <td className="col-shrink"><button className="btn btn-ghost btn-icon btn-xs"><IcMore size={13} /></button></td>
              </tr>
              <tr>
                <td><span className="badge badge-info">Knowledge Editor</span></td>
                <td><span className="mono text-xs">grp-ekp-editors</span></td>
                <td><span className="mono text-xs muted">b9e2…a4d8</span></td>
                <td className="col-num">12</td>
                <td className="col-shrink"><button className="btn btn-ghost btn-icon btn-xs"><IcMore size={13} /></button></td>
              </tr>
              <tr>
                <td><span className="badge badge-muted">End User</span></td>
                <td><span className="mono text-xs">grp-ekp-users (or default)</span></td>
                <td><span className="mono text-xs muted">c1f3…b7e2</span></td>
                <td className="col-num">28</td>
                <td className="col-shrink"><button className="btn btn-ghost btn-icon btn-xs"><IcMore size={13} /></button></td>
              </tr>
              <tr style={{ opacity: 0.5 }}>
                <td><span className="badge badge-muted">Power User</span> <span className="badge badge-muted">Tier 2</span></td>
                <td colSpan={4} className="text-xs muted">Power User role available post-W12 (advanced retrieval tuning + model picker per ADR-0024 future evolution)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Sign-in policy */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Sign-in policy</h3>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">Allowed email domains for self-register</label>
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
              <span className="badge badge-accent">@ricoh.com ×</span>
              <span className="badge badge-accent">@ricoh.co.jp ×</span>
              <button className="btn btn-ghost btn-xs">+ Add</button>
            </div>
            <div className="hint">Self-register requires matching email domain · email verification mandatory</div>
          </div>
          <div className="row" style={{ marginBottom: 10 }}>
            <span className="switch" data-on="true" />
            <span className="text-xs" style={{ flex: 1 }}>Require MFA for Workspace Admin role</span>
          </div>
          <div className="row" style={{ marginBottom: 10 }}>
            <span className="switch" data-on="false" />
            <span className="text-xs" style={{ flex: 1 }}>Require MFA for all roles (Tier 2)</span>
          </div>
          <div className="row">
            <span className="switch" data-on="true" />
            <span className="text-xs" style={{ flex: 1 }}>Auto-disable accounts after 90d inactivity</span>
          </div>
        </div>
      </div>
    </div>
  );
}
function ApiKeyInput({ defaultValue }) {
  const [reveal, setReveal] = useState(false);
  return (
    <div style={{ position: "relative", display: "flex" }}>
      <input className="input mono" defaultValue={defaultValue}
             type={reveal ? "text" : "password"}
             style={{ fontSize: 12, paddingRight: 80 }} />
      <div style={{ position: "absolute", right: 4, top: 4, display: "flex", gap: 2 }}>
        <button className="btn btn-ghost btn-icon btn-xs" onClick={() => setReveal(!reveal)} title={reveal ? "Hide" : "Reveal"}>
          {reveal ? <IcEyeOff size={11} /> : <IcEye size={11} />}
        </button>
        <button className="btn btn-ghost btn-icon btn-xs" title="Copy"><IcCopy size={11} /></button>
        <button className="btn btn-ghost btn-icon btn-xs" title="Rotate"><IcRefresh size={11} /></button>
      </div>
    </div>
  );
}

// ── API Keys & Quotas — workspace-wide usage + outgoing API keys ───────────
function SettingsApiKeys() {
  return (
    <div className="col" style={{ gap: 16 }}>
      {/* Workspace usage summary */}
      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)" }}>
        <Stat label="API calls today" value="14.2k" sub="↑ 8% vs yesterday" />
        <Stat label="Spend today" value="$24.18" sub="cap $30/day · 81% used" />
        <Stat label="Token throughput" value="2.1M/h" sub="P95 in TPM cap" />
        <Stat label="Rate limit hits" value="0" sub="Last 24h · all clear" />
      </div>

      {/* Outgoing API quota usage per provider */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Outgoing API quotas (per provider)</h3>
            <div className="card-desc">Real-time TPM / RPM utilization · alerts fire at 80% sustained</div>
          </div>
        </div>
        <div className="card-body card-body-tight">
          {[
            { p: "Azure OpenAI · gpt-5.5",     used_tpm: 100800, cap_tpm: 240000, rpm: 412,  rpm_cap: 600  },
            { p: "Azure OpenAI · embed-3-large", used_tpm: 217000, cap_tpm: 350000, rpm: 1240, rpm_cap: 2400 },
            { p: "Cohere · rerank-v4.0-pro",   used_tpm: 15500,  cap_tpm: 50000,  rpm: 84,   rpm_cap: 200  },
            { p: "Azure ACS · email",          used_tpm: 0,      cap_tpm: 100,    rpm: 2,    rpm_cap: 10,   unit: "emails" },
          ].map((q, i, arr) => {
            const tpmPct = q.used_tpm / q.cap_tpm;
            const rpmPct = q.rpm / q.rpm_cap;
            return (
              <div key={q.p} style={{ padding: "14px 18px", borderBottom: i < arr.length - 1 ? "1px solid oklch(var(--border))" : "none" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                  <span style={{ fontSize: 13, fontWeight: 500, flex: 1 }}>{q.p}</span>
                  <span className="badge badge-success"><span className="badge-dot" /> WITHIN LIMITS</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <QuotaBar label={q.unit ? "EMAILS / min" : "TPM"} used={q.used_tpm} cap={q.cap_tpm} pct={tpmPct} />
                  <QuotaBar label="RPM"   used={q.rpm}     cap={q.rpm_cap} pct={rpmPct} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Outgoing keys: workspace API keys to invite external systems */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Incoming API keys <span className="badge badge-muted" style={{ marginLeft: 4 }}>Tier 2</span></h3>
            <div className="card-desc">Issued to external applications that call EKP /query · per-key scoped to KB(s) + rate limit</div>
          </div>
          <button className="btn btn-secondary btn-sm" disabled><IcPlus size={13} /> Generate key</button>
        </div>
        <div className="card-body card-body-tight">
          <table className="table" style={{ opacity: 0.6 }}>
            <thead>
              <tr><th>Label</th><th>Key prefix</th><th>Scope</th><th>Rate limit</th><th className="col-num">Last used</th><th></th></tr>
            </thead>
            <tbody>
              {[
                ["Drive · self-service portal",  "ekp_sk_a7f4…",  "Drive Manuals (read)",         "100 RPM"],
                ["Sales reporting webhook",       "ekp_sk_b9e2…",  "Sales Playbooks (read)",       "20 RPM"],
                ["Internal slackbot",             "ekp_sk_c1f3…",  "All KBs (read)",               "200 RPM"],
              ].map(([l, k, s, r]) => (
                <tr key={l}>
                  <td>{l}</td><td className="col-mono">{k}</td><td>{s}</td><td className="col-mono">{r}</td><td className="col-num text-xs muted">—</td>
                  <td className="col-shrink"><button className="btn btn-ghost btn-icon btn-xs" disabled><IcMore size={13} /></button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ padding: "10px 16px", background: "oklch(var(--muted) / 0.3)", borderTop: "1px solid oklch(var(--border))", fontSize: 11, color: "oklch(var(--muted-foreground))", lineHeight: 1.5 }}>
            <IcShield size={11} style={{ verticalAlign: "-2px", marginRight: 4 }} />
            Tier 2 · API surface for external integrations. Tier 1 access is via the web UI only (MSAL SSO).
          </div>
        </div>
      </div>
    </div>
  );
}

function QuotaBar({ label, used, cap, pct }) {
  const color = pct > 0.8 ? "oklch(var(--destructive))" : pct > 0.5 ? "oklch(var(--warning))" : "oklch(var(--success))";
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
        <span className="text-xs muted mono" style={{ letterSpacing: "0.04em" }}>{label}</span>
        <span className="mono text-xs" style={{ fontWeight: 500 }}>
          {used.toLocaleString()} / {cap.toLocaleString()} <span className="muted">({(pct * 100).toFixed(0)}%)</span>
        </span>
      </div>
      <div style={{ height: 5, background: "oklch(var(--muted))", borderRadius: 999, overflow: "hidden" }}>
        <div style={{ width: `${Math.min(100, pct * 100)}%`, height: "100%", background: color, borderRadius: 999 }} />
      </div>
    </div>
  );
}

function SettingsAccount() {
  return (
    <div className="col" style={{ gap: 16 }}>
      <div className="card">
        <div className="card-header"><h3 className="card-title">Session</h3></div>
        <div className="card-body">
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> Rotate session token</button>
            <button className="btn btn-secondary btn-sm"><IcDownload size={13} /> Export my data</button>
            <div className="spacer" />
            <button className="btn btn-destructive btn-sm"><IcX size={13} /> Sign out</button>
          </div>
          <div className="text-xs muted mono" style={{ marginTop: 12, lineHeight: 1.55, padding: "10px 12px", background: "oklch(var(--muted) / 0.4)", borderRadius: "var(--radius-sm)" }}>
            Active session · MSAL Entra ID SSO<br />
            httpOnly cookie · 7-day TTL · CSRF double-submit (ADR-0022)<br />
            Last refresh 2026-05-15 08:42 UTC
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><h3 className="card-title">Danger zone</h3></div>
        <div className="card-body" style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-destructive btn-sm" disabled><IcTrash size={13} /> Delete account <span className="badge badge-muted" style={{ marginLeft: 6 }}>Tier 2</span></button>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, sub }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-meta">{sub}</div>
    </div>
  );
}

window.PageSettingsRich = PageSettingsRich;

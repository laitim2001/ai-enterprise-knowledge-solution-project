// ekp-page-misc.jsx — /kb/[id]/upload (3-step Pipeline Wizard) + /settings + /login

// ── /kb/[id]/upload — Pipeline Wizard per §5.5.3 ────────────────────────────
function PageUploadWizard({ kbId, onNavigate }) {
  const kb = window.MOCK_KBS.find((k) => k.kb_id === kbId) || window.MOCK_KBS[0];
  const [step, setStep] = useState(0);

  const steps = [
    { id: 0, label: "Data source",         hint: "Pick where docs come from" },
    { id: 1, label: "Document processing", hint: "Chunker + embedder" },
    { id: 2, label: "Execute",             hint: "Index + monitor progress" },
  ];

  return (
    <div className="content">
      <div className="content-narrow">
        <div className="page-header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <button className="btn btn-ghost btn-xs btn-ghost-muted" onClick={() => onNavigate("kb-detail", { kbId: kb.kb_id })}>
                <IcChevLeft size={12} /> {kb.name}
              </button>
            </div>
            <h1 className="page-title">Upload documents</h1>
            <p className="page-subtitle">Add documents to <span className="mono">{kb.index_name}</span>. New chunks are embedded with <span className="mono">text-embedding-3-large</span> (1024d) and upserted to Azure AI Search.</p>
          </div>
        </div>

        {/* Step indicator */}
        <div className="card" style={{ marginBottom: 16, overflow: "visible" }}>
          <div style={{ display: "flex", padding: "18px 24px", alignItems: "center", gap: 12 }}>
            {steps.map((s, i) => (
              <React.Fragment key={s.id}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, cursor: "default" }} onClick={() => setStep(s.id)}>
                  <div style={{
                    width: 28, height: 28, borderRadius: "50%",
                    background: step >= s.id ? "oklch(var(--primary))" : "oklch(var(--muted))",
                    color: step >= s.id ? "oklch(var(--primary-foreground))" : "oklch(var(--muted-foreground))",
                    display: "grid", placeItems: "center",
                    fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: 12,
                    border: step === s.id ? "2px solid oklch(var(--accent))" : "0",
                    transition: "all 0.2s",
                  }}>
                    {step > s.id ? <IcCheck size={14} /> : i + 1}
                  </div>
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: step === s.id ? 600 : 500, letterSpacing: "-0.005em" }}>
                      {s.label}
                    </div>
                    <div className="text-xs muted">{s.hint}</div>
                  </div>
                </div>
                {i < steps.length - 1 && (
                  <div style={{ flex: 1, height: 1, background: step > i ? "oklch(var(--foreground))" : "oklch(var(--border))", margin: "0 4px" }} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {step === 0 && <StepDataSource onNext={() => setStep(1)} />}
        {step === 1 && <StepDocumentProcessing kb={kb} onBack={() => setStep(0)} onNext={() => setStep(2)} />}
        {step === 2 && <StepExecute kb={kb} onBack={() => setStep(1)} onDone={() => onNavigate("kb-detail", { kbId: kb.kb_id })} />}
      </div>
    </div>
  );
}

function StepDataSource({ onNext }) {
  const [source, setSource] = useState("upload");
  const sources = [
    { id: "upload",     label: "Local files",   hint: ".docx, .pdf, .pptx · Drag & drop", icon: IcUpload, ready: true },
    { id: "sharepoint", label: "SharePoint",    hint: "OAuth-connected sites & libraries", icon: IcCloud, ready: true },
    { id: "drive",      label: "Drive folder",  hint: "Mounted share folder · network path", icon: IcGlobe, ready: true },
    { id: "url",        label: "URL crawler",   hint: "Tier 2 — disabled",                  icon: IcLink, ready: false },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Data source</h3>
      </div>
      <div className="card-body">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 20 }}>
          {sources.map((s) => {
            const Ic = s.icon;
            const active = source === s.id;
            return (
              <div key={s.id} onClick={() => s.ready && setSource(s.id)}
                   style={{
                     border: `1px solid ${active ? "oklch(var(--accent))" : "oklch(var(--border))"}`,
                     background: active ? "oklch(var(--accent) / 0.05)" : "oklch(var(--card))",
                     padding: "14px 16px",
                     borderRadius: "var(--radius-md)",
                     display: "flex",
                     gap: 12,
                     alignItems: "flex-start",
                     opacity: s.ready ? 1 : 0.5,
                     cursor: "default",
                     transition: "border-color 0.15s",
                   }}>
                <div style={{
                  width: 32, height: 32,
                  borderRadius: "var(--radius-sm)",
                  background: active ? "oklch(var(--accent) / 0.15)" : "oklch(var(--muted))",
                  color: active ? "oklch(var(--accent))" : "oklch(var(--foreground))",
                  display: "grid", placeItems: "center",
                  flexShrink: 0,
                }}>
                  <Ic size={16} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontWeight: 500 }}>{s.label}</span>
                    {!s.ready && <span className="badge badge-muted">SOON</span>}
                  </div>
                  <div className="text-xs muted" style={{ marginTop: 2 }}>{s.hint}</div>
                </div>
              </div>
            );
          })}
        </div>

        {source === "upload" && (
          <div style={{
            border: "2px dashed oklch(var(--border-strong))",
            borderRadius: "var(--radius-md)",
            padding: "40px 24px",
            textAlign: "center",
            background: "oklch(var(--muted) / 0.3)",
          }}>
            <div style={{ display: "inline-flex", padding: 12, borderRadius: "50%", background: "oklch(var(--accent) / 0.1)", color: "oklch(var(--accent))", marginBottom: 12 }}>
              <IcUpload size={24} />
            </div>
            <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>Drag and drop documents here</div>
            <div className="text-sm muted">or click to browse — up to 100 files, 50 MB each</div>
            <div className="text-xs muted mono" style={{ marginTop: 14 }}>Accepted: .docx · .pdf · .pptx</div>
          </div>
        )}

        {source === "sharepoint" && (
          <div style={{ padding: 24, textAlign: "center", border: "1px solid oklch(var(--border))", borderRadius: "var(--radius-md)" }}>
            <div className="text-sm">
              <b>SharePoint site URL</b><br />
              <input className="input mono" style={{ marginTop: 8, maxWidth: 480 }}
                     placeholder="https://ricoh.sharepoint.com/sites/D365-Docs" />
            </div>
            <div className="text-xs muted" style={{ marginTop: 10 }}>OAuth via Entra ID · scoped read-only</div>
          </div>
        )}
      </div>
      <div className="card-footer">
        <div className="text-xs muted mono">Step 1 of 3</div>
        <button className="btn btn-primary btn-sm" onClick={onNext}>Continue <IcChevRight size={13} /></button>
      </div>
    </div>
  );
}

function StepDocumentProcessing({ kb, onBack, onNext }) {
  const [chunkStrategy, setChunkStrategy] = useState(kb.config.chunk_strategy);
  const [chunkSize, setChunkSize] = useState(800);
  const [chunkOverlap, setChunkOverlap] = useState(100);

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Document processing</h3>
        <span className="text-xs muted">Override per-batch · KB defaults shown</span>
      </div>
      <div className="card-body">
        <div className="field">
          <label className="label">Chunk strategy</label>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {[
              { id: "heading_aware", label: "Heading-aware", hint: "Splits at H1/H2/H3 — for narrative docs" },
              { id: "layout_aware",  label: "Layout-aware",  hint: "Docling — preserves tables, lists, sections" },
              { id: "slide_based",   label: "Slide-based",   hint: "python-pptx — one chunk per slide" },
              { id: "auto",          label: "Auto",          hint: "Detect doc type, pick strategy" },
            ].map((s) => {
              const active = chunkStrategy === s.id;
              return (
                <div key={s.id} onClick={() => setChunkStrategy(s.id)}
                     style={{
                       border: `1px solid ${active ? "oklch(var(--foreground))" : "oklch(var(--border))"}`,
                       background: active ? "oklch(var(--muted) / 0.6)" : "transparent",
                       padding: "10px 14px", borderRadius: "var(--radius-sm)",
                       cursor: "default",
                     }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ fontWeight: 500, fontSize: 13.5 }}>{s.label}</span>
                    {active && <IcCheck size={12} />}
                  </div>
                  <div className="text-xs muted" style={{ marginTop: 2 }}>{s.hint}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div className="field">
            <label className="label">Chunk size (tokens)</label>
            <input className="input mono" value={chunkSize} onChange={(e) => setChunkSize(+e.target.value)} />
            <div className="hint">Effective max: 800 — fits within text-embedding-3-large 8k window</div>
          </div>
          <div className="field">
            <label className="label">Overlap (tokens)</label>
            <input className="input mono" value={chunkOverlap} onChange={(e) => setChunkOverlap(+e.target.value)} />
            <div className="hint">Recommended: 100–150 for layout_aware</div>
          </div>
        </div>

        <div className="field">
          <label className="label">Embedding model <span className="text-xs muted">— KB-locked</span></label>
          <select className="select" disabled>
            <option>text-embedding-3-large · 1024d MRL truncate</option>
          </select>
        </div>

        <div className="row" style={{ gap: 8, marginTop: 8 }}>
          <span className="switch" data-on="true" />
          <div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>Extract embedded screenshots</div>
            <div className="text-xs muted">Maps images via <span className="mono">embedded_images[]</span> + screenshot pipeline</div>
          </div>
        </div>
      </div>
      <div className="card-footer">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>← Back</button>
        <button className="btn btn-primary btn-sm" onClick={onNext}>Continue <IcChevRight size={13} /></button>
      </div>
    </div>
  );
}

// W77 / ADR-0056 層 A 段③ — L1 上載偵測 label(自動分類即時回饋)。
const UPLOAD_PROFILE_LABELS = {
  P1_sop_imgdense: "P1 圖密SOP", P1_sop_text: "P1 文字SOP", P2_prose: "P2 散文",
  P3_slide_imgdense: "P3 圖密簡報", P3_slide_text: "P3 文字簡報",
  P4_scan_imgdense: "P4 掃描", P5_form: "P5 表單",
};
function StepExecute({ kb, onBack, onDone }) {
  const [running, setRunning] = useState(true);
  const docs = window.MOCK_DOCUMENTS.slice(0, 6);

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Execute · indexing</h3>
          <div className="card-desc">Pipeline running · 4 of 6 documents complete</div>
        </div>
        <span className="badge badge-info"><span className="badge-dot" /> RUNNING</span>
      </div>
      <div className="card-body">
        <div className="banner banner-info" style={{ marginBottom: 16 }}>
          <span className="spinner" />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500 }}>Indexing 6 documents · 4 complete · 1 in progress · 1 failed</div>
            <div className="text-xs muted mono">Docling → layout_aware (800/100) → embed-3-large → ekp-kb-{kb.kb_id}-v1 upsert</div>
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 14, fontWeight: 600 }}>67%</div>
        </div>

        {/* W77 / ADR-0056 段③ — L1 自動文件分類即時回饋 */}
        <div className="banner banner-info" style={{ marginBottom: 16 }}>
          <IcLayers size={15} style={{ color: "oklch(var(--info))", flexShrink: 0 }} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13 }}><b>自動文件分類(W72 profiler)</b> — ingest 時偵測每份文件 profile,自動套對應 recall preset。</div>
            <div className="text-xs muted" style={{ marginTop: 2 }}>偵測錯可去文件詳情頁一鍵覆寫 · ADR-0056 層 A</div>
          </div>
        </div>

        <div className="col" style={{ gap: 6 }}>
          {docs.map((d, i) => {
            const statuses = ["indexed", "indexed", "indexed", "indexed", "indexing", "failed"];
            const progresses = [1, 1, 1, 1, 0.62, 0];
            const status = statuses[i];
            return (
              <div key={d.doc_id} style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "10px 14px",
                border: "1px solid oklch(var(--border))",
                borderRadius: "var(--radius-sm)",
                background: status === "failed" ? "oklch(var(--destructive) / 0.04)" : "oklch(var(--card))",
              }}>
                <span className={`status-dot ${status === "indexed" ? "ready" : status === "indexing" ? "indexing" : "failed"}`} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{d.title}</div>
                  {status === "indexed" && d.profile && (
                    <div className="text-xs muted" style={{ marginTop: 3, display: "flex", alignItems: "center", gap: 5, flexWrap: "wrap" }}>
                      <span className="badge badge-muted" style={{ fontSize: 9 }}><span className="badge-dot" /> {UPLOAD_PROFILE_LABELS[d.profile.profile] || d.profile.profile}</span>
                      偵測信心 {Math.round(d.profile.confidence * 100)}% · 已自動套對應 preset
                    </div>
                  )}
                  {status === "indexing" && (
                    <div style={{ marginTop: 4 }}>
                      <div className="progress accent" style={{ height: 3 }}>
                        <i style={{ width: `${progresses[i] * 100}%` }} />
                      </div>
                      <div className="text-xs muted mono" style={{ marginTop: 3 }}>Embedding chunk 28 of 38 · ~12s remaining</div>
                    </div>
                  )}
                  {status === "failed" && (
                    <div className="text-xs" style={{ color: "oklch(var(--destructive))", marginTop: 2 }}>
                      PPTX layout extraction failed — slide 47 contains nested SmartArt
                    </div>
                  )}
                </div>
                <span className="text-xs mono muted">{d.chunks || "—"} chunks</span>
                <span className={`badge ${status === "indexed" ? "badge-success" : status === "indexing" ? "badge-info" : "badge-error"}`}>
                  <span className="badge-dot" /> {status.toUpperCase()}
                </span>
              </div>
            );
          })}
        </div>
      </div>
      <div className="card-footer">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>← Back</button>
        <button className="btn btn-secondary btn-sm" onClick={onDone}>Continue in background</button>
      </div>
    </div>
  );
}

// ── /settings — thin per ADR-0024 W18 closeout: profile + theme + sign-out ─
function PageSettings({ theme, onToggleTheme }) {
  return (
    <div className="content">
      <div className="content-narrow" style={{ maxWidth: 720 }}>
        <div className="page-header">
          <div>
            <h1 className="page-title">Settings</h1>
            <p className="page-subtitle">Profile, theme, and account. Workspace-level configuration lives under each KB's Settings tab.</p>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header"><h3 className="card-title">Profile</h3></div>
          <div className="card-body" style={{ display: "flex", gap: 16, alignItems: "center" }}>
            <div className="avatar avatar-lg">CL</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 600 }}>Chris Lai</div>
              <div className="text-sm muted">chris.lai@ricoh.com · Workspace Admin</div>
              <div className="text-xs muted mono" style={{ marginTop: 4 }}>Entra ID SSO · MSAL session active</div>
            </div>
            <button className="btn btn-secondary btn-sm" disabled>Edit profile <span className="badge badge-muted" style={{ marginLeft: 6 }}>Tier 2</span></button>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header"><h3 className="card-title">Appearance</h3></div>
          <div className="card-body">
            <div className="row" style={{ padding: "4px 0" }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 500, fontSize: 13.5 }}>Theme</div>
                <div className="text-xs muted">Switches the entire app between Warm Charcoal (light) and Warm Neutral Dark (dark) palette</div>
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
                <div className="text-xs muted">JP / ZH support is Tier 2 — disabled affordance per ADR-0024</div>
              </div>
              <select className="select" disabled>
                <option>English</option>
              </select>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3 className="card-title">Account</h3></div>
          <div className="card-body" style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> Rotate session</button>
            <div className="spacer" />
            <button className="btn btn-destructive btn-sm"><IcX size={13} /> Sign out</button>
          </div>
        </div>

        <div style={{ marginTop: 24, padding: "12px 16px", border: "1px dashed oklch(var(--border-strong))", borderRadius: "var(--radius-sm)", fontSize: 12, color: "oklch(var(--muted-foreground))", lineHeight: 1.6 }}>
          <b style={{ color: "oklch(var(--foreground))" }}>v1 scope</b> · Settings is intentionally thin (W18 closeout). Tier 2 will add billing, API keys, team management, notification routing, and audit log delegation.
        </div>
      </div>
    </div>
  );
}

window.PageUploadWizard = PageUploadWizard;
window.PageSettings = PageSettings;

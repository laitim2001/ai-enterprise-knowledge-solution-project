// ekp-page-kb.jsx — /kb (list) + /kb/[id] (detail with 5 tabs)
// Tabs: Documents / Chunks / Pipeline / Retrieval Testing / Settings

// ── /kb ─────────────────────────────────────────────────────────────────────
function PageKbList({ onNavigate, tweaks }) {
  const kbs = window.MOCK_KBS;
  const [view, setView] = useState("grid"); // grid | table

  return (
    <div className="content">
      <div className="content-wide">
        <div className="page-header">
          <div>
            <h1 className="page-title">Knowledge bases</h1>
            <p className="page-subtitle">
              Each KB is provisioned with its own Azure AI Search index (<span className="mono">ekp-kb-&lt;kb_id&gt;-v1</span>, 1024d HNSW) per ADR-0018.
            </p>
          </div>
          <div className="page-actions">
            <div className="seg">
              <button className="seg-btn" data-active={view === "grid"} onClick={() => setView("grid")}>
                <IcLayers size={13} /> Grid
              </button>
              <button className="seg-btn" data-active={view === "table"} onClick={() => setView("table")}>
                <IcFilter size={13} /> Table
              </button>
            </div>
            <button className="btn btn-secondary btn-sm"><IcDownload size={13} /> Export</button>
            <button className="btn btn-primary btn-sm" onClick={() => onNavigate("kb-new")}><IcPlus size={13} /> New KB</button>
          </div>
        </div>

        {/* Filter bar */}
        <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center" }}>
          <div className="input-search-wrap" style={{ flex: 1, maxWidth: 320 }}>
            <span className="icon-leading"><IcSearch size={14} /></span>
            <input className="input" placeholder="Filter by name, owner, tag…" />
          </div>
          <button className="btn btn-secondary btn-sm"><IcFilter size={13} /> Status: All</button>
          <button className="btn btn-secondary btn-sm"><IcTag size={13} /> Tag: Any</button>
          <div className="spacer" />
          <div className="text-xs muted mono">{kbs.length} KBs · {kbs.reduce((s, k) => s + k.total_documents, 0)} docs total</div>
        </div>

        {view === "grid" ? (
          <div className="kb-grid">
            {kbs.map((kb) => <KbCard key={kb.kb_id} kb={kb} onClick={() => onNavigate("kb-detail", { kbId: kb.kb_id })} />)}
          </div>
        ) : (
          <KbTable kbs={kbs} onNavigate={onNavigate} />
        )}
      </div>
    </div>
  );
}

function KbCard({ kb, onClick }) {
  return (
    <div className="kb-card" onClick={onClick}>
      <div className="kb-card-head">
        <div className="kb-icon"><IcDatabase size={18} /></div>
        {kb.status === "ready" ? (
          <span className="badge badge-success"><span className="badge-dot" /> READY</span>
        ) : (
          <span className="badge badge-info"><span className="badge-dot" /> INDEXING</span>
        )}
      </div>
      <div>
        <div className="kb-title">{kb.name}</div>
        <div className="kb-desc">{kb.description}</div>
      </div>
      {kb.status === "indexing" && (
        <div className="progress accent"><i style={{ width: `${kb.indexing_progress * 100}%` }} /></div>
      )}
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {kb.tags.map((t) => <span key={t} className="badge badge-muted">{t}</span>)}
      </div>
      <div className="kb-meta">
        <span><IcFile size={11} /> {kb.total_documents}</span>
        <span><IcLayers size={11} /> {kb.total_chunks.toLocaleString()}</span>
        <span><IcZap size={11} /> R@5 {(kb.recall_at_5 * 100).toFixed(0)}%</span>
        <span style={{ marginLeft: "auto" }}>{window.formatRelative(kb.last_indexed_at)}</span>
      </div>
    </div>
  );
}

function KbTable({ kbs, onNavigate }) {
  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Chunk strategy</th>
            <th className="col-num">Docs</th>
            <th className="col-num">Chunks</th>
            <th className="col-num">Storage</th>
            <th className="col-num">R@5</th>
            <th>Owner</th>
            <th className="col-num">Last indexed</th>
            <th className="col-shrink"></th>
          </tr>
        </thead>
        <tbody>
          {kbs.map((kb) => (
            <tr key={kb.kb_id} onClick={() => onNavigate("kb-detail", { kbId: kb.kb_id })}>
              <td>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <div className="kb-icon" style={{ width: 26, height: 26 }}><IcDatabase size={13} /></div>
                  <div>
                    <div className="table-row-link">{kb.name}</div>
                    <div className="text-xs muted mono">{kb.index_name}</div>
                  </div>
                </div>
              </td>
              <td>
                {kb.status === "ready"
                  ? <span className="badge badge-success"><span className="badge-dot" /> READY</span>
                  : <span className="badge badge-info"><span className="badge-dot" /> INDEXING {Math.round(kb.indexing_progress*100)}%</span>}
              </td>
              <td><span className="badge badge-muted">{kb.config.chunk_strategy}</span></td>
              <td className="col-num">{kb.total_documents}</td>
              <td className="col-num">{kb.total_chunks.toLocaleString()}</td>
              <td className="col-num">{kb.storage_size_mb.toFixed(1)} MB</td>
              <td className="col-num">{(kb.recall_at_5 * 100).toFixed(1)}%</td>
              <td>{kb.owner}</td>
              <td className="col-num text-xs">{window.formatRelative(kb.last_indexed_at)}</td>
              <td className="col-shrink"><button className="btn btn-ghost btn-icon btn-xs"><IcMore size={14} /></button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── /kb/[id] — Detail with 5 tabs ──────────────────────────────────────────
function PageKbDetail({ kbId, initialTab, onNavigate, tweaks }) {
  const kb = window.MOCK_KBS.find((k) => k.kb_id === kbId) || window.MOCK_KBS[0];
  const [tab, setTab] = useState(initialTab || "documents");

  const tabs = [
    { id: "documents",        label: "Documents",         icon: IcFile,     count: kb.total_documents },
    { id: "chunks",           label: "Chunks",            icon: IcLayers,   count: kb.total_chunks },
    { id: "images",           label: "Images",            icon: IcLayers,   count: kb.total_screenshots },
    { id: "chunking",         label: "Chunking Lab",      icon: IcZap },
    { id: "pipeline",         label: "Pipeline",          icon: IcZap },
    { id: "retrieval-test",   label: "Retrieval Testing", icon: IcSearch },
    { id: "access",           label: "Access",            icon: IcShield },
    { id: "settings",         label: "Settings",          icon: IcSettings },
  ];

  return (
    <div className="content">
      <div className="content-wide">
        <div className="page-header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
              <button className="btn btn-ghost btn-xs btn-ghost-muted" onClick={() => onNavigate("kb")}>
                <IcChevLeft size={12} /> Knowledge
              </button>
              <span className="text-xs muted mono">·</span>
              <span className="text-xs muted mono">{kb.index_name}</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h1 className="page-title">{kb.name}</h1>
              {kb.status === "ready"
                ? <span className="badge badge-success"><span className="badge-dot" /> READY</span>
                : <span className="badge badge-info"><span className="badge-dot" /> INDEXING {Math.round(kb.indexing_progress*100)}%</span>}
            </div>
            <p className="page-subtitle">{kb.description}</p>
          </div>
          <div className="page-actions">
            <button className="btn btn-secondary btn-sm"><IcSearch size={13} /> Retrieval test</button>
            <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> Re-index</button>
            <button className="btn btn-primary btn-sm" onClick={() => onNavigate("kb-upload", { kbId: kb.kb_id })}>
              <IcUpload size={13} /> Upload documents
            </button>
          </div>
        </div>

        {/* Indexing strip */}
        {kb.status === "indexing" && (
          <div className="banner banner-info">
            <span className="spinner" />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>Indexing in progress · {Math.round(kb.indexing_progress * 100)}% complete</div>
              <div className="text-xs muted mono">
                Pipeline: Docling extract → layout_aware chunker → text-embedding-3-large (1024d) → HNSW upsert
              </div>
            </div>
            <button className="btn btn-ghost btn-sm">View pipeline</button>
          </div>
        )}

        {kb.failed_documents.length > 0 && (
          <div className="banner banner-warning">
            <IcAlert size={16} style={{ color: "oklch(var(--warning))" }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>
                {kb.failed_documents.length} document{kb.failed_documents.length > 1 ? "s" : ""} failed to index
              </div>
              <div className="text-xs muted">Review parser errors below in the Documents tab → "failed" filter.</div>
            </div>
            <button className="btn btn-ghost btn-sm">View errors</button>
          </div>
        )}

        {/* Tabs */}
        <div className="tabs">
          {tabs.map((t) => {
            const Ic = t.icon;
            return (
              <div key={t.id} className="tab" data-active={tab === t.id} onClick={() => setTab(t.id)}>
                <Ic size={14} /> {t.label}
                {t.count != null && <span className="count">{t.count.toLocaleString()}</span>}
              </div>
            );
          })}
        </div>

        {tab === "documents"      && <TabDocuments kb={kb} tweaks={tweaks} onNavigate={onNavigate} />}
        {tab === "chunks"         && <TabChunks kb={kb} tweaks={tweaks} />}
        {tab === "images"         && <TabImages kb={kb} onNavigate={onNavigate} />}
        {tab === "chunking"       && <TabChunkingLab kb={kb} onNavigate={onNavigate} />}
        {tab === "pipeline"       && <TabPipeline kb={kb} onNavigate={onNavigate} />}
        {tab === "retrieval-test" && <TabRetrievalTesting kb={kb} tweaks={tweaks} />}
        {tab === "access"         && <TabKbAccess kb={kb} onNavigate={onNavigate} />}
        {tab === "settings"       && <TabKbSettings kb={kb} />}
      </div>
    </div>
  );
}

// ── Tab: Documents ──────────────────────────────────────────────────────────
function TabDocuments({ kb, tweaks, onNavigate }) {
  const docs = window.MOCK_DOCUMENTS;
  const [filter, setFilter] = useState("all"); // all | indexed | indexing | failed | queued
  const filtered = filter === "all" ? docs : docs.filter((d) => d.status === filter);
  const compact = tweaks.density === "compact";

  return (
    <div>
      <div style={{ display: "flex", gap: 8, marginBottom: 12, alignItems: "center" }}>
        <div className="input-search-wrap" style={{ flex: 1, maxWidth: 340 }}>
          <span className="icon-leading"><IcSearch size={14} /></span>
          <input className="input" placeholder="Search documents by title or doc_id…" />
        </div>
        <div className="seg">
          {["all", "indexed", "indexing", "failed", "queued"].map((f) => (
            <button key={f} className="seg-btn" data-active={filter === f} onClick={() => setFilter(f)}>
              {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
              <span className="text-xs mono" style={{ opacity: 0.6 }}>
                {f === "all" ? docs.length : docs.filter((d) => d.status === f).length}
              </span>
            </button>
          ))}
        </div>
        <div className="spacer" />
        <button className="btn btn-secondary btn-sm"><IcDownload size={13} /> Export CSV</button>
      </div>

      <div className="table-wrap">
        <table className="table" style={compact ? { fontSize: 12 } : undefined}>
          <thead>
            <tr>
              <th style={{ width: 26 }}><span className="kbd" style={{ padding: "0 4px" }}>☐</span></th>
              <th>Document</th>
              <th>Source</th>
              <th>Type</th>
              <th className="col-num">Size</th>
              <th className="col-num">Pages</th>
              <th className="col-num">Chunks</th>
              <th className="col-num">Images</th>
              <th>Chunker</th>
              <th>Status</th>
              <th className="col-num">Indexed</th>
              <th className="col-shrink"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((d) => (
              <tr key={d.doc_id} onClick={() => onNavigate && onNavigate("doc-detail", { kbId: kb.kb_id, docId: d.doc_id })} style={{ cursor: "default" }}>
                <td onClick={(e) => e.stopPropagation()}><span className="kbd" style={{ padding: "0 4px" }}>☐</span></td>
                <td style={{ maxWidth: 360 }}>
                  <div className="table-row-link" style={{ whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: "oklch(var(--accent))" }}>{d.title}</div>
                  <div className="text-xs muted mono">{d.doc_id}</div>
                  {d.status === "failed" && (
                    <div className="text-xs" style={{ color: "oklch(var(--destructive))", marginTop: 2, lineHeight: 1.4 }}>
                      {d.error}
                    </div>
                  )}
                </td>
                <td><span className="badge badge-muted">{d.source}</span></td>
                <td><span className="mono text-xs" style={{ textTransform: "uppercase" }}>{d.file_type}</span></td>
                <td className="col-num">{(d.size_kb / 1024).toFixed(1)} MB</td>
                <td className="col-num">{d.pages}</td>
                <td className="col-num">{d.chunks}</td>
                <td className="col-num">{d.screenshots ?? 0}</td>
                <td><span className="badge badge-muted">{d.chunk_strategy}</span></td>
                <td>
                  {d.status === "indexed"  && <span className="badge badge-success"><span className="badge-dot" /> INDEXED</span>}
                  {d.status === "indexing" && <span className="badge badge-info"><span className="badge-dot" /> {Math.round(d.indexing_progress*100)}%</span>}
                  {d.status === "failed"   && <span className="badge badge-error"><span className="badge-dot" /> FAILED</span>}
                  {d.status === "queued"   && <span className="badge badge-muted"><span className="badge-dot" /> QUEUED</span>}
                </td>
                <td className="col-num text-xs">{d.indexed_at ? window.formatRelative(d.indexed_at) : "—"}</td>
                <td className="col-shrink">
                  <button className="btn btn-ghost btn-icon btn-xs"><IcMore size={14} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12, fontSize: 12 }}>
        <div className="muted">Showing {filtered.length} of {docs.length}</div>
        <div className="row">
          <button className="btn btn-ghost btn-icon btn-xs" disabled><IcChevLeft size={13} /></button>
          <span className="mono text-xs">1 / 1</span>
          <button className="btn btn-ghost btn-icon btn-xs" disabled><IcChevRight size={13} /></button>
        </div>
      </div>
    </div>
  );
}

// ── Tab: Chunks ─────────────────────────────────────────────────────────────
function TabChunks({ kb, tweaks }) {
  const chunks = window.MOCK_CHUNKS;
  return (
    <div className="split-2">
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Browse chunks</h3>
            <div className="card-desc">{kb.total_chunks.toLocaleString()} chunks total</div>
          </div>
        </div>
        <div className="card-body card-body-tight" style={{ maxHeight: 540, overflowY: "auto" }}>
          {chunks.map((c, i) => (
            <div key={c.chunk_id} style={{ padding: "10px 16px", borderBottom: "1px solid oklch(var(--border))", cursor: "default" }}>
              <div className="text-xs mono muted" style={{ marginBottom: 2 }}>#{c.chunk_id}</div>
              <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 2 }}>{c.chunk_title}</div>
              <div className="section-path text-xs">
                {c.section_path.map((s, j) => <span key={j}>{s}</span>)}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Chunk preview</h3>
            <div className="card-desc"><span className="mono">{chunks[0].chunk_id}</span></div>
          </div>
          <div className="row">
            <button className="btn btn-ghost btn-icon btn-sm"><IcEdit size={14} /></button>
            <button className="btn btn-ghost btn-icon btn-sm"><IcCopy size={14} /></button>
            <button className="btn btn-ghost btn-icon btn-sm" style={{ color: "oklch(var(--destructive))" }}><IcTrash size={14} /></button>
          </div>
        </div>
        <div className="card-body">
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
            <span className="badge badge-muted">chunk_index <b style={{ marginLeft: 2 }}>{chunks[0].chunk_index}</b></span>
            <span className="badge badge-muted">tokens <b style={{ marginLeft: 2 }}>312</b></span>
            <span className="badge badge-accent">embedded_images <b style={{ marginLeft: 2 }}>{chunks[0].embedded_images}</b></span>
          </div>
          <div className="section-path text-sm" style={{ marginBottom: 14 }}>
            {chunks[0].section_path.map((s, j) => <span key={j}>{s}</span>)}
          </div>
          <div style={{ background: "oklch(var(--muted) / 0.4)", border: "1px solid oklch(var(--border))", borderRadius: "var(--radius-sm)", padding: "14px 16px", fontSize: 13.5, lineHeight: 1.65 }}>
            <h3 style={{ fontSize: 14, fontWeight: 600, marginTop: 0, marginBottom: 10 }}>{chunks[0].chunk_title}</h3>
            <p style={{ margin: 0 }}>
              When configuring posting definitions for multi-currency journals, the <b>exchange rate type</b> field must align with the legal entity's accounting currency. Failure to map this field triggers a posting validation error at month-end close. Reference Section 4.3 for the full validation matrix.
            </p>
            <p style={{ marginTop: 12 }}>
              Setup path: <span className="mono" style={{ background: "oklch(var(--background))", padding: "1px 4px", borderRadius: 3, border: "1px solid oklch(var(--border))" }}>General ledger &gt; Setup &gt; Posting &gt; Posting definitions</span>
            </p>
          </div>
        </div>
        <div className="card-footer">
          <div className="text-xs muted mono">embedding_model · text-embedding-3-large · 1024d MRL</div>
          <button className="btn btn-ghost btn-xs">View raw embedding →</button>
        </div>
      </div>
    </div>
  );
}

// ── Tab: Retrieval Testing — TIER 1 HIGHLIGHT (per ADR-0021 §5.5.4) ────────
function TabRetrievalTesting({ kb, tweaks }) {
  const [query, setQuery] = useState("How do I configure multi-currency posting definitions for inter-company journals in D365 F&O?");
  const [mode, setMode] = useState("hybrid"); // hybrid | vector | fulltext
  const [topK, setTopK] = useState(5);
  const [rerank, setRerank] = useState(true);
  const [scoreThreshold, setScoreThreshold] = useState(0.4);
  const [reranker, setReranker] = useState("cohere-v4.0-pro");
  const [hasResults, setHasResults] = useState(true);

  const result = {
    embed_latency_ms: 84,
    search_latency_ms: 134,
    rerank_latency_ms: 384,
    total_latency_ms: 602,
    total_hits: 14,
    chunks: window.MOCK_CHUNKS,
  };

  const vizMode = tweaks.retrievalViz || "bars"; // list | bars | heatmap

  return (
    <div className="split-2" style={{ gridTemplateColumns: "360px 1fr" }}>
      {/* Left: query builder */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Query</h3>
            <div className="card-desc">Pure retrieval pass · no LLM synthesis · ADR-0021</div>
          </div>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">Query</label>
            <textarea className="input" rows={4} value={query} onChange={(e) => setQuery(e.target.value)} />
          </div>

          <div className="field">
            <label className="label">Retrieval mode</label>
            <div className="seg" style={{ width: "100%" }}>
              {[
                { id: "hybrid", label: "Hybrid", hint: "BM25 + Vector + RRF" },
                { id: "vector", label: "Vector", hint: "Dense only" },
                { id: "fulltext", label: "Full-text", hint: "BM25 only" },
              ].map((m) => (
                <button key={m.id} className="seg-btn" data-active={mode === m.id} onClick={() => setMode(m.id)} style={{ flex: 1, flexDirection: "column", padding: "6px 8px", gap: 2 }}>
                  <span style={{ fontSize: 12.5, fontWeight: 600 }}>{m.label}</span>
                  <span className="text-xs muted" style={{ fontSize: 10 }}>{m.hint}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <label className="label">Top-K <span className="text-xs muted mono">retrieve before rerank</span></label>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <input type="range" min={1} max={50} value={topK} onChange={(e) => setTopK(+e.target.value)} style={{ flex: 1 }} />
              <span className="mono" style={{ width: 26, textAlign: "right", fontSize: 13 }}>{topK}</span>
            </div>
          </div>

          <div className="field">
            <label className="label">
              Score threshold
              <span className="text-xs muted mono" style={{ marginLeft: 6 }}>
                {mode === "fulltext" ? "n/a — BM25 unbounded" : "0.0 – 1.0"}
              </span>
            </label>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <input type="range" min={0} max={1} step={0.01} value={scoreThreshold} disabled={mode === "fulltext"}
                     onChange={(e) => setScoreThreshold(+e.target.value)} style={{ flex: 1 }} />
              <span className="mono" style={{ width: 38, textAlign: "right", fontSize: 13 }}>{scoreThreshold.toFixed(2)}</span>
            </div>
          </div>

          <div className="field" style={{ marginBottom: 8 }}>
            <label className="label">Reranker</label>
            <select className="select" value={reranker} onChange={(e) => setReranker(e.target.value)} disabled={!rerank}>
              <option value="cohere-v4.0-pro">cohere-v4.0-pro (production lock)</option>
              <option value="cohere-v3.5">cohere-v3.5 (baseline)</option>
              <option value="azure-semantic">azure-semantic</option>
              <option value="off">off</option>
            </select>
          </div>

          <div className="row" style={{ marginBottom: 16 }}>
            <span className="switch" data-on={rerank} onClick={() => setRerank(!rerank)} />
            <span style={{ fontSize: 13 }}>Apply rerank after retrieval</span>
          </div>

          <button className="btn btn-accent" style={{ width: "100%" }} onClick={() => setHasResults(true)}>
            <IcZap size={14} /> Run retrieval
          </button>

          <div className="hr" />

          <div className="text-xs muted mono" style={{ lineHeight: 1.6 }}>
            POST <span style={{ color: "oklch(var(--foreground))" }}>/kb/{kb.kb_id}/retrieval-test</span><br />
            mode = {mode}, top_k = {topK}, rerank = {rerank.toString()}<br />
            score_threshold = {scoreThreshold.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Right: results */}
      <div>
        {/* Latency strip */}
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-body" style={{ padding: 0 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)" }}>
              {[
                { label: "Embed", ms: result.embed_latency_ms },
                { label: "Search", ms: result.search_latency_ms },
                { label: "Rerank", ms: rerank ? result.rerank_latency_ms : 0 },
                { label: "Total", ms: result.total_latency_ms, bold: true },
                { label: "Hits", ms: result.total_hits, suffix: "" },
              ].map((m, i) => (
                <div key={i} style={{ padding: "14px 18px", borderRight: i < 4 ? "1px solid oklch(var(--border))" : "none" }}>
                  <div className="text-xs muted" style={{ marginBottom: 4 }}>{m.label}</div>
                  <div style={{ fontSize: 18, fontWeight: 600, fontVariantNumeric: "tabular-nums", fontFamily: "var(--font-sans)" }}>
                    {m.ms}{m.suffix ?? "ms"}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* RRF source lane explainer (Hybrid only) */}
        {mode === "hybrid" && (
          <div className="banner banner-info" style={{ marginBottom: 12 }}>
            <IcZap size={15} style={{ color: "oklch(var(--info))" }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13 }}>
                Hybrid: <b>BM25</b> top 10 + <b>Vector</b> top 10 → <b>RRF fusion</b> → <b>Cohere v4.0-pro</b> rerank.
              </div>
              <div className="text-xs muted mono" style={{ marginTop: 2 }}>
                Source chip on each chunk: <span className="badge badge-info" style={{ marginLeft: 4 }}>BM25</span> <span className="badge badge-accent" style={{ marginLeft: 4 }}>Vector</span> <span className="badge badge-success" style={{ marginLeft: 4 }}>BM25 + Vector</span>
              </div>
            </div>
          </div>
        )}

        {/* Result view selector */}
        <div className="row" style={{ marginBottom: 12, alignItems: "center" }}>
          <h3 className="card-title">Ranked chunks <span className="text-xs muted mono" style={{ marginLeft: 8 }}>{result.chunks.length} of {result.total_hits} (threshold)</span></h3>
          <div className="spacer" />
          <span className="text-xs muted">Visualization →</span>
          <div className="seg">
            <button className="seg-btn" data-active={vizMode === "list"} onClick={() => window.__setTweak?.("retrievalViz", "list")}>
              List
            </button>
            <button className="seg-btn" data-active={vizMode === "bars"} onClick={() => window.__setTweak?.("retrievalViz", "bars")}>
              Bars
            </button>
            <button className="seg-btn" data-active={vizMode === "heatmap"} onClick={() => window.__setTweak?.("retrievalViz", "heatmap")}>
              Heatmap
            </button>
          </div>
        </div>

        {vizMode === "heatmap" ? (
          <RetrievalHeatmap chunks={result.chunks} mode={mode} />
        ) : (
          <div className="col" style={{ gap: 10 }}>
            {result.chunks.map((c, i) => (
              <ChunkResult key={c.chunk_id} chunk={c} rank={i + 1} mode={mode} viz={vizMode} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ChunkResult({ chunk, rank, mode, viz }) {
  const sourceBadge = chunk.source === "BM25+Vector"
    ? <span className="badge badge-success" title="In both BM25 + Vector"><span className="badge-dot" /> BM25+Vector</span>
    : chunk.source === "BM25"
      ? <span className="badge badge-info"><span className="badge-dot" /> BM25 only</span>
      : <span className="badge badge-accent"><span className="badge-dot" /> Vector only</span>;

  return (
    <div className="chunk">
      <div className="chunk-head">
        <div className={`chunk-rank ${rank <= 3 ? "chunk-rank-top" : ""}`}>#{rank}</div>
        <div className="chunk-source">
          <IcFile size={13} />
          <span className="doc-title">{chunk.doc_title}</span>
        </div>
        <div className="chunk-score-wrap">
          {mode === "hybrid" && sourceBadge}
          {chunk.rerank_delta !== 0 && (
            <span className="badge" style={{
              background: chunk.rerank_delta > 0 ? "oklch(var(--success) / 0.12)" : "oklch(var(--destructive) / 0.1)",
              color: chunk.rerank_delta > 0 ? "oklch(var(--success))" : "oklch(var(--destructive))",
              border: 0,
            }}>
              {chunk.rerank_delta > 0 ? "▲" : "▼"} {Math.abs(chunk.rerank_delta)} rerank
            </span>
          )}
          {viz === "bars" && (
            <div className="score-bar" title={`score ${chunk.score.toFixed(4)}`}>
              <i style={{ width: `${chunk.score * 100}%` }} />
            </div>
          )}
          <span className="chunk-score">{chunk.score.toFixed(4)}</span>
        </div>
      </div>
      <div className="section-path">
        {chunk.section_path.map((s, j) => <span key={j}>{s}</span>)}
      </div>
      <div className="chunk-body" dangerouslySetInnerHTML={{ __html: chunk.chunk_text_preview.replace(/\*\*(.+?)\*\*/g, "<mark>$1</mark>") }} />
      <div className="chunk-foot">
        <span>chunk_id <span style={{ color: "oklch(var(--foreground))" }}>{chunk.chunk_id}</span></span>
        <span>chunk_index <span style={{ color: "oklch(var(--foreground))" }}>#{chunk.chunk_index}</span></span>
        {chunk.embedded_images > 0 && <span>📎 {chunk.embedded_images} image{chunk.embedded_images > 1 ? "s" : ""} embedded</span>}
        <span style={{ marginLeft: "auto" }}>
          <button className="btn btn-ghost btn-xs">View full chunk →</button>
        </span>
      </div>
    </div>
  );
}

function RetrievalHeatmap({ chunks, mode }) {
  // Synthetic data: each row = chunk, columns = retrievers (BM25 / Vector / RRF / Rerank)
  const cols = mode === "hybrid"
    ? ["BM25", "Vector", "RRF", "Rerank"]
    : mode === "vector"
      ? ["Vector", "Rerank"]
      : ["BM25", "Rerank"];

  // Each cell: synthetic rank in that retriever
  const synthRanks = [
    [2, 1, 1, 1],
    [4, 3, 2, 2],
    [1, 6, 3, 3],
    [7, 2, 4, 4],
    [5, 5, 5, 5],
  ];

  return (
    <div className="card">
      <div className="card-body" style={{ overflowX: "auto" }}>
        <table className="table" style={{ tableLayout: "fixed" }}>
          <thead>
            <tr>
              <th style={{ width: "40%" }}>Chunk</th>
              {cols.map((c) => <th key={c} className="col-num">{c}</th>)}
              <th className="col-num">Final</th>
            </tr>
          </thead>
          <tbody>
            {chunks.map((c, i) => (
              <tr key={c.chunk_id}>
                <td>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{c.chunk_title}</div>
                  <div className="text-xs muted mono">{c.doc_id} · #{c.chunk_index}</div>
                </td>
                {cols.map((col, j) => {
                  const rank = synthRanks[i]?.[j] ?? "—";
                  const intensity = rank === "—" ? 0 : Math.max(0, 1 - (rank - 1) / 8);
                  return (
                    <td key={col} className="col-num">
                      <div style={{
                        display: "inline-block",
                        width: 36, height: 22, lineHeight: "22px",
                        textAlign: "center",
                        background: `oklch(var(--accent) / ${intensity * 0.4 + 0.05})`,
                        color: intensity > 0.6 ? "oklch(var(--accent))" : "oklch(var(--foreground))",
                        border: "1px solid oklch(var(--accent) / 0.2)",
                        borderRadius: 4,
                        fontFamily: "var(--font-mono)", fontSize: 11.5, fontWeight: 600,
                      }}>
                        {rank}
                      </div>
                    </td>
                  );
                })}
                <td className="col-num">
                  <span className="chunk-score">{c.score.toFixed(3)}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Tab: Pipeline ───────────────────────────────────────────────────────────
function TabPipeline({ kb, onNavigate }) {
  const stages = [
    { name: "1. Source ingestion",     desc: "SharePoint / Drive / share folder",                          status: "ok", duration: "—" },
    { name: "2. Document extraction",  desc: "Docling (PDF + DOCX) · python-pptx (slide_based)",          status: "ok", duration: "avg 8s/doc" },
    { name: "3. Chunking",             desc: `${kb.config.chunk_strategy} · 800 tokens · 100 overlap`,    status: "ok", duration: "avg 1s/doc" },
    { name: "4. Embedding",            desc: "Azure OpenAI text-embedding-3-large · 1024d MRL truncate", status: "ok", duration: "avg 0.4s/chunk" },
    { name: "5. Index upsert",         desc: `${kb.index_name} · HNSW vector + BM25 lexical`,            status: "ok", duration: "avg 0.1s/chunk" },
    { name: "6. Eval suite (nightly)", desc: "RAGAs 4-metric · 184-q eval set",                          status: "ok", duration: "ran 14:17 today" },
  ];
  return (
    <div>
      <div className="banner banner-success" style={{ marginBottom: 16 }}>
        <IcCheck size={15} style={{ color: "oklch(var(--success))" }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 500 }}>Pipeline healthy</div>
          <div className="text-xs muted">All stages running within SLOs · last full re-index 7 days ago</div>
        </div>
        <button className="btn btn-secondary btn-sm">Trigger full re-index</button>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Indexing pipeline</h3>
          <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("kb-upload", { kbId: kb.kb_id })}>
            <IcUpload size={13} /> Add documents
          </button>
        </div>
        <div className="card-body card-body-tight">
          {stages.map((s, i) => (
            <div key={s.name} style={{ display: "flex", gap: 16, padding: "16px 20px", borderBottom: i < stages.length - 1 ? "1px solid oklch(var(--border))" : "none" }}>
              <div style={{ flexShrink: 0 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "var(--radius-sm)",
                  background: "oklch(var(--accent) / 0.1)", color: "oklch(var(--accent))",
                  display: "grid", placeItems: "center", fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: 13,
                }}>
                  {i + 1}
                </div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontWeight: 500 }}>{s.name}</span>
                  <span className="badge badge-success"><span className="badge-dot" /> OK</span>
                </div>
                <div className="text-sm muted mono" style={{ marginTop: 2 }}>{s.desc}</div>
              </div>
              <div className="text-xs muted mono">{s.duration}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Tab: KB Settings ────────────────────────────────────────────────────────
function TabKbSettings({ kb }) {
  const [showReindexExplainer, setShowReindexExplainer] = useState(false);
  // W46 (ADR-0042 + ADR-0043) — chunk_strategy + per-KB image cap are now editable.
  // Both are INGEST-time params, so a change only takes effect after a re-index.
  const [chunkStrategy, setChunkStrategy] = useState(kb.config.chunk_strategy);
  const [maxImages, setMaxImages] = useState(""); // "" = 繼承全域 (8); else per-KB cap
  const [showReindexModal, setShowReindexModal] = useState(false);
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">General</h3>
          <span className="badge badge-success"><IcEdit size={10} /> Editable</span>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">Name</label>
            <input className="input" defaultValue={kb.name} />
            <div className="hint">PATCH /kb/{kb.kb_id} · KbMetadataPatch.name</div>
          </div>
          <div className="field">
            <label className="label">Description</label>
            <textarea className="input" rows={3} defaultValue={kb.description} />
          </div>
          <div className="field">
            <label className="label">kb_id <IcShield size={11} style={{ verticalAlign: "-2px", marginLeft: 4, color: "oklch(var(--warning))" }} /></label>
            <input className="input mono" disabled value={kb.kb_id} />
            <div className="hint">
              <b style={{ color: "oklch(var(--warning))" }}>Locked.</b> Forms index <span className="mono">{kb.index_name}</span> · cannot be changed without recreating the KB.
            </div>
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <div className="spacer" />
            <button className="btn btn-secondary btn-sm">Cancel</button>
            <button className="btn btn-primary btn-sm">Save changes</button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Retrieval config</h3>
          <span className="badge badge-warning"><IcShield size={10} /> Mix of locked + editable</span>
        </div>
        <div className="card-body">
          <div className="field">
            <label className="label">Embedding model <IcShield size={11} style={{ verticalAlign: "-2px", marginLeft: 4, color: "oklch(var(--warning))" }} /></label>
            <select className="select" defaultValue={kb.config.embedding_model} disabled>
              <option>text-embedding-3-large</option>
            </select>
            <div className="hint">
              <b style={{ color: "oklch(var(--warning))" }}>Locked.</b> 1024d MRL truncate · changing requires full re-index.
            </div>
          </div>
          <div className="field">
            <label className="label">Chunk strategy <IcRefresh size={11} style={{ verticalAlign: "-2px", marginLeft: 4, color: "oklch(var(--warning))" }} /></label>
            <div className="seg" style={{ width: "100%" }}>
              {["heading_aware", "layout_aware", "slide_based", "auto"].map((s) => (
                <button key={s} className="seg-btn" data-active={chunkStrategy === s} onClick={() => setChunkStrategy(s)} style={{ flex: 1, padding: "5px 6px", fontSize: 11.5 }}>{s}</button>
              ))}
            </div>
            <div className="hint">
              <b style={{ color: "oklch(var(--warning))" }}>需重新索引。</b> 改變切分策略 → 影響 chunk 邊界,儲存後須 re-index 全部文件先生效。
            </div>
          </div>
          <div className="field">
            <label className="label">Max images / chunk <IcRefresh size={11} style={{ verticalAlign: "-2px", marginLeft: 4, color: "oklch(var(--warning))" }} /></label>
            <input className="input mono" value={maxImages} placeholder="繼承全域 (8)" onChange={(e) => setMaxImages(e.target.value)} />
            <div className="hint">
              <b style={{ color: "oklch(var(--warning))" }}>需重新索引。</b> 留空 = 沿用全域上限(8)。每 chunk 圖片數上限,超過即 force-split(ADR-0042)。
            </div>
          </div>
          <div className="field">
            <label className="label">Default top_k (retrieval) <IcEdit size={10} style={{ verticalAlign: "-1px", marginLeft: 4, color: "oklch(var(--success))" }} /></label>
            <input className="input mono" defaultValue={kb.config.default_top_k} />
            <div className="hint">Editable any time · doesn't require re-index</div>
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Default rerank_k <IcEdit size={10} style={{ verticalAlign: "-1px", marginLeft: 4, color: "oklch(var(--success))" }} /></label>
            <input className="input mono" defaultValue={kb.config.default_rerank_k} />
          </div>
        </div>
      </div>

      {/* W43 — Per-KB advanced retrieval tuning (ADR-0040). 12 runtime knobs.
          null = inherit global; set = per-KB override. All runtime → no re-index.
          Grouped 檢索 / 引用 / 圖片. See backend KbConfig + EffectiveConfig resolver. */}
      <div className="card" style={{ gridColumn: "1 / -1" }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">Advanced retrieval tuning</h3>
            <div className="card-desc">
              Per-KB 覆寫檢索 / 引用 / 圖片行為。未覆寫嘅旋鈕沿用全域預設(Settings)。
              全部 runtime — <b>唔需要重新索引</b>(對比上面鎖定嘅 embedding / chunk strategy)。
            </div>
          </div>
          <span className="badge badge-info" style={{ fontSize: 9.5 }}><IcEdit size={10} /> Runtime · no re-index</span>
        </div>
        <div className="card-body" style={{ display: "grid", gap: 12 }}>
          <KbTuneGroup icon={IcLayers} title="Parent-document retrieval" enabled enabledInherit
            desc="把命中嘅子 chunk 擴展到所屬父段落,畀 LLM 更完整上下文。">
            <KbTuneKnob label="Section depth offset" inherit globalValue="1" />
            <KbTuneKnob label="Parent top_k" inherit globalValue="3" />
            <KbTuneKnob label="Max tokens / parent" inherit globalValue="1500" />
          </KbTuneGroup>

          <KbTuneGroup icon={IcLink} title="Citation post-hoc expansion" enabled enabledInherit
            desc="答案生成後,為每個引用補充鄰近輔助 chunk,提升完整性(Finding #1 5/5 解法)。">
            <KbTuneKnob label="Max aux / citation" inherit globalValue="10" />
            <KbTuneKnob label="Expansion window" inherit globalValue="1" />
            <KbTuneKnob label="Section path prefix depth" inherit globalValue="1" />
          </KbTuneGroup>

          <KbTuneGroup icon={IcEye} title="Citation neighbour images + 圖片上限" enabled enabledInherit
            desc="控制引用鄰近圖片帶入,同每個答案最多顯示幾多張圖(圖洪水收斂)。">
            <KbTuneKnob label="Neighbour max aux images" inherit globalValue="4" />
            <KbTuneKnob label="Neighbour prefix depth" inherit globalValue="1" />
            {/* 已覆寫示範:此 AR KB set max_images_per_answer = 8(per Finding #8 standing config) */}
            <KbTuneKnob label="Max images / answer" globalValue="—(無上限)" value="8" />
          </KbTuneGroup>
        </div>
        <div className="card-footer">
          <div className="text-xs muted">配置 scope:per-query &gt; <b>per-KB(此頁)</b> &gt; 全域 · ADR-0040</div>
          <div className="row">
            <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> 還原全部至全域</button>
            <button className="btn btn-primary btn-sm">儲存到此 KB</button>
          </div>
        </div>
      </div>

      {/* W43 — Config test-run panel (config-test harness, ADR-0040 §Decision 3).
          唔改全域 / 已存配置,經 PerQueryOverrides 把上面草稿注入同一條 pipeline 試跑。 */}
      <div className="card" style={{ gridColumn: "1 / -1" }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <IcZap size={14} style={{ verticalAlign: "-2px", marginRight: 6, color: "oklch(var(--accent))" }} />
              試跑(config-test)
            </h3>
            <div className="card-desc">
              唔改全域、唔改已存配置,試吓上面草稿配置喺真 pipeline 嘅效果。
              <span className="mono"> POST /kb/{kb.kb_id}/config-test</span>
            </div>
          </div>
        </div>
        <div className="card-body">
          {/* control row */}
          <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 16 }}>
            <div className="field" style={{ flex: 1, minWidth: 240, marginBottom: 0 }}>
              <label className="label">測試問題</label>
              <input className="input" defaultValue="How do I configure the address book sync?" />
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label">重跑次數</label>
              <div className="seg">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} className="seg-btn" data-active={n === 3} style={{ minWidth: 34 }}>{n}</button>
                ))}
              </div>
            </div>
            <label className="row" style={{ gap: 6, fontSize: 12.5, alignItems: "center", cursor: "pointer", paddingBottom: 8 }}>
              <span className="switch" data-on /> 同已存配置對照(A/B)
            </label>
            <button className="btn btn-primary"><IcZap size={14} /> 試跑</button>
          </div>

          {/* results A/B — DRAFT (保守草稿) vs SAVED (已存激進) ; 數字 = F2.6 dogfood */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <KbTestResultCard label="草稿配置(DRAFT)" accent
              cit="1" citBand="0" imgRaw="6" imgDedup="6" imgBand="0" lat="4.1s" chars="612" refused="否" />
            <KbTestResultCard label="已存配置(SAVED)"
              cit="11" citBand="0" imgRaw="36" imgDedup="28.7" imgBand="0" lat="5.8s" chars="1840" refused="否" />
          </div>

          {/* per-citation breakdown (草稿 · 最後一 run) */}
          <div style={{ marginTop: 16 }}>
            <div className="text-xs muted" style={{ marginBottom: 6 }}>草稿配置 · 每引用 section + 圖數(最後一 run)</div>
            <table className="table" style={{ fontSize: 12 }}>
              <thead>
                <tr>
                  <th>引用 chunk</th>
                  <th>Section</th>
                  <th style={{ textAlign: "right" }}>圖數</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="mono">chunk-42</td>
                  <td>Address Book › Sync</td>
                  <td className="mono" style={{ textAlign: "right" }}>6</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div className="card-footer">
          <div className="text-xs muted">
            N 次重跑取平均 · band = max − min(越細越穩定)· 對 RAGAs 盲 → presentation counters 為第二軸
          </div>
          <button className="btn btn-secondary btn-sm"><IcDownload size={13} /> 把草稿配置儲存到此 KB</button>
        </div>
      </div>

      {/* Re-index card — explainer (W46 / ADR-0043: in-place per-doc re-ingest) */}
      <div className="card" style={{ gridColumn: "1 / -1" }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">Re-indexing</h3>
            <div className="card-desc">Re-parse every document from its stored original source under the current config. Needed after a chunk_strategy or image-cap change.</div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={() => setShowReindexExplainer(!showReindexExplainer)}>
            {showReindexExplainer ? "Hide details" : "What is this?"} <IcChevRight size={11} style={{ transform: showReindexExplainer ? "rotate(90deg)" : "none" }} />
          </button>
        </div>
        {showReindexExplainer && (
          <div style={{ padding: "0 18px 18px" }}>
            <div style={{ padding: "14px 16px", background: "oklch(var(--muted) / 0.4)", border: "1px solid oklch(var(--border))", borderRadius: "var(--radius-sm)", fontSize: 13, lineHeight: 1.65 }}>
              <p style={{ marginTop: 0, marginBottom: 10 }}>
                <b>What happens during a re-index:</b>
              </p>
              <ol style={{ paddingLeft: 22, marginBottom: 10, lineHeight: 1.8 }}>
                <li>Each document is re-fetched from its stored original source (Word / PDF / PPT).</li>
                <li>Its existing chunks are removed, then it's re-parsed via the <b>current</b> chunker config (chunk_strategy + max images / chunk).</li>
                <li>Each chunk is re-embedded and upserted into <span className="mono">{kb.index_name}</span>.</li>
                <li>Repeats per document — synchronous, in-place (Tier 1: no task queue).</li>
              </ol>
              <p style={{ marginBottom: 8 }}>
                <b>When you need to re-index:</b>
                <span className="muted"> chunk_strategy change · max-images-per-chunk change · Docling parser upgrade.</span>
              </p>
              <p style={{ marginBottom: 0 }} className="text-xs muted">
                Docs ingested before W46 (no stored source) are skipped + reported — re-upload them to make them reindexable.
                Zero-downtime v1→v2 atomic switch + eval gate stays a Track A enhancement.
              </p>
              <div style={{ display: "flex", gap: 14, marginTop: 14, fontSize: 12, color: "oklch(var(--muted-foreground))", fontFamily: "var(--font-mono)", padding: 10, background: "oklch(var(--background))", borderRadius: "var(--radius-sm)" }}>
                <div><b style={{ color: "oklch(var(--foreground))" }}>{kb.total_documents}</b> docs to re-parse</div>
                <div><b style={{ color: "oklch(var(--foreground))" }}>{kb.total_chunks.toLocaleString()}</b> chunks to rebuild</div>
                <div>in-place · <b style={{ color: "oklch(var(--foreground))" }}>brief</b> inconsistency window</div>
              </div>
            </div>
          </div>
        )}
        {/* Last re-index summary (presentational example of the POST /kb/{id}/reindex shape) */}
        <div style={{ padding: "0 18px 14px" }}>
          <div className="banner banner-success" style={{ marginBottom: 0 }}>
            <IcCheck size={15} style={{ color: "oklch(var(--success))" }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>Re-indexed {kb.total_documents} / {kb.total_documents} documents · {kb.total_chunks.toLocaleString()} chunks rebuilt</div>
              <div className="text-xs muted mono">skipped (no source): 0 · failed: 0</div>
            </div>
          </div>
        </div>
        <div className="card-footer">
          <div className="text-xs muted">Last re-index: <span className="mono">{window.formatRelative(kb.last_indexed_at)}</span> · current version <span className="mono">v1</span></div>
          <div className="row">
            <button className="btn btn-secondary btn-sm" disabled><IcDownload size={13} /> Export config (YAML)</button>
            <button className="btn btn-secondary btn-sm" onClick={() => setShowReindexModal(true)}><IcRefresh size={13} /> Trigger re-index now</button>
          </div>
        </div>
      </div>

      {/* Danger zone */}
      <div className="card" style={{ gridColumn: "1 / -1", borderColor: "oklch(var(--destructive) / 0.3)" }}>
        <div className="card-header" style={{ background: "oklch(var(--destructive) / 0.04)" }}>
          <div>
            <h3 className="card-title" style={{ color: "oklch(var(--destructive))" }}>Danger zone</h3>
            <div className="card-desc">Irreversible · audit-logged</div>
          </div>
        </div>
        <div className="card-body" style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-secondary">Archive KB (read-only)</button>
          <div className="spacer" />
          <button className="btn btn-destructive"><IcTrash size={14} /> Delete KB</button>
        </div>
      </div>

      {/* W46 — re-index confirm modal (.modal-overlay + .modal per DESIGN_SYSTEM §4.5) */}
      {showReindexModal && (
        <div className="modal-overlay" onClick={() => setShowReindexModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Re-index this knowledge base?</h2>
              <p className="modal-desc">Re-parses every document from its stored original source under the current config. Each document is briefly unavailable while it rebuilds.</p>
            </div>
            <div className="modal-body">
              <div className="banner banner-warning" style={{ marginBottom: 14 }}>
                <IcAlert size={15} style={{ color: "oklch(var(--warning))" }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 500 }}>Save config changes first</div>
                  <div className="text-xs muted">Re-index uses the saved config. Unsaved chunk_strategy / image-cap edits won't apply until saved.</div>
                </div>
              </div>
              <div style={{ display: "flex", gap: 14, fontSize: 12.5, color: "oklch(var(--muted-foreground))", fontFamily: "var(--font-mono)", padding: 12, background: "oklch(var(--muted) / 0.4)", borderRadius: "var(--radius-sm)" }}>
                <div><b style={{ color: "oklch(var(--foreground))" }}>{kb.total_documents}</b> docs</div>
                <div><b style={{ color: "oklch(var(--foreground))" }}>{kb.total_chunks.toLocaleString()}</b> chunks</div>
                <div>strategy <b style={{ color: "oklch(var(--foreground))" }}>{chunkStrategy}</b></div>
                <div>max img <b style={{ color: "oklch(var(--foreground))" }}>{maxImages || "8 (全域)"}</b></div>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn btn-ghost btn-sm" onClick={() => setShowReindexModal(false)}>Cancel</button>
              <button className="btn btn-primary btn-sm" onClick={() => setShowReindexModal(false)}><IcRefresh size={13} /> Re-index {kb.total_documents} documents</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── W43 per-KB tuning helpers (ADR-0040) ─────────────────────────────────────
// File-local; visible to TabKbSettings via hoisting. null/inherit = 沿用全域。

// A single numeric/text knob. inherit → placeholder shows global default + no value;
// overridden → shows per-KB value + 「還原全域」affordance.
function KbTuneKnob({ label, inherit, globalValue, value, suffix }) {
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label" style={{ display: "flex", alignItems: "center", gap: 6 }}>
        {label}
        {inherit
          ? <span className="badge badge-muted" style={{ fontSize: 9, fontWeight: 500 }}>繼承全域</span>
          : <span className="badge badge-success" style={{ fontSize: 9 }}><IcEdit size={9} /> 已覆寫</span>}
      </label>
      <input
        className="input mono"
        defaultValue={inherit ? "" : value}
        placeholder={inherit ? `${globalValue}${suffix || ""}` : undefined}
      />
      <div className="hint" style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <span>全域預設 <span className="mono">{globalValue}{suffix || ""}</span></span>
        {!inherit && (
          <span style={{ display: "inline-flex", gap: 3, alignItems: "center", cursor: "pointer", color: "oklch(var(--muted-foreground))" }}>
            <IcRefresh size={10} /> 還原全域
          </span>
        )}
      </div>
    </div>
  );
}

// A toggle-led group (enable_* switch + title/desc + 繼承/覆寫 badge) with a
// collapsible 進階 numeric grid. Mirrors the OptionRow visual language (§4.3).
function KbTuneGroup({ icon, title, desc, enabled, enabledInherit, children }) {
  const [open, setOpen] = useState(false);
  const Ic = icon;
  return (
    <div style={{ border: "1px solid oklch(var(--border))", borderRadius: "var(--radius-sm)", overflow: "hidden" }}>
      <div style={{ display: "flex", gap: 12, padding: "12px 14px", alignItems: "flex-start", background: enabled ? "oklch(var(--muted) / 0.4)" : "transparent" }}>
        <span className="switch" data-on={enabled} style={{ flexShrink: 0, marginTop: 2 }} />
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
            <Ic size={13} style={{ color: "oklch(var(--muted-foreground))" }} />
            <span style={{ fontSize: 13, fontWeight: 500 }}>{title}</span>
            {enabledInherit
              ? <span className="badge badge-muted" style={{ fontSize: 9 }}>繼承全域</span>
              : <span className="badge badge-success" style={{ fontSize: 9 }}>已覆寫</span>}
          </div>
          <div className="text-xs muted" style={{ marginTop: 3, lineHeight: 1.5 }}>{desc}</div>
        </div>
        <button className="btn btn-ghost btn-sm" style={{ flexShrink: 0 }} onClick={() => setOpen(!open)}>
          進階 <IcChevRight size={11} style={{ transform: open ? "rotate(90deg)" : "none" }} />
        </button>
      </div>
      {open && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, padding: 14, borderTop: "1px solid oklch(var(--border))" }}>
          {children}
        </div>
      )}
    </div>
  );
}

// One A/B result column for the test-run panel. accent = DRAFT (草稿).
function KbTestResultCard({ label, accent, cit, citBand, imgRaw, imgDedup, imgBand, lat, chars, refused }) {
  return (
    <div style={{
      border: accent ? "1px solid oklch(var(--accent) / 0.4)" : "1px solid oklch(var(--border))",
      borderRadius: "var(--radius-sm)",
      background: accent ? "oklch(var(--accent) / 0.04)" : "transparent",
      overflow: "hidden",
    }}>
      <div style={{ padding: "10px 14px", borderBottom: "1px solid oklch(var(--border))", fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, background: "oklch(var(--border))" }}>
        <KbTestMetric k="引用數" v={cit} band={citBand} />
        <KbTestMetric k="圖片(dedup)" v={imgDedup} sub={`raw ${imgRaw}`} band={imgBand} />
        <KbTestMetric k="延遲 p50" v={lat} />
        <KbTestMetric k="答案字數" v={chars} />
        <KbTestMetric k="是否拒答" v={refused} />
        <KbTestMetric k="穩定度" v={`band ${citBand}/${imgBand}`} />
      </div>
    </div>
  );
}

function KbTestMetric({ k, v, sub, band }) {
  return (
    <div style={{ background: "oklch(var(--card))", padding: "10px 14px" }}>
      <div className="text-xs muted">{k}</div>
      <div className="mono" style={{ fontSize: 16, fontWeight: 600, marginTop: 2 }}>
        {v}
        {band != null && <span className="text-xs muted" style={{ fontWeight: 400, marginLeft: 4 }}>±{band}</span>}
      </div>
      {sub && <div className="text-xs muted mono" style={{ marginTop: 1 }}>{sub}</div>}
    </div>
  );
}

window.PageKbList = PageKbList;
window.PageKbDetail = PageKbDetail;

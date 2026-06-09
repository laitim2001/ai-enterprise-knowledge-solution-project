// ekp-page-doc-detail.jsx — /kb/[id]/doc/[docId]
// Three-pane: outline (left) · chunk list (center) · chunk inspector (right)
// Surfaces the real C01 ingestion pipeline output:
//   parser structure + extracted images + chunk-image association (embedded_image_positions)

function PageDocDetail({ kbId, docId, onNavigate }) {
  const kb = window.MOCK_KBS.find((k) => k.kb_id === kbId) || window.MOCK_KBS[0];
  const doc = window.MOCK_DOC_DETAIL;
  const allImages = window.MOCK_IMAGES.filter((img) => img.used_in_docs.includes(doc.doc_id));
  const [selectedChunk, setSelectedChunk] = useState(0);
  // W58 / ADR-0051 — doc-detail tabs (design-stage expansion: read-only inspector
  // + per-document config surface consuming the ADR-0050 per-doc CRUD API).
  const [tab, setTab] = useState("inspector");

  const sampleChunks = [
    { idx: 84, title: "4.2 Multi-Currency Setup — Exchange Rate Mapping", section_path: ["GL Setup", "Posting Definitions", "Multi-Currency"], tokens: 312, has_image: true, image_idx: 0, low_value: false, preview: "When configuring posting definitions for multi-currency journals, the **exchange rate type** field must align with the legal entity's accounting currency. Failure to map this field triggers a posting validation error at month-end close." },
    { idx: 85, title: "4.2 Multi-Currency Setup — Validation Errors", section_path: ["GL Setup", "Posting Definitions", "Multi-Currency"], tokens: 286, has_image: false, low_value: false, preview: "Validation runs at month-end close via the GL period-close batch. Common error codes: POST-VAL-101 (mismatched currency), POST-VAL-204 (missing exchange rate type)…" },
    { idx: 86, title: "4.2 Multi-Currency Setup — Reference Validation Matrix", section_path: ["GL Setup", "Posting Definitions", "Multi-Currency"], tokens: 198, has_image: true, image_idx: 1, low_value: false, preview: "Reference Section 4.3 for the full validation matrix. The matrix is keyed on (source_currency, dest_currency, rate_type) and lists all allowed combinations." },
    { idx: 87, title: "4.3 Validation Matrix — Header", section_path: ["GL Setup", "Posting Definitions", "Validation Matrix"], tokens: 64,  has_image: false, low_value: true, preview: "Section 4.3 — Validation Matrix" },
    { idx: 88, title: "4.3 Validation Matrix — Allowed Combinations", section_path: ["GL Setup", "Posting Definitions", "Validation Matrix"], tokens: 514, has_image: true, image_idx: 0, low_value: false, preview: "The following table lists allowed (source, destination, rate_type) combinations. Inter-company posting requires both legal entities have the rate type explicitly mapped." },
  ];

  const chunk = sampleChunks[selectedChunk];
  const chunkImage = chunk.has_image ? allImages[chunk.image_idx] : null;

  return (
    <div className="content content-wide" style={{ paddingTop: 16, paddingBottom: 16 }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 16 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
            <button className="btn btn-ghost btn-xs btn-ghost-muted" onClick={() => onNavigate("kb")}>
              <IcChevLeft size={12} /> Knowledge
            </button>
            <span className="text-xs muted">·</span>
            <button className="btn btn-ghost btn-xs btn-ghost-muted" onClick={() => onNavigate("kb-detail", { kbId: kb.kb_id })}>
              {kb.name}
            </button>
            <span className="text-xs muted">·</span>
            <span className="text-xs muted mono">{doc.doc_id}</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <h1 className="page-title" style={{ fontSize: 19 }}>{doc.title}</h1>
            <span className="badge badge-success"><span className="badge-dot" /> INDEXED</span>
          </div>
          <div className="page-subtitle" style={{ display: "flex", gap: 12, flexWrap: "wrap", fontSize: 12.5, fontFamily: "var(--font-mono)", marginTop: 6 }}>
            <span><IcFile size={11} style={{ verticalAlign: "-2px", marginRight: 4 }} />{doc.file_type.toUpperCase()} · {(doc.size_kb / 1024).toFixed(1)} MB · {doc.pages} pp</span>
            <span>· chunk_strategy <b style={{ color: "oklch(var(--foreground))" }}>{doc.chunk_strategy}</b></span>
            <span>· {doc.total_chunks} chunks ({doc.low_value_chunks} low_value)</span>
            <span>· {doc.total_tokens.toLocaleString()} tokens</span>
            <span>· {doc.total_images} embedded images</span>
          </div>
        </div>
        <div className="page-actions">
          <button className="btn btn-secondary btn-sm"><IcLink size={13} /> Open in SharePoint</button>
          <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> Re-process</button>
          <button className="btn btn-secondary btn-sm" style={{ color: "oklch(var(--destructive))" }}>
            <IcTrash size={13} /> Delete
          </button>
        </div>
      </div>

      {/* W58 / ADR-0051 — tab strip: read-only inspector + per-doc config surface */}
      <div className="tabs">
        {[
          { id: "inspector", label: "Chunk inspector", icon: IcLayers },
          { id: "config", label: "Per-doc 配置", icon: IcSettings },
        ].map((t) => {
          const Ic = t.icon;
          return (
            <div key={t.id} className="tab" data-active={tab === t.id} onClick={() => setTab(t.id)}>
              <Ic size={14} /> {t.label}
            </div>
          );
        })}
      </div>

      {tab === "inspector" && (<>
      {/* Pipeline stages strip */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-body" style={{ padding: 0 }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)" }}>
            {[
              { label: "Parse",   value: `${doc.parse_duration_ms}ms`, sub: "Docling layout-aware",           icon: IcFile, ok: true },
              { label: "Extract", value: `${doc.total_images} imgs`,    sub: "SHA256 dedup applied",           icon: IcLayers, ok: true },
              { label: "Chunk",   value: `${doc.total_chunks} chunks`,   sub: `${doc.chunk_strategy} strategy`, icon: IcLayers, ok: true },
              { label: "Embed",   value: `${doc.embed_duration_ms}ms`,   sub: "embed-3-large 1024d",            icon: IcZap, ok: true },
              { label: "Index",   value: "upserted",                     sub: kb.index_name,                     icon: IcDatabase, ok: true },
            ].map((s, i) => {
              const Ic = s.icon;
              return (
                <div key={s.label} style={{ padding: "14px 18px", borderRight: i < 4 ? "1px solid oklch(var(--border))" : "none", display: "flex", gap: 12, alignItems: "center" }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: "var(--radius-sm)",
                    background: "oklch(var(--success) / 0.12)",
                    color: "oklch(var(--success))",
                    display: "grid", placeItems: "center", flexShrink: 0,
                  }}><IcCheck size={15} /></div>
                  <div>
                    <div className="text-xs muted mono" style={{ letterSpacing: "0.04em", textTransform: "uppercase", marginBottom: 2 }}>{s.label}</div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, fontFamily: "var(--font-mono)" }}>{s.value}</div>
                    <div className="text-xs muted">{s.sub}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Image strip */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-header">
          <div>
            <h3 className="card-title">Extracted images <span className="text-xs muted mono" style={{ marginLeft: 6 }}>{allImages.length} total · SHA256 deduplicated</span></h3>
            <div className="card-desc">Each chunk in this doc references images via <span className="mono">embedded_image_positions</span>; orchestrator resolves to <span className="mono">ImageRef.blob_url</span></div>
          </div>
          <button className="btn btn-ghost btn-sm">View all in Image Library →</button>
        </div>
        <div className="card-body" style={{ padding: "14px 18px" }}>
          <div style={{ display: "flex", gap: 10, overflowX: "auto", paddingBottom: 4 }}>
            {allImages.map((img, i) => <ImageThumb key={img.sha256} img={img} idx={i} />)}
          </div>
        </div>
      </div>

      {/* 3-pane main */}
      <div style={{ display: "grid", gridTemplateColumns: "240px 1fr 380px", gap: 16 }}>
        {/* Left: outline */}
        <div className="card" style={{ alignSelf: "start", position: "sticky", top: 16 }}>
          <div className="card-header" style={{ padding: "10px 14px" }}>
            <div>
              <h3 className="card-title" style={{ fontSize: 12.5 }}>Document outline</h3>
            </div>
          </div>
          <div className="card-body card-body-tight" style={{ maxHeight: 540, overflowY: "auto", padding: "6px 0" }}>
            {doc.outline.map((s, i) => (
              <div key={i} style={{
                padding: `5px ${14}px 5px ${14 + (s.level - 1) * 14}px`,
                fontSize: s.level === 1 ? 12.5 : 12,
                fontWeight: s.level === 1 ? 600 : 450,
                background: s.active ? "oklch(var(--accent) / 0.08)" : "transparent",
                color: s.active ? "oklch(var(--accent))" : "oklch(var(--foreground))",
                borderLeft: s.active ? "2px solid oklch(var(--accent))" : "2px solid transparent",
                display: "flex",
                alignItems: "center",
                gap: 8,
                cursor: "default",
                lineHeight: 1.4,
              }}>
                <span style={{ flex: 1 }}>{s.title}</span>
                <span className="text-xs muted mono">{s.chunk_count}</span>
              </div>
            ))}
          </div>
          <div className="card-footer" style={{ padding: "8px 12px" }}>
            <span className="text-xs muted mono">{doc.outline.length} sections</span>
            <button className="btn btn-ghost btn-xs">Export TOC</button>
          </div>
        </div>

        {/* Center: chunk list */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Chunks · 4.2 Multi-Currency Setup</h3>
              <div className="card-desc">9 chunks in this section · showing 5 around your selection</div>
            </div>
            <div className="row">
              <button className="btn btn-secondary btn-xs"><IcFilter size={12} /> All</button>
              <button className="btn btn-secondary btn-xs"><IcLayers size={12} /> With images</button>
              <button className="btn btn-secondary btn-xs muted">low_value</button>
            </div>
          </div>
          <div className="card-body card-body-tight">
            {sampleChunks.map((c, i) => {
              const img = c.has_image ? allImages[c.image_idx] : null;
              const active = selectedChunk === i;
              return (
                <div key={i}
                     onClick={() => setSelectedChunk(i)}
                     style={{
                       padding: "14px 18px",
                       borderBottom: i < sampleChunks.length - 1 ? "1px solid oklch(var(--border))" : "none",
                       background: active ? "oklch(var(--muted) / 0.5)" : "transparent",
                       borderLeft: active ? "2px solid oklch(var(--accent))" : "2px solid transparent",
                       cursor: "default",
                       opacity: c.low_value ? 0.65 : 1,
                     }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span className="mono text-xs" style={{ background: "oklch(var(--muted))", padding: "1px 6px", borderRadius: 3, fontWeight: 600 }}>#{c.idx}</span>
                    <div className="section-path text-xs" style={{ flex: 1 }}>
                      {c.section_path.map((s, j) => <span key={j}>{s}</span>)}
                    </div>
                    {c.low_value && <span className="badge badge-warning">low_value</span>}
                    {c.has_image && <span className="badge badge-accent"><IcLayers size={10} /> image</span>}
                    <span className="text-xs mono muted">{c.tokens} tok</span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 500, marginBottom: 4 }}>{c.title}</div>
                  <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                    <div style={{ flex: 1, fontSize: 12.5, lineHeight: 1.55, color: "oklch(var(--foreground) / 0.85)" }}
                         dangerouslySetInnerHTML={{ __html: c.preview.replace(/\*\*(.+?)\*\*/g, "<mark>$1</mark>") }} />
                    {img && (
                      <div style={{
                        width: 72, height: 50, flexShrink: 0,
                        background: `linear-gradient(135deg, oklch(var(--accent) / 0.15), oklch(var(--accent) / 0.04))`,
                        border: "1px solid oklch(var(--accent) / 0.25)",
                        borderRadius: 4,
                        display: "grid", placeItems: "center",
                        color: "oklch(var(--accent))",
                      }}>
                        <IcLayers size={14} />
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: chunk inspector */}
        <div className="col" style={{ gap: 16, alignSelf: "start", position: "sticky", top: 16 }}>
          <ChunkInspector chunk={chunk} kb={kb} image={chunkImage} />
        </div>
      </div>
      </>)}

      {tab === "config" && <DocConfigTab kb={kb} doc={doc} />}
    </div>
  );
}

function ImageThumb({ img, idx, onClick }) {
  const colors = ["oklch(var(--accent))", "oklch(0.62 0.13 200)", "oklch(0.65 0.14 145)", "oklch(0.60 0.16 285)", "oklch(0.65 0.18 25)"];
  const c = colors[idx % colors.length];
  return (
    <div onClick={onClick}
         title={img.alt_text}
         style={{
           flexShrink: 0,
           width: 140,
           border: "1px solid oklch(var(--border))",
           borderRadius: "var(--radius-sm)",
           overflow: "hidden",
           background: "oklch(var(--card))",
           cursor: "default",
         }}>
      <div style={{
        height: 78,
        background: `linear-gradient(135deg, ${c} / 0.18, ${c} / 0.05)`.replace(/oklch\((.+?)\)/g, (_, x) => `oklch(${x.split(" / ")[0]} / 0.18)`),
        backgroundImage: `linear-gradient(135deg, ${c.replace(")", " / 0.2)")}, ${c.replace(")", " / 0.05)")})`,
        display: "grid", placeItems: "center",
        position: "relative",
        color: c,
      }}>
        <IcLayers size={20} />
        {img.low_value && (
          <span className="badge badge-warning" style={{ position: "absolute", top: 4, right: 4, fontSize: 9.5 }}>low_value</span>
        )}
        {img.used_in_docs.length > 1 && (
          <span className="badge badge-success" style={{ position: "absolute", top: 4, left: 4, fontSize: 9.5 }}>
            <span className="badge-dot" /> ×{img.used_in_docs.length}
          </span>
        )}
      </div>
      <div style={{ padding: "6px 8px" }}>
        <div className="text-xs" style={{ fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", lineHeight: 1.3 }}>
          {img.alt_text || "—"}
        </div>
        <div className="text-xs muted mono" style={{ marginTop: 2 }}>
          {img.width}×{img.height} · {img.size_kb}KB
        </div>
      </div>
    </div>
  );
}

function ChunkInspector({ chunk, kb, image }) {
  const chunkId = `kb-${kb.kb_id}_doc-d365_fno_gl_v2_4_chunk-${String(chunk.idx).padStart(4, "0")}`;
  return (
    <>
      <div className="card">
        <div className="card-header" style={{ padding: "12px 16px" }}>
          <div>
            <h3 className="card-title" style={{ fontSize: 13 }}>Chunk inspector</h3>
            <div className="text-xs muted mono" style={{ marginTop: 2 }}>{chunkId}</div>
          </div>
          <div className="row">
            <button className="btn btn-ghost btn-icon btn-xs"><IcCopy size={12} /></button>
            <button className="btn btn-ghost btn-icon btn-xs"><IcEdit size={12} /></button>
          </div>
        </div>
        <div className="card-body" style={{ padding: 14 }}>
          {/* metadata */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: 12 }}>
            <span className="badge badge-muted">chunk_index <b style={{ marginLeft: 2 }}>{chunk.idx}</b></span>
            <span className="badge badge-muted">tokens <b style={{ marginLeft: 2 }}>{chunk.tokens}</b></span>
            {chunk.has_image && <span className="badge badge-accent">embedded_images <b style={{ marginLeft: 2 }}>1</b></span>}
            {chunk.low_value && <span className="badge badge-warning">low_value</span>}
          </div>

          {/* section_path */}
          <div className="text-xs muted mono" style={{ marginBottom: 4, letterSpacing: "0.04em", textTransform: "uppercase" }}>section_path</div>
          <div className="section-path" style={{ fontSize: 12, marginBottom: 12 }}>
            {chunk.section_path.map((s, j) => <span key={j}>{s}</span>)}
          </div>

          {/* prev/next */}
          <div className="text-xs muted mono" style={{ marginBottom: 4, letterSpacing: "0.04em", textTransform: "uppercase" }}>Linked chunks</div>
          <div className="text-xs mono" style={{ marginBottom: 14, color: "oklch(var(--muted-foreground))" }}>
            ← <span style={{ color: "oklch(var(--accent))" }}>chunk-{String(chunk.idx - 1).padStart(4, "0")}</span> · this · <span style={{ color: "oklch(var(--accent))" }}>chunk-{String(chunk.idx + 1).padStart(4, "0")}</span> →
          </div>

          {/* embedded image (if any) */}
          {image && (
            <>
              <div className="text-xs muted mono" style={{ marginBottom: 6, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                Associated image
              </div>
              <div style={{
                border: "1px solid oklch(var(--accent) / 0.25)",
                borderRadius: "var(--radius-sm)",
                background: "oklch(var(--accent) / 0.04)",
                padding: 10,
                marginBottom: 14,
              }}>
                <div style={{
                  height: 110, marginBottom: 8,
                  background: "linear-gradient(135deg, oklch(var(--accent) / 0.18), oklch(var(--accent) / 0.04))",
                  borderRadius: 4,
                  display: "grid", placeItems: "center",
                  color: "oklch(var(--accent))",
                }}>
                  <IcLayers size={24} />
                </div>
                <div className="text-xs" style={{ fontWeight: 500, lineHeight: 1.4 }}>{image.alt_text}</div>
                <div className="text-xs muted mono" style={{ marginTop: 4, wordBreak: "break-all", lineHeight: 1.4 }}>
                  sha256 {image.sha256.slice(0, 12)}…
                </div>
                <div className="text-xs muted mono" style={{ marginTop: 2 }}>
                  {image.width}×{image.height} · doc_order {image.doc_order}
                </div>
              </div>
            </>
          )}

          {/* embedding preview */}
          <div className="text-xs muted mono" style={{ marginBottom: 6, letterSpacing: "0.04em", textTransform: "uppercase" }}>
            Embedding vector <span style={{ fontWeight: 500, color: "oklch(var(--foreground))" }}>1024d</span>
          </div>
          <div style={{
            border: "1px solid oklch(var(--border))",
            borderRadius: "var(--radius-sm)",
            background: "oklch(var(--muted) / 0.4)",
            padding: 10,
            fontFamily: "var(--font-mono)",
            fontSize: 10.5,
            lineHeight: 1.5,
            display: "grid",
            gridTemplateColumns: "repeat(8, 1fr)",
            gap: "2px 6px",
            color: "oklch(var(--muted-foreground))",
          }}>
            {[0.024, -0.018, 0.092, 0.144, -0.061, 0.027, -0.084, 0.117,
              0.038, -0.052, 0.071, 0.094, -0.022, 0.013, -0.046, 0.082,
              0.041, -0.029, 0.068, 0.075, -0.034, 0.018, -0.011, 0.063].map((v, i) => (
              <span key={i} style={{ color: v > 0 ? "oklch(var(--accent))" : "oklch(var(--foreground))" }}>
                {v.toFixed(3)}
              </span>
            ))}
            <span style={{ gridColumn: "1 / -1", color: "oklch(var(--muted-foreground))", marginTop: 4 }}>
              …  +1000 more dims  …
            </span>
          </div>
        </div>
        <div className="card-footer" style={{ padding: "8px 14px" }}>
          <div className="text-xs muted mono">embed-3-large · MRL truncate 1024d</div>
          <button className="btn btn-ghost btn-xs">Full JSON →</button>
        </div>
      </div>

      <div className="card">
        <div className="card-body" style={{ padding: 14 }}>
          <div className="text-xs muted mono" style={{ marginBottom: 6, letterSpacing: "0.04em", textTransform: "uppercase" }}>
            Chunk text
          </div>
          <div style={{
            background: "oklch(var(--muted) / 0.4)",
            border: "1px solid oklch(var(--border))",
            borderRadius: "var(--radius-sm)",
            padding: "10px 12px",
            fontSize: 12.5,
            lineHeight: 1.6,
            maxHeight: 220,
            overflowY: "auto",
          }}
          dangerouslySetInnerHTML={{ __html: chunk.preview.replace(/\*\*(.+?)\*\*/g, "<mark>$1</mark>") }} />
        </div>
      </div>
    </>
  );
}

// ── W58 / ADR-0051 — Per-document config tab ────────────────────────────────
// Consumes the ADR-0050 per-doc CRUD API. Mirrors the KB TabKbSettings tuning
// pattern (ekp-page-kb.jsx), but: per-DOCUMENT scope, post-retrieval knobs ONLY
// (retrieval-entry knobs stay per-KB per ADR-0050), and 繼承 KB (not 繼承全域)
// inherit semantics.
function DocConfigTab({ kb, doc }) {
  return (
    <div style={{ display: "grid", gap: 16 }}>
      {/* scope banner */}
      <div className="banner banner-info">
        <IcSettings size={15} style={{ color: "oklch(var(--info))" }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13 }}>
            <b>此文件度身訂做配置</b> — 留空 = 繼承 KB(<span className="mono">{kb.name}</span>)再全域。
          </div>
          <div className="text-xs muted" style={{ marginTop: 2 }}>
            解析優先:per-query &gt; <b>per-DOC(此文件)</b> &gt; per-KB &gt; 全域 · ADR-0050 ·
            <span className="mono"> PUT /kb/{kb.kb_id}/docs/{doc.doc_id}/config</span>
          </div>
        </div>
      </div>

      {/* Per-doc advanced tuning — post-retrieval knobs only */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Per-document 配置</h3>
            <div className="card-desc">
              覆寫此文件嘅<b>合成 + 引用後處理</b>行為。未覆寫嘅旋鈕沿用 KB 預設。
              全部 runtime — <b>唔需要重新索引</b>。
            </div>
          </div>
          <span className="badge badge-info" style={{ fontSize: 9.5 }}><IcEdit size={10} /> Runtime · no re-index</span>
        </div>
        <div className="card-body" style={{ display: "grid", gap: 12 }}>
          {/* answer_detail — synthesis (dominant doc) */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label" style={{ display: "flex", alignItems: "center", gap: 6 }}>
              答案詳細度(answer_detail)
              <span className="badge badge-muted" style={{ fontSize: 9, fontWeight: 500 }}>繼承 KB</span>
            </label>
            <div className="seg" style={{ width: "100%", maxWidth: 380 }}>
              {[
                { v: "inherit", l: "繼承 KB" },
                { v: "concise", l: "concise" },
                { v: "detailed", l: "detailed" },
              ].map((o) => (
                <button key={o.v} className="seg-btn" data-active={o.v === "inherit"} style={{ flex: 1, padding: "5px 8px", fontSize: 11.5 }}>{o.l}</button>
              ))}
            </div>
            <div className="hint">合成詳細度。程序手冊文件可設 <span className="mono">detailed</span>(逐步列盡);繼承 = 用 KB 設定。</div>
          </div>

          <DocTuneGroup icon={IcLink} title="Citation post-hoc expansion" enabled enabledInherit
            desc="答案生成後,為每個引用補充鄰近輔助 chunk,提升完整性。">
            <DocTuneKnob label="Max aux / citation" inherit kbValue="10" />
            <DocTuneKnob label="Expansion window" inherit kbValue="1" />
            <DocTuneKnob label="Section path prefix depth" inherit kbValue="1" />
          </DocTuneGroup>

          <DocTuneGroup icon={IcEye} title="Citation neighbour images + 圖片上限" enabled enabledInherit
            desc="控制引用鄰近圖片帶入,同每個答案最多顯示幾多張圖(圖洪水收斂)。">
            <DocTuneKnob label="Neighbour max aux images" inherit kbValue="18" />
            <DocTuneKnob label="Neighbour prefix depth" inherit kbValue="1" />
            <DocTuneKnob label="Max images / answer" inherit kbValue="20" />
            <DocSwitchKnob label="章節概覽圖置頂(overview pin)" inherit kbValue="開" />
          </DocTuneGroup>
        </div>
        <div className="card-footer">
          <div className="text-xs muted">配置 scope:per-query &gt; <b>per-DOC(此文件)</b> &gt; per-KB &gt; 全域 · ADR-0050</div>
          <div className="row">
            <button className="btn btn-secondary btn-sm"><IcRefresh size={13} /> 還原全部至 KB</button>
            <button className="btn btn-primary btn-sm">儲存到此文件</button>
          </div>
        </div>
      </div>

      {/* retrieval-entry knobs — KB-level only explainer (per ADR-0050) */}
      <div className="card">
        <div className="card-body" style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: 14 }}>
          <IcShield size={15} style={{ color: "oklch(var(--warning))", flexShrink: 0, marginTop: 2 }} />
          <div className="text-xs" style={{ lineHeight: 1.6, flex: 1 }}>
            <b>檢索入口旋鈕</b>(default_top_k / default_rerank_k / parent-document retrieval)
            <b>喺 KB 設定</b>,唔可以 per-document 覆寫 —— 呢類旋鈕喺「邊個文件被引用」確定<b>之前</b>
            已驅動檢索(ADR-0050)。
            <button className="btn btn-ghost btn-xs" style={{ marginLeft: 6 }}>去 KB 設定 →</button>
          </div>
        </div>
      </div>

      {/* per-doc config-test (scoped to this doc) */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">
              <IcZap size={14} style={{ verticalAlign: "-2px", marginRight: 6, color: "oklch(var(--accent))" }} />
              試跑(此文件 scope)
            </h3>
            <div className="card-desc">
              用此文件嘅配置喺真 pipeline 試跑(主導 doc = 此文件)。
              <span className="mono"> POST /kb/{kb.kb_id}/config-test · doc={doc.doc_id}</span>
            </div>
          </div>
        </div>
        <div className="card-body">
          <div style={{ display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap", marginBottom: 16 }}>
            <div className="field" style={{ flex: 1, minWidth: 240, marginBottom: 0 }}>
              <label className="label">測試問題</label>
              <input className="input" defaultValue="How do I process and confirm journal voucher transactions?" />
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
              <span className="switch" data-on /> 同繼承 KB 對照(A/B)
            </label>
            <button className="btn btn-primary"><IcZap size={14} /> 試跑</button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <DocTestResultCard label="此文件配置(DRAFT)" accent faith="0.82" faithBand="0.10" runs={3}
              cit="13" citBand="0" sec="4" secBand="0" imgRaw="20" imgDedup="15" imgBand="0" lat="5.2s" chars="1620" refused="否" />
            <DocTestResultCard label="繼承 KB(SAVED)" faith="0.84" faithBand="0.08" runs={3}
              cit="13" citBand="0" sec="2" secBand="0" imgRaw="20" imgDedup="15" imgBand="0" lat="5.1s" chars="1580" refused="否" />
          </div>
          <div className="hint" style={{ marginTop: 10, display: "flex", gap: 6, alignItems: "flex-start" }}>
            <IcAlert size={13} style={{ color: "oklch(var(--warning))", marginTop: 1, flexShrink: 0 }} />
            <span>忠實度對長 / 全面答案有 <b style={{ color: "oklch(var(--warning))" }}>length bias</b> —— 低分若配合高 <b>涵蓋章節數</b> / 字數,多為 bias 而非 config 差,宜一齊判讀。</span>
          </div>
        </div>
        <div className="card-footer">
          <div className="text-xs muted">N 次重跑取平均 · band = max − min · answer_detail 不在試跑草稿(經「儲存」生效)</div>
          <button className="btn btn-secondary btn-sm"><IcDownload size={13} /> 把草稿儲存到此文件</button>
        </div>
      </div>
    </div>
  );
}

// ── W58 per-doc tuning helpers (ADR-0051) — mirror KbTune* with 繼承 KB framing ──
// A single numeric/text knob. inherit → placeholder shows the KB value + no value;
// overridden → shows per-doc value + 「還原至 KB」affordance.
function DocTuneKnob({ label, inherit, kbValue, value, suffix }) {
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label" style={{ display: "flex", alignItems: "center", gap: 6 }}>
        {label}
        {inherit
          ? <span className="badge badge-muted" style={{ fontSize: 9, fontWeight: 500 }}>繼承 KB</span>
          : <span className="badge badge-success" style={{ fontSize: 9 }}><IcEdit size={9} /> 已覆寫</span>}
      </label>
      <input
        className="input mono"
        defaultValue={inherit ? "" : value}
        placeholder={inherit ? `${kbValue}${suffix || ""}` : undefined}
      />
      <div className="hint" style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
        <span>KB 預設 <span className="mono">{kbValue}{suffix || ""}</span></span>
        {!inherit && (
          <span style={{ display: "inline-flex", gap: 3, alignItems: "center", cursor: "pointer", color: "oklch(var(--muted-foreground))" }}>
            <IcRefresh size={10} /> 還原至 KB
          </span>
        )}
      </div>
    </div>
  );
}

// A boolean toggle cell (for overview pin) — switch + 繼承 KB / 已覆寫 badge.
function DocSwitchKnob({ label, inherit, kbValue }) {
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label" style={{ display: "flex", alignItems: "center", gap: 6 }}>
        {label}
        {inherit
          ? <span className="badge badge-muted" style={{ fontSize: 9, fontWeight: 500 }}>繼承 KB</span>
          : <span className="badge badge-success" style={{ fontSize: 9 }}><IcEdit size={9} /> 已覆寫</span>}
      </label>
      <div className="row" style={{ gap: 8, alignItems: "center", paddingTop: 4 }}>
        <span className="switch" data-on={!inherit} />
        <span className="text-xs muted">{inherit ? "繼承" : "覆寫"}</span>
      </div>
      <div className="hint">KB 預設 <span className="mono">{kbValue}</span></div>
    </div>
  );
}

// A toggle-led group (enable_* switch + title/desc + 繼承/覆寫 badge) with a
// collapsible 進階 numeric grid. Mirrors KbTuneGroup (§4.3 OptionRow language).
function DocTuneGroup({ icon, title, desc, enabled, enabledInherit, children }) {
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
              ? <span className="badge badge-muted" style={{ fontSize: 9 }}>繼承 KB</span>
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

// One A/B result column for the per-doc test-run panel. accent = DRAFT.
function DocTestResultCard({ label, accent, faith, faithBand, runs, cit, citBand, sec, secBand, imgRaw, imgDedup, imgBand, lat, chars, refused }) {
  return (
    <div style={{
      border: accent ? "1px solid oklch(var(--accent) / 0.4)" : "1px solid oklch(var(--border))",
      borderRadius: "var(--radius-sm)",
      background: accent ? "oklch(var(--accent) / 0.04)" : "transparent",
      overflow: "hidden",
    }}>
      <div style={{ padding: "10px 14px", borderBottom: "1px solid oklch(var(--border))", fontSize: 12, fontWeight: 600 }}>{label}</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, background: "oklch(var(--border))" }}>
        <div style={{ gridColumn: "1 / -1", background: "oklch(var(--card))", padding: "10px 14px" }}>
          <div className="text-xs muted">忠實度(faithfulness · 反幻覺 · 0–1)</div>
          <div className="mono" style={{ fontSize: 18, fontWeight: 700, marginTop: 2, color: faith != null ? "oklch(var(--success))" : "oklch(var(--muted-foreground))" }}>
            {faith != null ? faith : "—"}
            {faith != null && runs >= 2 && <span className="text-xs muted" style={{ fontWeight: 400, marginLeft: 6 }}>±{faithBand}</span>}
          </div>
          {faith != null && runs === 1 && (
            <div className="text-xs" style={{ marginTop: 3, color: "oklch(var(--warning))" }}>
              單次 judge · 方向性 · 重跑次數調高至 ≥2 先見穩定度 band
            </div>
          )}
        </div>
        <DocTestMetric k="引用數" v={cit} band={citBand} />
        <DocTestMetric k="涵蓋章節數" v={sec} band={secBand} sub="completeness proxy · 非 recall" />
        <DocTestMetric k="圖片(dedup)" v={imgDedup} sub={`raw ${imgRaw}`} band={imgBand} />
        <DocTestMetric k="延遲 p50" v={lat} />
        <DocTestMetric k="答案字數" v={chars} />
        <DocTestMetric k="是否拒答" v={refused} />
      </div>
    </div>
  );
}

function DocTestMetric({ k, v, sub, band }) {
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

window.PageDocDetail = PageDocDetail;
window.ImageThumb = ImageThumb;

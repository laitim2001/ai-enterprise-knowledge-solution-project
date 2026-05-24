'use client';

/**
 * /kb/[id]/docs/[docId] — Document Detail 3-pane per ADR-0029 Option C
 * + architecture.md v6 §5.5.2a.
 *
 * W22 F6.3 (NEW route, W21 F3 fold) per CLAUDE.md §5.7 H7 — 100% mockup fidelity
 * match against references/design-mockups/ekp-page-doc-detail.jsx:6 PageDocDetail.
 *
 * Mockup decomposition adopted (single-file pattern):
 *   Page sections inline: header + 5-stage pipeline strip + image strip + 3-pane
 *   (outline 240px / chunk list 1fr / inspector 380px). ONLY ImageThumb +
 *   ChunkInspector extracted as separate functions per mockup pattern.
 *
 * Backend integration:
 *   - W21 F1 `GET /kb/{kb_id}/docs/{doc_id}` (DocumentDetail enriched)
 *   - documentsApi.listChunks for chunk-level body (DocumentDetail returns
 *     outline + image_refs aggregate but not per-chunk text — list_chunks fills
 *     the center pane)
 *
 * F6.4 embedding vector preview: render mockup synthetic 24-dim hardcoded float
 * preview per `ChunkInspector` lines 343-353 (per D8.b 2026-05-18 D4 — real
 * Azure Search vector exposure stays Tier 2 but user-invisible via mockup-style).
 */

import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  ChevronLeft,
  Copy,
  Edit,
  FileText,
  Filter,
  Layers,
  Link as LinkIcon,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState } from 'react';

import {
  documentsApi,
  type ChunkSummary,
  type DocumentDetail,
  type ImageRef,
} from '@/lib/api/documents';
import { kbApi, type KbStatus } from '@/lib/api/kb';

export default function DocDetailPage() {
  const params = useParams<{ id: string; docId: string }>();
  const router = useRouter();
  const kbId = params.id;
  const docId = decodeURIComponent(params.docId);

  const kbQuery = useQuery<KbStatus>({
    queryKey: ['kb', kbId],
    queryFn: () => kbApi.get(kbId),
    enabled: !!kbId,
  });

  const docQuery = useQuery<DocumentDetail>({
    queryKey: ['kb', kbId, 'doc-detail', docId],
    queryFn: () => documentsApi.getDocDetail(kbId, docId),
    enabled: !!kbId && !!docId,
  });

  const chunksQuery = useQuery<ChunkSummary[]>({
    queryKey: ['kb', kbId, 'chunks', docId],
    queryFn: () => documentsApi.listChunks(kbId, docId),
    enabled: !!kbId && !!docId,
  });

  const [selectedChunkIdx, setSelectedChunkIdx] = useState(0);
  const [activeOutlinePath, setActiveOutlinePath] = useState<string | null>(null);

  if (kbQuery.isLoading || docQuery.isLoading) {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="banner banner-info">
            <span className="spinner" />
            <div style={{ flex: 1 }}>Loading document detail…</div>
          </div>
        </div>
      </div>
    );
  }
  if (docQuery.isError) {
    return (
      <div className="content">
        <div className="content-wide">
          <div className="banner banner-error">
            <AlertTriangle size={16} />
            <div style={{ flex: 1 }}>
              Failed to load document {docId}:{' '}
              {String((docQuery.error as Error)?.message ?? 'unknown')}
            </div>
          </div>
        </div>
      </div>
    );
  }
  if (!docQuery.data || !kbQuery.data) return null;

  const doc = docQuery.data;
  const kb = kbQuery.data;
  const chunkList = chunksQuery.data ?? [];
  const selectedChunk = chunkList[selectedChunkIdx];

  return (
    <div className="content content-wide" style={{ paddingTop: 16, paddingBottom: 16 }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 16 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 4,
            }}
          >
            <button
              type="button"
              className="btn btn-ghost btn-xs btn-ghost-muted"
              onClick={() => router.push('/kb')}
            >
              <ChevronLeft size={12} /> Knowledge
            </button>
            <span className="text-xs muted">·</span>
            <button
              type="button"
              className="btn btn-ghost btn-xs btn-ghost-muted"
              onClick={() => router.push(`/kb/${kbId}`)}
            >
              {kb.name || kbId}
            </button>
            <span className="text-xs muted">·</span>
            <span className="text-xs muted mono">{doc.doc_id}</span>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <h1 className="page-title" style={{ fontSize: 19 }}>
              {doc.title}
            </h1>
            <span className="badge badge-success">
              <span className="badge-dot" /> INDEXED
            </span>
          </div>
          <div
            className="page-subtitle"
            style={{
              display: 'flex',
              gap: 12,
              flexWrap: 'wrap',
              fontSize: 12.5,
              fontFamily: 'var(--font-mono)',
              marginTop: 6,
            }}
          >
            <span>
              <FileText
                size={11}
                style={{ verticalAlign: '-2px', marginRight: 4 }}
              />
              {doc.file_type.toUpperCase()}
              {doc.size_kb != null && ` · ${(doc.size_kb / 1024).toFixed(1)} MB`}
              {doc.pages != null && ` · ${doc.pages} pp`}
            </span>
            <span>
              · chunk_strategy{' '}
              <b style={{ color: 'oklch(var(--foreground))' }}>
                {doc.chunk_strategy ?? '—'}
              </b>
            </span>
            <span>
              · {doc.total_chunks} chunks ({doc.low_value_chunks} low_value)
            </span>
            {doc.total_tokens != null && (
              <span>· {doc.total_tokens.toLocaleString()} tokens</span>
            )}
            <span>· {doc.total_images} embedded images</span>
          </div>
        </div>
        <div className="page-actions">
          {doc.source_url && (
            <a
              href={doc.source_url}
              target="_blank"
              rel="noreferrer"
              className="btn btn-secondary btn-sm"
            >
              <LinkIcon size={13} /> Open source
            </a>
          )}
          <button type="button" className="btn btn-secondary btn-sm" disabled>
            <RefreshCw size={13} /> Re-process
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            style={{ color: 'oklch(var(--destructive))' }}
            disabled
          >
            <Trash2 size={13} /> Delete
          </button>
        </div>
      </div>

      {/* Pipeline stages strip */}
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="card-body" style={{ padding: 0 }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
            }}
          >
            {[
              {
                label: 'Parse',
                value:
                  doc.parse_duration_ms != null
                    ? `${doc.parse_duration_ms}ms`
                    : '—',
                sub: 'Docling layout-aware',
              },
              {
                label: 'Extract',
                value: `${doc.total_images} imgs`,
                sub: 'SHA256 dedup applied',
              },
              {
                label: 'Chunk',
                value: `${doc.total_chunks} chunks`,
                sub: `${doc.chunk_strategy ?? 'auto'} strategy`,
              },
              {
                label: 'Embed',
                value:
                  doc.embed_duration_ms != null
                    ? `${doc.embed_duration_ms}ms`
                    : '—',
                sub: `${kb.config.embedding_model} ${kb.config.embedding_dimension}d`,
              },
              {
                label: 'Index',
                value: 'upserted',
                sub: `ekp-kb-${kbId}-v1`,
              },
            ].map((s, i) => (
              <div
                key={s.label}
                style={{
                  padding: '14px 18px',
                  borderRight:
                    i < 4 ? '1px solid oklch(var(--border))' : 'none',
                  display: 'flex',
                  gap: 12,
                  alignItems: 'center',
                }}
              >
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 'var(--radius-sm)',
                    background: 'oklch(var(--success) / 0.12)',
                    color: 'oklch(var(--success))',
                    display: 'grid',
                    placeItems: 'center',
                    flexShrink: 0,
                  }}
                  title={
                    s.value === '—'
                      ? 'Stage timing — Wave C+ instrumentation'
                      : undefined
                  }
                >
                  <Layers size={15} />
                </div>
                <div>
                  <div
                    className="text-xs muted mono"
                    style={{
                      letterSpacing: '0.04em',
                      textTransform: 'uppercase',
                      marginBottom: 2,
                    }}
                  >
                    {s.label}
                  </div>
                  <div
                    style={{
                      fontSize: 13.5,
                      fontWeight: 600,
                      fontFamily: 'var(--font-mono)',
                    }}
                  >
                    {s.value}
                  </div>
                  <div className="text-xs muted">{s.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Image strip — horizontal scroll of inline ImageThumb */}
      {doc.image_refs.length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header">
            <div>
              <h3 className="card-title">
                Extracted images{' '}
                <span
                  className="text-xs muted mono"
                  style={{ marginLeft: 6 }}
                >
                  {doc.image_refs.length} total · SHA256 deduplicated
                </span>
              </h3>
              <div className="card-desc">
                Each chunk references images via{' '}
                <span className="mono">embedded_image_positions</span>;
                orchestrator resolves to{' '}
                <span className="mono">ImageRef.blob_url</span>.
              </div>
            </div>
            <Link
              href={`/kb/${kbId}?tab=images`}
              className="btn btn-ghost btn-sm"
            >
              View all in Image Library →
            </Link>
          </div>
          <div className="card-body" style={{ padding: '14px 18px' }}>
            <div
              style={{
                display: 'flex',
                gap: 10,
                overflowX: 'auto',
                paddingBottom: 4,
              }}
            >
              {doc.image_refs.map((img, i) => (
                <ImageThumb key={img.checksum_sha256} img={img} idx={i} />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 3-pane main: outline 240 / chunk list 1fr / inspector 380 */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '240px 1fr 380px',
          gap: 16,
        }}
      >
        {/* Left: outline */}
        <div
          className="card"
          style={{ alignSelf: 'start', position: 'sticky', top: 16 }}
        >
          <div className="card-header" style={{ padding: '10px 14px' }}>
            <div>
              <h3 className="card-title" style={{ fontSize: 12.5 }}>
                Document outline
              </h3>
            </div>
          </div>
          <div
            className="card-body card-body-tight"
            style={{
              maxHeight: 540,
              overflowY: 'auto',
              padding: '6px 0',
            }}
          >
            {doc.outline.length === 0 ? (
              <div className="text-xs muted" style={{ padding: '8px 14px' }}>
                (No structured outline — text-only doc.)
              </div>
            ) : (
              doc.outline.map((s, i) => {
                const key = `${s.level}|${s.title}|${i}`;
                const active = activeOutlinePath === key;
                return (
                  <div
                    key={key}
                    onClick={() => setActiveOutlinePath(key)}
                    style={{
                      padding: `5px ${14}px 5px ${14 + (s.level - 1) * 14}px`,
                      fontSize: s.level === 1 ? 12.5 : 12,
                      fontWeight: s.level === 1 ? 600 : 450,
                      background: active
                        ? 'oklch(var(--accent) / 0.08)'
                        : 'transparent',
                      color: active
                        ? 'oklch(var(--accent))'
                        : 'oklch(var(--foreground))',
                      borderLeft: active
                        ? '2px solid oklch(var(--accent))'
                        : '2px solid transparent',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      cursor: 'default',
                      lineHeight: 1.4,
                    }}
                  >
                    <span style={{ flex: 1 }}>{s.title}</span>
                    <span className="text-xs muted mono">{s.chunk_count}</span>
                  </div>
                );
              })
            )}
          </div>
          <div className="card-footer" style={{ padding: '8px 12px' }}>
            <span className="text-xs muted mono">
              {doc.outline.length} sections
            </span>
            <button type="button" className="btn btn-ghost btn-xs" disabled>
              Export TOC
            </button>
          </div>
        </div>

        {/* Center: chunk list */}
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Chunks</h3>
              <div className="card-desc">
                {chunkList.length.toLocaleString()} chunks in this document
              </div>
            </div>
            <div className="row">
              <button
                type="button"
                className="btn btn-secondary btn-xs"
                disabled
              >
                <Filter size={12} /> All
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-xs"
                disabled
              >
                <Layers size={12} /> With images
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-xs muted"
                disabled
              >
                low_value
              </button>
            </div>
          </div>
          <div className="card-body card-body-tight">
            {chunksQuery.isLoading && (
              <div style={{ padding: 14 }} className="text-xs muted">
                Loading chunks…
              </div>
            )}
            {chunksQuery.isError && (
              <div style={{ padding: 14 }} className="text-xs">
                Failed to load chunks:{' '}
                {String((chunksQuery.error as Error)?.message)}
              </div>
            )}
            {chunkList.length === 0 && !chunksQuery.isLoading && (
              <div className="text-xs muted" style={{ padding: 14 }}>
                No chunks listed.
              </div>
            )}
            {chunkList.map((c, i) => {
              const active = selectedChunkIdx === i;
              return (
                <div
                  key={c.chunk_id}
                  onClick={() => setSelectedChunkIdx(i)}
                  style={{
                    padding: '14px 18px',
                    borderBottom:
                      i < chunkList.length - 1
                        ? '1px solid oklch(var(--border))'
                        : 'none',
                    background: active
                      ? 'oklch(var(--muted) / 0.5)'
                      : 'transparent',
                    borderLeft: active
                      ? '2px solid oklch(var(--accent))'
                      : '2px solid transparent',
                    cursor: 'default',
                    opacity: c.low_value_flag ? 0.65 : 1,
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      marginBottom: 6,
                    }}
                  >
                    <span
                      className="mono text-xs"
                      style={{
                        background: 'oklch(var(--muted))',
                        padding: '1px 6px',
                        borderRadius: 3,
                        fontWeight: 600,
                      }}
                    >
                      #{c.chunk_index}
                    </span>
                    <div className="section-path text-xs" style={{ flex: 1 }}>
                      {c.section_path.map((s, j) => (
                        <span key={j}>{s}</span>
                      ))}
                    </div>
                    {c.embedded_image_count > 0 && (
                      <span className="badge badge-accent">
                        embedded_images{' '}
                        <b style={{ marginLeft: 2 }}>{c.embedded_image_count}</b>
                      </span>
                    )}
                    {c.low_value_flag && (
                      <span className="badge badge-warning">low_value</span>
                    )}
                  </div>
                  <div
                    style={{
                      fontSize: 13,
                      fontWeight: 500,
                      marginBottom: 4,
                    }}
                  >
                    {c.chunk_title}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: chunk inspector */}
        <div
          className="col"
          style={{ gap: 16, alignSelf: 'start', position: 'sticky', top: 16 }}
        >
          {selectedChunk && (
            <ChunkInspector
              chunk={selectedChunk}
              embeddingDim={kb.config.embedding_dimension}
              embeddingModel={kb.config.embedding_model}
            />
          )}
          {!selectedChunk && (
            <div className="card">
              <div className="card-body">
                <div className="text-xs muted">
                  Select a chunk to inspect metadata + embedding preview.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── ImageThumb ──────────────────────────────────────────────────────────────
function ImageThumb({ img, idx }: { img: ImageRef; idx: number }) {
  const colors = [
    'oklch(var(--accent))',
    'oklch(0.62 0.13 200)',
    'oklch(0.65 0.14 145)',
    'oklch(0.60 0.16 285)',
    'oklch(0.65 0.18 25)',
  ];
  const c = colors[idx % colors.length];
  // BUG-015 + Issue-1 H7 deviation (user-authorized 2026-05-24 Option B):
  // render real screenshot thumbnail via the BUG-015-emit proxy URL with
  // onError fallback to the mockup gradient + Layers placeholder (same
  // pattern as BUG-011 in `app/(app)/kb/[id]/page.tsx` `ImageCard`). Mockup's
  // pure-gradient `ImageThumb` is a static-prototype limitation (no image
  // server when the HTML mockup ran), not a design choice.
  const [imgError, setImgError] = useState(false);
  const showPlaceholder = !img.blob_url || imgError;
  return (
    <div
      title={img.alt_text}
      style={{
        flexShrink: 0,
        width: 140,
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
        background: 'oklch(var(--card))',
        cursor: 'default',
      }}
    >
      <div
        style={{
          height: 78,
          position: 'relative',
          ...(showPlaceholder
            ? {
                backgroundImage: `linear-gradient(135deg, ${c.replace(
                  ')',
                  ' / 0.2)',
                )}, ${c.replace(')', ' / 0.05)')})`,
                display: 'grid',
                placeItems: 'center',
                color: c,
              }
            : { background: 'oklch(var(--muted) / 0.4)' }),
        }}
      >
        {showPlaceholder ? (
          <Layers size={20} />
        ) : (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={img.blob_url}
            alt={img.alt_text || 'embedded image thumbnail'}
            loading="lazy"
            onError={() => setImgError(true)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display: 'block',
            }}
          />
        )}
      </div>
      <div style={{ padding: '6px 8px' }}>
        <div
          className="text-xs"
          style={{
            fontWeight: 500,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            lineHeight: 1.3,
          }}
        >
          {img.alt_text || '—'}
        </div>
        <div
          className="text-xs muted mono"
          style={{ marginTop: 2 }}
        >
          {img.width}×{img.height}
        </div>
      </div>
    </div>
  );
}

// ── ChunkInspector ──────────────────────────────────────────────────────────
// Synthetic 24-dim embedding vector preview per mockup ChunkInspector lines
// 343-353 (F6.4 — H7 mockup wins; real Azure Search vector exposure stays
// Tier 2 but user-invisible).
const SYNTHETIC_VECTOR_PREVIEW = [
  0.024, -0.018, 0.092, 0.144, -0.061, 0.027, -0.084, 0.117,
  0.038, -0.052, 0.071, 0.094, -0.022, 0.013, -0.046, 0.082,
  0.041, -0.029, 0.068, 0.075, -0.034, 0.018, -0.011, 0.063,
];

function ChunkInspector({
  chunk,
  embeddingDim,
  embeddingModel,
}: {
  chunk: ChunkSummary;
  embeddingDim: number;
  embeddingModel: string;
}) {
  return (
    <>
      <div className="card">
        <div className="card-header" style={{ padding: '12px 16px' }}>
          <div>
            <h3 className="card-title" style={{ fontSize: 13 }}>
              Chunk inspector
            </h3>
            <div
              className="text-xs muted mono"
              style={{ marginTop: 2, wordBreak: 'break-all' }}
            >
              {chunk.chunk_id}
            </div>
          </div>
          <div className="row">
            <button
              type="button"
              className="btn btn-ghost btn-icon btn-xs"
              aria-label="Copy chunk id"
              onClick={() => {
                void navigator.clipboard.writeText(chunk.chunk_id);
              }}
            >
              <Copy size={12} />
            </button>
            <button
              type="button"
              className="btn btn-ghost btn-icon btn-xs"
              aria-label="Edit"
              disabled
            >
              <Edit size={12} />
            </button>
          </div>
        </div>
        <div className="card-body" style={{ padding: 14 }}>
          {/* metadata */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: 5,
              marginBottom: 12,
            }}
          >
            <span className="badge badge-muted">
              chunk_index{' '}
              <b style={{ marginLeft: 2 }}>{chunk.chunk_index}</b>
            </span>
            <span className="badge badge-muted">
              of <b style={{ marginLeft: 2 }}>{chunk.chunk_total}</b>
            </span>
            {chunk.low_value_flag && (
              <span className="badge badge-warning">low_value</span>
            )}
            {!chunk.enabled && (
              <span className="badge badge-error">disabled</span>
            )}
          </div>

          {/* section_path */}
          <div
            className="text-xs muted mono"
            style={{
              marginBottom: 4,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            section_path
          </div>
          <div
            className="section-path"
            style={{ fontSize: 12, marginBottom: 12 }}
          >
            {chunk.section_path.map((s, j) => (
              <span key={j}>{s}</span>
            ))}
          </div>

          {/* prev/next */}
          <div
            className="text-xs muted mono"
            style={{
              marginBottom: 4,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Linked chunks
          </div>
          <div
            className="text-xs mono"
            style={{
              marginBottom: 14,
              color: 'oklch(var(--muted-foreground))',
            }}
          >
            ←{' '}
            <span style={{ color: 'oklch(var(--accent))' }}>
              chunk-{String(chunk.chunk_index - 1).padStart(4, '0')}
            </span>{' '}
            · this ·{' '}
            <span style={{ color: 'oklch(var(--accent))' }}>
              chunk-{String(chunk.chunk_index + 1).padStart(4, '0')}
            </span>{' '}
            →
          </div>

          {/* embedding preview — mockup synthetic per F6.4 */}
          <div
            className="text-xs muted mono"
            style={{
              marginBottom: 6,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Embedding vector{' '}
            <span
              style={{
                fontWeight: 500,
                color: 'oklch(var(--foreground))',
              }}
            >
              {embeddingDim}d
            </span>
          </div>
          <div
            style={{
              border: '1px solid oklch(var(--border))',
              borderRadius: 'var(--radius-sm)',
              background: 'oklch(var(--muted) / 0.4)',
              padding: 10,
              fontFamily: 'var(--font-mono)',
              fontSize: 10.5,
              lineHeight: 1.5,
              display: 'grid',
              gridTemplateColumns: 'repeat(8, 1fr)',
              gap: '2px 6px',
              color: 'oklch(var(--muted-foreground))',
            }}
          >
            {SYNTHETIC_VECTOR_PREVIEW.map((v, i) => (
              <span
                key={i}
                style={{
                  color:
                    v > 0
                      ? 'oklch(var(--accent))'
                      : 'oklch(var(--foreground))',
                }}
              >
                {v.toFixed(3)}
              </span>
            ))}
            <span
              style={{
                gridColumn: '1 / -1',
                color: 'oklch(var(--muted-foreground))',
                marginTop: 4,
              }}
            >
              … +{embeddingDim - SYNTHETIC_VECTOR_PREVIEW.length} more dims …
            </span>
          </div>
        </div>
        <div className="card-footer" style={{ padding: '8px 14px' }}>
          <div className="text-xs muted mono">
            {embeddingModel} · MRL truncate {embeddingDim}d
          </div>
          <button type="button" className="btn btn-ghost btn-xs" disabled>
            Full JSON →
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-body" style={{ padding: 14 }}>
          <div
            className="text-xs muted mono"
            style={{
              marginBottom: 6,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            Chunk text
          </div>
          <div
            style={{
              background: 'oklch(var(--muted) / 0.4)',
              border: '1px solid oklch(var(--border))',
              borderRadius: 'var(--radius-sm)',
              padding: '10px 12px',
              fontSize: 12.5,
              lineHeight: 1.6,
              maxHeight: 220,
              overflowY: 'auto',
            }}
          >
            <div
              style={{ fontWeight: 500, marginBottom: 6 }}
            >
              {chunk.chunk_title}
            </div>
            <div className="text-xs muted">
              Body text not surfaced via list_chunks (chunk_text_preview only
              via retrieval-test or /query). Use Retrieval Testing tab for full
              chunk text.
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

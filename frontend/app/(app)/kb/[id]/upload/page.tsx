'use client';

/**
 * /kb/[id]/upload — KB Pipeline Wizard per architecture.md v6 §5.5.3b + ADR-0028.
 *
 * W22 F6.2 rebuild per CLAUDE.md §5.7 H7 — 100% mockup fidelity match against
 * references/design-mockups/ekp-page-misc.jsx:4 PageUploadWizard 3-step
 * (Data source / Document processing / Execute).
 *
 * Backend integration preserved (per F6.5):
 *   useMutation(kbApi.uploadDoc) — single-file per call (architecture.md §3.3
 *   POST /kb/{id}/documents). Mockup Step 1 multi-doc drag-drop UI is
 *   aspirational; real impl single-file via input[type=file] + drag-and-drop
 *   styling. Backend wins per CLAUDE.md §13 When-in-Doubt.
 *
 * Mockup wizard stepper styling (per W22 D2 audit):
 *   - 28px circle + 2px border on active + transition 0.2s
 *   - letterSpacing: -0.005em on active label
 *   - divider margin 0 4px
 *   Rule-of-3 wizard primitive promotion DEFERRED W23+ per W22 F5.3
 *   (mockup has only 2 stepper wizards; threshold 3+未達).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  Check,
  ChevronLeft,
  ChevronRight,
  Cloud,
  Globe,
  Layers,
  Link as LinkIcon,
  Upload,
} from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { Fragment, useState, type ChangeEvent, type DragEvent } from 'react';

import {
  kbApi,
  ScanRequiresConfirmError,
  type KbConfig,
  type KbStatus,
} from '@/lib/api/kb';

type Step = 0 | 1 | 2;
type SourceKind = 'upload' | 'sharepoint' | 'drive' | 'url';

const STEPS: { id: Step; label: string; hint: string }[] = [
  { id: 0, label: 'Data source', hint: 'Pick where docs come from' },
  { id: 1, label: 'Document processing', hint: 'Chunker + embedder' },
  { id: 2, label: 'Execute', hint: 'Index + monitor progress' },
];

export default function KbUploadPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [step, setStep] = useState<Step>(0);
  const [source, setSource] = useState<SourceKind>('upload');
  const [file, setFile] = useState<File | null>(null);

  const kbQuery = useQuery({
    queryKey: ['kb', params.id],
    queryFn: () => kbApi.get(params.id),
  });

  const uploadMutation = useMutation({
    // W84 (ADR-0065) — forceScan flows through so the "仍要繼續" force-confirm retry
    // can re-run the same upload past the backend P4 scan guard.
    mutationFn: (vars: { file: File; forceScan: boolean }) =>
      kbApi.uploadDoc(params.id, vars.file, vars.forceScan),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['kb', params.id] });
      void queryClient.invalidateQueries({ queryKey: ['kb'] });
    },
  });

  const kb = kbQuery.data;

  return (
    <div className="content">
      <div className="content-narrow">
        <div className="page-header">
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                marginBottom: 4,
              }}
            >
              <Link
                href={`/kb/${params.id}`}
                className="btn btn-ghost btn-xs btn-ghost-muted"
              >
                <ChevronLeft size={12} /> {kb?.name || params.id}
              </Link>
            </div>
            <h1 className="page-title">Upload documents</h1>
            <p className="page-subtitle">
              Add documents to <span className="mono">ekp-kb-{params.id}-v1</span>.
              New chunks are embedded with{' '}
              <span className="mono">{kb?.config.embedding_model ?? 'text-embedding-3-large'}</span>
              {' '}
              ({kb?.config.embedding_dimension ?? 1024}d) and upserted to Azure AI
              Search.
            </p>
          </div>
        </div>

        {/* Step indicator — mockup 28px circle + letterSpacing -0.005em + transition + divider */}
        <div className="card" style={{ marginBottom: 16, overflow: 'visible' }}>
          <div
            style={{
              display: 'flex',
              padding: '18px 24px',
              alignItems: 'center',
              gap: 12,
            }}
          >
            {STEPS.map((s, i) => (
              <Fragment key={s.id}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    cursor: 'default',
                  }}
                  onClick={() => {
                    // Allow going back to a previous step only
                    if (s.id <= step) setStep(s.id);
                  }}
                >
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background:
                        step >= s.id
                          ? 'oklch(var(--primary))'
                          : 'oklch(var(--muted))',
                      color:
                        step >= s.id
                          ? 'oklch(var(--primary-foreground))'
                          : 'oklch(var(--muted-foreground))',
                      display: 'grid',
                      placeItems: 'center',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                      fontSize: 12,
                      border:
                        step === s.id ? '2px solid oklch(var(--accent))' : '0',
                      transition: 'all 0.2s',
                    }}
                  >
                    {step > s.id ? <Check size={14} /> : i + 1}
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: 13.5,
                        fontWeight: step === s.id ? 600 : 500,
                        letterSpacing: '-0.005em',
                      }}
                    >
                      {s.label}
                    </div>
                    <div className="text-xs muted">{s.hint}</div>
                  </div>
                </div>
                {i < STEPS.length - 1 && (
                  <div
                    style={{
                      flex: 1,
                      height: 1,
                      background:
                        step > i
                          ? 'oklch(var(--foreground))'
                          : 'oklch(var(--border))',
                      margin: '0 4px',
                    }}
                  />
                )}
              </Fragment>
            ))}
          </div>
        </div>

        {step === 0 && (
          <StepDataSource
            source={source}
            file={file}
            onSourceChange={setSource}
            onFileChange={setFile}
            onNext={() => setStep(1)}
          />
        )}
        {step === 1 && (
          <StepDocumentProcessing
            kb={kb}
            onBack={() => setStep(0)}
            onNext={() => setStep(2)}
          />
        )}
        {step === 2 && (
          <StepExecute
            kbId={params.id}
            file={file}
            kb={kb}
            isPending={uploadMutation.isPending}
            isSuccess={uploadMutation.isSuccess}
            error={uploadMutation.error as Error | null}
            onBack={() => setStep(1)}
            onRun={() => {
              if (file) uploadMutation.mutate({ file, forceScan: false });
            }}
            onForceRun={() => {
              if (file) uploadMutation.mutate({ file, forceScan: true });
            }}
            onDone={() => router.push(`/kb/${params.id}`)}
          />
        )}
      </div>
    </div>
  );
}

// ── Step 0 — Data source ────────────────────────────────────────────────────
function StepDataSource({
  source,
  file,
  onSourceChange,
  onFileChange,
  onNext,
}: {
  source: SourceKind;
  file: File | null;
  onSourceChange: (s: SourceKind) => void;
  onFileChange: (f: File | null) => void;
  onNext: () => void;
}) {
  const [isDragging, setIsDragging] = useState(false);
  const sources: {
    id: SourceKind;
    label: string;
    hint: string;
    icon: typeof Upload;
    ready: boolean;
  }[] = [
    {
      id: 'upload',
      label: 'Local files',
      hint: '.docx, .pdf, .pptx · Drag & drop',
      icon: Upload,
      ready: true,
    },
    {
      id: 'sharepoint',
      label: 'SharePoint',
      hint: 'OAuth-connected sites & libraries',
      icon: Cloud,
      ready: false,
    },
    {
      id: 'drive',
      label: 'Drive folder',
      hint: 'Mounted share folder · network path',
      icon: Globe,
      ready: false,
    },
    {
      id: 'url',
      label: 'URL crawler',
      hint: 'Tier 2 — disabled',
      icon: LinkIcon,
      ready: false,
    },
  ];

  function handleFileInput(e: ChangeEvent<HTMLInputElement>) {
    onFileChange(e.target.files?.[0] ?? null);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) onFileChange(dropped);
  }

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Data source</h3>
      </div>
      <div className="card-body">
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 10,
            marginBottom: 20,
          }}
        >
          {sources.map((s) => {
            const Ic = s.icon;
            const active = source === s.id;
            return (
              <div
                key={s.id}
                onClick={() => s.ready && onSourceChange(s.id)}
                style={{
                  border: `1px solid ${
                    active ? 'oklch(var(--accent))' : 'oklch(var(--border))'
                  }`,
                  background: active
                    ? 'oklch(var(--accent) / 0.05)'
                    : 'oklch(var(--card))',
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  gap: 12,
                  alignItems: 'flex-start',
                  opacity: s.ready ? 1 : 0.5,
                  cursor: 'default',
                  transition: 'border-color 0.15s',
                }}
              >
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 'var(--radius-sm)',
                    background: active
                      ? 'oklch(var(--accent) / 0.15)'
                      : 'oklch(var(--muted))',
                    color: active
                      ? 'oklch(var(--accent))'
                      : 'oklch(var(--foreground))',
                    display: 'grid',
                    placeItems: 'center',
                    flexShrink: 0,
                  }}
                >
                  <Ic size={16} />
                </div>
                <div style={{ flex: 1 }}>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span style={{ fontWeight: 500 }}>{s.label}</span>
                    {!s.ready && (
                      <span className="badge badge-muted">SOON</span>
                    )}
                  </div>
                  <div className="text-xs muted" style={{ marginTop: 2 }}>
                    {s.hint}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {source === 'upload' && (
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            style={{
              border: `2px dashed ${
                isDragging
                  ? 'oklch(var(--accent))'
                  : 'oklch(var(--border-strong))'
              }`,
              borderRadius: 'var(--radius-md)',
              padding: '40px 24px',
              textAlign: 'center',
              background: isDragging
                ? 'oklch(var(--accent) / 0.04)'
                : 'oklch(var(--muted) / 0.3)',
              transition: 'border-color 0.15s, background 0.15s',
            }}
          >
            <div
              style={{
                display: 'inline-flex',
                padding: 12,
                borderRadius: '50%',
                background: 'oklch(var(--accent) / 0.1)',
                color: 'oklch(var(--accent))',
                marginBottom: 12,
              }}
            >
              <Upload size={24} />
            </div>
            <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
              {file ? file.name : 'Drag and drop a document here'}
            </div>
            <div className="text-sm muted">
              {file ? `${(file.size / 1024).toFixed(1)} KB` : 'or click to browse'}
            </div>
            <div
              className="text-xs muted mono"
              style={{ marginTop: 14 }}
            >
              Accepted: .docx · .pdf · .pptx
            </div>
            <label
              className="btn btn-secondary btn-sm"
              style={{ marginTop: 14, cursor: 'pointer', display: 'inline-flex' }}
            >
              <input
                type="file"
                accept=".docx,.pdf,.pptx"
                onChange={handleFileInput}
                style={{ display: 'none' }}
              />
              {file ? 'Choose another file' : 'Browse files…'}
            </label>
          </div>
        )}

        {source === 'sharepoint' && (
          <div
            style={{
              padding: 24,
              textAlign: 'center',
              border: '1px solid oklch(var(--border))',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <div className="text-sm">
              <b>SharePoint site URL</b>
              <br />
              <input
                className="input mono"
                style={{ marginTop: 8, maxWidth: 480 }}
                placeholder="https://ricoh.sharepoint.com/sites/D365-Docs"
                disabled
              />
            </div>
            <div className="text-xs muted" style={{ marginTop: 10 }}>
              OAuth via Entra ID · scoped read-only · Wave C+
            </div>
          </div>
        )}
      </div>
      <div className="card-footer">
        <div className="text-xs muted mono">Step 1 of 3</div>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          disabled={!file || source !== 'upload'}
          onClick={onNext}
        >
          Continue <ChevronRight size={13} />
        </button>
      </div>
    </div>
  );
}

// ── Step 1 — Document processing ────────────────────────────────────────────
function StepDocumentProcessing({
  kb,
  onBack,
  onNext,
}: {
  kb: KbStatus | undefined;
  onBack: () => void;
  onNext: () => void;
}) {
  // Per CLAUDE.md §13 backend-wins: chunker config is KB-locked (architecture.md
  // §3.3 + §3.5);mockup allows per-batch override but real backend uses
  // kb_config from KbConfig at ingest time. Surface as READ-ONLY display of
  // current KB config with "Edit settings" link to /kb/[id]?tab=settings.
  const strategy = kb?.config.chunk_strategy ?? 'auto';
  const chunkSize = 800;
  const overlap = 100;

  const strategies: {
    id: KbConfig['chunk_strategy'];
    label: string;
    hint: string;
  }[] = [
    {
      id: 'heading_aware',
      label: 'Heading-aware',
      hint: 'Splits at H1/H2/H3 — for narrative docs',
    },
    {
      id: 'layout_aware',
      label: 'Layout-aware',
      hint: 'Docling — preserves tables, lists, sections',
    },
    {
      id: 'slide_based',
      label: 'Slide-based',
      hint: 'python-pptx — one chunk per slide',
    },
    {
      id: 'auto',
      label: 'Auto',
      hint: 'Detect doc type, pick strategy',
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Document processing</h3>
        <span className="text-xs muted">KB-locked · per-KB config</span>
      </div>
      <div className="card-body">
        <div className="field">
          <label className="label">Chunk strategy</label>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 10,
            }}
          >
            {strategies.map((s) => {
              const active = strategy === s.id;
              return (
                <div
                  key={s.id}
                  style={{
                    border: `1px solid ${
                      active
                        ? 'oklch(var(--foreground))'
                        : 'oklch(var(--border))'
                    }`,
                    background: active
                      ? 'oklch(var(--muted) / 0.6)'
                      : 'transparent',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'default',
                    opacity: active ? 1 : 0.6,
                  }}
                >
                  <div
                    style={{ display: 'flex', alignItems: 'center', gap: 6 }}
                  >
                    <span style={{ fontWeight: 500, fontSize: 13.5 }}>
                      {s.label}
                    </span>
                    {active && <Check size={12} />}
                  </div>
                  <div className="text-xs muted" style={{ marginTop: 2 }}>
                    {s.hint}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}
        >
          <div className="field">
            <label className="label">Chunk size (tokens)</label>
            <input
              className="input mono"
              value={chunkSize}
              readOnly
              disabled
            />
            <div className="hint">
              Effective max: 800 — fits within text-embedding-3-large 8k window
            </div>
          </div>
          <div className="field">
            <label className="label">Overlap (tokens)</label>
            <input
              className="input mono"
              value={overlap}
              readOnly
              disabled
            />
            <div className="hint">Recommended: 100–150 for layout_aware</div>
          </div>
        </div>

        <div className="field">
          <label className="label">
            Embedding model <span className="text-xs muted">— KB-locked</span>
          </label>
          <select className="select" disabled>
            <option>
              {kb?.config.embedding_model ?? 'text-embedding-3-large'} ·{' '}
              {kb?.config.embedding_dimension ?? 1024}d MRL truncate
            </option>
          </select>
        </div>

        <div className="row" style={{ gap: 8, marginTop: 8 }}>
          <span
            className="switch"
            data-on={kb?.config.extract_embedded_images ?? false}
            role="switch"
            aria-checked={kb?.config.extract_embedded_images ?? false}
            aria-disabled="true"
          />
          <div>
            <div style={{ fontSize: 13, fontWeight: 500 }}>
              Extract embedded screenshots
            </div>
            <div className="text-xs muted">
              Maps images via{' '}
              <span className="mono">embedded_images[]</span> + screenshot
              pipeline
            </div>
          </div>
        </div>

        <div className="banner banner-info" style={{ marginTop: 16 }}>
          <div style={{ flex: 1 }} className="text-xs">
            Per-batch override 唔 supported — config is KB-locked. To change
            chunking + multimodal,{' '}
            <Link
              href={`/kb/${kb?.kb_id ?? ''}?tab=settings`}
              style={{ color: 'oklch(var(--accent))' }}
            >
              edit KB Settings
            </Link>
            .
          </div>
        </div>
      </div>
      <div className="card-footer">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={onBack}
        >
          <ChevronLeft size={13} /> Back
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={onNext}
        >
          Continue <ChevronRight size={13} />
        </button>
      </div>
    </div>
  );
}

// ── Step 2 — Execute ────────────────────────────────────────────────────────
function StepExecute({
  kbId,
  file,
  kb,
  isPending,
  isSuccess,
  error,
  onBack,
  onRun,
  onForceRun,
  onDone,
}: {
  kbId: string;
  file: File | null;
  kb: KbStatus | undefined;
  isPending: boolean;
  isSuccess: boolean;
  error: Error | null;
  onBack: () => void;
  onRun: () => void;
  onForceRun: () => void;
  onDone: () => void;
}) {
  // W84 (ADR-0065) — a ScanRequiresConfirmError is NOT a failure: the backend P4
  // guard wants the user to confirm OCR (~8–9.5 min). Surface it as its own
  // "scan-confirm" state (warning banner + "仍要繼續" force button), not a red FAILED.
  const isScanConfirm =
    !isPending && !isSuccess && error instanceof ScanRequiresConfirmError;
  const status: 'idle' | 'running' | 'indexed' | 'failed' | 'scan-confirm' =
    isPending
      ? 'running'
      : isSuccess
        ? 'indexed'
        : isScanConfirm
          ? 'scan-confirm'
          : error
            ? 'failed'
            : 'idle';

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">Execute · indexing</h3>
          <div className="card-desc">
            {status === 'idle' && 'Ready to upload + ingest'}
            {status === 'running' && 'Pipeline running…'}
            {status === 'indexed' && 'Document indexed — KB ready'}
            {status === 'scan-confirm' && '掃描件需確認 — OCR 需時較長'}
            {status === 'failed' && 'Upload failed — see error below'}
          </div>
        </div>
        {status === 'running' && (
          <span className="badge badge-info">
            <span className="badge-dot" /> RUNNING
          </span>
        )}
        {status === 'indexed' && (
          <span className="badge badge-success">
            <span className="badge-dot" /> INDEXED
          </span>
        )}
        {status === 'scan-confirm' && (
          <span className="badge badge-warning">
            <span className="badge-dot" /> 需確認
          </span>
        )}
        {status === 'failed' && (
          <span className="badge badge-error">
            <span className="badge-dot" /> FAILED
          </span>
        )}
      </div>
      <div className="card-body">
        {status === 'running' && (
          <div className="banner banner-info" style={{ marginBottom: 16 }}>
            <span className="spinner" />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>
                Indexing {file?.name ?? 'document'} · in progress
              </div>
              <div className="text-xs muted mono">
                Docling → {kb?.config.chunk_strategy ?? 'auto'} → embed-3-large →
                ekp-kb-{kbId}-v1 upsert
              </div>
            </div>
          </div>
        )}

        {/* W84 / ADR-0065 — P4 scan pre-parse guard. The backend 422'd before the
            slow OCR parse; surface a warning + 「仍要繼續」force button (banner-warning
            primitive 復用視覺零發明 per plan §3-4). */}
        {status === 'scan-confirm' && (
          <div className="banner banner-warning" style={{ marginBottom: 16 }}>
            <AlertTriangle
              size={15}
              style={{ color: 'oklch(var(--warning))', flexShrink: 0 }}
            />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 500 }}>
                {file?.name ?? '此文件'} 似乎是掃描件(無文字層)
              </div>
              <div className="text-xs muted" style={{ marginTop: 2 }}>
                需 OCR 辨識,同步處理約需 8–9.5 分鐘,期間此頁會持續等待。確認後按下方「仍要繼續」。
              </div>
            </div>
          </div>
        )}

        {/* W78 / ADR-0056 段③ — L1 自動文件分類說明 banner per mockup ekp-page-misc.jsx:266-273.
            mockup per-doc 即時 profile badge 需 multi-doc batch + upload-response-含-profile;
            frontend single-file flow + uploadDoc return {doc_id} 無 profile（W78 plan §4-3 §13
            backend-wins）→ 說明 banner + 完成後 redirect /kb/{id}（L2 table 即見 profile）。 */}
        {file && (
          <div className="banner banner-info" style={{ marginBottom: 16 }}>
            <Layers size={15} style={{ color: 'oklch(var(--info))', flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 13 }}>
                <b>自動文件分類(W72 profiler)</b> —
                ingest 時偵測每份文件 profile,自動套對應 recall preset。
              </div>
              <div className="text-xs muted" style={{ marginTop: 2 }}>
                偵測錯可去文件詳情頁一鍵覆寫 · ADR-0056 層 A
              </div>
            </div>
          </div>
        )}

        {/* Single-file progress card per backend reality (mockup multi-doc UI is
            aspirational; backend POST /kb/{id}/documents takes one file per
            call) */}
        <div className="col" style={{ gap: 6 }}>
          {file && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 14px',
                border: '1px solid oklch(var(--border))',
                borderRadius: 'var(--radius-sm)',
                background:
                  status === 'failed'
                    ? 'oklch(var(--destructive) / 0.04)'
                    : status === 'scan-confirm'
                      ? 'oklch(var(--warning) / 0.04)'
                      : 'oklch(var(--card))',
              }}
            >
              <span
                className={`status-dot ${
                  status === 'indexed'
                    ? 'ready'
                    : status === 'running'
                      ? 'indexing'
                      : status === 'failed'
                        ? 'failed'
                        : status === 'scan-confirm'
                          ? 'queued'
                          : ''
                }`}
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 13,
                    fontWeight: 500,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {file.name}
                </div>
                {status === 'running' && (
                  <div className="text-xs muted mono" style={{ marginTop: 3 }}>
                    Embedding chunks · streaming…
                  </div>
                )}
                {status === 'failed' && error && (
                  <div
                    className="text-xs"
                    style={{
                      color: 'oklch(var(--destructive))',
                      marginTop: 2,
                    }}
                  >
                    {error.message}
                  </div>
                )}
              </div>
              <span className="text-xs mono muted">
                {(file.size / 1024).toFixed(1)} KB
              </span>
              <span
                className={`badge ${
                  status === 'indexed'
                    ? 'badge-success'
                    : status === 'running'
                      ? 'badge-info'
                      : status === 'failed'
                        ? 'badge-error'
                        : status === 'scan-confirm'
                          ? 'badge-warning'
                          : 'badge-muted'
                }`}
              >
                <span className="badge-dot" />{' '}
                {status === 'scan-confirm' ? '需確認' : status.toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {!file && (
          <div className="empty">
            <div className="empty-icon">
              <AlertTriangle size={20} />
            </div>
            <div className="empty-title">No file selected</div>
            <div>Go back to Step 1 + pick a document.</div>
          </div>
        )}
      </div>
      <div className="card-footer">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={onBack}
          disabled={isPending}
        >
          <ChevronLeft size={13} /> Back
        </button>
        {status === 'idle' && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={onRun}
            disabled={!file}
          >
            <Upload size={13} /> Upload + Ingest
          </button>
        )}
        {status === 'running' && (
          <button type="button" className="btn btn-secondary btn-sm" disabled>
            Uploading…
          </button>
        )}
        {status === 'indexed' && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={onDone}
          >
            Continue to KB <ChevronRight size={13} />
          </button>
        )}
        {status === 'scan-confirm' && (
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={onForceRun}
          >
            <Upload size={13} /> 仍要繼續(約 8–9.5 分鐘)
          </button>
        )}
        {status === 'failed' && (
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onRun}
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

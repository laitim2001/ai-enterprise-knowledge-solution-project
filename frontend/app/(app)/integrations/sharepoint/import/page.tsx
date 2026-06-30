'use client';

import { type Dispatch, Fragment, type SetStateAction, useEffect, useState } from 'react';

import Link from 'next/link';
import { Check, Folder } from 'lucide-react';
import { useMutation, useQuery } from '@tanstack/react-query';

import {
  integrationApi,
  type ImportSummary,
  type SourceContainer,
  type SourceDocumentRef,
} from '@/lib/api/integration';
import { kbApi } from '@/lib/api/kb';

/**
 * SharePoint import wizard — 4 steps (connect → select → import → done).
 *
 * H7 reproduction of `references/design-mockups/integration-import/20..23-*.html`.
 * Inline stepper + useState step state per existing wizard pattern (kb/new,
 * kb/[id]/upload), D-2 (no shared <Stepper> primitive). Step 1-2 here (F5);
 * step 3-4 in F6.
 *
 * #2 (D-4): credentials are NOT entered in the UI — they live server-side (.env /
 * Key Vault, H5). Step 1 shows a read-only "configured server-side" banner instead
 * of the mockup's tenant/app/credential input fields; "Test connection" verifies.
 */

const STEPS: ReadonlyArray<{ id: number; label: string; hint: string }> = [
  { id: 0, label: 'Connect', hint: 'SharePoint' },
  { id: 1, label: 'Select', hint: 'Sites & files' },
  { id: 2, label: 'Import', hint: 'Push to KB' },
  { id: 3, label: 'Done', hint: 'Summary' },
];

function ext(name: string): string {
  const dot = name.lastIndexOf('.');
  return dot >= 0 ? name.slice(dot + 1).toUpperCase() : 'FILE';
}

function fmtDate(iso?: string | null): string {
  return iso ? iso.slice(0, 10) : '—';
}

function fmtSize(bytes?: number | null): string {
  if (bytes == null) return '—';
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${Math.round(bytes / 1_000)} KB`;
  return `${bytes} B`;
}

export default function SharePointImportPage() {
  const [step, setStep] = useState(0);
  const [targetKb, setTargetKb] = useState('');
  const [siteUrl, setSiteUrl] = useState('');
  const [site, setSite] = useState<SourceContainer | null>(null);
  const [selectedRefs, setSelectedRefs] = useState<SourceDocumentRef[]>([]);
  // F6 — populated by step 3's import call, shown in step 4.
  const [summary, setSummary] = useState<ImportSummary | null>(null);

  const subtitle = [
    'Connect a site, pick documents, and import them through the EKP ingestion pipeline.',
    'Browse the site you connected, then pick documents to import.',
    'Documents run through the same Docling pipeline as uploads — image recall, profiles, per-KB config unchanged.',
    'Import finished. Review what landed and what needs attention.',
  ][step];

  return (
    <div className="content">
      <style>{`
        .sp-import .tree { display: flex; flex-direction: column; gap: 1px; }
        .sp-import .tree-row { display: flex; align-items: center; gap: 7px; padding: 5px 8px; border-radius: var(--radius-sm); font-size: 13px; cursor: pointer; color: oklch(var(--foreground)); }
        .sp-import .tree-row:hover { background: oklch(var(--muted)); }
        .sp-import .tree-row[data-active="true"] { background: oklch(var(--muted)); font-weight: 500; }
        .sp-import .tree-row svg { width: 15px; height: 15px; color: oklch(var(--muted-foreground)); flex-shrink: 0; }
        .sp-import .pick-table input[type=checkbox] { accent-color: oklch(var(--primary)); width: 14px; height: 14px; }
      `}</style>
      <div className="content-narrow sp-import">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
          <Link className="btn btn-ghost btn-xs btn-ghost-muted" href="/integrations">
            &#8249; Integrations
          </Link>
        </div>
        <div className="page-header">
          <div>
            <h1 className="page-title">Import from SharePoint</h1>
            <p className="page-subtitle">{subtitle}</p>
          </div>
        </div>

        {/* Stepper — mockup 20..23 lines (28px circle, kb/new pattern) */}
        <div className="card" style={{ marginBottom: 16, overflow: 'visible' }}>
          <div
            style={{ display: 'flex', padding: '18px 24px', alignItems: 'center', gap: 12 }}
          >
            {STEPS.map((s, i) => (
              <Fragment key={s.id}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div
                    style={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      background:
                        step >= s.id ? 'oklch(var(--primary))' : 'oklch(var(--muted))',
                      color:
                        step >= s.id
                          ? 'oklch(var(--primary-foreground))'
                          : 'oklch(var(--muted-foreground))',
                      display: 'grid',
                      placeItems: 'center',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 600,
                      fontSize: 12,
                      border: step === s.id ? '2px solid oklch(var(--accent))' : '0',
                    }}
                  >
                    {step > s.id ? <Check size={14} /> : i + 1}
                  </div>
                  <div>
                    <div style={{ fontSize: 13.5, fontWeight: step === s.id ? 600 : 500 }}>
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
                        step > i ? 'oklch(var(--foreground))' : 'oklch(var(--border))',
                    }}
                  />
                )}
              </Fragment>
            ))}
          </div>
        </div>

        {step === 0 && (
          <StepConnect
            targetKb={targetKb}
            setTargetKb={setTargetKb}
            siteUrl={siteUrl}
            setSiteUrl={setSiteUrl}
            site={site}
            onResolved={setSite}
            onContinue={() => setStep(1)}
          />
        )}
        {step === 1 && site && (
          <StepSelect
            site={site}
            selectedRefs={selectedRefs}
            setSelectedRefs={setSelectedRefs}
            onBack={() => setStep(0)}
            onImport={() => setStep(2)}
          />
        )}
        {step === 2 && (
          <StepImportPlaceholder
            count={selectedRefs.length}
            onDone={(s) => {
              setSummary(s);
              setStep(3);
            }}
          />
        )}
        {step === 3 && summary && <StepSummaryPlaceholder summary={summary} kbId={targetKb} />}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 1 — Connect (mockup 20-step1-connect.html)
// ──────────────────────────────────────────────────────────────────────────

interface StepConnectProps {
  targetKb: string;
  setTargetKb: Dispatch<SetStateAction<string>>;
  siteUrl: string;
  setSiteUrl: Dispatch<SetStateAction<string>>;
  site: SourceContainer | null;
  onResolved: (site: SourceContainer) => void;
  onContinue: () => void;
}

function StepConnect({
  targetKb,
  setTargetKb,
  siteUrl,
  setSiteUrl,
  site,
  onResolved,
  onContinue,
}: StepConnectProps) {
  const { data: kbs } = useQuery({ queryKey: ['kb', 'list'], queryFn: kbApi.list });
  const activeKbs = (kbs ?? []).filter((k) => !k.archived);

  const connect = useMutation({
    mutationFn: () => integrationApi.resolveSite(siteUrl),
    onSuccess: onResolved,
  });

  return (
    <>
      <div className="banner banner-info" style={{ marginBottom: 16 }}>
        <div style={{ flex: 1, fontSize: 12.5, lineHeight: 1.55 }}>
          Before importing, IT must grant this app{' '}
          <b>Sites.Selected (read)</b> on each target site (consent &ne; access).
          See blueprint &sect;1.3.
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Connect to SharePoint</h3>
          <div
            className="card-desc"
            style={{ fontSize: 12.5, color: 'oklch(var(--muted-foreground))' }}
          >
            Application (Sites.Selected) — least-privilege service account.
          </div>
        </div>
        <div className="card-body" style={{ display: 'grid', gap: 16 }}>
          <div className="field">
            <label className="label">Target knowledge base</label>
            <select
              className="select"
              value={targetKb}
              onChange={(e) => setTargetKb(e.target.value)}
            >
              <option value="">Select a knowledge base…</option>
              {activeKbs.map((k) => (
                <option key={k.kb_id} value={k.kb_id}>
                  {k.name}
                </option>
              ))}
            </select>
            <div className="hint">
              Imported documents are added to this KB. A KB can mix uploads + SharePoint.
            </div>
          </div>

          <div className="field">
            <label className="label">SharePoint site URL</label>
            <input
              className="input"
              placeholder="https://contoso.sharepoint.com/sites/manuals"
              value={siteUrl}
              onChange={(e) => setSiteUrl(e.target.value)}
            />
            <div className="hint">The site you granted Sites.Selected access to.</div>
          </div>

          {/* #2 / D-4 — credential is server-side (H5), not entered here. */}
          <div className="banner banner-info">
            <div style={{ flex: 1, fontSize: 12.5, lineHeight: 1.55 }}>
              Connection credentials (tenant, app, certificate / secret) are configured{' '}
              <b>server-side by your administrator</b> (H5 — never entered here, never
              committed). Use <b>Test connection</b> to verify access.
            </div>
          </div>

          <div className="row" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <button
              className="btn btn-secondary btn-sm"
              disabled={!siteUrl || connect.isPending}
              onClick={() => connect.mutate()}
            >
              {connect.isPending ? 'Testing…' : 'Test connection'}
            </button>
            {site ? (
              <span className="badge badge-success">
                <span className="badge-dot" /> Connected
              </span>
            ) : connect.isError ? (
              <span className="badge badge-error">
                <span className="badge-dot" /> Failed
              </span>
            ) : (
              <span className="badge badge-muted">
                <span className="badge-dot" /> Not tested
              </span>
            )}
          </div>
          {connect.isError && (
            <div className="hint" style={{ color: 'oklch(var(--destructive))' }}>
              {(connect.error as Error).message}
            </div>
          )}
        </div>
        <div className="card-footer">
          <div
            className="text-xs muted mono"
            style={{ fontSize: 11.5, color: 'oklch(var(--muted-foreground))' }}
          >
            Step 1 of 4
          </div>
          <button
            className="btn btn-primary btn-sm"
            disabled={!site || !targetKb}
            onClick={onContinue}
          >
            Continue &rarr;
          </button>
        </div>
      </div>
    </>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 2 — Select (mockup 21-step2-select.html)
// ──────────────────────────────────────────────────────────────────────────

interface StepSelectProps {
  site: SourceContainer;
  selectedRefs: SourceDocumentRef[];
  setSelectedRefs: Dispatch<SetStateAction<SourceDocumentRef[]>>;
  onBack: () => void;
  onImport: () => void;
}

function StepSelect({
  site,
  selectedRefs,
  setSelectedRefs,
  onBack,
  onImport,
}: StepSelectProps) {
  const [libraries, setLibraries] = useState<SourceContainer[] | null>(null);
  const [active, setActive] = useState<string | null>(null);
  const [docs, setDocs] = useState<SourceDocumentRef[]>([]);
  const [docsLoading, setDocsLoading] = useState(false);

  useEffect(() => {
    let live = true;
    integrationApi.browse(site.id).then((c) => {
      if (live) setLibraries(c);
    });
    return () => {
      live = false;
    };
  }, [site.id]);

  const selectContainer = async (c: SourceContainer) => {
    setActive(c.id);
    setDocsLoading(true);
    try {
      setDocs(await integrationApi.listDocuments(c.id));
    } finally {
      setDocsLoading(false);
    }
  };

  const toggleDoc = (ref: SourceDocumentRef) => {
    setSelectedRefs((prev) =>
      prev.some((r) => r.id === ref.id)
        ? prev.filter((r) => r.id !== ref.id)
        : [...prev, ref],
    );
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Select documents</h3>
        <div
          className="card-desc"
          style={{ fontSize: 12.5, color: 'oklch(var(--muted-foreground))' }}
        >
          {site.name}
        </div>
      </div>
      <div className="card-body card-body-tight">
        <div style={{ display: 'grid', gridTemplateColumns: '230px 1fr' }}>
          <div style={{ padding: '14px 12px', borderRight: '1px solid oklch(var(--border))' }}>
            <div className="nav-section-label" style={{ padding: '0 4px 8px' }}>
              Libraries
            </div>
            <div className="tree">
              {libraries === null ? (
                <div className="hint" style={{ padding: '4px 8px' }}>
                  Loading…
                </div>
              ) : (
                libraries.map((lib) => (
                  <TreeNode
                    key={lib.id}
                    container={lib}
                    depth={0}
                    active={active}
                    onSelect={selectContainer}
                  />
                ))
              )}
            </div>
          </div>
          <div className="pick-table">
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th style={{ width: 34 }} />
                    <th>Document</th>
                    <th>Type</th>
                    <th className="col-num">Modified</th>
                    <th className="col-num">Size</th>
                  </tr>
                </thead>
                <tbody>
                  {docsLoading ? (
                    <tr>
                      <td colSpan={5} className="hint">
                        Loading…
                      </td>
                    </tr>
                  ) : docs.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="hint">
                        Select a library or folder to list its documents.
                      </td>
                    </tr>
                  ) : (
                    docs.map((d) => (
                      <tr key={d.id}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedRefs.some((r) => r.id === d.id)}
                            onChange={() => toggleDoc(d)}
                          />
                        </td>
                        <td>{d.name}</td>
                        <td>
                          <span className="badge badge-muted">{ext(d.name)}</span>
                        </td>
                        <td className="col-num">{fmtDate(d.last_modified)}</td>
                        <td className="col-num">{fmtSize(d.size)}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
      <div className="card-footer">
        <button className="btn btn-ghost btn-sm" onClick={onBack}>
          &#8249; Back
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span
            className="text-xs muted"
            style={{ fontSize: 12, color: 'oklch(var(--muted-foreground))' }}
          >
            {selectedRefs.length} documents selected
          </span>
          <button
            className="btn btn-primary btn-sm"
            disabled={selectedRefs.length === 0}
            onClick={onImport}
          >
            Import {selectedRefs.length} documents &rarr;
          </button>
        </div>
      </div>
    </div>
  );
}

interface TreeNodeProps {
  container: SourceContainer;
  depth: number;
  active: string | null;
  onSelect: (c: SourceContainer) => void;
}

function TreeNode({ container, depth, active, onSelect }: TreeNodeProps) {
  const [expanded, setExpanded] = useState(false);
  const [children, setChildren] = useState<SourceContainer[] | null>(null);

  const handle = async () => {
    onSelect(container);
    if (children === null) {
      setChildren(await integrationApi.browse(container.id));
    }
    setExpanded((e) => !e);
  };

  return (
    <>
      <div
        className="tree-row"
        data-active={active === container.id}
        style={{ marginLeft: depth * 18 }}
        onClick={handle}
      >
        <Folder /> {container.name}
      </div>
      {expanded &&
        children?.map((c) => (
          <TreeNode
            key={c.id}
            container={c}
            depth={depth + 1}
            active={active}
            onSelect={onSelect}
          />
        ))}
    </>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 3 / 4 — placeholders (F6)
// ──────────────────────────────────────────────────────────────────────────

function StepImportPlaceholder({
  count,
  onDone,
}: {
  count: number;
  onDone: (s: ImportSummary) => void;
}) {
  return (
    <div className="card">
      <div className="card-body">
        <p className="hint">Step 3 (Import) — {count} documents. Built in F6.</p>
        <button
          className="btn btn-primary btn-sm"
          onClick={() => onDone({ total: count, succeeded: count, failed: 0, results: [] })}
        >
          (stub) finish
        </button>
      </div>
    </div>
  );
}

function StepSummaryPlaceholder({ summary, kbId }: { summary: ImportSummary; kbId: string }) {
  return (
    <div className="card">
      <div className="card-body">
        <p className="hint">
          Step 4 (Summary) — {summary.succeeded}/{summary.total} into {kbId}. Built in F6.
        </p>
      </div>
    </div>
  );
}

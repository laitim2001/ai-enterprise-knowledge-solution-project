'use client';

/**
 * KB Re-ingestion Wizard (`/kb/[id]/upload`) — per architecture.md v6 §5.5.3b
 * + ADR-0028 §5.5.3b extension (W20 F6.1).
 *
 * W12 baseline shipped a single-step file picker. W20 F6 promotes it to a
 * **3-step wizard** so the KB owner sees the multimodal config in effect before
 * the document lands:
 *   1. Source       — file picker (.docx / .pdf / .pptx)
 *   2. Multimodal   — read-only display of the KB's current multimodal config
 *                     (per-KB level, not per-doc — orchestrator `ingest()` reads
 *                     `kb_config` from `service.get(kb_id)` per W20 F4.2)
 *                     + Tier 2 disabled affordances (caption / clustering /
 *                     ledger) + "Edit settings" link → `/kb/[id]?tab=settings`
 *   3. Review       — summary + Stage progress (POST /kb/{id}/documents only)
 *                     + redirect /kb/[id] on success
 *
 * Step-skeleton primitives (`<Stepper>` / `<Field>` / `<ReadOnlyToggleRow>` /
 * `<Stage>` / `<Summary>`) inline-redeclared per W13 register strategy. This is
 * the 4th wizard usage in `frontend/` (F4 KB Pipeline + W13 Register + W18 F5
 * Pipeline + W20 F6 Re-ingestion) — rule-of-3 promotion trigger NOW hit;
 * extracting to a shared `frontend/components/ui/stepper.tsx` (+ Field/Stage)
 * is a Wave B+ candidate to avoid a Wave A ripple change.
 *
 * 100% design tokens via `tokens.ts`; no hardcoded `oklch()` arbitrary values
 * (W15→W18→W20 F1-F5 milestone preserved).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import { Switch } from '@/components/ui/switch';
import { kbApi, type KbStatus } from '@/lib/api/kb';
import { cn } from '@/lib/utils';

type Step = 1 | 2 | 3;

interface WizardState {
  file: File | null;
}

const STEPS: { id: Step; label: string }[] = [
  { id: 1, label: 'Source' },
  { id: 2, label: 'Multimodal' },
  { id: 3, label: 'Review' },
];

export default function KbUploadPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();

  const [step, setStep] = useState<Step>(1);
  const [state, setState] = useState<WizardState>({ file: null });

  const kbQuery = useQuery({
    queryKey: ['kb', params.id],
    queryFn: () => kbApi.get(params.id),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => kbApi.uploadDoc(params.id, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['kb', params.id] });
      queryClient.invalidateQueries({ queryKey: ['kb', 'list'] });
      router.push(`/kb/${params.id}`);
    },
  });

  const fileError = !state.file ? 'Pick a document to ingest.' : '';

  function next() {
    if (step === 1 && state.file) setStep(2);
    else if (step === 2) setStep(3);
  }
  function back() {
    if (step > 1) setStep((step - 1) as Step);
  }

  function handleExecute() {
    if (!state.file) return;
    uploadMutation.mutate(state.file);
  }

  // F1-pivot per CLAUDE.md §5.7 H7 (2026-05-18): page-level self-wrap per mockup
  // `ekp-page-misc.jsx:15-16` (`.content` + `.content-narrow`). Inner preserved until F6.
  return (
    <div className="content"><div className="content-narrow">
    <div className="max-w-3xl">
      <Link
        href={`/kb/${params.id}`}
        className="text-sm text-accent hover:underline"
      >
        ← Back to KB
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Upload Document</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Walk through the three-step re-ingestion wizard. The document will be
        parsed with the KB&apos;s current multimodal config.
      </p>

      <Stepper current={step} />

      <div className="mt-8">
        {step === 1 && (
          <Step1
            state={state}
            error={fileError}
            onChange={setState}
            onSubmit={(e) => {
              e.preventDefault();
              next();
            }}
          />
        )}
        {step === 2 && (
          <Step2
            kbId={params.id}
            kb={kbQuery.data}
            isLoading={kbQuery.isLoading}
            isError={kbQuery.isError}
            onBack={back}
            onSubmit={(e) => {
              e.preventDefault();
              next();
            }}
          />
        )}
        {step === 3 && (
          <Step3
            state={state}
            kb={kbQuery.data}
            fileError={fileError}
            uploadPending={uploadMutation.isPending}
            uploadSuccess={uploadMutation.isSuccess}
            uploadError={uploadMutation.error as Error | null}
            onBack={back}
            onExecute={handleExecute}
          />
        )}
      </div>
    </div>
    </div></div>
  );
}

// --------------------------------------------------------------------------- //
// Stepper indicator
// --------------------------------------------------------------------------- //

function Stepper({ current }: { current: Step }) {
  return (
    <ol
      className="mt-8 flex items-center gap-2 text-xs font-medium uppercase tracking-wide"
      aria-label="Wizard steps"
    >
      {STEPS.map((s, idx) => {
        const isActive = s.id === current;
        const isDone = s.id < current;
        return (
          <li key={s.id} className="flex flex-1 items-center gap-2">
            <span
              aria-current={isActive ? 'step' : undefined}
              className={cn(
                'flex h-7 w-7 items-center justify-center rounded-full text-[11px]',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : isDone
                    ? 'bg-success text-success-foreground'
                    : 'border border-border text-muted-foreground',
              )}
            >
              {isDone ? '✓' : s.id}
            </span>
            <span className={isActive ? 'text-foreground' : 'text-muted-foreground'}>
              {s.label}
            </span>
            {idx < STEPS.length - 1 && (
              <span className="ml-2 flex-1 border-t border-dashed border-border" />
            )}
          </li>
        );
      })}
    </ol>
  );
}

// --------------------------------------------------------------------------- //
// Step 1 — Source (file picker)
// --------------------------------------------------------------------------- //

function Step1({
  state,
  error,
  onChange,
  onSubmit,
}: {
  state: WizardState;
  error: string;
  onChange: (next: WizardState) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h2 className="text-lg font-medium">Source</h2>
      <p className="text-sm text-muted-foreground">
        Pick the document to re-ingest. Supported formats per
        architecture.md §3.3: <span className="font-mono">.docx</span>{' / '}
        <span className="font-mono">.pdf</span>{' / '}
        <span className="font-mono">.pptx</span>.
      </p>

      <Field label="Document">
        <input
          type="file"
          accept=".docx,.pdf,.pptx"
          onChange={(e) =>
            onChange({ ...state, file: e.target.files?.[0] ?? null })
          }
          className="block w-full text-sm"
        />
        {state.file && (
          <span className="mt-1 block text-xs text-muted-foreground">
            Selected: <span className="font-mono">{state.file.name}</span>
            {' · '}
            {(state.file.size / 1024).toFixed(1)} KB
          </span>
        )}
      </Field>

      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={!!error}>
          Next →
        </Button>
      </div>
    </form>
  );
}

// --------------------------------------------------------------------------- //
// Step 2 — Multimodal (read-only display per KB config + Tier 2 affordances)
// --------------------------------------------------------------------------- //

function Step2({
  kbId,
  kb,
  isLoading,
  isError,
  onBack,
  onSubmit,
}: {
  kbId: string;
  kb: KbStatus | undefined;
  isLoading: boolean;
  isError: boolean;
  onBack: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <h2 className="text-lg font-medium">Multimodal</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          The document will be ingested with the KB&apos;s current multimodal
          config. To change these settings,{' '}
          <Link
            href={`/kb/${kbId}?tab=settings`}
            className="text-accent hover:underline"
          >
            edit the KB&apos;s Settings tab
          </Link>
          .
        </p>
      </div>

      {isLoading && (
        <div className="rounded-md border border-border bg-muted/40 p-4 text-sm text-muted-foreground">
          Loading KB config…
        </div>
      )}
      {isError && (
        <div className="rounded-md border border-destructive bg-destructive/10 p-4 text-sm">
          Failed to load KB config. Refresh the page or check the KB exists.
        </div>
      )}

      {kb && (
        <>
          {/* Tier 1 active toggles — read-only display */}
          <fieldset className="space-y-3 rounded-md border border-border p-4">
            <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Tier 1 — active (read-only — per-KB config)
            </legend>

            <ReadOnlyToggleRow
              label="Extract embedded images"
              description="Pull figures from Word / PDF / PPT and persist them alongside chunks."
              checked={kb.config.extract_embedded_images}
            />
            <ReadOnlyToggleRow
              label="Slide screenshots"
              description="For PPT: capture each slide as a screenshot so the chat can surface visual context."
              checked={kb.config.slide_screenshots}
            />
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="text-sm font-medium">Dedup strategy</div>
                <p className="text-xs text-muted-foreground">
                  Skip uploading duplicate images by SHA-256 — or store every copy.
                </p>
              </div>
              <span className="rounded-sm border border-border bg-muted/40 px-2 py-1 font-mono text-xs">
                {kb.config.dedup_strategy}
              </span>
            </div>
            <ReadOnlyToggleRow
              label="Return images in chat"
              description="When the assistant cites a chunk with images, surface them inline (and in the gallery)."
              checked={kb.config.return_images_in_chat}
            />
          </fieldset>

          {/* Tier 2 disabled affordances */}
          <fieldset className="space-y-3 rounded-md border border-dashed border-border p-4">
            <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Tier 2 — coming in a later tier
            </legend>

            <DisabledAffordance
              variant="p3-preview"
              reason="LLM-generated captions for figures — arrives in a later tier"
              tier2Trigger="caption generation pipeline"
              showBadge
            >
              <ReadOnlyToggleRow
                label="Caption generation"
                description="Auto-describe images with a vision-LLM for better retrieval."
                checked={false}
              />
            </DisabledAffordance>

            <DisabledAffordance
              variant="p3-preview"
              reason="Image clustering for similarity search — arrives in a later tier"
              tier2Trigger="image clustering"
              showBadge
            >
              <ReadOnlyToggleRow
                label="Image clustering"
                description="Group near-duplicate or visually similar images for review."
                checked={false}
              />
            </DisabledAffordance>

            <DisabledAffordance
              variant="p3-preview"
              reason="Chain-of-custody hash verification — arrives in a later tier"
              tier2Trigger="provenance ledger"
              showBadge
            >
              <ReadOnlyToggleRow
                label="Provenance ledger"
                description="Cryptographically anchor source hashes for audit trail."
                checked={false}
              />
            </DisabledAffordance>
          </fieldset>
        </>
      )}

      <div className="flex justify-between pt-2">
        <Button type="button" variant="outline" onClick={onBack}>
          ← Back
        </Button>
        <Button type="submit" disabled={isLoading || isError}>
          Next →
        </Button>
      </div>
    </form>
  );
}

function ReadOnlyToggleRow({
  label,
  description,
  checked,
}: {
  label: string;
  description: string;
  checked: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="flex-1">
        <div className="text-sm font-medium">{label}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Switch
        checked={checked}
        disabled
        aria-label={label}
        aria-readonly="true"
        className="cursor-not-allowed"
      />
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Step 3 — Review (summary + Stage progress)
// --------------------------------------------------------------------------- //

function Step3({
  state,
  kb,
  fileError,
  uploadPending,
  uploadSuccess,
  uploadError,
  onBack,
  onExecute,
}: {
  state: WizardState;
  kb: KbStatus | undefined;
  fileError: string;
  uploadPending: boolean;
  uploadSuccess: boolean;
  uploadError: Error | null;
  onBack: () => void;
  onExecute: () => void;
}) {
  const inFlight = uploadPending;
  const allDone = uploadSuccess;

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-medium">Review</h2>
      <p className="text-sm text-muted-foreground">
        Confirm the ingestion plan, then upload. The document is parsed,
        chunked, embedded, and indexed via{' '}
        <span className="font-mono">POST /kb/{'{id}'}/documents</span>.
      </p>

      <dl className="rounded-md border border-border bg-muted/40 p-4 text-sm">
        <Summary label="KB id" value={kb?.kb_id ?? '—'} />
        <Summary label="KB name" value={kb?.name ?? '—'} />
        <Summary label="Document" value={state.file?.name ?? '—'} />
        <Summary
          label="Size"
          value={
            state.file
              ? `${(state.file.size / 1024).toFixed(1)} KB`
              : '—'
          }
        />
        {kb && (
          <>
            <Summary
              label="Extract images"
              value={kb.config.extract_embedded_images ? 'yes' : 'no'}
            />
            <Summary
              label="Slide screenshots"
              value={kb.config.slide_screenshots ? 'yes' : 'no'}
            />
            <Summary label="Dedup" value={kb.config.dedup_strategy} />
            <Summary
              label="Images in chat"
              value={kb.config.return_images_in_chat ? 'yes' : 'no'}
            />
          </>
        )}
      </dl>

      <ol className="space-y-2 text-sm">
        <Stage
          label="Upload + Ingest (POST /kb/{id}/documents)"
          pending={uploadPending}
          success={uploadSuccess}
          error={uploadError}
        />
      </ol>

      <div className="flex justify-between pt-2">
        <Button
          type="button"
          variant="outline"
          onClick={onBack}
          disabled={inFlight}
        >
          ← Back
        </Button>
        <Button
          type="button"
          onClick={onExecute}
          disabled={inFlight || allDone || !!fileError}
        >
          {inFlight
            ? 'Uploading…'
            : allDone
              ? 'Done — redirecting…'
              : 'Upload + Ingest'}
        </Button>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Shared primitives
// --------------------------------------------------------------------------- //

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <div className="mt-1">{children}</div>
      {error && (
        <span className="mt-1 block text-xs text-destructive">{error}</span>
      )}
    </label>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-border py-1.5 last:border-0">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="font-mono">{value}</dd>
    </div>
  );
}

function Stage({
  label,
  pending,
  success,
  error,
}: {
  label: string;
  pending: boolean;
  success: boolean;
  error: Error | null;
}) {
  let icon = '○';
  let cls = 'text-muted-foreground';
  if (pending) {
    icon = '◐';
    cls = 'text-accent animate-pulse';
  } else if (error) {
    icon = '✗';
    cls = 'text-destructive';
  } else if (success) {
    icon = '✓';
    cls = 'text-success';
  }
  return (
    <li className="flex items-start gap-3">
      <span className={`mt-0.5 font-mono ${cls}`}>{icon}</span>
      <div className="flex-1">
        <div>{label}</div>
        {error && (
          <div className="mt-0.5 text-xs text-destructive">{error.message}</div>
        )}
      </div>
    </li>
  );
}

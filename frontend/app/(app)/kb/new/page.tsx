'use client';

/**
 * KB Pipeline Wizard (`/kb/new`) — per architecture.md v6 §5.5.3 + ADR-0028
 * 5-step wizard expansion (W20 F4.4).
 *
 * W12 baseline shipped a 3-step wizard (DATA SOURCE → DOCUMENT PROCESSING →
 * EXECUTE). W20 F4.4 expands to **5 explicit steps** so the KB owner sees the
 * multimodal trade-offs up front rather than buried in a single "processing"
 * step:
 *   1. Source       — Name + Description + KB id (the `/kb` POST body)
 *   2. Parsing      — Embedding model + dimension (Docling profile = active
 *                     Tier 1; finer-grained "profile picker" is Wave B+)
 *   3. Chunking     — Strategy + top_k + rerank_k
 *   4. Multimodal   — Tier 1 active toggles (`extract_embedded_images` +
 *                     `slide_screenshots` + `dedup_strategy` +
 *                     `return_images_in_chat`) AND Tier 2 disabled affordances
 *                     (caption generation / image clustering / blockchain
 *                     verify — per W19 F5 27-affordance Tier 2 catalog)
 *   5. Review       — Summary table + POST /kb + POST /kb/{id}/documents
 *                     + redirect /kb/[id]
 *
 * Layout reference Dify Image 1 wizard (no code copy per ADR-0010).
 *
 * 100% design tokens via `tokens.ts`; no hardcoded `oklch()` arbitrary values
 * (W15→W18→W20 F1+F2+F3+F4 milestone preserved).
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';

import { Button } from '@/components/ui/button';
import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import { Switch } from '@/components/ui/switch';
import {
  DEFAULT_KB_CONFIG,
  kbApi,
  type KbConfig,
  type KbCreatePayload,
  type KbStatus,
} from '@/lib/api/kb';
import { cn } from '@/lib/utils';

type Step = 1 | 2 | 3 | 4 | 5;

interface WizardState {
  kb_id: string;
  name: string;
  description: string;
  config: KbConfig;
  file: File | null;
}

const KB_ID_PATTERN = /^[a-z0-9_-]+$/;

const STEPS: { id: Step; label: string }[] = [
  { id: 1, label: 'Source' },
  { id: 2, label: 'Parsing' },
  { id: 3, label: 'Chunking' },
  { id: 4, label: 'Multimodal' },
  { id: 5, label: 'Review' },
];

export default function KbNewPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [step, setStep] = useState<Step>(1);
  const [state, setState] = useState<WizardState>({
    kb_id: '',
    name: '',
    description: '',
    config: { ...DEFAULT_KB_CONFIG },
    file: null,
  });

  const createMutation = useMutation({
    mutationFn: (payload: KbCreatePayload) => kbApi.create(payload),
  });
  const uploadMutation = useMutation({
    mutationFn: ({ kbId, file }: { kbId: string; file: File }) =>
      kbApi.uploadDoc(kbId, file),
  });

  const step1Errors = validateStep1(state);
  const step2Errors = validateStep2(state);
  const step3Errors = validateStep3(state);
  const step5Errors = validateStep5(state);

  function next() {
    if (step === 1 && Object.keys(step1Errors).length === 0) setStep(2);
    else if (step === 2 && Object.keys(step2Errors).length === 0) setStep(3);
    else if (step === 3 && Object.keys(step3Errors).length === 0) setStep(4);
    else if (step === 4) setStep(5);
  }
  function back() {
    if (step > 1) setStep((step - 1) as Step);
  }

  async function handleExecute() {
    if (!state.file) return;
    let created: KbStatus;
    try {
      created = await createMutation.mutateAsync({
        kb_id: state.kb_id,
        name: state.name,
        description: state.description,
        config: state.config,
      });
    } catch {
      return;
    }
    try {
      await uploadMutation.mutateAsync({ kbId: created.kb_id, file: state.file });
    } catch {
      return;
    }
    queryClient.invalidateQueries({ queryKey: ['kb'] });
    router.push(`/kb/${created.kb_id}`);
  }

  return (
    <div className="max-w-3xl">
      <Link href="/kb" className="text-sm text-accent hover:underline">
        ← Back to KBs
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Create Knowledge Base</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Walk through the five-step wizard to ingest the first document into a new KB.
      </p>

      <Stepper current={step} />

      <div className="mt-8">
        {step === 1 && (
          <Step1
            state={state}
            errors={step1Errors}
            onChange={setState}
            onSubmit={(e) => {
              e.preventDefault();
              next();
            }}
          />
        )}
        {step === 2 && (
          <Step2
            state={state}
            errors={step2Errors}
            onChange={setState}
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
            errors={step3Errors}
            onChange={setState}
            onBack={back}
            onSubmit={(e) => {
              e.preventDefault();
              next();
            }}
          />
        )}
        {step === 4 && (
          <Step4
            state={state}
            onChange={setState}
            onBack={back}
            onSubmit={(e) => {
              e.preventDefault();
              next();
            }}
          />
        )}
        {step === 5 && (
          <Step5
            state={state}
            errors={step5Errors}
            createPending={createMutation.isPending}
            createSuccess={createMutation.isSuccess}
            createError={createMutation.error as Error | null}
            uploadPending={uploadMutation.isPending}
            uploadSuccess={uploadMutation.isSuccess}
            uploadError={uploadMutation.error as Error | null}
            onChange={setState}
            onBack={back}
            onExecute={handleExecute}
          />
        )}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Validators
// --------------------------------------------------------------------------- //

function validateStep1(state: WizardState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!state.kb_id) errors.kb_id = 'Required.';
  else if (!KB_ID_PATTERN.test(state.kb_id))
    errors.kb_id = 'Lowercase letters, digits, hyphen, underscore only.';
  if (!state.name) errors.name = 'Required.';
  return errors;
}

function validateStep2(state: WizardState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!state.config.embedding_model) errors.embedding_model = 'Required.';
  if (state.config.embedding_dimension <= 0)
    errors.embedding_dimension = 'Must be positive.';
  return errors;
}

function validateStep3(state: WizardState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (state.config.default_top_k <= 0) errors.default_top_k = 'Must be positive.';
  if (state.config.default_rerank_k <= 0)
    errors.default_rerank_k = 'Must be positive.';
  if (state.config.default_rerank_k > state.config.default_top_k)
    errors.default_rerank_k = 'Must be ≤ default_top_k.';
  return errors;
}

function validateStep5(state: WizardState): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!state.file) errors.file = 'Pick a document to ingest.';
  return errors;
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
// Step 1 — Source
// --------------------------------------------------------------------------- //

function Step1({
  state,
  errors,
  onChange,
  onSubmit,
}: {
  state: WizardState;
  errors: Record<string, string>;
  onChange: (next: WizardState) => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h2 className="text-lg font-medium">Source</h2>
      <p className="text-sm text-muted-foreground">
        Identify the new KB. The KB id forms the Azure AI Search index name
        (<span className="font-mono">ekp-kb-{'{kb_id}'}-v{'{n}'}</span>) and
        cannot change after creation.
      </p>

      <Field label="KB id" error={errors.kb_id}>
        <input
          value={state.kb_id}
          onChange={(e) => onChange({ ...state, kb_id: e.target.value })}
          placeholder="e.g. drive_user_manuals"
          className={inputClass}
          // eslint-disable-next-line jsx-a11y/no-autofocus
          autoFocus
        />
      </Field>
      <Field label="Display name" error={errors.name}>
        <input
          value={state.name}
          onChange={(e) => onChange({ ...state, name: e.target.value })}
          placeholder="Drive — User Manuals"
          className={inputClass}
        />
      </Field>
      <Field label="Description (optional)">
        <textarea
          value={state.description}
          onChange={(e) => onChange({ ...state, description: e.target.value })}
          rows={3}
          className={cn(inputClass, 'resize-none')}
        />
      </Field>

      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={Object.keys(errors).length > 0}>
          Next →
        </Button>
      </div>
    </form>
  );
}

// --------------------------------------------------------------------------- //
// Step 2 — Parsing
// --------------------------------------------------------------------------- //

function Step2({
  state,
  errors,
  onChange,
  onBack,
  onSubmit,
}: {
  state: WizardState;
  errors: Record<string, string>;
  onChange: (next: WizardState) => void;
  onBack: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h2 className="text-lg font-medium">Parsing</h2>
      <p className="text-sm text-muted-foreground">
        Choose the embedding model + dimension. Docling is the active Tier 1
        parser; alternative parser profiles arrive in a later tier.
      </p>

      <Field label="Embedding model" error={errors.embedding_model}>
        <input
          value={state.config.embedding_model}
          onChange={(e) =>
            onChange({
              ...state,
              config: { ...state.config, embedding_model: e.target.value },
            })
          }
          className={inputClass}
        />
      </Field>
      <Field label="Embedding dimension" error={errors.embedding_dimension}>
        <input
          type="number"
          min={1}
          value={state.config.embedding_dimension}
          onChange={(e) =>
            onChange({
              ...state,
              config: {
                ...state.config,
                embedding_dimension: Number(e.target.value),
              },
            })
          }
          className={inputClass}
        />
      </Field>

      <DisabledAffordance
        reason="Alternative parser profiles (Docling-fast / OCR-heavy) arrive in a later tier"
        tier2Trigger="parser profile picker"
        className="block"
      >
        <div className={cn(inputClass, 'flex items-center justify-between')}>
          <span className="text-sm">Parser profile</span>
          <span className="text-xs text-muted-foreground">docling-default</span>
        </div>
      </DisabledAffordance>

      <div className="flex justify-between pt-2">
        <Button type="button" variant="outline" onClick={onBack}>
          ← Back
        </Button>
        <Button type="submit" disabled={Object.keys(errors).length > 0}>
          Next →
        </Button>
      </div>
    </form>
  );
}

// --------------------------------------------------------------------------- //
// Step 3 — Chunking
// --------------------------------------------------------------------------- //

function Step3({
  state,
  errors,
  onChange,
  onBack,
  onSubmit,
}: {
  state: WizardState;
  errors: Record<string, string>;
  onChange: (next: WizardState) => void;
  onBack: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <h2 className="text-lg font-medium">Chunking</h2>
      <p className="text-sm text-muted-foreground">
        Pick the chunk strategy + retrieval top-K. Defaults match
        architecture.md §3.2 baseline; tune later under KB → Settings.
      </p>

      <Field label="Chunk strategy">
        <select
          value={state.config.chunk_strategy}
          onChange={(e) =>
            onChange({
              ...state,
              config: {
                ...state.config,
                chunk_strategy: e.target.value as KbConfig['chunk_strategy'],
              },
            })
          }
          className={inputClass}
        >
          <option value="auto">auto (per format)</option>
          <option value="layout_aware">layout_aware (Word/PDF)</option>
          <option value="heading_aware">heading_aware</option>
          <option value="slide_based">slide_based (PPT)</option>
        </select>
      </Field>

      <div className="grid grid-cols-2 gap-4">
        <Field label="Default top_k retrieval" error={errors.default_top_k}>
          <input
            type="number"
            min={1}
            value={state.config.default_top_k}
            onChange={(e) =>
              onChange({
                ...state,
                config: {
                  ...state.config,
                  default_top_k: Number(e.target.value),
                },
              })
            }
            className={inputClass}
          />
        </Field>
        <Field label="Default rerank_k" error={errors.default_rerank_k}>
          <input
            type="number"
            min={1}
            value={state.config.default_rerank_k}
            onChange={(e) =>
              onChange({
                ...state,
                config: {
                  ...state.config,
                  default_rerank_k: Number(e.target.value),
                },
              })
            }
            className={inputClass}
          />
        </Field>
      </div>

      <div className="flex justify-between pt-2">
        <Button type="button" variant="outline" onClick={onBack}>
          ← Back
        </Button>
        <Button type="submit" disabled={Object.keys(errors).length > 0}>
          Next →
        </Button>
      </div>
    </form>
  );
}

// --------------------------------------------------------------------------- //
// Step 4 — Multimodal (Tier 1 active + Tier 2 disabled affordances)
// --------------------------------------------------------------------------- //

function Step4({
  state,
  onChange,
  onBack,
  onSubmit,
}: {
  state: WizardState;
  onChange: (next: WizardState) => void;
  onBack: () => void;
  onSubmit: (e: FormEvent<HTMLFormElement>) => void;
}) {
  function setConfigField<K extends keyof KbConfig>(key: K, value: KbConfig[K]) {
    onChange({ ...state, config: { ...state.config, [key]: value } });
  }

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div>
        <h2 className="text-lg font-medium">Multimodal</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Tier 1 active toggles below. Tier 2 affordances are visible but
          disabled — they activate in a later tier (per architecture.md §11).
        </p>
      </div>

      {/* Tier 1 active toggles */}
      <fieldset className="space-y-3 rounded-md border border-border p-4">
        <legend className="px-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Tier 1 — active
        </legend>

        <ToggleRow
          label="Extract embedded images"
          description="Pull figures from Word / PDF / PPT and persist them alongside chunks."
          checked={state.config.extract_embedded_images}
          onChange={(v) => setConfigField('extract_embedded_images', v)}
        />
        <ToggleRow
          label="Slide screenshots"
          description="For PPT: capture each slide as a screenshot so the chat can surface visual context."
          checked={state.config.slide_screenshots}
          onChange={(v) => setConfigField('slide_screenshots', v)}
        />
        <div className="space-y-1">
          <label className="flex items-start justify-between gap-3">
            <span className="flex-1">
              <span className="block text-sm font-medium">Dedup strategy</span>
              <span className="block text-xs text-muted-foreground">
                Skip uploading duplicate images by SHA-256 — or store every copy.
              </span>
            </span>
            <select
              value={state.config.dedup_strategy}
              onChange={(e) =>
                setConfigField('dedup_strategy', e.target.value as KbConfig['dedup_strategy'])
              }
              className={cn(inputClass, 'w-32')}
            >
              <option value="sha256">SHA-256</option>
              <option value="none">None</option>
            </select>
          </label>
        </div>
        <ToggleRow
          label="Return images in chat"
          description="When the assistant cites a chunk with images, surface them inline (and in the gallery)."
          checked={state.config.return_images_in_chat}
          onChange={(v) => setConfigField('return_images_in_chat', v)}
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
          <ToggleRow
            label="Caption generation"
            description="Auto-describe images with a vision-LLM for better retrieval."
            checked={false}
            onChange={() => {}}
            disabled
          />
        </DisabledAffordance>

        <DisabledAffordance
          variant="p3-preview"
          reason="Image clustering for similarity search — arrives in a later tier"
          tier2Trigger="image clustering"
          showBadge
        >
          <ToggleRow
            label="Image clustering"
            description="Group near-duplicate or visually similar images for review."
            checked={false}
            onChange={() => {}}
            disabled
          />
        </DisabledAffordance>

        <DisabledAffordance
          variant="p3-preview"
          reason="Chain-of-custody hash verification — arrives in a later tier"
          tier2Trigger="provenance ledger"
          showBadge
        >
          <ToggleRow
            label="Provenance ledger"
            description="Cryptographically anchor source hashes for audit trail."
            checked={false}
            onChange={() => {}}
            disabled
          />
        </DisabledAffordance>
      </fieldset>

      <div className="flex justify-between pt-2">
        <Button type="button" variant="outline" onClick={onBack}>
          ← Back
        </Button>
        <Button type="submit">Next →</Button>
      </div>
    </form>
  );
}

function ToggleRow({
  label,
  description,
  checked,
  onChange,
  disabled = false,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="flex-1">
        <div className="text-sm font-medium">{label}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Switch
        checked={checked}
        onCheckedChange={onChange}
        disabled={disabled}
        aria-label={label}
      />
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Step 5 — Review (file picker + summary + execute)
// --------------------------------------------------------------------------- //

function Step5({
  state,
  errors,
  createPending,
  createSuccess,
  createError,
  uploadPending,
  uploadSuccess,
  uploadError,
  onChange,
  onBack,
  onExecute,
}: {
  state: WizardState;
  errors: Record<string, string>;
  createPending: boolean;
  createSuccess: boolean;
  createError: Error | null;
  uploadPending: boolean;
  uploadSuccess: boolean;
  uploadError: Error | null;
  onChange: (next: WizardState) => void;
  onBack: () => void;
  onExecute: () => void;
}) {
  const inFlight = createPending || uploadPending;
  const allDone = createSuccess && uploadSuccess;

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-medium">Review</h2>
      <p className="text-sm text-muted-foreground">
        Pick the first document, confirm the settings, then create the KB.
        <span className="ml-1 font-mono">POST /kb</span> →
        <span className="ml-1 font-mono">POST /kb/{'{id}'}/documents</span>.
      </p>

      <Field label="First document (.docx / .pdf / .pptx)" error={errors.file}>
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

      <dl className="rounded-md border border-border bg-muted/40 p-4 text-sm">
        <Summary label="KB id" value={state.kb_id} />
        <Summary label="Name" value={state.name} />
        <Summary label="Description" value={state.description || '—'} />
        <Summary label="Embedding" value={state.config.embedding_model} />
        <Summary label="Dimension" value={String(state.config.embedding_dimension)} />
        <Summary label="Chunk strategy" value={state.config.chunk_strategy} />
        <Summary
          label="top_k / rerank_k"
          value={`${state.config.default_top_k} / ${state.config.default_rerank_k}`}
        />
        <Summary
          label="Extract images"
          value={state.config.extract_embedded_images ? 'yes' : 'no'}
        />
        <Summary
          label="Slide screenshots"
          value={state.config.slide_screenshots ? 'yes' : 'no'}
        />
        <Summary label="Dedup" value={state.config.dedup_strategy} />
        <Summary
          label="Images in chat"
          value={state.config.return_images_in_chat ? 'yes' : 'no'}
        />
      </dl>

      <ol className="space-y-2 text-sm">
        <Stage
          label="Create KB (POST /kb)"
          pending={createPending}
          success={createSuccess}
          error={createError}
        />
        <Stage
          label="Upload + Ingest (POST /kb/{id}/documents)"
          pending={uploadPending}
          success={uploadSuccess}
          error={uploadError}
        />
      </ol>

      <div className="flex justify-between pt-2">
        <Button type="button" variant="outline" onClick={onBack} disabled={inFlight}>
          ← Back
        </Button>
        <Button
          type="button"
          onClick={onExecute}
          disabled={inFlight || allDone || Object.keys(errors).length > 0}
        >
          {inFlight ? 'Running…' : allDone ? 'Done — redirecting…' : 'Create + Ingest'}
        </Button>
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------- //
// Shared primitives
// --------------------------------------------------------------------------- //

const inputClass =
  'w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring';

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

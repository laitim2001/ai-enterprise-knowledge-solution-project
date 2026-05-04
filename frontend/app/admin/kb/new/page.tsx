'use client';

/**
 * KB Pipeline Wizard (`/admin/kb/new`) — per architecture.md §5.5 view 7.
 *
 * 3-step wizard: DATA SOURCE → DOCUMENT PROCESSING → EXECUTE.
 * Step 1 captures KB identity + description.
 * Step 2 reviews / overrides KbConfig defaults + picks first document.
 * Step 3 fires the POST sequence (POST /kb → POST /kb/{id}/documents) and
 * shows per-stage status, then routes to the new KB detail page on success.
 *
 * Plain Tailwind step indicator (shadcn Stepper deferred — same Karpathy §1.2
 * trade-off as W3 D4 chat UI baseline; matches W2 D5 admin views pattern).
 *
 * Layout reference Dify Image 1 wizard (no code copy per CLAUDE.md §7);
 * EKP design tokens only via `oklch(...)`.
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState, type FormEvent } from 'react';
import {
  DEFAULT_KB_CONFIG,
  kbApi,
  type KbConfig,
  type KbCreatePayload,
  type KbStatus,
} from '@/lib/api/kb';

type Step = 1 | 2 | 3;

interface WizardState {
  kb_id: string;
  name: string;
  description: string;
  config: KbConfig;
  file: File | null;
}

const KB_ID_PATTERN = /^[a-z0-9_-]+$/;

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

  function handleStep1Submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (Object.keys(step1Errors).length === 0) setStep(2);
  }

  function handleStep2Submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (Object.keys(step2Errors).length === 0) setStep(3);
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
    router.push(`/admin/kb/${created.kb_id}`);
  }

  return (
    <div className="max-w-3xl">
      <Link
        href="/admin/kb"
        className="text-sm text-[oklch(0.42_0.04_260)] hover:underline"
      >
        ← Back to KBs
      </Link>
      <h1 className="mt-2 text-2xl font-semibold">Create Knowledge Base</h1>
      <p className="mt-1 text-sm text-[oklch(0.45_0_0)]">
        Set up a new KB and ingest its first document in three steps.
      </p>

      <Stepper current={step} />

      <div className="mt-8">
        {step === 1 && (
          <Step1
            state={state}
            errors={step1Errors}
            onChange={setState}
            onSubmit={handleStep1Submit}
          />
        )}
        {step === 2 && (
          <Step2
            state={state}
            errors={step2Errors}
            onChange={setState}
            onBack={() => setStep(1)}
            onSubmit={handleStep2Submit}
          />
        )}
        {step === 3 && (
          <Step3
            state={state}
            createPending={createMutation.isPending}
            createSuccess={createMutation.isSuccess}
            createError={createMutation.error as Error | null}
            uploadPending={uploadMutation.isPending}
            uploadSuccess={uploadMutation.isSuccess}
            uploadError={uploadMutation.error as Error | null}
            onBack={() => setStep(2)}
            onExecute={handleExecute}
          />
        )}
      </div>
    </div>
  );
}

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
  if (state.config.default_top_k <= 0) errors.default_top_k = 'Must be positive.';
  if (state.config.default_rerank_k <= 0)
    errors.default_rerank_k = 'Must be positive.';
  if (state.config.default_rerank_k > state.config.default_top_k)
    errors.default_rerank_k = 'Must be ≤ default_top_k.';
  if (!state.file) errors.file = 'Pick a document to ingest.';
  return errors;
}

function Stepper({ current }: { current: Step }) {
  const steps = [
    { id: 1, label: 'DATA SOURCE' },
    { id: 2, label: 'DOCUMENT PROCESSING' },
    { id: 3, label: 'EXECUTE' },
  ] as const;
  return (
    <ol className="mt-8 flex items-center gap-2 text-xs font-medium uppercase tracking-wide">
      {steps.map((s, idx) => {
        const isActive = s.id === current;
        const isDone = s.id < current;
        return (
          <li key={s.id} className="flex flex-1 items-center gap-2">
            <span
              className={[
                'flex h-7 w-7 items-center justify-center rounded-full text-[11px]',
                isActive
                  ? 'bg-[oklch(0.42_0.04_260)] text-white'
                  : isDone
                    ? 'bg-[oklch(0.65_0.16_145)] text-white'
                    : 'border border-[oklch(0.92_0_0)] text-[oklch(0.55_0_0)]',
              ].join(' ')}
            >
              {isDone ? '✓' : s.id}
            </span>
            <span
              className={
                isActive
                  ? 'text-[oklch(0.20_0_0)]'
                  : 'text-[oklch(0.55_0_0)]'
              }
            >
              {s.label}
            </span>
            {idx < steps.length - 1 && (
              <span className="ml-2 flex-1 border-t border-dashed border-[oklch(0.92_0_0)]" />
            )}
          </li>
        );
      })}
    </ol>
  );
}

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
      <h2 className="text-lg font-medium">Data Source</h2>
      <p className="text-sm text-[oklch(0.45_0_0)]">
        Identify the new KB. The KB id forms the Azure AI Search index name
        (<span className="font-mono">ekp-kb-{'{kb_id}'}-v{'{n}'}</span>) and
        cannot change after creation.
      </p>

      <Field label="KB id" error={errors.kb_id}>
        <input
          value={state.kb_id}
          onChange={(e) => onChange({ ...state, kb_id: e.target.value })}
          placeholder="e.g. drive_user_manuals"
          className="w-full rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm font-mono"
          autoFocus
        />
      </Field>
      <Field label="Display name" error={errors.name}>
        <input
          value={state.name}
          onChange={(e) => onChange({ ...state, name: e.target.value })}
          placeholder="Drive — User Manuals"
          className="w-full rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm"
        />
      </Field>
      <Field label="Description (optional)">
        <textarea
          value={state.description}
          onChange={(e) => onChange({ ...state, description: e.target.value })}
          rows={3}
          className="w-full resize-none rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm"
        />
      </Field>

      <div className="flex justify-end pt-2">
        <button
          type="submit"
          disabled={Object.keys(errors).length > 0}
          className="rounded bg-[oklch(0.42_0.04_260)] px-4 py-2 text-sm font-medium text-white hover:bg-[oklch(0.36_0.04_260)] disabled:opacity-50"
        >
          Next →
        </button>
      </div>
    </form>
  );
}

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
      <h2 className="text-lg font-medium">Document Processing</h2>
      <p className="text-sm text-[oklch(0.45_0_0)]">
        Review the indexing config and choose the first document to ingest.
        Defaults match architecture.md §3.2 baseline; settings are editable
        later under KB → Settings.
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
          className="w-full rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm"
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
          className="w-full rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm"
        />
      </Field>
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
          className="w-full rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm"
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
            className="w-full rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm"
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
            className="w-full rounded border border-[oklch(0.92_0_0)] px-3 py-1.5 text-sm"
          />
        </Field>
      </div>

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
          <span className="mt-1 block text-xs text-[oklch(0.45_0_0)]">
            Selected: <span className="font-mono">{state.file.name}</span>
            {' · '}
            {(state.file.size / 1024).toFixed(1)} KB
          </span>
        )}
      </Field>

      <div className="flex justify-between pt-2">
        <button
          type="button"
          onClick={onBack}
          className="rounded border border-[oklch(0.92_0_0)] px-4 py-2 text-sm hover:bg-[oklch(0.96_0_0)]"
        >
          ← Back
        </button>
        <button
          type="submit"
          disabled={Object.keys(errors).length > 0}
          className="rounded bg-[oklch(0.42_0.04_260)] px-4 py-2 text-sm font-medium text-white hover:bg-[oklch(0.36_0.04_260)] disabled:opacity-50"
        >
          Next →
        </button>
      </div>
    </form>
  );
}

function Step3({
  state,
  createPending,
  createSuccess,
  createError,
  uploadPending,
  uploadSuccess,
  uploadError,
  onBack,
  onExecute,
}: {
  state: WizardState;
  createPending: boolean;
  createSuccess: boolean;
  createError: Error | null;
  uploadPending: boolean;
  uploadSuccess: boolean;
  uploadError: Error | null;
  onBack: () => void;
  onExecute: () => void;
}) {
  const inFlight = createPending || uploadPending;
  const allDone = createSuccess && uploadSuccess;

  return (
    <div className="space-y-5">
      <h2 className="text-lg font-medium">Execute</h2>
      <p className="text-sm text-[oklch(0.45_0_0)]">
        Confirm and create the KB. This runs two requests sequentially:
        <span className="font-mono"> POST /kb</span> then{' '}
        <span className="font-mono">POST /kb/{'{id}'}/documents</span>.
      </p>

      <dl className="rounded border border-[oklch(0.92_0_0)] bg-[oklch(0.98_0_0)] p-4 text-sm">
        <Summary label="KB id" value={state.kb_id} />
        <Summary label="Name" value={state.name} />
        <Summary label="Description" value={state.description || '—'} />
        <Summary label="Embedding" value={state.config.embedding_model} />
        <Summary
          label="Dimension"
          value={String(state.config.embedding_dimension)}
        />
        <Summary label="Chunk strategy" value={state.config.chunk_strategy} />
        <Summary
          label="top_k / rerank_k"
          value={`${state.config.default_top_k} / ${state.config.default_rerank_k}`}
        />
        <Summary label="First document" value={state.file?.name ?? '—'} />
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
        <button
          type="button"
          onClick={onBack}
          disabled={inFlight}
          className="rounded border border-[oklch(0.92_0_0)] px-4 py-2 text-sm hover:bg-[oklch(0.96_0_0)] disabled:opacity-50"
        >
          ← Back
        </button>
        <button
          type="button"
          onClick={onExecute}
          disabled={inFlight || allDone}
          className="rounded bg-[oklch(0.42_0.04_260)] px-4 py-2 text-sm font-medium text-white hover:bg-[oklch(0.36_0.04_260)] disabled:opacity-50"
        >
          {inFlight
            ? 'Running…'
            : allDone
              ? 'Done — redirecting…'
              : 'Create + Ingest'}
        </button>
      </div>
    </div>
  );
}

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
      <span className="block text-xs font-medium uppercase tracking-wide text-[oklch(0.45_0_0)]">
        {label}
      </span>
      <div className="mt-1">{children}</div>
      {error && (
        <span className="mt-1 block text-xs text-[oklch(0.57_0.22_25)]">
          {error}
        </span>
      )}
    </label>
  );
}

function Summary({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b border-[oklch(0.92_0_0)] py-1.5 last:border-0">
      <dt className="text-[oklch(0.45_0_0)]">{label}</dt>
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
  let cls = 'text-[oklch(0.55_0_0)]';
  if (pending) {
    icon = '◐';
    cls = 'text-[oklch(0.42_0.04_260)] animate-pulse';
  } else if (error) {
    icon = '✗';
    cls = 'text-[oklch(0.57_0.22_25)]';
  } else if (success) {
    icon = '✓';
    cls = 'text-[oklch(0.65_0.16_145)]';
  }
  return (
    <li className="flex items-start gap-3">
      <span className={`mt-0.5 font-mono ${cls}`}>{icon}</span>
      <div className="flex-1">
        <div>{label}</div>
        {error && (
          <div className="mt-0.5 text-xs text-[oklch(0.57_0.22_25)]">
            {error.message}
          </div>
        )}
      </div>
    </li>
  );
}

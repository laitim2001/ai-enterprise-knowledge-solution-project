'use client';

/**
 * KB creation wizard (`/kb/new`) — W22 F5b direct-copy from mockup
 * `references/design-mockups/ekp-page-kb-new.jsx` PageKbNew
 * (per CLAUDE.md §5.7 H7 strict fidelity 2026-05-18).
 *
 * 5-step wizard reordered to mockup canonical sequence:
 *   1. Identity (KB id + name + description; kb_id_auto-derive switch)
 *   2. Format & chunking (embedding model + dim + chunk strategy)
 *   3. Multimodal (pipeline diagram + image extraction toggles +
 *                  captioning Tier 2 + dedup + low_value Tier 2 +
 *                  return_images_in_chat UI switch + outcome preview)
 *   4. Retrieval defaults (top_k + rerank_k + reranker locked per ADR-0012)
 *   5. Review & create (16-row summary table + POST /kb)
 *
 * F5b scope removal (per H7 — mockup wins): the W20 first-doc file picker
 * is dropped here. Mockup `/kb/new` provisions an empty KB; document
 * ingestion is the `/kb/[id]/upload` `PageUploadWizard` flow (F6.2).
 * Result: /kb/new creates empty KB → redirects to /kb/[id] → user adds
 * documents via the upload wizard.
 *
 * Preserved (per W22 plan §0):
 *   - kbApi.create mutation + Azure index provisioning per ADR-0018
 *   - KbConfig schema (all 9 backend fields)
 *   - useRouter redirect to /kb/[id]
 *   - useQueryClient invalidation for /kb list refetch
 *
 * UI-only state not in KbConfig (Tier 2 preview only — never sent to backend):
 *   - kb_id_auto (derive kb_id from name on the fly)
 *   - captioning_model / low_value_threshold / render_pdf_pages
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Edit3,
  Eye,
  Layers,
  Shield,
  Sparkles,
  TriangleAlert,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Fragment, useEffect, useState, type ReactNode } from 'react';

import {
  DEFAULT_KB_CONFIG,
  IMAGE_DENSE_PRESET,
  kbApi,
  type KbConfig,
  type KbCreatePayload,
} from '@/lib/api/kb';

// ──────────────────────────────────────────────────────────────────────────
// Form state — superset of KbConfig + UI-only fields
// ──────────────────────────────────────────────────────────────────────────

type CaptioningModel = 'off' | 'gpt-5.5-vision' | 'azure-doc-intel';

interface WizardForm {
  name: string;
  description: string;
  kb_id: string;
  kb_id_auto: boolean;
  // Backend KbConfig fields (sent on POST /kb)
  embedding_model: KbConfig['embedding_model'];
  embedding_dimension: KbConfig['embedding_dimension'];
  chunk_strategy: KbConfig['chunk_strategy'];
  extract_embedded_images: KbConfig['extract_embedded_images'];
  slide_screenshots: KbConfig['slide_screenshots'];
  dedup_strategy: KbConfig['dedup_strategy'];
  return_images_in_chat: KbConfig['return_images_in_chat'];
  default_top_k: KbConfig['default_top_k'];
  default_rerank_k: KbConfig['default_rerank_k'];
  // Tier 2 preview only — never sent to backend
  captioning_model: CaptioningModel;
  low_value_threshold: number;
  render_pdf_pages: boolean;
  // Apply the W69 image-dense recall preset (IMAGE_DENSE_PRESET) at create time.
  // Expanded into the KbConfig on POST /kb; off = leave those knobs at default.
  image_dense_preset: boolean;
}

type UpdateFn = <K extends keyof WizardForm>(key: K, value: WizardForm[K]) => void;

// Blob-container-safe — matches the backend KbCreate validator: lowercase alnum
// separated by SINGLE dashes (no underscores, no leading/trailing/consecutive
// dashes). Manual-id entry is checked against this so it can't drift from the
// auto-derive slugify; both now reject exactly what Azure Blob would reject.
const KB_ID_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const STEPS: ReadonlyArray<{ id: number; labelKey: string; hintKey: string }> = [
  { id: 0, labelKey: 'stepIdentityLabel', hintKey: 'stepIdentityHint' },
  { id: 1, labelKey: 'stepFormatLabel', hintKey: 'stepFormatHint' },
  { id: 2, labelKey: 'stepMultimodalLabel', hintKey: 'stepMultimodalHint' },
  { id: 3, labelKey: 'stepRetrievalLabel', hintKey: 'stepRetrievalHint' },
  { id: 4, labelKey: 'stepReviewLabel', hintKey: 'stepReviewHint' },
];

// ──────────────────────────────────────────────────────────────────────────
// Page
// ──────────────────────────────────────────────────────────────────────────

export default function KbNewPage() {
  const t = useTranslations('KbNew');
  const router = useRouter();
  const queryClient = useQueryClient();

  const [step, setStep] = useState(0);
  const [form, setForm] = useState<WizardForm>({
    name: '',
    description: '',
    kb_id: '',
    kb_id_auto: true,
    embedding_model: DEFAULT_KB_CONFIG.embedding_model,
    embedding_dimension: DEFAULT_KB_CONFIG.embedding_dimension,
    chunk_strategy: DEFAULT_KB_CONFIG.chunk_strategy,
    extract_embedded_images: true,
    slide_screenshots: true,
    dedup_strategy: DEFAULT_KB_CONFIG.dedup_strategy,
    return_images_in_chat: true,
    default_top_k: DEFAULT_KB_CONFIG.default_top_k,
    default_rerank_k: DEFAULT_KB_CONFIG.default_rerank_k,
    captioning_model: 'off',
    low_value_threshold: 0.3,
    render_pdf_pages: false,
    image_dense_preset: false,
  });

  const update: UpdateFn = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
  };

  // Auto-derive kb_id from name when kb_id_auto enabled (mockup lines 31-36).
  // Functional setter prevents form.kb_id read → no infinite loop.
  useEffect(() => {
    if (!form.kb_id_auto || !form.name) return;
    // Collapse ANY run of non-alphanumerics (spaces, dashes, underscores) to a
    // single dash. The old [^a-z0-9_-] kept literal dashes, so "A - B" became
    // "a---b" — a consecutive-dash kb_id that Azure Blob rejects (InvalidResourceName)
    // for the ekp-kb-{kb_id}-screenshots / -sources containers, silently breaking
    // image ingest + KB reindex (chunks still index because the AI Search index
    // name is more lenient). Strip leading/trailing dashes AFTER the length clamp
    // so a 40-char cut can't re-expose a trailing dash.
    const safe = form.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .slice(0, 40)
      .replace(/^-+|-+$/g, '');
    setForm((f) => (f.kb_id === safe ? f : { ...f, kb_id: safe }));
  }, [form.name, form.kb_id_auto]);

  const createMutation = useMutation({
    mutationFn: (payload: KbCreatePayload) => kbApi.create(payload),
  });

  async function handleCreate() {
    const config: KbConfig = {
      embedding_model: form.embedding_model,
      embedding_dimension: form.embedding_dimension,
      chunk_strategy: form.chunk_strategy,
      extract_embedded_images: form.extract_embedded_images,
      slide_screenshots: form.slide_screenshots,
      dedup_strategy: form.dedup_strategy,
      return_images_in_chat: form.return_images_in_chat,
      default_top_k: form.default_top_k,
      // W69 image-dense preset overrides rerank_k + adds the two image-recall knobs
      // (neighbour max aux images, max images/answer). Off = leave them at default/null.
      default_rerank_k: form.image_dense_preset
        ? IMAGE_DENSE_PRESET.default_rerank_k
        : form.default_rerank_k,
      ...(form.image_dense_preset
        ? {
            citation_neighbour_max_aux_images:
              IMAGE_DENSE_PRESET.citation_neighbour_max_aux_images,
            max_images_per_answer: IMAGE_DENSE_PRESET.max_images_per_answer,
          }
        : {}),
    };
    try {
      const created = await createMutation.mutateAsync({
        kb_id: form.kb_id,
        name: form.name,
        description: form.description,
        config,
      });
      queryClient.invalidateQueries({ queryKey: ['kb'] });
      router.push(`/kb/${created.kb_id}`);
    } catch {
      // Surface inline below the create button.
    }
  }

  return (
    <div className="content">
      <div className="content-narrow">
        {/* Page header — mockup lines 49-62 */}
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
                href="/kb"
                className="btn btn-ghost btn-xs btn-ghost-muted"
                style={{ textDecoration: 'none' }}
              >
                <ChevronLeft size={12} /> {t('backToKnowledge')}
              </Link>
            </div>
            <h1 className="page-title">{t('pageTitle')}</h1>
            <p className="page-subtitle">
              {t.rich('subtitle', {
                b: (chunks) => <b>{chunks}</b>,
                mono: (chunks) => <span className="mono">{chunks}</span>,
                indexId: form.kb_id || '{kb_id}',
              })}
            </p>
          </div>
        </div>

        {/* Stepper — mockup lines 64-91 */}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
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
                        step === s.id
                          ? '2px solid oklch(var(--accent))'
                          : '0',
                    }}
                  >
                    {step > s.id ? <Check size={14} /> : i + 1}
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: 13.5,
                        fontWeight: step === s.id ? 600 : 500,
                      }}
                    >
                      {t(s.labelKey)}
                    </div>
                    <div className="text-xs muted">{t(s.hintKey)}</div>
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
                    }}
                  />
                )}
              </Fragment>
            ))}
          </div>
        </div>

        {step === 0 && (
          <StepIdentity form={form} update={update} onNext={() => setStep(1)} />
        )}
        {step === 1 && (
          <StepConfig
            form={form}
            update={update}
            onBack={() => setStep(0)}
            onNext={() => setStep(2)}
          />
        )}
        {step === 2 && (
          <StepMultimodal
            form={form}
            update={update}
            onBack={() => setStep(1)}
            onNext={() => setStep(3)}
          />
        )}
        {step === 3 && (
          <StepDefaults
            form={form}
            update={update}
            onBack={() => setStep(2)}
            onNext={() => setStep(4)}
          />
        )}
        {step === 4 && (
          <StepReview
            form={form}
            onBack={() => setStep(3)}
            onCreate={handleCreate}
            pending={createMutation.isPending}
            error={createMutation.error}
          />
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 0 — Identity (mockup lines 350-396)
// ──────────────────────────────────────────────────────────────────────────

function StepIdentity({
  form,
  update,
  onNext,
}: {
  form: WizardForm;
  update: UpdateFn;
  onNext: () => void;
}) {
  const t = useTranslations('KbNew');
  const trimmedName = form.name.trim();
  const trimmedId = form.kb_id.trim();
  const idValid = trimmedId.length > 0 && KB_ID_PATTERN.test(trimmedId);
  const canContinue = trimmedName.length > 0 && idValid;

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{t('identityCardTitle')}</h3>
      </div>
      <div className="card-body">
        <div className="field">
          <label className="label" htmlFor="kbnew-name">
            {t('nameLabel')}
          </label>
          <input
            id="kbnew-name"
            className="input"
            value={form.name}
            onChange={(e) => update('name', e.target.value)}
            placeholder={t('namePlaceholder')}
          />
          <div className="hint">{t('nameHint')}</div>
        </div>
        <div className="field">
          <label className="label" htmlFor="kbnew-desc">
            {t('descLabel')}
          </label>
          <textarea
            id="kbnew-desc"
            className="input"
            rows={3}
            value={form.description}
            onChange={(e) => update('description', e.target.value)}
            placeholder={t('descPlaceholder')}
          />
          <div className="hint">{t('descHint')}</div>
        </div>
        <div className="field">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <label
              className="label"
              htmlFor="kbnew-id"
              style={{ flex: 1, marginBottom: 0 }}
            >
              kb_id{' '}
              <Shield
                size={11}
                style={{
                  verticalAlign: '-2px',
                  marginLeft: 4,
                  color: 'oklch(var(--warning))',
                }}
              />
            </label>
            <div className="row">
              <span
                className="switch"
                data-on={form.kb_id_auto}
                onClick={() => update('kb_id_auto', !form.kb_id_auto)}
                role="switch"
                aria-checked={form.kb_id_auto}
                tabIndex={0}
              />
              <span className="text-xs muted">{t('autoDeriveLabel')}</span>
            </div>
          </div>
          <input
            id="kbnew-id"
            className="input mono"
            value={form.kb_id}
            onChange={(e) => update('kb_id', e.target.value)}
            disabled={form.kb_id_auto}
            placeholder="customer-service-sop"
            style={{ marginTop: 6 }}
          />
          <div className="hint">
            {t.rich('kbIdHint', {
              b: (chunks) => (
                <b style={{ color: 'oklch(var(--warning))' }}>{chunks}</b>
              ),
              mono: (chunks) => <span className="mono">{chunks}</span>,
              indexId: form.kb_id || '{kb_id}',
            })}
          </div>
          {!idValid && trimmedId.length > 0 && (
            <div
              className="hint"
              style={{ color: 'oklch(var(--destructive))' }}
              role="alert"
            >
              {t('kbIdError')}
            </div>
          )}
        </div>
      </div>
      <div className="card-footer">
        <div className="text-xs muted mono">{t('step1of5')}</div>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          disabled={!canContinue}
          onClick={onNext}
        >
          {t('continue')} <ChevronRight size={13} />
        </button>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 1 — Format & chunking (mockup lines 398-491)
// ──────────────────────────────────────────────────────────────────────────

function StepConfig({
  form,
  update,
  onBack,
  onNext,
}: {
  form: WizardForm;
  update: UpdateFn;
  onBack: () => void;
  onNext: () => void;
}) {
  const t = useTranslations('KbNew');
  const embeddings: Array<{
    id: KbConfig['embedding_model'];
    label: string;
    hint: string;
    supported: boolean;
  }> = [
    {
      id: 'text-embedding-3-large',
      label: 'embed-3-large',
      hint: t('embedLargeHint'),
      supported: true,
    },
    {
      id: 'text-embedding-3-small' as KbConfig['embedding_model'],
      label: 'embed-3-small',
      hint: t('embedSmallHint'),
      supported: false,
    },
  ];

  const dimensions: ReadonlyArray<KbConfig['embedding_dimension']> = [
    768, 1024, 1536, 3072,
  ];

  const chunkers: Array<{
    id: KbConfig['chunk_strategy'];
    label: string;
    hint: string;
    supported: boolean;
  }> = [
    {
      id: 'auto',
      label: t('chunkerAutoLabel'),
      hint: t('chunkerAutoHint'),
      supported: true,
    },
    {
      id: 'layout_aware',
      label: t('chunkerLayoutLabel'),
      hint: t('chunkerLayoutHint'),
      supported: true,
    },
    {
      id: 'slide_based',
      label: t('chunkerSlideLabel'),
      hint: t('chunkerSlideHint'),
      supported: true,
    },
    {
      id: 'heading_aware',
      label: t('chunkerHeadingLabel'),
      hint: t('chunkerHeadingHint'),
      supported: false,
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{t('configCardTitle')}</h3>
        <span className="badge badge-warning">
          <Shield size={10} /> {t('configLockedBadge')}
        </span>
      </div>
      <div className="card-body">
        <div className="banner banner-warning" style={{ marginBottom: 16 }}>
          <TriangleAlert
            size={14}
            style={{ color: 'oklch(var(--warning))' }}
          />
          <div style={{ flex: 1, fontSize: 12.5, lineHeight: 1.55 }}>
            {t.rich('configWarnBanner', {
              b: (chunks) => <b>{chunks}</b>,
              nPlus1: '{n+1}',
            })}
          </div>
        </div>

        <div className="field">
          <label className="label">{t('embeddingModelLabel')}</label>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 10,
            }}
          >
            {embeddings.map((m) => {
              const active = form.embedding_model === m.id;
              return (
                <div
                  key={m.id}
                  onClick={() => m.supported && update('embedding_model', m.id)}
                  style={{
                    border: `1px solid ${
                      active
                        ? 'oklch(var(--foreground) / 0.4)'
                        : 'oklch(var(--border))'
                    }`,
                    background: active
                      ? 'oklch(var(--muted) / 0.5)'
                      : 'transparent',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    opacity: m.supported ? 1 : 0.55,
                    cursor: m.supported ? 'pointer' : 'default',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      flexWrap: 'wrap',
                    }}
                  >
                    <span
                      className="mono"
                      style={{ fontSize: 12.5, fontWeight: 600 }}
                    >
                      {m.label}
                    </span>
                    {active && <Check size={11} className="muted" />}
                    {!m.supported && (
                      <span className="badge badge-accent">TIER 2</span>
                    )}
                  </div>
                  <div className="text-xs muted" style={{ marginTop: 4 }}>
                    {m.hint}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="field">
          <label className="label">{t('embeddingDimensionLabel')}</label>
          <div className="seg" style={{ width: '100%', maxWidth: 320 }}>
            {dimensions.map((d) => (
              <button
                key={d}
                type="button"
                className="seg-btn"
                data-active={form.embedding_dimension === d}
                onClick={() => update('embedding_dimension', d)}
                style={{ flex: 1 }}
              >
                {d}d
              </button>
            ))}
          </div>
          <div className="hint">{t('dimensionHint')}</div>
        </div>

        <div className="field">
          <label className="label">{t('chunkStrategyLabel')}</label>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 10,
            }}
          >
            {chunkers.map((s) => {
              const active = form.chunk_strategy === s.id;
              return (
                <div
                  key={s.id}
                  onClick={() => s.supported && update('chunk_strategy', s.id)}
                  style={{
                    border: `1px solid ${
                      active
                        ? 'oklch(var(--foreground) / 0.4)'
                        : 'oklch(var(--border))'
                    }`,
                    background: active
                      ? 'oklch(var(--muted) / 0.5)'
                      : 'transparent',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    opacity: s.supported ? 1 : 0.55,
                    cursor: s.supported ? 'pointer' : 'default',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <span style={{ fontWeight: 500, fontSize: 13 }}>
                      {s.label}
                    </span>
                    {active && <Check size={11} className="muted" />}
                    {!s.supported && (
                      <span className="badge badge-muted">N/A</span>
                    )}
                  </div>
                  <div
                    className="text-xs muted"
                    style={{ marginTop: 4, lineHeight: 1.45 }}
                  >
                    {s.hint}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div className="card-footer">
        <button type="button" className="btn btn-ghost btn-sm" onClick={onBack}>
          ← {t('back')}
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={onNext}
        >
          {t('continue')} <ChevronRight size={13} />
        </button>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 2 — Multimodal (mockup lines 103-312)
// ──────────────────────────────────────────────────────────────────────────

function StepMultimodal({
  form,
  update,
  onBack,
  onNext,
}: {
  form: WizardForm;
  update: UpdateFn;
  onBack: () => void;
  onNext: () => void;
}) {
  const t = useTranslations('KbNew');
  const pipeline = [
    {
      i: 1,
      label: t('pipelineParseLabel'),
      ic: '📄',
      note: t('pipelineParseNote', {
        schema: 'EmbeddedImage{sha256, alt_text, doc_order}',
      }),
      tier2: false,
    },
    {
      i: 2,
      label: t('pipelineCaptionLabel'),
      ic: '🤖',
      note: t('pipelineCaptionNote'),
      tier2: true,
    },
    {
      i: 3,
      label: t('pipelineDedupLabel'),
      ic: '🔗',
      note: t('pipelineDedupNote'),
      tier2: false,
    },
    {
      i: 4,
      label: t('pipelineBindLabel'),
      ic: '🔀',
      note: t('pipelineBindNote'),
      tier2: false,
    },
    {
      i: 5,
      label: t('pipelineIndexLabel'),
      ic: '📦',
      note: t('pipelineIndexNote'),
      tier2: false,
    },
  ];

  const captioningOptions: Array<{
    id: CaptioningModel;
    label: string;
    hint: string;
    tier2: boolean;
    recommended?: boolean;
  }> = [
    {
      id: 'gpt-5.5-vision',
      label: 'GPT-5.5 Vision',
      hint: t('captionGptHint'),
      tier2: true,
    },
    {
      id: 'azure-doc-intel',
      label: 'Azure Doc Intelligence',
      hint: t('captionAzureHint'),
      tier2: true,
    },
    {
      id: 'off',
      label: t('captionOffLabel'),
      hint: t('captionOffHint'),
      tier2: false,
      recommended: true,
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{t('multimodalCardTitle')}</h3>
        <span className="badge badge-info">
          <Layers size={10} /> {t('textImageRetrieval')}
        </span>
      </div>
      <div className="card-body">
        {/* Hero pipeline explainer — mockup lines 112-171 */}
        <div
          style={{
            padding: 14,
            background: 'oklch(var(--info) / 0.06)',
            border: '1px solid oklch(var(--info) / 0.22)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 18,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              marginBottom: 10,
            }}
          >
            <Layers size={14} style={{ color: 'oklch(var(--info))' }} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>
              {t('heroTitle')}
            </span>
          </div>
          <div
            className="text-xs"
            style={{ lineHeight: 1.65, marginBottom: 12 }}
          >
            {t.rich('heroDesc', {
              b: (chunks) => <b>{chunks}</b>,
              mono: (chunks) => <span className="mono">{chunks}</span>,
              docOrder: '{doc_order}',
            })}
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              gap: 4,
              background: 'oklch(var(--card))',
              border: '1px solid oklch(var(--border))',
              borderRadius: 'var(--radius-sm)',
              padding: 10,
              fontSize: 11,
            }}
          >
            {pipeline.map((s, idx, arr) => (
              <div
                key={s.i}
                style={{
                  position: 'relative',
                  padding: '8px 8px 6px',
                  textAlign: 'center',
                  background: s.tier2
                    ? 'oklch(var(--accent) / 0.06)'
                    : 'transparent',
                  border: s.tier2
                    ? '1px dashed oklch(var(--accent) / 0.3)'
                    : '1px solid transparent',
                  borderRadius: 4,
                }}
              >
                <div style={{ fontSize: 18, marginBottom: 4 }}>{s.ic}</div>
                <div
                  style={{ fontSize: 11, fontWeight: 600, marginBottom: 2 }}
                >
                  {s.i}. {s.label}
                  {s.tier2 && (
                    <div
                      className="badge badge-accent"
                      style={{
                        marginTop: 4,
                        fontSize: 9,
                        padding: '0 4px',
                        height: 14,
                      }}
                    >
                      T2
                    </div>
                  )}
                </div>
                <div
                  className="text-xs muted"
                  style={{ fontSize: 10, lineHeight: 1.35 }}
                >
                  {s.note}
                </div>
                {idx < arr.length - 1 && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '50%',
                      right: -8,
                      width: 12,
                      height: 1,
                      background: 'oklch(var(--info) / 0.4)',
                    }}
                  />
                )}
              </div>
            ))}
          </div>
          <div
            className="text-xs muted"
            style={{ marginTop: 8, fontSize: 10.5 }}
          >
            <span
              className="badge badge-accent"
              style={{
                fontSize: 9,
                padding: '0 4px',
                height: 14,
                marginRight: 4,
              }}
            >
              T2
            </span>
            {t('t2Legend')}
          </div>
        </div>

        {/* ACTIVE: Image extraction sources */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 10,
          }}
        >
          <span className="badge badge-success">
            <span className="badge-dot" /> ACTIVE
          </span>
          <span className="nav-section-label" style={{ padding: 0 }}>
            {t('sectionImageExtraction')}
          </span>
        </div>
        <div className="col" style={{ gap: 8, marginBottom: 18 }}>
          <OptionRow
            checked={form.extract_embedded_images}
            onToggle={(v) => update('extract_embedded_images', v)}
            title={t('optEmbeddedTitle')}
            desc={t('optEmbeddedDesc')}
            badge={t('optEmbeddedBadge')}
          />
          <OptionRow
            checked={form.slide_screenshots}
            onToggle={(v) => update('slide_screenshots', v)}
            title={t('optSlideTitle')}
            desc={t('optSlideDesc')}
            tier2
          />
          <OptionRow
            checked={form.render_pdf_pages}
            onToggle={(v) => update('render_pdf_pages', v)}
            title={t('optPdfTitle')}
            desc={t('optPdfDesc')}
            tier2
            warn={form.render_pdf_pages ? t('optPdfWarn') : null}
          />
          {/* W69 image-recall preset — same IMAGE_DENSE_PRESET as the KB Detail
              Settings 「套用配方」row, surfaced at create time so an image-heavy
              manual gets full image recall without a post-create Settings trip. */}
          <OptionRow
            checked={form.image_dense_preset}
            onToggle={(v) => update('image_dense_preset', v)}
            title={t('optPresetTitle')}
            desc={t('optPresetDesc')}
            badge={t('optPresetBadge')}
          />
        </div>

        {/* TIER 2: Captioning */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 10,
          }}
        >
          <span className="badge badge-accent">TIER 2 PREVIEW</span>
          <span className="nav-section-label" style={{ padding: 0 }}>
            {t('sectionCaptioning')}
          </span>
          <span className="text-xs muted" style={{ marginLeft: 4 }}>
            {t('captioningNote')}
          </span>
        </div>
        <div className="field" style={{ marginBottom: 18, opacity: 0.85 }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: 10,
            }}
          >
            {captioningOptions.map((c) => {
              const active = form.captioning_model === c.id;
              const borderColor =
                active && !c.tier2
                  ? 'oklch(var(--foreground))'
                  : active && c.tier2
                    ? 'oklch(var(--accent) / 0.5)'
                    : 'oklch(var(--border))';
              const bg =
                active && !c.tier2
                  ? 'oklch(var(--muted) / 0.5)'
                  : active && c.tier2
                    ? 'oklch(var(--accent) / 0.06)'
                    : 'transparent';
              return (
                <div
                  key={c.id}
                  onClick={() => update('captioning_model', c.id)}
                  style={{
                    border: `1px solid ${borderColor}`,
                    background: bg,
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                    position: 'relative',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      flexWrap: 'wrap',
                    }}
                  >
                    <span style={{ fontWeight: 500, fontSize: 13 }}>
                      {c.label}
                    </span>
                    {active && <Check size={11} className="muted" />}
                    {c.tier2 && (
                      <span
                        className="badge badge-accent"
                        style={{ fontSize: 9.5 }}
                      >
                        T2
                      </span>
                    )}
                    {c.recommended && (
                      <span
                        className="badge badge-success"
                        style={{ fontSize: 9.5 }}
                      >
                        BETA DEFAULT
                      </span>
                    )}
                  </div>
                  <div
                    className="text-xs muted"
                    style={{ marginTop: 4, lineHeight: 1.4 }}
                  >
                    {c.hint}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ACTIVE: Dedup */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 10,
          }}
        >
          <span className="badge badge-success">
            <span className="badge-dot" /> ACTIVE
          </span>
          <span className="nav-section-label" style={{ padding: 0 }}>
            {t('sectionDedup')}
          </span>
        </div>
        <div className="field" style={{ marginBottom: 18 }}>
          <select
            className="select"
            value={form.dedup_strategy}
            onChange={(e) =>
              update(
                'dedup_strategy',
                e.target.value as KbConfig['dedup_strategy'],
              )
            }
          >
            <option value="sha256">{t('dedupSha256')}</option>
            <option value="none">{t('dedupNone')}</option>
            <option value="perceptual" disabled>
              {t('dedupPerceptual')}
            </option>
          </select>
          <div className="hint">
            {t.rich('dedupHint', {
              mono: (chunks) => <span className="mono">{chunks}</span>,
            })}
          </div>
        </div>

        {/* TIER 2: low_value image filter */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 10,
          }}
        >
          <span className="badge badge-accent">TIER 2 PREVIEW</span>
          <span className="nav-section-label" style={{ padding: 0 }}>
            {t('sectionLowValue')}
          </span>
          <span className="text-xs muted">{t('lowValueNote')}</span>
        </div>
        <div className="field" style={{ marginBottom: 18, opacity: 0.85 }}>
          <label className="label" htmlFor="kbnew-low-value">
            {t('thresholdLabel')} ·{' '}
            <span className="mono text-xs muted">
              {form.low_value_threshold.toFixed(2)}
            </span>
          </label>
          <input
            id="kbnew-low-value"
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={form.low_value_threshold}
            onChange={(e) =>
              update('low_value_threshold', Number(e.target.value))
            }
            style={{ width: '100%' }}
          />
          <div className="hint">
            <span
              className="badge badge-accent"
              style={{ fontSize: 9.5, marginRight: 4 }}
            >
              T2
            </span>
            {t.rich('lowValueHint', {
              mono: (chunks) => <span className="mono">{chunks}</span>,
            })}
          </div>
        </div>

        <div className="hr" />

        {/* UI BEHAVIOR: return_images_in_chat */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            marginBottom: 10,
          }}
        >
          <span className="badge badge-info">
            <Eye size={9} /> UI BEHAVIOR
          </span>
          <span className="nav-section-label" style={{ padding: 0 }}>
            {t('sectionQueryTime')}
          </span>
        </div>
        <div
          className="row"
          style={{ marginBottom: 4, alignItems: 'flex-start', gap: 10 }}
        >
          <span
            className="switch"
            data-on={form.return_images_in_chat}
            onClick={() =>
              update('return_images_in_chat', !form.return_images_in_chat)
            }
            role="switch"
            aria-checked={form.return_images_in_chat}
            tabIndex={0}
          />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 13, fontWeight: 500 }}>
              {t('renderInlineTitle')}
            </div>
            <div className="text-xs muted" style={{ lineHeight: 1.5 }}>
              {t.rich('renderInlineDesc', {
                mono: (chunks) => <span className="mono">{chunks}</span>,
              })}
            </div>
          </div>
        </div>

        {/* Outcome preview */}
        <div
          style={{
            marginTop: 16,
            padding: '10px 12px',
            background: 'oklch(var(--muted) / 0.5)',
            border: '1px dashed oklch(var(--border-strong))',
            borderRadius: 'var(--radius-sm)',
            fontSize: 12.5,
            lineHeight: 1.6,
          }}
        >
          <b style={{ color: 'oklch(var(--foreground))' }}>
            {t('outcomeTitle')}
          </b>{' '}
          {t.rich('outcomeBody', {
            mono: (chunks) => <span className="mono">{chunks}</span>,
            mode: form.return_images_in_chat
              ? t('outcomeModeInline')
              : t('outcomeModeCollapsed'),
          })}
        </div>
      </div>
      <div className="card-footer">
        <button type="button" className="btn btn-ghost btn-sm" onClick={onBack}>
          ← {t('back')}
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={onNext}
        >
          {t('continue')} <ChevronRight size={13} />
        </button>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// OptionRow helper (mockup lines 314-348)
// ──────────────────────────────────────────────────────────────────────────

function OptionRow({
  checked,
  onToggle,
  title,
  desc,
  badge,
  warn,
  tier2,
}: {
  checked: boolean;
  onToggle: (v: boolean) => void;
  title: string;
  desc: string;
  badge?: string;
  warn?: string | null;
  tier2?: boolean;
}) {
  const border =
    tier2 && checked
      ? '1px solid oklch(var(--accent) / 0.4)'
      : checked
        ? '1px solid oklch(var(--foreground) / 0.4)'
        : '1px solid oklch(var(--border))';
  const bg =
    tier2 && checked
      ? 'oklch(var(--accent) / 0.05)'
      : checked
        ? 'oklch(var(--muted) / 0.5)'
        : 'transparent';
  return (
    <div
      onClick={() => onToggle(!checked)}
      style={{
        display: 'flex',
        gap: 12,
        padding: '12px 14px',
        border,
        background: bg,
        borderRadius: 'var(--radius-sm)',
        cursor: 'pointer',
      }}
    >
      <span
        className="switch"
        data-on={checked}
        style={{ flexShrink: 0, marginTop: 1 }}
      />
      <div style={{ flex: 1 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            flexWrap: 'wrap',
          }}
        >
          <span style={{ fontSize: 13, fontWeight: 500 }}>{title}</span>
          {badge && (
            <span
              className="badge badge-success"
              style={{ fontSize: 9.5 }}
            >
              {badge}
            </span>
          )}
          {tier2 && (
            <span className="badge badge-accent" style={{ fontSize: 9.5 }}>
              TIER 2
            </span>
          )}
        </div>
        <div
          className="text-xs muted"
          style={{ marginTop: 3, lineHeight: 1.5 }}
        >
          {desc}
        </div>
        {warn && checked && (
          <div
            className="text-xs"
            style={{
              marginTop: 4,
              color: 'oklch(var(--warning))',
              display: 'flex',
              gap: 4,
              alignItems: 'center',
            }}
          >
            <TriangleAlert size={11} /> {warn}
          </div>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 3 — Retrieval defaults (mockup lines 493-538)
// ──────────────────────────────────────────────────────────────────────────

function StepDefaults({
  form,
  update,
  onBack,
  onNext,
}: {
  form: WizardForm;
  update: UpdateFn;
  onBack: () => void;
  onNext: () => void;
}) {
  const t = useTranslations('KbNew');
  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{t('defaultsCardTitle')}</h3>
        <span className="badge badge-success">
          <Edit3 size={10} /> {t('editableLater')}
        </span>
      </div>
      <div className="card-body">
        <div className="banner banner-info" style={{ marginBottom: 16 }}>
          <Sparkles size={14} style={{ color: 'oklch(var(--info))' }} />
          <div style={{ flex: 1, fontSize: 12.5, lineHeight: 1.55 }}>
            {t.rich('defaultsBanner', {
              b: (chunks) => <b>{chunks}</b>,
            })}
          </div>
        </div>

        <div className="field">
          <label className="label" htmlFor="kbnew-topk">
            {t('topKLabel')} ·{' '}
            <span className="mono text-xs">{form.default_top_k}</span>
          </label>
          <input
            id="kbnew-topk"
            type="range"
            min={10}
            max={100}
            step={5}
            value={form.default_top_k}
            onChange={(e) =>
              update('default_top_k', Number(e.target.value))
            }
            style={{ width: '100%' }}
          />
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: 11,
              color: 'oklch(var(--muted-foreground))',
              fontFamily: 'var(--font-mono)',
              marginTop: 4,
            }}
          >
            <span>{t('topKFast')}</span>
            <span>{t('topKBaseline')}</span>
            <span>{t('topKThorough')}</span>
          </div>
        </div>

        <div className="field">
          <label className="label" htmlFor="kbnew-rerankk">
            {t('rerankKLabel')} ·{' '}
            <span className="mono text-xs">{form.default_rerank_k}</span>
          </label>
          <input
            id="kbnew-rerankk"
            type="range"
            min={3}
            max={20}
            value={form.default_rerank_k}
            onChange={(e) =>
              update('default_rerank_k', Number(e.target.value))
            }
            style={{ width: '100%' }}
          />
          <div className="hint">{t('rerankKHint')}</div>
        </div>

        <div className="field" style={{ marginBottom: 0 }}>
          <label className="label" htmlFor="kbnew-reranker">
            {t('rerankerLabel')}
          </label>
          <select id="kbnew-reranker" className="select" disabled>
            <option>{t('rerankerOption')}</option>
          </select>
          <div className="hint">{t('rerankerHint')}</div>
        </div>
      </div>
      <div className="card-footer">
        <button type="button" className="btn btn-ghost btn-sm" onClick={onBack}>
          ← {t('back')}
        </button>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={onNext}
        >
          {t('continue')} <ChevronRight size={13} />
        </button>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Step 4 — Review & create (mockup lines 540-584)
// ──────────────────────────────────────────────────────────────────────────

function StepReview({
  form,
  onBack,
  onCreate,
  pending,
  error,
}: {
  form: WizardForm;
  onBack: () => void;
  onCreate: () => void;
  pending: boolean;
  error: Error | null;
}) {
  const t = useTranslations('KbNew');
  const rows: Array<{
    k: string;
    v: ReactNode;
    locked: boolean;
    mono?: boolean;
  }> = [
    { k: t('rowName'), v: form.name || '—', locked: false },
    { k: t('rowDescription'), v: form.description || '—', locked: false },
    { k: 'kb_id', v: form.kb_id || '—', locked: true, mono: true },
    {
      k: t('rowIndexName'),
      v: `ekp-kb-${form.kb_id || '{kb_id}'}-v1`,
      locked: true,
      mono: true,
    },
    {
      k: t('rowBlobContainer'),
      v: `ekp-kb-${form.kb_id || '{kb_id}'}-screenshots`,
      locked: true,
      mono: true,
    },
    {
      k: t('rowEmbeddingModel'),
      v: `${form.embedding_model} · ${form.embedding_dimension}d`,
      locked: true,
      mono: true,
    },
    {
      k: t('rowChunkStrategy'),
      v: form.chunk_strategy,
      locked: true,
      mono: true,
    },
    {
      k: t('rowEmbeddedImages'),
      v: form.extract_embedded_images
        ? t('valExtracted')
        : t('valDisabled'),
      locked: true,
    },
    {
      k: t('rowSlideScreenshots'),
      v: form.slide_screenshots ? t('valSlideOn') : t('valOff'),
      locked: true,
    },
    {
      k: t('rowPdfRender'),
      v: form.render_pdf_pages ? t('valPdfOn') : t('valOff'),
      locked: true,
    },
    {
      k: t('rowCaptioningModel'),
      v: form.captioning_model === 'off'
        ? t('valCaptioningOff')
        : form.captioning_model,
      locked: true,
      mono: form.captioning_model !== 'off',
    },
    {
      k: t('rowLowValueThreshold'),
      v: form.low_value_threshold.toFixed(2),
      locked: true,
      mono: true,
    },
    {
      k: t('rowDedup'),
      v: t('valDedup', { strategy: form.dedup_strategy }),
      locked: true,
      mono: true,
    },
    {
      k: t('rowReturnImages'),
      v: form.return_images_in_chat
        ? t('valReturnYes')
        : t('valReturnNo'),
      locked: false,
    },
    {
      k: t('rowDefaultTopK'),
      v: String(form.default_top_k),
      locked: false,
      mono: true,
    },
    {
      k: t('rowDefaultRerankK'),
      v: String(form.default_rerank_k),
      locked: false,
      mono: true,
    },
  ];

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{t('reviewCardTitle')}</h3>
      </div>
      <div className="card-body card-body-tight">
        {rows.map((r, i, arr) => (
          <div
            key={r.k}
            style={{
              display: 'flex',
              alignItems: 'center',
              padding: '11px 18px',
              borderBottom:
                i < arr.length - 1
                  ? '1px solid oklch(var(--border))'
                  : 'none',
            }}
          >
            <span
              style={{
                width: 180,
                fontSize: 12.5,
                color: 'oklch(var(--muted-foreground))',
              }}
            >
              {r.k}
            </span>
            <span
              style={{
                flex: 1,
                fontSize: 13,
                fontFamily: r.mono ? 'var(--font-mono)' : 'inherit',
                fontWeight: 500,
              }}
            >
              {r.v}
            </span>
            {r.locked ? (
              <span className="badge badge-warning">
                <Shield size={10} /> {t('lockedBadge')}
              </span>
            ) : (
              <span className="badge badge-success">
                <Edit3 size={10} /> {t('editableBadge')}
              </span>
            )}
          </div>
        ))}
      </div>
      {error && (
        <div
          className="text-xs"
          style={{
            padding: '10px 18px',
            color: 'oklch(var(--destructive))',
            borderTop: '1px solid oklch(var(--border))',
          }}
          role="alert"
        >
          {t('createFailed')} {error.message}
        </div>
      )}
      <div className="card-footer">
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={onBack}
          disabled={pending}
        >
          ← {t('back')}
        </button>
        <button
          type="button"
          className="btn btn-accent"
          onClick={onCreate}
          disabled={pending}
        >
          <Check size={14} />{' '}
          {pending ? t('provisioning') : t('createKb')}
        </button>
      </div>
    </div>
  );
}

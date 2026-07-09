'use client';

/**
 * Per-document config tab — W58 / ADR-0051 (platform P2b / Gap A UI).
 *
 * 100% mockup fidelity match against references/design-mockups/ekp-page-doc-detail.jsx
 * `DocConfigTab` (per CLAUDE.md §5.7 H7). Consumes the W57 / ADR-0050 per-doc CRUD
 * API (docConfigApi) + the config-test harness (configTestApi).
 *
 * Per ADR-0050/0051 the per-DOCUMENT surface exposes ONLY the post-retrieval knobs
 * (answer_detail + citation expansion + neighbour images + max_images + overview
 * pin). The retrieval-entry knobs (top_k / rerank / parent_doc) stay per-KB (they
 * drive retrieval before any doc is cited) — surfaced here as an explainer card.
 *
 * W81 / ADR-0060 — image-anchor knobs (inline markers W70 / section 錨定 + per-anchor
 * cap W75) added as a design-stage expansion: the mockup has NO doc-level design for
 * these (section 錨定 post-dates the mockup), so per the user-approved 方案 A they reuse
 * the existing DocTuneGroup/DocSwitchKnob/DocTuneKnob mockup-aligned components — zero
 * new visuals. This is the one deliberate departure from strict mockup fidelity above.
 *
 * Self-contained (DocTune* helpers + config-test card duplicated from the KB
 * SettingsTab pattern rather than extracted) — the KB SettingsTab uses 繼承全域
 * framing, this uses 繼承 KB, and the 3174-line KB page stays untouched
 * (Karpathy §1.3). Deviation from W58 plan R2「傾向抽出共用」logged in the plan
 * changelog.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  ChevronRight,
  Download,
  Edit,
  Eye,
  Link as LinkIcon,
  RefreshCw,
  Settings,
  Shield,
  Tag,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useMemo, useState, type ReactNode } from 'react';
import { toast } from 'sonner';

import { docConfigApi, type DocConfig } from '@/lib/api/doc-config';
import { documentsApi, type DocProfileInfo } from '@/lib/api/documents';
import {
  configTestApi,
  type ConfigRunSummary,
  type ConfigTestResult,
  type DraftRetrievalConfig,
} from '@/lib/api/config-test';

// W77 / ADR-0056 層 A 段③ — 文件畫像(L3)helpers per mockup ekp-page-doc-detail.jsx:405-429.
const DOC_PROFILE_LABELS: Record<string, string> = {
  P1_sop_imgdense: 'P1 Image-dense SOP',
  P1_sop_text: 'P1 Text SOP',
  P2_prose: 'P2 Prose',
  P3_slide_imgdense: 'P3 Image-dense slides',
  P3_slide_text: 'P3 Text slides',
  P4_scan_imgdense: 'P4 Scan',
  P5_form: 'P5 Form',
};

function DocProfileBadge({ profile }: { profile: DocProfileInfo }) {
  // W79 / ADR-0058 — effective = manual_override ?? system auto profile.
  const effective = profile.manual_override ?? profile.profile;
  const overridden = profile.manual_override != null;
  // 低信心黃旗只對 system auto;override = 人手確定,唔標低信心。
  const low = !overridden && (profile.fallback_applied || profile.confidence < 0.7);
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      <span className={`badge ${low ? 'badge-warning' : 'badge-muted'}`} style={{ fontSize: 11 }}>
        <span className="badge-dot" /> {DOC_PROFILE_LABELS[effective] ?? effective}
      </span>
      {overridden ? (
        <span className="text-xs muted">Manually overridden</span>
      ) : (
        <span className="text-xs muted mono">Confidence {Math.round(profile.confidence * 100)}%</span>
      )}
    </span>
  );
}

function ProfileSignal({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat">
      <div className="stat-label" style={{ fontSize: 10.5 }}>
        {label}
      </div>
      <div className="stat-value" style={{ fontSize: 17 }}>
        {value}
      </div>
    </div>
  );
}

// The post-retrieval numeric/bool knobs editable per document (DocConfig minus
// answer_detail, which is its own seg). null = inherit per-KB.
const DOC_TUNE_KNOB_KEYS = [
  'enable_citation_post_hoc_expansion',
  'citation_expansion_max_aux',
  'citation_expansion_window',
  'citation_expansion_section_path_prefix_depth',
  'enable_citation_neighbour_images',
  'citation_neighbour_max_aux_images',
  'citation_neighbour_section_path_prefix_depth',
  'max_images_per_answer',
  'enable_chapter_overview_pin',
  // W81 / ADR-0060 — image-anchor knobs (mirror DocConfig; auto-wired into
  // setKnob / buildDraftConfig / dirty / saveMutation via this key list).
  'enable_inline_image_markers',
  'enable_section_anchored_aux_images',
  'section_anchor_nearest', // W99 / ADR-0056 §Amendment — leaf 級 doc_order-nearest 錨點
  'section_anchor_max_per_anchor',
] as const;

type DocKnobKey = (typeof DOC_TUNE_KNOB_KEYS)[number];
type DocKnobState = Record<DocKnobKey, number | boolean | null>;
type AnswerDetail = 'concise' | 'detailed' | null;

export function DocConfigTab({
  kbId,
  docId,
  kbName,
  profile,
}: {
  kbId: string;
  docId: string;
  kbName: string;
  profile?: DocProfileInfo | null;
}) {
  const queryClient = useQueryClient();
  const configQuery = useQuery<DocConfig>({
    queryKey: ['kb', kbId, 'doc-config', docId],
    queryFn: () => docConfigApi.get(kbId, docId),
    enabled: !!kbId && !!docId,
  });

  if (configQuery.isLoading) {
    return (
      <div className="banner banner-info">
        <span className="spinner" />
        <div style={{ flex: 1 }}>Loading per-document config…</div>
      </div>
    );
  }
  if (configQuery.isError || !configQuery.data) {
    return (
      <div className="banner banner-error">
        <AlertTriangle size={16} />
        <div style={{ flex: 1 }}>
          Failed to load per-document config:{' '}
          {String((configQuery.error as Error)?.message ?? 'unknown')}
        </div>
      </div>
    );
  }

  return (
    <DocConfigEditor
      kbId={kbId}
      docId={docId}
      kbName={kbName}
      profile={profile}
      saved={configQuery.data}
      onSaved={() =>
        void queryClient.invalidateQueries({
          queryKey: ['kb', kbId, 'doc-config', docId],
        })
      }
    />
  );
}

function DocConfigEditor({
  kbId,
  docId,
  kbName,
  profile,
  saved,
  onSaved,
}: {
  kbId: string;
  docId: string;
  kbName: string;
  profile?: DocProfileInfo | null;
  saved: DocConfig;
  onSaved: () => void;
}) {
  const [answerDetail, setAnswerDetail] = useState<AnswerDetail>(saved.answer_detail ?? null);
  const [knobs, setKnobs] = useState<DocKnobState>(() => {
    const init = {} as DocKnobState;
    for (const k of DOC_TUNE_KNOB_KEYS) init[k] = (saved[k] ?? null) as number | boolean | null;
    return init;
  });

  const setKnob = (key: DocKnobKey, value: number | boolean | null) =>
    setKnobs((prev) => ({ ...prev, [key]: value }));
  const resetAllToKb = () => {
    const cleared = {} as DocKnobState;
    for (const k of DOC_TUNE_KNOB_KEYS) cleared[k] = null;
    setKnobs(cleared);
    setAnswerDetail(null);
  };

  const dirty = useMemo(
    () =>
      (answerDetail ?? null) !== (saved.answer_detail ?? null) ||
      DOC_TUNE_KNOB_KEYS.some((k) => (knobs[k] ?? null) !== (saved[k] ?? null)),
    [answerDetail, knobs, saved],
  );

  const overriddenCount = useMemo(
    () =>
      (answerDetail !== null ? 1 : 0) + DOC_TUNE_KNOB_KEYS.filter((k) => knobs[k] !== null).length,
    [answerDetail, knobs],
  );

  function buildDocConfig(): DocConfig {
    return { answer_detail: answerDetail, ...(knobs as Partial<DocConfig>) };
  }

  // Draft config for the config-test preview — the post-retrieval knobs the user is
  // editing. DD-5 (2026-06-11): answer_detail is now part of DraftRetrievalConfig, so
  // the test preview reflects the synthesis detail level too (not just citation/image).
  function buildDraftConfig(): DraftRetrievalConfig {
    const draft: DraftRetrievalConfig = {};
    for (const k of DOC_TUNE_KNOB_KEYS) {
      const v = knobs[k];
      if (v !== null) (draft as Record<string, number | boolean>)[k] = v;
    }
    if (answerDetail !== null) draft.answer_detail = answerDetail;
    return draft;
  }

  const saveMutation = useMutation({
    mutationFn: () => docConfigApi.put(kbId, docId, buildDocConfig()),
    onSuccess: () => {
      onSaved();
      toast.success('Saved to this document');
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : 'Save failed'),
  });

  // W79 / ADR-0058 — 人手覆寫 profile mutation. override → 套對應 preset 落 per-doc config +
  // 記 manual_override. invalidate doc-detail (badge/select effective) + doc-config (preset 套落).
  const queryClient = useQueryClient();
  const overrideMutation = useMutation({
    mutationFn: (newProfile: string) => documentsApi.overrideProfile(kbId, docId, newProfile),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['kb', kbId, 'doc-detail', docId] });
      void queryClient.invalidateQueries({ queryKey: ['kb', kbId, 'doc-config', docId] });
      toast.success('Applied profile + matching preset (reload the page to see updated knobs)');
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : 'Profile override failed'),
  });

  // effective profile = manual_override ?? system auto (select 預設 + badge 顯示用).
  const effectiveProfile = profile ? (profile.manual_override ?? profile.profile) : null;

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* scope banner */}
      <div className="banner banner-info">
        <Settings size={15} style={{ color: 'oklch(var(--info))' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13 }}>
            <b>Per-document custom configuration</b> — Leave blank = Inherit from KB (
            <span className="mono">{kbName}</span>) then global.
            {overriddenCount > 0 && (
              <span className="badge badge-success" style={{ marginLeft: 6, fontSize: 9 }}>
                {overriddenCount} items overridden
              </span>
            )}
          </div>
          <div className="muted text-xs" style={{ marginTop: 2 }}>
            Resolution priority: per-query &gt; <b>per-DOC (this document)</b> &gt; per-KB &gt; global · ADR-0050 ·
            <span className="mono">
              {' '}
              PUT /kb/{kbId}/docs/{docId}/config
            </span>
          </div>
        </div>
      </div>

      {/* W77 / ADR-0056 段③ — 文件畫像(L3:自動偵測 profile + signals 透明展示 + 人手覆寫)
          per mockup ekp-page-doc-detail.jsx:453-505. profile=null → 唔 render(graceful)。 */}
      {profile && (
        <div className="card">
          <div className="card-header">
            <div>
              <h3 className="card-title">Document profile (auto-detected)</h3>
              <div className="card-desc">
                The system detects the content type from the document&apos;s structure signals and auto-applies the matching recall preset. Wrong detection → override with one click below.
                <span className="mono"> W72 profiler · ADR-0056 Layer A</span>
              </div>
            </div>
            <DocProfileBadge profile={profile} />
          </div>
          <div className="card-body" style={{ display: 'grid', gap: 14 }}>
            {(profile.fallback_applied || profile.confidence < 0.7) && (
              <div className="banner banner-warning">
                <Shield size={15} style={{ color: 'oklch(var(--warning))', flexShrink: 0 }} />
                <div className="text-xs" style={{ flex: 1, lineHeight: 1.5 }}>
                  <b>Low-confidence detection</b> (conflicting structure signals) — fell back to a conservative preset. Recommend manually confirming the profile below.
                </div>
              </div>
            )}
            <div>
              <div className="label" style={{ marginBottom: 8 }}>
                Detection signals (why this profile)
              </div>
              <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
                <ProfileSignal
                  label="Image density (img_density)"
                  value={profile.signals.img_density.toFixed(3)}
                />
                <ProfileSignal
                  label="List ratio (list_ratio)"
                  value={profile.signals.list_ratio.toFixed(3)}
                />
                <ProfileSignal label="Heading depth (max_depth)" value={profile.signals.max_depth} />
                <ProfileSignal label="Heading count (headings)" value={profile.signals.headings} />
                {profile.signals.pdf_pages != null && (
                  <>
                    <ProfileSignal label="PDF pages" value={profile.signals.pdf_pages} />
                    <ProfileSignal
                      label="Empty text-layer ratio"
                      value={(profile.signals.pdf_empty_ratio ?? 0).toFixed(2)}
                    />
                    <ProfileSignal
                      label="Avg chars/page"
                      value={Math.round(profile.signals.pdf_avg_chars ?? 0)}
                    />
                  </>
                )}
                <ProfileSignal label="Paragraph count (paragraphs)" value={profile.signals.paragraphs} />
              </div>
            </div>
            <div className="field" style={{ marginBottom: 0 }}>
              <label className="label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                Manual profile override (override)
                {profile.manual_override != null && (
                  <span className="badge badge-success" style={{ fontSize: 9 }}>
                    Overridden · originally classified as {DOC_PROFILE_LABELS[profile.profile] ?? profile.profile}
                  </span>
                )}
              </label>
              <select
                className="select"
                value={effectiveProfile ?? profile.profile}
                disabled={overrideMutation.isPending}
                onChange={(e) => overrideMutation.mutate(e.target.value)}
                style={{ maxWidth: 260 }}
              >
                <option value="P1_sop_imgdense">P1 Image-dense SOP</option>
                <option value="P1_sop_text">P1 Text SOP</option>
                <option value="P2_prose">P2 Prose</option>
                <option value="P3_slide_imgdense">P3 Image-dense slides</option>
                <option value="P3_slide_text">P3 Text slides</option>
                <option value="P4_scan_imgdense">P4 Scan</option>
                <option value="P5_form">P5 Form</option>
              </select>
              <div className="hint">
                Changing the profile immediately applies the matching preset to the knobs below (overrides the per-doc config). Admin override always takes priority over auto-detection
                (ADR-0056 D6).{overrideMutation.isPending && ' Applying…'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Per-doc advanced tuning — post-retrieval knobs only */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Per-document configuration</h3>
            <div className="card-desc">
              Override this document&apos;s <b>synthesis + citation post-processing</b> behavior. Knobs not overridden use the KB defaults. All runtime —{' '}
              <b>no re-indexing needed</b>.
            </div>
          </div>
          <span className="badge badge-info" style={{ fontSize: 9.5 }}>
            <Edit size={10} /> Runtime · no re-index
          </span>
        </div>
        <div className="card-body" style={{ display: 'grid', gap: 12 }}>
          {/* answer_detail — synthesis (dominant doc) */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              Answer detail (answer_detail)
              {answerDetail === null ? (
                <span className="badge badge-muted" style={{ fontSize: 9, fontWeight: 500 }}>
                  Inherit from KB
                </span>
              ) : (
                <span className="badge badge-success" style={{ fontSize: 9 }}>
                  <Edit size={9} /> Overridden
                </span>
              )}
            </label>
            <div className="seg" style={{ width: '100%', maxWidth: 380 }}>
              {(
                [
                  { v: null, l: 'Inherit from KB' },
                  { v: 'concise', l: 'concise' },
                  { v: 'detailed', l: 'detailed' },
                ] as { v: AnswerDetail; l: string }[]
              ).map((o) => (
                <button
                  type="button"
                  key={o.l}
                  className="seg-btn"
                  data-active={answerDetail === o.v}
                  style={{ flex: 1, padding: '5px 8px', fontSize: 11.5 }}
                  onClick={() => setAnswerDetail(o.v)}
                >
                  {o.l}
                </button>
              ))}
            </div>
            <div className="hint">
              Synthesis detail level. Procedure-manual documents can be set to{' '}
              <span className="mono">detailed</span> (lists every step); Inherit = use the KB setting.
            </div>
          </div>

          <DocTuneGroup
            icon={LinkIcon}
            title="Citation post-hoc expansion"
            desc="After the answer is generated, supplement each citation with neighbouring auxiliary chunks to improve completeness."
            enabled={knobs.enable_citation_post_hoc_expansion as boolean | null}
            onToggle={(v) => setKnob('enable_citation_post_hoc_expansion', v)}
            onReset={() => setKnob('enable_citation_post_hoc_expansion', null)}
          >
            <DocTuneKnob
              label="Max aux / citation"
              value={knobs.citation_expansion_max_aux as number | null}
              onChange={(v) => setKnob('citation_expansion_max_aux', v)}
            />
            <DocTuneKnob
              label="Expansion window"
              value={knobs.citation_expansion_window as number | null}
              onChange={(v) => setKnob('citation_expansion_window', v)}
            />
            <DocTuneKnob
              label="Section path prefix depth"
              value={knobs.citation_expansion_section_path_prefix_depth as number | null}
              onChange={(v) => setKnob('citation_expansion_section_path_prefix_depth', v)}
            />
          </DocTuneGroup>

          <DocTuneGroup
            icon={Eye}
            title="Citation neighbour images + image cap"
            desc="Controls bringing in citation-neighbour images and the max images shown per answer (image-flood convergence)."
            enabled={knobs.enable_citation_neighbour_images as boolean | null}
            onToggle={(v) => setKnob('enable_citation_neighbour_images', v)}
            onReset={() => setKnob('enable_citation_neighbour_images', null)}
          >
            <DocTuneKnob
              label="Neighbour max aux images"
              value={knobs.citation_neighbour_max_aux_images as number | null}
              onChange={(v) => setKnob('citation_neighbour_max_aux_images', v)}
            />
            <DocTuneKnob
              label="Neighbour prefix depth"
              value={knobs.citation_neighbour_section_path_prefix_depth as number | null}
              onChange={(v) => setKnob('citation_neighbour_section_path_prefix_depth', v)}
            />
            <DocTuneKnob
              label="Max images / answer"
              value={knobs.max_images_per_answer as number | null}
              onChange={(v) => setKnob('max_images_per_answer', v)}
            />
            <DocSwitchKnob
              label="Chapter overview image on top (overview pin)"
              value={knobs.enable_chapter_overview_pin as boolean | null}
              onChange={(v) => setKnob('enable_chapter_overview_pin', v)}
            />
          </DocTuneGroup>

          {/* W81 / ADR-0060 — image-anchor knobs (design-stage expansion, 方案 A:
              既有 DocTuneGroup/DocSwitchKnob/DocTuneKnob 復用, 視覺零發明). inline marker
              做主 toggle (section 錨定靠 marker 機制注入 → 主/進階關係); backend 零改動. */}
          <DocTuneGroup
            icon={Tag}
            title="Inline image anchoring (image markers + section anchoring)"
            desc="Answer text carries [IMG#…] markers at the original image positions, so text and images interleave in the source order. Advanced: section anchoring injects trailing un-anchored images into the same section, and can cap images per anchor (converges intra-section clumps)."
            enabled={knobs.enable_inline_image_markers as boolean | null}
            onToggle={(v) => setKnob('enable_inline_image_markers', v)}
            onReset={() => setKnob('enable_inline_image_markers', null)}
          >
            <DocSwitchKnob
              label="section-anchored aux images (trailing pile → into section)"
              value={knobs.enable_section_anchored_aux_images as boolean | null}
              onChange={(v) => setKnob('enable_section_anchored_aux_images', v)}
            />
            <DocSwitchKnob
              label="Anchor to nearest step (nearest; else section end)"
              value={knobs.section_anchor_nearest as boolean | null}
              onChange={(v) => setKnob('section_anchor_nearest', v)}
            />
            <DocTuneKnob
              label="Max images per anchor (0 = no cap)"
              value={knobs.section_anchor_max_per_anchor as number | null}
              onChange={(v) => setKnob('section_anchor_max_per_anchor', v)}
            />
          </DocTuneGroup>
        </div>
        <div className="card-footer">
          <div className="muted text-xs">
            Config scope: per-query &gt; <b>per-DOC (this document)</b> &gt; per-KB &gt; global · ADR-0050
          </div>
          <div className="row">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={resetAllToKb}
              disabled={overriddenCount === 0}
            >
              <RefreshCw size={13} /> Reset all to KB
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => saveMutation.mutate()}
              disabled={!dirty || saveMutation.isPending}
            >
              {saveMutation.isPending ? <span className="spinner" /> : null} Save to this document
            </button>
          </div>
        </div>
      </div>

      {/* retrieval-entry knobs — KB-level only explainer (per ADR-0050) */}
      <div className="card">
        <div
          className="card-body"
          style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: 14 }}
        >
          <Shield
            size={15}
            style={{ color: 'oklch(var(--warning))', flexShrink: 0, marginTop: 2 }}
          />
          <div className="text-xs" style={{ lineHeight: 1.6, flex: 1 }}>
            <b>Retrieval-entry knobs</b> (default_top_k / default_rerank_k / parent-document retrieval)
            <b>are set at the KB level</b> and can&apos;t be overridden per-document —— these knobs drive retrieval
            <b>before</b>
            it&apos;s determined which document gets cited (ADR-0050).
          </div>
        </div>
      </div>

      {/* per-doc config-test (scoped to this doc) */}
      <DocConfigTestPanel
        kbId={kbId}
        docId={docId}
        draftConfig={buildDraftConfig()}
        onSaveDraft={() => saveMutation.mutate()}
        saving={saveMutation.isPending}
        dirty={dirty}
      />
    </div>
  );
}

// One number knob. null = inherit KB (empty input + 繼承 KB placeholder); a value =
// per-doc override (badge + ↺ 還原至 KB).
function DocTuneKnob({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
}) {
  const overridden = value !== null;
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {label}
        {overridden ? (
          <span className="badge badge-success" style={{ fontSize: 9 }}>
            <Edit size={9} /> Overridden
          </span>
        ) : (
          <span className="badge badge-muted" style={{ fontSize: 9 }}>
            Inherit from KB
          </span>
        )}
      </label>
      <input
        type="number"
        className="input mono"
        value={value ?? ''}
        placeholder="Inherit from KB"
        onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
      />
      <div className="hint" style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
        <span>{overridden ? "This document's override value" : 'Not overridden · uses KB'}</span>
        {overridden && (
          <button
            type="button"
            onClick={() => onChange(null)}
            style={{
              display: 'inline-flex',
              gap: 3,
              alignItems: 'center',
              color: 'oklch(var(--muted-foreground))',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              font: 'inherit',
            }}
          >
            <RefreshCw size={10} /> Reset to KB
          </button>
        )}
      </div>
    </div>
  );
}

// A boolean toggle cell (overview pin) — null = inherit KB, true/false = per-doc.
function DocSwitchKnob({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean | null;
  onChange: (v: boolean | null) => void;
}) {
  const overridden = value !== null;
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {label}
        {overridden ? (
          <span className="badge badge-success" style={{ fontSize: 9 }}>
            <Edit size={9} /> Overridden
          </span>
        ) : (
          <span className="badge badge-muted" style={{ fontSize: 9 }}>
            Inherit from KB
          </span>
        )}
      </label>
      <div className="row" style={{ gap: 8, alignItems: 'center', paddingTop: 4 }}>
        <span
          className="switch"
          data-on={value === true}
          role="switch"
          aria-checked={value === true}
          tabIndex={0}
          onClick={() => onChange(value === true ? false : true)}
        />
        <span className="muted text-xs">{overridden ? (value ? 'On' : 'Off') : 'Inherit'}</span>
      </div>
      <div className="hint" style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
        <span>{overridden ? "This document's override value" : 'Not overridden · uses KB'}</span>
        {overridden && (
          <button
            type="button"
            onClick={() => onChange(null)}
            style={{
              display: 'inline-flex',
              gap: 3,
              alignItems: 'center',
              color: 'oklch(var(--muted-foreground))',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              font: 'inherit',
            }}
          >
            <RefreshCw size={10} /> Reset to KB
          </button>
        )}
      </div>
    </div>
  );
}

// A toggle-led group: enable_* switch + title/desc + 繼承/覆寫 badge + collapsible
// 進階 numeric grid. Mirrors the KB KbTuneGroup (DESIGN_SYSTEM §4.3 OptionRow).
function DocTuneGroup({
  icon: Ic,
  title,
  desc,
  enabled,
  onToggle,
  onReset,
  children,
}: {
  icon: LucideIcon;
  title: string;
  desc: string;
  enabled: boolean | null;
  onToggle: (v: boolean) => void;
  onReset: () => void;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const overridden = enabled !== null;
  return (
    <div
      style={{
        border: '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: 12,
          padding: '12px 14px',
          alignItems: 'flex-start',
          background: enabled === true ? 'oklch(var(--muted) / 0.4)' : 'transparent',
        }}
      >
        <span
          className="switch"
          data-on={enabled === true}
          role="switch"
          aria-checked={enabled === true}
          tabIndex={0}
          onClick={() => onToggle(!(enabled === true))}
          style={{ flexShrink: 0, marginTop: 2 }}
        />
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <Ic size={13} style={{ color: 'oklch(var(--muted-foreground))' }} />
            <span style={{ fontSize: 13, fontWeight: 500 }}>{title}</span>
            {overridden ? (
              <span className="badge badge-success" style={{ fontSize: 9 }}>
                Overridden
              </span>
            ) : (
              <span className="badge badge-muted" style={{ fontSize: 9 }}>
                Inherit from KB
              </span>
            )}
            {overridden && (
              <button
                type="button"
                onClick={onReset}
                style={{
                  display: 'inline-flex',
                  gap: 3,
                  alignItems: 'center',
                  fontSize: 11,
                  color: 'oklch(var(--muted-foreground))',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                <RefreshCw size={10} /> Reset to KB
              </button>
            )}
          </div>
          <div className="muted text-xs" style={{ marginTop: 3, lineHeight: 1.5 }}>
            {desc}
          </div>
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          style={{ flexShrink: 0 }}
          onClick={() => setOpen(!open)}
          aria-expanded={open}
        >
          Advanced <ChevronRight size={11} style={{ transform: open ? 'rotate(90deg)' : 'none' }} />
        </button>
      </div>
      {open && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr 1fr',
            gap: 14,
            padding: 14,
            borderTop: '1px solid oklch(var(--border))',
          }}
        >
          {children}
        </div>
      )}
    </div>
  );
}

// Per-doc config-test panel — runs the full pipeline N times with the current
// (unsaved) draft knobs, A/B vs the KB baseline (compare_to_saved). Sends the draft
// knobs as `draft_config` (NOT doc_id) so the A/B is proposed-doc vs KB-only.
function DocConfigTestPanel({
  kbId,
  docId,
  draftConfig,
  onSaveDraft,
  saving,
  dirty,
}: {
  kbId: string;
  docId: string;
  draftConfig: DraftRetrievalConfig;
  onSaveDraft: () => void;
  saving: boolean;
  dirty: boolean;
}) {
  const [testQuery, setTestQuery] = useState(
    'How do I process and confirm journal voucher transactions?',
  );
  const [runs, setRuns] = useState(3);
  const [compare, setCompare] = useState(true);

  const mutation = useMutation<ConfigTestResult>({
    mutationFn: () =>
      configTestApi.run(kbId, {
        query: testQuery,
        runs,
        draft_config: draftConfig,
        compare_to_saved: compare,
      }),
    onError: (e) => toast.error(e instanceof Error ? e.message : 'config-test failed'),
  });
  const result = mutation.data;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h3 className="card-title">
            <Zap
              size={14}
              style={{ verticalAlign: '-2px', marginRight: 6, color: 'oklch(var(--accent))' }}
            />
            Test run (this document scope)
          </h3>
          <div className="card-desc">
            Test run with this document&apos;s config on the real pipeline (dominant doc = this document).{' '}
            <span className="mono">
              POST /kb/{kbId}/config-test · doc={docId}
            </span>
          </div>
        </div>
      </div>
      <div className="card-body">
        <div
          style={{
            display: 'flex',
            gap: 12,
            alignItems: 'flex-end',
            flexWrap: 'wrap',
            marginBottom: 16,
          }}
        >
          <div className="field" style={{ flex: 1, minWidth: 240, marginBottom: 0 }}>
            <label className="label">Test query</label>
            <input
              className="input"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  if (testQuery.trim() && !mutation.isPending) mutation.mutate();
                }
              }}
            />
          </div>
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Number of runs</label>
            <div className="seg">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  type="button"
                  key={n}
                  className="seg-btn"
                  data-active={n === runs}
                  style={{ minWidth: 34 }}
                  onClick={() => setRuns(n)}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
          <label
            className="row"
            style={{
              gap: 6,
              fontSize: 12.5,
              alignItems: 'center',
              cursor: 'pointer',
              paddingBottom: 8,
            }}
          >
            <span
              className="switch"
              data-on={compare}
              role="switch"
              aria-checked={compare}
              tabIndex={0}
              onClick={() => setCompare(!compare)}
            />
            Compare against inherited KB (A/B)
          </label>
          <button
            type="button"
            className="btn btn-primary"
            disabled={mutation.isPending || !testQuery.trim()}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? (
              <>
                <span className="spinner" /> Running…
              </>
            ) : (
              <>
                <Zap size={14} /> Test run
              </>
            )}
          </button>
        </div>

        {!result && !mutation.isPending && (
          <div className="empty">
            <div className="empty-icon">
              <Zap size={20} />
            </div>
            <div className="empty-title">No test run yet</div>
            <div>Adjust the knobs above → pick the number of runs → click &quot;Test run&quot;.</div>
          </div>
        )}

        {result && (
          <>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: result.saved ? '1fr 1fr' : '1fr',
                gap: 14,
              }}
            >
              <DocConfigResultCard label="This document's config (DRAFT)" accent summary={result.draft} />
              {result.saved && (
                <DocConfigResultCard label="Inherit from KB (SAVED)" summary={result.saved} />
              )}
            </div>

            <div
              className="hint"
              style={{ marginTop: 10, display: 'flex', gap: 6, alignItems: 'flex-start' }}
            >
              <AlertTriangle
                size={13}
                style={{ color: 'oklch(var(--warning))', marginTop: 1, flexShrink: 0 }}
              />
              <span>
                For long / comprehensive answers, faithfulness has a{' '}
                <b style={{ color: 'oklch(var(--warning))' }}>length bias</b> —— a low score paired with high{' '}
                <b>Sections covered</b> / word count is usually bias, not a config difference; read them together.
              </span>
            </div>
          </>
        )}
      </div>
      <div className="card-footer">
        <div className="muted text-xs">
          Average over N runs · band = max − min · answer_detail included in the test-run draft
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onSaveDraft}
          disabled={!dirty || saving}
        >
          <Download size={13} /> Save draft to this document
        </button>
      </div>
    </div>
  );
}

// A/B result column for the per-doc test-run panel (mirror of the KB ConfigResultCard).
function DocConfigResultCard({
  label,
  accent,
  summary,
}: {
  label: string;
  accent?: boolean;
  summary: ConfigRunSummary;
}) {
  const last = summary.runs[summary.runs.length - 1];
  const fmt = (b: { mean: number }) =>
    Number.isInteger(b.mean) ? String(b.mean) : b.mean.toFixed(1);
  return (
    <div
      style={{
        border: accent ? '1px solid oklch(var(--accent) / 0.4)' : '1px solid oklch(var(--border))',
        borderRadius: 'var(--radius-sm)',
        background: accent ? 'oklch(var(--accent) / 0.04)' : 'transparent',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '10px 14px',
          borderBottom: '1px solid oklch(var(--border))',
          fontSize: 12,
          fontWeight: 600,
        }}
      >
        {label}
      </div>
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 1,
          background: 'oklch(var(--border))',
        }}
      >
        <div
          style={{ gridColumn: '1 / -1', background: 'oklch(var(--card))', padding: '10px 14px' }}
        >
          <div className="muted text-xs">Faithfulness (faithfulness · anti-hallucination · 0–1)</div>
          <div
            className="mono"
            style={{
              fontSize: 18,
              fontWeight: 700,
              marginTop: 2,
              color:
                summary.faithfulness != null
                  ? 'oklch(var(--success))'
                  : 'oklch(var(--muted-foreground))',
            }}
          >
            {summary.faithfulness != null ? summary.faithfulness.mean.toFixed(2) : '—'}
            {summary.faithfulness != null && summary.runs.length >= 2 && (
              <span className="muted text-xs" style={{ fontWeight: 400, marginLeft: 6 }}>
                ±{summary.faithfulness.band.toFixed(2)}
              </span>
            )}
            {summary.faithfulness == null && (
              <span className="muted text-xs" style={{ fontWeight: 400, marginLeft: 6 }}>
                Not evaluated (no judge / disabled)
              </span>
            )}
          </div>
          {summary.faithfulness != null && summary.runs.length === 1 && (
            <div className="text-xs" style={{ marginTop: 3, color: 'oklch(var(--warning))' }}>
              Single judge run · directional · raise runs to ≥2 to see the stability band
            </div>
          )}
        </div>
        <DocConfigMetric
          k="Citations"
          v={fmt(summary.citation_count)}
          band={summary.citation_count.band}
        />
        <DocConfigMetric
          k="Sections covered"
          v={fmt(summary.distinct_sections)}
          sub="completeness proxy · not recall"
          band={summary.distinct_sections.band}
        />
        <DocConfigMetric
          k="Images (dedup)"
          v={fmt(summary.figure_count_dedup)}
          sub={`raw ${fmt(summary.figure_count_raw)}`}
          band={summary.figure_count_dedup.band}
        />
        {/* W65 — image-axis coverage proxy (mirror of 涵蓋章節數; wide text + narrow image = b-1 risk) */}
        <DocConfigMetric
          k="Image sections"
          v={fmt(summary.image_section_count)}
          sub="sections-with-images coverage · proxy not recall"
          band={summary.image_section_count.band}
        />
        <DocConfigMetric k="Latency p50" v={`${(summary.latency_ms.mean / 1000).toFixed(1)}s`} />
        <DocConfigMetric k="Answer chars" v={String(last?.answer_chars ?? 0)} />
        <DocConfigMetric k="Refused?" v={last?.refused ? 'Yes' : 'No'} />
      </div>
    </div>
  );
}

function DocConfigMetric({
  k,
  v,
  sub,
  band,
}: {
  k: string;
  v: string;
  sub?: string;
  band?: number;
}) {
  return (
    <div style={{ background: 'oklch(var(--card))', padding: '10px 14px' }}>
      <div className="muted text-xs">{k}</div>
      <div className="mono" style={{ fontSize: 16, fontWeight: 600, marginTop: 2 }}>
        {v}
        {band != null && (
          <span className="muted text-xs" style={{ fontWeight: 400, marginLeft: 4 }}>
            ±{band}
          </span>
        )}
      </div>
      {sub && (
        <div className="muted mono text-xs" style={{ marginTop: 1 }}>
          {sub}
        </div>
      )}
    </div>
  );
}

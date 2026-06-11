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
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { useMemo, useState, type ReactNode } from 'react';
import { toast } from 'sonner';

import { docConfigApi, type DocConfig } from '@/lib/api/doc-config';
import {
  configTestApi,
  type ConfigRunSummary,
  type ConfigTestResult,
  type DraftRetrievalConfig,
} from '@/lib/api/config-test';

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
] as const;

type DocKnobKey = (typeof DOC_TUNE_KNOB_KEYS)[number];
type DocKnobState = Record<DocKnobKey, number | boolean | null>;
type AnswerDetail = 'concise' | 'detailed' | null;

export function DocConfigTab({
  kbId,
  docId,
  kbName,
}: {
  kbId: string;
  docId: string;
  kbName: string;
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
  saved,
  onSaved,
}: {
  kbId: string;
  docId: string;
  kbName: string;
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
      toast.success('已儲存到此文件');
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : '儲存失敗'),
  });

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* scope banner */}
      <div className="banner banner-info">
        <Settings size={15} style={{ color: 'oklch(var(--info))' }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13 }}>
            <b>此文件度身訂做配置</b> — 留空 = 繼承 KB(
            <span className="mono">{kbName}</span>)再全域。
            {overriddenCount > 0 && (
              <span className="badge badge-success" style={{ marginLeft: 6, fontSize: 9 }}>
                {overriddenCount} 項已覆寫
              </span>
            )}
          </div>
          <div className="muted text-xs" style={{ marginTop: 2 }}>
            解析優先:per-query &gt; <b>per-DOC(此文件)</b> &gt; per-KB &gt; 全域 · ADR-0050 ·
            <span className="mono">
              {' '}
              PUT /kb/{kbId}/docs/{docId}/config
            </span>
          </div>
        </div>
      </div>

      {/* Per-doc advanced tuning — post-retrieval knobs only */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Per-document 配置</h3>
            <div className="card-desc">
              覆寫此文件嘅<b>合成 + 引用後處理</b>行為。未覆寫嘅旋鈕沿用 KB 預設。 全部 runtime —{' '}
              <b>唔需要重新索引</b>。
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
              答案詳細度(answer_detail)
              {answerDetail === null ? (
                <span className="badge badge-muted" style={{ fontSize: 9, fontWeight: 500 }}>
                  繼承 KB
                </span>
              ) : (
                <span className="badge badge-success" style={{ fontSize: 9 }}>
                  <Edit size={9} /> 已覆寫
                </span>
              )}
            </label>
            <div className="seg" style={{ width: '100%', maxWidth: 380 }}>
              {(
                [
                  { v: null, l: '繼承 KB' },
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
              合成詳細度。程序手冊文件可設 <span className="mono">detailed</span>(逐步列盡); 繼承 =
              用 KB 設定。
            </div>
          </div>

          <DocTuneGroup
            icon={LinkIcon}
            title="Citation post-hoc expansion"
            desc="答案生成後,為每個引用補充鄰近輔助 chunk,提升完整性。"
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
            title="Citation neighbour images + 圖片上限"
            desc="控制引用鄰近圖片帶入,同每個答案最多顯示幾多張圖(圖洪水收斂)。"
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
              label="章節概覽圖置頂(overview pin)"
              value={knobs.enable_chapter_overview_pin as boolean | null}
              onChange={(v) => setKnob('enable_chapter_overview_pin', v)}
            />
          </DocTuneGroup>
        </div>
        <div className="card-footer">
          <div className="muted text-xs">
            配置 scope:per-query &gt; <b>per-DOC(此文件)</b> &gt; per-KB &gt; 全域 · ADR-0050
          </div>
          <div className="row">
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={resetAllToKb}
              disabled={overriddenCount === 0}
            >
              <RefreshCw size={13} /> 還原全部至 KB
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={() => saveMutation.mutate()}
              disabled={!dirty || saveMutation.isPending}
            >
              {saveMutation.isPending ? <span className="spinner" /> : null} 儲存到此文件
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
            <b>檢索入口旋鈕</b>(default_top_k / default_rerank_k / parent-document retrieval)
            <b>喺 KB 設定</b>,唔可以 per-document 覆寫 —— 呢類旋鈕喺「邊個文件被引用」確定
            <b>之前</b>
            已驅動檢索(ADR-0050)。
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
            <Edit size={9} /> 已覆寫
          </span>
        ) : (
          <span className="badge badge-muted" style={{ fontSize: 9 }}>
            繼承 KB
          </span>
        )}
      </label>
      <input
        type="number"
        className="input mono"
        value={value ?? ''}
        placeholder="繼承 KB"
        onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
      />
      <div className="hint" style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
        <span>{overridden ? '此文件覆寫值' : '未覆寫 · 沿用 KB'}</span>
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
            <RefreshCw size={10} /> 還原至 KB
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
            <Edit size={9} /> 已覆寫
          </span>
        ) : (
          <span className="badge badge-muted" style={{ fontSize: 9 }}>
            繼承 KB
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
        <span className="muted text-xs">{overridden ? (value ? '開' : '關') : '繼承'}</span>
      </div>
      <div className="hint" style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
        <span>{overridden ? '此文件覆寫值' : '未覆寫 · 沿用 KB'}</span>
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
            <RefreshCw size={10} /> 還原至 KB
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
                已覆寫
              </span>
            ) : (
              <span className="badge badge-muted" style={{ fontSize: 9 }}>
                繼承 KB
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
                <RefreshCw size={10} /> 還原至 KB
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
          進階 <ChevronRight size={11} style={{ transform: open ? 'rotate(90deg)' : 'none' }} />
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
            試跑(此文件 scope)
          </h3>
          <div className="card-desc">
            用此文件嘅配置喺真 pipeline 試跑(主導 doc = 此文件)。{' '}
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
            <label className="label">測試問題</label>
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
            <label className="label">重跑次數</label>
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
            同繼承 KB 對照(A/B)
          </label>
          <button
            type="button"
            className="btn btn-primary"
            disabled={mutation.isPending || !testQuery.trim()}
            onClick={() => mutation.mutate()}
          >
            {mutation.isPending ? (
              <>
                <span className="spinner" /> 試跑中…
              </>
            ) : (
              <>
                <Zap size={14} /> 試跑
              </>
            )}
          </button>
        </div>

        {!result && !mutation.isPending && (
          <div className="empty">
            <div className="empty-icon">
              <Zap size={20} />
            </div>
            <div className="empty-title">未有試跑結果</div>
            <div>調整上面旋鈕 → 揀重跑次數 → 撳「試跑」。</div>
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
              <DocConfigResultCard label="此文件配置(DRAFT)" accent summary={result.draft} />
              {result.saved && (
                <DocConfigResultCard label="繼承 KB(SAVED)" summary={result.saved} />
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
                忠實度對長 / 全面答案有{' '}
                <b style={{ color: 'oklch(var(--warning))' }}>length bias</b> —— 低分若配合高{' '}
                <b>涵蓋章節數</b> / 字數,多為 bias 而非 config 差,宜一齊判讀。
              </span>
            </div>
          </>
        )}
      </div>
      <div className="card-footer">
        <div className="muted text-xs">
          N 次重跑取平均 · band = max − min · answer_detail 已納入試跑草稿
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onSaveDraft}
          disabled={!dirty || saving}
        >
          <Download size={13} /> 把草稿儲存到此文件
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
          <div className="muted text-xs">忠實度(faithfulness · 反幻覺 · 0–1)</div>
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
                未評(無 judge / 已關)
              </span>
            )}
          </div>
          {summary.faithfulness != null && summary.runs.length === 1 && (
            <div className="text-xs" style={{ marginTop: 3, color: 'oklch(var(--warning))' }}>
              單次 judge · 方向性 · 重跑次數調高至 ≥2 先見穩定度 band
            </div>
          )}
        </div>
        <DocConfigMetric
          k="引用數"
          v={fmt(summary.citation_count)}
          band={summary.citation_count.band}
        />
        <DocConfigMetric
          k="涵蓋章節數"
          v={fmt(summary.distinct_sections)}
          sub="completeness proxy · 非 recall"
          band={summary.distinct_sections.band}
        />
        <DocConfigMetric
          k="圖片(dedup)"
          v={fmt(summary.figure_count_dedup)}
          sub={`raw ${fmt(summary.figure_count_raw)}`}
          band={summary.figure_count_dedup.band}
        />
        <DocConfigMetric k="延遲 p50" v={`${(summary.latency_ms.mean / 1000).toFixed(1)}s`} />
        <DocConfigMetric k="答案字數" v={String(last?.answer_chars ?? 0)} />
        <DocConfigMetric k="是否拒答" v={last?.refused ? '是' : '否'} />
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

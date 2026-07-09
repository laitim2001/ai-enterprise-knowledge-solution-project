'use client';

/**
 * Settings → 文件分類規則 tab — W78 / ADR-0056 層 A 段③ frontend; W82 / ADR-0063 write surface.
 *
 * 100% mockup fidelity match against references/design-mockups/ekp-page-settings-tabs.jsx
 * `SettingsDocProfiling` + `ThresholdRow` (per CLAUDE.md §5.7 H7) for the read layer.
 * admin 自行調試指揮中心: profile→preset 映射 (now editable) + 偵測 threshold (read-only).
 *
 * W82 / ADR-0063 — the「Profile → preset 映射」card is now WRITE-enabled (缺口 B):
 *   - table rows render the EFFECTIVE mapping from `GET /profile-presets`
 *     (admin override overlaid on the factory preset; 已覆寫 badge when overridden).
 *   - 「編輯」opens an edit Dialog (reuses the existing `dialog.tsx` primitive +
 *     `.field` / `.input` / `.switch` / `.seg` mockup primitives — 視覺零發明, the one
 *     deliberate design-stage expansion the mockup has no edit-form for, approved as
 *     方案 A in ADR-0063). The Dialog + its warning banner + explicit「儲存規則」is the
 *     「儲存確認」guard for a GLOBAL, future-only mapping change.
 *   - 「還原預設」(when overridden) drops the override → restores the factory value
 *     (reversible undo, mirrors L3「還原至 KB」— no extra confirm).
 *
 * 偵測 threshold card stays READ-ONLY / disabled — threshold persist is deliberately
 * NOT in scope (W79 / ADR-0058: 五輪實證已最佳, 改門檻 risk>reward).
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Layers } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import type { DocConfig } from '@/lib/api/doc-config';
import { type PresetMappingItem, profilePresetsApi } from '@/lib/api/profile-presets';

// profile label key → 中文縮短顯示名 (mirror mockup ekp-page-settings-tabs.jsx; 顯示層, 非 config data).
const PROFILE_LABELS: Record<string, string> = {
  P1_sop_imgdense: 'P1 Image-dense SOP',
  P1_sop_text: 'P1 Text SOP',
  P2_prose: 'P2 Prose',
  P3_slide_imgdense: 'P3 Image-dense slides',
  P3_slide_text: 'P3 Text slides',
  P4_scan_imgdense: 'P4 Scan',
  P5_form: 'P5 Form',
};

const PRESETS_QUERY_KEY = ['profile-presets'] as const;

// --- effective-config → table cell formatters (mirror mockup display strings) ---
const fmtNeighbour = (c: DocConfig): string =>
  c.enable_citation_neighbour_images
    ? `On · ${c.citation_neighbour_max_aux_images ?? '—'}`
    : 'Off';
const fmtAnchor = (c: DocConfig): string =>
  c.enable_section_anchored_aux_images
    ? `section · ${c.section_anchor_nearest ? 'nearest' : 'end'} · cap ${c.section_anchor_max_per_anchor ?? 0}`
    : '—';

export function SettingsDocProfiling() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: PRESETS_QUERY_KEY,
    queryFn: () => profilePresetsApi.list(),
  });
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<PresetMappingItem | null>(null);

  // 還原預設 — drop the override, restore the factory value (reversible).
  const resetMutation = useMutation({
    mutationFn: (profile: string) => profilePresetsApi.delete(profile),
    onSuccess: () => {
      toast.success('Reset to factory default');
      void queryClient.invalidateQueries({ queryKey: PRESETS_QUERY_KEY });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : 'Reset failed'),
  });

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="banner banner-info">
        <Layers size={15} style={{ color: 'oklch(var(--info))', flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13 }}>
            <b>Document classification rules</b> —
            the system uses a rule-based profiler (W72) at ingest to detect the document profile and
            automatically apply the matching recall preset.
          </div>
          <div className="text-xs muted" style={{ marginTop: 2 }}>
            Command center for automatic rules: tune the profile→preset mapping + detection threshold · ADR-0056 layer A · LLM fallback safeguard
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Profile → preset mapping</h3>
            <div className="card-desc">
              Which recall/render preset each detected profile applies. Changes here affect all newly ingested documents (existing documents need re-index).
            </div>
          </div>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {isLoading ? (
            <div className="text-xs muted" style={{ padding: 16 }}>
              Loading mappings…
            </div>
          ) : isError ? (
            <div className="banner banner-destructive" style={{ margin: 16 }}>
              Load failed: <span className="mono">{error instanceof Error ? error.message : 'Unknown error'}</span>
            </div>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Profile</th>
                    <th className="col-num">Image cap</th>
                    <th>Neighbour images</th>
                    <th>inline marker</th>
                    <th>Section anchoring</th>
                    <th>Detail level</th>
                    <th className="col-shrink" />
                  </tr>
                </thead>
                <tbody>
                  {(data ?? []).map((item) => {
                    const c = item.config;
                    return (
                      <tr key={item.profile}>
                        <td>
                          <span className="badge badge-muted">
                            <span className="badge-dot" /> {PROFILE_LABELS[item.profile] ?? item.profile}
                          </span>
                          <div className="text-xs muted mono">
                            {item.profile}
                            {item.overridden ? (
                              <span className="badge badge-warning" style={{ marginLeft: 6, fontSize: 9 }}>
                                Overridden
                              </span>
                            ) : null}
                          </div>
                        </td>
                        <td className="col-num mono">{c.max_images_per_answer ?? '—'}</td>
                        <td className="text-xs">{fmtNeighbour(c)}</td>
                        <td className="text-xs">{c.enable_inline_image_markers ? 'On' : 'Off'}</td>
                        <td className="text-xs">{fmtAnchor(c)}</td>
                        <td>
                          <span className="badge badge-muted">{c.answer_detail ?? '—'}</span>
                        </td>
                        <td className="col-shrink">
                          <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                            {item.overridden ? (
                              <button
                                type="button"
                                className="btn btn-ghost btn-xs"
                                onClick={() => resetMutation.mutate(item.profile)}
                                disabled={resetMutation.isPending}
                                title="Reset to factory default (remove override)"
                              >
                                Reset to default
                              </button>
                            ) : null}
                            <button
                              type="button"
                              className="btn btn-ghost btn-xs"
                              onClick={() => setEditing(item)}
                            >
                              Edit
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Detection threshold</h3>
            <div className="card-desc">
              Tune the profiler classification thresholds. Below the confidence threshold → fallback to a conservative preset + flag as &quot;pending manual review&quot;.
            </div>
          </div>
        </div>
        <div className="card-body" style={{ display: 'grid', gap: 12 }}>
          <ThresholdRow
            label="Low-confidence threshold (confidence)"
            value="0.70"
            hint="Below this → yellow flag + fallback conservative preset"
          />
          <ThresholdRow
            label="P1 image-dense threshold (img_density)"
            value="0.15"
            hint="≥ this + depth≥3 + list_ratio≥0.3 → P1 Image-dense SOP"
          />
          <ThresholdRow
            label="too_small paragraph threshold"
            value="20"
            hint="Fewer paragraphs than this → too_small (not routed, inherits parent)"
          />
        </div>
        <div className="card-footer">
          <div className="text-xs muted">Changing thresholds only affects future ingest · ADR-0056 D2 rule v3</div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            disabled
            title="Threshold write stays disabled (W79 / ADR-0058: five rounds of evidence already optimal)"
          >
            Save rule
          </button>
        </div>
      </div>

      {editing ? (
        <EditPresetDialog
          key={editing.profile}
          item={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            void queryClient.invalidateQueries({ queryKey: PRESETS_QUERY_KEY });
            setEditing(null);
          }}
        />
      ) : null}
    </div>
  );
}

// ============================================================================
// EditPresetDialog — global preset override edit form (W82 / ADR-0063, 視覺零發明).
// Reuses the existing dialog.tsx primitive + .field / .input / .switch / .seg.
// PUT is a FULL replacement, so the draft starts from the full effective config
// (preserves the factory's hidden fields — prefix_depth / overview_pin / etc.).
// ============================================================================

function EditPresetDialog({
  item,
  onClose,
  onSaved,
}: {
  item: PresetMappingItem;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState<DocConfig>(item.config);
  const label = PROFILE_LABELS[item.profile] ?? item.profile;

  const saveMutation = useMutation({
    mutationFn: (config: DocConfig) => profilePresetsApi.put(item.profile, config),
    onSuccess: () => {
      toast.success(`Saved "${label}" mapping`);
      onSaved();
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : 'Save failed'),
  });

  const set = <K extends keyof DocConfig>(key: K, val: DocConfig[K]): void =>
    setDraft((d) => {
      const next: DocConfig = { ...d };
      next[key] = val;
      return next;
    });
  const num = (v: string): number | null => (v === '' ? null : Number(v));

  return (
    <Dialog open onOpenChange={(o) => (!o ? onClose() : undefined)}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit preset mapping · {label}</DialogTitle>
          <DialogDescription>
            Adjust the recall preset this profile applies automatically · <span className="mono">{item.profile}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="banner banner-warning" style={{ marginBottom: 4 }}>
          <div className="text-xs">
            This mapping applies to <b>all newly ingested</b> &quot;{label}&quot; documents. Existing documents need{' '}
            <b>re-index</b> to take effect; the defaults are already well-proven — please confirm before changing.
          </div>
        </div>

        <div style={{ display: 'grid', gap: 14 }}>
          {/* 圖上限 */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Image cap (max_images_per_answer)</label>
            <input
              className="input"
              type="number"
              min={0}
              value={draft.max_images_per_answer ?? ''}
              onChange={(e) => set('max_images_per_answer', num(e.target.value))}
              style={{ maxWidth: 140 }}
            />
          </div>

          {/* 鄰近圖 + max_aux */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Neighbour images (citation neighbour images)</label>
            <div className="row" style={{ gap: 8, alignItems: 'center', paddingTop: 4 }}>
              <span
                className="switch"
                data-on={draft.enable_citation_neighbour_images === true}
                role="switch"
                aria-checked={draft.enable_citation_neighbour_images === true}
                tabIndex={0}
                onClick={() =>
                  set('enable_citation_neighbour_images', !draft.enable_citation_neighbour_images)
                }
              />
              <span className="muted text-xs">
                {draft.enable_citation_neighbour_images ? 'On' : 'Off'}
              </span>
            </div>
            {draft.enable_citation_neighbour_images ? (
              <input
                className="input"
                type="number"
                min={0}
                value={draft.citation_neighbour_max_aux_images ?? ''}
                onChange={(e) => set('citation_neighbour_max_aux_images', num(e.target.value))}
                style={{ maxWidth: 140, marginTop: 8 }}
                aria-label="Neighbour image cap (max aux images)"
              />
            ) : null}
            <div className="hint">On = same-section neighbour aux images enter candidates; number = aux image cap.</div>
          </div>

          {/* inline marker */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Inline markers (inline image markers)</label>
            <div className="row" style={{ gap: 8, alignItems: 'center', paddingTop: 4 }}>
              <span
                className="switch"
                data-on={draft.enable_inline_image_markers === true}
                role="switch"
                aria-checked={draft.enable_inline_image_markers === true}
                tabIndex={0}
                onClick={() => set('enable_inline_image_markers', !draft.enable_inline_image_markers)}
              />
              <span className="muted text-xs">{draft.enable_inline_image_markers ? 'On' : 'Off'}</span>
            </div>
          </div>

          {/* section 錨定 + cap */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Section anchoring (section-anchored aux images)</label>
            <div className="row" style={{ gap: 8, alignItems: 'center', paddingTop: 4 }}>
              <span
                className="switch"
                data-on={draft.enable_section_anchored_aux_images === true}
                role="switch"
                aria-checked={draft.enable_section_anchored_aux_images === true}
                tabIndex={0}
                onClick={() =>
                  set('enable_section_anchored_aux_images', !draft.enable_section_anchored_aux_images)
                }
              />
              <span className="muted text-xs">
                {draft.enable_section_anchored_aux_images ? 'On' : 'Off'}
              </span>
            </div>
            {draft.enable_section_anchored_aux_images ? (
              <>
                {/* W99 — nearest 錨點策略 toggle (跟既有 .switch row pattern, 視覺零發明) */}
                <div className="row" style={{ gap: 8, alignItems: 'center', marginTop: 8 }}>
                  <span
                    className="switch"
                    data-on={draft.section_anchor_nearest === true}
                    role="switch"
                    aria-checked={draft.section_anchor_nearest === true}
                    tabIndex={0}
                    onClick={() => set('section_anchor_nearest', !draft.section_anchor_nearest)}
                  />
                  <span className="muted text-xs">
                    Anchor to nearest step (nearest): {draft.section_anchor_nearest ? 'On' : 'Off (section end)'}
                  </span>
                </div>
                <input
                  className="input"
                  type="number"
                  min={0}
                  value={draft.section_anchor_max_per_anchor ?? ''}
                  onChange={(e) => set('section_anchor_max_per_anchor', num(e.target.value))}
                  style={{ maxWidth: 140, marginTop: 8 }}
                  aria-label="Per-anchor image cap (0 = no cap)"
                />
              </>
            ) : null}
            <div className="hint">
              On = aux images anchor into their own sections (end pile → within section); nearest = anchor to the
              nearest step by doc_order (otherwise section end); number = per-anchor cap (0 = no cap).
            </div>
          </div>

          {/* 詳細度 */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">Answer detail (answer_detail)</label>
            <div className="seg" style={{ width: '100%', maxWidth: 280 }}>
              {(['concise', 'detailed'] as const).map((v) => (
                <button
                  type="button"
                  key={v}
                  className="seg-btn"
                  data-active={draft.answer_detail === v}
                  style={{ flex: 1, padding: '5px 8px', fontSize: 11.5 }}
                  onClick={() => set('answer_detail', v)}
                >
                  {v}
                </button>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter>
          <button type="button" className="btn btn-ghost btn-sm" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => saveMutation.mutate(draft)}
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending ? <span className="spinner" /> : null} Save rule
          </button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function ThresholdRow({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      <label className="label">{label}</label>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <input className="input" defaultValue={value} style={{ maxWidth: 110 }} />
        <span className="text-xs muted">{hint}</span>
      </div>
    </div>
  );
}

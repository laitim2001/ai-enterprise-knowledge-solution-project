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
import { useTranslations } from 'next-intl';
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

// profile label key → i18n key (顯示層 friendly name; 非 config data). Resolved via
// `profileLabel(profile, t)`, falling back to the raw profile id for unknown profiles.
const PROFILE_LABELS: Record<string, string> = {
  P1_sop_imgdense: 'profileP1SopImgdense',
  P1_sop_text: 'profileP1SopText',
  P2_prose: 'profileP2Prose',
  P3_slide_imgdense: 'profileP3SlideImgdense',
  P3_slide_text: 'profileP3SlideText',
  P4_scan_imgdense: 'profileP4Scan',
  P5_form: 'profileP5Form',
};

/** Resolve a profile id to its translated friendly name (raw id when unmapped). */
function profileLabel(
  profile: string,
  t: ReturnType<typeof useTranslations>,
): string {
  const key = PROFILE_LABELS[profile];
  return key ? t(key) : profile;
}

const PRESETS_QUERY_KEY = ['profile-presets'] as const;

// --- effective-config → table cell formatters (mirror mockup display strings) ---
const fmtNeighbour = (
  c: DocConfig,
  t: ReturnType<typeof useTranslations>,
): string =>
  c.enable_citation_neighbour_images
    ? t('neighbourOn', { n: c.citation_neighbour_max_aux_images ?? '—' })
    : t('off');
const fmtAnchor = (
  c: DocConfig,
  t: ReturnType<typeof useTranslations>,
): string =>
  c.enable_section_anchored_aux_images
    ? t('anchorValue', {
        mode: c.section_anchor_nearest ? t('anchorNearest') : t('anchorEnd'),
        cap: c.section_anchor_max_per_anchor ?? 0,
      })
    : '—';

export function SettingsDocProfiling() {
  const t = useTranslations('SettingsDocProfiling');
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
      toast.success(t('toastReset'));
      void queryClient.invalidateQueries({ queryKey: PRESETS_QUERY_KEY });
    },
    onError: (e) =>
      toast.error(e instanceof Error ? e.message : t('toastResetFailed')),
  });

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="banner banner-info">
        <Layers size={15} style={{ color: 'oklch(var(--info))', flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13 }}>
            {t.rich('bannerText', {
              b: (chunks) => <b>{chunks}</b>,
            })}
          </div>
          <div className="text-xs muted" style={{ marginTop: 2 }}>
            {t('bannerDesc')}
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">{t('mappingTitle')}</h3>
            <div className="card-desc">{t('mappingDesc')}</div>
          </div>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {isLoading ? (
            <div className="text-xs muted" style={{ padding: 16 }}>
              {t('loadingMappings')}
            </div>
          ) : isError ? (
            <div className="banner banner-destructive" style={{ margin: 16 }}>
              {t('loadFailed')}{' '}
              <span className="mono">
                {error instanceof Error ? error.message : t('unknownError')}
              </span>
            </div>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>{t('colProfile')}</th>
                    <th className="col-num">{t('colImageCap')}</th>
                    <th>{t('colNeighbour')}</th>
                    <th>{t('colInlineMarker')}</th>
                    <th>{t('colSectionAnchor')}</th>
                    <th>{t('colDetailLevel')}</th>
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
                            <span className="badge-dot" /> {profileLabel(item.profile, t)}
                          </span>
                          <div className="text-xs muted mono">
                            {item.profile}
                            {item.overridden ? (
                              <span className="badge badge-warning" style={{ marginLeft: 6, fontSize: 9 }}>
                                {t('overridden')}
                              </span>
                            ) : null}
                          </div>
                        </td>
                        <td className="col-num mono">{c.max_images_per_answer ?? '—'}</td>
                        <td className="text-xs">{fmtNeighbour(c, t)}</td>
                        <td className="text-xs">{c.enable_inline_image_markers ? t('on') : t('off')}</td>
                        <td className="text-xs">{fmtAnchor(c, t)}</td>
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
                                title={t('resetTitle')}
                              >
                                {t('resetToDefault')}
                              </button>
                            ) : null}
                            <button
                              type="button"
                              className="btn btn-ghost btn-xs"
                              onClick={() => setEditing(item)}
                            >
                              {t('edit')}
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
            <h3 className="card-title">{t('thresholdTitle')}</h3>
            <div className="card-desc">{t('thresholdDesc')}</div>
          </div>
        </div>
        <div className="card-body" style={{ display: 'grid', gap: 12 }}>
          <ThresholdRow
            label={t('th1Label')}
            value="0.70"
            hint={t('th1Hint')}
          />
          <ThresholdRow
            label={t('th2Label')}
            value="0.15"
            hint={t('th2Hint')}
          />
          <ThresholdRow
            label={t('th3Label')}
            value="20"
            hint={t('th3Hint')}
          />
        </div>
        <div className="card-footer">
          <div className="text-xs muted">{t('thresholdFooter')}</div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            disabled
            title={t('saveRuleDisabledTitle')}
          >
            {t('saveRule')}
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
  const t = useTranslations('SettingsDocProfiling');
  const [draft, setDraft] = useState<DocConfig>(item.config);
  const label = profileLabel(item.profile, t);

  const saveMutation = useMutation({
    mutationFn: (config: DocConfig) => profilePresetsApi.put(item.profile, config),
    onSuccess: () => {
      toast.success(t('toastSaved', { label }));
      onSaved();
    },
    onError: (e) =>
      toast.error(e instanceof Error ? e.message : t('toastSaveFailed')),
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
          <DialogTitle>{t('dialogTitle', { label })}</DialogTitle>
          <DialogDescription>
            {t('dialogDesc')} <span className="mono">{item.profile}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="banner banner-warning" style={{ marginBottom: 4 }}>
          <div className="text-xs">
            {t.rich('editWarning', {
              b: (chunks) => <b>{chunks}</b>,
              label,
            })}
          </div>
        </div>

        <div style={{ display: 'grid', gap: 14 }}>
          {/* 圖上限 */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">{t('fieldImageCap')}</label>
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
            <label className="label">{t('fieldNeighbour')}</label>
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
                {draft.enable_citation_neighbour_images ? t('on') : t('off')}
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
                aria-label={t('neighbourCapAria')}
              />
            ) : null}
            <div className="hint">{t('neighbourHint')}</div>
          </div>

          {/* inline marker */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">{t('fieldInlineMarkers')}</label>
            <div className="row" style={{ gap: 8, alignItems: 'center', paddingTop: 4 }}>
              <span
                className="switch"
                data-on={draft.enable_inline_image_markers === true}
                role="switch"
                aria-checked={draft.enable_inline_image_markers === true}
                tabIndex={0}
                onClick={() => set('enable_inline_image_markers', !draft.enable_inline_image_markers)}
              />
              <span className="muted text-xs">{draft.enable_inline_image_markers ? t('on') : t('off')}</span>
            </div>
          </div>

          {/* section 錨定 + cap */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">{t('fieldSectionAnchor')}</label>
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
                {draft.enable_section_anchored_aux_images ? t('on') : t('off')}
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
                    {t('anchorNearestLabel')}{' '}
                    {draft.section_anchor_nearest ? t('on') : t('offSectionEnd')}
                  </span>
                </div>
                <input
                  className="input"
                  type="number"
                  min={0}
                  value={draft.section_anchor_max_per_anchor ?? ''}
                  onChange={(e) => set('section_anchor_max_per_anchor', num(e.target.value))}
                  style={{ maxWidth: 140, marginTop: 8 }}
                  aria-label={t('perAnchorCapAria')}
                />
              </>
            ) : null}
            <div className="hint">{t('sectionAnchorHint')}</div>
          </div>

          {/* 詳細度 */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">{t('fieldAnswerDetail')}</label>
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
            {t('cancel')}
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => saveMutation.mutate(draft)}
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending ? <span className="spinner" /> : null} {t('saveRule')}
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

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
  P1_sop_imgdense: 'P1 圖密SOP',
  P1_sop_text: 'P1 文字SOP',
  P2_prose: 'P2 散文',
  P3_slide_imgdense: 'P3 圖密簡報',
  P3_slide_text: 'P3 文字簡報',
  P4_scan_imgdense: 'P4 掃描',
  P5_form: 'P5 表單',
};

const PRESETS_QUERY_KEY = ['profile-presets'] as const;

// --- effective-config → table cell formatters (mirror mockup display strings) ---
const fmtNeighbour = (c: DocConfig): string =>
  c.enable_citation_neighbour_images
    ? `開 · ${c.citation_neighbour_max_aux_images ?? '—'}`
    : '關';
const fmtAnchor = (c: DocConfig): string =>
  c.enable_section_anchored_aux_images
    ? `section · cap ${c.section_anchor_max_per_anchor ?? 0}`
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
      toast.success('已還原出廠預設');
      void queryClient.invalidateQueries({ queryKey: PRESETS_QUERY_KEY });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : '還原失敗'),
  });

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      <div className="banner banner-info">
        <Layers size={15} style={{ color: 'oklch(var(--info))', flexShrink: 0 }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 13 }}>
            <b>文件分類規則</b> —
            系統 ingest 時用 rule-based profiler(W72)偵測文件 profile,自動套對應 recall preset。
          </div>
          <div className="text-xs muted" style={{ marginTop: 2 }}>
            呢度係自動規則嘅指揮中心:調 profile→preset 映射 + 偵測 threshold · ADR-0056 層 A · LLM 退選用保險
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">Profile → preset 映射</h3>
            <div className="card-desc">
              每個偵測 profile 套邊套 recall/render preset。改呢度影響所有新 ingest 文件(現有要 re-index)。
            </div>
          </div>
        </div>
        <div className="card-body" style={{ padding: 0 }}>
          {isLoading ? (
            <div className="text-xs muted" style={{ padding: 16 }}>
              載入映射中…
            </div>
          ) : isError ? (
            <div className="banner banner-destructive" style={{ margin: 16 }}>
              載入失敗:<span className="mono">{error instanceof Error ? error.message : '未知錯誤'}</span>
            </div>
          ) : (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Profile</th>
                    <th className="col-num">圖上限</th>
                    <th>鄰近圖</th>
                    <th>inline marker</th>
                    <th>section 錨定</th>
                    <th>詳細度</th>
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
                                已覆寫
                              </span>
                            ) : null}
                          </div>
                        </td>
                        <td className="col-num mono">{c.max_images_per_answer ?? '—'}</td>
                        <td className="text-xs">{fmtNeighbour(c)}</td>
                        <td className="text-xs">{c.enable_inline_image_markers ? '開' : '關'}</td>
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
                                title="還原出廠預設(刪除覆寫)"
                              >
                                還原預設
                              </button>
                            ) : null}
                            <button
                              type="button"
                              className="btn btn-ghost btn-xs"
                              onClick={() => setEditing(item)}
                            >
                              編輯
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
            <h3 className="card-title">偵測 threshold</h3>
            <div className="card-desc">
              調 profiler 分類門檻。低於信心門檻 → fallback 保守 preset + 標「待人手確認」。
            </div>
          </div>
        </div>
        <div className="card-body" style={{ display: 'grid', gap: 12 }}>
          <ThresholdRow
            label="低信心門檻(confidence)"
            value="0.70"
            hint="低於此 → 黃旗 + fallback 保守 preset"
          />
          <ThresholdRow
            label="P1 圖密門檻(img_density)"
            value="0.15"
            hint="≥ 此 + depth≥3 + list_ratio≥0.3 → P1 圖密SOP"
          />
          <ThresholdRow
            label="too_small 段落門檻"
            value="20"
            hint="少於此段落數 → too_small(唔路由,繼承上層)"
          />
        </div>
        <div className="card-footer">
          <div className="text-xs muted">改 threshold 只影響將來 ingest · ADR-0056 D2 rule v3</div>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            disabled
            title="threshold 寫入維持不做(W79 / ADR-0058:五輪實證已最佳)"
          >
            儲存規則
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
      toast.success(`已儲存「${label}」映射`);
      onSaved();
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : '儲存失敗'),
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
          <DialogTitle>編輯 preset 映射 · {label}</DialogTitle>
          <DialogDescription>
            調整呢個 profile 自動套用嘅 recall preset · <span className="mono">{item.profile}</span>
          </DialogDescription>
        </DialogHeader>

        <div className="banner banner-warning" style={{ marginBottom: 4 }}>
          <div className="text-xs">
            呢個映射套用到<b>所有新 ingest</b>嘅「{label}」類文件。現有文件要 <b>re-index</b> 先生效;
            預設值已實證良好,改前請確認。
          </div>
        </div>

        <div style={{ display: 'grid', gap: 14 }}>
          {/* 圖上限 */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">圖上限(max_images_per_answer)</label>
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
            <label className="label">鄰近圖(citation neighbour images)</label>
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
                {draft.enable_citation_neighbour_images ? '開' : '關'}
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
                aria-label="鄰近圖上限(max aux images)"
              />
            ) : null}
            <div className="hint">開 = 同章節鄰近輔助圖入候選;數字 = 輔助圖上限。</div>
          </div>

          {/* inline marker */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">inline 圖文標記(inline image markers)</label>
            <div className="row" style={{ gap: 8, alignItems: 'center', paddingTop: 4 }}>
              <span
                className="switch"
                data-on={draft.enable_inline_image_markers === true}
                role="switch"
                aria-checked={draft.enable_inline_image_markers === true}
                tabIndex={0}
                onClick={() => set('enable_inline_image_markers', !draft.enable_inline_image_markers)}
              />
              <span className="muted text-xs">{draft.enable_inline_image_markers ? '開' : '關'}</span>
            </div>
          </div>

          {/* section 錨定 + cap */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">section 錨定(section-anchored aux images)</label>
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
                {draft.enable_section_anchored_aux_images ? '開' : '關'}
              </span>
            </div>
            {draft.enable_section_anchored_aux_images ? (
              <input
                className="input"
                type="number"
                min={0}
                value={draft.section_anchor_max_per_anchor ?? ''}
                onChange={(e) => set('section_anchor_max_per_anchor', num(e.target.value))}
                style={{ maxWidth: 140, marginTop: 8 }}
                aria-label="每錨點圖片上限(0 = 無 cap)"
              />
            ) : null}
            <div className="hint">開 = aux 圖錨入各自章節(末尾堆→章節內);數字 = 每錨點上限(0=無 cap)。</div>
          </div>

          {/* 詳細度 */}
          <div className="field" style={{ marginBottom: 0 }}>
            <label className="label">答案詳細度(answer_detail)</label>
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
            取消
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => saveMutation.mutate(draft)}
            disabled={saveMutation.isPending}
          >
            {saveMutation.isPending ? <span className="spinner" /> : null} 儲存規則
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

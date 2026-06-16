/**
 * Global profile→preset mapping API (W82 / ADR-0063; consumes the backend
 * `api/routes/profile_presets.py`).
 *
 * The Settings →「文件分類規則」admin surface edits the GLOBAL profile→preset
 * mapping. `config` is the EFFECTIVE `DocConfig` (admin override overlaid on the
 * hardcoded factory preset); `overridden` flags an admin-edited profile. PUT
 * is a full replacement of the override; DELETE restores the factory (還原預設).
 * Edits only affect FUTURE routing (next ingest / manual override / backfill) —
 * existing per-doc configs are not re-routed (per ADR-0063).
 */

import { ApiClient } from '../api-client';
import type { DocConfig } from './doc-config';

const client = new ApiClient();

/** One row of the profile→preset mapping — mirrors backend `PresetMappingItem`. */
export interface PresetMappingItem {
  profile: string;
  config: DocConfig;
  overridden: boolean;
}

export const profilePresetsApi = {
  // GET — effective mapping (factory overlaid by admin override) for the routable profiles.
  list: (): Promise<PresetMappingItem[]> =>
    client.get<PresetMappingItem[]>('/profile-presets'),

  // PUT — upsert the admin override (full replacement); returns the new effective item.
  put: (profile: string, config: DocConfig): Promise<PresetMappingItem> =>
    client.put<PresetMappingItem>(`/profile-presets/${encodeURIComponent(profile)}`, config),

  // DELETE — 還原預設: drop the override, restore the factory value (204; idempotent).
  delete: (profile: string): Promise<void> =>
    client.delete(`/profile-presets/${encodeURIComponent(profile)}`),
};

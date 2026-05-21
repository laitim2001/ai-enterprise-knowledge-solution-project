/**
 * `<RoleBadge>` — the RBAC role chip (W24c F9.2 per ADR-0027).
 *
 * Canonical visual spec: mockup `references/design-mockups/ekp-page-users.jsx`
 * lines 193-207 (`RoleBadge`) + lines 19-24 (`ROLES`). Shared by the Members
 * (F9.2), Roles and Groups (F9.3) tabs of `/users`, so it lives here as a
 * standalone primitive — the mockup itself factored it out (`window.RoleBadge`).
 *
 * The mockup derives the background / border tints at runtime via
 * `color.replace(")", " / 0.12)")`. They are precomputed here as literal oklch
 * token strings — identical rendered output, no string surgery.
 */

import type { EkpRoleKey } from '@/lib/api/admin';
import { EKP_ROLE_LABELS } from '@/lib/api/admin';

/** Per-role chip colors — mockup `ROLES[].color` + the 0.12 / 0.3 alpha tints. */
const ROLE_BADGE_COLOR: Record<
  EkpRoleKey,
  { fg: string; bg: string; border: string }
> = {
  admin: {
    fg: 'oklch(var(--accent))',
    bg: 'oklch(var(--accent) / 0.12)',
    border: 'oklch(var(--accent) / 0.3)',
  },
  editor: {
    fg: 'oklch(0.55 0.13 240)',
    bg: 'oklch(0.55 0.13 240 / 0.12)',
    border: 'oklch(0.55 0.13 240 / 0.3)',
  },
  user: {
    fg: 'oklch(0.55 0.16 145)',
    bg: 'oklch(0.55 0.16 145 / 0.12)',
    border: 'oklch(0.55 0.16 145 / 0.3)',
  },
  power: {
    fg: 'oklch(0.55 0.16 285)',
    bg: 'oklch(0.55 0.16 285 / 0.12)',
    border: 'oklch(0.55 0.16 285 / 0.3)',
  },
};

export function RoleBadge({ role }: { role: EkpRoleKey }) {
  const c = ROLE_BADGE_COLOR[role];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '1px 7px',
        borderRadius: 'var(--radius-sm)',
        fontSize: 11.5,
        fontWeight: 500,
        background: c.bg,
        color: c.fg,
        border: `1px solid ${c.border}`,
        fontFamily: 'var(--font-mono)',
      }}
    >
      {EKP_ROLE_LABELS[role]}
    </span>
  );
}

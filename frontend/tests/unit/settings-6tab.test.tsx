/**
 * Unit tests — `/settings` 6-tab `PageSettingsRich` (W24-wave-c1 F5 / F7).
 *
 * Verifies:
 *  - 6-tab nav renders with mockup-faithful labels (Profile / Appearance /
 *    Connections / Identity & Auth / API Keys & Quotas / Account)
 *  - `?tab=` deep link drives the initial active panel
 *  - Tab switch updates `aria-selected` + URL via `router.replace`
 *  - Each tab content area mounts without throwing (sanity render-smoke)
 *
 * Mocks `adminApi` so 4 data-bound settings/* components don't fetch the
 * real backend in unit context.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';

// next/navigation mock — exposes searchParams + a controllable router.replace spy.
const mockReplace = vi.fn();
let mockSearchParams = new URLSearchParams('');

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: mockReplace }),
  useSearchParams: () => mockSearchParams,
}));

// next-themes mock — page reads useTheme() in AppearanceTab.
vi.mock('next-themes', () => ({
  useTheme: () => ({ resolvedTheme: 'light', setTheme: vi.fn() }),
}));

// auth-provider mock — preserves W22 F8.1 logic.
vi.mock('@/lib/providers/auth-provider', () => ({
  useCurrentUser: () => ({
    oid: 'mock-oid',
    tid: 'mock-tid',
    preferredUsername: 'chris.lai@ricoh.com',
    isMock: true,
  }),
  useAuthStore: (selector: (s: { signOut: () => void }) => unknown) =>
    selector({ signOut: vi.fn() }),
}));

// adminApi mock — settings/* components data-fetch on mount, return minimal
// shape that matches each component's render path.
vi.mock('@/lib/api/admin', () => ({
  adminApi: {
    listConnections: vi.fn(async () => []),
    getConnection: vi.fn(),
    updateConnection: vi.fn(),
    testConnection: vi.fn(),
    rotateSecret: vi.fn(),
    getIdentity: vi.fn(async () => ({
      tenant: {
        tenant_id: '00000000-0000-0000-0000-000000000000',
        tenant_domain: 'ricoh.onmicrosoft.com',
        cloud_instance: 'azure_public',
        authority_url:
          'https://login.microsoftonline.com/00000000-0000-0000-0000-000000000000',
      },
      app_registration: {
        client_id: '00000000-0000-0000-0000-000000000000',
        client_secret_kv_ref: 'ekp-entra-client-secret',
        client_secret_masked_preview: null,
        client_secret_expires_at: null,
        redirect_uris: ['https://ekp-beta.ricoh.com/auth/callback'],
        scopes: ['User.Read', 'openid'],
        sign_in_audience: 'single',
      },
      msal: {
        token_cache_strategy: 'memory',
        session_ttl: '7d',
        refresh_token_rotation: '24h',
        csrf_token_rotation: '1h',
        cookie_settings_preview: 'Set-Cookie: ekp_session=…',
      },
      roles: {
        mappings: [
          {
            ekp_role: 'workspace_admin',
            entra_group_name: 'grp-ekp-admins',
            entra_group_id: 'gid-1',
            member_count: null,
            is_tier2_disabled: false,
            tier2_reason: null,
          },
          {
            ekp_role: 'power_user',
            entra_group_name: '',
            entra_group_id: '',
            member_count: null,
            is_tier2_disabled: true,
            tier2_reason: 'Tier 2',
          },
        ],
      },
      policy: {
        allowed_email_domains: ['@ricoh.com'],
        require_mfa_workspace_admin: true,
        require_mfa_all_roles_tier2: false,
        auto_disable_after_days: 90,
      },
      updated_at: '2026-05-19T00:00:00Z',
    })),
    patchTenant: vi.fn(),
    patchAppRegistration: vi.fn(),
    patchMsal: vi.fn(),
    patchRoles: vi.fn(),
    patchPolicy: vi.fn(),
    getUsageStats: vi.fn(async () => ({
      api_calls_24h: 0,
      api_calls_delta_pct: null,
      spend_today_usd: 0,
      spend_cap_daily_usd: 10,
      spend_pct_used: 0,
      token_throughput_tpm: 0,
      token_throughput_p95_in_cap: true,
      rate_limit_hits_24h: 0,
      realtime_status: 'no_client',
    })),
    getOutgoingQuotas: vi.fn(async () => ({
      rows: [],
      realtime_status: 'no_client',
    })),
    patchAlertThreshold: vi.fn(),
    getIncomingKeys: vi.fn(async () => ({
      enabled: false,
      reason: 'Tier 2 — Tier 1 access via web UI only (MSAL SSO).',
      tier2_trigger: 'post-W12 Tier 2 governance',
    })),
    listAuditLog: vi.fn(async () => []),
  },
}));

import SettingsPage from '@/app/(app)/settings/page';

describe('Settings 6-tab PageSettingsRich (W24 F5)', () => {
  beforeEach(() => {
    mockReplace.mockReset();
    mockSearchParams = new URLSearchParams('');
  });

  it('renders all 6 tab labels in the navigation', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /^settings$/i })).toBeInTheDocument();
    });
    expect(screen.getByRole('tab', { name: /^profile$/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /^appearance$/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /^connections$/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /identity & auth/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /api keys & quotas/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /^account$/i })).toBeInTheDocument();
  });

  it('defaults to the Profile tab when no ?tab= query param', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      const profileTab = screen.getByRole('tab', { name: /^profile$/i });
      expect(profileTab).toHaveAttribute('aria-selected', 'true');
    });
    // Profile body — the user's mock email appears.
    expect(screen.getByText(/chris\.lai@ricoh\.com/i)).toBeInTheDocument();
  });

  it('honors ?tab=identity deep link', async () => {
    mockSearchParams = new URLSearchParams('tab=identity');
    render(<SettingsPage />);
    await waitFor(() => {
      const identityTab = screen.getByRole('tab', { name: /identity & auth/i });
      expect(identityTab).toHaveAttribute('aria-selected', 'true');
    });
    // Identity body — loading banner appears initially (adminApi.getIdentity is async).
    // Wait for the resolved tenant card heading.
    await waitFor(() => {
      expect(screen.getByText(/entra id tenant/i)).toBeInTheDocument();
    });
  });

  it('honors ?tab=api-keys deep link with hyphen', async () => {
    mockSearchParams = new URLSearchParams('tab=api-keys');
    render(<SettingsPage />);
    await waitFor(() => {
      const tab = screen.getByRole('tab', { name: /api keys & quotas/i });
      expect(tab).toHaveAttribute('aria-selected', 'true');
    });
  });

  it('falls back to profile when ?tab= contains an unknown value', async () => {
    mockSearchParams = new URLSearchParams('tab=bogus');
    render(<SettingsPage />);
    await waitFor(() => {
      const profileTab = screen.getByRole('tab', { name: /^profile$/i });
      expect(profileTab).toHaveAttribute('aria-selected', 'true');
    });
  });

  it('updates URL via router.replace on tab click', async () => {
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /^connections$/i })).toBeInTheDocument();
    });
    const connectionsTab = screen.getByRole('tab', { name: /^connections$/i });
    fireEvent.click(connectionsTab);
    await waitFor(() => {
      expect(connectionsTab).toHaveAttribute('aria-selected', 'true');
    });
    expect(mockReplace).toHaveBeenCalled();
    const [url] = mockReplace.mock.calls[0]!;
    expect(url).toContain('tab=connections');
  });

  it('Account tab renders Sign out + Audit log + Danger Zone', async () => {
    mockSearchParams = new URLSearchParams('tab=account');
    render(<SettingsPage />);
    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /sign out/i }),
      ).toBeInTheDocument();
    });
    // Audit log surface header (F5.8a promoted from F4 deferral).
    expect(screen.getByText(/audit log/i)).toBeInTheDocument();
    // Danger zone heading.
    expect(screen.getByText(/danger zone/i)).toBeInTheDocument();
  });

  it('Identity Power User row carries Tier 2 disabled affordance', async () => {
    mockSearchParams = new URLSearchParams('tab=identity');
    render(<SettingsPage />);
    await waitFor(() => {
      // Power User row badge (one of multiple "Tier 2" badges in mocked data).
      const tier2Badges = screen.getAllByText(/tier 2/i);
      expect(tier2Badges.length).toBeGreaterThan(0);
    });
    // "Power User" may appear in the role badge + the Tier 2 catalog —
    // `getAllByText` rather than `getByText` to allow either count.
    expect(screen.getAllByText(/power user/i).length).toBeGreaterThan(0);
  });

  it('API Keys tab renders 4-stat strip + incoming Tier 2 affordance', async () => {
    mockSearchParams = new URLSearchParams('tab=api-keys');
    render(<SettingsPage />);
    await waitFor(() => {
      expect(screen.getByText(/api calls today/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/spend today/i)).toBeInTheDocument();
    expect(screen.getByText(/token throughput/i)).toBeInTheDocument();
    expect(screen.getByText(/rate limit hits/i)).toBeInTheDocument();
    // Incoming API keys card heading carries the Tier 2 badge.
    expect(screen.getByText(/incoming api keys/i)).toBeInTheDocument();
  });
});

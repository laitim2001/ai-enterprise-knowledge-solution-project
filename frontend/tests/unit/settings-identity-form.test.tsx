/**
 * Unit tests — `<SettingsIdentity>` TenantCard form validation (W24b-wave-c2 F7.1).
 *
 * Verifies the react-hook-form + zod (`entraTenantConfigSchema`) inline-edit
 * wiring on the Identity tab's Tenant card: a malformed GUID / domain blocks
 * submit with an inline error, a corrected value clears it, and a valid edit
 * reaches `adminApi.patchTenant`.
 *
 * Mocks `adminApi` so the card's data-fetch + PATCH are controllable.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

vi.mock('@/lib/api/admin', () => ({
  adminApi: {
    getIdentity: vi.fn(),
    patchTenant: vi.fn(),
    patchAppRegistration: vi.fn(),
    patchMsal: vi.fn(),
    patchPolicy: vi.fn(),
  },
}));

import { adminApi } from '@/lib/api/admin';
import { SettingsIdentity } from '@/components/settings/settings-identity';

const getIdentity = vi.mocked(adminApi.getIdentity);
const patchTenant = vi.mocked(adminApi.patchTenant);

// Both are RFC-4122 v4-shaped (version nibble 4 + variant nibble 8) so they
// pass zod `.uuid()` under both the strict + relaxed regex variants.
const VALID_GUID = 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d';
const OTHER_VALID_GUID = '11111111-2222-4333-8444-555555555555';

function identityConfig() {
  return {
    tenant: {
      tenant_id: VALID_GUID,
      tenant_domain: 'ricoh.onmicrosoft.com',
      cloud_instance: 'azure_public' as const,
      authority_url: `https://login.microsoftonline.com/${VALID_GUID}`,
    },
    app_registration: {
      client_id: VALID_GUID,
      client_secret_kv_ref: 'ekp-entra-client-secret',
      client_secret_masked_preview: null,
      client_secret_expires_at: null,
      redirect_uris: ['https://ekp-beta.ricoh.com/auth/callback'],
      scopes: ['User.Read', 'openid'],
      sign_in_audience: 'single' as const,
    },
    msal: {
      token_cache_strategy: 'memory' as const,
      session_ttl: '7d',
      refresh_token_rotation: '24h',
      csrf_token_rotation: '1h',
      cookie_settings_preview: 'Set-Cookie: ekp_session=…',
    },
    roles: {
      mappings: [
        {
          ekp_role: 'workspace_admin' as const,
          entra_group_name: 'grp-ekp-admins',
          entra_group_id: 'gid-1',
          member_count: null,
          is_tier2_disabled: false,
          tier2_reason: null,
        },
      ],
    },
    policy: {
      allowed_email_domains: ['@ricoh.com'],
      require_mfa_workspace_admin: true,
      require_mfa_all_roles_tier2: false as const,
      auto_disable_after_days: 90,
    },
    updated_at: '2026-05-20T00:00:00Z',
  };
}

function renderIdentity() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={client}>
      <SettingsIdentity />
    </QueryClientProvider>,
  );
}

async function tenantForm(): Promise<HTMLFormElement> {
  const input = await screen.findByLabelText('Tenant ID');
  const form = input.closest('form');
  if (!form) throw new Error('Tenant ID input is not inside a <form>');
  return form;
}

describe('SettingsIdentity TenantCard validation (W24b F7.1)', () => {
  beforeEach(() => {
    getIdentity.mockReset();
    patchTenant.mockReset();
    getIdentity.mockResolvedValue(identityConfig());
    patchTenant.mockImplementation(async (v) => v);
  });

  it('blocks submit + shows a GUID error for a malformed tenant_id', async () => {
    renderIdentity();
    const form = await tenantForm();
    fireEvent.change(screen.getByLabelText('Tenant ID'), {
      target: { value: 'not-a-guid' },
    });
    fireEvent.submit(form);
    expect(
      await screen.findByText('Must be a valid GUID'),
    ).toBeInTheDocument();
    expect(patchTenant).not.toHaveBeenCalled();
  });

  it('clears the GUID error once a valid tenant_id is typed', async () => {
    renderIdentity();
    const form = await tenantForm();
    const input = screen.getByLabelText('Tenant ID');
    fireEvent.change(input, { target: { value: 'not-a-guid' } });
    fireEvent.submit(form);
    expect(
      await screen.findByText('Must be a valid GUID'),
    ).toBeInTheDocument();
    fireEvent.change(input, { target: { value: OTHER_VALID_GUID } });
    await waitFor(() => {
      expect(
        screen.queryByText('Must be a valid GUID'),
      ).not.toBeInTheDocument();
    });
  });

  it('blocks submit + shows a domain error for a malformed tenant_domain', async () => {
    renderIdentity();
    const form = await tenantForm();
    fireEvent.change(screen.getByLabelText('Tenant domain'), {
      target: { value: 'bad domain!' },
    });
    fireEvent.submit(form);
    expect(
      await screen.findByText(/domain may contain only/i),
    ).toBeInTheDocument();
    expect(patchTenant).not.toHaveBeenCalled();
  });

  it('submits a valid tenant edit to adminApi.patchTenant', async () => {
    renderIdentity();
    const form = await tenantForm();
    fireEvent.change(screen.getByLabelText('Tenant ID'), {
      target: { value: OTHER_VALID_GUID },
    });
    fireEvent.submit(form);
    await waitFor(() => {
      expect(patchTenant).toHaveBeenCalledTimes(1);
    });
    expect(patchTenant).toHaveBeenCalledWith(
      expect.objectContaining({
        tenant_id: OTHER_VALID_GUID,
        authority_url: null,
      }),
    );
  });
});

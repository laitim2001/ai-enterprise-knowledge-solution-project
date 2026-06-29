/**
 * Unit tests — <LoginGate> splash states (BUG-038).
 *
 * The gate wraps every (app) route. Regression focus: while auth identity is
 * still resolving (status='loading' — cookie hydration via GET /auth/me, or
 * MSAL init), the user may already be signed in, so the gate must show a neutral
 * spinner WITHOUT the "Sign in to continue" CTA. The CTA only belongs in the
 * definitively-unauthenticated (idle / error) states. Before the fix the CTA
 * rendered in every non-authenticated state including loading — the first test
 * here fails pre-fix, passes post-fix.
 */

import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const { useAuthStatusMock } = vi.hoisted(() => ({ useAuthStatusMock: vi.fn() }));

// authMode must NOT be 'mock' — mock mode passes through without ever gating.
vi.mock('@/lib/providers/auth-provider', () => ({
  authMode: 'cookie',
  useAuthStatus: useAuthStatusMock,
}));

import { LoginGate } from '@/components/auth/login-gate';

const CTA = 'Sign in to continue';

describe('<LoginGate> splash states (BUG-038)', () => {
  beforeEach(() => {
    useAuthStatusMock.mockReset();
  });

  it('loading: shows a spinner WITHOUT the sign-in CTA (BUG-038 regression)', () => {
    useAuthStatusMock.mockReturnValue('loading');
    render(
      <LoginGate>
        <div>protected</div>
      </LoginGate>,
    );
    // An already-signed-in user being re-hydrated must not be shown the CTA…
    expect(screen.queryByText(CTA)).not.toBeInTheDocument();
    // …but the neutral spinner is present (lucide Loader2 renders an svg).
    expect(document.querySelector('svg.animate-spin')).toBeInTheDocument();
    // Children stay gated while identity is resolving.
    expect(screen.queryByText('protected')).not.toBeInTheDocument();
  });

  it('idle (401 — definitively unauthenticated): shows the sign-in CTA', () => {
    useAuthStatusMock.mockReturnValue('idle');
    render(
      <LoginGate>
        <div>protected</div>
      </LoginGate>,
    );
    expect(screen.getByText(CTA)).toBeInTheDocument();
  });

  it('error: shows the sign-in CTA plus the failure message', () => {
    useAuthStatusMock.mockReturnValue('error');
    render(
      <LoginGate>
        <div>protected</div>
      </LoginGate>,
    );
    expect(screen.getByText(CTA)).toBeInTheDocument();
    expect(screen.getByText(/Sign-in failed/i)).toBeInTheDocument();
  });

  it('authenticated: passes children through (no splash, no CTA)', () => {
    useAuthStatusMock.mockReturnValue('authenticated');
    render(
      <LoginGate>
        <div>protected</div>
      </LoginGate>,
    );
    expect(screen.getByText('protected')).toBeInTheDocument();
    expect(screen.queryByText(CTA)).not.toBeInTheDocument();
  });
});

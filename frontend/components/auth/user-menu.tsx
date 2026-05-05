'use client';

/**
 * C09 Admin shell user menu (W7 D2 F1.4 login flow UI).
 *
 * Renders the current authenticated user (mock or real Entra ID) with a
 * sign-out action. Mock mode shows a "[mock]" badge so devs never confuse
 * dev session with LIVE Beta.
 */

import { useAuthStore, useCurrentUser } from '@/lib/providers/auth-provider';

export function UserMenu() {
  const user = useCurrentUser();
  const signOut = useAuthStore((s) => s.signOut);

  if (!user) {
    return (
      <div className="text-xs text-[oklch(0.55_0_0)]">Signing in…</div>
    );
  }

  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="flex flex-col">
        <span className="font-medium">{user.preferredUsername}</span>
        {user.isMock ? (
          <span className="text-xs text-[oklch(0.55_0_0)]">[mock]</span>
        ) : null}
      </div>
      <button
        type="button"
        onClick={() => void signOut()}
        className="rounded border border-[oklch(0.92_0_0)] px-3 py-1 text-xs hover:bg-[oklch(0.94_0_0)]"
      >
        Sign out
      </button>
    </div>
  );
}

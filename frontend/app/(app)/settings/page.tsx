'use client';

/**
 * Settings (`/settings`) — 6-tab `PageSettingsRich` (W24-wave-c1 F5 per
 * ADR-0026 Option B + mockup `references/design-mockups/ekp-page-settings-tabs.jsx:7-46`).
 *
 * **6 tabs** per ADR-0026 Accepted Option B fully editable Settings:
 *   profile (W22 F8.1 thin Profile card preserved)
 *   appearance (W22 F8.1 thin Appearance card preserved)
 *   connections (F2 9-provider × 5-category service connections — NEW)
 *   identity (F3 Entra + MSAL + role + policy — NEW)
 *   api-keys (F4 4-stat + outgoing quotas + incoming Tier 2 disabled — NEW)
 *   account (W22 F8.1 thin Account card + F5 audit log preview — NEW)
 *
 * **Deep link**: `?tab=<id>` query param resolves the initial tab; default
 * = `profile`. Pattern mirrors W18 F3 chat `?q=` deep-link.
 *
 * **Pre-active-flip R6 audit** (per CLAUDE.md §10 R6):
 *   - Plan §2 F5.1 "rewrite — replace thin v1 3-card structure" — confirmed
 *     W22 F8.1 ProfileCard / AppearanceCard / AccountCard inline functions
 *     are preserved as the Profile + Appearance + Account tab bodies.
 *   - Plan §2 F5.2 `?tab=` deep link "default = profile" — implemented via
 *     `useSearchParams` (App Router hook;Suspense-boundary required when
 *     consumed in client component per Next 14 docs).
 *   - Plan §2 F5.8 mentioned "Audit log preview surface" — F4 deferred read
 *     endpoint to "F5/Wave C2"; F5 ships the read endpoint as F5 backend
 *     hook + `<SettingsAuditLog>` sub-card inside Account tab.
 *
 * Preserved from W22 F8.1: `useAuthStore.signOut` + `useCurrentUser` hook +
 * AuthenticatedUser shape + computeInitials helper. Per CLAUDE.md §1.3
 * surgical — extends, does NOT rewrite the Profile / Appearance / Account
 * logic.
 *
 * W24b-wave-c2 F4: each of the 6 tab bodies is wrapped in an `<ErrorBoundary>`
 * (`<TabBoundary>`) so a thrown tab degrades to a recoverable `<TabErrorState>`
 * without taking down the page.
 */

import {
  Activity,
  KeyRound,
  Layers,
  LogOut,
  PlugZap,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Users,
} from 'lucide-react';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Suspense,
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from 'react';

import { ErrorBoundary } from '@/components/error/error-boundary';
import { SettingsApiKeys } from '@/components/settings/settings-api-keys';
import { SettingsAuditLog } from '@/components/settings/settings-audit-log';
import { SettingsConnections } from '@/components/settings/settings-connections';
import { SettingsDocProfiling } from '@/components/settings/settings-doc-profiling';
import { SettingsIdentity } from '@/components/settings/settings-identity';
import { TabErrorState } from '@/components/settings/tab-error-state';
import { DisabledAffordance } from '@/components/ui/disabled-affordance';
import type { AuthenticatedUser } from '@/lib/auth/types';
import { useAuthStore, useCurrentUser } from '@/lib/providers/auth-provider';

const TABS = [
  { id: 'profile', labelKey: 'tabProfile', icon: Users },
  { id: 'appearance', labelKey: 'tabAppearance', icon: Sparkles },
  { id: 'connections', labelKey: 'tabConnections', icon: PlugZap },
  { id: 'identity', labelKey: 'tabIdentity', icon: ShieldCheck },
  { id: 'api-keys', labelKey: 'tabApiKeys', icon: KeyRound },
  { id: 'account', labelKey: 'tabAccount', icon: Activity },
  // W78 / ADR-0056 層 A 段③ — 文件分類規則(admin profiler 指揮中心)
  { id: 'doc-profiling', labelKey: 'tabDocProfiling', icon: Layers },
] as const;

type TabId = (typeof TABS)[number]['id'];

const VALID_TABS = new Set<TabId>(TABS.map((t) => t.id));

/**
 * Compute 2-char avatar initials from `preferredUsername`:
 *  "chris.lai@ricoh.com" → "CL"
 */
function computeInitials(username: string | null | undefined): string {
  if (!username) return '??';
  const localPart = username.split('@')[0] ?? username;
  const parts = localPart.split(/[.\-_+]/).filter(Boolean);
  if (parts.length >= 2 && parts[0] && parts[1]) {
    return (parts[0][0]! + parts[1][0]!).toUpperCase();
  }
  return localPart.slice(0, 2).toUpperCase() || '??';
}

/** Wraps a settings tab body in an error boundary scoped to that tab. */
function TabBoundary({
  tabName,
  children,
}: {
  tabName: string;
  children: ReactNode;
}) {
  return (
    <ErrorBoundary
      fallback={(reset) => <TabErrorState tabName={tabName} onRetry={reset} />}
    >
      {children}
    </ErrorBoundary>
  );
}

export default function SettingsPage() {
  const t = useTranslations('Settings');
  return (
    <Suspense
      fallback={
        <div className="content">
          <div className="content-narrow" style={{ maxWidth: 1080 }}>
            <div className="page-header">
              <h1 className="page-title">{t('pageTitle')}</h1>
            </div>
          </div>
        </div>
      }
    >
      <SettingsPageInner />
    </Suspense>
  );
}

function SettingsPageInner() {
  const t = useTranslations('Settings');
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialTab = searchParams.get('tab') as TabId | null;
  const [tab, setTab] = useState<TabId>(
    initialTab && VALID_TABS.has(initialTab) ? initialTab : 'profile',
  );

  const user = useCurrentUser();
  const signOut = useAuthStore((s) => s.signOut);
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleTabChange = useCallback(
    (next: TabId) => {
      setTab(next);
      // Shallow URL update — preserves deep-link sharing without full navigation.
      const url = new URL(window.location.href);
      url.searchParams.set('tab', next);
      router.replace(url.pathname + url.search, { scroll: false });
    },
    [router],
  );

  return (
    <div className="content">
      <div className="content-narrow" style={{ maxWidth: 1080 }}>
        <div className="page-header">
          <div>
            <h1 className="page-title">{t('pageTitle')}</h1>
            <p className="page-subtitle">
              {t.rich('subtitle', {
                b: (chunks) => <b>{chunks}</b>,
              })}
            </p>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="tabs" role="tablist" aria-label={t('tablistAria')}>
          {TABS.map((tabItem) => {
            const Icon = tabItem.icon;
            const active = tab === tabItem.id;
            return (
              <button
                key={tabItem.id}
                type="button"
                role="tab"
                aria-selected={active}
                className="tab"
                data-active={active}
                onClick={() => handleTabChange(tabItem.id)}
              >
                <Icon size={14} aria-hidden="true" /> {t(tabItem.labelKey)}
              </button>
            );
          })}
        </div>

        {/* Tab body — each wrapped in a tab-scoped error boundary (F4). */}
        {tab === 'profile' && (
          <TabBoundary tabName={t('tabProfile')}>
            <ProfileTab user={user} />
          </TabBoundary>
        )}
        {tab === 'appearance' && (
          <TabBoundary tabName={t('tabAppearance')}>
            <AppearanceTab
              mounted={mounted}
              resolvedTheme={resolvedTheme ?? null}
              setTheme={setTheme}
            />
          </TabBoundary>
        )}
        {tab === 'connections' && (
          <TabBoundary tabName={t('tabConnections')}>
            <SettingsConnections />
          </TabBoundary>
        )}
        {tab === 'identity' && (
          <TabBoundary tabName={t('tabIdentity')}>
            <SettingsIdentity />
          </TabBoundary>
        )}
        {tab === 'api-keys' && (
          <TabBoundary tabName={t('tabApiKeys')}>
            <SettingsApiKeys />
          </TabBoundary>
        )}
        {tab === 'account' && (
          <TabBoundary tabName={t('tabAccount')}>
            <AccountTab onSignOut={() => void signOut()} />
          </TabBoundary>
        )}
        {tab === 'doc-profiling' && (
          <TabBoundary tabName={t('tabDocProfiling')}>
            <SettingsDocProfiling />
          </TabBoundary>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// ProfileTab — preserved from W22 F8.1 ProfileCard logic
// ============================================================================
function ProfileTab({ user }: { user: AuthenticatedUser | null }) {
  const t = useTranslations('Settings');
  const initials = computeInitials(user?.preferredUsername);
  const username = user?.preferredUsername ?? '—';
  const role = 'Workspace Admin';
  const sessionLine = user
    ? user.isMock
      ? t('sessionMockAuth')
      : t('sessionEntra')
    : t('signingIn');

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{t('profileTitle')}</h3>
      </div>
      <div
        className="card-body"
        style={{ display: 'flex', gap: 16, alignItems: 'center' }}
      >
        <div className="avatar avatar-lg" aria-hidden="true">
          {initials}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 15, fontWeight: 600 }}>{username}</div>
          <div className="text-sm muted">{role}</div>
          <div
            className="text-xs muted mono"
            style={{ marginTop: 4 }}
            title={user ? `oid ${user.oid} · tid ${user.tid}` : undefined}
          >
            {sessionLine}
          </div>
        </div>
        <DisabledAffordance
          variant="p1-strict"
          reason={t('editProfileReason')}
          tier2Trigger={t('editProfileTier2')}
        >
          <button className="btn btn-secondary btn-sm" disabled>
            {t('editProfile')}
            <span className="badge badge-muted" style={{ marginLeft: 6 }}>
              Tier 2
            </span>
          </button>
        </DisabledAffordance>
      </div>
    </div>
  );
}

// ============================================================================
// AppearanceTab — preserved from W22 F8.1 AppearanceCard logic
// ============================================================================
function AppearanceTab({
  mounted,
  resolvedTheme,
  setTheme,
}: {
  mounted: boolean;
  resolvedTheme: string | null;
  setTheme: (theme: string) => void;
}) {
  const t = useTranslations('Settings');
  const isLight = mounted && resolvedTheme === 'light';
  const isDark = mounted && resolvedTheme === 'dark';

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">{t('appearanceTitle')}</h3>
      </div>
      <div className="card-body">
        <div className="row" style={{ padding: '4px 0' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, fontSize: 13.5 }}>
              {t('themeLabel')}
            </div>
            <div className="text-xs muted">{t('themeDesc')}</div>
          </div>
          <div className="seg" role="tablist" aria-label={t('themePreferenceAria')}>
            <button
              type="button"
              role="tab"
              className="seg-btn"
              data-active={isLight}
              aria-selected={isLight}
              onClick={() => setTheme('light')}
            >
              {t('themeLight')}
            </button>
            <button
              type="button"
              role="tab"
              className="seg-btn"
              data-active={isDark}
              aria-selected={isDark}
              onClick={() => setTheme('dark')}
            >
              {t('themeDark')}
            </button>
          </div>
        </div>
        <div className="hr" />
        <div className="row" style={{ padding: '4px 0' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, fontSize: 13.5 }}>
              {t('densityLabel')}
            </div>
            <div className="text-xs muted">{t('densityDesc')}</div>
          </div>
          <DisabledAffordance
            variant="p1-strict"
            reason={t('densityReason')}
            tier2Trigger={t('densityTier2')}
          >
            <div className="seg" aria-label={t('densityDisabledAria')}>
              <button
                type="button"
                className="seg-btn"
                disabled
                data-active={true}
              >
                {t('densityComfortable')}
              </button>
              <button type="button" className="seg-btn" disabled>
                {t('densityCompact')}
              </button>
            </div>
          </DisabledAffordance>
        </div>
        <div className="hr" />
        <div className="row" style={{ padding: '4px 0' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 500, fontSize: 13.5 }}>
              {t('languageLabel')}
            </div>
            <div className="text-xs muted">{t('languageDesc')}</div>
          </div>
          <DisabledAffordance
            variant="p1-strict"
            reason={t('languageReason')}
            tier2Trigger={t('languageTier2')}
          >
            <select className="select" disabled aria-label={t('languageSelectAria')}>
              <option>{t('languageOptionEnglish')}</option>
            </select>
          </DisabledAffordance>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// AccountTab — preserved Sign-out + Rotate session + Audit log surface (F5)
// ============================================================================
function AccountTab({ onSignOut }: { onSignOut: () => void }) {
  const t = useTranslations('Settings');
  return (
    <div className="col" style={{ gap: 16 }}>
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">{t('sessionTitle')}</h3>
        </div>
        <div className="card-body" style={{ display: 'flex', gap: 8 }}>
          <DisabledAffordance
            variant="p1-strict"
            reason={t('rotateReason')}
            tier2Trigger={t('rotateTier2')}
          >
            <button className="btn btn-secondary btn-sm" disabled>
              <RefreshCw size={13} aria-hidden="true" /> {t('rotateSession')}
              <span className="badge badge-muted" style={{ marginLeft: 6 }}>
                Tier 2
              </span>
            </button>
          </DisabledAffordance>
          <div className="spacer" />
          <button
            type="button"
            className="btn btn-destructive btn-sm"
            onClick={onSignOut}
          >
            <LogOut size={13} aria-hidden="true" /> {t('signOut')}
          </button>
        </div>
      </div>

      {/* F5 audit log preview surface — promoted from F4 deferral. */}
      <SettingsAuditLog />

      {/* DangerZone — Tier 2 disabled affordance (mockup line 842-870). */}
      <div className="card">
        <div className="card-header">
          <h3
            className="card-title"
            style={{ color: 'oklch(var(--destructive))' }}
          >
            {t('dangerZoneTitle')}
          </h3>
        </div>
        <div className="card-body">
          <DisabledAffordance
            variant="p1-strict"
            reason={t('deleteReason')}
            tier2Trigger={t('deleteTier2')}
          >
            <button className="btn btn-destructive btn-sm" disabled>
              {t('deleteAccount')}
              <span className="badge badge-muted" style={{ marginLeft: 6 }}>
                Tier 2
              </span>
            </button>
          </DisabledAffordance>
        </div>
      </div>
    </div>
  );
}

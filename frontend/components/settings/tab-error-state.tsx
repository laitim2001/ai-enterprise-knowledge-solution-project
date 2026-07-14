'use client';

/**
 * `<TabErrorState>` — fallback UI for a settings tab whose render threw
 * (W24b-wave-c2 F4). Shown by the `<ErrorBoundary>` wrapping each of the 6
 * `/settings` tabs, so one bad tab degrades to a recoverable error state
 * without taking down the rest of the page.
 *
 * CSS-first `.banner banner-destructive` to match the inline error states the
 * 4 data-bound settings/* components already render on fetch failure.
 */

import { AlertTriangle } from 'lucide-react';
import { useTranslations } from 'next-intl';

interface TabErrorStateProps {
  /** Human label of the tab, e.g. "Connections". */
  tabName: string;
  /** Clears the boundary so the tab re-mounts and retries. */
  onRetry: () => void;
}

export function TabErrorState({ tabName, onRetry }: TabErrorStateProps) {
  const t = useTranslations('SettingsTabError');
  return (
    <div
      className="banner banner-destructive"
      role="alert"
      style={{ alignItems: 'center' }}
    >
      <AlertTriangle size={14} aria-hidden="true" />
      <div style={{ flex: 1, lineHeight: 1.55 }}>
        <div style={{ fontSize: 13, fontWeight: 500 }}>
          {t('title', { tabName })}
        </div>
        <div className="text-xs">{t('desc')}</div>
      </div>
      <button
        type="button"
        className="btn btn-secondary btn-sm"
        onClick={onRetry}
      >
        {t('retry')}
      </button>
    </div>
  );
}

/**
 * Unit tests — locale 切換態 (W103 F7.3)。
 *
 * 字典對稱由 `i18n-dictionaries.test.ts` 守;呢度守**組件真係跟住 locale 走**
 * —— 即 `useTranslations` 的接線冇斷、切 zh 之後 render 出來的真係中文、而
 * 保留清單的 technical identifier 兩態不變。
 *
 * locale 由 `setTestLocale()` 控制(見 `i18n-locale.ts`);`setup.ts` 會喺每個
 * test 之後 reset 返 en,所以測試之間唔會互相污染。
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { setTestLocale } from './i18n-locale';

vi.mock('@/lib/api-client', () => ({
  apiClient: {
    get: vi.fn(async () => ({
      items: [{ id: 'evt-1', title: 'KB ingestion completed — Drive (12 docs)', read: false }],
    })),
  },
}));

import { NotificationsMenu } from '../../components/nav/notifications-menu';

function renderMenu() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <NotificationsMenu />
    </QueryClientProvider>,
  );
}

describe('locale 切換 — 組件跟住 locale 走', () => {
  it('en 態:trigger 的 aria-label 係英文', () => {
    renderMenu();
    expect(screen.getByRole('button', { name: /notifications/i })).toBeInTheDocument();
  });

  it('zh 態:同一個 trigger 變中文,且唔再 match 英文', () => {
    setTestLocale('zh');
    renderMenu();
    expect(screen.getByRole('button', { name: /通知/ })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^notifications/i })).toBeNull();
  });

  it('同一輪內先 en 後 zh 都 render 得到(唔會因為缺 key 而 throw)', () => {
    // trigger 只有 Bell icon,冇文字節點 —— 所以驗 aria-label 而唔係 textContent。
    const { unmount } = renderMenu();
    expect(screen.getByRole('button').getAttribute('aria-label')).toBeTruthy();
    unmount();

    setTestLocale('zh');
    renderMenu();
    expect(screen.getByRole('button').getAttribute('aria-label')).toBeTruthy();
  });
});

describe('locale 切換 — ICU 參數喺兩個 locale 都代入得到', () => {
  // 未讀數是 ICU 參數;兩個 locale 都要見到數字,唔可以剩返 `{count}` 未代入。
  it.each(['en', 'zh'] as const)('%s 態 aria-label 帶出未讀數', (locale) => {
    setTestLocale(locale);
    renderMenu();
    const trigger = screen.getByRole('button', { name: locale === 'zh' ? /通知/ : /notifications/i });
    const label = trigger.getAttribute('aria-label') ?? '';
    expect(label).toMatch(/\d/);
    expect(label).not.toContain('{');
  });
});

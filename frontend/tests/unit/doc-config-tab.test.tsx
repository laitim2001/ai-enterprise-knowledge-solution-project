/**
 * Unit tests — per-document config tab (W58 / ADR-0051; platform P2b / Gap A UI).
 *
 * Verifies the DocConfigTab surface consuming the W57 per-doc CRUD API:
 *   - renders the scope banner, tuning card, retrieval-entry explainer, config-test
 *   - all-null stored config → every knob shows 繼承 KB (inherit) + save disabled
 *   - overriding answer_detail flips it to 已覆寫 and enables save
 *   - retrieval-entry knobs are NOT editable here (explainer only, per ADR-0050)
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const getMock = vi.fn(async () => ({}) as Record<string, unknown>);
const putMock = vi.fn(async (_kb: string, _doc: string, c: Record<string, unknown>) => c);

vi.mock('@/lib/api/doc-config', () => ({
  docConfigApi: {
    get: (kb: string, doc: string) => getMock(),
    put: (kb: string, doc: string, c: Record<string, unknown>) => putMock(kb, doc, c),
    delete: vi.fn(),
    list: vi.fn(),
  },
}));
vi.mock('@/lib/api/config-test', () => ({
  configTestApi: { run: vi.fn() },
}));
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

import { DocConfigTab } from '../../app/(app)/kb/[id]/docs/[docId]/doc-config-tab';

function renderTab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <DocConfigTab kbId="test-kb" docId="doc-001" kbName="Drive Manuals" />
    </QueryClientProvider>,
  );
}

describe('DocConfigTab (W58 / ADR-0051)', () => {
  it('renders the scope banner, tuning card, retrieval-entry explainer + config-test', async () => {
    renderTab();
    await screen.findByText('此文件度身訂做配置');
    expect(screen.getByText('Per-document 配置')).toBeInTheDocument();
    // retrieval-entry knobs are explainer-only per ADR-0050 (NOT editable here)
    expect(screen.getByText(/檢索入口旋鈕/)).toBeInTheDocument();
    // per-doc scoped config-test panel
    expect(screen.getByText('試跑(此文件 scope)')).toBeInTheDocument();
  });

  it('all-null stored config → answer_detail inherits KB + save disabled', async () => {
    renderTab();
    await screen.findByText('此文件度身訂做配置');
    // 3-way answer_detail seg with 繼承 KB active
    const inheritBtn = screen.getByRole('button', { name: '繼承 KB' });
    expect(inheritBtn).toHaveAttribute('data-active', 'true');
    // nothing overridden → 儲存到此文件 disabled
    const saveBtn = screen.getByRole('button', { name: /^儲存到此文件/ });
    expect(saveBtn).toBeDisabled();
  });

  it('overriding answer_detail flips to 已覆寫 and enables save', async () => {
    renderTab();
    await screen.findByText('此文件度身訂做配置');
    fireEvent.click(screen.getByRole('button', { name: 'detailed' }));
    // override badge appears + save enabled
    expect(screen.getAllByText('已覆寫').length).toBeGreaterThan(0);
    expect(screen.getByText('1 項已覆寫')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^儲存到此文件/ })).not.toBeDisabled();
  });

  it('saving PUTs the per-doc config with the overridden answer_detail', async () => {
    renderTab();
    await screen.findByText('此文件度身訂做配置');
    fireEvent.click(screen.getByRole('button', { name: 'detailed' }));
    fireEvent.click(screen.getByRole('button', { name: /^儲存到此文件/ }));
    await waitFor(() => expect(putMock).toHaveBeenCalledTimes(1));
    const body = putMock.mock.calls[0][2];
    expect(body.answer_detail).toBe('detailed');
  });
});

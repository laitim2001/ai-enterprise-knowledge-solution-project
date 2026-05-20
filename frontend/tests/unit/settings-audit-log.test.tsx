/**
 * Unit tests — `<SettingsAuditLog>` filter + cursor pagination (W24b-wave-c2
 * F6 + F7.2).
 *
 * F6: action_type filter re-fetches; the cursor-based "Load more" button
 * appends an older page rather than replacing it.
 * F7.2: the since date filter re-fetches; a filter matching nothing shows the
 * filtered empty-state message.
 *
 * Mocks `adminApi` so the component's `listAuditLog` fetch is controllable.
 */

import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';

vi.mock('@/lib/api/admin', () => ({
  adminApi: { listAuditLog: vi.fn() },
}));

import { adminApi, type AuditAction, type AuditLogEntry } from '@/lib/api/admin';
import { SettingsAuditLog } from '@/components/settings/settings-audit-log';

const listAuditLog = vi.mocked(adminApi.listAuditLog);

function makeEntry(
  id: number,
  action: AuditAction = 'connection_patch',
): AuditLogEntry {
  return {
    id,
    actor: null,
    action,
    resource: `admin_provider_configs/p_${id}`,
    payload: null,
    created_at: '2026-05-20T00:00:00Z',
  };
}

describe('SettingsAuditLog filter + pagination (W24b F6)', () => {
  beforeEach(() => {
    listAuditLog.mockReset();
  });

  it('renders fetched audit rows on mount', async () => {
    listAuditLog.mockResolvedValue({
      entries: [makeEntry(2), makeEntry(1)],
      next_cursor: null,
    });
    render(<SettingsAuditLog />);
    await waitFor(() => {
      expect(
        screen.getByText('admin_provider_configs/p_2'),
      ).toBeInTheDocument();
    });
    expect(listAuditLog).toHaveBeenCalledWith({
      limit: 10,
      action_type: undefined,
      since: undefined,
    });
  });

  it('re-fetches with action_type when the filter changes', async () => {
    listAuditLog.mockResolvedValue({ entries: [], next_cursor: null });
    render(<SettingsAuditLog />);
    await waitFor(() => expect(listAuditLog).toHaveBeenCalledTimes(1));
    fireEvent.change(screen.getByLabelText('Action'), {
      target: { value: 'identity_patch' },
    });
    await waitFor(() => {
      expect(listAuditLog).toHaveBeenCalledWith({
        limit: 10,
        action_type: 'identity_patch',
        since: undefined,
      });
    });
  });

  it('"Load more" appends the next page using the cursor', async () => {
    listAuditLog
      .mockResolvedValueOnce({ entries: [makeEntry(20)], next_cursor: 20 })
      .mockResolvedValueOnce({ entries: [makeEntry(10)], next_cursor: null });
    render(<SettingsAuditLog />);
    await waitFor(() => {
      expect(
        screen.getByText('admin_provider_configs/p_20'),
      ).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole('button', { name: /load more/i }));
    await waitFor(() => {
      expect(
        screen.getByText('admin_provider_configs/p_10'),
      ).toBeInTheDocument();
    });
    // First page still shown — appended, not replaced.
    expect(screen.getByText('admin_provider_configs/p_20')).toBeInTheDocument();
    expect(listAuditLog).toHaveBeenLastCalledWith({
      limit: 10,
      action_type: undefined,
      since: undefined,
      cursor: 20,
    });
  });

  it('re-fetches with the since param when the date filter changes', async () => {
    listAuditLog.mockResolvedValue({ entries: [], next_cursor: null });
    render(<SettingsAuditLog />);
    await waitFor(() => expect(listAuditLog).toHaveBeenCalledTimes(1));
    fireEvent.change(screen.getByLabelText('Since'), {
      target: { value: '2026-05-01' },
    });
    await waitFor(() => {
      expect(listAuditLog).toHaveBeenCalledWith({
        limit: 10,
        action_type: undefined,
        since: '2026-05-01',
      });
    });
  });

  it('shows the filtered empty-state message when a filter matches nothing', async () => {
    listAuditLog.mockResolvedValue({ entries: [], next_cursor: null });
    render(<SettingsAuditLog />);
    // Unfiltered empty state first.
    expect(
      await screen.findByText(/no audit entries yet/i),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Action'), {
      target: { value: 'identity_patch' },
    });
    expect(
      await screen.findByText(/no audit entries match the current filter/i),
    ).toBeInTheDocument();
  });
});

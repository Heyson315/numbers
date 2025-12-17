import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../apiClient';

// Basic mock of fetch
beforeEach(() => {
  vi.restoreAllMocks();
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({}) }));
});

describe('apiClient', () => {
  it('reconcileTransactions sends both bank and book arrays', async () => {
    await api.reconcileTransactions(
      [{ amount: 100, vendor: 'A', date: '2024-01-01' }],
      [{ amount: 200, vendor: 'B', date: '2024-01-02' }],
      'test-token'
    );
    const call = (fetch as any).mock.calls[0];
    expect(call[0]).toBe('/api/reconcile/transactions');
    const body = JSON.parse(call[1].body);
    expect(body.bank_transactions).toHaveLength(1);
    expect(body.book_transactions).toHaveLength(1);
  });

  it('includes Authorization header when token provided', async () => {
    await api.processInvoice({ invoice_text: 'Sample invoice text 12345' }, 'abc123');
    const { headers } = (fetch as any).mock.calls[0][1];
    expect(headers.Authorization).toBe('Bearer abc123');
  });

  it('throws on non-ok response', async () => {
    (fetch as any).mockResolvedValueOnce({ ok: false, status: 500, text: () => Promise.resolve('Server error') });
    await expect(
      api.processInvoice({ invoice_text: 'Bad invoice text 12345' }, 'abc123')
    ).rejects.toThrow(/HTTP 500/);
  });

  it('handles 400 error response', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      statusText: 'Bad Request',
      text: () => Promise.resolve('Invalid data'),
    }));

    await expect(
      api.reconcileTransactions(
        [{ amount: 100, vendor: 'A', date: '2024-01-01' }],
        [{ amount: 100, vendor: 'A', date: '2024-01-01' }],
        'test-token'
      )
    ).rejects.toThrow(/HTTP 400/);
  });

  it('handles 500 error response with error message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      text: () => Promise.resolve('Server error'),
    }));

    await expect(
      api.reconcileTransactions(
        [{ amount: 100, vendor: 'A', date: '2024-01-01' }],
        [{ amount: 100, vendor: 'A', date: '2024-01-01' }],
        'test-token'
      )
    ).rejects.toThrow(/HTTP 500/);
  });
});

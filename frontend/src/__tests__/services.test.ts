import { describe, it, expect, vi } from 'vitest';
import { api } from '../apiClient';

// Basic smoke tests for service layer functions (delegation correctness)

describe('api client delegation', () => {
  it('throws on non-200 responses', async () => {
    const originalFetch = global.fetch;
    global.fetch = vi.fn().mockResolvedValue({ ok: false, status: 500, text: () => Promise.resolve('error') });
    await expect(api.health()).rejects.toThrow(/HTTP 500/);
    global.fetch = originalFetch;
  });

  it('passes through JSON on success', async () => {
    const payload = { status: 'ok', version: '1.0.0' };
    const originalFetch = global.fetch;
    global.fetch = vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(payload) });
    const result = await api.health();
    expect(result).toEqual(payload);
    global.fetch = originalFetch;
  });

  it('throws on network error', async () => {
    const originalFetch = global.fetch;
    global.fetch = vi.fn().mockRejectedValue(new Error('Network failure'));
    await expect(api.health()).rejects.toThrow(/Network failure/);
    global.fetch = originalFetch;
  });

  it('handles 400 error with error message', async () => {
    const originalFetch = global.fetch;
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      text: () => Promise.resolve('Bad Request: Invalid data'),
    });
    await expect(api.health()).rejects.toThrow(/HTTP 400/);
    global.fetch = originalFetch;
  });

  it('propagates error messages from API', async () => {
    const originalFetch = global.fetch;
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      text: () => Promise.resolve('Bad Request: Invalid input'),
    });
    await expect(
      api.processInvoice({ invoice_text: '' }, 'test-token')
    ).rejects.toThrow(/HTTP 400/);
    global.fetch = originalFetch;
  });
});

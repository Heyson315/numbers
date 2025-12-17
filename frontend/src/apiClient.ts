import { LoginRequest, TokenResponse, InvoiceRequest, ProcessInvoiceResponse, ExpenseRequest, ExpenseCategorizeResponse, DetectAnomaliesRequest, DetectAnomaliesResponse, ReconcileResponse, AuditLogResponse } from './types';

const BASE_URL = '/api';

function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const mergedHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined || {})
  };
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: mergedHeaders,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  login: (data: LoginRequest) => request<TokenResponse>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  processInvoice: (data: InvoiceRequest, token: string) => request<ProcessInvoiceResponse>('/invoice/process', { method: 'POST', body: JSON.stringify(data), headers: authHeaders(token) }),
  categorizeExpense: (data: ExpenseRequest, token: string) => request<ExpenseCategorizeResponse>('/expense/categorize', { method: 'POST', body: JSON.stringify(data), headers: authHeaders(token) }),
  detectAnomalies: (data: DetectAnomaliesRequest, token: string) => request<DetectAnomaliesResponse>('/audit/detect-anomalies', { method: 'POST', body: JSON.stringify(data), headers: authHeaders(token) }),
  generateAuditReport: (data: DetectAnomaliesRequest, token: string) => request<any>('/audit/generate-report', { method: 'POST', body: JSON.stringify(data), headers: authHeaders(token) }),
  reconcileTransactions: (bank: any[], book: any[], token: string) => request<ReconcileResponse>('/reconcile/transactions', { method: 'POST', body: JSON.stringify({ bank_transactions: bank, book_transactions: book }), headers: authHeaders(token) }),
  getAuditLog: (token: string, start?: string, end?: string) => request<AuditLogResponse>(`/security/audit-log${start || end ? `?${new URLSearchParams({ ...(start && { start_date: start }), ...(end && { end_date: end }) }).toString()}` : ''}`, { headers: authHeaders(token) }),
  health: () => request<{ status: string; version: string }>('/health'),
};

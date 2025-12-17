import { useAuth } from './useAuth';
import { useMemo } from 'react';
import { api } from '../apiClient';

export function useApi() {
  const { token } = useAuth();
  return useMemo(() => ({
    login: api.login,
    processInvoice: (data: any) => api.processInvoice(data, token!),
    categorizeExpense: (data: any) => api.categorizeExpense(data, token!),
    detectAnomalies: (data: any) => api.detectAnomalies(data, token!),
    generateAuditReport: (data: any) => api.generateAuditReport(data, token!),
    reconcileTransactions: (bank: any[], book: any[]) => api.reconcileTransactions(bank, book, token!),
    getAuditLog: (start?: string, end?: string) => api.getAuditLog(token!, start, end),
    health: api.health
  }), [token]);
}

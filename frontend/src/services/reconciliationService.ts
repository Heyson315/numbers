import { api } from '../apiClient';

export async function reconcile(bank: any[], book: any[], token: string) {
  return api.reconcileTransactions(bank, book, token);
}

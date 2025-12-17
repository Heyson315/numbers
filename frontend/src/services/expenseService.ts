import { api } from '../apiClient';
import { ExpenseRequest, ExpenseCategorizeResponse } from '../types';

export async function categorizeExpense(data: ExpenseRequest, token: string): Promise<ExpenseCategorizeResponse> {
  return api.categorizeExpense(data, token);
}

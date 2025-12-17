import { api } from '../apiClient';
import { InvoiceRequest, ProcessInvoiceResponse } from '../types';

export async function submitInvoice(data: InvoiceRequest, token: string): Promise<ProcessInvoiceResponse> {
  return api.processInvoice(data, token);
}

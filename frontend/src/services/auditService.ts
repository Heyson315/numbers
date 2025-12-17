import { api } from '../apiClient';
import { AuditLogResponse } from '../types';

export async function getAuditLog(token: string, start?: string, end?: string): Promise<AuditLogResponse> {
  return api.getAuditLog(token, start, end);
}

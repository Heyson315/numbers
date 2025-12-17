// Shared TypeScript types mapping backend models
export interface LoginRequest { username: string; password: string; }
export interface TokenResponse { access_token: string; token_type: string; expires_in: number; }

export interface InvoiceRequest { invoice_text: string; vendor_name?: string; }
export interface InvoiceData {
  invoice_id: string;
  vendor_name?: string;
  total_amount?: number;
  invoice_date?: string;
  confidence_score?: number;
  [key: string]: any;
}
export interface ProcessInvoiceResponse {
  invoice: InvoiceData;
  is_valid: boolean;
  validation_errors: string[];
  category: string;
  gl_account: string;
}

export interface ExpenseRequest { description: string; vendor?: string; amount: number; date: string; }
export interface ExpenseCategorizeResponse {
  category: string;
  confidence: number;
  gl_account: string;
  needs_review: boolean;
}

export interface TransactionRecord { amount: number; vendor: string; date: string; [key: string]: any; }
export interface DetectAnomaliesRequest { transactions: TransactionRecord[]; }
export interface DetectAnomaliesResponse {
  total_transactions: number;
  anomalies_detected: number;
  anomalies: any[];
  potential_duplicates: any[];
  summary: { anomaly_rate: number; highest_risk_score: number; };
}

export interface ReconcileMatch { status: string; bank?: any; book?: any; score?: number; }
export interface ReconcileResponse {
  total_bank_transactions: number;
  total_book_transactions: number;
  matched: number;
  unmatched_bank: number;
  unmatched_book: number;
  match_rate: number;
  matches: ReconcileMatch[];
}

export interface AuditLogEntry { timestamp: string; user_id: string; action: string; resource: string; status?: string; [key: string]: any; }
export interface AuditLogResponse { total_entries: number; entries: AuditLogEntry[]; }

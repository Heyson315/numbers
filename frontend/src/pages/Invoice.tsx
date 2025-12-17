import React, { useState } from 'react';
import { api } from '../apiClient';
import { useAuth } from '../AuthContext';
import type { ProcessInvoiceResponse } from '../types';

const Invoice: React.FC = () => {
  const { token } = useAuth();
  const [text, setText] = useState('ACME Corp\nInvoice #INV-2024-001\nDate: 01/15/2024\nTotal: $1,250.00');
  const [result, setResult] = useState<ProcessInvoiceResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleProcess() {
    if (!token) return;
    setLoading(true); setError(null);
    try {
      const data = await api.processInvoice({ invoice_text: text }, token);
      setResult(data);
    } catch (e: any) { setError(e.message); }
    finally { setLoading(false); }
  }

  return (
    <div>
      <h2>Invoice Processing</h2>
      <textarea rows={8} value={text} onChange={e => setText(e.target.value)} />
      <div>
        <button onClick={handleProcess} disabled={loading}>{loading ? 'Processing...' : 'Process'}</button>
      </div>
      {error && <div className="error">{error}</div>}
      {result && (
        <pre className="result">{JSON.stringify(result, null, 2)}</pre>
      )}
    </div>
  );
};
export default Invoice;

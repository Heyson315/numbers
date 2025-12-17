import React, { useState } from 'react';
import { api } from '../apiClient';
import { useAuth } from '../AuthContext';
import type { AuditLogResponse } from '../types';

const Audit: React.FC = () => {
  const { token } = useAuth();
  const [log, setLog] = useState<AuditLogResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function fetchLog() {
    if (!token) return;
    setLoading(true); setError(null);
    try {
      const data = await api.getAuditLog(token);
      setLog(data);
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  return (
    <div>
      <h2>Audit Log</h2>
      <button onClick={fetchLog} disabled={loading}>{loading ? 'Loading...' : 'Load Audit Log'}</button>
      {error && <div className="error">{error}</div>}
      {log && <pre className="result">{JSON.stringify(log, null, 2)}</pre>}
    </div>
  );
};
export default Audit;

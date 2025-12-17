import React, { useState } from 'react';
import { api } from '../apiClient';
import { useAuth } from '../AuthContext';
import type { DetectAnomaliesResponse } from '../types';

const Anomaly: React.FC = () => {
  const { token } = useAuth();
  const transactions = [{ amount: 100, vendor: 'A', date: '2024-01-15' }, { amount: 5000, vendor: 'C', date: '2024-01-18' }];
  const [result, setResult] = useState<DetectAnomaliesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleDetect() {
    if (!token) return;
    setLoading(true); setError(null);
    try {
      const data = await api.detectAnomalies({ transactions }, token);
      setResult(data);
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  return (
    <div>
      <h2>Anomaly Detection</h2>
      <p>Using sample transactions. Extend UI for editing later.</p>
      <button onClick={handleDetect} disabled={loading}>{loading ? 'Detecting...' : 'Detect Anomalies'}</button>
      {error && <div className="error">{error}</div>}
      {result && <pre className="result">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
};
export default Anomaly;

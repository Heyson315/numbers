import React, { useState } from 'react';
import { api } from '../apiClient';
import { useAuth } from '../AuthContext';
import type { ExpenseCategorizeResponse } from '../types';

const Expense: React.FC = () => {
  const { token } = useAuth();
  const [description, setDescription] = useState('Microsoft 365 subscription');
  const [vendor, setVendor] = useState('Microsoft');
  const [amount, setAmount] = useState(150);
  const [date, setDate] = useState('2024-01-15');
  const [result, setResult] = useState<ExpenseCategorizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCategorize() {
    if (!token) return;
    setLoading(true); setError(null);
    try {
      const data = await api.categorizeExpense({ description, vendor, amount, date }, token);
      setResult(data);
    } catch (e: any) { setError(e.message); } finally { setLoading(false); }
  }

  return (
    <div>
      <h2>Expense Categorization</h2>
      <input value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" />
      <input value={vendor} onChange={e => setVendor(e.target.value)} placeholder="Vendor" />
      <input type="number" value={amount} onChange={e => setAmount(parseFloat(e.target.value))} placeholder="Amount" />
      <input value={date} onChange={e => setDate(e.target.value)} placeholder="Date" />
      <div><button onClick={handleCategorize} disabled={loading}>{loading ? 'Categorizing...' : 'Categorize'}</button></div>
      {error && <div className="error">{error}</div>}
      {result && <pre className="result">{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
};
export default Expense;

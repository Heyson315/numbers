import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export const Navbar: React.FC = () => {
  const { token, logout, role } = useAuth();
  return (
    <nav style={{ display: 'flex', gap: '1rem', padding: '0.75rem', borderBottom: '1px solid #ddd' }}>
      <Link to="/">Dashboard</Link>
      <Link to="/invoice">Invoice</Link>
      <Link to="/expense">Expense</Link>
      <Link to="/anomaly">Anomalies</Link>
      <Link to="/audit">Audit</Link>
      {role === 'admin' && <span style={{ marginLeft: 'auto', fontWeight: 'bold' }}>Admin</span>}
      {token ? (
        <button onClick={logout} style={{ marginLeft: 'auto' }}>Logout</button>
      ) : (
        <Link to="/login" style={{ marginLeft: 'auto' }}>Login</Link>
      )}
    </nav>
  );
};

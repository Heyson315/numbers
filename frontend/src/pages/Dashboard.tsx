import React from 'react';
import { useAuth } from '../AuthContext';
import { Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const { username, logout } = useAuth();
  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome {username}</p>
      <nav className="grid">
        <Link to="/invoice">Invoice Processing</Link>
        <Link to="/expense">Expense Categorization</Link>
        <Link to="/anomaly">Anomaly Detection</Link>
        <Link to="/audit">Audit Logs</Link>
      </nav>
      <button onClick={logout}>Logout</button>
    </div>
  );
};
export default Dashboard;

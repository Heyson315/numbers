import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './AuthContext';
import { ProtectedRoute } from './ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Invoice from './pages/Invoice';
import Expense from './pages/Expense';
import Anomaly from './pages/Anomaly';
import Audit from './pages/Audit';

const App: React.FC = () => (
  <AuthProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        <Route path="/invoice" element={<ProtectedRoute><Invoice /></ProtectedRoute>} />
        <Route path="/expense" element={<ProtectedRoute><Expense /></ProtectedRoute>} />
        <Route path="/anomaly" element={<ProtectedRoute><Anomaly /></ProtectedRoute>} />
        <Route path="/audit" element={<ProtectedRoute><Audit /></ProtectedRoute>} />
      </Routes>
    </BrowserRouter>
  </AuthProvider>
);

export default App;

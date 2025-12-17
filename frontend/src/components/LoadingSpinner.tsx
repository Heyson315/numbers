import React from 'react';

export const LoadingSpinner: React.FC<{ label?: string }> = ({ label = 'Loading...' }) => (
  <div role="status" style={{ padding: '1rem', textAlign: 'center' }}>
    <div style={{ width: 32, height: 32, border: '4px solid #ccc', borderTopColor: '#1976d2', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto' }} />
    <p style={{ fontSize: '0.9rem', color: '#555' }}>{label}</p>
    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
  </div>
);

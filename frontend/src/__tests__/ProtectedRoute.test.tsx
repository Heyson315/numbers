import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider, AuthContext } from '../AuthContext';
import { ProtectedRoute } from '../ProtectedRoute';
import React from 'react';

// NOTE: Initial auth state has no token, so should redirect to /login

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('redirects unauthenticated user to login', () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<ProtectedRoute><div data-testid="secret">Secret</div></ProtectedRoute>} />
            <Route path="/login" element={<div data-testid="login">Login</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    );
    expect(screen.queryByTestId('secret')).toBeNull();
    expect(screen.getByTestId('login')).toBeInTheDocument();
  });

  it('renders children for authenticated user', () => {
    // Create a mock auth context value with token
    const mockAuthValue = {
      token: 'fake-token',
      role: 'accountant',
      username: 'testuser',
      login: vi.fn(),
      logout: vi.fn(),
    };

    render(
      <AuthContext.Provider value={mockAuthValue}>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<ProtectedRoute><div data-testid="secret">Secret</div></ProtectedRoute>} />
            <Route path="/login" element={<div data-testid="login">Login</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    );
    
    expect(screen.getByTestId('secret')).toBeInTheDocument();
    expect(screen.queryByTestId('login')).not.toBeInTheDocument();
  });
});

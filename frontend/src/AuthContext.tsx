import React, { createContext, useContext, useState, useCallback } from 'react';
import { api } from './apiClient';
import type { TokenResponse } from './types';

interface AuthState {
  token: string | null;
  role: string | null;
  username: string | null;
}

interface AuthContextValue extends AuthState {
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({ token: null, role: null, username: null });

  const login = useCallback(async (username: string, password: string) => {
    const res: TokenResponse = await api.login({ username, password });
    // Demo token has implicit role accountant; in production decode JWT
    setState({ token: res.access_token, role: 'accountant', username });
  }, []);

  const logout = useCallback(() => setState({ token: null, role: null, username: null }), []);

  return <AuthContext.Provider value={{ ...state, login, logout }}>{children}</AuthContext.Provider>;
};

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

// Explicit export of context for external hooks (e.g. custom useAuth wrappers)
export { AuthContext };

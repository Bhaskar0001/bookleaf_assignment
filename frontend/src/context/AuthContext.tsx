import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../types';
import { apiRequest } from '../lib/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  switchUser: (email: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('bookleaf_token'));
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await apiRequest<{ success: boolean; data: any }>('/auth/me');
        const u = res.data;
        setUser({
          id: String(u.id),
          email: u.email,
          role: u.role,
          fullName: u.fullName || u.full_name || '',
          authorId: u.authorId || u.author_id,
        });
      } catch (err) {
        localStorage.removeItem('bookleaf_token');
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [token]);

  const login = async (email: string, password: string) => {
    const res = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const access_token = res.data.access_token;
    localStorage.setItem('bookleaf_token', access_token);
    setToken(access_token);
    const u = res.data.user;
    setUser({
      id: String(u.id),
      email: u.email,
      role: u.role,
      fullName: u.fullName || u.full_name || '',
      authorId: u.authorId || u.author_id,
    });
  };

  const logout = () => {
    localStorage.removeItem('bookleaf_token');
    setToken(null);
    setUser(null);
  };

  const switchUser = async (email: string, password: string) => {
    logout();
    await login(email, password);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, switchUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

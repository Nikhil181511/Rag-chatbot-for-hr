import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, AuthResponse } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isHR: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, role: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('hr_rag_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('hr_rag_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const verifyUser = async () => {
      const storedToken = localStorage.getItem('hr_rag_token');
      if (storedToken) {
        try {
          const freshUser = await api.getMe();
          setUser(freshUser);
          localStorage.setItem('hr_rag_user', JSON.stringify(freshUser));
        } catch (e) {
          // Token expired or invalid
          console.warn('Session expired, logging out', e);
          logout();
        }
      }
      setIsLoading(false);
    };

    verifyUser();
  }, []);

  const handleAuthSuccess = (data: AuthResponse) => {
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('hr_rag_token', data.access_token);
    localStorage.setItem('hr_rag_user', JSON.stringify(data.user));
  };

  const login = async (email: string, password: string) => {
    const data = await api.login(email, password);
    handleAuthSuccess(data);
  };

  const register = async (email: string, password: string, fullName: string, role: string) => {
    const data = await api.register(email, password, fullName, role);
    handleAuthSuccess(data);
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('hr_rag_token');
    localStorage.removeItem('hr_rag_user');
  };

  const isHR = user?.role === 'hr';
  const isAuthenticated = !!token && !!user;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated,
        isHR,
        login,
        register,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

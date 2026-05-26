'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/utils/api';
import { User } from '@/types/Auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('accessToken');
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const { data } = await api.get<User>('/auth/me');
        setUser(data);
      } catch (error) {
        console.error('Token invalid', error);
        logout();
      } finally {
        setIsLoading(false);
      }
    };
    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);

    const { data } = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    localStorage.setItem('accessToken', data.access_token);
    const userRes = await api.get<User>('/auth/me');
    setUser(userRes.data);
    router.push('/');
  };

  const signup = async (email: string, password: string, full_name: string) => {
    await api.post('/auth/register', {
      email,
      password,
      full_name,
    });

    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('accessToken');
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};

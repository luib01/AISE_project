// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import apiClient from '../api/apiClient.ts';
import { AUTH_VALIDATE_ENDPOINT, AUTH_LOGOUT_ENDPOINT } from '../api/endpoints.ts';

interface User {
  user_id: string;
  username: string;
  english_level: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string, userData: User) => void;
  logout: () => Promise<void>;
  updateUser: (userData: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check if user is authenticated on app load
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          // Set auth header for validation request
          const response = await apiClient.get(AUTH_VALIDATE_ENDPOINT, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          
          if (response.data.success) {
            setUser(response.data.data);
            // Set default auth header for future requests
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          } else {
            localStorage.removeItem('auth_token');
          }
        } catch (error) {
          localStorage.removeItem('auth_token');
          delete apiClient.defaults.headers.common['Authorization'];
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = (token: string, userData: User) => {
    localStorage.setItem('auth_token', token);
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    setUser(userData);
  };

  const logout = async () => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      try {
        await apiClient.post(AUTH_LOGOUT_ENDPOINT, {}, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
      } catch (error) {
        // Ignore logout errors, just clear local state
        console.error('Logout error:', error);
      }
    }
    
    localStorage.removeItem('auth_token');
    delete apiClient.defaults.headers.common['Authorization'];
    setUser(null);
  };

  const updateUser = (userData: Partial<User>) => {
    setUser(prevUser => prevUser ? { ...prevUser, ...userData } : null);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    updateUser
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

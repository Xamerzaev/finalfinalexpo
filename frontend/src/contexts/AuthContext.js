import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    // Проверяем токен при загрузке
    const checkToken = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          api.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          const response = await api.get('/auth/me');
          setCurrentUser(response.data);
          setToken(storedToken);
        } catch (error) {
          console.error('Token validation error:', error);
          localStorage.removeItem('token');
          delete api.defaults.headers.common['Authorization'];
        }
      }
      setLoading(false);
    };

    checkToken();
  }, []);

  // Функция для входа в систему
  const login = async (username, password) => {
    const response = await api.post('/auth/login', {
      username,
      password
    });
    
    const { access_token, user } = response.data;
    localStorage.setItem('token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    
    setToken(access_token);
    setCurrentUser(user);
    
    return user;
  };

  // Функция для регистрации
  const register = async (username, email, password) => {
    const response = await api.post('/auth/register', {
      username,
      email,
      password
    });
    
    return response.data;
  };

  // Функция для выхода из системы
  const logout = () => {
    localStorage.removeItem('token');
    delete api.defaults.headers.common['Authorization'];
    setToken(null);
    setCurrentUser(null);
  };

  const value = {
    currentUser,
    token,
    login,
    register,
    logout,
    isAuthenticated: !!token
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import { migrateSessionStorage } from '../utils/sessionMigration';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Run migration on mount (before session validation)
  useEffect(() => {
    const migrationResult = migrateSessionStorage();
    if (migrationResult.migrated) {
      console.info('✓ Session migrated to encrypted cookies');
    } else if (migrationResult.reason === 'error') {
      console.error('✗ Session migration failed:', migrationResult.error);
    }
  }, []); // Run once on mount

  const validateSession = useCallback(async () => {
    if (!api.isAuthenticated()) {
      setLoading(false);
      return;
    }

    try {
      const response = await api.validateSession();
      if (response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
      } else {
        setUser(null);
      }
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    validateSession();
  }, [validateSession]);

  const register = async ({ fullName, email, password, phoneNumber }) => {
    setError(null);
    try {
      const response = await api.register({ fullName, email, password, phoneNumber });
      if (response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      }
      throw new Error(response.message || 'Registration failed');
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const login = async ({ email, password }) => {
    setError(null);
    try {
      const response = await api.login({ email, password });
      if (response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      }
      throw new Error(response.message || 'Login failed');
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
    }
  };

  const updateProfile = async (data) => {
    setError(null);
    try {
      const response = await api.updateProfile(data);
      if (response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      }
      throw new Error(response.message || 'Update failed');
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const changePassword = async ({ currentPassword, newPassword }) => {
    setError(null);
    try {
      const response = await api.changePassword({ currentPassword, newPassword });
      if (response.status === 'success') {
        return { success: true };
      }
      throw new Error(response.message || 'Password change failed');
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const value = {
    user,
    loading,
    error,
    isAuthenticated: !!user,
    isAdmin: String(user?.role || user?.Role || '').trim().toLowerCase() === 'admin',
    register,
    login,
    logout,
    updateProfile,
    changePassword,
    refreshUser: validateSession,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

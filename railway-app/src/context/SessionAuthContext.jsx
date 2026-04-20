/**
 * SessionAuthContext - Session-Based Authentication Context
 * Smart Railway Ticketing System
 */
import React, { useState, useEffect, useRef, useContext, createContext, useCallback } from 'react';
import sessionApi, { clearCsrfToken } from '../services/sessionApi';

const SessionAuthContext = createContext(null);

export function SessionAuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionValidated, setSessionValidated] = useState(false);
  const pendingRequestsRef = useRef(new Set());

  // Determine if user is admin
  const isAdmin = (() => {
    if (!user) return false;
    const role = String(user.Role || user.role || '').trim().toLowerCase();
    const userType = String(user.type || user.user_type || '').trim().toLowerCase();
    const adminAccess = !!user?.permissions?.admin_access;
    return adminAccess || (userType === 'employee' && role === 'admin');
  })();

  /**
   * Validate current session with backend.
   */
  const validateSession = useCallback(async () => {
    try {
      const response = await sessionApi.validateSession();
      if (response && response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
      } else {
        setUser(null);
      }
    } catch (err) {
      setUser(null);
    } finally {
      setLoading(false);
      setSessionValidated(true);
    }
  }, []);

  useEffect(() => {
    validateSession();
  }, [validateSession]);

  const login = async (credentials) => {
    setError(null);
    try {
      // Passenger login should not hit employee endpoints first; use the user login route directly.
      const response = await sessionApi.userLogin(credentials);
      if (response && response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      }
      throw new Error(response?.message || 'Login failed');
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const logout = async () => {
    try {
      await sessionApi.logout();
    } finally {
      setUser(null);
      clearCsrfToken();
    }
  };

  const initiateRegistration = async (data) => {
    setError(null);
    try {
      const response = await sessionApi.initiateRegistration(data || {});
      if (response && response.status === 'success') {
        return { success: true, ...response.data };
      }
      throw new Error(response?.message || 'Registration initiation failed');
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    }
  };

  const verifyRegistration = async (email, otp, registration = {}) => {
    setError(null);
    if (!email) return { success: false, error: 'Email is required' };
    const key = `verify_${email}`;
    if (pendingRequestsRef.current.has(key)) return { success: false, error: 'Request pending' };
    pendingRequestsRef.current.add(key);
    try {
      const response = await sessionApi.verifyRegistration(email, otp, registration);
      if (response && response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      }
      throw new Error(response?.message || 'Verification failed');
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      pendingRequestsRef.current.delete(key);
    }
  };

  const resendOtp = async (email) => {
    try {
      return await sessionApi.resendOtp(email);
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const updateProfile = async (data) => {
    try {
      const response = await sessionApi.updateProfile(data || {});
      if (response && response.status === 'success' && response.data?.user) {
        setUser(response.data.user);
        return { success: true, user: response.data.user };
      }
      throw new Error(response?.message || 'Update failed');
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const value = {
    user,
    loading,
    error,
    sessionValidated,
    permissions: user?.permissions || {},
    isAuthenticated: !!user,
    isAdmin,
    login,
    logout,
    initiateRegistration,
    verifyRegistration,
    resendOtp,
    updateProfile,
    refreshUser: validateSession,
    clearError: () => setError(null),
  };

  return (
    <SessionAuthContext.Provider value={value}>
      {children}
    </SessionAuthContext.Provider>
  );
}

export const useSessionAuth = () => {
  const context = useContext(SessionAuthContext);
  if (!context) throw new Error('useSessionAuth must be used within SessionAuthProvider');
  return context;
};

export const useAuth = useSessionAuth;

export default SessionAuthContext;

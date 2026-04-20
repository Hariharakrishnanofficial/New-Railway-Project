import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import sessionApi from '../services/sessionApi';
import { useSessionAuth } from './SessionAuthContext';

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { isAuthenticated } = useSessionAuth();
  const [unreadCount, setUnreadCount] = useState(0);
  const [recentNotifications, setRecentNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  const resetState = useCallback(() => {
    setUnreadCount(0);
    setRecentNotifications([]);
    setError(null);
    setLoading(false);
  }, []);

  const refreshUnreadCount = useCallback(async ({ days = 30 } = {}) => {
    if (!isAuthenticated) {
      setUnreadCount(0);
      return 0;
    }

    try {
      const response = await sessionApi.getUnreadNotificationCount({ days });
      const count = Number(response?.data?.unread || 0);
      setUnreadCount(Number.isFinite(count) ? count : 0);
      return Number.isFinite(count) ? count : 0;
    } catch (err) {
      if (err?.status !== 401) {
        setError(err?.message || 'Failed to load notification count');
      }
      return 0;
    }
  }, [isAuthenticated]);

  const fetchRecent = useCallback(async ({ days = 30, limit = 10 } = {}) => {
    if (!isAuthenticated) {
      setRecentNotifications([]);
      return [];
    }

    setLoading(true);
    setError(null);
    try {
      const response = await sessionApi.getNotifications({ days, limit, offset: 0 });
      const items = response?.data?.items || [];
      setRecentNotifications(Array.isArray(items) ? items : []);
      return Array.isArray(items) ? items : [];
    } catch (err) {
      if (err?.status !== 401) {
        setError(err?.message || 'Failed to load notifications');
      }
      setRecentNotifications([]);
      return [];
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  const markRead = useCallback(async (id) => {
    try {
      await sessionApi.markNotificationRead(id);
      setRecentNotifications((prev) => prev.map((item) => (
        item.id === id ? { ...item, isRead: true } : item
      )));
      await refreshUnreadCount({ days: 30 });
      return true;
    } catch (err) {
      if (err?.status !== 401) {
        setError(err?.message || 'Failed to mark notification as read');
      }
      return false;
    }
  }, [refreshUnreadCount]);

  const markAllRead = useCallback(async ({ days = 30 } = {}) => {
    try {
      await sessionApi.markAllNotificationsRead({ days });
      setRecentNotifications((prev) => prev.map((item) => ({ ...item, isRead: true })));
      await refreshUnreadCount({ days });
      return true;
    } catch (err) {
      if (err?.status !== 401) {
        setError(err?.message || 'Failed to mark all notifications as read');
      }
      return false;
    }
  }, [refreshUnreadCount]);

  const deleteNotification = useCallback(async (id) => {
    try {
      await sessionApi.deleteNotification(id);
      setRecentNotifications((prev) => prev.filter((item) => item.id !== id));
      await refreshUnreadCount({ days: 30 });
      return true;
    } catch (err) {
      if (err?.status !== 401) {
        setError(err?.message || 'Failed to delete notification');
      }
      return false;
    }
  }, [refreshUnreadCount]);

  useEffect(() => {
    if (!isAuthenticated) {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
      resetState();
      return;
    }

    refreshUnreadCount({ days: 30 });
    pollRef.current = setInterval(() => {
      if (document.visibilityState === 'visible') {
        refreshUnreadCount({ days: 30 });
      }
    }, 30000);

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [isAuthenticated, refreshUnreadCount, resetState]);

  const value = useMemo(() => ({
    unreadCount,
    recentNotifications,
    loading,
    error,
    refreshUnreadCount,
    fetchRecent,
    markRead,
    markAllRead,
    deleteNotification,
  }), [unreadCount, recentNotifications, loading, error, refreshUnreadCount, fetchRecent, markRead, markAllRead, deleteNotification]);

  return (
    <NotificationContext.Provider value={value}>
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
}


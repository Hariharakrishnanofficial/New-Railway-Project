import React, { useEffect, useState } from 'react';
import sessionApi from '../services/sessionApi';
import { useNotifications } from '../context/NotificationContext';
import { useToast } from '../context/ToastContext';

function formatTime(value) {
  if (!value) return '';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

export default function NotificationsPage() {
  const toast = useToast();
  const { refreshUnreadCount } = useNotifications();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const load = async (nextOffset = 0, nextUnreadOnly = unreadOnly) => {
    setLoading(true);
    try {
      const response = await sessionApi.getNotifications({
        days: 30,
        limit,
        offset: nextOffset,
        unreadOnly: nextUnreadOnly,
      });
      const data = response?.data || {};
      setItems(Array.isArray(data.items) ? data.items : []);
      setHasMore(Boolean(data.hasMore));
      setOffset(nextOffset);
    } catch (err) {
      if (err?.status !== 401) {
        toast.error(err?.message || 'Failed to load notifications');
      }
      setItems([]);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load(0, unreadOnly);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unreadOnly]);

  const handleMarkRead = async (id) => {
    try {
      await sessionApi.markNotificationRead(id);
      setItems((prev) => prev.map((item) => (item.id === id ? { ...item, isRead: true } : item)));
      await refreshUnreadCount({ days: 30 });
    } catch (err) {
      if (err?.status !== 401) {
        toast.error(err?.message || 'Failed to mark notification as read');
      }
    }
  };

  const handleDelete = async (id) => {
    try {
      await sessionApi.deleteNotification(id);
      setItems((prev) => prev.filter((item) => item.id !== id));
      await refreshUnreadCount({ days: 30 });
    } catch (err) {
      if (err?.status !== 401) {
        toast.error(err?.message || 'Failed to delete notification');
      }
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await sessionApi.markAllNotificationsRead({ days: 30 });
      setItems((prev) => prev.map((item) => ({ ...item, isRead: true })));
      await refreshUnreadCount({ days: 30 });
      toast.success('Marked all as read');
    } catch (err) {
      if (err?.status !== 401) {
        toast.error(err?.message || 'Failed to mark all as read');
      }
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, gap: 12, flexWrap: 'wrap' }}>
        <h2 style={{ margin: 0, color: 'var(--text-primary)' }}>Notifications</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-secondary)', fontSize: 13 }}>
            <input type="checkbox" checked={unreadOnly} onChange={(e) => setUnreadOnly(e.target.checked)} />
            Unread only
          </label>
          <button
            type="button"
            onClick={handleMarkAllRead}
            style={{
              border: '1px solid var(--border)',
              background: 'var(--bg-inset)',
              color: 'var(--text-primary)',
              borderRadius: 8,
              padding: '8px 12px',
              cursor: 'pointer',
              fontSize: 13,
            }}
          >
            Mark all as read
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ color: 'var(--text-muted)' }}>Loading notifications...</div>
      ) : items.length === 0 ? (
        <div style={{ color: 'var(--text-muted)' }}>No notifications found.</div>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {items.map((item) => (
            <div key={item.id} style={{ border: '1px solid var(--border)', background: 'var(--bg-elevated)', borderRadius: 12, padding: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: 12 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    {!item.isRead && <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-blue)' }} />}
                    <strong style={{ color: 'var(--text-primary)' }}>{item.title}</strong>
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 6 }}>{item.message}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: 12, marginTop: 8 }}>{formatTime(item.createdAt)}</div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {!item.isRead && (
                    <button
                      type="button"
                      onClick={() => handleMarkRead(item.id)}
                      style={{ border: '1px solid var(--border)', background: 'var(--bg-inset)', color: 'var(--text-primary)', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', fontSize: 12 }}
                    >
                      Mark read
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => handleDelete(item.id)}
                    style={{ border: '1px solid #ef444440', background: '#2a0f0f', color: '#f87171', borderRadius: 8, padding: '6px 10px', cursor: 'pointer', fontSize: 12 }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 16 }}>
        <button
          type="button"
          disabled={offset <= 0 || loading}
          onClick={() => load(Math.max(0, offset - limit), unreadOnly)}
          style={{ border: '1px solid var(--border)', background: 'var(--bg-inset)', color: 'var(--text-primary)', borderRadius: 8, padding: '8px 12px', cursor: 'pointer', opacity: offset <= 0 ? 0.5 : 1 }}
        >
          Previous
        </button>
        <button
          type="button"
          disabled={!hasMore || loading}
          onClick={() => load(offset + limit, unreadOnly)}
          style={{ border: '1px solid var(--border)', background: 'var(--bg-inset)', color: 'var(--text-primary)', borderRadius: 8, padding: '8px 12px', cursor: 'pointer', opacity: !hasMore ? 0.5 : 1 }}
        >
          Next
        </button>
      </div>
    </div>
  );
}


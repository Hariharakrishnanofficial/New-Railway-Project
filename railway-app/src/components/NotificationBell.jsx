import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotifications } from '../context/NotificationContext';

function formatTime(value) {
  if (!value) return '';
  try {
    return new Date(value).toLocaleString();
  } catch {
    return String(value);
  }
}

export default function NotificationBell({ compact = false }) {
  const navigate = useNavigate();
  const {
    unreadCount,
    recentNotifications,
    loading,
    fetchRecent,
    markRead,
    markAllRead,
  } = useNotifications();
  const [open, setOpen] = useState(false);

  const badgeText = useMemo(() => {
    if (!unreadCount) return '';
    return unreadCount > 99 ? '99+' : String(unreadCount);
  }, [unreadCount]);

  const toggleOpen = async () => {
    const next = !open;
    setOpen(next);
    if (next) {
      await fetchRecent({ days: 30, limit: 10 });
    }
  };

  const handleItemClick = async (item) => {
    if (!item?.isRead) {
      await markRead(item.id);
    }
    setOpen(false);
    if (item?.actionUrl) {
      const target = String(item.actionUrl).replace(/^#/, '');
      navigate(target || '/notifications');
      return;
    }
    navigate('/notifications');
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        type="button"
        onClick={toggleOpen}
        style={{
          width: compact ? 34 : 38,
          height: compact ? 34 : 38,
          borderRadius: '50%',
          border: '1px solid var(--border)',
          background: 'var(--bg-inset)',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}
        aria-label="Notifications"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2a2 2 0 0 1-.6 1.4L4 17h5" />
          <path d="M9 17a3 3 0 0 0 6 0" />
        </svg>
        {badgeText && (
          <span
            style={{
              position: 'absolute',
              top: -6,
              right: -6,
              minWidth: 18,
              height: 18,
              borderRadius: 9,
              background: '#ef4444',
              color: '#fff',
              fontSize: 11,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 4px',
            }}
          >
            {badgeText}
          </span>
        )}
      </button>

      {open && (
        <div
          style={{
            position: 'absolute',
            right: 0,
            top: compact ? 38 : 42,
            width: 340,
            maxWidth: '90vw',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border)',
            borderRadius: 12,
            boxShadow: 'var(--shadow-md)',
            zIndex: 200,
            overflow: 'hidden',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', borderBottom: '1px solid var(--border)' }}>
            <strong style={{ fontSize: 14 }}>Notifications</strong>
            <button
              type="button"
              onClick={async () => {
                await markAllRead({ days: 30 });
                await fetchRecent({ days: 30, limit: 10 });
              }}
              style={{
                border: 'none',
                background: 'none',
                color: 'var(--accent-blue)',
                cursor: 'pointer',
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              Mark all read
            </button>
          </div>

          <div style={{ maxHeight: 360, overflowY: 'auto' }}>
            {loading ? (
              <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: 13 }}>Loading...</div>
            ) : recentNotifications.length === 0 ? (
              <div style={{ padding: 16, color: 'var(--text-muted)', fontSize: 13 }}>No notifications in last 30 days.</div>
            ) : (
              recentNotifications.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleItemClick(item)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    border: 'none',
                    background: 'none',
                    padding: '12px 14px',
                    borderBottom: '1px solid var(--border)',
                    cursor: 'pointer',
                  }}
                >
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    {!item.isRead && <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-blue)' }} />}
                    <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>{item.title}</span>
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.4 }}>{item.message}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>{formatTime(item.createdAt)}</div>
                </button>
              ))
            )}
          </div>

          <div style={{ padding: 10, borderTop: '1px solid var(--border)', textAlign: 'center' }}>
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                navigate('/notifications');
              }}
              style={{
                border: 'none',
                background: 'none',
                color: 'var(--accent-blue)',
                cursor: 'pointer',
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              View all
            </button>
          </div>
        </div>
      )}
    </div>
  );
}


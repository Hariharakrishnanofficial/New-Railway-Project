/**
 * Admin Dashboard - Overview statistics and quick actions.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';
import PermissionGate from '../../components/PermissionGate';

const ICON_MAP = {
  users: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  train: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="4" y="3" width="16" height="16" rx="2" />
      <path d="M4 11h16" />
      <path d="M12 3v8" />
      <circle cx="8" cy="15" r="1" />
      <circle cx="16" cy="15" r="1" />
    </svg>
  ),
  ticket: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
    </svg>
  ),
  dollar: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="1" x2="12" y2="23" />
      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
    </svg>
  ),
  station: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
      <circle cx="12" cy="10" r="3" />
    </svg>
  ),
  refresh: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 2v6h-6" />
      <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
      <path d="M3 22v-6h6" />
      <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
    </svg>
  ),
};

function Icon({ name, size = 24 }) {
  const icon = ICON_MAP[name];
  if (!icon) return null;
  return <span style={{ width: size, height: size, display: 'inline-flex' }}>{icon}</span>;
}

const styles = {
  page: {
    padding: 0,
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    color: 'var(--text-primary, #fff)',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: 'var(--text-muted, #6b7280)',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
    gap: 20,
    marginBottom: 32,
  },
  card: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 12,
    padding: 20,
    border: '1px solid var(--border, #2a2a2a)',
  },
  statCard: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
  },
  statInfo: {
    flex: 1,
  },
  statLabel: {
    fontSize: 13,
    color: 'var(--text-muted, #6b7280)',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 700,
    color: 'var(--text-primary, #fff)',
    marginBottom: 4,
  },
  statSubtext: {
    fontSize: 12,
    color: 'var(--text-secondary, #9ca3af)',
  },
  statIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: '#fff',
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 600,
    color: 'var(--text-primary, #fff)',
    marginBottom: 16,
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '12px 16px',
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted, #6b7280)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid var(--border, #2a2a2a)',
  },
  td: {
    padding: '14px 16px',
    fontSize: 14,
    color: 'var(--text-secondary, #9ca3af)',
    borderBottom: '1px solid var(--border, #2a2a2a)',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: 20,
    fontSize: 12,
    fontWeight: 500,
  },
  badgeSuccess: {
    background: 'rgba(34, 197, 94, 0.15)',
    color: '#22c55e',
  },
  badgeWarning: {
    background: 'rgba(234, 179, 8, 0.15)',
    color: '#eab308',
  },
  badgeDanger: {
    background: 'rgba(239, 68, 68, 0.15)',
    color: '#ef4444',
  },
  quickActions: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 12,
  },
  quickAction: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '14px 16px',
    background: 'var(--bg-inset, #252525)',
    borderRadius: 10,
    border: '1px solid var(--border, #2a2a2a)',
    color: 'var(--text-secondary, #9ca3af)',
    textDecoration: 'none',
    fontSize: 14,
    fontWeight: 500,
    transition: 'all 0.2s',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
    color: 'var(--text-muted, #6b7280)',
  },
  error: {
    padding: 20,
    background: 'rgba(239, 68, 68, 0.1)',
    borderRadius: 8,
    color: '#ef4444',
    textAlign: 'center',
  },
  refreshBtn: {
    padding: '8px 16px',
    background: 'var(--accent-blue, #3b82f6)',
    color: '#fff',
    border: 'none',
    borderRadius: 8,
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
};

export default function DashboardPage() 
{
  const [stats, setStats] = useState(null);
  const [recentBookings, setRecentBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, bookingsRes] = await Promise.all([
        api.get('/overview/stats').catch(() => ({ data: null })),
        api.get('/overview/recent-bookings').catch(() => ({ data: null })),
      ]);

      if (statsRes.data?.status === 'success') {
        setStats(statsRes.data.data);
      }
      if (bookingsRes.data?.status === 'success') {
        setRecentBookings(bookingsRes.data.data || []);
      }
    } catch (err) {
      setError(err.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  const getStatusBadge = (status) => {
    const statusLower = (status || '').toLowerCase();
    if (statusLower === 'confirmed') return { ...styles.badge, ...styles.badgeSuccess };
    if (statusLower === 'cancelled') return { ...styles.badge, ...styles.badgeDanger };
    return { ...styles.badge, ...styles.badgeWarning };
  };

  if (loading) {
    return <div style={styles.loading}>Loading dashboard...</div>;
  }

  if (error) {
    return (
      <div style={styles.error}>
        <p>{error}</p>
        <button onClick={fetchData} style={{ ...styles.refreshBtn, margin: '16px auto 0' }}>
          Retry
        </button>
      </div>
    ); 
  }

  const statCards = [
    {
      label: 'Total Users',
      value: stats?.users?.total || 0,
      subtext: `${stats?.users?.admins || 0} admins`,
      icon: 'users',
      color: 'var(--accent-blue, #3b82f6)',
    },
    {
      label: 'Active Trains',
      value: stats?.trains?.total || 0,
      subtext: `${stats?.trains?.active || 0} running`,
      icon: 'train',
      color: 'var(--accent-green, #22c55e)',
    },
    {
      label: 'Total Bookings',
      value: stats?.bookings?.total || 0,
      subtext: `${stats?.bookings?.today || 0} today`,
      icon: 'ticket',
      color: 'var(--accent-amber, #f59e0b)',
    },
    {
      label: 'Total Revenue',
      value: formatCurrency(stats?.revenue?.total),
      subtext: `${formatCurrency(stats?.revenue?.today)} today`,
      icon: 'dollar',
      color: 'var(--accent-purple, #8b5cf6)',
      isFormatted: true,
    },
    {
      label: 'Stations',
      value: stats?.stations?.total || 0,
      subtext: 'Active stations',
      icon: 'station',
      color: 'var(--accent-pink, #ec4899)',
    },
    {
      label: 'Confirmed',
      value: stats?.bookings?.confirmed || 0,
      subtext: `${stats?.bookings?.cancelled || 0} cancelled`,
      icon: 'ticket',
      color: '#22c55e',
    },
  ];

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={styles.title}>Dashboard</h1>
            <p style={styles.subtitle}>Welcome to the Railway Admin Panel</p>
          </div>
          <button onClick={fetchData} style={styles.refreshBtn}>
            <Icon name="refresh" size={16} />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div style={styles.grid}>
        {statCards.map((stat, index) => (
          <div key={index} style={{ ...styles.card, ...styles.statCard }}>
            <div style={styles.statInfo}>
              <div style={styles.statLabel}>{stat.label}</div>
              <div style={styles.statValue}>
                {stat.isFormatted ? stat.value : stat.value.toLocaleString()}
              </div>
              <div style={styles.statSubtext}>{stat.subtext}</div>
            </div>
            <div style={{ ...styles.statIcon, background: stat.color }}>
              <Icon name={stat.icon} size={24} />
            </div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Quick Actions</h2>
        <div style={styles.quickActions}>
          <PermissionGate module="users" action="view">
            <Link to="/admin/users" style={styles.quickAction}>
              <Icon name="users" size={20} /> Manage Users
            </Link>
          </PermissionGate>
          <PermissionGate module="trains" action="view">
            <Link to="/admin/trains" style={styles.quickAction}>
              <Icon name="train" size={20} /> Manage Trains
            </Link>
          </PermissionGate>
          <PermissionGate module="bookings" action="view">
            <Link to="/admin/bookings" style={styles.quickAction}>
              <Icon name="ticket" size={20} /> View Bookings
            </Link>
          </PermissionGate>
          <PermissionGate module="stations" action="view">
            <Link to="/admin/stations" style={styles.quickAction}>
              <Icon name="station" size={20} /> Manage Stations
            </Link>
          </PermissionGate>
        </div>
      </div>

      {/* Recent Bookings */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Recent Bookings</h2>
        <div style={styles.card}>
          {recentBookings.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 20 }}>
              No recent bookings
            </p>
          ) : (
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>PNR</th>
                  <th style={styles.th}>Route</th>
                  <th style={styles.th}>Date</th>
                  <th style={styles.th}>Fare</th>
                  <th style={styles.th}>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentBookings.slice(0, 5).map((booking, index) => (
                  <tr key={booking.ROWID || index}>
                    <td style={{ ...styles.td, fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                      {booking.PNR || '—'}
                    </td>
                    <td style={styles.td}>
                      {booking.Source_Station || '—'} → {booking.Destination_Station || '—'}
                    </td>
                    <td style={styles.td}>
                      {booking.Journey_Date || '—'}
                    </td>
                    <td style={{ ...styles.td, color: 'var(--text-primary)' }}>
                      {formatCurrency(booking.Total_Fare)}
                    </td>
                    <td style={styles.td}>
                      <span style={getStatusBadge(booking.Booking_Status)}>
                        {booking.Booking_Status || 'Unknown'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

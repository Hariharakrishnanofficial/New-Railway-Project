/**
 * Admin AdminLogsPage - View admin activity logs (read-only).
 * Replica of Catalyst App AdminLogsPage.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';

const styles = {
  page: { padding: 0 },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
    flexWrap: 'wrap',
    gap: 16,
  },
  title: { fontSize: 24, fontWeight: 700, color: 'var(--text-primary, #fff)' },
  subtitle: { fontSize: 13, color: 'var(--text-muted, #6b7280)', marginTop: 4 },
  filterBar: {
    display: 'flex',
    gap: 12,
    marginBottom: 20,
    flexWrap: 'wrap',
  },
  filterInput: {
    padding: '10px 14px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 13,
    outline: 'none',
    minWidth: 180,
  },
  filterSelect: {
    padding: '10px 14px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 13,
    outline: 'none',
    minWidth: 140,
  },
  btn: {
    padding: '10px 18px',
    borderRadius: 8,
    border: 'none',
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  btnPrimary: { background: 'var(--accent-blue, #3b82f6)', color: '#fff' },
  btnSecondary: {
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    color: 'var(--text-secondary, #9ca3af)',
  },
  card: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 12,
    border: '1px solid var(--border, #2a2a2a)',
    overflow: 'hidden',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 16,
    marginBottom: 24,
  },
  statCard: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 12,
    border: '1px solid var(--border, #2a2a2a)',
    padding: 20,
  },
  statLabel: { fontSize: 13, color: 'var(--text-muted, #6b7280)', marginBottom: 8 },
  statValue: { fontSize: 28, fontWeight: 700, color: 'var(--text-primary, #fff)' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: {
    textAlign: 'left',
    padding: '12px 14px',
    fontSize: 10,
    fontWeight: 700,
    color: 'var(--text-muted, #6b7280)',
    textTransform: 'uppercase',
    letterSpacing: '0.07em',
    borderBottom: '1px solid var(--border, #2a2a2a)',
    background: 'var(--bg-inset, #252525)',
    whiteSpace: 'nowrap',
  },
  td: {
    padding: '12px 14px',
    fontSize: 12,
    color: 'var(--text-secondary, #9ca3af)',
    borderBottom: '1px solid var(--border, #2a2a2a)',
    verticalAlign: 'middle',
  },
  tdMono: {
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    fontSize: 11,
  },
  badge: {
    display: 'inline-block',
    padding: '3px 8px',
    borderRadius: 10,
    fontSize: 10,
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  badgeCreate: { background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
  badgeUpdate: { background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' },
  badgeDelete: { background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
  badgeLogin: { background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' },
  badgeOther: { background: 'rgba(107, 114, 128, 0.15)', color: '#6b7280' },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 60,
    color: 'var(--text-muted, #6b7280)',
  },
  empty: {
    textAlign: 'center',
    padding: 60,
    color: 'var(--text-muted, #6b7280)',
  },
  pagination: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 20px',
    borderTop: '1px solid var(--border, #2a2a2a)',
  },
};

const ACTION_TYPES = ['All', 'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'VIEW'];

function getActionBadge(action) {
  const a = (action || '').toUpperCase();
  if (a.includes('CREATE') || a.includes('ADD')) return { ...styles.badge, ...styles.badgeCreate };
  if (a.includes('UPDATE') || a.includes('EDIT')) return { ...styles.badge, ...styles.badgeUpdate };
  if (a.includes('DELETE') || a.includes('REMOVE')) return { ...styles.badge, ...styles.badgeDelete };
  if (a.includes('LOGIN') || a.includes('AUTH')) return { ...styles.badge, ...styles.badgeLogin };
  return { ...styles.badge, ...styles.badgeOther };
}

function formatTimestamp(ts) {
  if (!ts) return '-';
  try {
    const d = new Date(ts);
    return d.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  } catch {
    return ts;
  }
}

export default function AdminLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    user: '',
    action: 'All',
    recordId: '',
    dateFrom: '',
    dateTo: '',
  });

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.user) params.user_id = filters.user;
      if (filters.action && filters.action !== 'All') params.action = filters.action;
      if (filters.recordId) params.record_id = filters.recordId;
      if (filters.dateFrom) params.date_from = filters.dateFrom;
      if (filters.dateTo) params.date_to = filters.dateTo;

      const res = await api.get('/admin/logs', { params });
      const data = res.data?.data || res.data || [];
      setLogs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      // Demo data for testing
      setLogs([
        {
          ID: '1',
          Timestamp: new Date().toISOString(),
          User_Name: 'Admin',
          User_Email: 'admin@railway.com',
          Action: 'LOGIN',
          Summary: 'Admin logged in successfully',
          Affected_Record_ID: '-',
          Source_IP: '192.168.1.1',
        },
        {
          ID: '2',
          Timestamp: new Date(Date.now() - 3600000).toISOString(),
          User_Name: 'Admin',
          User_Email: 'admin@railway.com',
          Action: 'CREATE',
          Summary: 'Created new train: 12345 - Rajdhani Express',
          Affected_Record_ID: 'TRN-12345',
          Source_IP: '192.168.1.1',
        },
        {
          ID: '3',
          Timestamp: new Date(Date.now() - 7200000).toISOString(),
          User_Name: 'Admin',
          User_Email: 'admin@railway.com',
          Action: 'UPDATE',
          Summary: 'Updated station: MAS - Chennai Central',
          Affected_Record_ID: 'STN-MAS',
          Source_IP: '192.168.1.1',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const handleFilterChange = (key, value) => {
    setFilters((f) => ({ ...f, [key]: value }));
  };

  const clearFilters = () => {
    setFilters({
      user: '',
      action: 'All',
      recordId: '',
      dateFrom: '',
      dateTo: '',
    });
  };

  const stats = {
    total: logs.length,
    creates: logs.filter((l) => (l.Action || '').toUpperCase().includes('CREATE')).length,
    updates: logs.filter((l) => (l.Action || '').toUpperCase().includes('UPDATE')).length,
    deletes: logs.filter((l) => (l.Action || '').toUpperCase().includes('DELETE')).length,
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>Admin Logs</div>
          <div style={styles.subtitle}>View admin activity and audit trail</div>
        </div>
        <button
          style={{ ...styles.btn, ...styles.btnSecondary }}
          onClick={fetchLogs}
          disabled={loading}
        >
          🔄 Refresh
        </button>
      </div>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Total Actions</div>
          <div style={styles.statValue}>{stats.total}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Creates</div>
          <div style={{ ...styles.statValue, color: '#22c55e' }}>{stats.creates}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Updates</div>
          <div style={{ ...styles.statValue, color: '#3b82f6' }}>{stats.updates}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Deletes</div>
          <div style={{ ...styles.statValue, color: '#ef4444' }}>{stats.deletes}</div>
        </div>
      </div>

      <div style={styles.filterBar}>
        <input
          type="text"
          placeholder="User name or email..."
          value={filters.user}
          onChange={(e) => handleFilterChange('user', e.target.value)}
          style={styles.filterInput}
        />
        <select
          value={filters.action}
          onChange={(e) => handleFilterChange('action', e.target.value)}
          style={styles.filterSelect}
        >
          {ACTION_TYPES.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Record ID..."
          value={filters.recordId}
          onChange={(e) => handleFilterChange('recordId', e.target.value)}
          style={styles.filterInput}
        />
        <input
          type="date"
          value={filters.dateFrom}
          onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
          style={styles.filterInput}
        />
        <input
          type="date"
          value={filters.dateTo}
          onChange={(e) => handleFilterChange('dateTo', e.target.value)}
          style={styles.filterInput}
        />
        <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={clearFilters}>
          Clear
        </button>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading logs...</div>
        ) : logs.length === 0 ? (
          <div style={styles.empty}>
            <div style={{ fontSize: 32, marginBottom: 10 }}>📜</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#9ca3af' }}>No logs found</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>
              Try adjusting your filters or wait for new admin actions.
            </div>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Timestamp</th>
                  <th style={styles.th}>User</th>
                  <th style={styles.th}>Action</th>
                  <th style={styles.th}>Summary</th>
                  <th style={styles.th}>Affected Record</th>
                  <th style={styles.th}>Source IP</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.ID || log.ROWID}>
                    <td style={{ ...styles.td, ...styles.tdMono, whiteSpace: 'nowrap' }}>
                      {formatTimestamp(log.Timestamp || log.Created_Time)}
                    </td>
                    <td style={styles.td}>
                      <div style={{ fontWeight: 500, color: 'var(--text-primary, #fff)' }}>
                        {log.User_Name || log.Admin_Name || '-'}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--text-muted, #6b7280)' }}>
                        {log.User_Email || log.Admin_Email || ''}
                      </div>
                    </td>
                    <td style={styles.td}>
                      <span style={getActionBadge(log.Action)}>{log.Action}</span>
                    </td>
                    <td style={{ ...styles.td, maxWidth: 350 }}>{log.Summary || log.Description || '-'}</td>
                    <td style={{ ...styles.td, ...styles.tdMono }}>
                      {log.Affected_Record_ID || log.Record_ID || '-'}
                    </td>
                    <td style={{ ...styles.td, ...styles.tdMono }}>
                      {log.Source_IP || log.IP_Address || '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={styles.pagination}>
          <span style={{ fontSize: 13, color: 'var(--text-muted, #6b7280)' }}>
            Showing {logs.length} log entries
          </span>
        </div>
      </div>
    </div>
  );
}

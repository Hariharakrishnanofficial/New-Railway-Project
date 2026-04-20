/**
 * Admin SettingsPage - System settings key-value CRUD.
 * Replica of Catalyst App SettingsPage.
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
  headerActions: { display: 'flex', gap: 12, alignItems: 'center' },
  searchInput: {
    padding: '10px 14px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 14,
    width: 220,
    outline: 'none',
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
  table: { width: '100%', borderCollapse: 'collapse' },
  th: {
    textAlign: 'left',
    padding: '14px 16px',
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted, #6b7280)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid var(--border, #2a2a2a)',
    background: 'var(--bg-inset, #252525)',
  },
  td: {
    padding: '14px 16px',
    fontSize: 14,
    color: 'var(--text-secondary, #9ca3af)',
    borderBottom: '1px solid var(--border, #2a2a2a)',
  },
  tdMono: {
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    fontSize: 13,
    color: 'var(--accent-blue, #3b82f6)',
  },
  actions: { display: 'flex', gap: 8 },
  actionBtn: {
    padding: '6px 10px',
    borderRadius: 6,
    border: 'none',
    fontSize: 12,
    cursor: 'pointer',
    background: 'var(--bg-inset, #252525)',
    color: 'var(--text-secondary, #9ca3af)',
  },
  badge: {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: 12,
    fontSize: 11,
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  badgeActive: { background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
  badgeInactive: { background: 'rgba(107, 114, 128, 0.15)', color: '#6b7280' },
  typeBadge: {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: 12,
    fontSize: 11,
    fontWeight: 600,
    background: 'rgba(139, 92, 246, 0.15)',
    color: '#8b5cf6',
  },
  modal: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  modalContent: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 16,
    width: '100%',
    maxWidth: 550,
    maxHeight: '90vh',
    overflow: 'auto',
    border: '1px solid var(--border, #2a2a2a)',
  },
  modalHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid var(--border, #2a2a2a)',
  },
  modalTitle: { fontSize: 18, fontWeight: 600, color: 'var(--text-primary, #fff)' },
  modalBody: { padding: 24 },
  modalFooter: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 12,
    padding: '16px 24px',
    borderTop: '1px solid var(--border, #2a2a2a)',
  },
  formGroup: { marginBottom: 20 },
  formRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  label: {
    display: 'block',
    fontSize: 13,
    fontWeight: 500,
    color: 'var(--text-secondary, #9ca3af)',
    marginBottom: 8,
  },
  input: {
    width: '100%',
    padding: '10px 14px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 14,
    outline: 'none',
  },
  textarea: {
    width: '100%',
    padding: '10px 14px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 14,
    outline: 'none',
    minHeight: 80,
    resize: 'vertical',
    fontFamily: 'inherit',
  },
  select: {
    width: '100%',
    padding: '10px 14px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 14,
    outline: 'none',
  },
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '12px 14px',
    background: 'var(--bg-inset, #252525)',
    borderRadius: 8,
    cursor: 'pointer',
  },
  error: { color: '#ef4444', fontSize: 12, marginTop: 4 },
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
};

const TYPE_OPTIONS = ['System', 'Booking', 'Fare', 'Notification', 'Security', 'API', 'Other'];

const BLANK_FORM = {
  Type_field: 'System',
  Key: '',
  Value: '',
  Description: '',
  Is_Active: true,
};

export default function SettingsPage() {
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (typeFilter) params.type = typeFilter;
      const res = await api.get('/settings', { params });
      const data = res.data?.data || res.data || [];
      setSettings(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
      // Demo data
      setSettings([
        {
          ROWID: '1',
          Type_field: 'System',
          Key: 'MAX_PASSENGERS_PER_BOOKING',
          Value: '6',
          Description: 'Maximum passengers allowed per booking',
          Is_Active: true,
        },
        {
          ROWID: '2',
          Type_field: 'Booking',
          Key: 'TATKAL_BOOKING_START_TIME',
          Value: '10:00',
          Description: 'Time when Tatkal booking opens daily',
          Is_Active: true,
        },
        {
          ROWID: '3',
          Type_field: 'Fare',
          Key: 'GST_PERCENTAGE',
          Value: '5',
          Description: 'GST percentage applied on ticket fares',
          Is_Active: true,
        },
        {
          ROWID: '4',
          Type_field: 'Security',
          Key: 'SESSION_TIMEOUT_MINUTES',
          Value: '30',
          Description: 'User session timeout in minutes',
          Is_Active: true,
        },
        {
          ROWID: '5',
          Type_field: 'Notification',
          Key: 'ENABLE_SMS_ALERTS',
          Value: 'true',
          Description: 'Enable SMS notifications for bookings',
          Is_Active: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [typeFilter]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  // Extract unique types from settings
  const availableTypes = [...new Set(settings.map((s) => s.Type_field).filter(Boolean))].sort();

  const filtered = settings.filter((s) => {
    const matchSearch =
      (s.Type_field || '').toLowerCase().includes(search.toLowerCase()) ||
      (s.Key || '').toLowerCase().includes(search.toLowerCase()) ||
      (s.Value || '').toLowerCase().includes(search.toLowerCase()) ||
      (s.Description || '').toLowerCase().includes(search.toLowerCase());
    const matchType = !typeFilter || s.Type_field === typeFilter;
    return matchSearch && matchType;
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((f) => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: '' }));
  };

  const validate = () => {
    const e = {};
    if (!form.Type_field) e.Type_field = 'Required';
    if (!form.Key.trim()) e.Key = 'Required';
    if (!form.Value.trim()) e.Value = 'Required';
    return e;
  };

  const openCreate = () => {
    setForm(BLANK_FORM);
    setErrors({});
    setEditRow(null);
    setModal('create');
  };

  const openEdit = (row) => {
    setForm({
      Type_field: row.Type_field || 'System',
      Key: row.Key || '',
      Value: row.Value || '',
      Description: row.Description || '',
      Is_Active: row.Is_Active === true || row.Is_Active === 'true',
    });
    setErrors({});
    setEditRow(row);
    setModal('edit');
  };

  const handleSave = async () => {
    const errs = validate();
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setSaving(true);
    try {
      const payload = { ...form };
      if (modal === 'create') {
        await api.post('/settings', payload);
      } else {
        const id = editRow.ROWID || editRow.Setting_ID;
        await api.put(`/settings/${id}`, payload);
      }
      setModal(null);
      fetchSettings();
    } catch (err) {
      console.error('Save failed:', err);
      setErrors({ _form: err.response?.data?.message || 'Save failed' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete setting "${row.Key}"?`)) return;
    try {
      const id = row.ROWID || row.Setting_ID;
      await api.delete(`/settings/${id}`);
      fetchSettings();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>System Settings</div>
          <div style={styles.subtitle}>Manage application configuration</div>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search settings..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={styles.filterSelect}
          >
            <option value="">All Types</option>
            {(availableTypes.length > 0 ? availableTypes : TYPE_OPTIONS).map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
            + Add Setting
          </button>
        </div>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading settings...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>
            <div style={{ fontSize: 32, marginBottom: 10 }}>⚙️</div>
            <div style={{ fontSize: 14, fontWeight: 600, color: '#9ca3af' }}>No settings found</div>
          </div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Key</th>
                <th style={styles.th}>Value</th>
                <th style={styles.th}>Description</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.ROWID || row.Setting_ID || row.Key}>
                  <td style={styles.td}>
                    <span style={styles.typeBadge}>{row.Type_field}</span>
                  </td>
                  <td style={{ ...styles.td, ...styles.tdMono }}>{row.Key}</td>
                  <td style={styles.td}>
                    <code
                      style={{
                        background: 'var(--bg-inset, #252525)',
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontSize: 13,
                      }}
                    >
                      {row.Value}
                    </code>
                  </td>
                  <td style={{ ...styles.td, maxWidth: 280, color: 'var(--text-muted, #6b7280)' }}>
                    {row.Description || '-'}
                  </td>
                  <td style={styles.td}>
                    <span
                      style={
                        row.Is_Active === true || row.Is_Active === 'true'
                          ? { ...styles.badge, ...styles.badgeActive }
                          : { ...styles.badge, ...styles.badgeInactive }
                      }
                    >
                      {row.Is_Active === true || row.Is_Active === 'true' ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <button style={styles.actionBtn} onClick={() => openEdit(row)}>
                        Edit
                      </button>
                      <button
                        style={{ ...styles.actionBtn, color: '#ef4444' }}
                        onClick={() => handleDelete(row)}
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div style={styles.modalTitle}>
                {modal === 'create' ? 'Add Setting' : 'Edit Setting'}
              </div>
              <button
                style={{ ...styles.actionBtn, fontSize: 18 }}
                onClick={() => setModal(null)}
              >
                ×
              </button>
            </div>
            <div style={styles.modalBody}>
              {errors._form && (
                <div style={{ ...styles.error, marginBottom: 16 }}>{errors._form}</div>
              )}
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Type *</label>
                  <select
                    name="Type_field"
                    value={form.Type_field}
                    onChange={handleChange}
                    style={styles.select}
                  >
                    {TYPE_OPTIONS.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                  {errors.Type_field && <div style={styles.error}>{errors.Type_field}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Key *</label>
                  <input
                    type="text"
                    name="Key"
                    value={form.Key}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., MAX_RETRIES"
                  />
                  {errors.Key && <div style={styles.error}>{errors.Key}</div>}
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Value *</label>
                <input
                  type="text"
                  name="Value"
                  value={form.Value}
                  onChange={handleChange}
                  style={styles.input}
                  placeholder="Setting value"
                />
                {errors.Value && <div style={styles.error}>{errors.Value}</div>}
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Description</label>
                <textarea
                  name="Description"
                  value={form.Description}
                  onChange={handleChange}
                  style={styles.textarea}
                  placeholder="Optional description..."
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.checkbox}>
                  <input
                    type="checkbox"
                    name="Is_Active"
                    checked={form.Is_Active}
                    onChange={handleChange}
                  />
                  <span style={{ color: 'var(--text-primary, #fff)' }}>Active</span>
                </label>
              </div>
            </div>
            <div style={styles.modalFooter}>
              <button
                style={{ ...styles.btn, ...styles.btnSecondary }}
                onClick={() => setModal(null)}
              >
                Cancel
              </button>
              <button
                style={{ ...styles.btn, ...styles.btnPrimary }}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

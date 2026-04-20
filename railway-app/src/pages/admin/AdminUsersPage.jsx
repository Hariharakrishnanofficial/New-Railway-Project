/**
 * Admin Users Page - Manage administrator accounts.
 */
import React, { useState, useEffect, useCallback } from 'react';
import sessionApi from '../../services/sessionApi';

const STATUS_OPTIONS = ['Active', 'Suspended', 'Blocked'];

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
    width: 240,
    outline: 'none',
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
  btnPrimary: {
    background: 'var(--accent-amber, #f59e0b)',
    color: '#000',
  },
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
  badge: {
    display: 'inline-block',
    padding: '4px 10px',
    borderRadius: 20,
    fontSize: 11,
    fontWeight: 500,
  },
  badgeSuccess: { background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
  badgeWarning: { background: 'rgba(234, 179, 8, 0.15)', color: '#eab308' },
  badgeDanger: { background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
  actions: { display: 'flex', gap: 8 },
  actionBtn: {
    padding: '6px 10px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 6,
    color: 'var(--text-muted, #6b7280)',
    fontSize: 12,
    cursor: 'pointer',
  },
  modal: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: 20,
  },
  modalContent: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 16,
    border: '1px solid var(--border, #2a2a2a)',
    width: '100%',
    maxWidth: 500,
    maxHeight: '90vh',
    overflow: 'auto',
  },
  modalHeader: {
    padding: '20px 24px',
    borderBottom: '1px solid var(--border, #2a2a2a)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: { fontSize: 18, fontWeight: 600, color: 'var(--text-primary, #fff)' },
  modalBody: { padding: 24 },
  modalFooter: {
    padding: '16px 24px',
    borderTop: '1px solid var(--border, #2a2a2a)',
    display: 'flex',
    justifyContent: 'flex-end',
    gap: 12,
  },
  formGroup: { marginBottom: 16 },
  formRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  label: {
    display: 'block',
    fontSize: 13,
    fontWeight: 500,
    color: 'var(--text-secondary, #9ca3af)',
    marginBottom: 6,
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
  error: {
    color: '#ef4444',
    fontSize: 12,
    marginTop: 4,
  },
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
  infoBox: {
    padding: 16,
    background: 'rgba(59, 130, 246, 0.1)',
    borderRadius: 8,
    marginBottom: 20,
    fontSize: 13,
    color: 'var(--text-secondary)',
    border: '1px solid rgba(59, 130, 246, 0.2)',
  },
};

function getStatusBadge(status) {
  const s = (status || '').toLowerCase();
  if (s === 'active') return { ...styles.badge, ...styles.badgeSuccess };
  if (s === 'suspended') return { ...styles.badge, ...styles.badgeWarning };
  if (s === 'blocked') return { ...styles.badge, ...styles.badgeDanger };
  return styles.badge;
}

const BLANK_FORM = {
  Full_Name: '',
  Email: '',
  Phone_Number: '',
  Password: '',
  Account_Status: 'Active',
  Address: '',
};

export default function AdminUsersPage() {
  const [admins, setAdmins] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [details, setDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchAdmins = useCallback(async () => {
    setLoading(true);
    try {
      const res = await sessionApi.get('/admin/users');
      const data = res.data?.data || res.data || [];
      const adminList = Array.isArray(data) ? data : (data.data || []);
      setAdmins(adminList);
    } catch (err) {
      console.error('Failed to fetch admin users:', err);
      setAdmins([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAdmins();
  }, [fetchAdmins]);

  const filtered = admins.filter((u) => {
    const s = search.toLowerCase();
    return (
      (u.Full_Name || '').toLowerCase().includes(s) ||
      (u.Email || '').toLowerCase().includes(s)
    );
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: '' }));
  };

  const validate = (isCreate) => {
    const e = {};
    if (!form.Full_Name.trim()) e.Full_Name = 'Required';
    if (!form.Email.trim()) e.Email = 'Required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.Email)) e.Email = 'Invalid email';
    if (isCreate && !form.Password.trim()) e.Password = 'Password required';
    else if (form.Password && form.Password.length < 8) e.Password = 'Min 8 characters';
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
      Full_Name: row.Full_Name || '',
      Email: row.Email || '',
      Phone_Number: row.Phone_Number || '',
      Password: '',
      Account_Status: row.Account_Status || 'Active',
      Address: row.Address || '',
    });
    setErrors({});
    setEditRow(row);
    setModal('edit');
  };

  const openView = async (row) => {
    setErrors({});
    setEditRow(row);
    setDetails(null);
    setDetailsLoading(true);
    setModal('view');
    try {
      const userId = row?.ROWID || row?.ID || row?.id;
      const res = await sessionApi.get(`/admin/users/${userId}`);
      const d = res.data?.data || res.data;
      if (d && typeof d === 'object') {
        // Defense-in-depth: never display password
        delete d.Password;
        delete d.password;
      }
      setDetails(d);
    } catch (err) {
      setErrors({ _api: err.message || 'Failed to load details' });
      setDetails(null);
    } finally {
      setDetailsLoading(false);
    }
  };

  const handleSave = async () => {
    const errs = validate(modal === 'create');
    if (Object.keys(errs).length) {
      setErrors(errs);
      return;
    }
    setSaving(true);
    try {
      const payload = {
        Full_Name: form.Full_Name.trim(),
        Email: form.Email.trim(),
        Phone_Number: form.Phone_Number.trim(),
        Account_Status: form.Account_Status,
        Address: form.Address.trim(),
      };
      if (form.Password) payload.Password = form.Password;

      if (modal === 'create') {
        await sessionApi.post('/admin/users', payload);
      } else {
        const userId = editRow?.ROWID || editRow?.ID || editRow?.id;
        await sessionApi.put(`/admin/users/${userId}`, payload);
      }
      setModal(null);
      fetchAdmins();
    } catch (err) {
      setErrors({ _api: err.message || 'Failed to save' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete admin "${row.Full_Name}"? This cannot be undone.`)) return;
    try {
      const userId = row.ROWID || row.ID || row.id;
      await sessionApi.delete(`/admin/users/${userId}`);
      fetchAdmins();
    } catch (err) {
      alert(err.message || 'Delete failed');
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Admin Users</h1>
          <p style={styles.subtitle}>{admins.length} administrator accounts</p>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search admins..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={fetchAdmins}>
            Refresh
          </button>
          <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
            + Add Admin
          </button>
        </div>
      </div>

      <div style={styles.infoBox}>
        <strong>🛡️ Admin Privileges:</strong> Admin users have full access to manage trains, stations, 
        bookings, users, and system settings. Only create admin accounts for trusted personnel.
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading admin users...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>No admin users found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Email</th>
                <th style={styles.th}>Phone</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((admin) => (
                <tr key={admin.ROWID || admin.ID || admin.Email}>
                  <td style={{ ...styles.td, color: 'var(--text-primary)' }}>
                    {admin.Full_Name || '—'}
                  </td>
                  <td style={styles.td}>{admin.Email || '—'}</td>
                  <td style={{ ...styles.td, fontFamily: 'monospace' }}>
                    {admin.Phone_Number || '—'}
                  </td>
                  <td style={styles.td}>
                    <span style={getStatusBadge(admin.Account_Status)}>
                      {admin.Account_Status || 'Active'}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <button style={styles.actionBtn} onClick={() => openView(admin)}>
                        View
                      </button>
                      <button style={styles.actionBtn} onClick={() => openEdit(admin)}>
                        Edit
                      </button>
                      <button
                        style={{ ...styles.actionBtn, color: '#ef4444' }}
                        onClick={() => handleDelete(admin)}
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
        <div style={styles.pagination}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Showing {filtered.length} of {admins.length}
          </span>
        </div>
      </div>

      {/* Modal */}
      {modal && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>
                {modal === 'create' ? 'Add Admin' : modal === 'edit' ? 'Edit Admin' : 'Admin Details'}
              </h2>
              <button
                onClick={() => setModal(null)}
                style={{ ...styles.btn, ...styles.btnSecondary, padding: '6px 12px' }}
              >
                ✕
              </button>
            </div>

            <div style={styles.modalBody}>
              {errors._api && (
                <div style={{ ...styles.error, marginBottom: 16, padding: 12, background: 'rgba(239,68,68,0.1)', borderRadius: 8 }}>
                  {errors._api}
                </div>
              )}

              {modal === 'view' ? (
                <div>
                  {detailsLoading ? (
                    <div style={styles.loading}>Loading details...</div>
                  ) : !details ? (
                    <div style={styles.empty}>No details available</div>
                  ) : (
                    <div style={{ display: 'grid', gap: 10 }}>
                      {Object.entries(details)
                        .filter(([k]) => {
                          const key = (k || '').toLowerCase();
                          if (key === 'password') return false;
                          if (key === 'rowid') return false;
                          if (key === 'createdtime') return false;
                          if (key === 'modifiedtime') return false;
                          if (key === 'is_active') return false;
                          if (key === 'account_status') return false;
                          return true;
                        })
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([k, v]) => (
                          <div key={k} style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: 12 }}>
                            <div style={{ ...styles.label, marginBottom: 0 }}>{k}</div>
                            <div style={{ color: 'var(--text-primary, #fff)', wordBreak: 'break-word' }}>
                              {v === null || v === undefined || v === '' ? '—' : String(v)}
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Full Name *</label>
                    <input
                      name="Full_Name"
                      value={form.Full_Name}
                      onChange={handleChange}
                      style={styles.input}
                    />
                    {errors.Full_Name && <div style={styles.error}>{errors.Full_Name}</div>}
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Email *</label>
                    <input
                      name="Email"
                      type="email"
                      value={form.Email}
                      onChange={handleChange}
                      style={styles.input}
                    />
                    {errors.Email && <div style={styles.error}>{errors.Email}</div>}
                  </div>
                  <div style={styles.formRow}>
                    <div style={styles.formGroup}>
                      <label style={styles.label}>Phone Number</label>
                      <input
                        name="Phone_Number"
                        value={form.Phone_Number}
                        onChange={handleChange}
                        maxLength={10}
                        style={styles.input}
                      />
                    </div>
                    <div style={styles.formGroup}>
                      <label style={styles.label}>Account Status</label>
                      <select
                        name="Account_Status"
                        value={form.Account_Status}
                        onChange={handleChange}
                        style={styles.select}
                      >
                        {STATUS_OPTIONS.map((s) => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>
                      {modal === 'create' ? 'Password *' : 'Reset Password (optional)'}
                    </label>
                    <input
                      name="Password"
                      type="password"
                      value={form.Password}
                      onChange={handleChange}
                      placeholder={modal === 'edit' ? 'Leave blank to keep current' : ''}
                      style={styles.input}
                    />
                    {errors.Password && <div style={styles.error}>{errors.Password}</div>}
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Address</label>
                    <input name="Address" value={form.Address} onChange={handleChange} style={styles.input} />
                  </div>
                </>
              )}
            </div>

            <div style={styles.modalFooter}>
              <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={() => setModal(null)}>
                {modal === 'view' ? 'Close' : 'Cancel'}
              </button>
              {modal !== 'view' && (
                <button
                  style={{ ...styles.btn, ...styles.btnPrimary }}
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : modal === 'create' ? 'Create Admin' : 'Save Changes'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

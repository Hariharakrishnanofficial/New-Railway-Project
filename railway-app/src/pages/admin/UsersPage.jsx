/**
 * Admin UsersPage - User management CRUD interface.
 */
import React, { useState, useEffect, useCallback } from 'react';
import sessionApi, { getCsrfToken } from '../../services/sessionApi';
import PermissionGate from '../../components/PermissionGate';

const STATUS_OPTIONS = ['Active', 'Suspended', 'Blocked'];
const ROLE_OPTIONS = ['User', 'Admin'];
const ID_PROOF_OPTIONS = ['Aadhaar', 'PAN', 'Passport', 'Driving Licence', 'Voter ID'];

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
    background: 'var(--accent-blue, #3b82f6)',
    color: '#fff',
  },
  btnSecondary: {
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    color: 'var(--text-secondary, #9ca3af)',
  },
  btnDanger: {
    background: 'rgba(239, 68, 68, 0.15)',
    color: '#ef4444',
    border: '1px solid rgba(239, 68, 68, 0.3)',
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
  badgeBlue: { background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' },
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
    maxWidth: 560,
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
  checkbox: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '12px 14px',
    background: 'var(--bg-inset, #252525)',
    borderRadius: 8,
    cursor: 'pointer',
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
};

function getStatusBadge(status) {
  const s = (status || '').toLowerCase();
  if (s === 'active') return { ...styles.badge, ...styles.badgeSuccess };
  if (s === 'suspended') return { ...styles.badge, ...styles.badgeWarning };
  if (s === 'blocked') return { ...styles.badge, ...styles.badgeDanger };
  return styles.badge;
}

function getRoleBadge(role) {
  const r = (role || '').toLowerCase();
  if (r === 'admin') return { ...styles.badge, ...styles.badgeBlue };
  return { ...styles.badge, background: 'rgba(156, 163, 175, 0.15)', color: '#9ca3af' };
}

const BLANK_FORM = {
  Full_Name: '',
  Email: '',
  Phone_Number: '',
  Password: '',
  Role: 'User',
  Account_Status: 'Active',
  Address: '',
  Date_of_Birth: '',
  ID_Proof_Type: '',
  ID_Proof_Number: '',
  Aadhar_Verified: false,
};

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null); // 'create' | 'edit' | 'view'
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await sessionApi.get('/users');
      const payload = res?.data;

      // Expected backend shape: { status: 'success', data: [ { id, fullName, ... } ] }
      // But tolerate older/raw shapes too.
      const rawList = payload?.data?.data || payload?.data || payload || [];
      const list = Array.isArray(rawList) ? rawList : [];

      const normalized = list.map((item) => {
        const row = item?.Users && typeof item.Users === 'object' ? item.Users : item;
        const id = String(row?.id || row?.ROWID || row?.rowid || '').trim();

        const roleRaw = String(row?.role || row?.Role || 'User');
        const roleLower = roleRaw.toLowerCase();
        const roleUi = roleLower === 'admin' || roleLower === 'administrator' || roleRaw === 'ADMIN' ? 'Admin' : 'User';

        const status = row?.accountStatus || row?.Account_Status || 'Active';

        return {
          ROWID: id,
          Full_Name: row?.fullName || row?.Full_Name || '',
          Email: row?.email || row?.Email || '',
          Phone_Number: row?.phoneNumber || row?.Phone_Number || '',
          Role: roleUi,
          Account_Status: status,
          Address: row?.address || row?.Address || '',
          Date_of_Birth: row?.dateOfBirth || row?.Date_of_Birth || '',
          ID_Proof_Type: row?.idProofType || row?.ID_Proof_Type || '',
          ID_Proof_Number: row?.idProofNumber || row?.ID_Proof_Number || '',
          Aadhar_Verified: row?.aadharVerified ?? row?.Aadhar_Verified ?? false,
          Is_Verified: row?.isVerified ?? row?.Is_Verified ?? null,
        };
      });

      setUsers(normalized);
    } catch (err) {
      console.error('Failed to fetch users:', err);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const filtered = users.filter((u) => {
    const s = search.toLowerCase();
    return (
      (u.Full_Name || '').toLowerCase().includes(s) ||
      (u.Email || '').toLowerCase().includes(s) ||
      (u.Phone_Number || '').includes(s)
    );
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((f) => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
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
      Role: row.Role || 'User',
      Account_Status: row.Account_Status || 'Active',
      Address: row.Address || '',
      Date_of_Birth: row.Date_of_Birth?.split('T')[0] || row.Date_of_Birth || '',
      ID_Proof_Type: row.ID_Proof_Type || '',
      ID_Proof_Number: row.ID_Proof_Number || '',
      Aadhar_Verified: row.Aadhar_Verified === true || row.Aadhar_Verified === 'true',
    });
    setErrors({});
    setEditRow(row);
    setModal('edit');
  };

  const openView = (row) => {
    setEditRow(row);
    setModal('view');
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
        // Send both legacy (DB-style) and new (camelCase) keys for compatibility.
        Full_Name: form.Full_Name.trim(),
        Email: form.Email.trim(),
        Phone_Number: form.Phone_Number.trim(),
        Role: form.Role,
        Account_Status: form.Account_Status,
        Address: form.Address.trim(),
        Date_of_Birth: form.Date_of_Birth || undefined,
        ID_Proof_Type: form.ID_Proof_Type || undefined,
        ID_Proof_Number: form.ID_Proof_Number.trim() || undefined,
        Aadhar_Verified: !!form.Aadhar_Verified,

        fullName: form.Full_Name.trim(),
        email: form.Email.trim(),
        phoneNumber: form.Phone_Number.trim(),
        role: form.Role,
        accountStatus: form.Account_Status,
        address: form.Address.trim(),
        dateOfBirth: form.Date_of_Birth || undefined,
        idProofType: form.ID_Proof_Type || undefined,
        idProofNumber: form.ID_Proof_Number.trim() || undefined,
        aadharVerified: !!form.Aadhar_Verified,
      };
      // Backend expects `password` (new) but we also accept `Password` (legacy)
      if (form.Password) payload.password = form.Password;

      if (!getCsrfToken()) {
        await sessionApi.refreshCsrfToken();
      }

      if (modal === 'create') {
        await sessionApi.post('/users', payload);
      } else {
        const userId = editRow?.ROWID || editRow?.ID || editRow?.id;
        await sessionApi.put(`/users/${userId}`, payload);
      }
      setModal(null);
      fetchUsers();
    } catch (err) {
      setErrors({ _api: err.message || 'Failed to save' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete user "${row.Full_Name}"?`)) return;
    try {
      if (!getCsrfToken()) {
        await sessionApi.refreshCsrfToken();
      }
      const userId = row.ROWID || row.ID || row.id;
      await sessionApi.delete(`/users/${userId}`);
      fetchUsers();
    } catch (err) {
      alert(err.message || 'Delete failed');
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Users</h1>
          <p style={styles.subtitle}>{users.length} registered users</p>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search users..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <PermissionGate module="users" action="create">
            <button
              style={{ ...styles.btn, ...styles.btnPrimary }}
              onClick={openCreate}
            >
              + Create User
            </button>
          </PermissionGate>
        </div>
      </div>
      {filtered.length === 0 ? (
        <div style={styles.empty}>No users found</div>
      ) : (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Name</th>
              <th style={styles.th}>Email</th>
              <th style={styles.th}>Phone</th>
              <th style={styles.th}>Role</th>
              <th style={styles.th}>Status</th>
              <th style={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((user) => (
              <tr key={user.ROWID || user.ID || user.Email}>
                <td style={{ ...styles.td, color: 'var(--text-primary)' }}>{user.Full_Name || '—'}</td>
                <td style={styles.td}>{user.Email || '—'}</td>
                <td style={{ ...styles.td, fontFamily: 'monospace' }}>{user.Phone_Number || '—'}</td>
                <td style={styles.td}><span style={getRoleBadge(user.Role)}>{user.Role || 'User'}</span></td>
                <td style={styles.td}><span style={getStatusBadge(user.Account_Status)}>{user.Account_Status || 'Active'}</span></td>
                <td style={styles.td}>
                  <div style={styles.actions}>
                    <button style={styles.actionBtn} onClick={() => openView(user)}>View</button>
                    <PermissionGate module="users" action="edit">
                      <button style={styles.actionBtn} onClick={() => openEdit(user)}>Edit</button>
                    </PermissionGate>
                    <PermissionGate module="users" action="deactivate">
                      <button style={styles.actionBtn} onClick={() => handleDelete(user)}>Delete</button>
                    </PermissionGate>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {/* Modal */}
      {modal && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>
                {modal === 'create' ? 'Add User' : modal === 'edit' ? 'Edit User' : 'User Details'}
              </h2>
              <button
                onClick={() => setModal(null)}
                style={{ ...styles.btn, ...styles.btnSecondary, padding: '6px 12px' }}
              >
                ✕
              </button>
            </div>

            {modal === 'view' ? (
              <div style={styles.modalBody}>
                <div style={{ display: 'grid', gap: 16 }}>
                  <div style={styles.formRow}>
                    <div>
                      <div style={styles.label}>Full Name</div>
                      <div style={{ color: 'var(--text-primary)' }}>{editRow?.Full_Name || '—'}</div>
                    </div>
                    <div>
                      <div style={styles.label}>Email</div>
                      <div style={{ color: 'var(--text-primary)' }}>{editRow?.Email || '—'}</div>
                    </div>
                  </div>
                  <div style={styles.formRow}>
                    <div>
                      <div style={styles.label}>Phone</div>
                      <div style={{ color: 'var(--text-primary)' }}>{editRow?.Phone_Number || '—'}</div>
                    </div>
                    <div>
                      <div style={styles.label}>Role</div>
                      <span style={getRoleBadge(editRow?.Role)}>{editRow?.Role || 'User'}</span>
                    </div>
                  </div>
                  <div style={styles.formRow}>
                    <div>
                      <div style={styles.label}>Status</div>
                      <span style={getStatusBadge(editRow?.Account_Status)}>
                        {editRow?.Account_Status || 'Active'}
                      </span>
                    </div>
                    <div>
                      <div style={styles.label}>Date of Birth</div>
                      <div style={{ color: 'var(--text-primary)' }}>{editRow?.Date_of_Birth || '—'}</div>
                    </div>
                  </div>
                  <div>
                    <div style={styles.label}>Address</div>
                    <div style={{ color: 'var(--text-primary)' }}>{editRow?.Address || '—'}</div>
                  </div>
                  <div style={styles.formRow}>
                    <div>
                      <div style={styles.label}>ID Proof</div>
                      <div style={{ color: 'var(--text-primary)' }}>
                        {editRow?.ID_Proof_Type || '—'} / {editRow?.ID_Proof_Number || '—'}
                      </div>
                    </div>
                    <div>
                      <div style={styles.label}>Aadhar Verified</div>
                      <div style={{ color: 'var(--text-primary)' }}>
                        {editRow?.Aadhar_Verified === true || editRow?.Aadhar_Verified === 'true' ? 'Yes' : 'No'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div style={styles.modalBody}>
                {errors._api && (
                  <div style={{ ...styles.error, marginBottom: 16, padding: 12, background: 'rgba(239,68,68,0.1)', borderRadius: 8 }}>
                    {errors._api}
                  </div>
                )}
                <div style={styles.formRow}>
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
                    <label style={styles.label}>
                      {modal === 'create' ? 'Password *' : 'Reset Password'}
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
                </div>
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Role</label>
                    <select name="Role" value={form.Role} onChange={handleChange} style={styles.select}>
                      {ROLE_OPTIONS.map((r) => (
                        <option key={r} value={r}>{r}</option>
                      ))}
                    </select>
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
                  <label style={styles.label}>Address</label>
                  <input name="Address" value={form.Address} onChange={handleChange} style={styles.input} />
                </div>
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Date of Birth</label>
                    <input
                      name="Date_of_Birth"
                      type="date"
                      value={form.Date_of_Birth}
                      onChange={handleChange}
                      style={styles.input}
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>ID Proof Type</label>
                    <select
                      name="ID_Proof_Type"
                      value={form.ID_Proof_Type}
                      onChange={handleChange}
                      style={styles.select}
                    >
                      <option value="">Select...</option>
                      {ID_PROOF_OPTIONS.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>ID Proof Number</label>
                    <input
                      name="ID_Proof_Number"
                      value={form.ID_Proof_Number}
                      onChange={handleChange}
                      style={styles.input}
                    />
                  </div>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Verification</label>
                    <label style={styles.checkbox}>
                      <input
                        type="checkbox"
                        name="Aadhar_Verified"
                        checked={form.Aadhar_Verified}
                        onChange={handleChange}
                      />
                      <span>Aadhar Verified</span>
                    </label>
                  </div>
                </div>
              </div>
            )}

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
                  {saving ? 'Saving...' : modal === 'create' ? 'Create User' : 'Save Changes'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

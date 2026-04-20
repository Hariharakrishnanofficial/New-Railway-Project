/**
 * Admin AnnouncementsPage - System announcements management.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import PermissionGate from '../../components/PermissionGate';

const TYPE_OPTIONS = ['Info', 'Warning', 'Alert', 'Success', 'Maintenance'];
const TARGET_OPTIONS = ['Both', 'Users', 'Employees'];

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
  announcementsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
  },
  announcementCard: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 12,
    border: '1px solid var(--border, #2a2a2a)',
    padding: 20,
    position: 'relative',
  },
  announcementHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  announcementTitle: {
    fontSize: 16,
    fontWeight: 600,
    color: 'var(--text-primary, #fff)',
  },
  announcementMeta: {
    display: 'flex',
    gap: 12,
    alignItems: 'center',
  },
  announcementContent: {
    fontSize: 14,
    color: 'var(--text-secondary, #9ca3af)',
    lineHeight: 1.6,
    marginBottom: 16,
  },
  announcementFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 16,
    borderTop: '1px solid var(--border, #2a2a2a)',
  },
  announcementInfo: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
  },
  actions: { display: 'flex', gap: 8 },
  actionBtn: {
    padding: '6px 12px',
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
  badgeInfo: { background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' },
  badgeWarning: { background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' },
  badgeAlert: { background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
  badgeSuccess: { background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
  badgeMaintenance: { background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' },
  badgeActive: { background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
  badgeInactive: { background: 'rgba(107, 114, 128, 0.15)', color: '#6b7280' },
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
    maxWidth: 600,
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
    minHeight: 100,
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

function getTypeBadge(type) {
  const t = (type || '').toLowerCase();
  if (t === 'info') return { ...styles.badge, ...styles.badgeInfo };
  if (t === 'warning') return { ...styles.badge, ...styles.badgeWarning };
  if (t === 'alert') return { ...styles.badge, ...styles.badgeAlert };
  if (t === 'success') return { ...styles.badge, ...styles.badgeSuccess };
  if (t === 'maintenance') return { ...styles.badge, ...styles.badgeMaintenance };
  return styles.badge;
}

const BLANK_FORM = {
  Title: '',
  Message: '',
  Announcement_Type: 'Info',
  Target_Audience: 'Both',
  Start_Date: '',
  End_Date: '',
  Is_Active: true,
  Priority: '1',
  Related_Route: '',
  Audience_Roles: '',
};

export default function AnnouncementsPage() {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchAnnouncements = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/announcements');
      setAnnouncements(res.data?.data || res.data || []);
    } catch (err) {
      console.error('Failed to fetch announcements:', err);
      // Use sample data for demo
      setAnnouncements([
        {
          ROWID: '1',
          Title: 'System Maintenance Notice',
          Message: 'Scheduled maintenance on April 5th, 2026 from 2:00 AM to 6:00 AM IST. Booking services will be temporarily unavailable.',
          Announcement_Type: 'Maintenance',
          Target_Audience: 'All Users',
          Start_Date: '2026-04-01',
          End_Date: '2026-04-06',
          Is_Active: true,
          Priority: 1,
          Created_At: '2026-03-30',
        },
        {
          ROWID: '2',
          Title: 'New Routes Added',
          Message: 'We have added 15 new train routes connecting major cities. Book your tickets now!',
          Announcement_Type: 'Info',
          Target_Audience: 'Passengers',
          Start_Date: '2026-03-25',
          End_Date: '2026-04-15',
          Is_Active: true,
          Priority: 2,
          Created_At: '2026-03-25',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnnouncements();
  }, [fetchAnnouncements]);

  const stats = {
    total: announcements.length,
    active: announcements.filter((a) => a.Is_Active).length,
    alerts: announcements.filter((a) => (a.Announcement_Type || '').toLowerCase() === 'alert').length,
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((f) => ({ ...f, [name]: type === 'checkbox' ? checked : value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: '' }));
  };

  const validate = () => {
    const e = {};
    if (!form.Title.trim()) e.Title = 'Required';
    if (!form.Message.trim()) e.Message = 'Required';
    if (!form.Start_Date) e.Start_Date = 'Required';
    return e;
  };

  const openCreate = () => {
    setForm({
      ...BLANK_FORM,
      Start_Date: new Date().toISOString().split('T')[0],
    });
    setErrors({});
    setEditRow(null);
    setModal('create');
  };

  const openEdit = (row) => {
    setForm({
      Title: row.Title || '',
      Message: row.Message || '',
      Announcement_Type: row.Announcement_Type || 'Info',
      Target_Audience: row.Audience_Type || row.Target_Audience || 'Both',
      Start_Date: row.Start_Date?.split('T')[0] || row.Start_Date || '',
      End_Date: row.End_Date?.split('T')[0] || row.End_Date || '',
      Is_Active: row.Is_Active === true || row.Is_Active === 'true',
      Priority: row.Priority || '1',
      Related_Route: row.Related_Route || '',
      Audience_Roles: Array.isArray(row.Audience_Roles)
        ? row.Audience_Roles.join(', ')
        : (row.Audience_Roles || ''),
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
      payload.audienceType = String(form.Target_Audience || 'Both').toLowerCase() === 'users'
        ? 'user'
        : String(form.Target_Audience || 'Both').toLowerCase() === 'employees'
          ? 'employee'
          : 'both';
      const roleTokens = String(form.Audience_Roles || '')
        .split(',')
        .map((x) => x.trim())
        .filter(Boolean);
      payload.audienceRoles = roleTokens;
      if (modal === 'create') {
        await api.post('/announcements', payload);
      } else {
        const id = editRow.ROWID || editRow.Announcement_ID;
        await api.put(`/announcements/${id}`, payload);
      }
      setModal(null);
      fetchAnnouncements();
    } catch (err) {
      console.error('Save failed:', err);
      setErrors({ _form: err.response?.data?.message || 'Save failed' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm('Delete this announcement?')) return;
    try {
      const id = row.ROWID || row.Announcement_ID;
      await api.delete(`/announcements/${id}`);
      fetchAnnouncements();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const toggleActive = async (row) => {
    try {
      const id = row.ROWID || row.Announcement_ID;
      await api.put(`/announcements/${id}`, {
        ...row,
        Is_Active: !row.Is_Active,
      });
      fetchAnnouncements();
    } catch (err) {
      console.error('Toggle failed:', err);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>Announcements</div>
          <div style={styles.subtitle}>Manage system announcements and alerts</div>
        </div>
        <div style={styles.headerActions}>
          <PermissionGate module="announcements" action="create">
            <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
              + New Announcement
            </button>
          </PermissionGate>
        </div>
      </div>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Total</div>
          <div style={styles.statValue}>{stats.total}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Active</div>
          <div style={{ ...styles.statValue, color: '#22c55e' }}>{stats.active}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Alerts</div>
          <div style={{ ...styles.statValue, color: '#ef4444' }}>{stats.alerts}</div>
        </div>
      </div>

      {loading ? (
        <div style={styles.loading}>Loading announcements...</div>
      ) : announcements.length === 0 ? (
        <div style={styles.empty}>No announcements found</div>
      ) : (
        <div style={styles.announcementsList}>
          {announcements.map((ann) => (
            <div key={ann.ROWID || ann.Announcement_ID} style={styles.announcementCard}>
              <div style={styles.announcementHeader}>
                <div style={styles.announcementTitle}>{ann.Title}</div>
                <div style={styles.announcementMeta}>
                  <span style={getTypeBadge(ann.Announcement_Type)}>{ann.Announcement_Type}</span>
                  <span
                    style={
                      ann.Is_Active
                        ? { ...styles.badge, ...styles.badgeActive }
                        : { ...styles.badge, ...styles.badgeInactive }
                    }
                  >
                    {ann.Is_Active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
              <div style={styles.announcementContent}>{ann.Message}</div>
              <div style={styles.announcementFooter}>
                <div style={styles.announcementInfo}>
                  Target: {(ann.Audience_Type || ann.Target_Audience || 'both')} • {ann.Start_Date}
                  {ann.End_Date ? ` to ${ann.End_Date}` : ''}
                </div>
                <div style={styles.actions}>
                  <PermissionGate module="announcements" action="edit">
                    <button
                      style={styles.actionBtn}
                      onClick={() => toggleActive(ann)}
                    >
                      {ann.Is_Active ? 'Deactivate' : 'Activate'}
                    </button>
                  </PermissionGate>
                  <PermissionGate module="announcements" action="edit">
                    <button style={styles.actionBtn} onClick={() => openEdit(ann)}>
                      Edit
                    </button>
                  </PermissionGate>
                  <PermissionGate module="announcements" action="delete">
                    <button
                      style={{ ...styles.actionBtn, color: '#ef4444' }}
                      onClick={() => handleDelete(ann)}
                    >
                      Delete
                    </button>
                  </PermissionGate>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div style={styles.modalTitle}>
                {modal === 'create' ? 'New Announcement' : 'Edit Announcement'}
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
              <div style={styles.formGroup}>
                <label style={styles.label}>Title *</label>
                <input
                  type="text"
                  name="Title"
                  value={form.Title}
                  onChange={handleChange}
                  style={styles.input}
                  placeholder="Announcement title"
                />
                {errors.Title && <div style={styles.error}>{errors.Title}</div>}
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Message *</label>
                <textarea
                  name="Message"
                  value={form.Message}
                  onChange={handleChange}
                  style={styles.textarea}
                  placeholder="Announcement message content..."
                />
                {errors.Message && <div style={styles.error}>{errors.Message}</div>}
              </div>
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Type</label>
                  <select
                    name="Announcement_Type"
                    value={form.Announcement_Type}
                    onChange={handleChange}
                    style={styles.select}
                  >
                    {TYPE_OPTIONS.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Target Audience</label>
                  <select
                    name="Target_Audience"
                    value={form.Target_Audience}
                    onChange={handleChange}
                    style={styles.select}
                  >
                    {TARGET_OPTIONS.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Start Date *</label>
                  <input
                    type="date"
                    name="Start_Date"
                    value={form.Start_Date}
                    onChange={handleChange}
                    style={styles.input}
                  />
                  {errors.Start_Date && <div style={styles.error}>{errors.Start_Date}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>End Date</label>
                  <input
                    type="date"
                    name="End_Date"
                    value={form.End_Date}
                    onChange={handleChange}
                    style={styles.input}
                  />
                </div>
              </div>
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Audience Roles (employees only)</label>
                    <input
                      type="text"
                      name="Audience_Roles"
                      value={form.Audience_Roles}
                      onChange={handleChange}
                      style={styles.input}
                      placeholder="Admin, Employee"
                    />
                  </div>
                </div>
                <div style={styles.formRow}>
                  <div style={styles.formGroup}>
                    <label style={styles.label}>Priority (1=highest)</label>
                    <input
                    type="number"
                    name="Priority"
                    value={form.Priority}
                    onChange={handleChange}
                    style={styles.input}
                    min="1"
                    max="10"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Status</label>
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

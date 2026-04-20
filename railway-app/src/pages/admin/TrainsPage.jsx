/**
 * Admin TrainsPage - Train management CRUD interface.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import PermissionGate from '../../components/PermissionGate';

const TRAIN_TYPES = [
  'Superfast', 'Mail/Express', 'Rajdhani', 'Shatabdi', 'Duronto',
  'Garib Rath', 'Jan Shatabdi', 'Vande Bharat', 'Tejas', 'Passenger', 'Local'
];

const STATUS_OPTIONS = ['Active', 'Inactive', 'Cancelled'];
const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

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
  btnPrimary: { background: 'var(--accent-green, #22c55e)', color: '#fff' },
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
    maxWidth: 640,
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
  formRow3: { display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 },
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
  daysRow: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
  },
  dayChip: {
    padding: '6px 12px',
    borderRadius: 6,
    fontSize: 12,
    fontWeight: 500,
    cursor: 'pointer',
    border: '1px solid var(--border, #2a2a2a)',
    background: 'var(--bg-inset, #252525)',
    color: 'var(--text-muted, #6b7280)',
    transition: 'all 0.2s',
  },
  dayChipActive: {
    background: 'var(--accent-green, #22c55e)',
    color: '#fff',
    borderColor: 'var(--accent-green, #22c55e)',
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
  if (s === 'inactive') return { ...styles.badge, ...styles.badgeWarning };
  if (s === 'cancelled') return { ...styles.badge, ...styles.badgeDanger };
  return styles.badge;
}

const BLANK_FORM = {
  Train_Number: '',
  Train_Name: '',
  Train_Type: 'Superfast',
  From_Station: '',
  To_Station: '',
  Departure_Time: '',
  Arrival_Time: '',
  Duration: '',
  Days_Of_Operation: 'All Days',
  Is_Active: 'true',
  Total_Seats_SL: '',
  Total_Seats_3A: '',
  Total_Seats_2A: '',
  Total_Seats_1A: '',
  Total_Seats_CC: '',
};

export default function TrainsPage() {
  const [trains, setTrains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchTrains = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/trains');
      const data = res.data?.data || res.data || [];
      const trainList = Array.isArray(data) ? data : (data.data || []);
      setTrains(trainList);
    } catch (err) {
      console.error('Failed to fetch trains:', err);
      setTrains([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTrains();
  }, [fetchTrains]);

  const filtered = trains.filter((t) => {
    const s = search.toLowerCase();
    return (
      (t.Train_Number || '').toLowerCase().includes(s) ||
      (t.Train_Name || '').toLowerCase().includes(s) ||
      (t.From_Station || '').toLowerCase().includes(s) ||
      (t.To_Station || '').toLowerCase().includes(s)
    );
  });

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setForm((f) => ({
      ...f,
      [name]: type === 'number' ? parseInt(value, 10) || 0 : value,
    }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: '' }));
  };

  const toggleDay = (day) => {
    // Days of operation is stored as a string in CloudScale
    // For now, keep it simple
    setForm((f) => ({ ...f, Days_Of_Operation: 'All Days' }));
  };

  const validate = () => {
    const e = {};
    if (!form.Train_Number.trim()) e.Train_Number = 'Required';
    if (!form.Train_Name.trim()) e.Train_Name = 'Required';
    if (!form.From_Station.trim()) e.From_Station = 'Required';
    if (!form.To_Station.trim()) e.To_Station = 'Required';
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
      Train_Number: row.Train_Number || '',
      Train_Name: row.Train_Name || '',
      Train_Type: row.Train_Type || 'Superfast',
      From_Station: row.From_Station || '',
      To_Station: row.To_Station || '',
      Departure_Time: row.Departure_Time || '',
      Arrival_Time: row.Arrival_Time || '',
      Duration: row.Duration || '',
      Days_Of_Operation: row.Days_Of_Operation || row.Run_Days || 'All Days',
      Is_Active: row.Is_Active || 'true',
      Total_Seats_SL: row.Total_Seats_SL || '',
      Total_Seats_3A: row.Total_Seats_3A || '',
      Total_Seats_2A: row.Total_Seats_2A || '',
      Total_Seats_1A: row.Total_Seats_1A || '',
      Total_Seats_CC: row.Total_Seats_CC || '',
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
      const payload = {
        Train_Number: form.Train_Number.trim(),
        Train_Name: form.Train_Name.trim(),
        Train_Type: form.Train_Type,
        From_Station: form.From_Station.trim(),
        To_Station: form.To_Station.trim(),
        Departure_Time: form.Departure_Time || undefined,
        Arrival_Time: form.Arrival_Time || undefined,
        Days_Of_Operation: form.Days_Of_Operation || 'All Days',
        Is_Active: form.Is_Active,
        Total_Seats_SL: form.Total_Seats_SL || 0,
        Total_Seats_3A: form.Total_Seats_3A || 0,
        Total_Seats_2A: form.Total_Seats_2A || 0,
        Total_Seats_1A: form.Total_Seats_1A || 0,
        Total_Seats_CC: form.Total_Seats_CC || 0,
      };

      if (modal === 'create') {
        await api.post('/trains', payload);
      } else {
        const trainId = editRow?.ROWID || editRow?.ID || editRow?.id;
        await api.put(`/trains/${trainId}`, payload);
      }
      setModal(null);
      fetchTrains();
    } catch (err) {
      setErrors({ _api: err.message || 'Failed to save' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete train "${row.Train_Name}"?`)) return;
    try {
      const trainId = row.ROWID || row.ID || row.id;
      await api.delete(`/trains/${trainId}`);
      fetchTrains();
    } catch (err) {
      alert(err.message || 'Delete failed');
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Trains</h1>
          <p style={styles.subtitle}>{trains.length} trains in the system</p>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search trains..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={fetchTrains}>
            Refresh
          </button>
          <PermissionGate module="trains" action="create">
            <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
              + Add Train
            </button>
          </PermissionGate>
        </div>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading trains...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>No trains found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Train No.</th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Route</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((train) => (
                <tr key={train.ROWID || train.ID || train.Train_Number}>
                  <td style={{ ...styles.td, fontFamily: 'monospace', color: 'var(--text-primary)' }}>
                    {train.Train_Number || '—'}
                  </td>
                  <td style={{ ...styles.td, color: 'var(--text-primary)' }}>
                    {train.Train_Name || '—'}
                  </td>
                  <td style={styles.td}>
                    <span style={{ ...styles.badge, ...styles.badgeBlue }}>
                      {train.Train_Type || 'Express'}
                    </span>
                  </td>
                  <td style={styles.td}>
                    {train.From_Station || '—'} → {train.To_Station || '—'}
                  </td>
                  <td style={styles.td}>
                    <span style={getStatusBadge(train.Is_Active === 'true' ? 'active' : 'inactive')}>
                      {train.Is_Active === 'true' ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <PermissionGate module="trains" action="edit">
                        <button style={styles.actionBtn} onClick={() => openEdit(train)}>
                          Edit
                        </button>
                      </PermissionGate>
                      <PermissionGate module="trains" action="delete">
                        <button
                          style={{ ...styles.actionBtn, color: '#ef4444' }}
                          onClick={() => handleDelete(train)}
                        >
                          Delete
                        </button>
                      </PermissionGate>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div style={styles.pagination}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Showing {filtered.length} of {trains.length}
          </span>
        </div>
      </div>

      {/* Modal */}
      {modal && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>
                {modal === 'create' ? 'Add Train' : 'Edit Train'}
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
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Train Number *</label>
                  <input
                    name="Train_Number"
                    value={form.Train_Number}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., 12345"
                  />
                  {errors.Train_Number && <div style={styles.error}>{errors.Train_Number}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Train Name *</label>
                  <input
                    name="Train_Name"
                    value={form.Train_Name}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., Rajdhani Express"
                  />
                  {errors.Train_Name && <div style={styles.error}>{errors.Train_Name}</div>}
                </div>
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Train Type</label>
                  <select name="Train_Type" value={form.Train_Type} onChange={handleChange} style={styles.select}>
                    {TRAIN_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Status</label>
                  <select name="Is_Active" value={form.Is_Active} onChange={handleChange} style={styles.select}>
                    <option value="true">Active</option>
                    <option value="false">Inactive</option>
                  </select>
                </div>
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>From Station *</label>
                  <input
                    name="From_Station"
                    value={form.From_Station}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., NDLS or MAS"
                  />
                  {errors.From_Station && <div style={styles.error}>{errors.From_Station}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>To Station *</label>
                  <input
                    name="To_Station"
                    value={form.To_Station}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., HWH or BCT"
                  />
                  {errors.To_Station && <div style={styles.error}>{errors.To_Station}</div>}
                </div>
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Departure Time</label>
                  <input
                    name="Departure_Time"
                    type="time"
                    value={form.Departure_Time}
                    onChange={handleChange}
                    style={styles.input}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Arrival Time</label>
                  <input
                    name="Arrival_Time"
                    type="time"
                    value={form.Arrival_Time}
                    onChange={handleChange}
                    style={styles.input}
                  />
                </div>
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>Days of Operation</label>
                <input
                  name="Days_Of_Operation"
                  value={form.Days_Of_Operation}
                  onChange={handleChange}
                  style={styles.input}
                  placeholder="All Days or Mon,Tue,Wed,Thu,Fri,Sat,Sun"
                />
              </div>

              <div style={{ ...styles.formGroup, marginTop: 20 }}>
                <label style={{ ...styles.label, marginBottom: 12 }}>Seat Configuration</label>
                <div style={styles.formRow}>
                  <div>
                    <label style={{ ...styles.label, fontSize: 11 }}>Sleeper (SL)</label>
                    <input
                      name="Total_Seats_SL"
                      type="number"
                      value={form.Total_Seats_SL}
                      onChange={handleChange}
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={{ ...styles.label, fontSize: 11 }}>3AC</label>
                    <input
                      name="Total_Seats_3A"
                      type="number"
                      value={form.Total_Seats_3A}
                      onChange={handleChange}
                      style={styles.input}
                    />
                  </div>
                </div>
                <div style={{ ...styles.formRow, marginTop: 12 }}>
                  <div>
                    <label style={{ ...styles.label, fontSize: 11 }}>2AC</label>
                    <input
                      name="Total_Seats_2A"
                      type="number"
                      value={form.Total_Seats_2A}
                      onChange={handleChange}
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={{ ...styles.label, fontSize: 11 }}>1AC</label>
                    <input
                      name="Total_Seats_1A"
                      type="number"
                      value={form.Total_Seats_1A}
                      onChange={handleChange}
                      style={styles.input}
                    />
                  </div>
                  <div>
                    <label style={{ ...styles.label, fontSize: 11 }}>Chair Car (CC)</label>
                    <input
                      name="Total_Seats_CC"
                      type="number"
                      value={form.Total_Seats_CC}
                      onChange={handleChange}
                      style={styles.input}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div style={styles.modalFooter}>
              <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={() => setModal(null)}>
                Cancel
              </button>
              <button
                style={{ ...styles.btn, ...styles.btnPrimary }}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? 'Saving...' : modal === 'create' ? 'Create Train' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

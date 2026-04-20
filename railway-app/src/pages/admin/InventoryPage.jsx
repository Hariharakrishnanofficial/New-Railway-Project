/**
 * Admin InventoryPage - Seat/Coach inventory management.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/SessionAuthContext';

const CLASS_OPTIONS = ['SL', '3A', '2A', '1A', 'CC', 'EC', '2S', 'GN'];
const STATUS_OPTIONS = ['Available', 'Waitlisted', 'RAC', 'Sold Out'];

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
  filterBar: {
    display: 'flex',
    gap: 12,
    marginBottom: 20,
    flexWrap: 'wrap',
  },
  filterSelect: {
    padding: '8px 12px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 13,
    outline: 'none',
    minWidth: 120,
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
  statSub: { fontSize: 12, color: 'var(--text-muted, #6b7280)', marginTop: 4 },
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
    fontSize: 12,
    fontWeight: 500,
  },
  badgeSuccess: { background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
  badgeWarning: { background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' },
  badgeDanger: { background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
  badgeBlue: { background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' },
  progressBar: {
    height: 6,
    background: 'var(--bg-inset, #252525)',
    borderRadius: 3,
    overflow: 'hidden',
    marginTop: 6,
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
    transition: 'width 0.3s',
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

function getStatusBadge(status) {
  const s = (status || '').toLowerCase();
  if (s === 'available') return { ...styles.badge, ...styles.badgeSuccess };
  if (s === 'rac') return { ...styles.badge, ...styles.badgeWarning };
  if (s === 'waitlisted') return { ...styles.badge, ...styles.badgeBlue };
  if (s === 'sold out') return { ...styles.badge, ...styles.badgeDanger };
  return styles.badge;
}

const BLANK_FORM = {
  Train_ID: '',
  Schedule_ID: '',
  Class_Type: 'SL',
  Total_Seats: '',
  Available_Seats: '',
  RAC_Seats: '',
  Waitlist_Count: '',
  Booking_Status: 'Available',
  Journey_Date: '',
};

export default function InventoryPage() {
  const { isAdmin } = useAuth();
  const [inventory, setInventory] = useState([]);
  const [trains, setTrains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterClass, setFilterClass] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [invRes, trainsRes] = await Promise.all([
        api.get('/inventory'),
        api.get('/trains'),
      ]);
      setInventory(invRes.data?.data || invRes.data || []);
      setTrains(trainsRes.data?.data || trainsRes.data || []);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAdmin) {
      fetchData();
    } else {
      setLoading(false);
    }
  }, [isAdmin, fetchData]);

  if (!isAdmin) {
    return (
      <div style={styles.page}>
        <div style={styles.card}>
          <div style={{ padding: 20, color: 'var(--text-muted, #6b7280)' }}>
            Admin access required.
          </div>
        </div>
      </div>
    );
  }

  const getTrainName = (id) => {
    const t = trains.find((x) => x.ROWID === id || x.Train_ID === id);
    return t ? `${t.Train_Number} - ${t.Train_Name}` : id || '-';
  };

  const filtered = inventory.filter((inv) => {
    const s = search.toLowerCase();
    const matchSearch =
      getTrainName(inv.Train_ID).toLowerCase().includes(s) ||
      (inv.Class_Type || '').toLowerCase().includes(s) ||
      (inv.Journey_Date || '').includes(s);
    const matchClass = !filterClass || inv.Class_Type === filterClass;
    const matchStatus = !filterStatus || (inv.Booking_Status || '').toLowerCase() === filterStatus.toLowerCase();
    return matchSearch && matchClass && matchStatus;
  });

  const stats = {
    totalSeats: inventory.reduce((a, i) => a + parseInt(i.Total_Seats || 0), 0),
    available: inventory.reduce((a, i) => a + parseInt(i.Available_Seats || 0), 0),
    booked: inventory.reduce(
      (a, i) => a + (parseInt(i.Total_Seats || 0) - parseInt(i.Available_Seats || 0)),
      0
    ),
    occupancy: inventory.length
      ? Math.round(
          ((inventory.reduce(
            (a, i) => a + (parseInt(i.Total_Seats || 0) - parseInt(i.Available_Seats || 0)),
            0
          ) /
            inventory.reduce((a, i) => a + parseInt(i.Total_Seats || 0), 0)) *
            100) || 0
        )
      : 0,
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: '' }));
  };

  const validate = () => {
    const e = {};
    if (!form.Train_ID) e.Train_ID = 'Required';
    if (!form.Class_Type) e.Class_Type = 'Required';
    if (!form.Total_Seats || parseInt(form.Total_Seats) <= 0) e.Total_Seats = 'Must be > 0';
    if (!form.Journey_Date) e.Journey_Date = 'Required';
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
      Train_ID: row.Train_ID || '',
      Schedule_ID: row.Schedule_ID || '',
      Class_Type: row.Class_Type || 'SL',
      Total_Seats: row.Total_Seats || '',
      Available_Seats: row.Available_Seats || '',
      RAC_Seats: row.RAC_Seats || '',
      Waitlist_Count: row.Waitlist_Count || '',
      Booking_Status: row.Booking_Status || 'Available',
      Journey_Date: row.Journey_Date?.split('T')[0] || row.Journey_Date || '',
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
        await api.post('/inventory', payload);
      } else {
        const id = editRow.ROWID || editRow.Inventory_ID;
        await api.put(`/inventory/${id}`, payload);
      }
      setModal(null);
      fetchData();
    } catch (err) {
      console.error('Save failed:', err);
      setErrors({ _form: err.response?.data?.message || 'Save failed' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm('Delete this inventory record?')) return;
    try {
      const id = row.ROWID || row.Inventory_ID;
      await api.delete(`/inventory/${id}`);
      fetchData();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>Seat Inventory</div>
          <div style={styles.subtitle}>Manage seat availability across trains</div>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
            + Add Inventory
          </button>
        </div>
      </div>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Total Seats</div>
          <div style={styles.statValue}>{stats.totalSeats.toLocaleString()}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Available</div>
          <div style={{ ...styles.statValue, color: '#22c55e' }}>
            {stats.available.toLocaleString()}
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Booked</div>
          <div style={{ ...styles.statValue, color: '#3b82f6' }}>
            {stats.booked.toLocaleString()}
          </div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Occupancy</div>
          <div style={styles.statValue}>{stats.occupancy}%</div>
          <div style={styles.progressBar}>
            <div
              style={{
                ...styles.progressFill,
                width: `${stats.occupancy}%`,
                background:
                  stats.occupancy > 80 ? '#ef4444' : stats.occupancy > 50 ? '#f59e0b' : '#22c55e',
              }}
            />
          </div>
        </div>
      </div>

      <div style={styles.filterBar}>
        <select
          value={filterClass}
          onChange={(e) => setFilterClass(e.target.value)}
          style={styles.filterSelect}
        >
          <option value="">All Classes</option>
          {CLASS_OPTIONS.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          style={styles.filterSelect}
        >
          <option value="">All Status</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading inventory...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>No inventory records found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Train</th>
                <th style={styles.th}>Date</th>
                <th style={styles.th}>Class</th>
                <th style={styles.th}>Total</th>
                <th style={styles.th}>Available</th>
                <th style={styles.th}>RAC</th>
                <th style={styles.th}>WL</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, idx) => (
                <tr key={row.ROWID || row.Availability_ID || idx}>
                  <td style={styles.td}>{getTrainName(row.Train_ID)}</td>
                  <td style={styles.td}>{row.Journey_Date}</td>
                  <td style={styles.td}>
                    <span style={{ ...styles.badge, ...styles.badgeBlue }}>{row.Class_Type}</span>
                  </td>
                  <td style={styles.td}>{row.Total_Seats}</td>
                  <td style={{ ...styles.td, color: '#22c55e', fontWeight: 600 }}>
                    {row.Available_Seats}
                  </td>
                  <td style={styles.td}>{row.RAC_Seats || 0}</td>
                  <td style={styles.td}>{row.Waitlist_Count || 0}</td>
                  <td style={styles.td}>
                    <span style={getStatusBadge(row.Booking_Status)}>{row.Booking_Status}</span>
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
                {modal === 'create' ? 'Add Inventory' : 'Edit Inventory'}
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
                  <label style={styles.label}>Train *</label>
                  <select
                    name="Train_ID"
                    value={form.Train_ID}
                    onChange={handleChange}
                    style={styles.select}
                  >
                    <option value="">Select Train</option>
                    {trains.map((t) => (
                      <option key={t.ROWID || t.Train_ID} value={t.ROWID || t.Train_ID}>
                        {t.Train_Number} - {t.Train_Name}
                      </option>
                    ))}
                  </select>
                  {errors.Train_ID && <div style={styles.error}>{errors.Train_ID}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Journey Date *</label>
                  <input
                    type="date"
                    name="Journey_Date"
                    value={form.Journey_Date}
                    onChange={handleChange}
                    style={styles.input}
                  />
                  {errors.Journey_Date && <div style={styles.error}>{errors.Journey_Date}</div>}
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Class Type *</label>
                  <select
                    name="Class_Type"
                    value={form.Class_Type}
                    onChange={handleChange}
                    style={styles.select}
                  >
                    {CLASS_OPTIONS.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                  {errors.Class_Type && <div style={styles.error}>{errors.Class_Type}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Status</label>
                  <select
                    name="Booking_Status"
                    value={form.Booking_Status}
                    onChange={handleChange}
                    style={styles.select}
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Total Seats *</label>
                  <input
                    type="number"
                    name="Total_Seats"
                    value={form.Total_Seats}
                    onChange={handleChange}
                    style={styles.input}
                    min="1"
                  />
                  {errors.Total_Seats && <div style={styles.error}>{errors.Total_Seats}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Available Seats</label>
                  <input
                    type="number"
                    name="Available_Seats"
                    value={form.Available_Seats}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>RAC Seats</label>
                  <input
                    type="number"
                    name="RAC_Seats"
                    value={form.RAC_Seats}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Waitlist Count</label>
                  <input
                    type="number"
                    name="Waitlist_Count"
                    value={form.Waitlist_Count}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
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

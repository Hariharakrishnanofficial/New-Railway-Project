/**
 * Admin FaresPage - Fare rules CRUD management.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import { useAuth } from '../../context/SessionAuthContext';

const CLASS_OPTIONS = ['SL', '3A', '2A', '1A', 'CC', 'EC', '2S', 'GN'];

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
  card: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 12,
    border: '1px solid var(--border, #2a2a2a)',
    overflow: 'hidden',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
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
    background: 'rgba(59, 130, 246, 0.15)',
    color: '#3b82f6',
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

const BLANK_FORM = {
  Train_Type: '',
  Class_Type: 'SL',
  Base_Fare_Per_KM: '',
  Reservation_Charge: '40',
  Superfast_Charge: '0',
  GST_Percentage: '5',
  Dynamic_Pricing_Factor: '1.0',
  Min_Distance: '',
  Max_Distance: '',
};

export default function FaresPage() {
  const { isAdmin } = useAuth();
  const [fares, setFares] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({}); 
  const [saving, setSaving] = useState(false); 
 
  const fetchFares = useCallback(async () => { 
    setLoading(true); 
    try { 
      const res = await api.get('/fares'); 
      const payload = res?.data;

      // Many Catalyst function handlers return HTTP 200 with { status: "error" } on failures.
      if (payload && payload.status === 'error') {
        throw new Error(payload.message || 'Failed to fetch fares');
      }

      const list =
        (Array.isArray(payload?.data) && payload.data) ||
        (Array.isArray(payload) && payload) ||
        [];

      setFares(list); 
    } catch (err) { 
      console.error('Failed to fetch fares:', err); 
      setFares([]); 
    } finally { 
      setLoading(false); 
    } 
  }, []); 

  useEffect(() => {
    if (isAdmin) {
      fetchFares();
    } else {
      setLoading(false);
    }
  }, [isAdmin, fetchFares]);

  const faresList = Array.isArray(fares) ? fares : [];

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

  const filtered = faresList.filter((f) => { 
    const s = search.toLowerCase(); 
    return ( 
      (f.Train_Type || '').toLowerCase().includes(s) || 
      (f.Class_Type || '').toLowerCase().includes(s) 
    ); 
  }); 
 
  const stats = { 
    totalRules: faresList.length, 
    avgBaseFare: faresList.length 
      ? (faresList.reduce((a, f) => a + parseFloat(f.Base_Fare_Per_KM || 0), 0) / faresList.length).toFixed(2) 
      : '0.00', 
    classes: [...new Set(faresList.map((f) => f.Class_Type))].length, 
  }; 

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: '' }));
  };

  const validate = () => {
    const e = {};
    if (!form.Train_Type.trim()) e.Train_Type = 'Required';
    if (!form.Class_Type) e.Class_Type = 'Required';
    if (!form.Base_Fare_Per_KM || parseFloat(form.Base_Fare_Per_KM) <= 0) {
      e.Base_Fare_Per_KM = 'Must be > 0';
    }
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
      Train_Type: row.Train_Type || '',
      Class_Type: row.Class_Type || 'SL',
      Base_Fare_Per_KM: row.Base_Fare_Per_KM || '',
      Reservation_Charge: row.Reservation_Charge || '40',
      Superfast_Charge: row.Superfast_Charge || '0',
      GST_Percentage: row.GST_Percentage || '5',
      Dynamic_Pricing_Factor: row.Dynamic_Pricing_Factor || '1.0',
      Min_Distance: row.Min_Distance || '',
      Max_Distance: row.Max_Distance || '',
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
        await api.post('/fares', payload);
      } else {
        const id = editRow.ROWID || editRow.Fare_ID;
        await api.put(`/fares/${id}`, payload);
      }
      setModal(null);
      fetchFares();
    } catch (err) {
      console.error('Save failed:', err);
      setErrors({ _form: err.response?.data?.message || 'Save failed' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm('Delete this fare rule?')) return;
    try {
      const id = row.ROWID || row.Fare_ID;
      await api.delete(`/fares/${id}`);
      fetchFares();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>Fare Rules</div>
          <div style={styles.subtitle}>Manage fare pricing and charges</div>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search fares..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
            + Add Fare Rule
          </button>
        </div>
      </div>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Total Rules</div>
          <div style={styles.statValue}>{stats.totalRules}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Avg Base Fare/km</div>
          <div style={styles.statValue}>₹{stats.avgBaseFare}</div>
        </div>
        <div style={styles.statCard}>
          <div style={styles.statLabel}>Classes Covered</div>
          <div style={styles.statValue}>{stats.classes}</div>
        </div>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading fares...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>No fare rules found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Train Type</th>
                <th style={styles.th}>Class</th>
                <th style={styles.th}>Base/km</th>
                <th style={styles.th}>Reservation</th>
                <th style={styles.th}>Superfast</th>
                <th style={styles.th}>GST %</th>
                <th style={styles.th}>Distance Range</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.ROWID || row.Fare_ID || `${row.Train_Type}-${row.Class_Type}`}>
                  <td style={styles.td}>{row.Train_Type}</td>
                  <td style={styles.td}>
                    <span style={styles.badge}>{row.Class_Type}</span>
                  </td>
                  <td style={styles.td}>₹{row.Base_Fare_Per_KM}</td>
                  <td style={styles.td}>₹{row.Reservation_Charge || 0}</td>
                  <td style={styles.td}>₹{row.Superfast_Charge || 0}</td>
                  <td style={styles.td}>{row.GST_Percentage || 5}%</td>
                  <td style={styles.td}>
                    {row.Min_Distance || 0} - {row.Max_Distance || '∞'} km
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
                {modal === 'create' ? 'Add Fare Rule' : 'Edit Fare Rule'}
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
                  <label style={styles.label}>Train Type *</label>
                  <input
                    type="text"
                    name="Train_Type"
                    value={form.Train_Type}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., Express, Superfast"
                  />
                  {errors.Train_Type && <div style={styles.error}>{errors.Train_Type}</div>}
                </div>
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
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Base Fare per KM (₹) *</label>
                  <input
                    type="number"
                    name="Base_Fare_Per_KM"
                    value={form.Base_Fare_Per_KM}
                    onChange={handleChange}
                    style={styles.input}
                    step="0.01"
                    min="0"
                  />
                  {errors.Base_Fare_Per_KM && (
                    <div style={styles.error}>{errors.Base_Fare_Per_KM}</div>
                  )}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Reservation Charge (₹)</label>
                  <input
                    type="number"
                    name="Reservation_Charge"
                    value={form.Reservation_Charge}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Superfast Charge (₹)</label>
                  <input
                    type="number"
                    name="Superfast_Charge"
                    value={form.Superfast_Charge}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>GST Percentage</label>
                  <input
                    type="number"
                    name="GST_Percentage"
                    value={form.GST_Percentage}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                    max="28"
                  />
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Min Distance (km)</label>
                  <input
                    type="number"
                    name="Min_Distance"
                    value={form.Min_Distance}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Max Distance (km)</label>
                  <input
                    type="number"
                    name="Max_Distance"
                    value={form.Max_Distance}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Dynamic Pricing Factor</label>
                <input
                  type="number"
                  name="Dynamic_Pricing_Factor"
                  value={form.Dynamic_Pricing_Factor}
                  onChange={handleChange}
                  style={styles.input}
                  step="0.1"
                  min="0.5"
                  max="3.0"
                />
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

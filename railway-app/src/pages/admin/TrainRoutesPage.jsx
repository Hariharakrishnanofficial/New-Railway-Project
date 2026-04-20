/**
 * Admin TrainRoutesPage - Train routes CRUD management.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import PermissionGate from '../../components/PermissionGate';

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
  Train_ID: '',
  Station_ID: '',
  Station_Order: '',
  Arrival_Time: '',
  Departure_Time: '',
  Distance_From_Origin: '',
  Day_Offset: '0',
  Platform_Number: '',
  Halt_Duration: '',
};

export default function TrainRoutesPage() {
  const [routes, setRoutes] = useState([]);
  const [trains, setTrains] = useState([]);
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [routesRes, trainsRes, stationsRes] = await Promise.all([
        api.get('/train-routes'),
        api.get('/trains'),
        api.get('/stations'),
      ]);
      setRoutes(routesRes.data?.data || routesRes.data || []);
      setTrains(trainsRes.data?.data || trainsRes.data || []);
      setStations(stationsRes.data?.data || stationsRes.data || []);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getTrainName = (id) => {
    const t = trains.find((x) => x.ROWID === id || x.Train_ID === id);
    return t ? `${t.Train_Number} - ${t.Train_Name}` : id;
  };

  const getStationName = (id) => {
    const s = stations.find((x) => x.ROWID === id || x.Station_ID === id);
    return s ? `${s.Station_Code} - ${s.Station_Name}` : id;
  };

  const filtered = routes.filter((r) => {
    const s = search.toLowerCase();
    return (
      getTrainName(r.Train_ID).toLowerCase().includes(s) ||
      getStationName(r.Station_ID).toLowerCase().includes(s) ||
      String(r.Station_Order || '').includes(s)
    );
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((f) => ({ ...f, [name]: value }));
    if (errors[name]) setErrors((er) => ({ ...er, [name]: '' }));
  };

  const validate = () => {
    const e = {};
    if (!form.Train_ID) e.Train_ID = 'Required';
    if (!form.Station_ID) e.Station_ID = 'Required';
    if (!form.Station_Order) e.Station_Order = 'Required';
    if (!form.Arrival_Time) e.Arrival_Time = 'Required';
    if (!form.Departure_Time) e.Departure_Time = 'Required';
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
      Station_ID: row.Station_ID || '',
      Station_Order: row.Station_Order || '',
      Arrival_Time: row.Arrival_Time || '',
      Departure_Time: row.Departure_Time || '',
      Distance_From_Origin: row.Distance_From_Origin || '',
      Day_Offset: row.Day_Offset || '0',
      Platform_Number: row.Platform_Number || '',
      Halt_Duration: row.Halt_Duration || '',
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
        await api.post('/train-routes', payload);
      } else {
        const id = editRow.ROWID || editRow.Route_ID;
        await api.put(`/train-routes/${id}`, payload);
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
    if (!window.confirm('Delete this route stop?')) return;
    try {
      const id = row.ROWID || row.Route_ID;
      await api.delete(`/train-routes/${id}`);
      fetchData();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <div style={styles.title}>Train Routes</div>
          <div style={styles.subtitle}>Manage train route stops and schedules</div>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search routes..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <PermissionGate module="routes" action="create">
            <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
              + Add Route Stop
            </button>
          </PermissionGate>
        </div>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading routes...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>No routes found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Train</th>
                <th style={styles.th}>Station</th>
                <th style={styles.th}>Order</th>
                <th style={styles.th}>Arrival</th>
                <th style={styles.th}>Departure</th>
                <th style={styles.th}>Distance</th>
                <th style={styles.th}>Platform</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.ROWID || row.Route_ID}>
                  <td style={styles.td}>{getTrainName(row.Train_ID)}</td>
                  <td style={styles.td}>{getStationName(row.Station_ID)}</td>
                  <td style={styles.td}>{row.Station_Order}</td>
                  <td style={styles.td}>{row.Arrival_Time}</td>
                  <td style={styles.td}>{row.Departure_Time}</td>
                  <td style={styles.td}>{row.Distance_From_Origin} km</td>
                  <td style={styles.td}>{row.Platform_Number || '-'}</td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <PermissionGate module="routes" action="edit">
                        <button style={styles.actionBtn} onClick={() => openEdit(row)}>
                          Edit
                        </button>
                      </PermissionGate>
                      <PermissionGate module="routes" action="delete">
                        <button
                          style={{ ...styles.actionBtn, color: '#ef4444' }}
                          onClick={() => handleDelete(row)}
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
      </div>

      {modal && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <div style={styles.modalTitle}>
                {modal === 'create' ? 'Add Route Stop' : 'Edit Route Stop'}
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
                  <label style={styles.label}>Station *</label>
                  <select
                    name="Station_ID"
                    value={form.Station_ID}
                    onChange={handleChange}
                    style={styles.select}
                  >
                    <option value="">Select Station</option>
                    {stations.map((s) => (
                      <option key={s.ROWID || s.Station_ID} value={s.ROWID || s.Station_ID}>
                        {s.Station_Code} - {s.Station_Name}
                      </option>
                    ))}
                  </select>
                  {errors.Station_ID && <div style={styles.error}>{errors.Station_ID}</div>}
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Station Order *</label>
                  <input
                    type="number"
                    name="Station_Order"
                    value={form.Station_Order}
                    onChange={handleChange}
                    style={styles.input}
                    min="1"
                  />
                  {errors.Station_Order && <div style={styles.error}>{errors.Station_Order}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Distance from Origin (km)</label>
                  <input
                    type="number"
                    name="Distance_From_Origin"
                    value={form.Distance_From_Origin}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Arrival Time *</label>
                  <input
                    type="time"
                    name="Arrival_Time"
                    value={form.Arrival_Time}
                    onChange={handleChange}
                    style={styles.input}
                  />
                  {errors.Arrival_Time && <div style={styles.error}>{errors.Arrival_Time}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Departure Time *</label>
                  <input
                    type="time"
                    name="Departure_Time"
                    value={form.Departure_Time}
                    onChange={handleChange}
                    style={styles.input}
                  />
                  {errors.Departure_Time && <div style={styles.error}>{errors.Departure_Time}</div>}
                </div>
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Day Offset</label>
                  <input
                    type="number"
                    name="Day_Offset"
                    value={form.Day_Offset}
                    onChange={handleChange}
                    style={styles.input}
                    min="0"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Platform Number</label>
                  <input
                    type="text"
                    name="Platform_Number"
                    value={form.Platform_Number}
                    onChange={handleChange}
                    style={styles.input}
                  />
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Halt Duration (minutes)</label>
                <input
                  type="number"
                  name="Halt_Duration"
                  value={form.Halt_Duration}
                  onChange={handleChange}
                  style={styles.input}
                  min="0"
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

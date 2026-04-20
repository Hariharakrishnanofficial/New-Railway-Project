/**
 * Admin StationsPage - Station management CRUD interface.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import PermissionGate from '../../components/PermissionGate';

const STATION_TYPES = ['Junction', 'Terminal', 'Regular', 'Halt'];
const ZONES = ['NR', 'SR', 'ER', 'WR', 'CR', 'NWR', 'SWR', 'SER', 'NCR', 'NER', 'NFR', 'SCR', 'SECR', 'WCR', 'ECoR', 'ECR', 'KRCL'];

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
  btnPrimary: { background: 'var(--accent-pink, #ec4899)', color: '#fff' },
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
  badgePink: { background: 'rgba(236, 72, 153, 0.15)', color: '#ec4899' },
  badgePurple: { background: 'rgba(139, 92, 246, 0.15)', color: '#8b5cf6' },
  badgeBlue: { background: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' },
  badgeGray: { background: 'rgba(156, 163, 175, 0.15)', color: '#9ca3af' },
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
    maxWidth: 540,
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

function getTypeBadge(type) {
  const t = (type || '').toLowerCase();
  if (t === 'junction') return { ...styles.badge, ...styles.badgePink };
  if (t === 'terminal') return { ...styles.badge, ...styles.badgePurple };
  if (t === 'halt') return { ...styles.badge, ...styles.badgeGray };
  return { ...styles.badge, ...styles.badgeBlue };
}

const BLANK_FORM = {
  Station_Code: '',
  Station_Name: '',
  Station_Type: 'Regular',
  Zone: '',
  State: '',
  City: '',
  Platforms: 1,
  Latitude: '',
  Longitude: '',
};

export default function StationsPage() {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [editRow, setEditRow] = useState(null);
  const [form, setForm] = useState(BLANK_FORM);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchStations = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/stations');
      const data = res.data?.data || res.data || [];
      const stationList = Array.isArray(data) ? data : (data.data || []);
      setStations(stationList);
    } catch (err) {
      console.error('Failed to fetch stations:', err);
      setStations([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStations();
  }, [fetchStations]);

  const filtered = stations.filter((s) => {
    const q = search.toLowerCase();
    return (
      (s.Station_Code || '').toLowerCase().includes(q) ||
      (s.Station_Name || '').toLowerCase().includes(q) ||
      (s.City || '').toLowerCase().includes(q) ||
      (s.State || '').toLowerCase().includes(q)
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

  const validate = () => {
    const e = {};
    if (!form.Station_Code.trim()) e.Station_Code = 'Required';
    if (!form.Station_Name.trim()) e.Station_Name = 'Required';
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
      Station_Code: row.Station_Code || '',
      Station_Name: row.Station_Name || '',
      Station_Type: row.Station_Type || 'Regular',
      Zone: row.Zone || '',
      State: row.State || '',
      City: row.City || '',
      Platforms: row.Platforms || 1,
      Latitude: row.Latitude || '',
      Longitude: row.Longitude || '',
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
        Station_Code: form.Station_Code.trim().toUpperCase(),
        Station_Name: form.Station_Name.trim(),
        Station_Type: form.Station_Type,
        Zone: form.Zone || undefined,
        State: form.State.trim() || undefined,
        City: form.City.trim() || undefined,
        Platforms: form.Platforms || 1,
        Latitude: form.Latitude || undefined,
        Longitude: form.Longitude || undefined,
      };

      if (modal === 'create') {
        await api.post('/stations', payload);
      } else {
        const stationId = editRow?.ROWID || editRow?.ID || editRow?.id;
        await api.put(`/stations/${stationId}`, payload);
      }
      setModal(null);
      fetchStations();
    } catch (err) {
      setErrors({ _api: err.message || 'Failed to save' });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (row) => {
    if (!window.confirm(`Delete station "${row.Station_Name}"?`)) return;
    try {
      const stationId = row.ROWID || row.ID || row.id;
      await api.delete(`/stations/${stationId}`);
      fetchStations();
    } catch (err) {
      alert(err.message || 'Delete failed');
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Stations</h1>
          <p style={styles.subtitle}>{stations.length} stations in the network</p>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search stations..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={fetchStations}>
            Refresh
          </button>
          <PermissionGate module="stations" action="create">
            <button style={{ ...styles.btn, ...styles.btnPrimary }} onClick={openCreate}>
              + Add Station
            </button>
          </PermissionGate>
        </div>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading stations...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>No stations found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Code</th>
                <th style={styles.th}>Name</th>
                <th style={styles.th}>Type</th>
                <th style={styles.th}>Zone</th>
                <th style={styles.th}>City / State</th>
                <th style={styles.th}>Platforms</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((station) => (
                <tr key={station.ROWID || station.ID || station.Station_Code}>
                  <td style={{ ...styles.td, fontFamily: 'monospace', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {station.Station_Code || '—'}
                  </td>
                  <td style={{ ...styles.td, color: 'var(--text-primary)' }}>
                    {station.Station_Name || '—'}
                  </td>
                  <td style={styles.td}>
                    <span style={getTypeBadge(station.Station_Type)}>
                      {station.Station_Type || 'Regular'}
                    </span>
                  </td>
                  <td style={styles.td}>{station.Zone || '—'}</td>
                  <td style={styles.td}>
                    {station.City || '—'}{station.State ? `, ${station.State}` : ''}
                  </td>
                  <td style={{ ...styles.td, textAlign: 'center' }}>
                    {station.Platforms || 1}
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <PermissionGate module="stations" action="edit">
                        <button style={styles.actionBtn} onClick={() => openEdit(station)}>
                          Edit
                        </button>
                      </PermissionGate>
                      <PermissionGate module="stations" action="delete">
                        <button
                          style={{ ...styles.actionBtn, color: '#ef4444' }}
                          onClick={() => handleDelete(station)}
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
            Showing {filtered.length} of {stations.length}
          </span>
        </div>
      </div>

      {/* Modal */}
      {modal && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>
                {modal === 'create' ? 'Add Station' : 'Edit Station'}
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
                  <label style={styles.label}>Station Code *</label>
                  <input
                    name="Station_Code"
                    value={form.Station_Code}
                    onChange={handleChange}
                    style={{ ...styles.input, textTransform: 'uppercase' }}
                    placeholder="e.g., MAS"
                    maxLength={5}
                  />
                  {errors.Station_Code && <div style={styles.error}>{errors.Station_Code}</div>}
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Station Name *</label>
                  <input
                    name="Station_Name"
                    value={form.Station_Name}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., Chennai Central"
                  />
                  {errors.Station_Name && <div style={styles.error}>{errors.Station_Name}</div>}
                </div>
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Station Type</label>
                  <select name="Station_Type" value={form.Station_Type} onChange={handleChange} style={styles.select}>
                    {STATION_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Zone</label>
                  <select name="Zone" value={form.Zone} onChange={handleChange} style={styles.select}>
                    <option value="">Select Zone</option>
                    {ZONES.map((z) => (
                      <option key={z} value={z}>{z}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>City</label>
                  <input
                    name="City"
                    value={form.City}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., Chennai"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>State</label>
                  <input
                    name="State"
                    value={form.State}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., Tamil Nadu"
                  />
                </div>
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>Number of Platforms</label>
                <input
                  name="Platforms"
                  type="number"
                  min="1"
                  max="50"
                  value={form.Platforms}
                  onChange={handleChange}
                  style={styles.input}
                />
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Latitude</label>
                  <input
                    name="Latitude"
                    value={form.Latitude}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., 13.0827"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Longitude</label>
                  <input
                    name="Longitude"
                    value={form.Longitude}
                    onChange={handleChange}
                    style={styles.input}
                    placeholder="e.g., 80.2707"
                  />
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
                {saving ? 'Saving...' : modal === 'create' ? 'Create Station' : 'Save Changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

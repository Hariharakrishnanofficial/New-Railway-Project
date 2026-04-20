/**
 * Admin BookingsPage - Booking management interface.
 */
import React, { useState, useEffect, useCallback } from 'react';
import api from '../../services/api';
import PermissionGate from '../../components/PermissionGate';

const STATUS_OPTIONS = ['All', 'Confirmed', 'Pending', 'Cancelled', 'Waitlist'];

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
    width: 200,
    outline: 'none',
  },
  filterSelect: {
    padding: '10px 14px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 8,
    color: 'var(--text-primary, #fff)',
    fontSize: 14,
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
    maxWidth: 600,
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
  detailRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 16,
    marginBottom: 16,
  },
  detailLabel: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  detailValue: {
    fontSize: 14,
    color: 'var(--text-primary, #fff)',
  },
  passengerCard: {
    background: 'var(--bg-inset, #252525)',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
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
  statsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 16,
    marginBottom: 24,
  },
  statCard: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 10,
    padding: 16,
    border: '1px solid var(--border, #2a2a2a)',
    textAlign: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: 700,
    color: 'var(--text-primary, #fff)',
  },
  statLabel: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
    marginTop: 4,
  },
};

function getStatusBadge(status) {
  const s = (status || '').toLowerCase();
  if (s === 'confirmed') return { ...styles.badge, ...styles.badgeSuccess };
  if (s === 'pending') return { ...styles.badge, ...styles.badgeWarning };
  if (s === 'cancelled') return { ...styles.badge, ...styles.badgeDanger };
  if (s === 'waitlist') return { ...styles.badge, ...styles.badgeBlue };
  return styles.badge;
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount || 0);
}

export default function BookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [modal, setModal] = useState(null);
  const [selectedBooking, setSelectedBooking] = useState(null);

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get('/bookings');
      const data = res.data?.data || res.data || [];
      const bookingList = Array.isArray(data) ? data : (data.data || []);
      setBookings(bookingList);
    } catch (err) {
      console.error('Failed to fetch bookings:', err);
      setBookings([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  const filtered = bookings.filter((b) => {
    const matchesSearch =
      (b.PNR || '').toLowerCase().includes(search.toLowerCase()) ||
      (b.User_Email || '').toLowerCase().includes(search.toLowerCase()) ||
      (b.Source_Station || '').toLowerCase().includes(search.toLowerCase()) ||
      (b.Destination_Station || '').toLowerCase().includes(search.toLowerCase());

    const matchesStatus =
      statusFilter === 'All' ||
      (b.Booking_Status || '').toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesStatus;
  });

  const stats = {
    total: bookings.length,
    confirmed: bookings.filter((b) => (b.Booking_Status || '').toLowerCase() === 'confirmed').length,
    pending: bookings.filter((b) => (b.Booking_Status || '').toLowerCase() === 'pending').length,
    cancelled: bookings.filter((b) => (b.Booking_Status || '').toLowerCase() === 'cancelled').length,
  };

  const openView = (booking) => {
    setSelectedBooking(booking);
    setModal('view');
  };

  const handleConfirm = async (booking) => {
    if (!window.confirm('Confirm this booking?')) return;
    try {
      const bookingId = booking.ROWID || booking.ID || booking.id;
      await api.post(`/bookings/${bookingId}/confirm`);
      fetchBookings();
    } catch (err) {
      alert(err.message || 'Failed to confirm booking');
    }
  };

  const handleCancel = async (booking) => {
    if (!window.confirm('Cancel this booking?')) return;
    try {
      const bookingId = booking.ROWID || booking.ID || booking.id;
      await api.post(`/bookings/${bookingId}/cancel`);
      fetchBookings();
    } catch (err) {
      alert(err.message || 'Failed to cancel booking');
    }
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Bookings</h1>
          <p style={styles.subtitle}>{bookings.length} total bookings</p>
        </div>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search PNR, email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={styles.searchInput}
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={styles.filterSelect}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={fetchBookings}>
            Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={styles.statsRow}>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{stats.total}</div>
          <div style={styles.statLabel}>Total Bookings</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: '#22c55e' }}>{stats.confirmed}</div>
          <div style={styles.statLabel}>Confirmed</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: '#eab308' }}>{stats.pending}</div>
          <div style={styles.statLabel}>Pending</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: '#ef4444' }}>{stats.cancelled}</div>
          <div style={styles.statLabel}>Cancelled</div>
        </div>
      </div>

      <div style={styles.card}>
        {loading ? (
          <div style={styles.loading}>Loading bookings...</div>
        ) : filtered.length === 0 ? (
          <div style={styles.empty}>No bookings found</div>
        ) : (
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>PNR</th>
                <th style={styles.th}>Route</th>
                <th style={styles.th}>Date</th>
                <th style={styles.th}>Class</th>
                <th style={styles.th}>Passengers</th>
                <th style={styles.th}>Fare</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((booking) => (
                <tr key={booking.ROWID || booking.ID || booking.PNR}>
                  <td style={{ ...styles.td, fontFamily: 'monospace', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {booking.PNR || '—'}
                  </td>
                  <td style={styles.td}>
                    {booking.Source_Station || '—'} → {booking.Destination_Station || '—'}
                  </td>
                  <td style={styles.td}>{booking.Journey_Date || '—'}</td>
                  <td style={styles.td}>
                    <span style={{ ...styles.badge, ...styles.badgeBlue }}>
                      {booking.Class || booking.Travel_Class || '—'}
                    </span>
                  </td>
                  <td style={{ ...styles.td, textAlign: 'center' }}>
                    {booking.Passenger_Count || booking.Total_Passengers || 1}
                  </td>
                  <td style={{ ...styles.td, color: 'var(--text-primary)' }}>
                    {formatCurrency(booking.Total_Fare)}
                  </td>
                  <td style={styles.td}>
                    <span style={getStatusBadge(booking.Booking_Status)}>
                      {booking.Booking_Status || 'Pending'}
                    </span>
                  </td>
                  <td style={styles.td}>
                    <div style={styles.actions}>
                      <button style={styles.actionBtn} onClick={() => openView(booking)}>
                        View
                      </button>
                      <PermissionGate module="bookings" action="edit">
                        {(booking.Booking_Status || '').toLowerCase() === 'pending' && (
                          <button
                            style={{ ...styles.actionBtn, color: '#22c55e' }}
                            onClick={() => handleConfirm(booking)}
                          >
                            Confirm
                          </button>
                        )}
                      </PermissionGate>
                      <PermissionGate module="bookings" action="cancel">
                        {(booking.Booking_Status || '').toLowerCase() !== 'cancelled' && (
                          <button
                            style={{ ...styles.actionBtn, color: '#ef4444' }}
                            onClick={() => handleCancel(booking)}
                          >
                            Cancel
                          </button>
                        )}
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
            Showing {filtered.length} of {bookings.length}
          </span>
        </div>
      </div>

      {/* View Modal */}
      {modal === 'view' && selectedBooking && (
        <div style={styles.modal} onClick={() => setModal(null)}>
          <div style={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div style={styles.modalHeader}>
              <h2 style={styles.modalTitle}>
                Booking Details - {selectedBooking.PNR || 'N/A'}
              </h2>
              <button
                onClick={() => setModal(null)}
                style={{ ...styles.btn, ...styles.btnSecondary, padding: '6px 12px' }}
              >
                ✕
              </button>
            </div>

            <div style={styles.modalBody}>
              <div style={styles.detailRow}>
                <div>
                  <div style={styles.detailLabel}>PNR Number</div>
                  <div style={{ ...styles.detailValue, fontFamily: 'monospace', fontSize: 18 }}>
                    {selectedBooking.PNR || '—'}
                  </div>
                </div>
                <div>
                  <div style={styles.detailLabel}>Status</div>
                  <span style={getStatusBadge(selectedBooking.Booking_Status)}>
                    {selectedBooking.Booking_Status || 'Pending'}
                  </span>
                </div>
              </div>

              <div style={styles.detailRow}>
                <div>
                  <div style={styles.detailLabel}>From</div>
                  <div style={styles.detailValue}>{selectedBooking.Source_Station || '—'}</div>
                </div>
                <div>
                  <div style={styles.detailLabel}>To</div>
                  <div style={styles.detailValue}>{selectedBooking.Destination_Station || '—'}</div>
                </div>
              </div>

              <div style={styles.detailRow}>
                <div>
                  <div style={styles.detailLabel}>Journey Date</div>
                  <div style={styles.detailValue}>{selectedBooking.Journey_Date || '—'}</div>
                </div>
                <div>
                  <div style={styles.detailLabel}>Train</div>
                  <div style={styles.detailValue}>
                    {selectedBooking.Train_Name || selectedBooking.Train_ID || '—'}
                  </div>
                </div>
              </div>

              <div style={styles.detailRow}>
                <div>
                  <div style={styles.detailLabel}>Class</div>
                  <div style={styles.detailValue}>
                    {selectedBooking.Class || selectedBooking.Travel_Class || '—'}
                  </div>
                </div>
                <div>
                  <div style={styles.detailLabel}>Total Fare</div>
                  <div style={{ ...styles.detailValue, fontSize: 20, color: '#22c55e' }}>
                    {formatCurrency(selectedBooking.Total_Fare)}
                  </div>
                </div>
              </div>

              <div style={styles.detailRow}>
                <div>
                  <div style={styles.detailLabel}>Passengers</div>
                  <div style={styles.detailValue}>
                    {selectedBooking.Passenger_Count || selectedBooking.Total_Passengers || 1}
                  </div>
                </div>
                <div>
                  <div style={styles.detailLabel}>Booked On</div>
                  <div style={styles.detailValue}>{selectedBooking.Created_At || '—'}</div>
                </div>
              </div>

              {selectedBooking.User_Email && (
                <div style={{ marginTop: 16 }}>
                  <div style={styles.detailLabel}>Booked By</div>
                  <div style={styles.detailValue}>{selectedBooking.User_Email}</div>
                </div>
              )}

              {/* Passenger list if available */}
              {selectedBooking.Passengers && selectedBooking.Passengers.length > 0 && (
                <div style={{ marginTop: 20 }}>
                  <div style={{ ...styles.detailLabel, marginBottom: 12 }}>Passenger Details</div>
                  {selectedBooking.Passengers.map((p, idx) => (
                    <div key={idx} style={styles.passengerCard}>
                      <div style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                        {p.Name || p.Passenger_Name || `Passenger ${idx + 1}`}
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                        Age: {p.Age || '—'} | {p.Gender || '—'} | Seat: {p.Seat_Number || p.Coach + '-' + p.Berth || '—'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div style={styles.modalFooter}>
              <button style={{ ...styles.btn, ...styles.btnSecondary }} onClick={() => setModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

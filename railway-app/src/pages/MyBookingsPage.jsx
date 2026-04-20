/**
 * MyBookingsPage.jsx — View user's bookings.
 * 
 * Features:
 *   - List all user bookings
 *   - Filter by status
 *   - View booking details
 *   - Cancel bookings
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

// Icons
const Icons = {
  Ticket: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
      <path d="M13 5v2" /><path d="M13 17v2" /><path d="M13 11v2" />
    </svg>
  ),
  Train: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="4" y="3" width="16" height="16" rx="2" />
      <path d="M4 11h16" /><path d="M12 3v8" />
    </svg>
  ),
  Calendar: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  ),
  Users: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  X: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  Eye: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  Loader: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  ),
  AlertCircle: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  ),
};

const styles = {
  container: {
    maxWidth: 1000,
    margin: '0 auto',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 800,
    fontFamily: 'var(--font-display)',
    color: 'var(--text-primary)',
    margin: 0,
  },
  subtitle: {
    fontSize: 14,
    color: 'var(--text-muted)',
    marginTop: 8,
  },
  
  // Filters
  filterBar: {
    display: 'flex',
    gap: 12,
    marginBottom: 24,
    flexWrap: 'wrap',
  },
  filterChip: {
    padding: '8px 16px',
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-full)',
    color: 'var(--text-secondary)',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  filterChipActive: {
    background: 'rgba(59, 130, 246, 0.15)',
    borderColor: 'var(--accent-blue)',
    color: 'var(--accent-blue)',
  },
  
  // Stats
  statsRow: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 16,
    marginBottom: 32,
  },
  statCard: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: 16,
    textAlign: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: 700,
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
  },
  statLabel: {
    fontSize: 12,
    color: 'var(--text-muted)',
    marginTop: 4,
  },
  
  // Booking card
  bookingCard: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: 20,
    marginBottom: 16,
  },
  bookingHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  bookingPnr: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-muted)',
    fontFamily: 'var(--font-mono)',
    marginBottom: 4,
  },
  bookingTrain: {
    fontSize: 18,
    fontWeight: 700,
    color: 'var(--text-primary)',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  statusBadge: {
    padding: '4px 12px',
    borderRadius: 'var(--radius-full)',
    fontSize: 12,
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  statusConfirmed: {
    background: 'rgba(74, 222, 128, 0.15)',
    color: 'var(--success)',
  },
  statusRac: {
    background: 'rgba(251, 191, 36, 0.15)',
    color: 'var(--warning)',
  },
  statusWaitlisted: {
    background: 'rgba(248, 113, 113, 0.15)',
    color: 'var(--error)',
  },
  statusCancelled: {
    background: 'var(--bg-inset)',
    color: 'var(--text-muted)',
  },
  
  bookingMeta: {
    display: 'flex',
    gap: 24,
    marginBottom: 16,
    flexWrap: 'wrap',
  },
  metaItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    fontSize: 13,
    color: 'var(--text-secondary)',
  },
  
  bookingRoute: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '12px 16px',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-md)',
    marginBottom: 16,
  },
  stationCode: {
    fontSize: 18,
    fontWeight: 700,
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
  },
  routeArrow: {
    flex: 1,
    height: 2,
    background: 'var(--border)',
    position: 'relative',
  },
  
  bookingFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  fare: {
    fontSize: 20,
    fontWeight: 700,
    color: 'var(--accent-blue)',
  },
  actions: {
    display: 'flex',
    gap: 8,
  },
  actionButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '8px 14px',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-secondary)',
    fontSize: 13,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  actionButtonDanger: {
    color: 'var(--error)',
    borderColor: 'rgba(248, 113, 113, 0.3)',
  },
  
  // Empty state
  emptyState: {
    textAlign: 'center',
    padding: '60px 20px',
    background: 'var(--bg-elevated)',
    borderRadius: 'var(--radius-xl)',
    border: '1px solid var(--border)',
  },
  emptyIcon: {
    width: 64,
    height: 64,
    margin: '0 auto 16px',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-full)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--text-muted)',
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: 'var(--text-muted)',
    marginBottom: 24,
  },
  emptyButton: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    padding: '12px 24px',
    background: 'var(--accent-blue)',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    color: 'white',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  },
  
  // Loading
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 60,
    color: 'var(--text-muted)',
  },
  
  // Modal
  modalOverlay: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0, 0, 0, 0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: 24,
  },
  modal: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-xl)',
    padding: 24,
    maxWidth: 400,
    width: '100%',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: 12,
  },
  modalText: {
    fontSize: 14,
    color: 'var(--text-secondary)',
    marginBottom: 24,
  },
  modalActions: {
    display: 'flex',
    gap: 12,
    justifyContent: 'flex-end',
  },
  modalButton: {
    padding: '10px 20px',
    borderRadius: 'var(--radius-md)',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  },
};

const statusFilters = [
  { value: '', label: 'All' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'rac', label: 'RAC' },
  { value: 'waitlisted', label: 'Waitlisted' },
  { value: 'cancelled', label: 'Cancelled' },
];

export default function MyBookingsPage() {
  const navigate = useNavigate();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [cancelModal, setCancelModal] = useState(null);
  const [cancelling, setCancelling] = useState(false);
  
  const fetchBookings = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get('/bookings/my', {
        params: { status: statusFilter || undefined },
      });
      
      if (response.data?.status === 'success') {
        setBookings(response.data.data?.bookings || []);
      }
    } catch (err) {
      console.error('Failed to fetch bookings:', err);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);
  
  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);
  
  const handleCancel = async () => {
    if (!cancelModal) return;
    
    setCancelling(true);
    try {
      const response = await api.post(`/bookings/${cancelModal.id}/cancel`);
      
      if (response.data?.status === 'success') {
        setCancelModal(null);
        fetchBookings();
      }
    } catch (err) {
      console.error('Cancellation failed:', err);
    } finally {
      setCancelling(false);
    }
  };
  
  const getStatusStyle = (status) => {
    switch (status?.toLowerCase()) {
      case 'confirmed': return styles.statusConfirmed;
      case 'rac': return styles.statusRac;
      case 'waitlisted': return styles.statusWaitlisted;
      case 'cancelled': return styles.statusCancelled;
      default: return {};
    }
  };
  
  // Calculate stats
  const stats = {
    total: bookings.length,
    confirmed: bookings.filter(b => b.status === 'confirmed').length,
    upcoming: bookings.filter(b => b.status !== 'cancelled').length,
    cancelled: bookings.filter(b => b.status === 'cancelled').length,
  };
  
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>My Bookings</h1>
        <p style={styles.subtitle}>View and manage your train bookings</p>
      </header>
      
      {/* Stats */}
      <div style={styles.statsRow}>
        <div style={styles.statCard}>
          <div style={styles.statValue}>{stats.total}</div>
          <div style={styles.statLabel}>Total Bookings</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: 'var(--success)' }}>{stats.confirmed}</div>
          <div style={styles.statLabel}>Confirmed</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: 'var(--accent-blue)' }}>{stats.upcoming}</div>
          <div style={styles.statLabel}>Active</div>
        </div>
        <div style={styles.statCard}>
          <div style={{ ...styles.statValue, color: 'var(--text-muted)' }}>{stats.cancelled}</div>
          <div style={styles.statLabel}>Cancelled</div>
        </div>
      </div>
      
      {/* Filters */}
      <div style={styles.filterBar}>
        {statusFilters.map((filter) => (
          <button
            key={filter.value}
            style={{
              ...styles.filterChip,
              ...(statusFilter === filter.value ? styles.filterChipActive : {}),
            }}
            onClick={() => setStatusFilter(filter.value)}
          >
            {filter.label}
          </button>
        ))}
      </div>
      
      {/* Loading */}
      {loading && (
        <div style={styles.loading}>
          <Icons.Loader />
          Loading bookings...
        </div>
      )}
      
      {/* Bookings List */}
      {!loading && bookings.length === 0 && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>
            <Icons.Ticket />
          </div>
          <h3 style={styles.emptyTitle}>No bookings found</h3>
          <p style={styles.emptyText}>
            {statusFilter ? 'No bookings match this filter' : "You haven't made any bookings yet"}
          </p>
          <button style={styles.emptyButton} onClick={() => navigate('/search')}>
            <Icons.Train />
            Book a Train
          </button>
        </div>
      )}
      
      {!loading && bookings.map((booking) => (
        <div key={booking.id} style={styles.bookingCard}>
          <div style={styles.bookingHeader}>
            <div>
              <div style={styles.bookingPnr}>PNR: {booking.pnr}</div>
              <div style={styles.bookingTrain}>
                <Icons.Train />
                {booking.train_name || booking.train_number}
              </div>
            </div>
            <span style={{ ...styles.statusBadge, ...getStatusStyle(booking.status) }}>
              {booking.status}
            </span>
          </div>
          
          <div style={styles.bookingMeta}>
            <div style={styles.metaItem}>
              <Icons.Calendar />
              {booking.journey_date}
            </div>
            <div style={styles.metaItem}>
              <Icons.Users />
              {booking.passengers} passenger{booking.passengers !== 1 ? 's' : ''}
            </div>
            <div style={styles.metaItem}>
              <Icons.Ticket />
              Class: {booking.class}
            </div>
          </div>
          
          <div style={styles.bookingRoute}>
            <span style={styles.stationCode}>{booking.from}</span>
            <div style={styles.routeArrow} />
            <span style={styles.stationCode}>{booking.to}</span>
          </div>
          
          <div style={styles.bookingFooter}>
            <span style={styles.fare}>₹{booking.total_fare}</span>
            <div style={styles.actions}>
              <button 
                style={styles.actionButton}
                onClick={() => navigate(`/booking/${booking.id}`)}
              >
                <Icons.Eye />
                View
              </button>
              {booking.status !== 'cancelled' && (
                <button 
                  style={{ ...styles.actionButton, ...styles.actionButtonDanger }}
                  onClick={() => setCancelModal(booking)}
                >
                  <Icons.X />
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
      
      {/* Cancel Modal */}
      {cancelModal && (
        <div style={styles.modalOverlay} onClick={() => setCancelModal(null)}>
          <div style={styles.modal} onClick={(e) => e.stopPropagation()}>
            <div style={{ color: 'var(--warning)', marginBottom: 16 }}>
              <Icons.AlertCircle />
            </div>
            <h3 style={styles.modalTitle}>Cancel Booking?</h3>
            <p style={styles.modalText}>
              Are you sure you want to cancel PNR {cancelModal.pnr}? 
              Cancellation charges may apply based on the time of cancellation.
            </p>
            <div style={styles.modalActions}>
              <button
                style={{ ...styles.modalButton, background: 'var(--bg-inset)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
                onClick={() => setCancelModal(null)}
              >
                Keep Booking
              </button>
              <button
                style={{ ...styles.modalButton, background: 'var(--error)', border: 'none', color: 'white' }}
                onClick={handleCancel}
                disabled={cancelling}
              >
                {cancelling ? 'Cancelling...' : 'Yes, Cancel'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

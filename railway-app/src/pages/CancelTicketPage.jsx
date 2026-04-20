/**
 * CancelTicketPage - Ticket cancellation with refund preview.
 */
import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

const styles = {
  page: {
    minHeight: '100vh',
    background: 'var(--bg-base, #0f0f0f)',
    padding: '32px 24px',
  },
  container: {
    maxWidth: 700,
    margin: '0 auto',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: 700,
    color: 'var(--text-primary, #fff)',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 14,
    color: 'var(--text-muted, #6b7280)',
  },
  card: {
    background: 'var(--bg-elevated, #1a1a1a)',
    borderRadius: 16,
    border: '1px solid var(--border, #2a2a2a)',
    padding: 24,
    marginBottom: 24,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: 600,
    color: 'var(--text-primary, #fff)',
    marginBottom: 20,
    paddingBottom: 16,
    borderBottom: '1px solid var(--border, #2a2a2a)',
  },
  searchBox: {
    display: 'flex',
    gap: 12,
    marginBottom: 24,
  },
  input: {
    flex: 1,
    padding: '14px 18px',
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    borderRadius: 10,
    color: 'var(--text-primary, #fff)',
    fontSize: 15,
    outline: 'none',
    fontFamily: 'monospace',
    letterSpacing: 2,
  },
  btn: {
    padding: '14px 24px',
    borderRadius: 10,
    border: 'none',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  btnPrimary: {
    background: 'var(--accent-blue, #3b82f6)',
    color: '#fff',
  },
  btnDanger: {
    background: 'rgba(239, 68, 68, 0.15)',
    color: '#ef4444',
    border: '1px solid rgba(239, 68, 68, 0.3)',
  },
  btnSecondary: {
    background: 'var(--bg-inset, #252525)',
    border: '1px solid var(--border, #2a2a2a)',
    color: 'var(--text-secondary, #9ca3af)',
  },
  infoRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 0',
    borderBottom: '1px solid var(--border, #2a2a2a)',
  },
  infoLabel: {
    fontSize: 13,
    color: 'var(--text-muted, #6b7280)',
  },
  infoValue: {
    fontSize: 14,
    fontWeight: 500,
    color: 'var(--text-primary, #fff)',
  },
  trainHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    marginBottom: 20,
  },
  trainNumber: {
    background: 'var(--accent-blue, #3b82f6)',
    color: '#fff',
    padding: '8px 14px',
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 700,
  },
  trainName: {
    fontSize: 18,
    fontWeight: 600,
    color: 'var(--text-primary, #fff)',
  },
  journeyInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: 20,
    padding: '16px 0',
    marginBottom: 16,
  },
  station: {
    flex: 1,
  },
  stationCode: {
    fontSize: 20,
    fontWeight: 700,
    color: 'var(--text-primary, #fff)',
  },
  stationName: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
    marginTop: 4,
  },
  stationTime: {
    fontSize: 13,
    color: 'var(--text-secondary, #9ca3af)',
    marginTop: 4,
  },
  arrow: {
    fontSize: 24,
    color: 'var(--text-muted, #6b7280)',
  },
  passengerList: {
    marginTop: 16,
  },
  passengerItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '12px 16px',
    background: 'var(--bg-inset, #252525)',
    borderRadius: 10,
    marginBottom: 8,
  },
  passengerCheckbox: {
    marginRight: 12,
  },
  passengerInfo: {
    flex: 1,
  },
  passengerName: {
    fontSize: 14,
    fontWeight: 500,
    color: 'var(--text-primary, #fff)',
  },
  passengerDetails: {
    fontSize: 12,
    color: 'var(--text-muted, #6b7280)',
    marginTop: 2,
  },
  refundSection: {
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.2)',
    borderRadius: 12,
    padding: 20,
    marginTop: 24,
  },
  refundTitle: {
    fontSize: 14,
    fontWeight: 600,
    color: '#ef4444',
    marginBottom: 16,
  },
  refundRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
  },
  refundLabel: {
    fontSize: 13,
    color: 'var(--text-secondary, #9ca3af)',
  },
  refundValue: {
    fontSize: 14,
    color: 'var(--text-primary, #fff)',
  },
  refundTotal: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 0 0',
    marginTop: 12,
    borderTop: '1px solid rgba(239, 68, 68, 0.3)',
  },
  refundTotalLabel: {
    fontSize: 15,
    fontWeight: 600,
    color: '#ef4444',
  },
  refundTotalValue: {
    fontSize: 20,
    fontWeight: 700,
    color: '#22c55e',
  },
  warning: {
    display: 'flex',
    alignItems: 'flex-start',
    gap: 12,
    padding: 16,
    background: 'rgba(245, 158, 11, 0.1)',
    border: '1px solid rgba(245, 158, 11, 0.2)',
    borderRadius: 10,
    marginTop: 20,
  },
  warningIcon: {
    color: '#f59e0b',
    fontSize: 20,
  },
  warningText: {
    fontSize: 13,
    color: 'var(--text-secondary, #9ca3af)',
    lineHeight: 1.5,
  },
  actions: {
    display: 'flex',
    gap: 12,
    justifyContent: 'flex-end',
    marginTop: 24,
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
  error: {
    padding: 16,
    background: 'rgba(239, 68, 68, 0.1)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: 10,
    color: '#ef4444',
    marginBottom: 20,
  },
  success: {
    padding: 24,
    background: 'rgba(34, 197, 94, 0.1)',
    border: '1px solid rgba(34, 197, 94, 0.3)',
    borderRadius: 12,
    textAlign: 'center',
  },
  successIcon: {
    fontSize: 48,
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 20,
    fontWeight: 600,
    color: '#22c55e',
    marginBottom: 8,
  },
  successMessage: {
    fontSize: 14,
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
  badgeConfirmed: { background: 'rgba(34, 197, 94, 0.15)', color: '#22c55e' },
  badgeWaitlisted: { background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' },
  badgeCancelled: { background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444' },
};

function getStatusBadge(status) {
  const s = (status || '').toLowerCase();
  if (s === 'confirmed' || s === 'cnf') return { ...styles.badge, ...styles.badgeConfirmed };
  if (s === 'waitlisted' || s === 'wl') return { ...styles.badge, ...styles.badgeWaitlisted };
  if (s === 'cancelled') return { ...styles.badge, ...styles.badgeCancelled };
  return styles.badge;
}

export default function CancelTicketPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [pnr, setPnr] = useState(searchParams.get('pnr') || '');
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [selectedPassengers, setSelectedPassengers] = useState([]);
  const [cancelling, setCancelling] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  const [refundDetails, setRefundDetails] = useState(null);

  useEffect(() => {
    if (searchParams.get('pnr')) {
      handleSearch();
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = async () => {
    if (!pnr.trim()) {
      setError('Please enter a PNR number');
      return;
    }
    setLoading(true);
    setError('');
    setBooking(null);
    setCancelled(false);
    try {
      const res = await api.get(`/bookings/pnr/${pnr.trim()}`);
      const data = res.data?.data || res.data;
      if (data && (data.ROWID || data.Booking_ID)) {
        setBooking(data);
        // Calculate refund based on cancellation policy
        calculateRefund(data);
      } else {
        setError('Booking not found');
      }
    } catch (err) {
      console.error('Search failed:', err);
      setError(err.response?.data?.message || 'Failed to find booking');
    } finally {
      setLoading(false);
    }
  };

  const calculateRefund = (bookingData) => {
    const totalFare = parseFloat(bookingData.Total_Fare || 0);
    const journeyDate = new Date(bookingData.Journey_Date);
    const now = new Date();
    const hoursToJourney = (journeyDate - now) / (1000 * 60 * 60);

    let cancellationCharge = 0;
    let chargePercent = 0;

    // Indian Railways-like cancellation policy
    if (hoursToJourney > 48) {
      chargePercent = 10; // More than 48 hours: 10% charge
    } else if (hoursToJourney > 12) {
      chargePercent = 25; // 12-48 hours: 25% charge
    } else if (hoursToJourney > 4) {
      chargePercent = 50; // 4-12 hours: 50% charge
    } else {
      chargePercent = 75; // Less than 4 hours: 75% charge
    }

    cancellationCharge = (totalFare * chargePercent) / 100;
    const refundAmount = totalFare - cancellationCharge;

    setRefundDetails({
      totalFare,
      chargePercent,
      cancellationCharge,
      refundAmount,
      hoursToJourney: Math.max(0, Math.floor(hoursToJourney)),
    });
  };

  const togglePassenger = (passengerId) => {
    setSelectedPassengers((prev) =>
      prev.includes(passengerId)
        ? prev.filter((id) => id !== passengerId)
        : [...prev, passengerId]
    );
  };

  const selectAllPassengers = () => {
    const passengers = booking?.Passengers || [];
    if (selectedPassengers.length === passengers.length) {
      setSelectedPassengers([]);
    } else {
      setSelectedPassengers(passengers.map((p, i) => p.Passenger_ID || i));
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this booking? This action cannot be undone.')) {
      return;
    }
    setCancelling(true);
    setError('');
    try {
      const bookingId = booking.ROWID || booking.Booking_ID;
      await api.put(`/bookings/${bookingId}/cancel`, {
        passengers: selectedPassengers.length > 0 ? selectedPassengers : 'all',
      });
      setCancelled(true);
    } catch (err) {
      console.error('Cancellation failed:', err);
      setError(err.response?.data?.message || 'Failed to cancel booking');
    } finally {
      setCancelling(false);
    }
  };

  const passengers = booking?.Passengers || [];

  if (cancelled) {
    return (
      <div style={styles.page}>
        <div style={styles.container}>
          <div style={styles.card}>
            <div style={styles.success}>
              <div style={styles.successIcon}>✓</div>
              <div style={styles.successTitle}>Booking Cancelled Successfully</div>
              <div style={styles.successMessage}>
                Your refund of ₹{refundDetails?.refundAmount?.toFixed(2)} will be processed within 5-7 business days.
              </div>
              <div style={{ marginTop: 24 }}>
                <button
                  style={{ ...styles.btn, ...styles.btnPrimary }}
                  onClick={() => navigate('/my-bookings')}
                >
                  View My Bookings
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>Cancel Ticket</h1>
          <p style={styles.subtitle}>Enter your PNR to cancel and view refund details</p>
        </div>

        <div style={styles.card}>
          <div style={styles.searchBox}>
            <input
              type="text"
              placeholder="Enter PNR Number"
              value={pnr}
              onChange={(e) => setPnr(e.target.value.toUpperCase())}
              style={styles.input}
              maxLength={10}
            />
            <button
              style={{ ...styles.btn, ...styles.btnPrimary }}
              onClick={handleSearch}
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>

          {error && <div style={styles.error}>{error}</div>}

          {loading && <div style={styles.loading}>Searching...</div>}
        </div>

        {booking && (
          <>
            <div style={styles.card}>
              <div style={styles.cardTitle}>Booking Details</div>

              <div style={styles.trainHeader}>
                <div style={styles.trainNumber}>{booking.Train_Number || 'N/A'}</div>
                <div style={styles.trainName}>{booking.Train_Name || 'Train Name'}</div>
                <span style={getStatusBadge(booking.Booking_Status)}>{booking.Booking_Status}</span>
              </div>

              <div style={styles.journeyInfo}>
                <div style={styles.station}>
                  <div style={styles.stationCode}>{booking.Source_Station || 'SRC'}</div>
                  <div style={styles.stationName}>{booking.Source_Station_Name || ''}</div>
                  <div style={styles.stationTime}>{booking.Departure_Time || ''}</div>
                </div>
                <div style={styles.arrow}>→</div>
                <div style={{ ...styles.station, textAlign: 'right' }}>
                  <div style={styles.stationCode}>{booking.Destination_Station || 'DST'}</div>
                  <div style={styles.stationName}>{booking.Destination_Station_Name || ''}</div>
                  <div style={styles.stationTime}>{booking.Arrival_Time || ''}</div>
                </div>
              </div>

              <div style={styles.infoRow}>
                <span style={styles.infoLabel}>Journey Date</span>
                <span style={styles.infoValue}>{booking.Journey_Date}</span>
              </div>
              <div style={styles.infoRow}>
                <span style={styles.infoLabel}>Class</span>
                <span style={styles.infoValue}>{booking.Class_Type || 'SL'}</span>
              </div>
              <div style={styles.infoRow}>
                <span style={styles.infoLabel}>PNR</span>
                <span style={{ ...styles.infoValue, fontFamily: 'monospace' }}>{booking.PNR_Number}</span>
              </div>
            </div>

            {passengers.length > 0 && (
              <div style={styles.card}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                  <div style={styles.cardTitle}>Select Passengers to Cancel</div>
                  <button style={styles.btnSecondary} onClick={selectAllPassengers}>
                    {selectedPassengers.length === passengers.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>

                <div style={styles.passengerList}>
                  {passengers.map((passenger, idx) => (
                    <div key={passenger.Passenger_ID || idx} style={styles.passengerItem}>
                      <input
                        type="checkbox"
                        checked={selectedPassengers.includes(passenger.Passenger_ID || idx)}
                        onChange={() => togglePassenger(passenger.Passenger_ID || idx)}
                        style={styles.passengerCheckbox}
                      />
                      <div style={styles.passengerInfo}>
                        <div style={styles.passengerName}>{passenger.Passenger_Name}</div>
                        <div style={styles.passengerDetails}>
                          {passenger.Age} yrs, {passenger.Gender} • Seat: {passenger.Seat_Number || 'WL'}
                        </div>
                      </div>
                      <span style={getStatusBadge(passenger.Booking_Status || booking.Booking_Status)}>
                        {passenger.Booking_Status || booking.Booking_Status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {refundDetails && (
              <div style={styles.card}>
                <div style={styles.refundSection}>
                  <div style={styles.refundTitle}>Cancellation & Refund Details</div>

                  <div style={styles.refundRow}>
                    <span style={styles.refundLabel}>Time until journey</span>
                    <span style={styles.refundValue}>{refundDetails.hoursToJourney} hours</span>
                  </div>
                  <div style={styles.refundRow}>
                    <span style={styles.refundLabel}>Original Fare</span>
                    <span style={styles.refundValue}>₹{refundDetails.totalFare.toFixed(2)}</span>
                  </div>
                  <div style={styles.refundRow}>
                    <span style={styles.refundLabel}>Cancellation Charge ({refundDetails.chargePercent}%)</span>
                    <span style={{ ...styles.refundValue, color: '#ef4444' }}>
                      -₹{refundDetails.cancellationCharge.toFixed(2)}
                    </span>
                  </div>

                  <div style={styles.refundTotal}>
                    <span style={styles.refundTotalLabel}>Estimated Refund</span>
                    <span style={styles.refundTotalValue}>₹{refundDetails.refundAmount.toFixed(2)}</span>
                  </div>
                </div>

                <div style={styles.warning}>
                  <span style={styles.warningIcon}>⚠</span>
                  <span style={styles.warningText}>
                    Cancellation charges are calculated based on Indian Railways policy. 
                    Refund will be credited to your original payment method within 5-7 business days.
                    This action cannot be undone.
                  </span>
                </div>

                <div style={styles.actions}>
                  <button
                    style={{ ...styles.btn, ...styles.btnSecondary }}
                    onClick={() => navigate('/my-bookings')}
                  >
                    Go Back
                  </button>
                  <button
                    style={{ ...styles.btn, ...styles.btnDanger }}
                    onClick={handleCancel}
                    disabled={cancelling || (passengers.length > 0 && selectedPassengers.length === 0)}
                  >
                    {cancelling ? 'Cancelling...' : 'Confirm Cancellation'}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

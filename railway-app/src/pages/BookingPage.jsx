/**
 * BookingPage.jsx — Booking flow for train tickets.
 * 
 * Features:
 *   - Passenger details form
 *   - Fare calculation display
 *   - Booking confirmation
 */

import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/SessionAuthContext';
import api from '../services/api';

// Icons
const Icons = {
  Train: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="4" y="3" width="16" height="16" rx="2" />
      <path d="M4 11h16" /><path d="M12 3v8" />
      <circle cx="8" cy="15" r="1" /><circle cx="16" cy="15" r="1" />
    </svg>
  ),
  User: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  Plus: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="12" y1="5" x2="12" y2="19" />
      <line x1="5" y1="12" x2="19" y2="12" />
    </svg>
  ),
  Trash: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
    </svg>
  ),
  Check: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  ArrowLeft: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  ),
  Loader: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  ),
};

const styles = {
  container: {
    maxWidth: 1000,
    margin: '0 auto',
  },
  backButton: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    padding: '8px 12px',
    background: 'none',
    border: 'none',
    color: 'var(--text-secondary)',
    fontSize: 14,
    cursor: 'pointer',
    marginBottom: 16,
    transition: 'color 0.2s',
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
  
  // Train summary card
  trainSummary: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: 20,
    marginBottom: 24,
    display: 'flex',
    alignItems: 'center',
    gap: 16,
  },
  trainIcon: {
    width: 48,
    height: 48,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--accent-blue)',
  },
  trainDetails: {
    flex: 1,
  },
  trainName: {
    fontSize: 18,
    fontWeight: 700,
    color: 'var(--text-primary)',
  },
  trainMeta: {
    fontSize: 13,
    color: 'var(--text-muted)',
    marginTop: 4,
  },
  journeyBadge: {
    padding: '8px 16px',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-md)',
    fontSize: 13,
    color: 'var(--text-secondary)',
  },
  
  // Two column layout
  grid: {
    display: 'grid',
    gridTemplateColumns: '1fr 360px',
    gap: 24,
  },
  
  // Passengers section
  section: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: 24,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: 16,
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  
  passengerCard: {
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: 16,
    marginBottom: 12,
  },
  passengerHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  passengerNumber: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-secondary)',
  },
  removeButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 4,
    padding: '6px 10px',
    background: 'none',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--error)',
    fontSize: 12,
    cursor: 'pointer',
  },
  passengerFields: {
    display: 'grid',
    gridTemplateColumns: '1fr 80px 100px 120px',
    gap: 12,
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  label: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
  },
  input: {
    padding: '10px 12px',
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-primary)',
    fontSize: 14,
    fontFamily: 'var(--font-body)',
    outline: 'none',
  },
  select: {
    padding: '10px 12px',
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-primary)',
    fontSize: 14,
    fontFamily: 'var(--font-body)',
    outline: 'none',
    cursor: 'pointer',
  },
  
  addPassengerButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    width: '100%',
    padding: '12px',
    background: 'none',
    border: '2px dashed var(--border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-secondary)',
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  
  // Fare summary
  fareCard: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: 24,
    position: 'sticky',
    top: 24,
  },
  fareRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 0',
    fontSize: 14,
    color: 'var(--text-secondary)',
    borderBottom: '1px solid var(--border)',
  },
  fareTotal: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px 0',
    fontSize: 18,
    fontWeight: 700,
    color: 'var(--text-primary)',
  },
  
  bookButton: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    width: '100%',
    padding: '16px',
    background: 'var(--accent-blue)',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    color: 'white',
    fontSize: 16,
    fontWeight: 600,
    cursor: 'pointer',
    marginTop: 16,
    transition: 'all 0.2s',
  },
  bookButtonDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  
  // Error
  error: {
    padding: 16,
    background: 'rgba(248, 113, 113, 0.1)',
    border: '1px solid rgba(248, 113, 113, 0.3)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--error)',
    fontSize: 14,
    marginBottom: 24,
  },
  
  // Success
  success: {
    textAlign: 'center',
    padding: 48,
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-xl)',
  },
  successIcon: {
    width: 64,
    height: 64,
    margin: '0 auto 24px',
    background: 'rgba(74, 222, 128, 0.15)',
    borderRadius: 'var(--radius-full)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--success)',
  },
  successTitle: {
    fontSize: 24,
    fontWeight: 800,
    color: 'var(--text-primary)',
    marginBottom: 8,
  },
  pnrDisplay: {
    fontSize: 32,
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
    color: 'var(--accent-blue)',
    margin: '16px 0',
  },
};

const emptyPassenger = {
  Name: '',
  Age: '',
  Gender: 'M',
  Berth_Preference: '',
};

export default function BookingPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();
  
  const { train, travelClass, journeyDate, from, to } = location.state || {};
  
  const [passengers, setPassengers] = useState([{ ...emptyPassenger }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [fareData, setFareData] = useState(null);
  const [bookingResult, setBookingResult] = useState(null);
  
  // Redirect if no train selected
  useEffect(() => {
    if (!train) {
      navigate('/search');
    }
  }, [train, navigate]);
  
  // Fetch fare when passengers change
  useEffect(() => {
    if (!train || passengers.length === 0) return;
    
    const fetchFare = async () => {
      try {
        const adults = passengers.filter(p => parseInt(p.Age) >= 12 && parseInt(p.Age) < 60).length;
        const children = passengers.filter(p => parseInt(p.Age) >= 5 && parseInt(p.Age) < 12).length;
        const seniors = passengers.filter(p => parseInt(p.Age) >= 60).length;
        
        const response = await api.get('/fares/calculate', {
          params: {
            trainId: train.ROWID,
            fromStation: from,
            toStation: to,
            travelClass: travelClass,
            adults: adults || 1,
            children,
            seniors,
          },
        });
        
        if (response.data?.status === 'success') {
          setFareData(response.data.data);
        }
      } catch (err) {
        console.error('Fare fetch error:', err);
      }
    };
    
    const timeout = setTimeout(fetchFare, 500);
    return () => clearTimeout(timeout);
  }, [train, passengers, travelClass, from, to]);
  
  const addPassenger = () => {
    if (passengers.length < 6) {
      setPassengers([...passengers, { ...emptyPassenger }]);
    }
  };
  
  const removePassenger = (index) => {
    if (passengers.length > 1) {
      setPassengers(passengers.filter((_, i) => i !== index));
    }
  };
  
  const updatePassenger = (index, field, value) => {
    const updated = [...passengers];
    updated[index] = { ...updated[index], [field]: value };
    setPassengers(updated);
  };
  
  const validatePassengers = () => {
    for (let i = 0; i < passengers.length; i++) {
      const p = passengers[i];
      if (!p.Name?.trim()) {
        setError(`Passenger ${i + 1}: Name is required`);
        return false;
      }
      if (!p.Age || isNaN(parseInt(p.Age)) || parseInt(p.Age) < 1) {
        setError(`Passenger ${i + 1}: Valid age is required`);
        return false;
      }
    }
    return true;
  };
  
  const handleBook = async () => {
    setError(null);
    
    if (!validatePassengers()) return;
    
    setLoading(true);
    
    try {
      const response = await api.post('/bookings', {
        trainId: train.ROWID,
        fromStation: from,
        toStation: to,
        journeyDate,
        travelClass,
        quota: 'GN',
        passengers,
        contactEmail: user?.email || user?.Email,
        contactPhone: user?.phoneNumber || user?.Phone_Number,
      });
      
      if (response.data?.status === 'success') {
        setBookingResult(response.data.data);
      } else {
        setError(response.data?.message || 'Booking failed');
      }
    } catch (err) {
      setError(err.message || 'Failed to create booking');
    } finally {
      setLoading(false);
    }
  };
  
  if (!train) return null;
  
  // Success state
  if (bookingResult) {
    return (
      <div style={styles.container}>
        <div style={styles.success}>
          <div style={styles.successIcon}>
            <Icons.Check />
          </div>
          <h2 style={styles.successTitle}>Booking Confirmed!</h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: 8 }}>Your PNR number is</p>
          <div style={styles.pnrDisplay}>{bookingResult.pnr}</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>
            Status: <strong style={{ color: 'var(--success)' }}>{bookingResult.status?.toUpperCase()}</strong>
          </p>
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
            <button
              style={{ ...styles.bookButton, maxWidth: 200 }}
              onClick={() => navigate('/my-bookings')}
            >
              View My Bookings
            </button>
            <button
              style={{ ...styles.bookButton, maxWidth: 200, background: 'var(--bg-inset)', color: 'var(--text-primary)' }}
              onClick={() => navigate('/search')}
            >
              Book Another
            </button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div style={styles.container}>
      <button style={styles.backButton} onClick={() => navigate(-1)}>
        <Icons.ArrowLeft />
        Back to Search
      </button>
      
      <header style={styles.header}>
        <h1 style={styles.title}>Complete Your Booking</h1>
      </header>
      
      {/* Train Summary */}
      <div style={styles.trainSummary}>
        <div style={styles.trainIcon}>
          <Icons.Train />
        </div>
        <div style={styles.trainDetails}>
          <div style={styles.trainName}>{train.Train_Name}</div>
          <div style={styles.trainMeta}>
            #{train.Train_Number} • {train.Train_Type || 'Express'} • {travelClass}
          </div>
        </div>
        <div style={styles.journeyBadge}>
          {from} → {to} • {journeyDate}
        </div>
      </div>
      
      {error && <div style={styles.error}>{error}</div>}
      
      <div style={styles.grid}>
        {/* Left column - Passengers */}
        <div>
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>
              <Icons.User />
              Passenger Details
            </h3>
            
            {passengers.map((passenger, index) => (
              <div key={index} style={styles.passengerCard}>
                <div style={styles.passengerHeader}>
                  <span style={styles.passengerNumber}>Passenger {index + 1}</span>
                  {passengers.length > 1 && (
                    <button style={styles.removeButton} onClick={() => removePassenger(index)}>
                      <Icons.Trash />
                      Remove
                    </button>
                  )}
                </div>
                
                <div style={styles.passengerFields}>
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Full Name</label>
                    <input
                      type="text"
                      placeholder="As per ID"
                      value={passenger.Name}
                      onChange={(e) => updatePassenger(index, 'Name', e.target.value)}
                      style={styles.input}
                    />
                  </div>
                  
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Age</label>
                    <input
                      type="number"
                      placeholder="Age"
                      value={passenger.Age}
                      onChange={(e) => updatePassenger(index, 'Age', e.target.value)}
                      style={styles.input}
                      min="1"
                      max="120"
                    />
                  </div>
                  
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Gender</label>
                    <select
                      value={passenger.Gender}
                      onChange={(e) => updatePassenger(index, 'Gender', e.target.value)}
                      style={styles.select}
                    >
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                  </div>
                  
                  <div style={styles.inputGroup}>
                    <label style={styles.label}>Berth Pref</label>
                    <select
                      value={passenger.Berth_Preference}
                      onChange={(e) => updatePassenger(index, 'Berth_Preference', e.target.value)}
                      style={styles.select}
                    >
                      <option value="">No Pref</option>
                      <option value="Lower">Lower</option>
                      <option value="Middle">Middle</option>
                      <option value="Upper">Upper</option>
                      <option value="Side Lower">Side Lower</option>
                      <option value="Side Upper">Side Upper</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
            
            {passengers.length < 6 && (
              <button style={styles.addPassengerButton} onClick={addPassenger}>
                <Icons.Plus />
                Add Passenger
              </button>
            )}
          </div>
        </div>
        
        {/* Right column - Fare Summary */}
        <div>
          <div style={styles.fareCard}>
            <h3 style={styles.sectionTitle}>Fare Summary</h3>
            
            {fareData ? (
              <>
                <div style={styles.fareRow}>
                  <span>Base Fare ({passengers.length} pax)</span>
                  <span>₹{fareData.per_passenger?.base_fare * passengers.length || 0}</span>
                </div>
                <div style={styles.fareRow}>
                  <span>Reservation Charges</span>
                  <span>₹{fareData.per_passenger?.reservation_charge * passengers.length || 0}</span>
                </div>
                {fareData.per_passenger?.superfast_surcharge > 0 && (
                  <div style={styles.fareRow}>
                    <span>Superfast Surcharge</span>
                    <span>₹{fareData.per_passenger?.superfast_surcharge * passengers.length}</span>
                  </div>
                )}
                {fareData.per_passenger?.gst > 0 && (
                  <div style={styles.fareRow}>
                    <span>GST (5%)</span>
                    <span>₹{fareData.per_passenger?.gst * passengers.length}</span>
                  </div>
                )}
                <div style={styles.fareTotal}>
                  <span>Total Amount</span>
                  <span style={{ color: 'var(--accent-blue)' }}>
                    ₹{fareData.total || 0}
                  </span>
                </div>
              </>
            ) : (
              <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
                Calculating fare...
              </div>
            )}
            
            <button
              style={{
                ...styles.bookButton,
                ...(loading ? styles.bookButtonDisabled : {}),
              }}
              onClick={handleBook}
              disabled={loading}
            >
              {loading ? (
                <>
                  <Icons.Loader />
                  Processing...
                </>
              ) : (
                <>
                  <Icons.Check />
                  Confirm Booking
                </>
              )}
            </button>
            
            <p style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', marginTop: 12 }}>
              By booking, you agree to our Terms & Conditions
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

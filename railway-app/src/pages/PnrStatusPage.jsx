/**
 * PnrStatusPage.jsx — Check PNR status.
 */

import React, { useState } from 'react';
import api from '../services/api';

const Icons = {
  Search: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  ),
  Ticket: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
    </svg>
  ),
  Loader: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  ),
  Check: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  X: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
};

const styles = {
  container: {
    maxWidth: 800,
    margin: '0 auto',
  },
  header: {
    textAlign: 'center',
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
  
  searchCard: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-xl)',
    padding: 32,
    marginBottom: 32,
  },
  searchForm: {
    display: 'flex',
    gap: 16,
  },
  input: {
    flex: 1,
    padding: '16px 20px',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-primary)',
    fontSize: 18,
    fontFamily: 'var(--font-mono)',
    letterSpacing: 2,
    textTransform: 'uppercase',
    outline: 'none',
  },
  button: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '16px 32px',
    background: 'var(--accent-blue)',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    color: 'white',
    fontSize: 16,
    fontWeight: 600,
    cursor: 'pointer',
  },
  
  // Result card
  resultCard: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-xl)',
    overflow: 'hidden',
  },
  resultHeader: {
    padding: 24,
    borderBottom: '1px solid var(--border)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  pnrDisplay: {
    fontSize: 24,
    fontWeight: 700,
    fontFamily: 'var(--font-mono)',
    color: 'var(--text-primary)',
  },
  statusBadge: {
    padding: '6px 16px',
    borderRadius: 'var(--radius-full)',
    fontSize: 13,
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
  
  resultBody: {
    padding: 24,
  },
  trainInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: 16,
    marginBottom: 24,
  },
  trainIcon: {
    width: 56,
    height: 56,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--accent-blue)',
  },
  trainName: {
    fontSize: 20,
    fontWeight: 700,
    color: 'var(--text-primary)',
  },
  trainMeta: {
    fontSize: 14,
    color: 'var(--text-muted)',
    marginTop: 4,
  },
  
  journeyInfo: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 16,
    padding: 20,
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-md)',
    marginBottom: 24,
  },
  infoItem: {},
  infoLabel: {
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    marginBottom: 4,
  },
  infoValue: {
    fontSize: 16,
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  
  // Passengers table
  passengerTable: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '12px 16px',
    background: 'var(--bg-inset)',
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
  },
  td: {
    padding: '16px',
    borderBottom: '1px solid var(--border)',
    fontSize: 14,
    color: 'var(--text-primary)',
  },
  passengerStatus: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 6,
    padding: '4px 10px',
    borderRadius: 'var(--radius-sm)',
    fontSize: 13,
    fontWeight: 600,
  },
  
  // Error
  error: {
    padding: 20,
    background: 'rgba(248, 113, 113, 0.1)',
    border: '1px solid rgba(248, 113, 113, 0.3)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--error)',
    fontSize: 14,
    textAlign: 'center',
  },
  
  // Empty state
  emptyState: {
    textAlign: 'center',
    padding: 48,
    color: 'var(--text-muted)',
  },
};

export default function PnrStatusPage() {
  const [pnr, setPnr] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  
  const handleSearch = async () => {
    if (!pnr.trim()) {
      setError('Please enter a PNR number');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/bookings/pnr/${pnr.trim().toUpperCase()}`);
      
      if (response.data?.status === 'success') {
        setResult(response.data.data);
      } else {
        setError(response.data?.message || 'PNR not found');
        setResult(null);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch PNR status');
      setResult(null);
    } finally {
      setLoading(false);
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
  
  const getPassengerStatusStyle = (status) => {
    if (status?.startsWith('CNF')) {
      return { background: 'rgba(74, 222, 128, 0.15)', color: 'var(--success)' };
    }
    if (status?.startsWith('RAC')) {
      return { background: 'rgba(251, 191, 36, 0.15)', color: 'var(--warning)' };
    }
    if (status?.startsWith('WL')) {
      return { background: 'rgba(248, 113, 113, 0.15)', color: 'var(--error)' };
    }
    if (status === 'CAN') {
      return { background: 'var(--bg-inset)', color: 'var(--text-muted)' };
    }
    return {};
  };
  
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>PNR Status</h1>
        <p style={styles.subtitle}>Check your booking status instantly</p>
      </header>
      
      <div style={styles.searchCard}>
        <div style={styles.searchForm}>
          <input
            type="text"
            placeholder="Enter 10-digit PNR"
            value={pnr}
            onChange={(e) => setPnr(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            style={styles.input}
            maxLength={15}
          />
          <button 
            style={styles.button} 
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? <Icons.Loader /> : <Icons.Search />}
            Check Status
          </button>
        </div>
      </div>
      
      {error && <div style={styles.error}>{error}</div>}
      
      {result && (
        <div style={styles.resultCard}>
          <div style={styles.resultHeader}>
            <span style={styles.pnrDisplay}>PNR: {result.booking?.pnr}</span>
            <span style={{ ...styles.statusBadge, ...getStatusStyle(result.booking?.status) }}>
              {result.booking?.status}
            </span>
          </div>
          
          <div style={styles.resultBody}>
            <div style={styles.trainInfo}>
              <div style={styles.trainIcon}>
                <Icons.Ticket />
              </div>
              <div>
                <div style={styles.trainName}>{result.train?.name || result.train?.number}</div>
                <div style={styles.trainMeta}>
                  #{result.train?.number} • {result.booking?.class}
                </div>
              </div>
            </div>
            
            <div style={styles.journeyInfo}>
              <div style={styles.infoItem}>
                <div style={styles.infoLabel}>From</div>
                <div style={styles.infoValue}>{result.train?.from_station}</div>
              </div>
              <div style={styles.infoItem}>
                <div style={styles.infoLabel}>To</div>
                <div style={styles.infoValue}>{result.train?.to_station}</div>
              </div>
              <div style={styles.infoItem}>
                <div style={styles.infoLabel}>Date</div>
                <div style={styles.infoValue}>{result.booking?.journey_date}</div>
              </div>
              <div style={styles.infoItem}>
                <div style={styles.infoLabel}>Fare</div>
                <div style={{ ...styles.infoValue, color: 'var(--accent-blue)' }}>
                  ₹{result.booking?.total_fare}
                </div>
              </div>
            </div>
            
            <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
              Passenger Details
            </h4>
            
            <table style={styles.passengerTable}>
              <thead>
                <tr>
                  <th style={styles.th}>Name</th>
                  <th style={styles.th}>Age/Gender</th>
                  <th style={styles.th}>Booking Status</th>
                  <th style={styles.th}>Coach/Seat</th>
                </tr>
              </thead>
              <tbody>
                {(result.passengers || []).map((p, i) => (
                  <tr key={i}>
                    <td style={styles.td}>{p.name}</td>
                    <td style={styles.td}>{p.age} / {p.gender}</td>
                    <td style={styles.td}>
                      <span style={{ ...styles.passengerStatus, ...getPassengerStatusStyle(p.status) }}>
                        {p.status?.startsWith('CNF') && <Icons.Check />}
                        {p.status}
                      </span>
                    </td>
                    <td style={styles.td}>
                      {p.coach && p.seat ? `${p.coach} / ${p.seat}` : '-'}
                      {p.berth && ` (${p.berth})`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      
      {!loading && !error && !result && (
        <div style={styles.emptyState}>
          <Icons.Ticket />
          <p style={{ marginTop: 16 }}>Enter your PNR number to check booking status</p>
        </div>
      )}
    </div>
  );
}

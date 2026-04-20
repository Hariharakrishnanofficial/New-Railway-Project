/**
 * SearchPage.jsx — Train search page for passengers.
 * 
 * Features:
 *   - Search trains by source/destination/date
 *   - Display results with availability
 *   - Filter and sort options
 */

import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

// Icons
const Icons = {
  Search: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  ),
  Swap: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M7 16V4M7 4L3 8M7 4l4 4M17 8v12M17 20l4-4M17 20l-4-4" />
    </svg>
  ),
  Clock: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  Train: () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="4" y="3" width="16" height="16" rx="2" />
      <path d="M4 11h16" />
      <path d="M12 3v8" />
      <circle cx="8" cy="15" r="1" />
      <circle cx="16" cy="15" r="1" />
    </svg>
  ),
  ArrowRight: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  ),
  Filter: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
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
    maxWidth: 1200,
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
  
  // Search form
  searchCard: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-xl)',
    padding: 24,
    marginBottom: 32,
  },
  searchRow: {
    display: 'flex',
    gap: 16,
    alignItems: 'flex-end',
    flexWrap: 'wrap',
  },
  inputGroup: {
    flex: 1,
    minWidth: 200,
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: {
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-muted)',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  input: {
    padding: '14px 16px',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-primary)',
    fontSize: 15,
    fontFamily: 'var(--font-body)',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  swapButton: {
    width: 44,
    height: 44,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-full)',
    color: 'var(--text-secondary)',
    cursor: 'pointer',
    transition: 'all 0.2s',
    flexShrink: 0,
  },
  searchButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    padding: '14px 28px',
    background: 'var(--accent-blue)',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    color: 'white',
    fontSize: 15,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s',
    flexShrink: 0,
  },
  
  // Filters
  filterBar: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    marginBottom: 24,
    flexWrap: 'wrap',
  },
  filterChip: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '8px 14px',
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
  
  // Results
  resultsHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  resultsCount: {
    fontSize: 14,
    color: 'var(--text-muted)',
  },
  
  // Train card
  trainCard: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    padding: 20,
    marginBottom: 12,
    transition: 'all 0.2s',
    cursor: 'pointer',
  },
  trainHeader: {
    display: 'flex',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  trainInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
  },
  trainIcon: {
    width: 44,
    height: 44,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--accent-blue)',
  },
  trainName: {
    fontSize: 16,
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: 2,
  },
  trainNumber: {
    fontSize: 13,
    color: 'var(--text-muted)',
  },
  trainType: {
    display: 'inline-block',
    padding: '4px 10px',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-sm)',
    fontSize: 11,
    fontWeight: 600,
    color: 'var(--text-secondary)',
    textTransform: 'uppercase',
  },
  
  journeyInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: 24,
    marginBottom: 16,
  },
  stationBlock: {
    flex: 1,
  },
  stationTime: {
    fontSize: 24,
    fontWeight: 700,
    color: 'var(--text-primary)',
    fontFamily: 'var(--font-mono)',
  },
  stationName: {
    fontSize: 13,
    color: 'var(--text-secondary)',
    marginTop: 2,
  },
  journeyLine: {
    flex: 2,
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  journeyDash: {
    flex: 1,
    height: 2,
    background: 'var(--border)',
    borderRadius: 1,
  },
  journeyDuration: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 12px',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-full)',
    fontSize: 12,
    color: 'var(--text-muted)',
  },
  
  // Availability row
  availabilityRow: {
    display: 'flex',
    gap: 12,
    overflowX: 'auto',
    paddingBottom: 4,
  },
  classCard: {
    flex: '0 0 auto',
    minWidth: 100,
    padding: '12px 16px',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    textAlign: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  classCardSelected: {
    background: 'rgba(59, 130, 246, 0.1)',
    borderColor: 'var(--accent-blue)',
  },
  className: {
    fontSize: 14,
    fontWeight: 700,
    color: 'var(--text-primary)',
    marginBottom: 4,
  },
  classStatus: {
    fontSize: 12,
    fontWeight: 600,
  },
  classStatusAvailable: {
    color: 'var(--success)',
  },
  classStatusRac: {
    color: 'var(--warning)',
  },
  classStatusWl: {
    color: 'var(--error)',
  },
  classFare: {
    fontSize: 11,
    color: 'var(--text-muted)',
    marginTop: 4,
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
  },
  
  // Loading
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 40,
    color: 'var(--text-muted)',
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
};

const classNames = ['SL', '3A', '2A', '1A', 'CC', '2S'];

export default function SearchPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useState({
    from: '',
    to: '',
    date: new Date().toISOString().split('T')[0],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const [selectedClass, setSelectedClass] = useState('3A');
  
  const handleSwap = () => {
    setSearchParams(prev => ({
      ...prev,
      from: prev.to,
      to: prev.from,
    }));
  };
  
  const handleSearch = useCallback(async () => {
    if (!searchParams.from || !searchParams.to) {
      setError('Please enter both source and destination stations');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSearched(true);
    
    try {
      const response = await api.get('/trains/search', {
        params: {
          from: searchParams.from,
          to: searchParams.to,
          date: searchParams.date,
        },
      });
      
      if (response.data?.status === 'success') {
        setResults(response.data.data?.trains || []);
      } else {
        setError(response.data?.message || 'Search failed');
      }
    } catch (err) {
      setError(err.message || 'Failed to search trains');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);
  
  const handleBookTrain = (train, travelClass) => {
    navigate('/book', {
      state: {
        train,
        travelClass,
        journeyDate: searchParams.date,
        from: searchParams.from,
        to: searchParams.to,
      },
    });
  };
  
  const getStatusStyle = (status) => {
    if (status === 'AVAILABLE') return styles.classStatusAvailable;
    if (status === 'RAC') return styles.classStatusRac;
    return styles.classStatusWl;
  };
  
  const formatAvailability = (avail) => {
    if (!avail) return 'N/A';
    if (avail.status === 'AVAILABLE') return `${avail.available}`;
    if (avail.status === 'RAC') return `RAC ${avail.rac_available}`;
    if (avail.status?.startsWith('WL')) return avail.status;
    return avail.status || 'N/A';
  };
  
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Search Trains</h1>
        <p style={styles.subtitle}>Find and book trains across India</p>
      </header>
      
      {/* Search Form */}
      <div style={styles.searchCard}>
        <div style={styles.searchRow}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>From Station</label>
            <input
              type="text"
              placeholder="Enter station code or name"
              value={searchParams.from}
              onChange={(e) => setSearchParams(p => ({ ...p, from: e.target.value }))}
              style={styles.input}
            />
          </div>
          
          <button 
            style={styles.swapButton} 
            onClick={handleSwap}
            title="Swap stations"
          >
            <Icons.Swap />
          </button>
          
          <div style={styles.inputGroup}>
            <label style={styles.label}>To Station</label>
            <input
              type="text"
              placeholder="Enter station code or name"
              value={searchParams.to}
              onChange={(e) => setSearchParams(p => ({ ...p, to: e.target.value }))}
              style={styles.input}
            />
          </div>
          
          <div style={{ ...styles.inputGroup, minWidth: 160 }}>
            <label style={styles.label}>Journey Date</label>
            <input
              type="date"
              value={searchParams.date}
              onChange={(e) => setSearchParams(p => ({ ...p, date: e.target.value }))}
              style={styles.input}
              min={new Date().toISOString().split('T')[0]}
            />
          </div>
          
          <button
            style={styles.searchButton}
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? <Icons.Loader /> : <Icons.Search />}
            Search
          </button>
        </div>
      </div>
      
      {error && <div style={styles.error}>{error}</div>}
      
      {/* Class Filter */}
      {searched && (
        <div style={styles.filterBar}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
            <Icons.Filter /> Filter:
          </span>
          {classNames.map((cls) => (
            <button
              key={cls}
              style={{
                ...styles.filterChip,
                ...(selectedClass === cls ? styles.filterChipActive : {}),
              }}
              onClick={() => setSelectedClass(cls)}
            >
              {cls}
            </button>
          ))}
        </div>
      )}
      
      {/* Loading */}
      {loading && (
        <div style={styles.loading}>
          <Icons.Loader />
          Searching trains...
        </div>
      )}
      
      {/* Results */}
      {!loading && searched && (
        <>
          <div style={styles.resultsHeader}>
            <span style={styles.resultsCount}>
              {results.length} train{results.length !== 1 ? 's' : ''} found
            </span>
          </div>
          
          {results.length === 0 ? (
            <div style={styles.emptyState}>
              <div style={styles.emptyIcon}>
                <Icons.Train />
              </div>
              <h3 style={styles.emptyTitle}>No trains found</h3>
              <p style={styles.emptyText}>
                Try different stations or dates
              </p>
            </div>
          ) : (
            results.map((train) => (
              <div
                key={train.ROWID}
                style={styles.trainCard}
                onClick={() => handleBookTrain(train, selectedClass)}
              >
                <div style={styles.trainHeader}>
                  <div style={styles.trainInfo}>
                    <div style={styles.trainIcon}>
                      <Icons.Train />
                    </div>
                    <div>
                      <div style={styles.trainName}>{train.Train_Name}</div>
                      <div style={styles.trainNumber}>#{train.Train_Number}</div>
                    </div>
                  </div>
                  <span style={styles.trainType}>{train.Train_Type || 'Express'}</span>
                </div>
                
                <div style={styles.journeyInfo}>
                  <div style={styles.stationBlock}>
                    <div style={styles.stationTime}>
                      {train.Departure_Time || '--:--'}
                    </div>
                    <div style={styles.stationName}>
                      {train.From_Station_Code || train.From_Station || searchParams.from}
                    </div>
                  </div>
                  
                  <div style={styles.journeyLine}>
                    <div style={styles.journeyDash} />
                    <div style={styles.journeyDuration}>
                      <Icons.Clock />
                      {train.Duration || '--'}
                    </div>
                    <div style={styles.journeyDash} />
                    <Icons.ArrowRight />
                  </div>
                  
                  <div style={{ ...styles.stationBlock, textAlign: 'right' }}>
                    <div style={styles.stationTime}>
                      {train.Arrival_Time || '--:--'}
                    </div>
                    <div style={styles.stationName}>
                      {train.To_Station_Code || train.To_Station || searchParams.to}
                    </div>
                  </div>
                </div>
                
                {/* Availability by class */}
                <div style={styles.availabilityRow}>
                  {classNames.map((cls) => {
                    const avail = train.availability?.[cls];
                    const isSelected = selectedClass === cls;
                    
                    return (
                      <div
                        key={cls}
                        style={{
                          ...styles.classCard,
                          ...(isSelected ? styles.classCardSelected : {}),
                        }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedClass(cls);
                        }}
                      >
                        <div style={styles.className}>{cls}</div>
                        <div style={{
                          ...styles.classStatus,
                          ...getStatusStyle(avail?.status),
                        }}>
                          {formatAvailability(avail)}
                        </div>
                        <div style={styles.classFare}>
                          ₹{avail?.fare || '--'}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))
          )}
        </>
      )}
    </div>
  );
}

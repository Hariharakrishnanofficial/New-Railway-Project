/**
 * SessionManagement Component - Smart Railway Ticketing System
 * 
 * Allows users to:
 * - View all active sessions (devices logged in)
 * - See which session is current
 * - Revoke individual sessions (log out other devices)
 * - Revoke all sessions except current
 */

import React, { useState, useEffect, useCallback } from 'react';
import sessionApi from '../services/sessionApi';
import './SessionManagement.css';

// Icons (inline SVG for simplicity)
const DeviceIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
    <line x1="8" y1="21" x2="16" y2="21"/>
    <line x1="12" y1="17" x2="12" y2="21"/>
  </svg>
);

const CurrentBadge = () => (
  <span className="session-badge session-badge-current">Current</span>
);

const RefreshIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M23 4v6h-6"/>
    <path d="M1 20v-6h6"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const LogoutIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
);

/**
 * Format a date string to a human-readable format.
 */
function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
}

/**
 * Parse user agent string to get browser/device info.
 */
function parseUserAgent(userAgent) {
  if (!userAgent) return { browser: 'Unknown', device: 'Unknown', os: '', full: 'Unknown Device' };

  let browser = 'Unknown Browser';
  let device = 'Desktop';

  // Detect browser
  if (userAgent.includes('Firefox')) {
    browser = 'Firefox';
  } else if (userAgent.includes('Edg')) {
    browser = 'Microsoft Edge';
  } else if (userAgent.includes('Chrome')) {
    browser = 'Chrome';
  } else if (userAgent.includes('Safari')) {
    browser = 'Safari';
  } else if (userAgent.includes('Opera') || userAgent.includes('OPR')) {
    browser = 'Opera';
  }

  // Detect device type
  if (userAgent.includes('Mobile') || userAgent.includes('Android')) {
    device = 'Mobile';
  } else if (userAgent.includes('Tablet') || userAgent.includes('iPad')) {
    device = 'Tablet';
  }

  // Detect OS
  let os = '';
  if (userAgent.includes('Windows')) {
    os = 'Windows';
  } else if (userAgent.includes('Mac OS X')) {
    os = 'macOS';
  } else if (userAgent.includes('Linux')) {
    os = 'Linux';
  } else if (userAgent.includes('Android')) {
    os = 'Android';
  } else if (userAgent.includes('iOS') || userAgent.includes('iPhone')) {
    os = 'iOS';
  }

  return {
    browser,
    device,
    os,
    full: `${browser} on ${os || device}`,
  };
}

function SessionManagement() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [revoking, setRevoking] = useState(null); // Session being revoked
  const [revokingAll, setRevokingAll] = useState(false);

  const loadSessions = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await sessionApi.getSessions();
      
      if (response.status === 'success' && response.data) {
        setSessions(response.data.sessions || []);
      } else {
        throw new Error(response.message || 'Failed to load sessions');
      }
    } catch (err) {
      setError(err.message || 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  const handleRevokeSession = async (sessionSuffix) => {
    if (!sessionSuffix) return;
    
    setRevoking(sessionSuffix);
    setError(null);

    try {
      const response = await sessionApi.revokeSession(sessionSuffix);
      
      if (response.status === 'success') {
        // Remove from list
        setSessions(prev => prev.filter(s => !s.session_id.endsWith(sessionSuffix)));
      } else {
        throw new Error(response.message || 'Failed to revoke session');
      }
    } catch (err) {
      setError(err.message || 'Failed to revoke session');
    } finally {
      setRevoking(null);
    }
  };

  const handleRevokeAll = async () => {
    if (!window.confirm('This will log out all other devices. Continue?')) {
      return;
    }

    setRevokingAll(true);
    setError(null);

    try {
      const response = await sessionApi.revokeAllSessions();
      
      if (response.status === 'success') {
        // Keep only current session
        setSessions(prev => prev.filter(s => s.is_current));
      } else {
        throw new Error(response.message || 'Failed to revoke sessions');
      }
    } catch (err) {
      setError(err.message || 'Failed to revoke sessions');
    } finally {
      setRevokingAll(false);
    }
  };

  if (loading) {
    return (
      <div className="session-management">
        <div className="session-loading">
          <div className="session-spinner"></div>
          <p>Loading sessions...</p>
        </div>
      </div>
    );
  }

  const otherSessions = sessions.filter(s => !s.is_current);

  return (
    <div className="session-management">
      <div className="session-header">
        <h2>Active Sessions</h2>
        <div className="session-actions">
          <button 
            className="session-btn session-btn-secondary"
            onClick={loadSessions}
            disabled={loading}
          >
            <RefreshIcon /> Refresh
          </button>
          {otherSessions.length > 0 && (
            <button 
              className="session-btn session-btn-danger"
              onClick={handleRevokeAll}
              disabled={revokingAll}
            >
              {revokingAll ? 'Logging out...' : 'Log Out All Other Devices'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="session-error">
          {error}
        </div>
      )}

      <p className="session-description">
        These are the devices currently logged into your account. 
        You can log out any device you don't recognize.
      </p>

      <div className="session-list">
        {sessions.length === 0 ? (
          <div className="session-empty">
            <p>No active sessions found.</p>
          </div>
        ) : (
          sessions.map((session) => {
            const { full } = parseUserAgent(session.user_agent);
            const sessionSuffix = session.session_id?.replace('...', '');

            return (
              <div 
                key={session.session_id} 
                className={`session-card ${session.is_current ? 'session-card-current' : ''}`}
              >
                <div className="session-icon">
                  <DeviceIcon />
                </div>
                
                <div className="session-info">
                  <div className="session-device">
                    {full}
                    {session.is_current && <CurrentBadge />}
                  </div>
                  
                  <div className="session-details">
                    <span className="session-ip">
                      IP: {session.ip_address || 'Unknown'}
                    </span>
                    <span className="session-time">
                      Last active: {formatDate(session.last_accessed_at)}
                    </span>
                    <span className="session-created">
                      Signed in: {formatDate(session.created_at)}
                    </span>
                  </div>
                </div>

                <div className="session-action">
                  {!session.is_current && (
                    <button
                      className="session-btn session-btn-revoke"
                      onClick={() => handleRevokeSession(sessionSuffix)}
                      disabled={revoking === sessionSuffix}
                      title="Log out this device"
                    >
                      {revoking === sessionSuffix ? (
                        <span className="session-spinner-small"></span>
                      ) : (
                        <>
                          <LogoutIcon />
                          <span>Log Out</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="session-footer">
        <p className="session-note">
          <strong>Security tip:</strong> If you see a session you don't recognize, 
          log it out immediately and change your password.
        </p>
      </div>
    </div>
  );
}

export default SessionManagement;

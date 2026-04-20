/**
 * ProfilePage.jsx — User profile settings.
 */

import React, { useState } from 'react';
import { useAuth } from '../context/SessionAuthContext';

const Icons = {
  User: () => (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  ),
  Mail: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22,6 12,13 2,6" />
    </svg>
  ),
  Phone: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
    </svg>
  ),
  Lock: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  ),
  Shield: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  ),
  Edit: () => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
    </svg>
  ),
  Check: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  LogOut: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  ),
  Loader: () => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
      <circle cx="12" cy="12" r="10" strokeOpacity="0.25" />
      <path d="M12 2a10 10 0 0 1 10 10" strokeLinecap="round" />
    </svg>
  ),
};

const styles = {
  container: {
    maxWidth: 800,
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
  
  // Profile header
  profileHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: 24,
    padding: 24,
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-xl)',
    marginBottom: 24,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 'var(--radius-full)',
    background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-purple))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 28,
    fontWeight: 700,
    color: 'white',
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 24,
    fontWeight: 700,
    color: 'var(--text-primary)',
  },
  profileEmail: {
    fontSize: 14,
    color: 'var(--text-muted)',
    marginTop: 4,
  },
  profileBadge: {
    display: 'inline-block',
    padding: '4px 12px',
    background: 'rgba(74, 222, 128, 0.15)',
    borderRadius: 'var(--radius-full)',
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--success)',
    marginTop: 8,
  },
  
  // Section
  section: {
    background: 'var(--bg-elevated)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-lg)',
    marginBottom: 24,
    overflow: 'hidden',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    borderBottom: '1px solid var(--border)',
  },
  sectionTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    fontSize: 16,
    fontWeight: 600,
    color: 'var(--text-primary)',
  },
  editButton: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '6px 12px',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    color: 'var(--text-secondary)',
    fontSize: 13,
    cursor: 'pointer',
  },
  sectionBody: {
    padding: 20,
  },
  
  // Form
  form: {
    display: 'grid',
    gap: 20,
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  label: {
    fontSize: 13,
    fontWeight: 600,
    color: 'var(--text-secondary)',
  },
  input: {
    padding: '12px 14px',
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-primary)',
    fontSize: 15,
    fontFamily: 'var(--font-body)',
    outline: 'none',
  },
  inputDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  
  // Info row
  infoRow: {
    display: 'flex',
    alignItems: 'center',
    padding: '16px 0',
    borderBottom: '1px solid var(--border)',
  },
  infoIcon: {
    width: 40,
    height: 40,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-inset)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-muted)',
    marginRight: 16,
  },
  infoContent: {
    flex: 1,
  },
  infoLabel: {
    fontSize: 12,
    color: 'var(--text-muted)',
    marginBottom: 2,
  },
  infoValue: {
    fontSize: 15,
    color: 'var(--text-primary)',
    fontWeight: 500,
  },
  
  // Buttons
  button: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: '12px 24px',
    background: 'var(--accent-blue)',
    border: 'none',
    borderRadius: 'var(--radius-md)',
    color: 'white',
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  buttonSecondary: {
    background: 'var(--bg-inset)',
    border: '1px solid var(--border)',
    color: 'var(--text-secondary)',
  },
  buttonDanger: {
    background: 'rgba(248, 113, 113, 0.15)',
    border: '1px solid rgba(248, 113, 113, 0.3)',
    color: 'var(--error)',
  },
  
  // Messages
  success: {
    padding: 12,
    background: 'rgba(74, 222, 128, 0.15)',
    border: '1px solid rgba(74, 222, 128, 0.3)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--success)',
    fontSize: 14,
    marginBottom: 16,
  },
  error: {
    padding: 12,
    background: 'rgba(248, 113, 113, 0.1)',
    border: '1px solid rgba(248, 113, 113, 0.3)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--error)',
    fontSize: 14,
    marginBottom: 16,
  },
};

export default function ProfilePage() {
  const { user, logout, updateProfile, changePassword } = useAuth();
  
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState(null);
  
  const [formData, setFormData] = useState({
    fullName: user?.fullName || user?.Full_Name || '',
    phoneNumber: user?.phoneNumber || user?.Phone_Number || '',
  });
  
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  
  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };
  
  const handleUpdateProfile = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const result = await updateProfile({
        fullName: formData.fullName,
        phoneNumber: formData.phoneNumber,
      });
      
      if (result.success) {
        setSuccess('Profile updated successfully');
        setEditing(false);
      } else {
        setError(result.error || 'Failed to update profile');
      }
    } catch (err) {
      setError(err.message || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };
  
  const handleChangePassword = async () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (passwordForm.newPassword.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const result = await changePassword({
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword,
      });
      
      if (result.success) {
        setSuccess('Password changed successfully. Other devices have been logged out.');
        setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        setError(result.error || 'Failed to change password');
      }
    } catch (err) {
      setError(err.message || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>Profile Settings</h1>
      </header>
      
      {/* Profile Header */}
      <div style={styles.profileHeader}>
        <div style={styles.avatar}>
          {getInitials(user?.fullName || user?.Full_Name)}
        </div>
        <div style={styles.profileInfo}>
          <div style={styles.profileName}>{user?.fullName || user?.Full_Name || 'User'}</div>
          <div style={styles.profileEmail}>{user?.email || user?.Email}</div>
          <span style={styles.profileBadge}>
            <Icons.Shield /> {user?.accountStatus || 'Active'}
          </span>
        </div>
      </div>
      
      {success && <div style={styles.success}><Icons.Check /> {success}</div>}
      {error && <div style={styles.error}>{error}</div>}
      
      {/* Personal Information */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <h3 style={styles.sectionTitle}>
            <Icons.User />
            Personal Information
          </h3>
          <button 
            style={styles.editButton}
            onClick={() => setEditing(!editing)}
          >
            <Icons.Edit />
            {editing ? 'Cancel' : 'Edit'}
          </button>
        </div>
        <div style={styles.sectionBody}>
          {editing ? (
            <div style={styles.form}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Full Name</label>
                <input
                  type="text"
                  value={formData.fullName}
                  onChange={(e) => setFormData(p => ({ ...p, fullName: e.target.value }))}
                  style={styles.input}
                />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Email Address</label>
                <input
                  type="email"
                  value={user?.email || user?.Email || ''}
                  disabled
                  style={{ ...styles.input, ...styles.inputDisabled }}
                />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Phone Number</label>
                <input
                  type="tel"
                  value={formData.phoneNumber}
                  onChange={(e) => setFormData(p => ({ ...p, phoneNumber: e.target.value }))}
                  style={styles.input}
                />
              </div>
              <button 
                style={styles.button}
                onClick={handleUpdateProfile}
                disabled={loading}
              >
                {loading ? <Icons.Loader /> : <Icons.Check />}
                Save Changes
              </button>
            </div>
          ) : (
            <>
              <div style={styles.infoRow}>
                <div style={styles.infoIcon}><Icons.User /></div>
                <div style={styles.infoContent}>
                  <div style={styles.infoLabel}>Full Name</div>
                  <div style={styles.infoValue}>{user?.fullName || user?.Full_Name || '-'}</div>
                </div>
              </div>
              <div style={styles.infoRow}>
                <div style={styles.infoIcon}><Icons.Mail /></div>
                <div style={styles.infoContent}>
                  <div style={styles.infoLabel}>Email Address</div>
                  <div style={styles.infoValue}>{user?.email || user?.Email || '-'}</div>
                </div>
              </div>
              <div style={{ ...styles.infoRow, borderBottom: 'none' }}>
                <div style={styles.infoIcon}><Icons.Phone /></div>
                <div style={styles.infoContent}>
                  <div style={styles.infoLabel}>Phone Number</div>
                  <div style={styles.infoValue}>{user?.phoneNumber || user?.Phone_Number || '-'}</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* Change Password */}
      <div style={styles.section}>
        <div style={styles.sectionHeader}>
          <h3 style={styles.sectionTitle}>
            <Icons.Lock />
            Change Password
          </h3>
        </div>
        <div style={styles.sectionBody}>
          <div style={styles.form}>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Current Password</label>
              <input
                type="password"
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm(p => ({ ...p, currentPassword: e.target.value }))}
                style={styles.input}
                placeholder="Enter current password"
              />
            </div>
            <div style={styles.inputGroup}>
              <label style={styles.label}>New Password</label>
              <input
                type="password"
                value={passwordForm.newPassword}
                onChange={(e) => setPasswordForm(p => ({ ...p, newPassword: e.target.value }))}
                style={styles.input}
                placeholder="Enter new password"
              />
            </div>
            <div style={styles.inputGroup}>
              <label style={styles.label}>Confirm New Password</label>
              <input
                type="password"
                value={passwordForm.confirmPassword}
                onChange={(e) => setPasswordForm(p => ({ ...p, confirmPassword: e.target.value }))}
                style={styles.input}
                placeholder="Confirm new password"
              />
            </div>
            <button 
              style={{ ...styles.button, ...styles.buttonSecondary }}
              onClick={handleChangePassword}
              disabled={loading}
            >
              {loading ? <Icons.Loader /> : <Icons.Lock />}
              Update Password
            </button>
          </div>
        </div>
      </div>
      
      {/* Logout */}
      <div style={styles.section}>
        <div style={styles.sectionBody}>
          <button 
            style={{ ...styles.button, ...styles.buttonDanger, width: '100%' }}
            onClick={logout}
          >
            <Icons.LogOut />
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * ProfilePage.jsx — Passenger self-service profile management with CRUD operations
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, updateProfile, changePassword, deactivateAccount } from '../services/authApi';
import '../styles/ProfilePage.css';

export default function ProfilePage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('profile');
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Profile state
  const [profileData, setProfileData] = useState({
    fullName: '',
    phoneNumber: '',
    address: '',
  });

  // Password state
  const [passwordData, setPasswordData] = useState({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      setLoading(true);
      const userData = JSON.parse(sessionStorage.getItem('rail_user') || '{}');
      
      if (!userData.ID) {
        navigate('/');
        return;
      }

      const response = await getProfile(userData.ID);
      
      if (response.success) {
        const profile = response.data;
        setUser(profile);
        setProfileData({
          fullName: profile.Full_Name || '',
          phoneNumber: profile.Phone_Number || '',
          address: profile.Address || '',
        });
      } else {
        setError(response.error || 'Failed to load profile');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  // ══════════════════════════════════════════════════════════════════════════
  //  UPDATE PROFILE
  // ══════════════════════════════════════════════════════════════════════════

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      const userData = JSON.parse(sessionStorage.getItem('rail_user') || '{}');
      const response = await updateProfile(userData.ID, profileData);

      if (response.success) {
        setSuccess('Profile updated successfully');
        const updated = { ...user, ...response.data };
        setUser(updated);
        sessionStorage.setItem('rail_user', JSON.stringify(updated));
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(response.error || 'Failed to update profile');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update profile');
    }
  };

  // ══════════════════════════════════════════════════════════════════════════
  //  CHANGE PASSWORD
  // ══════════════════════════════════════════════════════════════════════════

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const { oldPassword, newPassword, confirmPassword } = passwordData;

    if (!oldPassword || !newPassword || !confirmPassword) {
      setError('All password fields are required');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setError('New password must be at least 6 characters');
      return;
    }

    try {
      const userData = JSON.parse(sessionStorage.getItem('rail_user') || '{}');
      const response = await changePassword(userData.ID, oldPassword, newPassword);

      if (response.success) {
        setSuccess('Password changed successfully');
        setPasswordData({
          oldPassword: '',
          newPassword: '',
          confirmPassword: '',
        });
        setTimeout(() => setSuccess(''), 3000);
      } else {
        setError(response.error || 'Failed to change password');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to change password');
    }
  };

  // ══════════════════════════════════════════════════════════════════════════
  //  DEACTIVATE ACCOUNT
  // ══════════════════════════════════════════════════════════════════════════

  const handleDeactivateAccount = async () => {
    const password = prompt('Enter your password to confirm account deactivation:');
    
    if (!password) return;

    try {
      const userData = JSON.parse(sessionStorage.getItem('rail_user') || '{}');
      const response = await deactivateAccount(userData.ID, password);

      if (response.success) {
        setSuccess('Account deactivated. Redirecting...');
        sessionStorage.clear();
        setTimeout(() => navigate('/'), 2000);
      } else {
        setError(response.error || 'Failed to deactivate account');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to deactivate account');
    }
  };

  if (loading) {
    return <div className="profile-container"><p>Loading profile...</p></div>;
  }

  return (
    <div className="profile-container">
      <div className="profile-card">
        {/* Header */}
        <div className="profile-header">
          <h1>My Account</h1>
          <p className="user-email">{user?.Email}</p>
        </div>

        {/* Messages */}
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        {/* Tab Navigation */}
        <div className="profile-tabs">
          <button
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Profile Info
          </button>
          <button
            className={`tab-btn ${activeTab === 'password' ? 'active' : ''}`}
            onClick={() => setActiveTab('password')}
          >
            Change Password
          </button>
          <button
            className={`tab-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            Account Settings
          </button>
        </div>

        {/* PROFILE INFO TAB */}
        {activeTab === 'profile' && (
          <form onSubmit={handleUpdateProfile} className="profile-form">
            <div className="form-section">
              <h3>Personal Information</h3>

              <div className="form-group">
                <label htmlFor="email">Email (Read-only)</label>
                <input
                  id="email"
                  type="email"
                  value={user?.Email || ''}
                  disabled
                  className="read-only"
                />
              </div>

              <div className="form-group">
                <label htmlFor="fullName">Full Name</label>
                <input
                  id="fullName"
                  type="text"
                  value={profileData.fullName}
                  onChange={(e) => setProfileData({...profileData, fullName: e.target.value})}
                  placeholder="Your full name"
                />
              </div>

              <div className="form-group">
                <label htmlFor="phoneNumber">Phone Number</label>
                <input
                  id="phoneNumber"
                  type="tel"
                  value={profileData.phoneNumber}
                  onChange={(e) => setProfileData({...profileData, phoneNumber: e.target.value})}
                  placeholder="+1 (555) 123-4567"
                />
              </div>

              <div className="form-group">
                <label htmlFor="address">Address</label>
                <textarea
                  id="address"
                  value={profileData.address}
                  onChange={(e) => setProfileData({...profileData, address: e.target.value})}
                  placeholder="Your address"
                  rows="4"
                ></textarea>
              </div>

              <div className="form-group">
                <label>Account Status</label>
                <div className="status-badge">
                  {user?.Account_Status === 'Active' ? (
                    <span className="badge-active">● Active</span>
                  ) : (
                    <span className="badge-inactive">● Inactive</span>
                  )}
                </div>
              </div>

              <div className="form-group">
                <label>User Role</label>
                <div className="role-badge">
                  <span className={`badge-${user?.Role?.toLowerCase() || 'user'}`}>
                    {user?.Role || 'User'}
                  </span>
                </div>
              </div>

              <button type="submit" className="submit-btn">Save Changes</button>
            </div>
          </form>
        )}

        {/* PASSWORD TAB */}
        {activeTab === 'password' && (
          <form onSubmit={handleChangePassword} className="profile-form">
            <div className="form-section">
              <h3>Change Password</h3>
              <p className="section-hint">For security, your password should be at least 6 characters and include uppercase, lowercase, and numbers.</p>

              <div className="form-group">
                <label htmlFor="oldPassword">Current Password *</label>
                <input
                  id="oldPassword"
                  type="password"
                  value={passwordData.oldPassword}
                  onChange={(e) => setPasswordData({...passwordData, oldPassword: e.target.value})}
                  placeholder="••••••••"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="newPassword">New Password *</label>
                <input
                  id="newPassword"
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({...passwordData, newPassword: e.target.value})}
                  placeholder="••••••••"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm New Password *</label>
                <input
                  id="confirmPassword"
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({...passwordData, confirmPassword: e.target.value})}
                  placeholder="••••••••"
                  required
                />
              </div>

              <button type="submit" className="submit-btn">Update Password</button>
            </div>
          </form>
        )}

        {/* SETTINGS TAB */}
        {activeTab === 'settings' && (
          <div className="profile-form">
            <div className="form-section">
              <h3>Account Settings</h3>

              <div className="settings-group">
                <div className="setting-item">
                  <div className="setting-info">
                    <h4>Deactivate Account</h4>
                    <p>Temporarily disable your account. You can reactivate it anytime by signing in.</p>
                  </div>
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleDeactivateAccount}
                  >
                    Deactivate
                  </button>
                </div>

                <div className="setting-item danger">
                  <div className="setting-info">
                    <h4>Account Information</h4>
                    <p>Email: {user?.Email}</p>
                    <p>Member Since: {user?.CreatedAt ? new Date(user.CreatedAt).toLocaleDateString() : 'N/A'}</p>
                    <p>Last Login: {user?.Last_Login ? new Date(user.Last_Login).toLocaleDateString() : 'N/A'}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

import api from './api';

const AUTH_BASE = '/auth';

// ══════════════════════════════════════════════════════════════════════════
//  CREATE - REGISTER NEW USER
// ══════════════════════════════════════════════════════════════════════════

export const registerUser = async (userData) => {
  const response = await api.post(`${AUTH_BASE}/register`, {
    full_name: userData.fullName,
    email: userData.email,
    password: userData.password,
    phone_number: userData.phoneNumber || '',
    address: userData.address || '',
  });
  return response.data;
};

// ══════════════════════════════════════════════════════════════════════════
//  READ - SIGNIN
// ══════════════════════════════════════════════════════════════════════════

export const signin = async (email, password) => {
  const response = await api.post(`${AUTH_BASE}/signin`, {
    email,
    password,
  });
  return response.data;
};

// ══════════════════════════════════════════════════════════════════════════
//  READ - GET PROFILE
// ══════════════════════════════════════════════════════════════════════════

export const getProfile = async (userId) => {
  const response = await api.get(`${AUTH_BASE}/profile/${userId}`);
  return response.data;
};

// ══════════════════════════════════════════════════════════════════════════
//  UPDATE - PROFILE
// ══════════════════════════════════════════════════════════════════════════

export const updateProfile = async (userId, profileData) => {
  const response = await api.put(`${AUTH_BASE}/profile/${userId}`, {
    full_name: profileData.fullName,
    phone_number: profileData.phoneNumber,
    address: profileData.address,
  });
  return response.data;
};

// ══════════════════════════════════════════════════════════════════════════
//  UPDATE - CHANGE PASSWORD
// ══════════════════════════════════════════════════════════════════════════

export const changePassword = async (userId, oldPassword, newPassword) => {
  const response = await api.post(`${AUTH_BASE}/change-password`, {
    user_id: userId,
    old_password: oldPassword,
    new_password: newPassword,
  });
  return response.data;
};

// ══════════════════════════════════════════════════════════════════════════
//  DELETE - DELETE ACCOUNT (PERMANENT)
// ══════════════════════════════════════════════════════════════════════════

export const deleteAccount = async (userId, password) => {
  const response = await api.post(`${AUTH_BASE}/delete-account`, {
    user_id: userId,
    password,
  });
  return response.data;
};

// ══════════════════════════════════════════════════════════════════════════
//  SOFT DELETE - DEACTIVATE ACCOUNT
// ══════════════════════════════════════════════════════════════════════════

export const deactivateAccount = async (userId, password) => {
  const response = await api.post(`${AUTH_BASE}/deactivate-account`, {
    user_id: userId,
    password,
  });
  return response.data;
};

// ══════════════════════════════════════════════════════════════════════════
//  TOKEN MANAGEMENT
// ══════════════════════════════════════════════════════════════════════════

export const saveTokens = (accessToken, refreshToken) => {
  sessionStorage.setItem('access_token', accessToken);
  sessionStorage.setItem('refresh_token', refreshToken);
};

export const getAccessToken = () => {
  return sessionStorage.getItem('access_token');
};

export const clearTokens = () => {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
};

export const isAuthenticated = () => {
  return !!getAccessToken();
};

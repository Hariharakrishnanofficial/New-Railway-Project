/**
 * Session-Based API Client - Smart Railway Ticketing System
 * 
 * Uses HttpOnly cookies for session management (set by server).
 * Includes CSRF token handling for state-changing requests.
 * 
 * Usage:
 *   import sessionApi from './sessionApi';
 *   
 *   // Login (sets HttpOnly cookie automatically)
 *   const result = await sessionApi.login({ email, password });
 *   
 *   // All subsequent requests include session cookie automatically
 *   const trains = await sessionApi.get('/trains');
 */

// CSRF token storage (in memory, not localStorage for security)
let csrfToken = null;

/**
 * Get the current CSRF token.
 * Call refreshCsrfToken() after login to get initial token.
 */
export function getCsrfToken() {
  return csrfToken;
}

/**
 * Set CSRF token (called after login/session validation).
 */
export function setCsrfToken(token) {
  csrfToken = token;
}

/**
 * Clear CSRF token (called on logout).
 */
export function clearCsrfToken() {
  csrfToken = null;
}

function trimTrailingSlash(value) {
  return value.replace(/\/+$/, '');
}

function resolveApiBase() {
  const configuredBase = process.env.REACT_APP_API_BASE_URL?.trim();
  if (configuredBase) {
    return trimTrailingSlash(configuredBase);
  }
  return window.location.origin;
}

function getCandidateBases(baseOrigin) {
  const candidates = [
    `${trimTrailingSlash(baseOrigin)}/server/smart_railway_app_function`,
    `${trimTrailingSlash(baseOrigin)}/app/server/smart_railway_app_function`,
  ];

  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    candidates.push('http://localhost:3000/server/smart_railway_app_function');
    candidates.push('http://127.0.0.1:3000/server/smart_railway_app_function');
  }

  return candidates.filter((base, index, arr) => arr.indexOf(base) === index);
}

function isStateChangingRequest(method) {
  return ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method?.toUpperCase());
}

function withQuery(endpoint, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.append(key, String(value));
    }
  });

  const qs = query.toString();
  return qs ? `${endpoint}?${qs}` : endpoint;
}

function shouldTryNextBase(response, data) {
  if (response.status === 404 || response.status === 405) {
    return true;
  }

  if (response.status >= 500) {
    const msg = String(data?.message || '').toLowerCase();
    return msg.includes('method not allowed') || msg.includes('not found');
  }

  return false;
}

function extractErrorMessage(data, status) {
  const direct = typeof data?.message === 'string' ? data.message : '';
  const details = data?.details;
  const nestedDetailMessage = typeof details?.message === 'string' ? details.message : '';
  const detailsText = typeof details === 'string' ? details : '';

  return direct || nestedDetailMessage || detailsText || `Request failed (${status})`;
}

/**
 * Session-based API client.
 * Authentication via HttpOnly cookies (set by server).
 * CSRF protection via X-CSRF-Token header.
 */
class SessionApiClient {
  constructor() {
    this.baseOrigin = resolveApiBase();
    this.baseUrl = `${trimTrailingSlash(this.baseOrigin)}/server/smart_railway_app_function`;
    this.user = null;
    this.isSessionValid = false;
  }

  /**
   * Get current user from memory cache.
   */
  getUser() {
    return this.user;
  }

  /**
   * Set user in memory cache.
   */
  setUser(user) {
    this.user = user;
    this.isSessionValid = !!user;
  }

  /**
   * Check if user is admin.
   */
  isAdmin(user = null) {
    const current = user || this.getUser();
    if (!current) return false;

    const role = String(current.Role || current.role || '').trim().toLowerCase();
    const userType = String(current.type || current.user_type || '').trim().toLowerCase();
    const adminAccess = !!current?.permissions?.admin_access;

    return adminAccess || (userType === 'employee' && role === 'admin');
  }

  /**
   * Check if session is valid (user is logged in).
   */
  isAuthenticated() {
    return this.isSessionValid && !!this.user;
  }

  /**
   * Core request method.
   * Includes credentials (cookies) and CSRF token.
   */
  async request(endpoint, options = {}) {
    const method = options.method || 'GET';
    
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add CSRF token for state-changing requests
    if (isStateChangingRequest(method) && csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    const configBase = {
      ...options,
      headers,
      credentials: 'include', // Always include cookies
    };

    const candidateBases = [
      trimTrailingSlash(this.baseUrl),
      ...getCandidateBases(this.baseOrigin),
    ].filter((base, index, arr) => arr.indexOf(base) === index);

    let lastError = null;

    for (const base of candidateBases) {
      const url = `${base}${endpoint}`;
      let response = await fetch(url, configBase);
      const contentType = response.headers.get('content-type') || '';
      const isJson = contentType.includes('application/json');
      let data = isJson ? await response.json() : { message: await response.text() };

      if (!response.ok) {
        const errorMessage = extractErrorMessage(data, response.status);
        const error = new Error(errorMessage);
        error.status = response.status;
        error.code = data?.code;
        error.url = url;
        error.body = data;
        lastError = error;

        // Handle session expiry
        if (response.status === 401) {
          this.setUser(null);
          clearCsrfToken();
        }

        if (shouldTryNextBase(response, data)) {
          continue;
        }

        throw error;
      }

      this.baseUrl = base;
      return data;
    }

    throw lastError || new Error('Request failed');
  }

  // HTTP method helpers
  async get(endpoint, options = {}) {
    const target = options.params ? withQuery(endpoint, options.params) : endpoint;
    const data = await this.request(target, { method: 'GET', ...options });
    return { data };
  }

  async post(endpoint, body = {}, options = {}) {
    const data = await this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(body),
      ...options,
    });
    return { data };
  }

  async put(endpoint, body = {}, options = {}) {
    const data = await this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
      ...options,
    });
    return { data };
  }

  async delete(endpoint, options = {}) {
    const data = await this.request(endpoint, {
      method: 'DELETE',
      ...options,
    });
    return { data };
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  AUTH METHODS (Session-based)
  // ══════════════════════════════════════════════════════════════════════════

  /**
   * Register a new user (direct, no OTP).
   * Server sets HttpOnly session cookie.
   * @deprecated Use registerWithOtp for email verification
   */
  async register({ fullName, email, password, phoneNumber, type = 'user', department, designation }) {
    const endpoint = type === 'employee' ? '/session/employee/register' : '/session/register';
    
    const response = await this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify({ 
        fullName, 
        email, 
        password, 
        phoneNumber,
        department,
        designation
      }),
    });

    if (response.status === 'success' && response.data) {
      const userData = response.data.user || response.data.employee;
      this.setUser(userData);
      setCsrfToken(response.data.csrfToken);
    }

    return response;
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  OTP REGISTRATION (Two-Step with Email Verification)
  // ══════════════════════════════════════════════════════════════════════════

  /**
   * Step 1: Initiate registration - sends OTP to email.
   * @param {Object} data - { fullName, email, password, phoneNumber }
   * @returns {Promise<Object>} - { status, message, data: { email, expiresInMinutes } }
   */
  async initiateRegistration({ fullName, email, password, phoneNumber }) {
    const response = await this.request('/session/register/initiate', {
      method: 'POST',
      body: JSON.stringify({ fullName, email, password, phoneNumber }),
    });
    return response;
  }

  /**
   * Step 2: Verify OTP and complete registration.
   * Server sets HttpOnly session cookie on success.
   * @param {string} email - User's email
   * @param {string} otp - 6-digit OTP from email
   * @returns {Promise<Object>} - { status, message, data: { user, csrfToken } }
   */
  async verifyRegistration(email, otp, registration = {}) {
    const response = await this.request('/session/register/verify', {
      method: 'POST',
      body: JSON.stringify({ email, otp, ...registration }),
    });

    if (response.status === 'success' && response.data) {
      this.setUser(response.data.user);
      setCsrfToken(response.data.csrfToken);
    }

    return response;
  }

  /**
   * Resend OTP for pending registration.
   * @param {string} email - User's email
   * @returns {Promise<Object>} - { status, message, data: { expiresInMinutes } }
   */
  async resendRegistrationOtp(email) {
    const response = await this.request('/session/register/resend-otp', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
    return response;
  }

  /**
   * User-specific login.
   * Server sets HttpOnly session cookie.
   */
  async userLogin({ email, password }) {
    const response = await this.request('/session/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.status === 'success' && response.data) {
      this.setUser(response.data.user);
      setCsrfToken(response.data.csrfToken);
    }

    return response;
  }

  /**
   * Login with email and password.
   * Tries employee login first, falls back to user login.
   * Server sets HttpOnly session cookie.
   */
  async login({ email, password }) {
    // Try employee login first; if it fails due to non-employee credentials,
    // fall back to user login. Note: request() throws on non-2xx responses.
    let response;
    try {
      response = await this.request('/session/employee/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
    } catch (err) {
      const status = Number(err?.status);
      // Only fall back for "not an employee / not found / forbidden" style failures.
      if ([400, 401, 403, 404].includes(status) || !Number.isFinite(status)) {
        response = await this.request('/session/login', {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
      } else {
        throw err;
      }
    }

    if (response.status === 'success' && response.data) {
      // Handle both user and employee response formats
      const userData = response.data.user || response.data.employee;
      this.setUser(userData);
      setCsrfToken(response.data.csrfToken);
    }

    return response;
  }

  /**
   * Employee-specific login.
   * Server sets HttpOnly session cookie.
   */
  async employeeLogin({ email, password }) {
    const response = await this.request('/session/employee/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.status === 'success' && response.data) {
      this.setUser(response.data.employee);
      setCsrfToken(response.data.csrfToken);
    }

    return response;
  }

  /**
   * Logout.
   * Server clears session cookie.
   */
  async logout() {
    try {
      await this.request('/session/logout', { method: 'POST' });
    } finally {
      this.setUser(null);
      clearCsrfToken();
    }
  }

  /**
   * Validate current session.
   * Returns user data and refreshes CSRF token.
   */
  async validateSession() {
    try {
      const response = await this.request('/session/validate', { method: 'GET' });
      
      if (response.status === 'success' && response.data) {
        this.setUser(response.data.user);
        if (response.data.csrfToken) {
          setCsrfToken(response.data.csrfToken);
        }
      }
      
      return response;
    } catch (error) {
      this.setUser(null);
      clearCsrfToken();
      throw error;
    }
  }

  /**
   * Update user profile.
   */
  async updateProfile(data) {
    const response = await this.request('/session/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    if (response.status === 'success' && response.data) {
      this.setUser(response.data.user);
    }

    return response;
  }

  /**
   * Change password.
   * Revokes all other sessions automatically.
   */
  async changePassword({ currentPassword, newPassword }) {
    const response = await this.request('/session/change-password', {
      method: 'POST',
      body: JSON.stringify({ currentPassword, newPassword }),
    });

    return response;
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  SESSION MANAGEMENT
  // ══════════════════════════════════════════════════════════════════════════

  /**
   * Get list of active sessions for current user.
   */
  async getSessions() {
    const response = await this.request('/session/sessions', { method: 'GET' });
    return response;
  }

  /**
   * Revoke a specific session by suffix.
   */
  async revokeSession(sessionSuffix) {
    const response = await this.request(`/session/sessions/${sessionSuffix}/revoke`, {
      method: 'POST',
    });
    return response;
  }

  /**
   * Revoke all sessions except current.
   */
  async revokeAllSessions() {
    const response = await this.request('/session/sessions/revoke-all', {
      method: 'POST',
    });
    return response;
  }

  /**
   * Refresh CSRF token.
   */
  async refreshCsrfToken() {
    const response = await this.request('/session/csrf-token', { method: 'GET' });
    if (response.status === 'success' && response.data?.csrfToken) {
      setCsrfToken(response.data.csrfToken);
    }
    return response;
  }

  // ══════════════════════════════════════════════════════════════════════════
  //  NOTIFICATIONS
  // ══════════════════════════════════════════════════════════════════════════

  async getNotifications({ days = 30, limit = 10, offset = 0, unreadOnly = false, type } = {}) {
    const params = new URLSearchParams();
    params.set('days', String(days));
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    if (unreadOnly) params.set('unreadOnly', 'true');
    if (type) params.set('type', String(type));
    return this.request(`/notifications?${params.toString()}`, { method: 'GET' });
  }

  async getUnreadNotificationCount({ days = 30 } = {}) {
    return this.request(`/notifications/unread-count?days=${encodeURIComponent(String(days))}`, { method: 'GET' });
  }

  async markNotificationRead(notificationId) {
    return this.request(`/notifications/${notificationId}/read`, { method: 'PUT' });
  }

  async markAllNotificationsRead({ days = 30 } = {}) {
    return this.request(`/notifications/read-all?days=${encodeURIComponent(String(days))}`, { method: 'PUT' });
  }

  async deleteNotification(notificationId) {
    return this.request(`/notifications/${notificationId}`, { method: 'DELETE' });
  }
}

// Singleton instance
const sessionApi = new SessionApiClient();

// Export helper functions
export function getCurrentUser() {
  return sessionApi.getUser();
}

export function isAdmin(user) {
  return sessionApi.isAdmin(user);
}

// Backward-compatible auth facade
export const sessionAuthApi = {
  async login(payload = {}) {
    const email = payload.email || payload.Email || '';
    const password = payload.password || payload.Password || '';
    const response = await sessionApi.login({ email, password });

    if (response?.status === 'success') {
      return {
        success: true,
        data: response.data,
        user: response.data?.user,
      };
    }

    return {
      success: false,
      error: response?.message || 'Login failed',
      data: response,
    };
  },

  async register(payload = {}) {
    const fullName = payload.fullName || payload.Full_Name || '';
    const email = payload.email || payload.Email || '';
    const password = payload.password || payload.Password || '';
    const phoneNumber = payload.phoneNumber || payload.Phone_Number || '';

    const response = await sessionApi.register({ fullName, email, password, phoneNumber });

    if (response?.status === 'success') {
      return {
        success: true,
        data: response.data,
        user: response.data?.user,
      };
    }

    return {
      success: false,
      error: response?.message || 'Registration failed',
      data: response,
    };
  },

  logout: () => sessionApi.logout(),
};

export default sessionApi;

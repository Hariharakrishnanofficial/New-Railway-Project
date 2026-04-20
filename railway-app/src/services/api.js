import cookieStorage from '../utils/cookieStorage';
import { getCsrfToken } from './sessionApi';

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

  // Local Catalyst dev server usually runs on 3000; include fallback when UI runs on another port.
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    candidates.push('http://localhost:3000/server/smart_railway_app_function');
    candidates.push('http://127.0.0.1:3000/server/smart_railway_app_function');
  }

  return candidates.filter((base, index, arr) => arr.indexOf(base) === index);
}

function shouldAttachAuthHeader(endpoint) {
  return !endpoint.startsWith('/auth/login') && !endpoint.startsWith('/auth/register');
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

function parseTokenPayload(token) {
  if (!token || typeof token !== 'string') {
    return null;
  }

  // JWT format: header.payload.signature
  const parts = token.split('.');
  if (parts.length === 3) {
    try {
      const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const padded = b64.padEnd(Math.ceil(b64.length / 4) * 4, '=');
      return JSON.parse(atob(padded));
    } catch {
      return null;
    }
  }

  // Fallback token used by backend when jwt lib is unavailable.
  try {
    const padded = token.padEnd(Math.ceil(token.length / 4) * 4, '=');
    return JSON.parse(atob(padded));
  } catch {
    return null;
  }
}

function isTokenExpired(token) {
  const payload = parseTokenPayload(token);
  if (!payload || !payload.exp) {
    return false;
  }

  // JWT exp is epoch seconds.
  if (typeof payload.exp === 'number') {
    const nowEpoch = Math.floor(Date.now() / 1000);
    return payload.exp <= nowEpoch;
  }

  // Fallback token exp is ISO datetime.
  if (typeof payload.exp === 'string') {
    const expMs = Date.parse(payload.exp);
    if (Number.isNaN(expMs)) {
      return false;
    }
    return expMs <= Date.now();
  }

  return false;
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

class ApiClient {
  constructor() {
    this.baseOrigin = resolveApiBase();
    this.baseUrl = `${trimTrailingSlash(this.baseOrigin)}/server/smart_railway_app_function`;
  }

  getToken() {
    const token = cookieStorage.getToken();

    if (!token || token === 'undefined' || token === 'null') {
      return null;
    }

    if (isTokenExpired(token)) {
      cookieStorage.clearSession();
      return null;
    }

    return token;
  }

  setToken(token) {
    if (token) {
      const user = cookieStorage.getUser();
      cookieStorage.setSession(token, user);
    } else {
      cookieStorage.clearSession();
    }
  }

  getUser() {
    return cookieStorage.getUser();
  }

  isAdmin(user = null) {
    const current = user || this.getUser();
    if (!current) return false;

    const email = String(current.Email || current.email || '').trim().toLowerCase();
    const role = String(current.Role || current.role || '').trim().toLowerCase();

    if (email.endsWith('@admin.com')) return true;
    return role === 'admin';
  }

  setUser(user) {
    if (user) {
      const token = cookieStorage.getToken();
      cookieStorage.setSession(token, user);
    } else {
      cookieStorage.clearSession();
    }
  }

  async request(endpoint, options = {}) {
    const token = this.getToken();
    const attachAuth = shouldAttachAuthHeader(endpoint);
    const method = options.method || 'GET';

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (token && attachAuth) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const csrfToken = getCsrfToken();
    if (csrfToken && isStateChangingRequest(method)) {
      headers['X-CSRF-Token'] = csrfToken;
    }

    const configBase = {
      ...options,
      credentials: options.credentials || 'include',
      headers,
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

      if (response.status === 431 && configBase.headers?.Authorization) {
        const { Authorization, ...restHeaders } = configBase.headers;
        response = await fetch(url, {
          ...configBase,
          headers: restHeaders,
        });
        const retryContentType = response.headers.get('content-type') || '';
        const retryIsJson = retryContentType.includes('application/json');
        data = retryIsJson ? await response.json() : { message: await response.text() };
      }

      if (!response.ok) {
        const errorMessage = extractErrorMessage(data, response.status);
        const error = new Error(errorMessage);
        error.status = response.status;
        error.url = url;
        error.body = data;
        lastError = error;

        if (shouldTryNextBase(response, data)) {
          continue;
        }

        throw error;
      }

      this.baseUrl = base;

      // Refresh session on successful API call (sliding session)
      if (this.getToken()) {
        cookieStorage.refreshSession();
      }

      return data;
    }

    throw lastError || new Error('Request failed');
  }

  // Axios-like compatibility helpers for legacy callers.
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

  async register({ fullName, email, password, phoneNumber }) {
    const response = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ fullName, email, password, phoneNumber }),
    });

    if (response.status === 'success' && response.data) {
      this.setToken(response.data.token);
      this.setUser(response.data.user);
    }

    return response;
  }

  async login({ email, password }) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.status === 'success' && response.data) {
      this.setToken(response.data.token);
      this.setUser(response.data.user);
    }

    return response;
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
      this.setUser(null);
    }
  }

  async validateSession() {
    const token = this.getToken();
    if (!token) {
      return { status: 'error', message: 'No token' };
    }

    try {
      const response = await this.request('/auth/validate', { method: 'GET' });
      if (response.status === 'success' && response.data) {
        this.setUser(response.data.user);
      }
      return response;
    } catch (error) {
      this.setToken(null);
      this.setUser(null);
      throw error;
    }
  }

  async updateProfile(data) {
    const response = await this.request('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });

    if (response.status === 'success' && response.data) {
      this.setUser(response.data.user);
    }

    return response;
  }

  async changePassword({ currentPassword, newPassword }) {
    const response = await this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify({ currentPassword, newPassword }),
    });

    if (response.status === 'success' && response.data?.token) {
      this.setToken(response.data.token);
    }

    return response;
  }

  isAuthenticated() {
    return !!this.getToken();
  }
}

const api = new ApiClient();

export function getCurrentUser() {
  return api.getUser();
}

export function isAdmin(user) {
  return api.isAdmin(user);
}

// Backward-compatible auth facade used by legacy modal components.
export const authApi = {
  async login(payload = {}) {
    const email = payload.email || payload.Email || '';
    const password = payload.password || payload.Password || '';
    const response = await api.login({ email, password });

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

    const response = await api.register({ fullName, email, password, phoneNumber });

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

  logout: () => api.logout(),
};

export default api;

/**
 * Cookie Storage Manager
 * Drop-in replacement for localStorage with encryption
 * Singleton pattern for consistent state across the application
 */

import Cookies from 'js-cookie';
import { encrypt, decrypt } from './encryption';
import {
  SESSION_COOKIE_NAME,
  COOKIE_OPTIONS,
  MAX_COOKIE_SIZE
} from '../config/security.config';

/**
 * CookieStorage - Encrypted cookie-based storage manager
 * Provides localStorage-like API with automatic encryption/decryption
 */
class CookieStorage {
  /**
   * Store encrypted session data in cookie
   * @param {string} token - Auth token (JWT)
   * @param {object|null} user - User object (can be null during initial login)
   */
  setSession(token, user) {
    try {
      // Create session payload with metadata
      const sessionData = {
        token,
        user,
        timestamp: Date.now(),  // For cache invalidation
        version: 'v1'           // For future migration support
      };

      // Encrypt the payload
      const encryptedData = encrypt(sessionData);

      // Check size (browser limit is 4KB per cookie)
      const estimatedSize = new Blob([encryptedData]).size;
      if (estimatedSize > MAX_COOKIE_SIZE) {
        console.warn('Session cookie exceeds size limit:', estimatedSize, 'bytes');

        // Fallback: Store minimal user data only
        if (user) {
          const minimalUser = {
            id: user.id,
            email: user.email,
            fullName: user.fullName,
            role: user.role,
            accountStatus: user.accountStatus
          };
          console.warn('Storing minimal user data to fit cookie size limit');
          this.setSession(token, minimalUser);
          return;
        }
      }

      // Store encrypted data in cookie
      Cookies.set(SESSION_COOKIE_NAME, encryptedData, COOKIE_OPTIONS);
    } catch (error) {
      console.error('Failed to set session cookie:', error);
      throw error;
    }
  }

  /**
   * Retrieve and decrypt session data from cookie
   * @returns {object|null} Session data or null if invalid/missing
   */
  getSession() {
    try {
      // Get encrypted cookie
      const encryptedData = Cookies.get(SESSION_COOKIE_NAME);

      if (!encryptedData) {
        return null;
      }

      // Decrypt the data
      const sessionData = decrypt(encryptedData);

      // Validate decrypted data
      if (!sessionData || !sessionData.token) {
        console.warn('Invalid session data in cookie (missing token)');
        this.clearSession();
        return null;
      }

      // Validate version for future migrations
      if (sessionData.version !== 'v1') {
        console.warn('Outdated session version:', sessionData.version);
        this.clearSession();
        return null;
      }

      return sessionData;
    } catch (error) {
      console.error('Failed to read session cookie:', error);
      return null;
    }
  }

  /**
   * Get auth token from session
   * @returns {string|null} JWT token or null
   */
  getToken() {
    const session = this.getSession();
    return session?.token || null;
  }

  /**
   * Get user object from session
   * @returns {object|null} User object or null
   */
  getUser() {
    const session = this.getSession();
    return session?.user || null;
  }

  /**
   * Update user data (keep existing token)
   * @param {object|null} user - Updated user object
   */
  setUser(user) {
    const token = this.getToken();
    if (token) {
      this.setSession(token, user);
    } else {
      console.warn('Cannot set user without token');
    }
  }

  /**
   * Update token (keep existing user)
   * @param {string|null} token - Updated JWT token
   */
  setToken(token) {
    const user = this.getUser();
    if (user) {
      this.setSession(token, user);
    } else {
      // Token-only session (e.g., during login flow before user data is available)
      this.setSession(token, null);
    }
  }

  /**
   * Clear session cookie (logout)
   */
  clearSession() {
    Cookies.remove(SESSION_COOKIE_NAME, { path: COOKIE_OPTIONS.path });
  }

  /**
   * Check if session exists
   * @returns {boolean} True if session cookie exists with valid token
   */
  hasSession() {
    return !!this.getToken();
  }

  /**
   * Refresh cookie expiry (sliding session)
   * Call this on each successful API request to extend session
   */
  refreshSession() {
    const session = this.getSession();
    if (session) {
      // Re-set the cookie to update expiry time
      this.setSession(session.token, session.user);
    }
  }

  /**
   * Get session age in milliseconds
   * @returns {number|null} Age in ms or null if no session
   */
  getSessionAge() {
    const session = this.getSession();
    if (!session || !session.timestamp) {
      return null;
    }
    return Date.now() - session.timestamp;
  }
}

// Export singleton instance
export default new CookieStorage();

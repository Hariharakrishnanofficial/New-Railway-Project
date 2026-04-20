/**
 * Session Migration Utility
 * One-time migration from localStorage to encrypted cookies
 * Runs automatically on app load, idempotent (safe to run multiple times)
 */

import Cookies from 'js-cookie';
import cookieStorage from './cookieStorage';
import { MIGRATION_FLAG_COOKIE, COOKIE_OPTIONS } from '../config/security.config';

/**
 * Migrate existing localStorage session to encrypted cookies
 * This runs once per browser and is idempotent
 * @returns {object} Migration result {migrated: boolean, reason: string, error?: string}
 */
export function migrateSessionStorage() {
  try {
    // Check if already migrated (idempotency check)
    const migrationFlag = Cookies.get(MIGRATION_FLAG_COOKIE);
    if (migrationFlag) {
      return {
        migrated: false,
        reason: 'already_migrated',
        previousResult: migrationFlag
      };
    }

    // Check for existing localStorage data
    const token = localStorage.getItem('authToken');
    const userStr = localStorage.getItem('user');

    // No existing session - mark as migrated to skip future checks
    if (!token && !userStr) {
      Cookies.set(MIGRATION_FLAG_COOKIE, 'true', COOKIE_OPTIONS);
      return { migrated: false, reason: 'no_session' };
    }

    // Parse user data if it exists
    let user = null;
    if (userStr) {
      try {
        user = JSON.parse(userStr);
      } catch (e) {
        console.warn('Invalid user JSON in localStorage:', e);
        // Continue without user data
      }
    }

    // Migrate to encrypted cookies
    if (token) {
      cookieStorage.setSession(token, user);
      console.info('✓ Session migrated from localStorage to encrypted cookies');
      console.info('  Token:', token ? '✓ Present' : '✗ Missing');
      console.info('  User:', user ? '✓ Present' : '✗ Missing');
    }

    // Clear localStorage AFTER successful cookie set (safety measure)
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');

    // Also clear legacy session storage if present
    sessionStorage.removeItem('rail_user');

    // Set migration flag to prevent future runs
    Cookies.set(MIGRATION_FLAG_COOKIE, 'true', COOKIE_OPTIONS);

    return {
      migrated: true,
      hasToken: !!token,
      hasUser: !!user
    };
  } catch (error) {
    console.error('Session migration failed:', error);

    // Set error flag to prevent retry loops
    Cookies.set(MIGRATION_FLAG_COOKIE, 'error', COOKIE_OPTIONS);

    return {
      migrated: false,
      reason: 'error',
      error: error.message
    };
  }
}

/**
 * Force re-migration (for testing/debugging only)
 * WARNING: This will clear the migration flag and re-run migration on next load
 */
export function resetMigrationFlag() {
  Cookies.remove(MIGRATION_FLAG_COOKIE, { path: COOKIE_OPTIONS.path });
  console.warn('Migration flag cleared. Migration will run again on next app load.');
}

/**
 * Get migration status (for debugging)
 * @returns {object} Migration status information
 */
export function getMigrationStatus() {
  const flag = Cookies.get(MIGRATION_FLAG_COOKIE);
  const hasLocalStorageToken = !!localStorage.getItem('authToken');
  const hasLocalStorageUser = !!localStorage.getItem('user');
  const hasCookieSession = cookieStorage.hasSession();

  return {
    hasMigrated: !!flag,
    flagValue: flag,
    hasLocalStorage: hasLocalStorageToken || hasLocalStorageUser,
    hasLocalStorageToken,
    hasLocalStorageUser,
    hasCookieSession,
    status: flag === 'true' ? 'success' : flag === 'error' ? 'error' : 'pending'
  };
}

/**
 * Manual migration trigger (for admin/debugging purposes)
 * Forces migration even if flag is set
 */
export function forceMigration() {
  console.warn('Forcing migration...');
  resetMigrationFlag();
  return migrateSessionStorage();
}

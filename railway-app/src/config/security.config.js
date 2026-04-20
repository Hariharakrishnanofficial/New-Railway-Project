/**
 * Security Configuration
 * Cookie options, encryption key, and security constants
 */

// Cookie configuration options
export const COOKIE_OPTIONS = {
  expires: 7,                                      // 7 days (matches token TTL)
  path: '/',                                       // Available to entire app
  secure: process.env.NODE_ENV === 'production',  // HTTPS only in production
  sameSite: 'Strict'                               // CSRF protection
};

// Cookie names
export const SESSION_COOKIE_NAME = 'railway_session';
export const MIGRATION_FLAG_COOKIE = 'railway_migrated';

// Encryption key from environment variable
export const ENCRYPTION_KEY = process.env.REACT_APP_SESSION_ENCRYPTION_KEY;

// Cookie size limits (4KB browser limit, use 3.5KB safety margin)
export const MAX_COOKIE_SIZE = 3500;  // 3.5KB

// Validation on import
if (!ENCRYPTION_KEY) {
  console.error('CRITICAL: REACT_APP_SESSION_ENCRYPTION_KEY not set in environment');
  console.error('Please create .env.local with a valid encryption key');
}

// Validate key length (should be at least 32 characters for 256-bit encryption)
if (ENCRYPTION_KEY && ENCRYPTION_KEY.length < 32) {
  console.error('WARNING: Encryption key is too short. Use at least 32 characters (256-bit)');
}

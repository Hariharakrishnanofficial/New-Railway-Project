/**
 * Encryption Utilities
 * AES-256 encryption/decryption for session data
 */

import CryptoJS from 'crypto-js';
import { ENCRYPTION_KEY } from '../config/security.config';

/**
 * Encrypt data with AES-256
 * @param {string|object} data - Data to encrypt (auto-serializes objects)
 * @returns {string} Encrypted base64 string
 * @throws {Error} If encryption fails
 */
export function encrypt(data) {
  try {
    // Convert objects to JSON string
    const plaintext = typeof data === 'string' ? data : JSON.stringify(data);

    // Encrypt with AES-256 (crypto-js uses CBC mode by default)
    const encrypted = CryptoJS.AES.encrypt(plaintext, ENCRYPTION_KEY);

    // Return as base64 string
    return encrypted.toString();
  } catch (error) {
    console.error('Encryption failed:', error);
    throw new Error('Failed to encrypt session data');
  }
}

/**
 * Decrypt AES-256 encrypted data
 * @param {string} encryptedData - Encrypted base64 string
 * @returns {any} Decrypted data (parsed if JSON), or null on failure
 */
export function decrypt(encryptedData) {
  try {
    // Decrypt the data
    const decrypted = CryptoJS.AES.decrypt(encryptedData, ENCRYPTION_KEY);

    // Convert to UTF-8 string
    const plaintext = decrypted.toString(CryptoJS.enc.Utf8);

    // Check if decryption produced a result
    if (!plaintext) {
      throw new Error('Decryption produced empty result');
    }

    // Try parsing as JSON, fallback to string
    try {
      return JSON.parse(plaintext);
    } catch {
      return plaintext; // Return as string if not JSON
    }
  } catch (error) {
    console.error('Decryption failed:', error);
    return null; // Graceful failure - return null for corrupted/tampered data
  }
}

/**
 * Validate encryption key is properly configured
 * @throws {Error} If encryption key is invalid
 */
export function validateEncryptionKey() {
  if (!ENCRYPTION_KEY) {
    throw new Error('Encryption key not configured. Set REACT_APP_SESSION_ENCRYPTION_KEY in .env.local');
  }

  if (ENCRYPTION_KEY.length < 32) {
    throw new Error('Encryption key is too short. Must be at least 32 characters (256-bit)');
  }
}

// Validate on module load
try {
  validateEncryptionKey();
} catch (error) {
  console.error('Encryption key validation failed:', error.message);
}

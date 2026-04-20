/**
 * Email Masking Utilities - Production Ready
 * 
 * Security-focused email masking for privacy protection.
 * Follows industry standards similar to Google, Microsoft, and banking apps.
 * 
 * @module emailUtils
 * @version 2.0.0
 */

// Masking character options
const MASK_CHAR = '•';  // Unicode bullet (U+2022) - most readable
const MASK_ASTERISK = '*';
const MASK_DOT = '·';

/**
 * Validates if a string is a valid email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid email format
 */
export function isValidEmail(email) {
  if (!email || typeof email !== 'string') return false;
  // RFC 5322 simplified regex
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email.trim());
}

/**
 * Production-grade email masking (Google/Microsoft style)
 * 
 * Shows first 2 chars + last char of local part, full domain visible.
 * This is the most common pattern used by major tech companies.
 * 
 * Examples:
 *   john@gmail.com          → jo•••n@gmail.com
 *   alice.smith@company.com → al•••h@company.com  
 *   ab@test.com             → a•••b@test.com
 *   a@x.co                  → a•••@x.co
 *   test@subdomain.mail.com → te•••t@subdomain.mail.com
 * 
 * @param {string} email - Email address to mask
 * @param {Object} options - Masking options
 * @param {number} options.showStart - Characters to show at start (default: 2)
 * @param {number} options.showEnd - Characters to show at end (default: 1)
 * @param {number} options.minMaskLength - Minimum mask length (default: 3)
 * @param {string} options.maskChar - Character to use for masking (default: '•')
 * @returns {string} Masked email or original if invalid
 */
export function maskEmail(email, options = {}) {
  if (!isValidEmail(email)) {
    return email || '';
  }

  const {
    showStart = 2,
    showEnd = 1,
    minMaskLength = 3,
    maskChar = MASK_CHAR
  } = options;

  const [localPart, domain] = email.toLowerCase().trim().split('@');
  
  // Calculate how many characters to mask
  const totalVisible = showStart + showEnd;
  const localLength = localPart.length;
  
  let maskedLocal;
  
  if (localLength <= 1) {
    // Single character: show it + mask
    maskedLocal = localPart + maskChar.repeat(minMaskLength);
  } else if (localLength <= totalVisible) {
    // Short email: show first char + mask + last char
    maskedLocal = localPart.charAt(0) + maskChar.repeat(minMaskLength) + 
                  (localLength > 1 ? localPart.charAt(localLength - 1) : '');
  } else {
    // Normal email: show start chars + mask + end chars
    const start = localPart.substring(0, showStart);
    const end = localPart.substring(localLength - showEnd);
    const maskLength = Math.max(minMaskLength, localLength - totalVisible);
    maskedLocal = start + maskChar.repeat(Math.min(maskLength, 5)) + end;
  }

  return `${maskedLocal}@${domain}`;
}

/**
 * Full privacy masking (Banking/Financial style)
 * 
 * Shows only first char of local part and first char of domain.
 * Maximum privacy for sensitive contexts.
 * 
 * Examples:
 *   john@gmail.com          → j•••@g•••.com
 *   alice.smith@company.com → a•••@c•••.com
 * 
 * @param {string} email - Email address to mask
 * @returns {string} Heavily masked email
 */
export function maskEmailStrict(email) {
  if (!isValidEmail(email)) {
    return email || '';
  }

  const [localPart, domain] = email.toLowerCase().trim().split('@');
  const domainParts = domain.split('.');
  
  // Mask local part: first char + dots
  const maskedLocal = localPart.charAt(0) + MASK_CHAR.repeat(4);
  
  // Mask domain: first char of domain name + dots + full TLD
  let maskedDomain;
  if (domainParts.length >= 2) {
    const domainName = domainParts[0];
    const tld = domainParts.slice(1).join('.');
    maskedDomain = domainName.charAt(0) + MASK_CHAR.repeat(4) + '.' + tld;
  } else {
    maskedDomain = domain.charAt(0) + MASK_CHAR.repeat(4);
  }

  return `${maskedLocal}@${maskedDomain}`;
}

/**
 * Partial masking for confirmation displays
 * 
 * Shows more characters for user confirmation while still protecting privacy.
 * Ideal for "We sent a code to your email" messages.
 * 
 * Examples:
 *   john@gmail.com              → jo••n@gmail.com
 *   hariharakrishnan@gmail.com  → har••••nan@gmail.com
 *   ab@test.com                 → a••b@test.com
 * 
 * @param {string} email - Email address to mask
 * @param {Object} options - Masking options  
 * @param {number} options.showStart - Characters to show at start (default: 3)
 * @param {number} options.showEnd - Characters to show at end (default: 3)
 * @returns {string} Partially masked email
 */
export function partialEmail(email, options = {}) {
  if (!isValidEmail(email)) {
    return email || '';
  }

  const {
    showStart = 3,
    showEnd = 3
  } = options;

  const [localPart, domain] = email.toLowerCase().trim().split('@');
  const localLength = localPart.length;
  
  let maskedLocal;
  
  if (localLength <= 4) {
    // Very short: show first + mask + last
    maskedLocal = localPart.charAt(0) + MASK_CHAR.repeat(2) + 
                  (localLength > 1 ? localPart.charAt(localLength - 1) : '');
  } else if (localLength <= showStart + showEnd) {
    // Short: show first 2 + mask + last 2
    const half = Math.floor(localLength / 2);
    maskedLocal = localPart.substring(0, half) + MASK_CHAR.repeat(2) + 
                  localPart.substring(localLength - (localLength - half));
  } else {
    // Normal: show start + mask + end
    const start = localPart.substring(0, showStart);
    const end = localPart.substring(localLength - showEnd);
    maskedLocal = start + MASK_CHAR.repeat(4) + end;
  }

  return `${maskedLocal}@${domain}`;
}

/**
 * Minimal masking for logged-in user displays
 * 
 * Shows most of the email, just obscures middle portion.
 * Use when user is authenticated and email is their own.
 * 
 * Examples:
 *   john@gmail.com              → john@gmail.com (too short to mask)
 *   hariharakrishnan@gmail.com  → hariha••••hnan@gmail.com
 * 
 * @param {string} email - Email address to mask
 * @returns {string} Minimally masked email
 */
export function maskEmailLight(email) {
  if (!isValidEmail(email)) {
    return email || '';
  }

  const [localPart, domain] = email.toLowerCase().trim().split('@');
  
  // Don't mask short emails
  if (localPart.length <= 8) {
    return email.toLowerCase().trim();
  }

  const showCount = Math.floor(localPart.length / 3);
  const start = localPart.substring(0, showCount);
  const end = localPart.substring(localPart.length - showCount);
  
  return `${start}${MASK_CHAR.repeat(4)}${end}@${domain}`;
}

/**
 * Check if an email appears to be masked
 * @param {string} email - Email to check
 * @returns {boolean} True if email contains masking characters
 */
export function isMaskedEmail(email) {
  if (!email || typeof email !== 'string') return false;
  return email.includes(MASK_CHAR) || 
         email.includes(MASK_ASTERISK) || 
         email.includes('***') ||
         email.includes('•••');
}

/**
 * Format email for display based on context
 * 
 * @param {string} email - Email to format
 * @param {string} context - Display context
 *   - 'confirmation': For OTP/verification messages (shows more)
 *   - 'public': For public displays (maximum masking)
 *   - 'profile': For user's own profile (minimal masking)
 *   - 'list': For admin lists (standard masking)
 *   - 'full': No masking (authenticated user viewing own email)
 * @returns {string} Formatted email
 */
export function formatEmailForDisplay(email, context = 'confirmation') {
  if (!email) return '';
  
  switch (context) {
    case 'confirmation':
    case 'otp':
    case 'verify':
      return partialEmail(email);
      
    case 'public':
    case 'strict':
    case 'banking':
      return maskEmailStrict(email);
      
    case 'profile':
    case 'light':
      return maskEmailLight(email);
      
    case 'list':
    case 'admin':
    case 'standard':
      return maskEmail(email);
      
    case 'full':
    case 'none':
      return email.toLowerCase().trim();
      
    default:
      return partialEmail(email);
  }
}

/**
 * Get domain from email
 * @param {string} email - Email address
 * @returns {string} Domain part of email
 */
export function getEmailDomain(email) {
  if (!isValidEmail(email)) return '';
  return email.split('@')[1].toLowerCase();
}

/**
 * Get local part from email
 * @param {string} email - Email address
 * @returns {string} Local part of email (before @)
 */
export function getEmailLocalPart(email) {
  if (!isValidEmail(email)) return '';
  return email.split('@')[0].toLowerCase();
}

// Export masking characters for customization
export const MASKING_CHARS = {
  BULLET: MASK_CHAR,
  ASTERISK: MASK_ASTERISK,
  DOT: MASK_DOT
};
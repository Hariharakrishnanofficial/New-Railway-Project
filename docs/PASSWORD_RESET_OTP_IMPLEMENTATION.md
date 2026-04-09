# Password Reset OTP Implementation

## Overview
Changed password reset from token-based to OTP (One-Time Password) based system with configurable timer.

## Changes Made

### 1. Backend Changes

#### `otp_service.py`
- **Fixed**: `_cleanup_old_otps()` - Changed `Is_Used = false` to `Is_Used = 'false'` (string format for Catalyst DB)
- **Added**: `send_password_reset_otp(email)` - Sends 6-digit OTP for password reset
- **Added**: `verify_password_reset_otp(email, otp)` - Verifies password reset OTP
- **Added**: `resend_password_reset_otp(email)` - Resends password reset OTP
- **Email Template**: `_build_password_reset_email(otp)` - Beautiful HTML email with OTP

#### `auth.py`
- **Updated**: `/auth/forgot-password` endpoint
  - Now sends OTP via `send_password_reset_otp()`
  - Returns `expiresInMinutes` from env config
  - Handles cooldown with 429 status code
  
- **Updated**: `/auth/reset-password` endpoint
  - Now accepts `otp` field instead of `token`
  - Uses `verify_password_reset_otp()` for verification
  - Simplified validation (no SQL token lookup needed)

### 2. Frontend Changes

#### `AuthPage.jsx`
- **Added**: `ResetOTPInput` component - 6-digit OTP input with:
  - Auto-advance on digit entry
  - Paste support
  - Backspace handling
  - Arrow key navigation
  - Focus states

- **Added State**:
  - `resetOtp` - Current OTP value
  - `resetOtpSent` - Flag for OTP sent status
  - `resetOtpExpiresInMinutes` - Expiry time from server
  - `resetOtpTimeLeft` - Countdown timer in seconds

- **Added Timer Logic**:
  - useEffect countdown from `resetOtpTimeLeft`
  - Updates every second
  - Shows MM:SS format
  - Disables submit when expired

- **Updated Handlers**:
  - `handleForgotPassword()` - Starts timer on OTP send
  - `handleResetPassword()` - Sends OTP instead of token
  - `handleResendResetOtp()` - Resets timer on resend

- **UI Enhancements**:
  - Timer display with color coding (blue = active, red = expired)
  - Resend button with cooldown (disabled for first 30 seconds)
  - Submit button disabled when OTP expired
  - Better error messages

### 3. Environment Configuration

#### `.env`
```env
# OTP expiry time in minutes (customizable)
OTP_EXPIRY_MINUTES=1

# Maximum OTP verification attempts
OTP_MAX_ATTEMPTS=3

# Cooldown between OTP resend requests in seconds
OTP_RESEND_COOLDOWN_SECONDS=60

# Verified sender email for OTP emails
CATALYST_FROM_EMAIL=krishnan.hari@zappyworks.com

# Application name displayed in emails
APP_NAME=Smart Railway
```

## User Flow

1. **Forgot Password Request**
   - User clicks "Forgot Password" on login page
   - Enters email address
   - Clicks "Send Verification Code"
   - Backend sends 6-digit OTP via email

2. **OTP Entry & Password Reset**
   - User sees reset password form with 6 OTP boxes
   - Timer starts counting down (e.g., 1:00)
   - User enters OTP from email
   - User enters new password + confirmation
   - Clicks "Reset Password"
   - Backend verifies OTP and updates password

3. **Timer Expiration**
   - If timer reaches 0:00, submit is disabled
   - User sees "Code expired" message
   - User can click "Resend Code" to get new OTP

4. **Resend OTP**
   - Resend button disabled for first 30 seconds
   - After 30 seconds, user can request new OTP
   - Timer resets to full duration

## Security Features

1. **Rate Limiting**: 5 requests per hour for forgot password
2. **Cooldown**: 60 seconds between resend requests
3. **Expiration**: OTP expires after configured minutes (default 1 min in dev)
4. **Single Use**: OTP marked as used after successful verification
5. **Purpose Isolation**: Password reset OTPs separate from registration OTPs
6. **Email Obfuscation**: Email addresses masked in UI (e.g., ha•••n@gmail.com)

## Email Template

The password reset email includes:
- 🚂 App branding
- Clear "Reset Your Password" heading
- 6-digit OTP in large, monospace font
- Pink/red gradient card for visibility
- Expiration time warning
- Security warning if user didn't request reset
- Professional footer

## Testing

To test the implementation:

1. Start backend: `catalyst serve`
2. Start frontend: `npm start`
3. Navigate to login page
4. Click "Forgot Password"
5. Enter registered email
6. Check email for 6-digit OTP
7. Enter OTP in reset form
8. Watch timer countdown
9. Enter new password
10. Verify password reset works

## Configuration Notes

- `OTP_EXPIRY_MINUTES` in `.env` controls timer duration
- Set to `1` for development (quick testing)
- Set to `15` for production (standard practice)
- Timer shows MM:SS format (e.g., 1:00, 14:30)
- Resend cooldown prevents spam (60 seconds default)

## Database Schema

Uses existing `OTP_Tokens` table:
```
- User_Email: email address
- OTP: 6-digit code
- Purpose: 'password_reset'
- Expires_At: timestamp
- Is_Used: 'false' (string boolean)
- Attempts: '0' (string integer)
- Created_At: timestamp
```

## Future Enhancements

1. Add SMS OTP option
2. Add backup codes for account recovery
3. Add security questions
4. Log all password reset attempts
5. Add IP-based rate limiting
6. Add CAPTCHA for repeated failures

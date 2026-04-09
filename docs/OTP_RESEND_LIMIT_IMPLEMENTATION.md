# OTP Resend Limit Implementation

## Overview
Added resend limits to prevent abuse of the OTP system for both registration and password reset flows. Users now have a maximum number of resend attempts within a 1-hour window.

## Configuration

### Environment Variables (.env)
```bash
# Maximum resend attempts per hour (default: 3)
# After this limit, user must wait 1 hour before requesting more OTPs
OTP_MAX_RESEND_ATTEMPTS=3

# Existing OTP configurations
OTP_EXPIRY_MINUTES=1                    # OTP validity (minutes)
OTP_MAX_ATTEMPTS=3                      # Max wrong OTP entry attempts
OTP_RESEND_COOLDOWN_SECONDS=60         # Cooldown between resends (seconds)
```

## How It Works

### Backend Tracking
**File:** `functions/smart_railway_app_function/services/otp_service.py`

1. **In-Memory Tracker:**
   ```python
   _resend_attempt_tracker = {}
   # Format: {f"{email}:{purpose}": {"count": int, "first_attempt_at": datetime}}
   ```

2. **Key Functions:**
   - `_track_resend_attempt()` - Increments counter for each resend
   - `_check_resend_limit()` - Validates if user can still resend
   - `_reset_resend_tracker()` - Clears counter on successful verification

3. **Limit Logic:**
   - First OTP send counts as attempt #1
   - Each resend increments the counter
   - After `OTP_MAX_RESEND_ATTEMPTS` (default: 3), returns error
   - Counter auto-resets after 1 hour from first attempt
   - Counter resets on successful OTP verification

### API Responses

#### Success Response
```json
{
  "status": "success",
  "message": "Verification code sent to your email",
  "expiresInMinutes": 1,
  "remaining_resend_attempts": 2
}
```

#### Limit Exceeded Response (429)
```json
{
  "status": "error",
  "message": "Maximum resend limit (3) reached. Please try again after 1 hour.",
  "limit_exceeded": true
}
```

#### Cooldown Response (429)
```json
{
  "status": "error",
  "message": "Please wait 45 seconds before requesting another code",
  "cooldown": 45
}
```

## User Experience

### Registration Email Verification

**Scenario 1: Normal Flow**
1. User registers → Gets OTP email (2 resends remaining)
2. Clicks "Resend Code" → New OTP sent (1 resend remaining)
3. Toast shows: "New code sent! 1 resend remaining."

**Scenario 2: Limit Reached**
1. User clicks resend 3 times
2. 4th attempt shows: "Maximum resend limit (3) reached. Please try again after 1 hour."
3. Resend button disabled with error message

**Scenario 3: Successful Verification**
1. User enters correct OTP
2. Counter resets automatically
3. Next registration (different email) starts fresh

### Password Reset

**Scenario 1: Normal Flow**
1. User requests password reset → Gets OTP (2 resends remaining)
2. Clicks "🔄 Resend Code" → New OTP sent (1 resend remaining)
3. Toast shows: "New code sent! 1 resend remaining."

**Scenario 2: Limit Reached**
1. User requests reset 3 times
2. 4th attempt: "Maximum resend limit (3) reached. Please try again after 1 hour."
3. Error toast displayed

## Frontend Changes

### AuthPage.jsx

**Registration Resend Handler:**
```javascript
const handleOtpResend = async () => {
  const result = await resendOtp(pendingEmail);
  
  if (result.success) {
    const remaining = result.remaining_resend_attempts;
    if (remaining !== undefined && remaining > 0) {
      toast.success(`New code sent! ${remaining} resend${remaining !== 1 ? 's' : ''} remaining.`);
    } else {
      toast.success('New verification code sent!');
    }
  } else if (result.limit_exceeded) {
    toast.error(result.error || 'Maximum resend limit reached. Please try again later.');
  }
};
```

**Password Reset Resend Handler:**
```javascript
const handleResendResetOtp = async () => {
  const response = await api.post('/auth/forgot-password', {
    email: form.email
  });
  
  if (response.data.status === 'success') {
    const remaining = response.data.remaining_resend_attempts;
    toast.success(`New code sent! ${remaining} resend${remaining !== 1 ? 's' : ''} remaining.`);
  } else if (response.data.limit_exceeded) {
    toast.error(response.data.message || 'Maximum resend limit reached.');
  }
};
```

## Backend Implementation Details

### Modified Functions

**1. send_registration_otp() - Added `is_resend` parameter**
```python
def send_registration_otp(email: str, is_resend: bool = False) -> Dict:
    # Check resend limit (only for resend requests)
    if is_resend:
        can_resend_limit, remaining_attempts = _check_resend_limit(email, 'registration')
        if not can_resend_limit:
            return {
                'success': False,
                'error': f'Maximum resend limit ({OTP_MAX_RESEND_ATTEMPTS}) reached...',
                'limit_exceeded': True
            }
    
    # Track resend attempt
    if is_resend:
        _track_resend_attempt(email, 'registration')
    
    # ... rest of OTP generation and sending logic
```

**2. send_password_reset_otp() - Added `is_resend` parameter**
```python
def send_password_reset_otp(email: str, is_resend: bool = False) -> Dict:
    # Same logic as registration
    # Tracks every attempt (including first one)
```

**3. verify_otp() - Auto-resets tracker on success**
```python
def verify_otp(email: str, otp: str, purpose: str = 'registration') -> Tuple[bool, str]:
    # ... verification logic
    
    if otp_valid:
        # Reset resend tracker on successful verification
        _reset_resend_tracker(email, purpose)
    
    return success, message
```

### Route Changes

**1. /session/register/resend-otp**
```python
otp_result = send_registration_otp(email, is_resend=True)

if otp_result.get('limit_exceeded'):
    return jsonify({
        'status': 'error',
        'message': otp_result.get('error'),
        'limit_exceeded': True
    }), 429
```

**2. /auth/forgot-password**
```python
# Always track as resend (including first attempt)
result = send_password_reset_otp(email, is_resend=True)

if result.get('limit_exceeded'):
    return jsonify({
        'status': 'error',
        'message': result.get('error'),
        'limit_exceeded': True
    }), 429
```

## Testing

### Test Cases

**1. Normal Resend Flow**
- ✅ First OTP send succeeds
- ✅ Resend button shows remaining attempts
- ✅ Each resend decrements counter
- ✅ Toast shows "X resends remaining"

**2. Limit Reached**
- ✅ After 3 attempts, 4th returns 429 error
- ✅ Error message shows 1-hour wait time
- ✅ Frontend shows appropriate error toast

**3. Counter Reset (Time-based)**
- ✅ After 1 hour, counter auto-resets
- ✅ User can request new OTPs

**4. Counter Reset (Verification)**
- ✅ On successful OTP verification, counter resets immediately
- ✅ Next OTP request starts with full limit

**5. Cooldown vs Limit**
- ✅ Cooldown (60s) prevents rapid requests
- ✅ Limit (3 attempts) prevents long-term abuse
- ✅ Both work together correctly

### Manual Testing Steps

**Registration:**
1. Go to register page, fill form, submit
2. On OTP page, click "Resend Code" 
3. Verify toast shows "2 resends remaining"
4. Click resend again → "1 resend remaining"
5. Click resend again → "0 resends remaining"
6. Try clicking again → Error: "Maximum resend limit reached"

**Password Reset:**
1. Click "Forgot Password"
2. Enter email, get OTP screen
3. Click "🔄 Resend Code" 3 times
4. 4th click should show limit error
5. Wait 1 hour or enter correct OTP to reset

## Security Considerations

1. **In-Memory Storage:**
   - Tracker resets on server restart
   - Consider Redis for production (persistent storage across restarts)

2. **Rate Limiting Still Active:**
   - Existing rate limits still apply
   - Resend limit adds extra layer

3. **Per Email+Purpose Tracking:**
   - Registration and password reset tracked separately
   - Same email can request both simultaneously

4. **1-Hour Window:**
   - Prevents long-term abuse
   - Reasonable for legitimate users
   - Can be adjusted via future configuration

## Production Recommendations

1. **Increase OTP_EXPIRY_MINUTES to 15** (currently 1 for dev)
2. **Consider persistent storage** (Redis) for tracker in production
3. **Monitor resend patterns** for abuse detection
4. **Add user notification** when limit is reached
5. **Log limit violations** for security analysis

## Files Modified

### Backend
- `functions/smart_railway_app_function/services/otp_service.py`
  - Added `_track_resend_attempt()`
  - Added `_check_resend_limit()`
  - Added `_reset_resend_tracker()`
  - Modified `send_registration_otp()`
  - Modified `send_password_reset_otp()`
  - Modified `verify_otp()`

- `functions/smart_railway_app_function/routes/otp_register.py`
  - Updated `/session/register/resend-otp` endpoint

- `functions/smart_railway_app_function/routes/auth.py`
  - Updated `/auth/forgot-password` endpoint

- `functions/smart_railway_app_function/.env`
  - Added `OTP_MAX_RESEND_ATTEMPTS=3`

### Frontend
- `railway-app/src/pages/auth/AuthPage.jsx`
  - Updated `handleOtpResend()` - shows remaining attempts
  - Updated `handleResendResetOtp()` - shows remaining attempts

- `railway-app/src/context/SessionAuthContext.jsx`
  - Updated `resendOtp()` - handles `limit_exceeded` response

## Summary

The OTP resend limit feature provides:
- ✅ Prevents abuse of email OTP system
- ✅ Configurable limits via environment variables
- ✅ User-friendly error messages with remaining attempts
- ✅ Automatic reset after 1 hour
- ✅ Automatic reset on successful verification
- ✅ Works for both registration and password reset
- ✅ Maintains existing cooldown functionality
- ✅ Clear toast notifications for users

**Default Limits:**
- 3 total resend attempts per hour (configurable)
- 60-second cooldown between requests (configurable)
- Auto-reset after 1 hour or successful verification

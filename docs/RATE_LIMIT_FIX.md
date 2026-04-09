# Rate Limit Fix for Forgot Password

## Issue
Getting 429 (TOO MANY REQUESTS) when testing forgot password functionality.

## Root Cause
The `/auth/forgot-password` endpoint had hardcoded rate limit of 5 calls per hour, which is too restrictive for development testing.

## Solution Applied

### 1. Added Environment Variables
Added to `.env`:
```env
# Forgot Password specific rate limiting
# For development: 100 attempts per hour
# For production: 5 attempts per hour recommended
RATE_LIMIT_FORGOT_PASSWORD=100
RATE_LIMIT_FORGOT_PASSWORD_WINDOW=3600
```

### 2. Updated auth.py
```python
# Added configuration constants
RATE_LIMIT_FORGOT_PASSWORD = int(os.getenv('RATE_LIMIT_FORGOT_PASSWORD', '5'))
RATE_LIMIT_FORGOT_PASSWORD_WINDOW = int(os.getenv('RATE_LIMIT_FORGOT_PASSWORD_WINDOW', '3600'))

# Updated decorator
@auth_bp.route('/auth/forgot-password', methods=['POST'])
@rate_limit(max_calls=RATE_LIMIT_FORGOT_PASSWORD, window_seconds=RATE_LIMIT_FORGOT_PASSWORD_WINDOW)
def forgot_password():
```

## To Clear Rate Limit

**Option 1: Restart the server (RECOMMENDED)**
```bash
# Stop the current server (Ctrl+C)
catalyst serve
```

**Option 2: Wait 60 minutes** (not practical for testing)

**Option 3: Change your IP or use incognito mode** (rate limits are per IP)

## Configuration for Different Environments

### Development (.env)
```env
RATE_LIMIT_FORGOT_PASSWORD=100      # 100 attempts
RATE_LIMIT_FORGOT_PASSWORD_WINDOW=3600  # per hour
```

### Production (.env)
```env
RATE_LIMIT_FORGOT_PASSWORD=5        # 5 attempts
RATE_LIMIT_FORGOT_PASSWORD_WINDOW=3600  # per hour
```

## Testing After Fix

1. Restart the Catalyst server
2. Go to login page → "Forgot Password"
3. You can now test up to 100 times per hour
4. Rate limit resets automatically after 1 hour

## Security Note

The rate limiting is stored in-memory, so it resets when the server restarts. For production, consider:
- Redis-based rate limiting for distributed systems
- Database-backed rate limit tracking
- IP-based + email-based rate limiting

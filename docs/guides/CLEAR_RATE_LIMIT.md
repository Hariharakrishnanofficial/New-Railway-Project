# Clear Rate Limits - Quick Script

**Issue:** Hit rate limit (429) again  
**Solution:** Call debug endpoint to clear

---

## Quick Fix

### Open a new terminal and run:

```bash
curl -X POST http://localhost:3000/server/smart_railway_app_function/debug/clear-rate-limits
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Cleared X rate limit entries",
  "note": "This endpoint is only available in development mode"
}
```

---

## Then Try Registration Again

The rate limit is cleared - you can register now.

---

## Alternative: Wait 30 Seconds

Or just wait 30 seconds as the message says, but clearing is faster.

---

## To Prevent This

The `.env` already has high limits:
```bash
RATE_LIMIT_AUTH=1000
RATE_LIMIT_WINDOW=3600
```

But the server needs to be restarted for this to take effect.

**Did you restart the server after the .env was updated?**

If not:
```bash
# Stop server
Ctrl+C

# Delete .build
rmdir /s /q .build

# Restart
catalyst serve
```

---

**Clear rate limits now with the curl command above!**

# 🔧 URGENT FIX: SSL Certificate Error

**Error:** `Could not find a suitable TLS CA certificate bundle`  
**Cause:** Missing SSL certificates for HTTPS requests  
**Impact:** Cannot connect to Catalyst database/email services

---

## Quick Fix (Option 1: Recommended)

### Install certifi package

```bash
cd functions\smart_railway_app_function
pip install certifi
```

### Restart server

```bash
catalyst serve
```

---

## Quick Fix (Option 2: Set Environment Variable)

If Option 1 doesn't work, set SSL certificate path:

### Windows (PowerShell):
```powershell
$env:REQUESTS_CA_BUNDLE = (python -m certifi)
catalyst serve
```

### Windows (Command Prompt):
```cmd
set REQUESTS_CA_BUNDLE=%LOCALAPPDATA%\Programs\Python\Python3XX\Lib\site-packages\certifi\cacert.pem
catalyst serve
```

---

## Quick Fix (Option 3: Add to requirements.txt)

### 1. Edit requirements.txt

Add this line:
```txt
certifi>=2023.7.22
```

### 2. Install

```bash
pip install -r requirements.txt
```

### 3. Restart

```bash
catalyst serve
```

---

## Why This Happens

The Catalyst SDK uses `requests` library which needs SSL certificates to make HTTPS calls to:
- Catalyst database (CloudScale)
- Catalyst email service
- Other Catalyst APIs

The `certifi` package provides these certificates.

---

## Verify Fix

After installing certifi, try to register again.

**Expected logs (good):**
```
INFO: OTP created for user@example.com
INFO: OTP email sent to user@example.com
```

**NOT see (bad):**
```
ERROR: Could not find a suitable TLS CA certificate bundle
```

---

## If Still Not Working

Try this in Python to check certifi:

```bash
python -c "import certifi; print(certifi.where())"
```

Should print path like:
```
C:\Users\...\site-packages\certifi\cacert.pem
```

If error, certifi is not installed properly.

---

**Fix this NOW - it's blocking everything!** 🚨

Run:
```bash
pip install certifi
catalyst serve
```

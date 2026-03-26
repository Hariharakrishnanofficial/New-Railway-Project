# Fix for React Router (SPA) with Catalyst

## Problem
When you navigate to `/app/auth`, the server tries to serve a file instead of routing it to React Router. Browser DevTools shows:
```
GET /app/auth → 404 (returns error HTML)
```

This happens because:
1. Catalyst's static file server doesn't know `/app/auth` is a React route
2. It tries to find `auth.html` or `auth/index.html` in the build folder
3. Finding nothing, it returns 404.html

---

## Solution

The fix requires adding a **catch-all route** that serves `index.html` for all unknown paths, allowing React Router to handle client-side routing.

### Option 1: Fix in Catalyst Routes (Recommended)

Add this to `functions/catalyst_backend/routes/__init__.py`:

```python
# Add this AFTER all other route registrations

# SPA catch-all: serve index.html for client-side routing
@app.route('/app/<path:path>')
@app.route('/app')
def serve_spa(path=''):
    """Serve React app for all /app/* routes (SPA routing)"""
    try:
        with open('../../catalyst-frontend/build/index.html', 'r') as f:
            return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        logger.error(f'Failed to serve index.html: {e}')
        return jsonify({'error': 'Unable to serve app'}), 500
```

### Option 2: Use Catalyst's Static File Server

Catalyst CLI should handle this automatically if configured correctly. The issue might be in `catalyst.json`:

```json
{
  "functions": {
    "targets": ["catalyst_backend"],
    "ignore": [],
    "source": "functions"
  },
  "client": {
    "source": "catalyst-frontend"
  }
}
```

This looks correct. The issue is that Catalyst doesn't automatically redirect unknown routes to index.html.

### Option 3: Create a _redirects file (Netlify/Vercel style)

Create `catalyst-frontend/build/_redirects`:
```
/app/* /app/index.html 200
```

But Catalyst doesn't support this natively.

---

## Recommended Fix (Quickest)

Add this route to `functions/catalyst_backend/routes/__init__.py`:

```python
import os
from flask import send_from_directory

# After all other blueprints are registered, add:

@app.route('/app/')
@app.route('/app/<path:path>')
def serve_spa(path=''):
    """Serve React SPA - redirects all /app/* to index.html for client-side routing"""
    try:
        build_path = os.path.join(os.path.dirname(__file__), '../../catalyst-frontend/build')
        # For any non-file request, serve index.html
        if '.' not in path or path.endswith('index.html'):
            return send_from_directory(build_path, 'index.html')
        # For actual files (assets, etc), serve them
        try:
            return send_from_directory(build_path, path)
        except:
            # If file not found, serve index.html (let React handle the route)
            return send_from_directory(build_path, 'index.html')
    except Exception as e:
        from flask import jsonify
        return jsonify({'error': f'Failed to serve app: {str(e)}'}), 500
```

---

## Steps to Apply Fix

1. **Open:** `functions/catalyst_backend/routes/__init__.py`
2. **Add above code** at the END of the file (after all blueprint registrations)
3. **Save file**
4. **Run:** `rebuild_and_serve.bat`
5. **Test:** Navigate to `http://localhost:3000/app/auth`
6. **Expected:** AuthPage loads (red circle gone, page visible)

---

## Why This Works

Flow:
```
Browser: GET /app/auth
  ↓
Catalyst routes to Flask
  ↓
Flask tries to match /app/auth route
  ↓
NEW catch-all route matches: /app/<path:path>
  ↓
Returns index.html (which loads React + React Router)
  ↓
React loads and routing rule matches /auth
  ↓
AuthPage component renders ✓
```

---

## Testing After Fix

Open DevTools (F12) → Network tab:
- `GET /app/auth` should return **200** (not 404)
- Response should be HTML (index.html content)
- Page should load fully (no red circle)
- No JavaScript errors in Console tab

---

## If Still Not Working

**Check:**
1. Asset paths still correct? (`/assets/` not `/app/assets/`)
2. Flask restarted? (`catalyst serve`)
3. Build folder exists? (`catalyst-frontend/build/index.html`)
4. Correct path to build folder in route?

**Debug:**
```bash
# Check if index.html accessible
cat catalyst-frontend/build/index.html | head -5

# Restart Catalyst with verbose:
catalyst serve --verbose
```


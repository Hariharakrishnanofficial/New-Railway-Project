# 🚀 Security Fix Quick Reference
## Smart Railway Ticketing System

**Quick implementation guide for developers**

---

## 📋 Priority Order

1. 🔴 **CRITICAL** - Fix within 24 hours
2. 🟠 **HIGH** - Fix within 1 week
3. 🟡 **MEDIUM** - Fix within 1 month

---

## 🔴 CRITICAL: Fix #1 - HMAC Cookie Signing

**Time:** 2-3 hours  
**Files:** 3 new, 2 modified

### Quick Steps

```bash
# 1. Create cookie signer
touch functions/smart_railway_app_function/core/cookie_signer.py

# 2. Copy code from SECURITY_IMPLEMENTATION_PLAN.md (Plan #1, Step 1.1)

# 3. Update session service
# Modify: services/session_service.py
# Add: from core.cookie_signer import sign_cookie, unsign_cookie

# 4. Update routes
# Modify: routes/session_auth.py
# Return signed_session_id instead of session_id

# 5. Test
pytest tests/test_cookie_signing.py -v

# 6. Deploy
catalyst deploy
```

### Verification

```bash
# Login and check cookie format
curl -c cookies.txt -X POST .../session/login -d '{...}'
cat cookies.txt | grep railway_sid
# Should contain: value.signature (with dot separator)
```

---

## 🔴 CRITICAL: Fix #2 - Input Validation

**Time:** 3-4 hours  
**Files:** 1 new, 5+ modified

### Quick Steps

```bash
# 1. Create validator
touch functions/smart_railway_app_function/core/input_validator.py

# 2. Copy code from SECURITY_IMPLEMENTATION_PLAN.md (Plan #4)

# 3. Apply to routes
# Add to session_auth.py:
from core.input_validator import validate_input

@validate_input({
    'email': {'type': 'email', 'required': True},
    'password': {'type': 'string', 'min_length': 8}
})
def session_login():
    data = request.validated_data  # Use this
    ...

# 4. Apply to all user input endpoints
# - login, register, change-password
# - bookings, search, filters

# 5. Test
pytest tests/test_input_validation.py -v
```

### Verification

```bash
# Test SQL injection blocked
curl -X POST .../session/login \
  -d '{"email":"test@test.com OR 1=1--","password":"pass"}'
# Expected: 400 Bad Request
```

---

## 🔴 CRITICAL: Fix #3 - Security Headers

**Time:** 1-2 hours  
**Files:** 1 new, 1 modified

### Quick Steps

```bash
# 1. Create headers module
touch functions/smart_railway_app_function/core/security_headers.py

# 2. Copy code from SECURITY_IMPLEMENTATION_PLAN.md (Plan #2)

# 3. Add to main.py
from core.security_headers import create_security_headers
create_security_headers(app)

# 4. Test
curl -I http://localhost:3000/.../health | grep -i "x-frame"

# 5. Deploy
catalyst deploy
```

### Verification

```bash
# Check all headers present
curl -I https://your-domain.com | grep -E "X-Frame|CSP|X-Content"
# Should show: X-Frame-Options, Content-Security-Policy, etc.

# Check browser console for CSP violations
# Open DevTools → Console (should be clean)
```

---

## 🔴 CRITICAL: Fix #4 - CORS Hardening

**Time:** 1 hour  
**Files:** 1 new, 2 modified

### Quick Steps

```bash
# 1. Create CORS module
touch functions/smart_railway_app_function/core/cors_config.py

# 2. Replace CORS code in main.py
# Remove old @app.after_request CORS handler
# Add: from core.cors_config import create_cors_middleware

# 3. Update .env
CORS_ALLOWED_ORIGINS=https://your-domain.com,http://localhost:3000

# 4. Test
curl -H "Origin: http://evil.com" http://localhost:3000/.../health
# Expected: NO Access-Control-Allow-Origin header

# 5. Deploy
```

### Verification

```bash
# Test allowed origin
curl -v -H "Origin: http://localhost:3000" \
  http://localhost:3000/.../health
# Expected: Access-Control-Allow-Origin: http://localhost:3000

# Test blocked origin
curl -v -H "Origin: http://evil.com" \
  http://localhost:3000/.../health
# Expected: NO Access-Control-Allow-Origin header
```

---

## 🟠 HIGH: Fix #5 - Rate Limiting

**Time:** 2-3 hours  
**Files:** 1 new, 1 modified

### Quick Steps

```bash
# 1. Create rate limiter
touch functions/smart_railway_app_function/core/rate_limiter.py

# 2. Apply to auth routes
from core.rate_limiter import rate_limit_by_email

@rate_limit_by_email(max_requests=5, window_seconds=900)
def session_login():
    ...

# 3. Test
# Make 6 login attempts rapidly
# 6th should return 429 Too Many Requests
```

### Rate Limit Recommendations

| Endpoint | Limit | Window | Key |
|----------|-------|--------|-----|
| Login | 5 | 15 min | email |
| Register | 3 | 1 hour | IP |
| OTP Verify | 3 | 10 min | email |
| Password Reset | 3 | 1 hour | email |
| Password Change | 5 | 1 hour | user_id |

---

## 🟠 HIGH: Fix #6 - Debug Endpoints

**Time:** 30 minutes  
**Files:** 1 modified

### Quick Steps

```bash
# In main.py, wrap debug endpoints:
if os.getenv('APP_ENVIRONMENT') == 'development':
    @app.route('/debug/...')
    def debug_endpoint():
        ...
else:
    @app.route('/debug/<path:path>')
    def debug_not_available(path):
        return jsonify({'status': 'error', 'message': 'Not found'}), 404
```

### Verification

```bash
# Test in production
APP_ENVIRONMENT=production catalyst serve
curl http://localhost:3000/.../debug/config
# Expected: 404 Not Found
```

---

## 🟠 HIGH: Fix #7 - HTTPS Enforcement

**Time:** 30-60 minutes  
**Files:** 1 new, 2 modified

### Quick Steps

```bash
# 1. Create HTTPS enforcer
touch functions/smart_railway_app_function/core/https_enforcer.py

# 2. Add to main.py
from core.https_enforcer import create_https_enforcer
create_https_enforcer(app)

# 3. Update config.py
SESSION_COOKIE_SECURE = os.getenv('APP_ENVIRONMENT') == 'production'

# 4. Set environment
APP_ENVIRONMENT=production

# 5. Test
curl -I http://your-domain.com
# Expected: 301 redirect to https://
```

---

## 🧪 Testing Checklist

### After Each Fix

- [ ] Unit tests pass
- [ ] Manual testing confirms fix works
- [ ] No regressions in existing features
- [ ] Deploy to staging
- [ ] Test in staging environment
- [ ] Deploy to production
- [ ] Verify in production

### Full Security Test Suite

```bash
# Run all tests
cd functions/smart_railway_app_function
pytest tests/ -v

# Security scan
pip install bandit safety
bandit -r . -ll
safety check

# Check for secrets
pip install detect-secrets
detect-secrets scan .

# Manual tests
./run_security_tests.sh  # (create this script)
```

---

## 📝 Implementation Order

### Day 1-2: Cookie Signing (CRITICAL)
- [ ] Create cookie_signer.py
- [ ] Update session_service.py
- [ ] Update routes/session_auth.py
- [ ] Write tests
- [ ] Deploy

### Day 3: Input Validation (CRITICAL)
- [ ] Create input_validator.py
- [ ] Update all routes with validation
- [ ] Write tests
- [ ] Deploy

### Day 4: Security Headers (CRITICAL)
- [ ] Create security_headers.py
- [ ] Update main.py
- [ ] Test CSP compatibility
- [ ] Deploy

### Day 5: CORS + Debug (CRITICAL + HIGH)
- [ ] Create cors_config.py
- [ ] Update main.py CORS
- [ ] Wrap debug endpoints
- [ ] Deploy

### Day 6-7: Rate Limiting (HIGH)
- [ ] Create rate_limiter.py
- [ ] Apply to all auth endpoints
- [ ] Test limits
- [ ] Deploy

### Day 8: HTTPS (HIGH)
- [ ] Create https_enforcer.py
- [ ] Update main.py
- [ ] Configure SSL
- [ ] Deploy

### Day 9-10: Final Testing
- [ ] Integration testing
- [ ] Security scanning
- [ ] Penetration testing
- [ ] Documentation

---

## 🔧 Quick Commands

### Development

```bash
# Start local server
cd functions/smart_railway_app_function
catalyst serve

# Run tests
pytest tests/ -v

# Check security
bandit -r . -ll
safety check

# View logs
catalyst logs --follow
```

### Deployment

```bash
# Build frontend
cd railway-app
npm run build

# Deploy to Catalyst
catalyst deploy

# View production logs
catalyst logs --production --follow

# Rollback if needed
catalyst rollback
```

### Debugging

```bash
# Check environment
curl http://localhost:3000/.../health

# Check CORS
curl -H "Origin: http://localhost:3000" -I \
  http://localhost:3000/.../health

# Check rate limits
for i in {1..6}; do
  curl -X POST .../session/login -d '{...}'
done

# Check cookies
curl -c cookies.txt -X POST .../session/login -d '{...}'
cat cookies.txt
```

---

## 📊 Success Metrics

### Security Score Target

- [ ] **securityheaders.com**: A+ rating
- [ ] **ssllabs.com**: A rating
- [ ] **Observatory by Mozilla**: 90+ score
- [ ] **OWASP ZAP**: 0 high/medium vulnerabilities

### Performance Metrics

- [ ] Session validation: < 50ms
- [ ] Rate limit check: < 10ms
- [ ] Input validation: < 5ms
- [ ] No significant latency increase

---

## 🚨 Emergency Rollback

If a security fix causes issues:

```bash
# 1. Identify the problematic deployment
catalyst logs --production | tail -100

# 2. Rollback
catalyst rollback

# 3. Disable specific feature via environment variable
# In Catalyst Console → Environment Variables:
ENABLE_COOKIE_SIGNING=false
ENABLE_SECURITY_HEADERS=false
ENFORCE_HTTPS=false

# 4. Fix issue locally
# Test thoroughly
pytest tests/ -v

# 5. Redeploy
catalyst deploy
```

---

## 📚 Reference Documents

- **Full Analysis:** `SECURITY_ANALYSIS_REPORT.md`
- **Implementation Plans:** `SECURITY_IMPLEMENTATION_PLAN.md`
- **Extended Plans:** `SECURITY_IMPLEMENTATION_PLAN_PART2.md`
- **This Guide:** `SECURITY_QUICK_REFERENCE.md`

---

## 🎯 Quick Win: 30-Minute Security Boost

If you only have 30 minutes, do these:

1. **Add Security Headers** (10 min)
   ```python
   # main.py
   @app.after_request
   def add_security_headers(response):
       response.headers['X-Frame-Options'] = 'DENY'
       response.headers['X-Content-Type-Options'] = 'nosniff'
       response.headers['X-XSS-Protection'] = '1; mode=block'
       return response
   ```

2. **Disable Debug Endpoints in Production** (5 min)
   ```python
   # main.py
   if os.getenv('APP_ENVIRONMENT') != 'development':
       @app.route('/debug/<path:path>')
       def no_debug(path):
           return '', 404
   ```

3. **Add Rate Limiting to Login** (15 min)
   ```python
   # routes/session_auth.py
   from core.security import rate_limit
   
   @rate_limit(max_calls=5, window_seconds=900)
   def session_login():
       ...
   ```

---

## ✅ Final Checklist Before Production

- [ ] All 7 critical fixes implemented
- [ ] All tests passing
- [ ] Security scan clean
- [ ] No hardcoded secrets
- [ ] `.env` in `.gitignore`
- [ ] HTTPS enforced
- [ ] Security headers present
- [ ] CORS configured
- [ ] Rate limiting active
- [ ] Debug endpoints disabled
- [ ] Cookies signed
- [ ] Input validated
- [ ] Audit logging working
- [ ] Monitoring configured
- [ ] Documentation updated
- [ ] Team trained on security

---

**Need Help?** Refer to detailed implementation plans for step-by-step code and explanations.

**Ready to Deploy?** Follow the day-by-day schedule above.

**Questions?** Review the full security analysis report first.

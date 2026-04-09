# 📋 Deployment Checklist
## Smart Railway Ticketing System - Production Deployment

---

## Pre-Deployment

### 🔐 Security

- [ ] All security features implemented and tested
- [ ] SESSION_SECRET is strong (64+ characters, unique for production)
- [ ] CORS_ALLOWED_ORIGINS set to production domains only
- [ ] APP_ENVIRONMENT=production
- [ ] Debug endpoints disabled (returns 404)
- [ ] Security headers present and correct
- [ ] SSL/TLS certificate configured
- [ ] HTTPS redirect working

**Verify:**
```bash
# Check security headers
curl -I https://your-domain.com/server/.../health

# Test HTTPS redirect
curl -I http://your-domain.com
# Expected: 301 → https://

# Test debug disabled
curl https://your-domain.com/.../debug/config
# Expected: 404 Not Found
```

### 🧪 Testing

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual testing completed
- [ ] Security scan passed (no high/critical issues)
- [ ] Load testing completed
- [ ] Browser compatibility tested

**Run tests:**
```bash
cd functions\smart_railway_app_function
pytest tests\ -v
bandit -r . -ll
safety check
```

### ⚙️ Configuration

- [ ] Environment variables set in Catalyst Console
- [ ] Database connection tested
- [ ] Email service configured (OTP sender verified)
- [ ] Logging configured
- [ ] Monitoring configured

**Production Environment Variables:**
```bash
APP_ENVIRONMENT=production
SESSION_SECRET=<strong-64-char-secret>
CORS_ALLOWED_ORIGINS=https://your-domain.com
SESSION_TIMEOUT_HOURS=4
SESSION_IDLE_TIMEOUT_HOURS=1
CATALYST_FROM_EMAIL=<verified-email>
```

### 📦 Build

- [ ] Frontend build successful (`npm run build`)
- [ ] No build errors or warnings
- [ ] Build size acceptable
- [ ] Source maps disabled in production

**Build:**
```bash
cd railway-app
npm run build
# Check build\
```

---

## Deployment

### 1️⃣ Set Production Environment Variables

**In Catalyst Console → Environment Variables:**

```bash
APP_ENVIRONMENT=production
SESSION_SECRET=<new-strong-secret>
CORS_ALLOWED_ORIGINS=https://your-actual-domain.com
```

### 2️⃣ Deploy to Catalyst

```bash
catalyst deploy
```

### 3️⃣ Verify Deployment

```bash
# Check deployment status
catalyst logs --production --tail 50

# Test endpoints
curl -I https://your-domain.com/server/.../health
# Expected: 200 OK with security headers
```

---

## Post-Deployment

### ✅ Verification

- [ ] Homepage loads correctly
- [ ] Login works
- [ ] Sessions persist on refresh
- [ ] Security headers present
- [ ] HTTPS working
- [ ] Cookies have Secure flag
- [ ] Debug endpoints return 404
- [ ] Audit logging working

**Test Login Flow:**
```bash
curl -c cookies.txt -X POST https://your-domain.com/.../session/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"password\"}"

# Check cookie
type cookies.txt
# Should have: Secure; HttpOnly; SameSite=Strict
```

### 📊 Monitoring

- [ ] Set up log monitoring
- [ ] Configure alerts for errors
- [ ] Monitor security events
- [ ] Track session metrics

**Key Metrics to Monitor:**
- Login success/failure rate
- Session creation rate
- Cookie tampering attempts
- CORS violations
- API response times

### 🔍 Security Verification

**Test Security Headers:**
Visit: https://securityheaders.com  
Enter: your-domain.com  
Target: A+ rating

**Test SSL/TLS:**
Visit: https://www.ssllabs.com/ssltest/  
Enter: your-domain.com  
Target: A rating

**Manual Security Checks:**
```bash
# 1. Check security headers
curl -I https://your-domain.com/.../health | findstr /I "X-Frame CSP HSTS"

# 2. Test CORS blocking
curl -H "Origin: http://evil.com" https://your-domain.com/.../health
# Should NOT have Access-Control-Allow-Origin

# 3. Test debug disabled
curl https://your-domain.com/.../debug/config
# Should return 404

# 4. Test HTTPS redirect
curl -I http://your-domain.com
# Should return 301 to https://

# 5. Test cookie signing
# Login, tamper with cookie, try to use it
# Should return 401 Unauthorized
```

---

## Rollback Plan

### If Issues Occur

1. **Immediate Rollback:**
   ```bash
   catalyst rollback
   ```

2. **Disable Specific Feature:**
   ```bash
   # In Catalyst Console, set:
   APP_ENVIRONMENT=development
   ```

3. **Check Logs:**
   ```bash
   catalyst logs --production --tail 100
   ```

4. **Fix Locally:**
   - Identify issue from logs
   - Fix in development
   - Test thoroughly
   - Redeploy

---

## Post-Deployment Tasks

### Day 1

- [ ] Monitor logs continuously
- [ ] Check error rates
- [ ] Verify all features working
- [ ] Watch for security alerts

### Week 1

- [ ] Review audit logs
- [ ] Check session metrics
- [ ] Monitor performance
- [ ] Gather user feedback

### Month 1

- [ ] Security audit
- [ ] Performance review
- [ ] Update documentation
- [ ] Plan improvements

---

## Maintenance Schedule

### Daily
- Monitor logs for errors
- Check security alerts

### Weekly
- Review audit logs
- Check dependency updates
- Monitor session statistics

### Monthly
- Rotate SESSION_SECRET
- Review security headers
- Update dependencies
- Check SSL certificate

### Quarterly
- Full security audit
- Penetration testing
- Performance optimization
- Documentation review

---

## Emergency Contacts

**For Security Issues:**
1. Check security logs
2. Review audit trail
3. Contact security team

**For System Issues:**
1. Check Catalyst logs
2. Review error messages
3. Contact DevOps team

---

## Sign-Off

### Deployment Approval

- [ ] **Developer:** Code reviewed and tested
- [ ] **DevOps:** Infrastructure ready
- [ ] **Security:** Security review passed
- [ ] **QA:** All tests passing
- [ ] **Project Lead:** Deployment approved

**Deployment Date:** ___________  
**Deployed By:** ___________  
**Approved By:** ___________

---

## Success Criteria

✅ **Deployment Successful When:**

1. All endpoints responding correctly
2. Security headers present (A+ rating)
3. SSL/TLS configured (A rating)
4. Sessions working correctly
5. No critical errors in logs
6. Performance within acceptable range
7. All tests passing

---

**Checklist Version:** 2.0  
**Last Updated:** April 2, 2026  
**Status:** Production Ready

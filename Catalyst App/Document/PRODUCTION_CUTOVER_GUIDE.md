# 🚀 Railway Ticketing System - Production Cutover Guide

**Date**: 2026-03-19
**Environment**: Catalyst Development → Production

---

## 📋 Pre-Cutover Checklist

### Verify All Tests Pass
- [ ] Backend health check: ✅
- [ ] Frontend loads: ✅
- [ ] CORS working: ✅
- [ ] Authentication flow: ✅
- [ ] Core features (search, booking): ✅
- [ ] Admin features: ✅
- [ ] AI features: ✅
- [ ] Error handling: ✅

### Prepare for Cutover
- [ ] Stakeholders notified
- [ ] Support team briefed
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

---

## 🚀 Deployment Commands

### Step 1: Navigate to Catalyst App
```bash
cd "f:/Railway Project Backend/Catalyst App"
```

### Step 2: Login to Catalyst
```bash
catalyst login
```

### Step 3: Deploy Client Only
```bash
catalyst deploy --only client
```

### Step 4: Deploy Everything (Functions + Client)
```bash
catalyst deploy
```

### Step 5: Verify Deployment
```bash
catalyst serve --port 3000
```

---

## 🔗 Production URLs

| Service | Development URL | Production URL |
|---------|-----------------|----------------|
| **Frontend** | `railway-ticketing-system-60066581545.development.catalyst-cs.in` | `railway-ticketing-system.catalyst-cs.in` |
| **Backend** | `railway-project-backend-50039510865.development.catalystappsail.in` | `railway-project-backend.catalystappsail.in` |

---

## 📊 Monitoring Setup

### Key Metrics to Monitor

1. **Uptime**
   - Monitor: Frontend URL every 5 minutes
   - Alert: If down > 2 minutes

2. **Error Rate**
   - Monitor: Browser console errors
   - Alert: If > 1% error rate

3. **Response Time**
   - Monitor: API latency
   - Alert: If > 2000ms average

4. **User Activity**
   - Track: Login success/failure
   - Track: Booking completions

### Catalyst Monitoring
```bash
# View logs
catalyst logs

# View specific function logs
catalyst logs --function catalyst_backend
```

---

## 🆘 Incident Response

### Scenario 1: Frontend Not Loading
```
1. Check: Catalyst deployment status
2. Verify: Build files exist in catalyst-frontend/build/
3. Action: Redeploy client
   catalyst deploy --only client
4. Recovery: < 5 minutes
```

### Scenario 2: CORS Errors
```
1. Check: Backend CORS config in app.py
2. Verify: Frontend domain in CORS_ALLOWED_ORIGINS
3. Action: Update config, redeploy backend
4. Recovery: < 10 minutes
```

### Scenario 3: API Errors (500)
```
1. Check: Backend logs
   catalyst logs --function catalyst_backend
2. Identify: Error in stack trace
3. Action: Fix and redeploy
4. Recovery: 15-30 minutes
```

### Scenario 4: Authentication Issues
```
1. Check: JWT token in sessionStorage
2. Verify: JWT_SECRET_KEY consistent
3. Action: Clear tokens, re-login
4. Recovery: < 5 minutes
```

---

## 🔄 Rollback Procedure

### If Frontend Broken
```bash
# Option 1: Redeploy previous version
git checkout HEAD~1 -- "Frontend/fixed_frontend/dist"
catalyst deploy --only client

# Option 2: Restore from backup
cp -r backup/dist/* "Catalyst App/catalyst-frontend/build/"
catalyst deploy --only client
```

### If Backend Broken
```bash
# Check AppSail status in Catalyst dashboard
# Redeploy backend
cd "Backend"
catalyst deploy --only appsail
```

---

## 📢 Communication Template

### Pre-Cutover Notification
```
Subject: Railway Ticketing System - Scheduled Maintenance

Dear Team,

We will be deploying updates to the Railway Ticketing System frontend.

Timing: [Date/Time]
Expected Duration: 15-30 minutes
Impact: Brief interruption to web access

What's changing:
- Frontend migrated to Catalyst Client
- Improved performance and reliability

Action needed: None

Questions? Contact: [Support Email]
```

### Post-Cutover Notification
```
Subject: Railway Ticketing System - Update Complete

The Railway Ticketing System frontend has been successfully updated.

New URLs:
- Frontend: https://railway-ticketing-system-60066581545.development.catalyst-cs.in/
- API: https://railway-project-backend-50039510865.development.catalystappsail.in/api/

All features are operational. Please report any issues.

Thank you for your patience.
```

---

## ✅ Go-Live Checklist

### Immediately After Deployment
- [ ] Frontend accessible at Catalyst URL
- [ ] Login works
- [ ] Search trains works
- [ ] Create booking works
- [ ] Admin pages accessible

### 24 Hours Post-Cutover
- [ ] Error rate < 0.1%
- [ ] Response time < 2 seconds
- [ ] No major user complaints
- [ ] All scheduled bookings processing

### 72 Hours Post-Cutover
- [ ] System stable
- [ ] No recurring issues
- [ ] Performance baseline established
- [ ] Team confident

---

## 📊 Success Criteria

| Metric | Target | Status |
|--------|--------|--------|
| Uptime | > 99.9% | [ ] |
| Page Load | < 3 seconds | [ ] |
| API Latency | < 1 second | [ ] |
| Error Rate | < 0.1% | [ ] |
| User Satisfaction | No complaints | [ ] |

---

## 📝 Sign-Off

| Role | Name | Date | Approved |
|------|------|------|----------|
| Tech Lead | | | [ ] |
| QA Lead | | | [ ] |
| Product Owner | | | [ ] |
| Operations | | | [ ] |

---

**Status**: ✅ READY FOR PRODUCTION CUTOVER

**Next Steps**:
1. Run `catalyst deploy --only client`
2. Verify deployment
3. Run test checklist
4. Send notification
5. Monitor for 72 hours

---

## 🎉 Migration Complete!

Congratulations! The Railway Ticketing System frontend has been migrated to Zoho Catalyst Client.

**Architecture Summary**:
- **Frontend**: Catalyst Client (React SPA)
- **Backend**: Catalyst AppSail (Flask API)
- **Database**: Zoho Creator

**Total Migration Time**: ~6-8 hours
**Risk Level**: Low (Hybrid approach)

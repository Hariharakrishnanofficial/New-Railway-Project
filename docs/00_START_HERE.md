# 🚀 Quick Start Guide
## Smart Railway Ticketing System

**Welcome!** This guide will get you up and running in 15 minutes.

⚠️ **IMPORTANT**: Before running the application, complete the database migration for Sessions table.  
See: `docs/CRITICAL_DATABASE_MIGRATION_REQUIRED.md`

---

## What You Need

- ✅ Python 3.8+
- ✅ Node.js 14+
- ✅ Zoho Catalyst CLI
- ✅ Git
- ⚠️ **CloudScale Console Access** (for database migration)

---

## Pre-Flight Check (Required)

### ⚠️ Database Migration (One-Time Setup)

**Before running catalyst serve for employee/admin features:**

1. Open https://console.catalyst.zoho.com
2. Navigate to **DataStore → Tables → Sessions**
3. Check if **User_ID** column has a Foreign Key constraint to Users table
4. If yes: **Remove the FK constraint** and save
5. Why: Employee sessions need to reference Employees table, not Users table

**Detailed Instructions**: See `docs/CRITICAL_DATABASE_MIGRATION_REQUIRED.md`

**Skip this if**: You're only testing passenger (user) login, not employee/admin login.

---

## Quick Setup (5 Steps)

### 1️⃣ Clone & Install

```bash
# Navigate to project
cd "F:\New Railway Project"

# Install backend dependencies
cd functions\smart_railway_app_function
pip install -r requirements.txt

# Install frontend dependencies
cd ..\..\railway-app
npm install
```

### 2️⃣ Configure Environment

```bash
# Copy example environment file
cd ..\functions\smart_railway_app_function
copy .env.example .env

# Edit .env with your values
notepad .env
```

**Required Variables:**
```bash
APP_ENVIRONMENT=development
SESSION_SECRET=<generate-with-command-below>
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**Generate Session Secret:**
```bash
python -c "import secrets; print(secrets.token_hex(64))"
```

### 3️⃣ Start Development Server

```bash
# Start backend
catalyst serve

# In new terminal, start frontend
cd railway-app
npm start
```

### 4️⃣ Verify It Works

Open browser: http://localhost:3000

You should see the Smart Railway Ticketing System homepage.

### 5️⃣ Test Security Features

```bash
# Check security headers
curl -I http://localhost:3000/server/smart_railway_app_function/health

# Expected: X-Frame-Options, Content-Security-Policy, etc.
```

---

## 🔒 Security Features (Already Implemented!)

Your application now has:

✅ **HMAC Cookie Signing** - Sessions can't be tampered with  
✅ **Security Headers** - XSS and clickjacking protection  
✅ **CORS Hardening** - Only whitelisted domains allowed  
✅ **HTTPS Enforcement** - Auto-redirect in production  
✅ **Debug Protection** - Debug endpoints only in development  

**Security Score:** HIGH ✅

---

## 📖 Next Steps

### Learn More

- **Full Documentation:** [README.md](README.md)
- **Database Schema:** [architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md](architecture/CLOUDSCALE_DATABASE_SCHEMA_V2.md)
- **User/Employee Architecture:** [architecture/USER_EMPLOYEE_RESTRUCTURE_PLAN.md](architecture/USER_EMPLOYEE_RESTRUCTURE_PLAN.md)
- **Security Guide:** [security/SECURITY_IMPLEMENTATION_SUMMARY.md](security/SECURITY_IMPLEMENTATION_SUMMARY.md)
- **Setup Reference:** [setup/COMPLETE_SETUP_REFERENCE.md](setup/COMPLETE_SETUP_REFERENCE.md)

### Test Authentication

**Passenger Login** (uses Users table):
```bash
# Register passenger
POST /session/register
{
  "email": "passenger@railway.com",
  "password": "Pass@123",
  "fullName": "John Passenger"
}

# Login
POST /session/login
{
  "email": "passenger@railway.com",
  "password": "Pass@123"
}
```

**Employee/Admin Login** (uses Employees table):
```bash
# Create employee (admin only)
POST /data-seed/admin-employee
{
  "email": "admin@railway.com",
  "password": "Admin@123",
  "full_name": "System Admin",
  "department": "IT",
  "designation": "System Administrator"
}

# Login
POST /session/employee/login
{
  "email": "admin@railway.com",
  "password": "Admin@123"
}
```

### Deploy to Production

1. Read [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
2. Configure production environment variables
3. Run: `catalyst deploy`

### Common Tasks

```bash
# Run tests
cd functions\smart_railway_app_function
pytest tests\ -v

# Build frontend
cd railway-app
npm run build

# View logs
catalyst logs --follow

# Deploy
catalyst deploy
```

---

## 🆘 Troubleshooting

### Employee/Admin login shows 500 error

**Symptom**: `POST /session/employee/login` returns 500 Internal Server Error

**Cause**: Sessions table has FK constraint on User_ID → Users.ROWID

**Fix**: Remove FK constraint in CloudScale console

**See**: [CRITICAL_DATABASE_MIGRATION_REQUIRED.md](CRITICAL_DATABASE_MIGRATION_REQUIRED.md)

### Server won't start

**Check:**
- Is Catalyst CLI installed? `catalyst --version`
- Are dependencies installed? `pip install -r requirements.txt`
- Is .env file configured?

### Sessions not persisting

**Check:**
- CORS_ALLOWED_ORIGINS includes your frontend URL
- Cookies enabled in browser
- SESSION_SECRET is set (32+ characters)

### TLS Certificate Error

**Symptom**: "Could not find a suitable TLS CA certificate bundle"

**Fix**:
```bash
catalyst login
# Then restart server
catalyst serve
```

### Security errors

**Check:**
- Logger error fixed? (Should be fixed in latest version)
- Environment variables set correctly?
- See: [security/QUICK_FIX_LOGGER_ERROR.md](security/QUICK_FIX_LOGGER_ERROR.md)

---

## 📚 Key Documentation

| Topic | Document | Time |
|-------|----------|------|
| **Quick Start** | This file | 5 min |
| **Security Overview** | [Security Summary](security/SECURITY_IMPLEMENTATION_SUMMARY.md) | 10 min |
| **Full Setup** | [Complete Setup](setup/COMPLETE_SETUP_REFERENCE.md) | 30 min |
| **Architecture** | [Session Architecture](architecture/SESSION_ARCHITECTURE_GUIDE.md) | 15 min |

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Server starts without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] Login works
- [ ] Sessions persist on refresh
- [ ] Security headers present (curl test)
- [ ] Debug endpoints return 404 in production

---

## 🎯 You're Ready!

Your Smart Railway Ticketing System is configured with:
- ✅ Secure session management
- ✅ Production-ready security
- ✅ Clean documentation structure

**Happy Coding!** 🚀

---

**Questions?** Check [README.md](README.md) for complete documentation.

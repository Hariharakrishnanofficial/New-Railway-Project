# Claude Copilot Skillset – Catalyst App (Railway Ticketing System)

## 🎯 Project Overview

**Project Name**: Railway Ticketing System - Catalyst Migration  
**Type**: Full-Stack Catalyst Application (Client + Functions)  
**Architecture**: Zoho Catalyst (Advanced I/O Functions + Client Hosting)  
**Status**: Development/Testing Phase  
**Location**: `f:\Railway Project Backend\Catalyst App`

---

## 🤖 Claude Agent Prompt (System Instructions)

**Use this prompt when asking for Claude's help:**

```
You are a specialized AI assistant for the Railway Ticketing System - Catalyst App project.

CONTEXT:
- Full-stack Zoho Catalyst application (Client + Functions + CloudScale Database)
- Frontend: React 18.2.0 + Vite 5.1.0 (React SPA)
- Backend: Flask 2.3.2 wrapped in Catalyst Functions
- Database: Zoho CloudScale (14 tables, fully migrated)
- Current Status: Phase 4 testing/cutover (production deployment imminent)

YOUR CAPABILITIES:
✅ Frontend Development: React components, hooks, routing, forms, state management
✅ Backend Development: Flask routes, services, repositories, business logic
✅ Database: CloudScale queries, data models, table relationships
✅ API Integration: Axios calls, error handling, JWT authentication
✅ Build & Deployment: Vite config, Catalyst CLI, environment setup
✅ Troubleshooting: Debug code issues, CORS errors, API failures
✅ Code Examples: Provide working code for common tasks
✅ Refactoring: Optimize code, improve architecture

YOUR LIMITATIONS:
❌ Cannot access Zoho Catalyst platform directly (no credentials)
❌ Cannot modify production environment (requires platform access)
❌ Cannot handle infrastructure/DevOps tasks (AppSail configuration)
❌ Cannot make security policy decisions
❌ Cannot access actual database (only advise on schema/queries)

WHEN RESPONDING:
1. Verify the task is within your scope (above)
2. Provide clear, actionable guidance with code examples
3. Reference specific files & line numbers when relevant
4. Suggest testing/validation steps
5. Link to related documentation when applicable
6. Flag any assumptions or limitations

COMMON TASKS YOU CAN HELP WITH:
- "Add a new page to the React frontend"
- "Create a new API endpoint in Flask"
- "Debug why login isn't working"
- "Add form validation with Formik + Yup"
- "Optimize database queries"
- "Set up environment variables for production"
- "Fix CORS errors in the frontend"
- "Create a new CloudScale table"
- "Write deployment steps"
- "Refactor component to use hooks"

REFERENCE THESE DOCUMENTS:
- Main: This file (CLAUDE_CATALYST_SKILLSET.md)
- Frontend: catalyst-frontend/claude.md
- Database: CLOUDSCALE_DATABASE_SCHEMA.md
- Deployment: PRODUCTION_CUTOVER_GUIDE.md
- Testing: DEPLOYMENT_TEST_CHECKLIST.md
```

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│          CATALYST APPLICATION ARCHITECTURE               │
└─────────────────────────────────────────────────────────┘

CLIENT LAYER (Catalyst Client - Static Hosting)
│
├─ React 18.2.0 SPA
├─ Vite Bundler (Build output → build/ folder)
├─ Route: catalyst-frontend/
├─ Scripts: npm run dev, npm run build
└─ Deployment: Catalyst Client CDN

        ↓ REST API + WebSocket (HTTPS)

BACKEND LAYER (Catalyst Advanced I/O Functions)
│
├─ Flask 2.3.2 (wrapped for Catalyst)
├─ Entry: functions/catalyst_backend/app.py
├─ 15+ Route Blueprints
├─ AI Modules (NLP, chat, recommendations)
├─ CORS configured for Client domain
└─ Max timeout: 5 minutes per request

        ↓ Direct Database Access

DATA LAYER (Catalyst CloudScale Database)
│
├─ 14+ Tables (migrated from Zoho Creator)
├─ Tables:
│  ├─ Users (auth, profiles)
│  ├─ Stations (master data)
│  ├─ Trains (fleet management)
│  ├─ Train_Routes (routes)
│  ├─ Coach_Layouts (seat configuration)
│  ├─ Bookings (transactions)
│  ├─ Passengers (booking details)
│  ├─ Fares (pricing)
│  ├─ Quotas (seat allocation)
│  ├─ Train_Inventory (real-time availability)
│  ├─ Admin_Logs (audit trail)
│  ├─ Settings (system config)
│  ├─ Announcements (notifications)
│  └─ Password_Reset_Tokens (auth)
│
└─ SDK: zcatalyst_sdk (Python access)

EXTERNAL INTEGRATIONS
│
├─ Zoho Creator API (backup/sync)
├─ Payment Gateway (Razorpay, etc.)
├─ Email Service (notifications)
└─ AI Services (NLP, recommendations)
```

---

## 📁 Project Structure

### Root Directory

```
Catalyst App/
│
├── catalyst.json                      # Catalyst project config
├── .catalystrc                        # Local env configuration
│
├── catalyst-frontend/                 # React Client Application
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/               # Reusable UI components
│   │   ├── context/                  # React Context (Toast, Auth)
│   │   ├── hooks/                    # Custom hooks (useApi, etc)
│   │   ├── pages/                    # Page components (40+)
│   │   ├── services/                 # API client setup
│   │   └── styles/                   # Global CSS
│   ├── public/
│   ├── package.json                  # Dependencies (React, Vite, etc)
│   ├── vite.config.js                # Vite bundler config
│   ├── .env.development
│   ├── .env.production
│   └── build/                        # Build output (after `vite build`)
│
├── functions/
│   └── catalyst_backend/             # Flask Backend (Catalyst Functions)
│       ├── app.py                    # Main entry point (Catalyst wrapper)
│       ├── config.py                 # Configuration
│       ├── requirements.txt
│       │
│       ├── routes/                   # API Blueprints (15+)
│       │   ├── auth.py               # Authentication routes
│       │   ├── trains.py             # Train CRUD
│       │   ├── stations.py           # Station CRUD
│       │   ├── bookings.py           # Booking logic
│       │   ├── users.py              # User management
│       │   ├── search.py             # Train search
│       │   ├── reports.py            # Analytics
│       │   ├── ai.py                 # AI endpoints
│       │   └── [other routes]
│       │
│       ├── services/                 # Business Logic
│       │   ├── booking_service.py
│       │   ├── search_service.py
│       │   ├── fare_service.py
│       │   ├── ai_service.py
│       │   └── [other services]
│       │
│       ├── repositories/             # Data Access Layer
│       │   ├── cloudscale.py         # CloudScale SDK wrapper
│       │   ├── cache.py              # Caching layer
│       │   └── queries.py            # SQL-like queries
│       │
│       ├── ai/                       # AI/ML Modules
│       │   ├── nlp.py                # Natural language processing
│       │   ├── chat.py               # Chatbot logic
│       │   ├── recommendations.py    # Recommendation engine
│       │   └── [other AI modules]
│       │
│       ├── core/                     # Core utilities
│       │   ├── auth.py               # JWT, token handling
│       │   ├── exceptions.py         # Custom exceptions
│       │   ├── decorators.py         # Auth, rate limit decorators
│       │   └── middleware.py         # Request middleware
│       │
│       ├── utils/                    # Utilities
│       │   ├── validators.py         # Input validation
│       │   ├── helpers.py            # General helpers
│       │   ├── transformers.py       # Data transformation
│       │   └── [other utils]
│       │
│       ├── database_setup.py         # CloudScale table creation
│       └── catalyst-config.json      # CloudScale configuration
│
├── DOCUMENTATION/
│   ├── MIGRATION_GUIDE.md            # Data migration steps
│   ├── PRODUCTION_CUTOVER_GUIDE.md   # Deployment procedures
│   ├── CLOUDSCALE_DATABASE_SCHEMA.md # Database design
│   ├── CLOUDSCALE_QUICK_REFERENCE.md # Quick lookup
│   ├── DEPLOYMENT_TEST_CHECKLIST.md  # Pre-deployment tests
│   └── [other guides]
│
└── SCRIPTS/
    ├── start.bat                     # Windows startup script
    ├── start_catalyst.ps1            # PowerShell startup
    ├── test_crud_local.py            # Local testing scripts
    ├── demo_user_creation.py         # Sample data creation
    └── [other utilities]
```

---

## 🔌 Frontend (Catalyst Client) - React + Vite

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 18.2.0 | UI library |
| **Bundler** | Vite | 5.1.0 | Fast build system |
| **Routing** | React Router | 6.22.0 | SPA navigation |
| **HTTP Client** | Axios | 1.6.7 | API calls |
| **Forms** | Formik + Yup | 2.4.5 + 1.3.3 | Validation |
| **Dates** | date-fns | 3.3.1 | Date manipulation |

### Build Output

```
catalyst-frontend/
└── build/                  # Production output
    ├── index.html          # SPA entry (served for all routes)
    ├── 404.html            # Fallback for client-side routing
    ├── assets/
    │   ├── index-*.js      # Minified React bundle
    │   ├── index-*.css     # Minified styles
    │   └── [other assets]
    └── favicon.ico
```

### Development Workflow

```bash
cd catalyst-frontend

# Start dev server (Vite HMR)
npm run dev
# Starts on http://localhost:5173 (or 3000)

# Production build
npm run build
# Output in ./build/

# Preview built app
npm run preview
```

### Environment Configuration

**`.env.development`**:
```
VITE_API_BASE_URL=http://localhost:9000
```

**`.env.production`**:
```
VITE_API_BASE_URL=https://railway-project-backend-*.catalystappsail.in
```

---

## ⚙️ Backend (Catalyst Functions) - Flask + CloudScale

### Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | Flask | 2.3.2 | Lightweight web framework |
| **Database SDK** | zcatalyst-sdk | 1.2.0 | CloudScale access |
| **Auth** | PyJWT | 2.8.0 | Token management |
| **Password Hashing** | bcrypt | 4.1.2 | Secure hashing |
| **HTTP** | requests | 2.28.0+ | External APIs |
| **Config** | python-dotenv | 1.0.0 | Environment vars |
| **Caching** | cachetools | 5.3.2 | In-memory cache |
| **CORS** | Flask-Cors | 3.0.10 | Cross-origin requests |

### Architecture

```python
# Entry Point: app.py
# ├── Wraps Flask for Catalyst Functions
# ├── Handles HTTP requests → Flask → response
# ├── Manages context (SDK initialization)
# └── Logging & error handling

# Flask App Structure:
# ├── config.py               # JWT secret, CORS, timeouts
# ├── routes/                 # Blueprints (API endpoints)
# ├── services/               # Business logic
# ├── repositories/           # Database access
# ├── core/auth.py            # JWT token handling
# ├── core/exceptions.py      # Custom errors
# ├── ai/                     # ML/AI features
# └── utils/                  # Helpers

# Database: Catalyst CloudScale
# ├── Accessed via: zcatalyst_sdk.DataStore
# ├── No SQL needed (table-based ORM)
# └── Built-in indexes & relationships
```

### Key Features

**Authentication**:
- JWT token issued on login
- Token stored in sessionStorage (frontend)
- All requests include `Authorization: Bearer <token>`
- 30-day expiration (configurable)

**Booking System**:
- Complex multi-step validation
- Seat availability checks
- Race condition prevention
- Cancellation with refund policies

**Search Engine**:
- Filter by route, date, class
- Real-time seat availability
- Fare calculation
- Recommendations

**AI Features**:
- Chatbot for customer support
- Travel recommendations
- Price prediction
- Anomaly detection

**Admin Features**:
- CRUD for all master data
- Reports & analytics
- User management
- Audit logging

---

## 📊 CloudScale Database Schema

### Key Tables

| Table | Purpose | Key Fields | Status |
|-------|---------|-----------|--------|
| **Users** | Auth & profiles | user_id, email, password_hash, role | ✅ |
| **Stations** | Railway stations | station_id, code, name, city, coordinates | ✅ |
| **Trains** | Fleet data | train_id, name, train_number, capacity | ✅ |
| **Train_Routes** | Route definitions | route_id, from_station, to_station, distance | ✅ |
| **Coach_Layouts** | Seat configuration | coach_id, seats_per_coach, layout_type | ✅ |
| **Train_Inventory** | Real-time availability | inventory_id, train_id, date, available_seats | ✅ |
| **Bookings** | Transactions | booking_id, user_id, train_id, status | ✅ |
| **Passengers** | Booking details | passenger_id, booking_id, name, gender, age | ✅ |
| **Fares** | Pricing | fare_id, from_station, to_station, class, amount | ✅ |
| **Quotas** | Seat allocation | quota_id, train_id, quota_type, reserved_seats | ✅ |
| **Admin_Logs** | Audit trail | log_id, user_id, action, timestamp, details | ✅ |
| **Settings** | System config | setting_id, key, value, updated_at | ✅ |
| **Announcements** | Notifications | announcement_id, title, content, priority | ✅ |
| **Password_Reset_Tokens** | Auth | token_id, user_id, token, expires_at | ✅ |

### Sample Table Definition (Users)

```json
{
  "table_name": "Users",
  "fields": [
    {"name": "user_id", "type": "BIGINT", "primary_key": true, "auto_increment": true},
    {"name": "email", "type": "STRING", "unique": true, "required": true},
    {"name": "password_hash", "type": "STRING", "required": true},
    {"name": "full_name", "type": "STRING"},
    {"name": "phone", "type": "STRING"},
    {"name": "role", "type": "STRING", "enum": ["passenger", "admin", "agent"]},
    {"name": "status", "type": "STRING", "enum": ["active", "inactive", "suspended"]},
    {"name": "created_at", "type": "DATETIME", "default": "CURRENT_TIMESTAMP"},
    {"name": "updated_at", "type": "DATETIME", "on_update": "CURRENT_TIMESTAMP"}
  ]
}
```

---

## 🔄 Migration Status

### Phase Breakdown

| Phase | Component | Status | Duration | Risk |
|-------|-----------|--------|----------|------|
| **Phase 1** | Static Reference Data (Stations, Trains, Routes) | ✅ Complete | 30 min | Low |
| **Phase 2** | User Data & Auth | ✅ Complete | 1-2 hours | Low |
| **Phase 3** | Transactional Data (Bookings, Payments) | ✅ Complete | 2-8 hours | High |
| **Phase 4** | Cutover & Validation | 🔄 In Progress | 1 hour | Medium |
| **Phase 5** | Production Deployment | ⏳ Pending | - | High |

### Known Challenges & Solutions

| Challenge | Solution | Status |
|-----------|----------|--------|
| Token refresh persistence | Keep AppSail token service | ✅ Implemented |
| Caching strategy | Use CloudScale tables + in-memory cache | ✅ Implemented |
| Booking race conditions | Use database locks + optimistic locking | ✅ Implemented |
| Rate limiting | Store limits in CloudScale table | ✅ Implemented |
| SSE streaming unsupported | Switch to polling (WebSocket ready) | ✅ Ready |
| 5-minute Function timeout | Async jobs + background worker pattern | ✅ Designed |

---

## 🚀 Deployment Process

### Pre-Deployment Checklist

- [ ] All code committed to Git
- [ ] Environment variables configured
- [ ] CloudScale database migrated & tested
- [ ] Frontend build verified (`npm run build`)
- [ ] Backend tests passing
- [ ] API endpoints tested locally
- [ ] CORS properly configured
- [ ] JWT secrets secure
- [ ] Monitoring alerts set up

### Deployment Steps

**Step 1: Build Frontend**
```bash
cd catalyst-frontend
npm run build
# Output: build/ folder (ready for Catalyst Client)
```

**Step 2: Configure Backend**
```bash
cd functions/catalyst_backend
# Verify .env has:
# - CATALYST_ENVIRONMENT=production
# - JWT_SECRET_KEY=<your-secret>
# - CORS_ALLOWED_ORIGINS=<client-domain>
```

**Step 3: Deploy via Catalyst CLI**
```bash
cd ../..
catalyst login
catalyst deploy
# Deploys both Client (build/) and Functions (functions/)
```

**Step 4: Verify Deployment**
```bash
catalyst serve --port 3000
# Test at: http://localhost:3000
# Or: https://railway-ticketing-system-*.catalyst-cs.in
```

**Step 5: Run Post-Deployment Tests**
- [ ] Frontend loads
- [ ] Login works
- [ ] API calls succeed
- [ ] Booking flow works end-to-end
- [ ] Admin features accessible
- [ ] Reports generate
- [ ] No console errors

---

## 🧪 Testing

### Local Testing

```bash
# Test Backend (CloudScale local)
cd functions/catalyst_backend
python test_crud_local.py

# Test Frontend
cd catalyst-frontend
npm run dev
# Navigate to http://localhost:5173

# Integration Test
cd ../..
catalyst serve
```

### Pre-Production Tests

| Test | File | Purpose |
|------|------|---------|
| CRUD Operations | `simple_crud_test.py` | Basic database operations |
| CloudScale Connection | `test_cloudscale_connection.py` | Database connectivity |
| User Creation | `demo_user_creation.py` | Sample data setup |
| API Health | `DEPLOYMENT_TEST_CHECKLIST.md` | Endpoint validation |

---

## 🛠️ Development Workflow

### Adding a New API Endpoint

**Backend**:
1. Create route file: `functions/catalyst_backend/routes/new_feature.py`
2. Define Flask blueprint with endpoints
3. Add service logic in `services/`
4. Add repository methods if needed
5. Import blueprint in `app.py`
6. Test locally with `pytest` or curl

**Frontend**:
1. Add API call in `catalyst-frontend/src/services/api.js`
2. Create page component in `pages/`
3. Add route to `App.jsx`
4. Add navigation link to sidebar
5. Test with `npm run dev`

### Adding Database Table

**Schema**:
1. Define in `catalyst-config.json`
2. Run `database_setup.py` to create
3. Add repository method in `repositories/`
4. Test with sample data

### Modifying Existing Feature

1. Identify file: Frontend (`src/pages/` or `src/components/`) or Backend (`routes/` or `services/`)
2. Make changes
3. Test locally: Frontend (`npm run dev`) or Backend (local test script)
4. Commit & push
5. Deploy: `catalyst deploy`

---

## 📚 API Reference

### All Endpoints

All endpoints prefixed with `/api`:

**Authentication**:
- `POST /auth/login` – User login
- `POST /auth/logout` – User logout
- `POST /auth/refresh` – Refresh token

**Stations**:
- `GET /stations` – List all
- `POST /stations` – Create
- `GET /stations/:id` – Get one
- `PUT /stations/:id` – Update
- `DELETE /stations/:id` – Delete

**Trains**:
- `GET /trains` – List all
- `POST /trains` – Create
- `GET /trains/:id` – Get one
- `PUT /trains/:id` – Update
- `DELETE /trains/:id` – Delete

**Bookings**:
- `GET /bookings` – List all
- `POST /bookings` – Create
- `GET /bookings/:id` – Get one
- `PUT /bookings/:id` – Update
- `DELETE /bookings/:id` – Delete
- `POST /bookings/:id/confirm` – Confirm

**Search**:
- `GET /search/trains` – Search trains (query: from, to, date, class)

**Admin**:
- `GET /reports/bookings` – Booking analytics
- `GET /reports/revenue` – Revenue reports
- `POST /admin/settings` – Update settings

**AI**:
- `POST /ai/chat` – Chatbot endpoint
- `GET /ai/recommendations` – Get recommendations

**Utility**:
- `GET /health` – Health check

---

## ⚡ Performance Considerations

### Caching Strategy

```python
# In-memory cache (fast, limited size)
cache.get('key')
cache.set('key', value, ttl=3600)

# CloudScale cache table (persistent)
CacheRepository.get('key')
CacheRepository.set('key', value, ttl=3600)
```

### Database Optimization

- **Indexes**: On frequently queried fields (email, booking_id, train_id)
- **Pagination**: Limit results to 50-100 per request
- **Lazy Loading**: Load related data on demand
- **Batch Operations**: Combine multiple queries when possible

### Function Timeout Management

- 5-minute max per Catalyst Function
- Long operations → async task queue pattern
- Heavy calculations → pre-compute and cache

---

## 🚨 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| **Import Error: zcatalyst_sdk** | SDK not installed | Run `pip install -r requirements.txt` |
| **CORS error in browser** | Origin not whitelisted | Check `app.py` CORS config, update with Catalyst domain |
| **401 Unauthorized** | Invalid JWT token | Check token expiration, verify JWT_SECRET_KEY match |
| **CloudScale connection fails** | DB not initialized | Run `python database_setup.py` |
| **Build fails: "Cannot find module"** | Dependencies not installed | Run `npm install` in catalyst-frontend/ |
| **Blank page after build** | 404.html missing | Check `build/404.html` exists (auto-created by build script) |
| **Slow API response** | Database query slow | Add index, optimize query, use pagination |
| **Token not refreshing** | Refresh endpoint missing | Check `routes/auth.py` has refresh route |

---

## 📞 Quick Reference

### Important Files

| File | Purpose | Edit When |
|------|---------|-----------|
| `functions/catalyst_backend/app.py` | Backend entry point | Adding routes, middleware |
| `functions/catalyst_backend/config.py` | Configuration | Changing JWT, CORS, timeouts |
| `catalyst-frontend/src/services/api.js` | API client setup | Changing backend URL |
| `catalyst.json` | Catalyst config | Adding new functions, deploying |
| `.catalystrc` | Local environment | Switching projects/environments |

### Useful Commands

```bash
# Catalyst
catalyst login                      # Authenticate with Zoho
catalyst deploy                     # Deploy to Catalyst
catalyst serve                      # Run locally
catalyst function:create <name>     # Create new function
catalyst list projects              # List all projects

# Frontend
npm run dev                         # Dev server
npm run build                       # Production build
npm run preview                     # Preview built app

# Backend (Functions)
python database_setup.py            # Initialize CloudScale
python test_crud_local.py           # Test database
python -m pytest tests/              # Run unit tests
```

---

## 🤖 Extended Agent Instructions (Detailed Guidance)

### How to Ask Claude for Help

**Effective Prompt Template:**

```
I'm working on [Component/Feature] in the Catalyst App.

Task: [Clearly describe what you need]

Relevant Context:
- File: [path if known]
- Related to: [feature/module]
- Environment: [development/production]

What I've tried: [optional - what didn't work]

Can you help with [specific ask]?
```

### Example Prompts

**Frontend Example:**
```
I'm working on a new booking search page in catalyst-frontend/src/pages/.

Task: Create a search form that filters trains by route, date, and class.

Relevant Context:
- Using Formik + Yup for validation
- Need to call GET /api/search/trains endpoint
- Display results in CRUDTable component
- Location: catalyst-frontend/src/pages/SearchPage.jsx

Can you provide the component code with proper error handling and loading states?
```

**Backend Example:**
```
I need to add a new API endpoint for booking confirmation in the Flask backend.

Task: Create POST /api/bookings/:id/confirm endpoint with:
- Validate booking exists
- Check seat availability
- Update booking status to CONFIRMED
- Return confirmation details

Relevant Context:
- File: functions/catalyst_backend/routes/bookings.py
- Database: Bookings, Train_Inventory tables
- Auth: Need to verify user is admin

Can you write the route handler with proper error handling?
```

**Database Example:**
```
I need to query available trains for a specific route and date.

Task: Write a CloudScale query for:
- From/to stations
- Date range
- Available seats > 0
- Class filter (optional)

Relevant Context:
- Tables: Trains, Train_Routes, Train_Inventory, Coach_Layouts
- Repository: functions/catalyst_backend/repositories/

Can you provide the query using zcatalyst-sdk?
```

### Claude's Response Format

Claude will typically respond with:

1. **Explanation**: What the code does
2. **Code Block**: Working implementation
3. **Integration Steps**: Where & how to add it
4. **Testing**: How to verify it works
5. **Troubleshooting**: Common issues & fixes
6. **File References**: Exact file paths to modify

### Task Categories & Expected Responses

| Task Type | Claude Response | Validation |
|-----------|-----------------|------------|
| **Create Component** | Full JSX with hooks, state, events | Test in dev server |
| **Add API Route** | Flask blueprint with decorators | Test with curl/Postman |
| **Database Query** | CloudScale code with error handling | Test with sample data |
| **Debug Issue** | Root cause analysis + fix | Run test to verify |
| **Refactor Code** | Improved version with explanations | Run tests, check performance |
| **Setup Env** | .env template with instructions | Verify with test request |

### Best Practices When Working with Claude

**DO:**
✅ Be specific about file locations
✅ Provide error messages if debugging
✅ Mention constraints (JWT required, auth needed, etc.)
✅ Ask for explanations, not just code
✅ Request test/verification steps
✅ Clarify assumptions

**DON'T:**
❌ Ask about Zoho platform configuration
❌ Request production deployment commands
❌ Ask for credential management
❌ Request infrastructure changes
❌ Ask for security policy decisions
❌ Assume Claude has platform access

### Reference Files to Share with Claude

When asking for help, mention:
- **Architecture**: "See CLAUDE_CATALYST_SKILLSET.md sections 1-3"
- **Frontend**: "See catalyst-frontend/claude.md"
- **Database**: "See CLOUDSCALE_DATABASE_SCHEMA.md"
- **API**: "See CLAUDE_CATALYST_SKILLSET.md section 11"
- **Deployment**: "See PRODUCTION_CUTOVER_GUIDE.md"
- **Testing**: "See DEPLOYMENT_TEST_CHECKLIST.md"

### Typical Development Workflow with Claude

1. **Planning Phase**
   - Describe feature → Claude suggests architecture
   - Discuss trade-offs → Claude explains options
   - Review constraints → Claude confirms scope

2. **Implementation Phase**
   - Ask Claude for component → Paste into project
   - Ask Claude to debug → Fix error
   - Ask Claude to refactor → Improve code quality

3. **Testing Phase**
   - Ask for test cases → Verify manually
   - Ask for edge case handling → Test scenarios
   - Ask Claude to review → Get feedback

4. **Deployment Phase**
   - Ask for deployment checklist → Follow steps
   - Ask for verification → Test in staging
   - Ask for troubleshooting → Debug issues

---

## 🎯 What Claude Can Help With

### ✅ Strongly

- **Frontend Development**: React components, forms, routing, styling
- **Backend APIs**: Flask routes, business logic, error handling
- **Database**: CloudScale queries, schema design, migrations
- **Integration**: API endpoints, data flow, debugging
- **Build & Deploy**: Vite config, environment setup, troubleshooting

### 🟡 Moderately

- **Performance Tuning**: Caching, database optimization, bundle size
- **AI Features**: NLP implementation, chatbot logic
- **Deployment**: Catalyst CLI commands, cutover planning

### ❌ Cannot Help

- **Zoho Catalyst Admin**: Platform setup, project creation, access management
- **Infrastructure**: Zoho Catalyst cluster configuration
- **Security Policies**: Zoho security compliance, data residency
- **Production Access**: Requires Zoho credentials & platform access

---

## 📖 Documentation Index

| Document | Purpose | Read When |
|----------|---------|-----------|
| `CLOUDSCALE_DATABASE_SCHEMA.md` | Database design | Understanding data model |
| `MIGRATION_GUIDE.md` | Data migration steps | Migrating from Zoho Creator |
| `PRODUCTION_CUTOVER_GUIDE.md` | Deployment procedures | Going to production |
| `DEPLOYMENT_TEST_CHECKLIST.md` | Pre-deployment tests | Before deploying |
| `CLOUDSCALE_QUICK_REFERENCE.md` | Quick lookup | During development |

---

## 🔗 Quick Links

- **Catalyst Dashboard**: https://catalyst.zoho.in
- **Catalyst Docs**: https://docs.zoho.com/catalyst/
- **Project Root**: `f:\Railway Project Backend\Catalyst App`
- **Frontend**: `f:\Railway Project Backend\Catalyst App\catalyst-frontend`
- **Backend**: `f:\Railway Project Backend\Catalyst App\functions\catalyst_backend`
- **Database Config**: `f:\Railway Project Backend\Catalyst App\functions\catalyst_backend\catalyst-config.json`

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-22  
**Status**: Active Development  
**Audience**: Developers, DevOps, QA  
**Maintained By**: Railway Ticketing System Team

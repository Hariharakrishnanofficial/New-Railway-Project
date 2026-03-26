# Railway Ticketing System - Folder Structure
## Functions (Backend) & Client (Frontend)

---

## 1. Functions (Backend)

**Location**: `Catalyst App/functions/catalyst_backend/`

```
functions/
└── catalyst_backend/
    │
    ├── app.py                    # Flask application entry point
    ├── app_backup.py             # Backup of main application
    ├── config.py                 # Environment & configuration settings
    ├── database_setup.py         # CloudScale database table creation
    ├── requirements.txt          # Python dependencies
    ├── catalyst-config.json      # Zoho Catalyst configuration
    ├── .env                      # Environment variables (secrets)
    ├── .env.example              # Environment template
    │
    ├── ai/                       # AI & NLP Module
    │   ├── __init__.py
    │   ├── booking_conversation.py   # Conversational booking assistant
    │   ├── booking_prompts.py        # AI prompt templates for booking
    │   ├── circuit_breaker.py        # Fault tolerance for AI calls
    │   ├── claude_agent.py           # Claude AI integration
    │   ├── gemini_agent.py           # Google Gemini integration
    │   ├── nlp_search.py             # Natural language train search
    │   ├── prompts.py                # General AI prompts
    │   └── qwen_client.py            # Qwen model client
    │
    ├── core/                     # Core Framework
    │   ├── __init__.py
    │   ├── exceptions.py             # Custom exception classes
    │   └── security.py               # JWT auth, decorators, bcrypt
    │
    ├── repositories/             # Data Access Layer
    │   ├── __init__.py
    │   ├── cache_manager.py          # In-memory caching (TTL-based)
    │   └── cloudscale_repository.py  # Zoho Creator/CloudScale CRUD
    │
    ├── routes/                   # API Endpoints (Blueprints)
    │   ├── __init__.py
    │   ├── admin_logs.py             # GET /api/admin-logs
    │   ├── admin_reports.py          # GET /api/reports/*
    │   ├── ai_routes.py              # POST /api/ai/chat, /api/ai/qwen
    │   ├── announcements.py          # CRUD /api/announcements
    │   ├── auth.py                   # POST /api/auth/login, /register
    │   ├── auth_crud.py              # Auth CRUD operations
    │   ├── bookings.py               # CRUD /api/bookings, /cancel
    │   ├── coach_layouts.py          # CRUD /api/coach-layouts
    │   ├── coaches.py                # CRUD /api/coaches
    │   ├── fares.py                  # CRUD /api/fares, /calculate
    │   ├── inventory.py              # GET /api/inventory
    │   ├── overview.py               # GET /api/overview (dashboard)
    │   ├── quotas.py                 # CRUD /api/quotas
    │   ├── settings.py               # CRUD /api/settings
    │   ├── stations.py               # CRUD /api/stations
    │   ├── train_routes.py           # CRUD /api/train-routes, /stops
    │   ├── trains.py                 # CRUD /api/trains, /vacancy
    │   ├── users.py                  # CRUD /api/users (Zoho)
    │   └── users_cloudscale.py       # CRUD /api/users (CloudScale)
    │
    ├── services/                 # Business Logic Layer
    │   ├── __init__.py
    │   ├── analytics_service.py      # Dashboard analytics & reports
    │   ├── auth_crud_service.py      # Authentication operations
    │   ├── booking_service.py        # Booking create/cancel/modify
    │   ├── schema_discovery.py       # Dynamic Zoho schema discovery
    │   ├── user_service.py           # User management & validation
    │   └── zoho_service.py           # Zoho Creator API wrapper
    │
    └── utils/                    # Utility Functions
        ├── __init__.py
        ├── admin_logger.py           # Audit log writer
        ├── date_helpers.py           # Date format conversions
        ├── fare_helper.py            # Fare calculation logic
        ├── log_helper.py             # Logging utilities
        ├── seat_allocation.py        # CNF/RAC/WL allocation engine
        └── validators.py             # Input validation helpers
```

### 1.1 Folder Descriptions

| Folder | Purpose | Key Responsibilities |
|--------|---------|---------------------|
| **ai/** | AI & NLP | Conversational booking, natural language search, multi-model support |
| **core/** | Framework | Security (JWT/bcrypt), custom exceptions, decorators |
| **repositories/** | Data Access | Zoho API calls, caching, criteria builder |
| **routes/** | API Layer | HTTP endpoints, request/response handling, validation |
| **services/** | Business Logic | Booking rules, fare calculation, user management |
| **utils/** | Helpers | Date formatting, seat allocation, logging |

### 1.2 Key Files

| File | Purpose |
|------|---------|
| `app.py` | Flask app initialization, blueprint registration, CORS setup |
| `config.py` | Environment variables, table mappings, constants |
| `database_setup.py` | CloudScale table DDL scripts |

---

## 2. Client (Frontend)

**Location**: `Frontend/fixed_frontend/`

```
fixed_frontend/
│
├── index.html                # HTML entry point
├── package.json              # NPM dependencies & scripts
├── vite.config.js            # Vite build configuration
├── .env                      # Environment variables
│
├── public/                   # Static Assets
│   └── (favicon, images)
│
├── dist/                     # Production Build Output
│   ├── index.html
│   └── assets/
│       ├── index-*.js
│       └── index-*.css
│
└── src/                      # Source Code
    │
    ├── main.jsx              # React entry point
    ├── App.jsx               # Root component & routing
    │
    ├── components/           # Reusable UI Components
    │   ├── AdminLayout.jsx           # Admin panel wrapper
    │   ├── AdminMasterLayout.jsx     # Master data admin wrapper
    │   ├── AIChatWidget.jsx          # Floating AI chat assistant
    │   ├── CRUDTable.jsx             # Generic CRUD data table
    │   ├── ErrorBoundary.jsx         # Error handling wrapper
    │   ├── FormFields.jsx            # Reusable form inputs
    │   ├── Layout.jsx                # Main app layout
    │   ├── LoginModal.jsx            # Login popup modal
    │   ├── PassengerLayout.jsx       # Passenger portal wrapper
    │   ├── RequireAuth.jsx           # Route protection HOC
    │   ├── SignInModal.jsx           # Sign-in popup
    │   └── UI.jsx                    # Common UI elements
    │
    ├── context/              # React Context Providers
    │   ├── SettingsContext.jsx       # App settings state
    │   └── ToastContext.jsx          # Toast notifications
    │
    ├── hooks/                # Custom React Hooks
    │   └── useApi.js                 # API call hook with loading/error
    │
    ├── pages/                # Page Components
    │   │
    │   │── LoginPage.jsx             # User login
    │   │── ProfilePage.jsx           # User profile
    │   │── ChangePasswordPage.jsx    # Password change
    │   │
    │   │── PassengerHome.jsx         # Passenger dashboard
    │   │── SearchPage.jsx            # Train search
    │   │── BookingsPage.jsx          # Book tickets
    │   │── MyBookings.jsx            # User's bookings list
    │   │── PNRStatus.jsx             # PNR enquiry
    │   │── CancelTicket.jsx          # Cancel booking
    │   │── TrainSchedule.jsx         # Train schedule viewer
    │   │── ChartVacancy.jsx          # Seat availability chart
    │   │
    │   │── AdminDashboard.jsx        # Admin home
    │   │── AdminDashboard.css        # Admin dashboard styles
    │   │── OverviewPage.jsx          # System overview
    │   │── TrainsPage.jsx            # Train management
    │   │── StationsPage.jsx          # Station management
    │   │── TrainRoutesPage.jsx       # Route management
    │   │── FaresPage.jsx             # Fare management
    │   │── UsersPage.jsx             # User management
    │   │── InventoryPage.jsx         # Seat inventory
    │   │── ReservationChartPage.jsx  # Reservation charts
    │   │── AnnouncementsPage.jsx     # Announcements CRUD
    │   │── AdminLogsPage.jsx         # Audit logs viewer
    │   │── ReportsPage.jsx           # Analytics reports
    │   │── SettingsPage.jsx          # System settings
    │   │── PassengerExplorerPage.jsx # Passenger data explorer
    │   │── ZohoExplorerPage.jsx      # Zoho data explorer
    │   │
    │   │── AITestAgent.jsx           # AI testing interface
    │   │── MCPChatPage.jsx           # MCP query chat
    │   │
    │   └── admin/                    # Admin Sub-Pages
    │       ├── MasterDataAdmin.jsx       # Master data management
    │       ├── MasterDataAdmin.css       # Master data styles
    │       ├── TrainRoutesAdmin.jsx      # Route stops editor
    │       └── TrainRoutesAdmin.css      # Route editor styles
    │
    ├── services/             # API Services
    │   └── api.js                    # Axios instance & API calls
    │
    └── styles/               # Global Styles
        └── global.css                # Global CSS styles
```

### 2.1 Folder Descriptions

| Folder | Purpose | Contents |
|--------|---------|----------|
| **components/** | Reusable UI | Layouts, forms, tables, modals |
| **context/** | State Management | Settings, toast notifications |
| **hooks/** | Custom Hooks | API calls, form handling |
| **pages/** | Route Pages | All application screens |
| **pages/admin/** | Admin Sub-Pages | Master data management |
| **services/** | API Layer | Axios config, API methods |
| **styles/** | Styling | Global CSS |

### 2.2 Page Categories

#### Passenger Pages
| Page | Route | Purpose |
|------|-------|---------|
| PassengerHome | `/` | Passenger dashboard |
| SearchPage | `/search` | Train search |
| BookingsPage | `/book` | Create booking |
| MyBookings | `/my-bookings` | View user bookings |
| PNRStatus | `/pnr-status` | PNR enquiry |
| CancelTicket | `/cancel` | Cancel booking |
| TrainSchedule | `/schedule` | View train schedule |

#### Admin Pages
| Page | Route | Purpose |
|------|-------|---------|
| AdminDashboard | `/admin` | Admin home |
| TrainsPage | `/admin/trains` | Train CRUD |
| StationsPage | `/admin/stations` | Station CRUD |
| TrainRoutesPage | `/admin/routes` | Route CRUD |
| FaresPage | `/admin/fares` | Fare CRUD |
| UsersPage | `/admin/users` | User management |
| InventoryPage | `/admin/inventory` | Seat inventory |
| AnnouncementsPage | `/admin/announcements` | Announcements |
| AdminLogsPage | `/admin/logs` | Audit logs |
| ReportsPage | `/admin/reports` | Analytics |
| SettingsPage | `/admin/settings` | System config |

---

## 3. Full Project Structure

```
Railway Project Backend/
│
├── Catalyst App/                     # Zoho Catalyst Project
│   │
│   ├── functions/                    # Backend (Serverless Functions)
│   │   └── catalyst_backend/         # Main Flask Application
│   │       ├── ai/                       # AI & NLP
│   │       ├── core/                     # Framework
│   │       ├── repositories/             # Data Access
│   │       ├── routes/                   # API Endpoints
│   │       ├── services/                 # Business Logic
│   │       ├── utils/                    # Utilities
│   │       ├── app.py                    # Entry Point
│   │       └── config.py                 # Configuration
│   │
│   ├── client/                       # Frontend (React)
│   │   └── (Catalyst hosted build)
│   │
│   ├── catalyst-config.json          # Catalyst project config
│   └── *.md                          # Documentation files
│
├── Frontend/                         # Frontend Source
│   └── fixed_frontend/
│       ├── src/
│       │   ├── components/               # UI Components
│       │   ├── context/                  # State Management
│       │   ├── hooks/                    # Custom Hooks
│       │   ├── pages/                    # Page Components
│       │   ├── services/                 # API Services
│       │   └── styles/                   # CSS Styles
│       ├── dist/                         # Build Output
│       └── package.json                  # Dependencies
│
└── Backend/                          # Alternative Backend
    └── appsail-python/               # AppSail deployment
        └── (same structure as catalyst_backend)
```

---

## 4. Summary

### Backend (Functions) - 53 Python Files

| Layer | Files | Purpose |
|-------|-------|---------|
| Entry | 2 | app.py, config.py |
| AI | 9 | Conversational AI, NLP search |
| Core | 2 | Security, exceptions |
| Repositories | 2 | Cache, Zoho API |
| Routes | 19 | API endpoints |
| Services | 6 | Business logic |
| Utils | 6 | Helpers |

### Frontend (Client) - 52 Source Files

| Layer | Files | Purpose |
|-------|-------|---------|
| Entry | 2 | main.jsx, App.jsx |
| Components | 12 | Reusable UI |
| Context | 2 | State management |
| Hooks | 1 | Custom hooks |
| Pages | 32 | Application screens |
| Services | 1 | API client |
| Styles | 2 | CSS |

---

*Document Version: 1.0*
*Generated: 2026-03-25*

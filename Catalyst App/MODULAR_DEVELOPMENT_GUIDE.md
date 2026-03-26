# Railway Ticketing System - Modular Development Guide
## CloudScale Database Implementation

---

## Table of Contents
1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Development Phases](#3-development-phases)
4. [Module Implementation Guide](#4-module-implementation-guide)
5. [CloudScale Database Setup](#5-cloudscale-database-setup)
6. [Code Templates](#6-code-templates)
7. [Testing Strategy](#7-testing-strategy)

---

## 1. Architecture Overview

### 1.1 Layered Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                 │
│                        (routes/ - API Endpoints)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                           BUSINESS LOGIC LAYER                              │
│                        (services/ - Business Rules)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                           DATA ACCESS LAYER                                 │
│                     (repositories/ - CloudScale CRUD)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                              DATABASE                                        │
│                      (Zoho Catalyst CloudScale)                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Module Independence Principle

Each module should be:
- **Self-contained**: Own routes, services, repositories
- **Loosely coupled**: Minimal dependencies on other modules
- **Independently testable**: Can be tested in isolation
- **Plug-and-play**: Can be enabled/disabled without breaking system

---

## 2. Project Structure

### 2.1 Modular Folder Structure

```
railway_backend/
│
├── app.py                          # Main Flask app (imports all modules)
├── config.py                       # Global configuration
├── requirements.txt                # Dependencies
│
├── core/                           # Shared Core (used by all modules)
│   ├── __init__.py
│   ├── database.py                 # CloudScale connection manager
│   ├── exceptions.py               # Custom exception classes
│   ├── security.py                 # JWT auth, decorators
│   └── base_repository.py          # Base CRUD operations
│
├── shared/                         # Shared Utilities
│   ├── __init__.py
│   ├── validators.py               # Common validators
│   ├── date_helpers.py             # Date utilities
│   └── response_helpers.py         # API response formatters
│
├── modules/                        # Individual Modules
│   │
│   ├── auth/                       # AUTH MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # POST /api/auth/login, /register
│   │   ├── services.py             # AuthService class
│   │   ├── repository.py           # User data access
│   │   ├── models.py               # User model/schema
│   │   └── tests/
│   │       └── test_auth.py
│   │
│   ├── stations/                   # STATIONS MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # CRUD /api/stations
│   │   ├── services.py             # StationService class
│   │   ├── repository.py           # Station data access
│   │   ├── models.py               # Station model/schema
│   │   └── tests/
│   │       └── test_stations.py
│   │
│   ├── trains/                     # TRAINS MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # CRUD /api/trains
│   │   ├── services.py             # TrainService class
│   │   ├── repository.py           # Train data access
│   │   ├── models.py               # Train model/schema
│   │   └── tests/
│   │       └── test_trains.py
│   │
│   ├── train_routes/               # TRAIN ROUTES MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # CRUD /api/train-routes
│   │   ├── services.py             # TrainRouteService class
│   │   ├── repository.py           # Route data access
│   │   ├── models.py               # Route model/schema
│   │   └── tests/
│   │       └── test_train_routes.py
│   │
│   ├── fares/                      # FARES MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # CRUD /api/fares, /calculate
│   │   ├── services.py             # FareService, FareCalculator
│   │   ├── repository.py           # Fare data access
│   │   ├── models.py               # Fare model/schema
│   │   └── tests/
│   │       └── test_fares.py
│   │
│   ├── quotas/                     # QUOTAS MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # CRUD /api/quotas
│   │   ├── services.py             # QuotaService class
│   │   ├── repository.py           # Quota data access
│   │   ├── models.py               # Quota model/schema
│   │   └── tests/
│   │       └── test_quotas.py
│   │
│   ├── inventory/                  # INVENTORY MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # GET /api/inventory
│   │   ├── services.py             # InventoryService class
│   │   ├── repository.py           # Inventory data access
│   │   ├── models.py               # Inventory model/schema
│   │   └── tests/
│   │       └── test_inventory.py
│   │
│   ├── bookings/                   # BOOKINGS MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # CRUD /api/bookings
│   │   ├── services.py             # BookingService class
│   │   ├── repository.py           # Booking data access
│   │   ├── models.py               # Booking model/schema
│   │   ├── seat_allocator.py       # CNF/RAC/WL logic
│   │   ├── pnr_generator.py        # PNR generation
│   │   └── tests/
│   │       └── test_bookings.py
│   │
│   ├── passengers/                 # PASSENGERS MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # GET /api/passengers
│   │   ├── services.py             # PassengerService class
│   │   ├── repository.py           # Passenger data access
│   │   └── models.py               # Passenger model/schema
│   │
│   ├── announcements/              # ANNOUNCEMENTS MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # CRUD /api/announcements
│   │   ├── services.py             # AnnouncementService class
│   │   ├── repository.py           # Announcement data access
│   │   └── models.py               # Announcement model/schema
│   │
│   ├── admin_logs/                 # ADMIN LOGS MODULE
│   │   ├── __init__.py
│   │   ├── routes.py               # GET /api/admin-logs
│   │   ├── services.py             # AdminLogService class
│   │   ├── repository.py           # Log data access
│   │   └── models.py               # Log model/schema
│   │
│   └── reports/                    # REPORTS MODULE
│       ├── __init__.py
│       ├── routes.py               # GET /api/reports/*
│       ├── services.py             # ReportService class
│       └── repository.py           # Report queries
│
└── tests/                          # Integration Tests
    ├── __init__.py
    ├── conftest.py                 # Pytest fixtures
    └── test_integration.py         # Cross-module tests
```

---

## 3. Development Phases

### Phase 1: Foundation (Week 1)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 1: CORE INFRASTRUCTURE                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1.1: Project Setup                                                    │
│  ─────────────────────────                                                  │
│  ├─ Create folder structure                                                 │
│  ├─ Initialize virtual environment                                          │
│  ├─ Install dependencies (Flask, zcatalyst-sdk, PyJWT, bcrypt)             │
│  └─ Create config.py with environment variables                            │
│                                                                             │
│  Step 1.2: Core Module                                                      │
│  ────────────────────────                                                   │
│  ├─ core/database.py - CloudScale connection manager                       │
│  ├─ core/exceptions.py - Custom exceptions                                 │
│  ├─ core/security.py - JWT authentication                                  │
│  └─ core/base_repository.py - Base CRUD operations                         │
│                                                                             │
│  Step 1.3: Shared Utilities                                                 │
│  ──────────────────────────                                                 │
│  ├─ shared/validators.py - Input validation                                │
│  ├─ shared/date_helpers.py - Date formatting                               │
│  └─ shared/response_helpers.py - API response structure                    │
│                                                                             │
│  Step 1.4: Main App Entry                                                   │
│  ────────────────────────                                                   │
│  └─ app.py - Flask app with blueprint registration                         │
│                                                                             │
│  DELIVERABLES:                                                              │
│  ✓ Working Flask app shell                                                  │
│  ✓ CloudScale connection verified                                           │
│  ✓ JWT auth middleware working                                              │
│  ✓ Base repository with CRUD operations                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Master Data Modules (Week 2)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 2: MASTER DATA MODULES                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 2.1: Auth Module                                                      │
│  ─────────────────────                                                      │
│  ├─ CloudScale table: Users                                                │
│  ├─ routes.py: POST /login, /register, /forgot-password                    │
│  ├─ services.py: AuthService (login, register, password_reset)             │
│  └─ repository.py: UserRepository (get_by_email, create, update)           │
│                                                                             │
│  Step 2.2: Stations Module                                                  │
│  ─────────────────────────                                                  │
│  ├─ CloudScale table: Stations                                             │
│  ├─ routes.py: GET, POST, PUT, DELETE /api/stations                        │
│  ├─ services.py: StationService (search, validate)                         │
│  └─ repository.py: StationRepository (CRUD + search)                       │
│                                                                             │
│  Step 2.3: Trains Module                                                    │
│  ────────────────────────                                                   │
│  ├─ CloudScale table: Trains                                               │
│  ├─ routes.py: CRUD + /search, /vacancy                                    │
│  ├─ services.py: TrainService (search, filter, vacancy)                    │
│  └─ repository.py: TrainRepository (CRUD + complex queries)                │
│                                                                             │
│  Step 2.4: Train Routes Module                                              │
│  ─────────────────────────────                                              │
│  ├─ CloudScale tables: Train_Routes, Route_Stops                           │
│  ├─ routes.py: CRUD /api/train-routes, /stops                              │
│  ├─ services.py: TrainRouteService (schedule, connections)                 │
│  └─ repository.py: RouteRepository (with stops management)                 │
│                                                                             │
│  DELIVERABLES:                                                              │
│  ✓ User authentication working                                              │
│  ✓ Station CRUD with search                                                │
│  ✓ Train CRUD with search & vacancy                                        │
│  ✓ Route management with stops                                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Business Logic Modules (Week 3)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 3: BUSINESS LOGIC MODULES                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 3.1: Fares Module                                                     │
│  ──────────────────────                                                     │
│  ├─ CloudScale table: Fares                                                │
│  ├─ routes.py: CRUD + POST /calculate                                      │
│  ├─ services.py: FareService, FareCalculator                               │
│  │   └─ IRCTC calculation (base + surcharge + GST + concession)            │
│  └─ repository.py: FareRepository (fare lookup by route/class)             │
│                                                                             │
│  Step 3.2: Quotas Module                                                    │
│  ───────────────────────                                                    │
│  ├─ CloudScale table: Quotas                                               │
│  ├─ routes.py: CRUD /api/quotas                                            │
│  ├─ services.py: QuotaService (availability, surcharge)                    │
│  └─ repository.py: QuotaRepository (by train/class)                        │
│                                                                             │
│  Step 3.3: Inventory Module                                                 │
│  ──────────────────────────                                                 │
│  ├─ CloudScale table: Train_Inventory                                      │
│  ├─ routes.py: GET /api/inventory                                          │
│  ├─ services.py: InventoryService (availability check)                     │
│  └─ repository.py: InventoryRepository (by train/date/class)               │
│                                                                             │
│  Step 3.4: Coach Layouts Module                                             │
│  ──────────────────────────────                                             │
│  ├─ CloudScale table: Coach_Layouts                                        │
│  ├─ routes.py: CRUD /api/coach-layouts                                     │
│  └─ services.py: CoachLayoutService (layout JSON management)               │
│                                                                             │
│  DELIVERABLES:                                                              │
│  ✓ Full fare calculation with IRCTC rules                                  │
│  ✓ Quota management with surcharges                                        │
│  ✓ Real-time inventory tracking                                            │
│  ✓ Coach layout configuration                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 4: Booking Module (Week 4)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 4: BOOKING MODULE (CORE TRANSACTION)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 4.1: Booking Repository                                               │
│  ────────────────────────────                                               │
│  ├─ CloudScale tables: Bookings, Passengers                                │
│  ├─ Create, Read, Update bookings                                          │
│  ├─ Monthly booking count query                                            │
│  └─ Duplicate booking check                                                │
│                                                                             │
│  Step 4.2: PNR Generator                                                    │
│  ────────────────────────                                                   │
│  ├─ Generate unique PNR (PNR + 8 alphanumeric)                             │
│  └─ Collision check with retry                                             │
│                                                                             │
│  Step 4.3: Seat Allocator                                                   │
│  ────────────────────────                                                   │
│  ├─ process_booking_allocation()                                           │
│  │   ├─ Get/Create Train_Inventory                                         │
│  │   ├─ Load Coach Layout JSON                                             │
│  │   ├─ Find available seat (preference → any)                             │
│  │   └─ Assign CNF/RAC/WL status                                           │
│  │                                                                          │
│  ├─ process_booking_cancellation()                                         │
│  │   ├─ Free confirmed seats                                               │
│  │   ├─ Update inventory counts                                            │
│  │   └─ Trigger waitlist promotion                                         │
│  │                                                                          │
│  └─ calculate_refund()                                                     │
│      └─ IRCTC refund rules (time-based, class-based)                       │
│                                                                             │
│  Step 4.4: Booking Service                                                  │
│  ─────────────────────────                                                  │
│  ├─ create() - Full booking flow                                           │
│  │   ├─ Validate inputs                                                    │
│  │   ├─ Check booking limits                                               │
│  │   ├─ Calculate fare                                                     │
│  │   ├─ Allocate seats                                                     │
│  │   ├─ Generate PNR                                                       │
│  │   └─ Create records                                                     │
│  │                                                                          │
│  ├─ cancel() - Full cancellation                                           │
│  ├─ partial_cancel() - Partial passenger cancel                            │
│  └─ get_by_pnr() - PNR lookup                                              │
│                                                                             │
│  Step 4.5: Booking Routes                                                   │
│  ────────────────────────                                                   │
│  ├─ POST /api/bookings - Create booking                                    │
│  ├─ GET /api/bookings/{id} - Get by ID                                     │
│  ├─ GET /api/bookings/pnr/{pnr} - Get by PNR                               │
│  ├─ POST /api/bookings/{id}/cancel - Full cancel                           │
│  └─ POST /api/bookings/{id}/partial-cancel - Partial cancel                │
│                                                                             │
│  DELIVERABLES:                                                              │
│  ✓ Complete booking flow with PNR                                          │
│  ✓ CNF/RAC/WL seat allocation                                              │
│  ✓ Cancellation with refund calculation                                    │
│  ✓ Waitlist promotion                                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 5: Support Modules (Week 5)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PHASE 5: SUPPORT MODULES                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 5.1: Announcements Module                                             │
│  ──────────────────────────────                                             │
│  ├─ CloudScale table: Announcements                                        │
│  ├─ CRUD operations                                                        │
│  └─ Active announcements filter (date range)                               │
│                                                                             │
│  Step 5.2: Admin Logs Module                                                │
│  ───────────────────────────                                                │
│  ├─ CloudScale table: Admin_Logs                                           │
│  ├─ Fire-and-forget logging                                                │
│  └─ Query with filters (user, action, record)                              │
│                                                                             │
│  Step 5.3: Reports Module                                                   │
│  ────────────────────────                                                   │
│  ├─ GET /api/reports/bookings - Booking statistics                         │
│  ├─ GET /api/reports/revenue - Revenue by period                           │
│  ├─ GET /api/reports/trains - Train utilization                            │
│  └─ GET /api/reports/users - User activity                                 │
│                                                                             │
│  Step 5.4: Settings Module                                                  │
│  ─────────────────────────                                                  │
│  ├─ CloudScale table: Settings                                             │
│  └─ Key-value configuration store                                          │
│                                                                             │
│  DELIVERABLES:                                                              │
│  ✓ Announcement system                                                     │
│  ✓ Audit logging                                                           │
│  ✓ Analytics reports                                                       │
│  ✓ System settings                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Module Implementation Guide

### 4.1 Module Development Checklist

For each module, follow this sequence:

```
□ Step 1: Define Model (models.py)
    ├─ Define CloudScale table schema
    ├─ Define field types and constraints
    └─ Define validation rules

□ Step 2: Create Repository (repository.py)
    ├─ Inherit from BaseRepository
    ├─ Implement CRUD operations
    ├─ Add module-specific queries
    └─ Add caching where needed

□ Step 3: Implement Service (services.py)
    ├─ Add business logic
    ├─ Add validation rules
    ├─ Handle cross-module dependencies
    └─ Add error handling

□ Step 4: Create Routes (routes.py)
    ├─ Create Flask Blueprint
    ├─ Define API endpoints
    ├─ Add auth decorators
    └─ Add input validation

□ Step 5: Register Module (app.py)
    └─ Import and register blueprint

□ Step 6: Write Tests (tests/)
    ├─ Unit tests for service
    ├─ Integration tests for API
    └─ Edge case tests
```

### 4.2 Module Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODULE DEPENDENCY GRAPH                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LEVEL 0 (No Dependencies)                                                  │
│  ─────────────────────────                                                  │
│  ├─ auth          → Uses only core/                                        │
│  ├─ stations      → Uses only core/                                        │
│  ├─ coach_layouts → Uses only core/                                        │
│  ├─ announcements → Uses only core/                                        │
│  ├─ admin_logs    → Uses only core/                                        │
│  └─ settings      → Uses only core/                                        │
│                                                                             │
│  LEVEL 1 (Single Dependency)                                                │
│  ────────────────────────────                                               │
│  ├─ trains        → Depends on: stations                                   │
│  ├─ quotas        → Depends on: trains                                     │
│  └─ train_routes  → Depends on: trains, stations                           │
│                                                                             │
│  LEVEL 2 (Multiple Dependencies)                                            │
│  ────────────────────────────────                                           │
│  ├─ fares         → Depends on: trains, stations                           │
│  └─ inventory     → Depends on: trains, coach_layouts                      │
│                                                                             │
│  LEVEL 3 (Complex Dependencies)                                             │
│  ────────────────────────────────                                           │
│  └─ bookings      → Depends on: ALL above modules                          │
│      ├─ auth (user validation)                                             │
│      ├─ trains (train lookup)                                              │
│      ├─ stations (boarding/deboarding)                                     │
│      ├─ fares (fare calculation)                                           │
│      ├─ quotas (surcharge lookup)                                          │
│      ├─ inventory (seat allocation)                                        │
│      └─ coach_layouts (seat map)                                           │
│                                                                             │
│  LEVEL 4 (Cross-Cutting)                                                    │
│  ────────────────────────                                                   │
│  └─ reports       → Reads from: ALL modules                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Implementation Order

```
Week 1: Foundation
├─ Day 1-2: core/ (database, security, exceptions)
├─ Day 3-4: shared/ (validators, helpers)
└─ Day 5: app.py setup

Week 2: Level 0 Modules
├─ Day 1: auth module
├─ Day 2: stations module
├─ Day 3: coach_layouts module
├─ Day 4: announcements module
└─ Day 5: admin_logs, settings modules

Week 3: Level 1-2 Modules
├─ Day 1-2: trains module
├─ Day 2-3: train_routes module
├─ Day 3-4: quotas module
├─ Day 4: fares module
└─ Day 5: inventory module

Week 4: Level 3 Module
├─ Day 1: booking repository, models
├─ Day 2: PNR generator, seat allocator
├─ Day 3-4: booking service (create, cancel)
└─ Day 5: booking routes, integration

Week 5: Finalization
├─ Day 1-2: reports module
├─ Day 3: Integration testing
├─ Day 4: Bug fixes
└─ Day 5: Documentation
```

---

## 5. CloudScale Database Setup

### 5.1 Table Creation Order

```python
# database_setup.py - Execute in this order

TABLES_ORDER = [
    # Level 0: No foreign keys
    "Users",
    "Stations",
    "Coach_Layouts",
    "Settings",
    "Announcements",
    "Admin_Logs",

    # Level 1: Single FK
    "Trains",           # FK: From_Station, To_Station

    # Level 2: Multiple FKs
    "Train_Routes",     # FK: Train_ID
    "Route_Stops",      # FK: Train_Route_ID, Station_ID
    "Quotas",           # FK: Train_ID
    "Fares",            # FK: Train_ID, From_Station, To_Station
    "Train_Inventory",  # FK: Train_ID

    # Level 3: Transactional
    "Bookings",         # FK: User_ID, Train_ID
    "Passengers",       # FK: Booking_ID
]
```

### 5.2 CloudScale Table Definitions

```python
# core/database.py

from zcatalyst_sdk import CatalystApp

class CloudScaleDB:
    def __init__(self):
        self.app = CatalystApp()
        self.zcql = self.app.zcql()
        self.datastore = self.app.datastore()

    def execute_query(self, query: str) -> list:
        """Execute ZCQL query and return results."""
        result = self.zcql.execute_query(query)
        return result if result else []

    def get_table(self, table_name: str):
        """Get table reference for CRUD operations."""
        return self.datastore.table(table_name)

    def insert(self, table_name: str, data: dict) -> dict:
        """Insert a record into table."""
        table = self.get_table(table_name)
        return table.insert_row(data)

    def update(self, table_name: str, row_id: int, data: dict) -> dict:
        """Update a record by ROWID."""
        table = self.get_table(table_name)
        data['ROWID'] = row_id
        return table.update_row(data)

    def delete(self, table_name: str, row_id: int) -> bool:
        """Delete a record by ROWID."""
        table = self.get_table(table_name)
        table.delete_row(row_id)
        return True

    def get_by_id(self, table_name: str, row_id: int) -> dict:
        """Get a record by ROWID."""
        table = self.get_table(table_name)
        return table.get_row(row_id)


# Global instance
db = CloudScaleDB()
```

### 5.3 Table Schemas (ZCQL)

```sql
-- Users Table
CREATE TABLE Users (
    ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Email VARCHAR(255) UNIQUE NOT NULL,
    Password_Hash VARCHAR(255) NOT NULL,
    Full_Name VARCHAR(255),
    Phone VARCHAR(20),
    Role VARCHAR(20) DEFAULT 'user',
    Is_Aadhar_Verified BOOLEAN DEFAULT false,
    Created_At DATETIME DEFAULT CURRENT_TIMESTAMP,
    Updated_At DATETIME
);

-- Stations Table
CREATE TABLE Stations (
    ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Station_Code VARCHAR(10) UNIQUE NOT NULL,
    Station_Name VARCHAR(255) NOT NULL,
    City VARCHAR(100),
    State VARCHAR(100),
    Zone VARCHAR(50),
    Station_Type VARCHAR(50),
    Is_Active BOOLEAN DEFAULT true
);

-- Trains Table
CREATE TABLE Trains (
    ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Train_Number VARCHAR(20) UNIQUE NOT NULL,
    Train_Name VARCHAR(255) NOT NULL,
    Train_Type VARCHAR(50),
    From_Station_ID BIGINT REFERENCES Stations(ROWID),
    To_Station_ID BIGINT REFERENCES Stations(ROWID),
    Departure_Time TIME,
    Arrival_Time TIME,
    Run_Days VARCHAR(50),
    Total_Seats_SL INT DEFAULT 0,
    Total_Seats_3A INT DEFAULT 0,
    Total_Seats_2A INT DEFAULT 0,
    Total_Seats_1A INT DEFAULT 0,
    Fare_SL DECIMAL(10,2),
    Fare_3A DECIMAL(10,2),
    Fare_2A DECIMAL(10,2),
    Fare_1A DECIMAL(10,2),
    Is_Active BOOLEAN DEFAULT true
);

-- Train_Inventory Table
CREATE TABLE Train_Inventory (
    ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Train_ID BIGINT REFERENCES Trains(ROWID),
    Journey_Date DATE NOT NULL,
    Class VARCHAR(10) NOT NULL,
    Total_Capacity INT NOT NULL,
    Confirmed_Count INT DEFAULT 0,
    RAC_Count INT DEFAULT 0,
    Waitlist_Count INT DEFAULT 0,
    Confirmed_Seats_JSON TEXT,
    UNIQUE(Train_ID, Journey_Date, Class)
);

-- Bookings Table
CREATE TABLE Bookings (
    ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
    PNR VARCHAR(20) UNIQUE NOT NULL,
    User_ID BIGINT REFERENCES Users(ROWID),
    Train_ID BIGINT REFERENCES Trains(ROWID),
    Journey_Date DATE NOT NULL,
    Class VARCHAR(10) NOT NULL,
    Quota VARCHAR(20) DEFAULT 'GN',
    Num_Passengers INT NOT NULL,
    Total_Fare DECIMAL(10,2),
    Booking_Status VARCHAR(20) DEFAULT 'confirmed',
    Payment_Status VARCHAR(20) DEFAULT 'pending',
    Booking_Time DATETIME DEFAULT CURRENT_TIMESTAMP,
    Cancelled_At DATETIME,
    Refund_Amount DECIMAL(10,2)
);

-- Passengers Table
CREATE TABLE Passengers (
    ROWID BIGINT PRIMARY KEY AUTO_INCREMENT,
    Booking_ID BIGINT REFERENCES Bookings(ROWID),
    Passenger_Name VARCHAR(255) NOT NULL,
    Age INT,
    Gender VARCHAR(10),
    Current_Status VARCHAR(50),
    Coach VARCHAR(10),
    Seat_Number VARCHAR(10),
    Berth_Type VARCHAR(20)
);
```

---

## 6. Code Templates

### 6.1 Base Repository Template

```python
# core/base_repository.py

from typing import List, Dict, Any, Optional
from core.database import db

class BaseRepository:
    """Base class for all repositories with common CRUD operations."""

    table_name: str = None  # Override in child class

    def __init__(self):
        if not self.table_name:
            raise ValueError("table_name must be defined")

    def get_all(self, limit: int = 200, offset: int = 0) -> List[Dict]:
        """Get all records with pagination."""
        query = f"SELECT * FROM {self.table_name} LIMIT {limit} OFFSET {offset}"
        return db.execute_query(query)

    def get_by_id(self, row_id: int) -> Optional[Dict]:
        """Get record by ROWID."""
        return db.get_by_id(self.table_name, row_id)

    def create(self, data: Dict[str, Any]) -> Dict:
        """Create a new record."""
        return db.insert(self.table_name, data)

    def update(self, row_id: int, data: Dict[str, Any]) -> Dict:
        """Update a record."""
        return db.update(self.table_name, row_id, data)

    def delete(self, row_id: int) -> bool:
        """Delete a record."""
        return db.delete(self.table_name, row_id)

    def find_by(self, field: str, value: Any) -> List[Dict]:
        """Find records by field value."""
        query = f"SELECT * FROM {self.table_name} WHERE {field} = '{value}'"
        return db.execute_query(query)

    def count(self, criteria: str = None) -> int:
        """Count records with optional criteria."""
        query = f"SELECT COUNT(*) as count FROM {self.table_name}"
        if criteria:
            query += f" WHERE {criteria}"
        result = db.execute_query(query)
        return result[0]['count'] if result else 0
```

### 6.2 Module Repository Template

```python
# modules/stations/repository.py

from typing import List, Dict, Optional
from core.base_repository import BaseRepository
from core.database import db

class StationRepository(BaseRepository):
    """Repository for Station data access."""

    table_name = "Stations"

    def get_by_code(self, station_code: str) -> Optional[Dict]:
        """Get station by code."""
        query = f"SELECT * FROM {self.table_name} WHERE Station_Code = '{station_code.upper()}'"
        results = db.execute_query(query)
        return results[0] if results else None

    def search(self, search_term: str, limit: int = 50) -> List[Dict]:
        """Search stations by code or name."""
        term = search_term.upper()
        query = f"""
            SELECT * FROM {self.table_name}
            WHERE Station_Code LIKE '%{term}%'
               OR Station_Name LIKE '%{term}%'
            LIMIT {limit}
        """
        return db.execute_query(query)

    def get_active(self) -> List[Dict]:
        """Get all active stations."""
        query = f"SELECT * FROM {self.table_name} WHERE Is_Active = true ORDER BY Station_Name"
        return db.execute_query(query)

    def get_by_state(self, state: str) -> List[Dict]:
        """Get stations by state."""
        query = f"SELECT * FROM {self.table_name} WHERE State = '{state}' AND Is_Active = true"
        return db.execute_query(query)


# Singleton instance
station_repo = StationRepository()
```

### 6.3 Module Service Template

```python
# modules/stations/services.py

from typing import List, Dict, Optional
from core.exceptions import ValidationError, NotFoundError
from modules.stations.repository import station_repo
from modules.admin_logs.services import log_admin_action

class StationService:
    """Business logic for Station management."""

    def __init__(self):
        self.repo = station_repo

    def get_all(self, search: str = None, state: str = None) -> List[Dict]:
        """Get stations with optional filters."""
        if search:
            return self.repo.search(search)
        if state:
            return self.repo.get_by_state(state)
        return self.repo.get_active()

    def get_by_id(self, station_id: int) -> Dict:
        """Get station by ID."""
        station = self.repo.get_by_id(station_id)
        if not station:
            raise NotFoundError(f"Station {station_id} not found")
        return station

    def get_by_code(self, code: str) -> Dict:
        """Get station by code."""
        station = self.repo.get_by_code(code)
        if not station:
            raise NotFoundError(f"Station with code {code} not found")
        return station

    def create(self, data: Dict, admin_email: str) -> Dict:
        """Create a new station."""
        # Validation
        if not data.get('Station_Code'):
            raise ValidationError("Station_Code is required")
        if not data.get('Station_Name'):
            raise ValidationError("Station_Name is required")

        # Check duplicate
        existing = self.repo.get_by_code(data['Station_Code'])
        if existing:
            raise ValidationError(f"Station with code {data['Station_Code']} already exists")

        # Normalize
        data['Station_Code'] = data['Station_Code'].upper().strip()
        data['Station_Name'] = data['Station_Name'].strip()
        data['Is_Active'] = data.get('Is_Active', True)

        # Create
        result = self.repo.create(data)

        # Audit log
        log_admin_action(admin_email, "CREATE", "Station", result.get('ROWID'), new_value=str(data))

        return result

    def update(self, station_id: int, data: Dict, admin_email: str) -> Dict:
        """Update a station."""
        # Verify exists
        old_station = self.get_by_id(station_id)

        # Update
        if 'Station_Code' in data:
            data['Station_Code'] = data['Station_Code'].upper().strip()

        result = self.repo.update(station_id, data)

        # Audit log
        log_admin_action(admin_email, "UPDATE", "Station", station_id,
                        old_value=str(old_station), new_value=str(data))

        return result

    def delete(self, station_id: int, admin_email: str) -> bool:
        """Delete a station."""
        station = self.get_by_id(station_id)

        result = self.repo.delete(station_id)

        # Audit log
        log_admin_action(admin_email, "DELETE", "Station", station_id, old_value=str(station))

        return result


# Singleton instance
station_service = StationService()
```

### 6.4 Module Routes Template

```python
# modules/stations/routes.py

from flask import Blueprint, jsonify, request
from core.security import require_auth, require_admin
from core.exceptions import ValidationError, NotFoundError
from modules.stations.services import station_service

stations_bp = Blueprint('stations', __name__, url_prefix='/api/stations')


@stations_bp.route('', methods=['GET'])
def get_stations():
    """GET /api/stations - List all stations."""
    try:
        search = request.args.get('search', '').strip()
        state = request.args.get('state', '').strip()

        stations = station_service.get_all(search=search, state=state)

        return jsonify({
            'success': True,
            'data': stations,
            'count': len(stations)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@stations_bp.route('/<int:station_id>', methods=['GET'])
def get_station(station_id: int):
    """GET /api/stations/{id} - Get single station."""
    try:
        station = station_service.get_by_id(station_id)
        return jsonify({'success': True, 'data': station}), 200

    except NotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@stations_bp.route('/code/<string:code>', methods=['GET'])
def get_station_by_code(code: str):
    """GET /api/stations/code/{code} - Get station by code."""
    try:
        station = station_service.get_by_code(code)
        return jsonify({'success': True, 'data': station}), 200

    except NotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@stations_bp.route('', methods=['POST'])
@require_admin
def create_station():
    """POST /api/stations - Create new station (Admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        admin_email = request.headers.get('X-User-Email', 'unknown')
        station = station_service.create(data, admin_email)

        return jsonify({'success': True, 'data': station}), 201

    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@stations_bp.route('/<int:station_id>', methods=['PUT'])
@require_admin
def update_station(station_id: int):
    """PUT /api/stations/{id} - Update station (Admin only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        admin_email = request.headers.get('X-User-Email', 'unknown')
        station = station_service.update(station_id, data, admin_email)

        return jsonify({'success': True, 'data': station}), 200

    except NotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except ValidationError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@stations_bp.route('/<int:station_id>', methods=['DELETE'])
@require_admin
def delete_station(station_id: int):
    """DELETE /api/stations/{id} - Delete station (Admin only)."""
    try:
        admin_email = request.headers.get('X-User-Email', 'unknown')
        station_service.delete(station_id, admin_email)

        return jsonify({'success': True, 'message': 'Station deleted'}), 200

    except NotFoundError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

### 6.5 Module Init Template

```python
# modules/stations/__init__.py

from modules.stations.routes import stations_bp
from modules.stations.services import station_service
from modules.stations.repository import station_repo

__all__ = ['stations_bp', 'station_service', 'station_repo']
```

### 6.6 Main App Template

```python
# app.py

from flask import Flask
from flask_cors import CORS

def create_app():
    """Application factory."""
    app = Flask(__name__)

    # Configuration
    app.config.from_object('config.Config')

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints from modules
    from modules.auth.routes import auth_bp
    from modules.stations.routes import stations_bp
    from modules.trains.routes import trains_bp
    from modules.train_routes.routes import train_routes_bp
    from modules.fares.routes import fares_bp
    from modules.quotas.routes import quotas_bp
    from modules.inventory.routes import inventory_bp
    from modules.bookings.routes import bookings_bp
    from modules.announcements.routes import announcements_bp
    from modules.admin_logs.routes import admin_logs_bp
    from modules.reports.routes import reports_bp
    from modules.settings.routes import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(stations_bp)
    app.register_blueprint(trains_bp)
    app.register_blueprint(train_routes_bp)
    app.register_blueprint(fares_bp)
    app.register_blueprint(quotas_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(announcements_bp)
    app.register_blueprint(admin_logs_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)

    # Health check
    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    return app


# For Catalyst
app = create_app()

def handler(request, response):
    """Catalyst function handler."""
    return app(request.environ, response.start_response)
```

---

## 7. Testing Strategy

### 7.1 Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── test_core/
│   ├── test_database.py
│   └── test_security.py
├── test_modules/
│   ├── test_auth.py
│   ├── test_stations.py
│   ├── test_trains.py
│   ├── test_bookings.py
│   └── ...
└── test_integration/
    └── test_booking_flow.py
```

### 7.2 Test Template

```python
# tests/test_modules/test_stations.py

import pytest
from modules.stations.services import station_service
from core.exceptions import ValidationError, NotFoundError


class TestStationService:
    """Tests for StationService."""

    def test_create_station_success(self):
        """Test successful station creation."""
        data = {
            'Station_Code': 'TEST',
            'Station_Name': 'Test Station',
            'City': 'Test City',
            'State': 'Test State'
        }
        result = station_service.create(data, 'admin@test.com')

        assert result is not None
        assert result['Station_Code'] == 'TEST'

    def test_create_station_missing_code(self):
        """Test station creation without code fails."""
        data = {'Station_Name': 'Test Station'}

        with pytest.raises(ValidationError):
            station_service.create(data, 'admin@test.com')

    def test_get_station_not_found(self):
        """Test getting non-existent station."""
        with pytest.raises(NotFoundError):
            station_service.get_by_id(999999)

    def test_search_stations(self):
        """Test station search."""
        stations = station_service.get_all(search='MAS')
        assert isinstance(stations, list)
```

---

## 8. Summary Checklist

### Pre-Development
- [ ] Set up Catalyst project
- [ ] Create CloudScale database
- [ ] Configure environment variables
- [ ] Set up development environment

### Phase 1: Foundation
- [ ] core/database.py
- [ ] core/exceptions.py
- [ ] core/security.py
- [ ] core/base_repository.py
- [ ] shared/validators.py
- [ ] shared/date_helpers.py
- [ ] app.py

### Phase 2: Master Data
- [ ] modules/auth/
- [ ] modules/stations/
- [ ] modules/trains/
- [ ] modules/train_routes/
- [ ] modules/coach_layouts/

### Phase 3: Business Logic
- [ ] modules/fares/
- [ ] modules/quotas/
- [ ] modules/inventory/

### Phase 4: Transactions
- [ ] modules/bookings/
- [ ] modules/passengers/

### Phase 5: Support
- [ ] modules/announcements/
- [ ] modules/admin_logs/
- [ ] modules/reports/
- [ ] modules/settings/

### Post-Development
- [ ] Integration testing
- [ ] Performance testing
- [ ] Documentation
- [ ] Deployment

---

*Document Version: 1.0*
*Generated: 2026-03-25*

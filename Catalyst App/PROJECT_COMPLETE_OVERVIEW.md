# Railway Ticketing System - Complete Project Overview
## Version 2.0 | Flask + Zoho Creator Backend

---

## Table of Contents
1. [Client Requirements & Goals](#1-client-requirements--goals)
2. [System Architecture](#2-system-architecture)
3. [Module Breakdown](#3-module-breakdown)
4. [Database Schema (15 Tables)](#4-database-schema-15-tables)
5. [Module-to-Database Mapping](#5-module-to-database-mapping)
6. [Data Flow Diagrams](#6-data-flow-diagrams)
7. [API Endpoints Reference](#7-api-endpoints-reference)
8. [Configuration & Environment](#8-configuration--environment)

---

## 1. Client Requirements & Goals

### 1.1 Project Objective
Build a full-featured railway ticket booking platform (similar to IRCTC) with:
- Real-time train search and seat availability
- End-to-end booking workflow with PNR tracking
- AI-powered conversational booking assistant
- Admin panel for operations management

### 1.2 Functional Requirements

| Category | Requirement | Priority |
|----------|-------------|----------|
| **User Management** | Registration, JWT login, password reset, role-based access | High |
| **Train Search** | Search by stations, dates, class; filter by train type | High |
| **Seat Availability** | Real-time inventory check across classes/quotas | High |
| **Booking** | Multi-passenger booking, PNR generation, seat allocation | High |
| **Cancellation** | Full/partial cancellation with refund calculation | High |
| **Waitlist** | RAC/WL management with auto-promotion | Medium |
| **Fare Calculation** | Base fare + surcharges + concessions + GST | High |
| **AI Assistant** | Natural language search, conversational booking | Medium |
| **Admin Panel** | Train/station CRUD, fare management, quota control | High |
| **Analytics** | Dashboard, trends, revenue reports | Medium |
| **Announcements** | System alerts, train-specific notices | Low |
| **Audit Trail** | Admin activity logging | Medium |

### 1.3 Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Scalability | 1M+ users, 10M+ bookings |
| Booking Window | 120 days advance booking |
| Tatkal Opening | 10:00 AM, day before journey |
| Max Passengers | 6 per booking |
| Response Time | < 2 seconds for search |
| Availability | 99.9% uptime |
| Platform | Python 3.9, Zoho Catalyst deployment |

### 1.4 Technology Stack

| Layer | Technology |
|-------|------------|
| Backend Framework | Flask 2.3.2 |
| Runtime | Python 3.9 |
| WSGI Server | Gunicorn |
| Database | Zoho Creator (Forms/Reports) |
| Cache | In-memory (CacheManager with TTL) |
| Authentication | JWT (PyJWT) + bcrypt/SHA-256 |
| AI/ML | Gemini API, Claude, Zoho Catalyst QuickML |
| Deployment | Zoho Catalyst AppSail |

---

## 2. System Architecture

### 2.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                     │
│           React Frontend / Mobile App / Third-Party APIs                 │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTP/JSON
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER (Routes)                         │
│  ┌──────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌────┐ ┌─────────┐ ┌───────┐  │
│  │ Auth │ │Trains│ │Bookings│ │Stations│ │ AI │ │Analytics│ │ Admin │  │
│  └──┬───┘ └──┬───┘ └───┬────┘ └───┬────┘ └─┬──┘ └────┬────┘ └───┬───┘  │
└─────┼────────┼─────────┼──────────┼────────┼─────────┼──────────┼──────┘
      │        │         │          │        │         │          │
      ▼        ▼         ▼          ▼        ▼         ▼          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        SERVICE LAYER (Business Logic)                    │
│  ┌───────────────┐ ┌────────────────┐ ┌─────────────────┐               │
│  │  UserService  │ │ BookingService │ │ AnalyticsService│               │
│  │  • register   │ │ • create       │ │ • overview      │               │
│  │  • login      │ │ • cancel       │ │ • trends        │               │
│  │  • resetPwd   │ │ • allocateSeat │ │ • revenue       │               │
│  └───────┬───────┘ └───────┬────────┘ └────────┬────────┘               │
│          │                 │                   │                         │
│  ┌───────┴─────────────────┴───────────────────┴────────┐               │
│  │               SchemaDiscovery (MCP/AI)               │               │
│  │  • discoverSchemas  • buildMCPPrompt  • executeQuery │               │
│  └──────────────────────────┬───────────────────────────┘               │
└─────────────────────────────┼───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      REPOSITORY LAYER (Data Access)                      │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      ZohoRepository                              │    │
│  │  • get_records(form, criteria, pagination)                       │    │
│  │  • create_record(form, data)                                     │    │
│  │  • update_record(form, id, data)                                 │    │
│  │  • delete_record(form, id)                                       │    │
│  │  • build_criteria(filters) → Zoho criteria syntax                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────┐  ┌────────────────────┐                        │
│  │    CacheManager     │  │  ZohoTokenManager  │                        │
│  │  • get/set (TTL)    │  │  • OAuth refresh   │                        │
│  │  • invalidate       │  │  • scope handling  │                        │
│  └─────────────────────┘  └────────────────────┘                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTPS/REST
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       DATA LAYER (Zoho Creator)                          │
│                                                                          │
│   ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐        │
│   │  USERS  │ │ TRAINS  │ │ BOOKINGS │ │PASSENGERS│ │STATIONS │        │
│   └─────────┘ └─────────┘ └──────────┘ └──────────┘ └─────────┘        │
│   ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐        │
│   │  FARES  │ │ QUOTAS  │ │INVENTORY │ │ COACHES  │ │ ROUTES  │        │
│   └─────────┘ └─────────┘ └──────────┘ └──────────┘ └─────────┘        │
│   ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐        │
│   │SETTINGS │ │  LOGS   │ │ANNOUNCE  │ │ROUTE_STOP│ │PWD_RESET│        │
│   └─────────┘ └─────────┘ └──────────┘ └──────────┘ └─────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
Railway Project Backend/
├── Backend/
│   └── appsail-python/
│       ├── app.py                    # Flask entry point
│       ├── config.py                 # Environment configuration
│       ├── requirements.txt          # Python dependencies
│       ├── gunicorn.conf.py          # WSGI server config
│       ├── core/
│       │   ├── __init__.py
│       │   ├── security.py           # JWT, bcrypt, decorators
│       │   └── exceptions.py         # Custom exceptions
│       ├── services/
│       │   ├── __init__.py
│       │   ├── user_service.py       # Auth business logic
│       │   ├── booking_service.py    # Booking business logic
│       │   ├── analytics_service.py  # Dashboard metrics
│       │   ├── schema_discovery.py   # MCP schema discovery
│       │   └── zoho_token_manager.py # OAuth token handling
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── zoho_repository.py    # Zoho Creator API client
│       │   └── cache_manager.py      # TTL cache implementation
│       ├── routes/
│       │   ├── __init__.py           # Blueprint registration
│       │   ├── auth.py               # /api/auth/*
│       │   ├── trains.py             # /api/trains/*
│       │   ├── bookings.py           # /api/bookings/*
│       │   ├── stations.py           # /api/stations/*
│       │   ├── users.py              # /api/users/*
│       │   ├── fares.py              # /api/fares/*
│       │   ├── quotas.py             # /api/quotas/*
│       │   ├── inventory.py          # /api/inventory/*
│       │   ├── coaches.py            # /api/coaches/*
│       │   ├── coach_layouts.py      # /api/coach-layouts/*
│       │   ├── train_routes.py       # /api/train-routes/*
│       │   ├── announcements.py      # /api/announcements/*
│       │   ├── settings.py           # /api/settings/*
│       │   ├── admin_logs.py         # /api/admin/logs/*
│       │   ├── admin_reports.py      # /api/admin/reports/*
│       │   ├── overview.py           # /api/overview/*
│       │   └── ai_routes.py          # /api/ai/*
│       └── ai/
│           ├── __init__.py
│           ├── nlp_search.py         # Natural language → criteria
│           ├── booking_conversation.py
│           ├── booking_prompts.py
│           ├── claude_agent.py
│           ├── gemini_agent.py
│           └── qwen_client.py
├── Frontend/
│   └── fixed_frontend/               # React 18 + Vite
└── Catalyst App/
    └── functions/
        └── catalyst_backend/         # Catalyst deployment
```

---

## 3. Module Breakdown

### 3.1 Module Summary

| # | Module | Route Prefix | Service | Primary Tables |
|---|--------|--------------|---------|----------------|
| 1 | Authentication | `/api/auth` | UserService | Users, Password_Reset_Tokens |
| 2 | Trains | `/api/trains` | ZohoRepository | Trains, Train_Routes, Route_Stops |
| 3 | Bookings | `/api/bookings` | BookingService | Bookings, Passengers, Train_Inventory |
| 4 | Stations | `/api/stations` | ZohoRepository | Stations |
| 5 | Users | `/api/users` | UserService | Users |
| 6 | Fares | `/api/fares` | ZohoRepository | Fares |
| 7 | Quotas | `/api/quotas` | ZohoRepository | Quotas |
| 8 | Inventory | `/api/inventory` | ZohoRepository | Train_Inventory |
| 9 | Coaches | `/api/coaches`, `/api/coach-layouts` | ZohoRepository | Coach_Layouts |
| 10 | Train Routes | `/api/train-routes` | ZohoRepository | Train_Routes, Route_Stops |
| 11 | Announcements | `/api/announcements` | ZohoRepository | Announcements |
| 12 | Settings | `/api/settings` | ZohoRepository | Settings |
| 13 | Admin Logs | `/api/admin/logs` | ZohoRepository | Admin_Logs |
| 14 | Admin Reports | `/api/admin/reports` | AnalyticsService | Bookings, Trains, Users |
| 15 | Analytics | `/api/analytics` | AnalyticsService | Bookings, Trains, Users |
| 16 | AI Assistant | `/api/ai` | NLP/Claude/Gemini | All queryable tables |

### 3.2 Module Details

#### Module 1: Authentication
**Purpose:** User registration, login, password management, JWT token handling

**Endpoints:**
| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| POST | `/api/auth/register` | Register new user | 10/hour |
| POST | `/api/auth/login` | Login, returns JWT | 10/15min |
| POST | `/api/auth/refresh` | Refresh JWT token | - |
| POST | `/api/auth/logout` | Revoke token (stub) | - |
| POST | `/api/auth/change-password` | Change password | - |
| POST | `/api/auth/forgot-password` | Request OTP | 5/15min |
| POST | `/api/auth/reset-password` | Reset with OTP | - |
| POST | `/api/auth/setup-admin` | Setup admin account | Setup key |
| GET | `/api/test/token` | Verify auth status | - |

**Business Rules:**
- Password: SHA-256 hashed (legacy) or bcrypt (new)
- JWT expiry: 24 hours (access), 7 days (refresh)
- OTP expiry: 15 minutes
- Admin detection: Email domain matching

---

#### Module 2: Trains
**Purpose:** Train master data, search, schedule, availability, running status

**Endpoints:**
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/trains` | Search/list trains | Public |
| POST | `/api/trains` | Create train | Admin |
| GET | `/api/trains/{id}` | Get train details | Public |
| PUT | `/api/trains/{id}` | Update train | Admin |
| DELETE | `/api/trains/{id}` | Delete train | Admin |
| GET | `/api/trains/{id}/schedule` | Get route stops | Public |
| GET | `/api/trains/{id}/vacancy` | Seat availability | Public |
| GET | `/api/trains/{id}/running-status` | Running status | Public |
| PUT | `/api/trains/{id}/running-status` | Update status | Admin |
| POST | `/api/trains/{id}/cancel-on-date` | Cancel train | Admin |
| POST | `/api/trains/bulk` | Bulk create | Admin |
| GET | `/api/trains/connecting` | Find connecting trains | Public |
| GET | `/api/trains/search-by-station` | Search by station | Public |

**Search Parameters:**
- `from_station`, `to_station`: Station codes
- `date`: Journey date (dd-MMM-yyyy)
- `class`: SL, 3A, 2A, 1A, CC, EC, 2S
- `train_type`: EXPRESS, SUPERFAST, RAJDHANI, SHATABDI
- `page`, `limit`: Pagination

---

#### Module 3: Bookings
**Purpose:** Ticket booking, cancellation, PNR status, seat allocation

**Endpoints:**
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/bookings` | List user bookings | User |
| POST | `/api/bookings` | Create booking | User |
| GET | `/api/bookings/{id}` | Get booking details | User |
| PUT | `/api/bookings/{id}` | Update booking | Admin |
| DELETE | `/api/bookings/{id}` | Delete booking | Admin |
| GET | `/api/bookings/pnr/{pnr}` | PNR lookup | Public |
| POST | `/api/bookings/{id}/confirm` | Confirm booking | Admin |
| POST | `/api/bookings/{id}/pay` | Mark as paid | Admin |
| POST | `/api/bookings/{id}/cancel` | Cancel booking | User |
| POST | `/api/bookings/{id}/partial-cancel` | Cancel passengers | User |
| GET | `/api/bookings/{id}/ticket` | Get ticket | User |
| GET | `/api/bookings/chart` | Reservation chart | Admin |
| GET | `/api/bookings/stream` | SSE live updates | User |

**Booking Request:**
```json
{
  "train_id": "123456789",
  "journey_date": "25-Apr-2026",
  "class": "3A",
  "quota": "GN",
  "boarding_station": "MAS",
  "deboarding_station": "NDLS",
  "passengers": [
    {
      "name": "John Doe",
      "age": 30,
      "gender": "Male",
      "berth_preference": "Lower"
    }
  ]
}
```

**Cancellation Policy:**
| Hours Before | Deduction |
|--------------|-----------|
| > 48 hours | 25% (min ₹50) |
| 48-12 hours | 25% |
| 12-4 hours | 50% |
| < 4 hours | 100% |
| Tatkal | No refund |

---

#### Module 4: AI Assistant
**Purpose:** NLP search, conversational booking, recommendations

**Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ai/qwen` | Catalyst QuickML proxy |
| POST | `/api/ai/search` | NLP → Zoho criteria |
| POST | `/api/ai/chat` | Conversational assistant |
| GET | `/api/ai/recommendations` | Personalized suggestions |
| POST | `/api/ai/analyze` | Analytics insights |
| GET | `/api/ai/predict-availability` | Availability prediction |
| POST | `/api/ai/agent` | Intent-based routing |
| POST | `/api/ai/mcp-query` | MCP query execution |
| GET | `/api/ai/schema` | Schema discovery |
| GET | `/api/ai/schema/modules` | Queryable modules |

**NLP Search Examples:**
```
"trains from Chennai to Delhi tomorrow"
  → (From_Station.Station_Code == "MAS") && (To_Station.Station_Code == "NDLS")

"Rajdhani trains with 2AC availability"
  → (Train_Type == "RAJDHANI") && (Available_Seats_2A > 0)
```

---

## 4. Database Schema (15 Tables)

### 4.1 Entity-Relationship Diagram

```
                              ┌──────────────────┐
                              │     STATIONS     │
                              │──────────────────│
                              │ ID (PK)          │
                              │ Station_Code (UK)│◄─────────────────────────────┐
                              │ Station_Name     │                              │
                              │ City             │                              │
                              │ State            │                              │
                              │ Zone             │                              │
                              │ Division         │                              │
                              │ Station_Type     │                              │
                              │ Number_of_Platforms                             │
                              │ Latitude         │                              │
                              │ Longitude        │                              │
                              │ Is_Active        │                              │
                              └────────┬─────────┘                              │
                                       │                                        │
         ┌─────────────────────────────┼────────────────────────────┐          │
         │                             │                            │          │
         ▼                             ▼                            ▼          │
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐  │
│     TRAINS      │          │      FARES      │          │  ANNOUNCEMENTS  │  │
│─────────────────│          │─────────────────│          │─────────────────│  │
│ ID (PK)         │          │ ID (PK)         │          │ ID (PK)         │  │
│ Train_Number(UK)│          │ Train (FK)      │          │ Title           │  │
│ Train_Name      │          │ From_Station(FK)│──────────│ Message         │  │
│ Train_Type      │          │ To_Station (FK) │          │ Priority        │  │
│ From_Station(FK)│──────────│ Class           │          │ Trains (FK)     │  │
│ To_Station (FK) │          │ Base_Fare       │          │ Stations (FK)───┼──┤
│ Departure_Time  │          │ Dynamic_Fare    │          │ Start_Date      │  │
│ Arrival_Time    │          │ Distance_KM     │          │ End_Date        │  │
│ Duration        │          │ Concession_Type │          │ Is_Active       │  │
│ Distance        │          │ Concession_%    │          │ Created_By (FK) │  │
│ Run_Days        │          │ Effective_From  │          └─────────────────┘  │
│ Is_Active       │          │ Effective_To    │                               │
│ Pantry_Car      │          │ Is_Active       │                               │
│ ─── Fares ───   │          └─────────────────┘                               │
│ Fare_SL         │                                                            │
│ Fare_3A         │                                                            │
│ Fare_2A         │                                                            │
│ Fare_1A         │                                                            │
│ Fare_CC         │                                                            │
│ Fare_EC         │                                                            │
│ Fare_2S         │                                                            │
│ ─── Seats ───   │                                                            │
│ Total_Seats_SL  │                                                            │
│ Total_Seats_3A  │                                                            │
│ Total_Seats_2A  │                                                            │
│ Total_Seats_1A  │                                                            │
│ Total_Seats_CC  │                                                            │
│ Avail_Seats_SL  │                                                            │
│ Avail_Seats_3A  │                                                            │
│ Avail_Seats_2A  │                                                            │
│ Avail_Seats_1A  │                                                            │
│ Avail_Seats_CC  │                                                            │
│ ─── Status ──── │                                                            │
│ Running_Status  │                                                            │
│ Delay_Minutes   │                                                            │
│ Expected_Dep    │                                                            │
└────────┬────────┘                                                            │
         │                                                                     │
         │  ┌───────────────┬──────────────┬─────────────┐                    │
         │  │               │              │             │                    │
         ▼  ▼               ▼              ▼             ▼                    │
┌───────────────┐  ┌───────────────┐  ┌─────────┐  ┌────────────┐            │
│ TRAIN_ROUTES  │  │TRAIN_INVENTORY│  │ QUOTAS  │  │COACH_LAYOUTS│            │
│───────────────│  │───────────────│  │─────────│  │────────────│            │
│ ID (PK)       │  │ ID (PK)       │  │ ID (PK) │  │ ID (PK)    │            │
│ Train (FK)    │  │ Train (FK)    │  │Train(FK)│  │ Class_Code │            │
│ Notes         │  │ Journey_Date  │  │ Class   │  │ Class_Name │            │
└───────┬───────┘  │ Class         │  │Quota_Type│ │Coach_Prefix│            │
        │          │ Total_Seats   │  │Quota_Code│ │Total_Berths│            │
        ▼          │ Available     │  │Total_Seats││Berth_Cycle │            │
┌───────────────┐  │ Booked        │  │Available  ││Layout_JSON │            │
│  ROUTE_STOPS  │  │ RAC_Count     │  │Booking_   ││ Is_AC      │            │
│───────────────│  │ Waitlist_Count│  │  Opens    ││ Is_Active  │            │
│ ID (PK)       │  │ Last_Updated  │  │ Is_Active │└────────────┘            │
│Train_Routes(FK)│ └───────────────┘  └─────────┘                            │
│ Sequence      │                                                             │
│ Station_Name  │                                                             │
│ Station_Code  │                                                             │
│ Stations (FK) │─────────────────────────────────────────────────────────────┘
│ Arrival_Time  │
│ Departure_Time│
│ Halt_Minutes  │
│ Distance_KM   │
│ Day_Count     │
│ Platform      │
└───────────────┘


┌─────────────────┐
│      USERS      │
│─────────────────│
│ ID (PK)         │
│ Full_Name       │
│ Email (UK)      │◄─────────────────────────────────────────┐
│ Password        │                                          │
│ Phone_Number    │                                          │
│ Role            │                                          │
│ Account_Status  │                                          │
│ Aadhar_Verified │                                          │
│ Date_of_Birth   │                                          │
│ ID_Proof_Type   │                                          │
│ ID_Proof_Number │                                          │
│ Address         │                                          │
│ Last_Login      │                                          │
└────────┬────────┘                                          │
         │                                                   │
         │  ┌──────────────────────┐                        │
         │  │                      │                        │
         ▼  ▼                      ▼                        │
┌────────────────┐       ┌─────────────────┐      ┌─────────────────────┐
│   ADMIN_LOGS   │       │    BOOKINGS     │      │ PASSWORD_RESET_TOKENS│
│────────────────│       │─────────────────│      │─────────────────────│
│ ID (PK)        │       │ ID (PK)         │      │ ID (PK)             │
│ Admin_User(FK) │       │ PNR (UK)        │      │ User_Email          │
│ Action         │       │ Users (FK)      │──────│ OTP                 │
│ Resource_Type  │       │ Trains (FK)     │      │ Expires_At          │
│ Resource_ID    │       │ Journey_Date    │      │ Is_Used             │
│ Old_Value      │       │ Class           │      └─────────────────────┘
│ New_Value      │       │ Quota           │
│ IP_Address     │       │ Num_Passengers  │      ┌─────────────────┐
│ User_Agent     │       │ Passengers(JSON)│      │    SETTINGS     │
│ Status         │       │ Total_Fare      │      │─────────────────│
└────────────────┘       │ Booking_Status  │      │ ID (PK)         │
                         │ Payment_Status  │      │ Setting_Key(UK) │
                         │ Payment_Method  │      │ Setting_Value   │
                         │ Boarding_Stn(FK)│      │ Setting_Type    │
                         │ Deboarding(FK)  │      │ Description     │
                         │ Booking_Time    │      │ Is_System       │
                         │ Cancel_Time     │      │ Updated_By (FK) │
                         │ Refund_Amount   │      └─────────────────┘
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   PASSENGERS    │
                         │─────────────────│
                         │ ID (PK)         │
                         │ Booking (FK)    │
                         │ Passenger_Name  │
                         │ Age             │
                         │ Gender          │
                         │ Is_Child        │
                         │ Berth_Preference│
                         │ Coach           │
                         │ Seat_Number     │
                         │ Berth_Type      │
                         │ Current_Status  │
                         │ Cancelled       │
                         └─────────────────┘
```

### 4.2 Table Definitions

---

#### TABLE 1: USERS
**Purpose:** User accounts and authentication

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Full_Name | VARCHAR(255) | Yes | - | User's full name |
| Email | VARCHAR(255) | Yes | Yes | Login email (lowercase) |
| Password | VARCHAR(512) | Yes | - | SHA-256 or bcrypt hashed |
| Phone_Number | VARCHAR(20) | - | - | Contact phone |
| Role | ENUM | - | - | 'Admin' \| 'User' (default: User) |
| Account_Status | ENUM | - | - | 'Active' \| 'Blocked' \| 'Suspended' |
| Aadhar_Verified | VARCHAR(10) | - | - | 'true' \| 'false' |
| Date_of_Birth | DATE | - | - | User DOB (dd-MMM-yyyy) |
| ID_Proof_Type | VARCHAR(50) | - | - | Aadhaar, PAN, Passport |
| ID_Proof_Number | VARCHAR(50) | - | - | ID document number |
| Address | TEXT | - | - | User address |
| Last_Login | DATETIME | - | - | Last login timestamp |
| Created_Time | DATETIME | Auto | - | Record creation time |
| Modified_Time | DATETIME | Auto | - | Last modification time |

**Indexes:**
- `idx_users_email` UNIQUE (Email)
- `idx_users_role` (Role)
- `idx_users_status` (Account_Status)

---

#### TABLE 2: STATIONS
**Purpose:** Railway station master data

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Station_Code | VARCHAR(10) | Yes | Yes | 3-5 char code (MAS, NDLS) |
| Station_Name | VARCHAR(255) | Yes | - | Full station name |
| City | VARCHAR(100) | Yes | - | City name |
| State | VARCHAR(100) | Yes | - | State/Province |
| Zone | VARCHAR(50) | - | - | Railway zone (SR, NR) |
| Division | VARCHAR(100) | - | - | Railway division |
| Station_Type | VARCHAR(50) | - | - | Junction, Terminal |
| Number_of_Platforms | INT | - | - | Platform count |
| Latitude | DOUBLE | - | - | GPS latitude |
| Longitude | DOUBLE | - | - | GPS longitude |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_stations_code` UNIQUE (Station_Code)
- `idx_stations_city` (City)
- `idx_stations_state` (State)

---

#### TABLE 3: TRAINS
**Purpose:** Train master data with fares and seats

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train_Number | VARCHAR(10) | Yes | Yes | Unique train number |
| Train_Name | VARCHAR(255) | Yes | - | Train name |
| Train_Type | VARCHAR(50) | - | - | EXPRESS, SUPERFAST, RAJDHANI, SHATABDI |
| From_Station | LOOKUP | Yes | - | Source station (FK → Stations) |
| To_Station | LOOKUP | Yes | - | Destination station (FK → Stations) |
| Departure_Time | TIME | Yes | - | Departure from source (HH:MM) |
| Arrival_Time | TIME | Yes | - | Arrival at destination |
| Duration | VARCHAR(20) | - | - | Journey duration string |
| Distance | DECIMAL(10,2) | - | - | Total distance in km |
| Run_Days | VARCHAR(100) | - | - | Comma-separated: Mon,Wed,Fri |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Pantry_Car_Available | VARCHAR(10) | - | - | 'true' \| 'false' |
| **Fares by Class** |||||
| Fare_SL | DECIMAL(10,2) | - | - | Sleeper class fare |
| Fare_3A | DECIMAL(10,2) | - | - | 3rd AC fare |
| Fare_2A | DECIMAL(10,2) | - | - | 2nd AC fare |
| Fare_1A | DECIMAL(10,2) | - | - | 1st AC fare |
| Fare_CC | DECIMAL(10,2) | - | - | Chair Car fare |
| Fare_EC | DECIMAL(10,2) | - | - | Executive Chair fare |
| Fare_2S | DECIMAL(10,2) | - | - | Second Sitting fare |
| **Total Seats** |||||
| Total_Seats_SL | INT | - | - | Total Sleeper seats |
| Total_Seats_3A | INT | - | - | Total 3AC seats |
| Total_Seats_2A | INT | - | - | Total 2AC seats |
| Total_Seats_1A | INT | - | - | Total 1AC seats |
| Total_Seats_CC | INT | - | - | Total Chair Car seats |
| **Available Seats** |||||
| Available_Seats_SL | INT | - | - | Available Sleeper |
| Available_Seats_3A | INT | - | - | Available 3AC |
| Available_Seats_2A | INT | - | - | Available 2AC |
| Available_Seats_1A | INT | - | - | Available 1AC |
| Available_Seats_CC | INT | - | - | Available Chair Car |
| **Running Status** |||||
| Running_Status | VARCHAR(50) | - | - | 'On Time' \| 'Delayed' |
| Delay_Minutes | INT | - | - | Delay in minutes |
| Expected_Departure | DATETIME | - | - | Expected departure time |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_trains_number` UNIQUE (Train_Number)
- `idx_trains_route` (From_Station, To_Station)
- `idx_trains_active` (Is_Active)

---

#### TABLE 4: TRAIN_ROUTES
**Purpose:** Parent route record for each train

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | Yes | - | Train reference (FK → Trains) |
| Notes | TEXT | - | - | Route notes |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_routes_train` (Train)

---

#### TABLE 5: ROUTE_STOPS
**Purpose:** Intermediate stops for each train route

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train_Routes | LOOKUP | Yes | - | Parent route (FK → Train_Routes) |
| Sequence | INT | Yes | - | Stop order (1=origin) |
| Station_Name | VARCHAR(255) | Yes | - | Station name |
| Station_Code | VARCHAR(10) | - | - | IRCTC station code |
| Stations | LOOKUP | - | - | Station reference (FK → Stations) |
| Arrival_Time | TIME | - | - | Arrival time at stop |
| Departure_Time | TIME | - | - | Departure time from stop |
| Halt_Minutes | INT | - | - | Halt duration |
| Distance_KM | DECIMAL(10,2) | - | - | Distance from source |
| Day_Count | INT | - | - | Day number (1=same day) |
| Platform | INT | - | - | Platform number |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_stops_route_seq` (Train_Routes, Sequence)
- `idx_stops_station` (Station_Code)

---

#### TABLE 6: COACH_LAYOUTS
**Purpose:** Coach configuration by class type

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Class_Code | VARCHAR(10) | Yes | Yes | SL, 3A, 2A, 1A, CC, EC, 2S |
| Class_Name | VARCHAR(100) | Yes | - | Sleeper, 3rd AC, etc. |
| Coach_Prefix | VARCHAR(5) | - | - | S, B, A, H, C |
| Total_Berths | INT | Yes | - | Berths per coach |
| Berth_Cycle | INT | - | - | Berth numbering cycle |
| Layout_Pattern | JSON | - | - | Berth layout config |
| Is_AC | VARCHAR(10) | - | - | 'true' for AC classes |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Standard Configurations:**
| Class | Prefix | Berths/Coach | Berth Order |
|-------|--------|--------------|-------------|
| SL | S | 72 | Lower, Middle, Upper, Side Lower, Side Upper |
| 2S | D | 100 | Window, Middle, Aisle |
| 3A | B | 64 | Lower, Middle, Upper, Side Lower, Side Upper |
| 2A | A | 46 | Lower, Upper, Side Lower, Side Upper |
| 1A | H | 18 | Lower, Upper |
| CC | C | 78 | Window, Aisle, Middle |
| EC | E | 56 | Window, Aisle |

---

#### TABLE 7: TRAIN_INVENTORY
**Purpose:** Daily seat inventory per train/class

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | Yes | - | Train reference (FK → Trains) |
| Journey_Date | DATE | Yes | - | Date of journey |
| Class | VARCHAR(10) | Yes | - | SL, 3A, 2A, 1A, CC |
| Total_Seats | INT | Yes | - | Total capacity |
| Available_Seats | INT | Yes | - | Currently available |
| Booked_Seats | INT | - | - | Confirmed bookings |
| RAC_Count | INT | - | - | RAC passengers |
| Waitlist_Count | INT | - | - | Waitlisted passengers |
| Last_Updated | DATETIME | - | - | Last inventory update |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_inventory_train_date_class` UNIQUE (Train, Journey_Date, Class)

---

#### TABLE 8: FARES
**Purpose:** Fare rules between stations

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | - | - | Train reference (FK → Trains) |
| From_Station | LOOKUP | Yes | - | Source station (FK → Stations) |
| To_Station | LOOKUP | Yes | - | Destination (FK → Stations) |
| Class | VARCHAR(10) | Yes | - | SL, 3A, 2A, 1A, CC, EC |
| Base_Fare | DECIMAL(10,2) | Yes | - | Base fare amount |
| Dynamic_Fare | DECIMAL(10,2) | - | - | Dynamic pricing fare |
| Distance_KM | DECIMAL(10,2) | - | - | Distance between stations |
| Concession_Type | VARCHAR(50) | - | - | General, Senior, Student |
| Concession_Percent | DECIMAL(5,2) | - | - | Discount percentage |
| Effective_From | DATE | - | - | Fare start date |
| Effective_To | DATE | - | - | Fare end date |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Fare Calculation Formula:**
```
Total = Base_Fare
      + Reservation_Charge (₹15-₹60 by class)
      + Superfast_Surcharge (if applicable)
      + Tatkal_Premium (30% capped)
      - Concession_Discount
      + GST_5% (AC only)
      + Catering (optional)
      + Convenience_Fee (₹17.70-₹35.40)
```

---

#### TABLE 9: QUOTAS
**Purpose:** Seat quota distribution per train/class

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | Yes | - | Train reference (FK → Trains) |
| Class | VARCHAR(10) | Yes | - | SL, 3A, 2A, 1A, CC |
| Quota_Type | VARCHAR(50) | Yes | - | General, TQ, PT |
| Quota_Code | VARCHAR(10) | - | - | GN, TQ, PT, SS, LD |
| Total_Seats | INT | Yes | - | Total seats in quota |
| Available_Seats | INT | - | - | Currently available |
| Booking_Opens | TIME | - | - | 10:00 for Tatkal |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Standard Quota Types:**
| Code | Name | Opens |
|------|------|-------|
| GN | General | 120 days before |
| TQ | Tatkal | 10:00 AM, day before |
| PT | Premium Tatkal | 10:00 AM, day before |
| SS | Senior Citizen | 120 days before |
| LD | Ladies | 120 days before |
| HP | Handicapped | 120 days before |

---

#### TABLE 10: BOOKINGS
**Purpose:** Main booking records

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated ID |
| PNR | VARCHAR(20) | Yes | Yes | 10-char alphanumeric |
| Users | LOOKUP | Yes | - | User (FK → Users) |
| Trains | LOOKUP | Yes | - | Train (FK → Trains) |
| Journey_Date | DATE | Yes | - | Date (dd-MMM-yyyy) |
| Class | VARCHAR(10) | Yes | - | SL, 2S, 3A, 2A, 1A, CC, EC |
| Quota | VARCHAR(50) | - | - | GN, TQ, PT |
| Num_Passengers | INT | Yes | - | 1-6 passengers |
| Passengers | JSON | Yes | - | Passenger array |
| Total_Fare | DECIMAL(10,2) | Yes | - | Total amount |
| Booking_Status | ENUM | - | - | 'confirmed' \| 'waitlisted' \| 'cancelled' |
| Payment_Status | ENUM | - | - | 'pending' \| 'paid' |
| Payment_Method | VARCHAR(50) | - | - | UPI, Card, NetBanking |
| Boarding_Station | LOOKUP | - | - | FK → Stations |
| Deboarding_Station | LOOKUP | - | - | FK → Stations |
| Booking_Time | DATETIME | Auto | - | When booked |
| Cancellation_Time | DATETIME | - | - | When cancelled |
| Refund_Amount | DECIMAL(10,2) | - | - | Refund on cancel |
| Created_Time | DATETIME | Auto | - | Record creation |
| Modified_Time | DATETIME | Auto | - | Last modification |

**Passengers JSON Structure:**
```json
[
  {
    "Passenger_Name": "John Doe",
    "Age": 30,
    "Gender": "Male",
    "Is_Child": false,
    "Current_Status": "CNF/S1/14",
    "Coach": "S1",
    "Seat_Number": 14,
    "Berth": "Lower",
    "Cancelled": false
  }
]
```

**Indexes:**
- `idx_bookings_pnr` UNIQUE (PNR)
- `idx_bookings_user` (Users, Booking_Time)
- `idx_bookings_train_date` (Trains, Journey_Date)
- `idx_bookings_status` (Booking_Status)

---

#### TABLE 11: PASSENGERS
**Purpose:** Individual passenger records (alternative to JSON)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated ID |
| Booking | LOOKUP | Yes | - | FK → Bookings |
| Passenger_Name | VARCHAR(255) | Yes | - | Full name |
| Age | INT | Yes | - | Age in years |
| Gender | VARCHAR(10) | Yes | - | Male, Female, Other |
| Is_Child | VARCHAR(10) | - | - | 'true' if age < 5 |
| Berth_Preference | VARCHAR(50) | - | - | Lower, Upper, No Pref |
| Coach | VARCHAR(10) | - | - | S1, B2 |
| Seat_Number | INT | - | - | Seat/berth number |
| Berth_Type | VARCHAR(20) | - | - | Lower, Middle, Upper |
| Current_Status | VARCHAR(50) | - | - | CNF/S1/14, WL/5 |
| Cancelled | VARCHAR(10) | - | - | 'true' if cancelled |
| Created_Time | DATETIME | Auto | - | Record creation |

---

#### TABLE 12: ANNOUNCEMENTS
**Purpose:** System announcements and alerts

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated ID |
| Title | VARCHAR(500) | Yes | - | Announcement title |
| Message | TEXT | Yes | - | Full message |
| Priority | VARCHAR(20) | - | - | Low, Medium, High, Critical |
| Trains | LOOKUP | - | - | FK → Trains |
| Stations | LOOKUP | - | - | FK → Stations |
| Start_Date | DATETIME | - | - | Start time |
| End_Date | DATETIME | - | - | End time |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_By | LOOKUP | - | - | FK → Users |
| Created_Time | DATETIME | Auto | - | Record creation |

---

#### TABLE 13: ADMIN_LOGS
**Purpose:** Admin activity audit trail

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated ID |
| Admin_User | LOOKUP | Yes | - | FK → Users |
| Action | VARCHAR(100) | Yes | - | Action performed |
| Resource_Type | VARCHAR(50) | Yes | - | Train, Booking, User |
| Resource_ID | VARCHAR(50) | - | - | Affected resource ID |
| Old_Value | JSON | - | - | Previous value |
| New_Value | JSON | - | - | New value |
| IP_Address | VARCHAR(50) | - | - | Client IP |
| User_Agent | VARCHAR(500) | - | - | Browser/client info |
| Status | VARCHAR(20) | - | - | success, failure |
| Created_Time | DATETIME | Auto | - | Record creation |

---

#### TABLE 14: SETTINGS
**Purpose:** System configuration key-value store

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated ID |
| Setting_Key | VARCHAR(100) | Yes | Yes | Config key |
| Setting_Value | TEXT | Yes | - | Config value |
| Setting_Type | VARCHAR(20) | - | - | string, int, bool, json |
| Description | VARCHAR(500) | - | - | Setting description |
| Is_System | VARCHAR(10) | - | - | 'true' for system |
| Updated_By | LOOKUP | - | - | FK → Users |
| Created_Time | DATETIME | Auto | - | Record creation |
| Modified_Time | DATETIME | Auto | - | Last modification |

**Common Settings:**
| Key | Default | Description |
|-----|---------|-------------|
| booking_advance_days | 120 | Days in advance |
| max_passengers_per_booking | 6 | Max passengers |
| tatkal_open_hour | 10 | Tatkal opens at |
| maintenance_start | 23:45 | Maintenance start |
| maintenance_end | 00:15 | Maintenance end |

---

#### TABLE 15: PASSWORD_RESET_TOKENS
**Purpose:** Temporary OTP tokens for password reset

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated ID |
| User_Email | VARCHAR(255) | Yes | - | User email |
| OTP | VARCHAR(10) | Yes | - | 6-digit OTP |
| Expires_At | DATETIME | Yes | - | Expiry (15 min) |
| Is_Used | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation |

---

## 5. Module-to-Database Mapping

### 5.1 Read Operations Matrix

| Module | Tables Read | Query Pattern |
|--------|-------------|---------------|
| **Auth Login** | Users | Email exact match |
| **Auth Register** | Users | Email uniqueness check |
| **Password Reset** | Users, Password_Reset_Tokens | Email, OTP match |
| **Train Search** | Trains, Fares | From/To station filter |
| **Train Schedule** | Train_Routes, Route_Stops | Train FK, ordered by sequence |
| **Seat Availability** | Train_Inventory | Train + Date + Class |
| **Booking List** | Bookings | User FK, date range |
| **PNR Status** | Bookings, Passengers | PNR exact match |
| **Fare Calculation** | Fares, Trains | From/To/Class |
| **Quota Check** | Quotas | Train + Class + Quota_Type |
| **Analytics** | Bookings, Trains, Users | Aggregations |
| **Admin Logs** | Admin_Logs | User FK, date range |
| **Announcements** | Announcements | Station/Train FK, Is_Active |

### 5.2 Write Operations Matrix

| Module | Tables Written | Trigger |
|--------|----------------|---------|
| **Auth Register** | Users | New registration |
| **Auth Login** | Users | Update Last_Login |
| **Password Reset** | Password_Reset_Tokens, Users | OTP generation, password update |
| **Create Booking** | Bookings, Passengers, Train_Inventory | New booking |
| **Cancel Booking** | Bookings, Train_Inventory | Cancellation |
| **Train CRUD** | Trains, Train_Routes, Route_Stops | Admin action |
| **Station CRUD** | Stations | Admin action |
| **Fare CRUD** | Fares | Admin action |
| **Quota CRUD** | Quotas | Admin action |
| **Inventory Init** | Train_Inventory | Bulk insert for date range |
| **Settings Update** | Settings | Admin config change |
| **Any Admin Action** | Admin_Logs | Audit logging |

---

## 6. Data Flow Diagrams

### 6.1 User Registration Flow

```
┌──────────┐    POST /api/auth/register    ┌──────────────┐
│  Client  │ ────────────────────────────> │   auth.py    │
└──────────┘   {email, password, name}     └──────┬───────┘
                                                  │
                                                  ▼
                                           ┌──────────────┐
                                           │ UserService  │
                                           │  register()  │
                                           └──────┬───────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
                    ▼                             ▼                             ▼
           ┌────────────────┐           ┌────────────────┐           ┌────────────────┐
           │ Check email    │           │ Hash password  │           │ Insert user    │
           │ uniqueness     │           │ (bcrypt)       │           │ record         │
           │ → All_Users    │           │                │           │ → Users form   │
           └────────────────┘           └────────────────┘           └────────────────┘
                                                  │
                                                  ▼
                                           ┌──────────────┐
                                           │ Return JWT   │
                                           │ access_token │
                                           └──────────────┘
```

### 6.2 Train Search Flow

```
┌──────────┐   GET /api/trains?from=MAS&to=NDLS&date=25-Apr-2026   ┌──────────────┐
│  Client  │ ───────────────────────────────────────────────────> │  trains.py   │
└──────────┘                                                       └──────┬───────┘
                                                                          │
                                                                          ▼
                                                                   ┌──────────────┐
                                                                   │ CacheManager │
                                                                   │   check()    │
                                                                   └──────┬───────┘
                                                                          │
                                                     ┌────────────────────┴────────────────────┐
                                                     │ Cache Miss                              │
                                                     ▼                                         │
                                              ┌──────────────┐                                │
                                              │ZohoRepository│                                │
                                              │ get_records()│                                │
                                              └──────┬───────┘                                │
                                                     │                                         │
                         ┌───────────────────────────┼───────────────────────────┐            │
                         │                           │                           │            │
                         ▼                           ▼                           ▼            │
                ┌────────────────┐         ┌────────────────┐         ┌────────────────┐     │
                │ Query Trains   │         │ Join Fares     │         │ Filter by      │     │
                │ (All_Trains)   │         │ (All_Fares)    │         │ Run_Days       │     │
                │ From/To filter │         │ By class       │         │                │     │
                └────────────────┘         └────────────────┘         └────────────────┘     │
                                                     │                                         │
                                                     ▼                                         │
                                              ┌──────────────┐                                │
                                              │ Cache result │                                │
                                              │ (TTL: 10min) │                                │
                                              └──────────────┘                                │
                                                     │                                         │
                                                     ▼                                         │
                                              ┌──────────────┐     Cache Hit                  │
                                              │ Return JSON  │<────────────────────────────────┘
                                              │ train list   │
                                              └──────────────┘
```

### 6.3 Booking Creation Flow

```
┌──────────┐     POST /api/bookings      ┌──────────────┐
│  Client  │ ──────────────────────────> │ bookings.py  │
└──────────┘  {train_id, date, class,    └──────┬───────┘
               passengers[]}                     │
                                                 ▼
                                          ┌──────────────┐
                                          │BookingService│
                                          │   create()   │
                                          └──────┬───────┘
                                                 │
    ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
    │                                            │                                            │
    ▼                                            ▼                                            ▼
┌─────────────┐                          ┌─────────────┐                          ┌─────────────┐
│ 1. Validate │                          │ 2. Check    │                          │ 3. Calculate│
│    Train    │                          │  Inventory  │                          │    Fare     │
│ → All_Trains│                          │→ All_Invent │                          │ → All_Fares │
│ Run_Days OK │                          │ Available>0 │                          │ + surcharges│
└──────┬──────┘                          └──────┬──────┘                          └──────┬──────┘
       │                                        │                                        │
       ▼                                        ▼                                        ▼
┌─────────────┐                          ┌─────────────┐                          ┌─────────────┐
│ 4. Generate │                          │ 5. Allocate │                          │ 6. Decrement│
│    PNR      │                          │    Seats    │                          │  Inventory  │
│ (11-char)   │                          │ Coach/Berth │                          │→Train_Invent│
└──────┬──────┘                          └──────┬──────┘                          └──────┬──────┘
       │                                        │                                        │
       └────────────────────────────────────────┼────────────────────────────────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │ 7. Insert   │
                                         │   Booking   │
                                         │ → Bookings  │
                                         └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │ 8. Insert   │
                                         │ Passengers  │
                                         │→ Passengers │
                                         └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │ Return PNR  │
                                         │ + ticket    │
                                         └─────────────┘
```

### 6.4 Booking Cancellation Flow

```
┌──────────┐   POST /api/bookings/{id}/cancel   ┌──────────────┐
│  Client  │ ─────────────────────────────────> │ bookings.py  │
└──────────┘                                    └──────┬───────┘
                                                       │
                                                       ▼
                                                ┌──────────────┐
                                                │BookingService│
                                                │   cancel()   │
                                                └──────┬───────┘
                                                       │
    ┌──────────────────────────────────────────────────┼──────────────────────────────────────────────────┐
    │                                                  │                                                  │
    ▼                                                  ▼                                                  ▼
┌─────────────┐                                ┌─────────────┐                                ┌─────────────┐
│ 1. Fetch    │                                │ 2. Calculate│                                │ 3. Update   │
│   Booking   │                                │   Refund    │                                │   Status    │
│→ All_Booking│                                │ (policy %)  │                                │→ Bookings   │
└──────┬──────┘                                └──────┬──────┘                                └──────┬──────┘
       │                                              │                                              │
       │                                              │  Hours Before    Deduction                   │
       │                                              │  > 48            25%                         │
       │                                              │  48-12           25%                         │
       │                                              │  12-4            50%                         │
       │                                              │  < 4             100%                        │
       │                                              │  Tatkal          100%                        │
       │                                              │                                              │
       ▼                                              ▼                                              ▼
┌─────────────┐                                ┌─────────────┐                                ┌─────────────┐
│ 4. Increment│                                │ 5. Promote  │                                │ 6. Update   │
│  Inventory  │                                │  Waitlist   │                                │ Passengers  │
│→Train_Invent│                                │ (if any)    │                                │→ Passengers │
└──────┬──────┘                                └──────┬──────┘                                └──────┬──────┘
       │                                              │                                              │
       └──────────────────────────────────────────────┼──────────────────────────────────────────────┘
                                                      │
                                                      ▼
                                               ┌─────────────┐
                                               │ Return      │
                                               │ refund_amt  │
                                               └─────────────┘
```

### 6.5 AI Chat Flow

```
┌──────────┐      POST /api/ai/chat       ┌──────────────┐
│  Client  │ ───────────────────────────> │ ai_routes.py │
└──────────┘  {message: "book train       └──────┬───────┘
               from Chennai to Delhi"}            │
                                                  ▼
                                           ┌──────────────┐
                                           │ NLP Search / │
                                           │ Intent Parse │
                                           └──────┬───────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │ Intent: search              │ Intent: book               │
                    ▼                             ▼                             ▼
           ┌────────────────┐           ┌────────────────┐           ┌────────────────┐
           │ Build Zoho     │           │ Conversational │           │ Execute        │
           │ criteria from  │           │ state machine  │           │ booking flow   │
           │ NL query       │           │ collect params │           │                │
           └───────┬────────┘           └───────┬────────┘           └───────┬────────┘
                   │                            │                            │
                   ▼                            ▼                            ▼
           ┌────────────────┐           ┌────────────────┐           ┌────────────────┐
           │ Query Trains   │           │ Suggest trains │           │ BookingService │
           │ → All_Trains   │           │ from search    │           │ create()       │
           └───────┬────────┘           └───────┬────────┘           └───────┬────────┘
                   │                            │                            │
                   └────────────────────────────┼────────────────────────────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │ Return AI   │
                                         │ response    │
                                         └─────────────┘
```

---

## 7. API Endpoints Reference

### 7.1 Complete Endpoint List

| Module | Method | Endpoint | Auth | Description |
|--------|--------|----------|------|-------------|
| **Auth** | POST | `/api/auth/register` | - | Register user |
| | POST | `/api/auth/login` | - | Login, get JWT |
| | POST | `/api/auth/refresh` | - | Refresh token |
| | POST | `/api/auth/logout` | - | Logout |
| | POST | `/api/auth/change-password` | User | Change password |
| | POST | `/api/auth/forgot-password` | - | Request OTP |
| | POST | `/api/auth/reset-password` | - | Reset with OTP |
| | POST | `/api/auth/setup-admin` | Key | Setup admin |
| | GET | `/api/test/token` | - | Verify auth |
| **Trains** | GET | `/api/trains` | - | Search trains |
| | POST | `/api/trains` | Admin | Create train |
| | GET | `/api/trains/{id}` | - | Get train |
| | PUT | `/api/trains/{id}` | Admin | Update train |
| | DELETE | `/api/trains/{id}` | Admin | Delete train |
| | GET | `/api/trains/{id}/schedule` | - | Get schedule |
| | GET | `/api/trains/{id}/vacancy` | - | Availability |
| | GET | `/api/trains/{id}/running-status` | - | Status |
| | PUT | `/api/trains/{id}/running-status` | Admin | Update status |
| | POST | `/api/trains/{id}/cancel-on-date` | Admin | Cancel train |
| | POST | `/api/trains/bulk` | Admin | Bulk create |
| | GET | `/api/trains/connecting` | - | Connecting trains |
| | GET | `/api/trains/search-by-station` | - | Station search |
| **Bookings** | GET | `/api/bookings` | User | List bookings |
| | POST | `/api/bookings` | User | Create booking |
| | GET | `/api/bookings/{id}` | User | Get booking |
| | PUT | `/api/bookings/{id}` | Admin | Update booking |
| | DELETE | `/api/bookings/{id}` | Admin | Delete booking |
| | GET | `/api/bookings/pnr/{pnr}` | - | PNR lookup |
| | POST | `/api/bookings/{id}/confirm` | Admin | Confirm |
| | POST | `/api/bookings/{id}/pay` | Admin | Mark paid |
| | POST | `/api/bookings/{id}/cancel` | User | Cancel |
| | POST | `/api/bookings/{id}/partial-cancel` | User | Partial cancel |
| | GET | `/api/bookings/{id}/ticket` | User | Get ticket |
| | GET | `/api/bookings/chart` | Admin | Res chart |
| | GET | `/api/bookings/stream` | User | SSE updates |
| **Stations** | GET | `/api/stations` | - | List stations |
| | POST | `/api/stations` | Admin | Create station |
| | GET | `/api/stations/{id}` | - | Get station |
| | PUT | `/api/stations/{id}` | Admin | Update station |
| | DELETE | `/api/stations/{id}` | Admin | Delete station |
| **Users** | GET | `/api/users` | Admin | List users |
| | GET | `/api/users/{id}` | Admin | Get user |
| | PUT | `/api/users/{id}` | Admin | Update user |
| | DELETE | `/api/users/{id}` | Admin | Delete user |
| **Fares** | GET | `/api/fares` | - | List fares |
| | POST | `/api/fares` | Admin | Create fare |
| | PUT | `/api/fares/{id}` | Admin | Update fare |
| | DELETE | `/api/fares/{id}` | Admin | Delete fare |
| | POST | `/api/fares/calculate` | - | Calculate fare |
| **Quotas** | GET | `/api/quotas` | - | List quotas |
| | POST | `/api/quotas` | Admin | Create quota |
| | PUT | `/api/quotas/{id}` | Admin | Update quota |
| | DELETE | `/api/quotas/{id}` | Admin | Delete quota |
| **Inventory** | GET | `/api/inventory` | - | List inventory |
| | POST | `/api/inventory` | Admin | Create inventory |
| | PUT | `/api/inventory/{id}` | Admin | Update inventory |
| | POST | `/api/inventory/bulk-init` | Admin | Bulk init |
| **Coaches** | GET | `/api/coaches` | - | List coaches |
| | GET | `/api/coach-layouts` | - | List layouts |
| | POST | `/api/coach-layouts` | Admin | Create layout |
| **Routes** | GET | `/api/train-routes` | - | List routes |
| | POST | `/api/train-routes` | Admin | Create route |
| | GET | `/api/train-routes/{id}/stops` | - | Get stops |
| **Announcements** | GET | `/api/announcements` | - | List |
| | POST | `/api/announcements` | Admin | Create |
| | PUT | `/api/announcements/{id}` | Admin | Update |
| | DELETE | `/api/announcements/{id}` | Admin | Delete |
| **Settings** | GET | `/api/settings` | Admin | List settings |
| | PUT | `/api/settings/{key}` | Admin | Update setting |
| **Admin** | GET | `/api/admin/logs` | Admin | Audit logs |
| | GET | `/api/admin/reports/bookings` | Admin | Booking report |
| | GET | `/api/admin/reports/revenue` | Admin | Revenue report |
| **Analytics** | GET | `/api/analytics/overview` | Admin | Dashboard |
| | GET | `/api/analytics/trends` | Admin | Trends |
| | GET | `/api/analytics/top-trains` | Admin | Top trains |
| | GET | `/api/analytics/routes` | Admin | Route stats |
| | GET | `/api/analytics/revenue` | Admin | Revenue |
| **AI** | POST | `/api/ai/qwen` | - | QuickML proxy |
| | POST | `/api/ai/search` | - | NLP search |
| | POST | `/api/ai/chat` | - | Chat assistant |
| | GET | `/api/ai/recommendations` | User | Suggestions |
| | POST | `/api/ai/analyze` | Admin | AI insights |
| | GET | `/api/ai/predict-availability` | - | Predictions |
| | POST | `/api/ai/agent` | - | Intent routing |
| | POST | `/api/ai/mcp-query` | - | MCP query |
| | GET | `/api/ai/schema` | - | Schema discovery |
| | GET | `/api/ai/schema/modules` | - | Modules list |
| | GET | `/api/ai/cache-stats` | Admin | Cache stats |
| | POST | `/api/ai/cache/invalidate` | Admin | Clear cache |

---

## 8. Configuration & Environment

### 8.1 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| **Zoho API** |||
| `ZOHO_CLIENT_ID` | Yes | OAuth client ID |
| `ZOHO_CLIENT_SECRET` | Yes | OAuth client secret |
| `ZOHO_REFRESH_TOKEN` | Yes | OAuth refresh token |
| `ZOHO_ACCOUNT_OWNER_NAME` | Yes | Zoho account owner |
| `ZOHO_APP_LINK_NAME` | Yes | Creator app link name |
| **Authentication** |||
| `SECRET_KEY` | Yes | JWT signing key |
| `ADMIN_EMAIL` | No | Admin email pattern |
| `ADMIN_DOMAIN` | No | Admin domain pattern |
| `ADMIN_SETUP_KEY` | No | Admin setup secret |
| **AI Services** |||
| `GEMINI_API_KEY` | No | Google Gemini API key |
| `CATALYST_ACCESS_TOKEN` | No | Catalyst QuickML token |
| `ANTHROPIC_API_KEY` | No | Claude API key |
| **Server** |||
| `CORS_ALLOWED_ORIGINS` | No | CORS origins (default: *) |
| `DEBUG` | No | Debug mode |

### 8.2 System Constants (config.py)

```python
# Seat class mapping
SEAT_CLASS_MAP = {
    'SL': 'Available_Seats_SL',
    '3A': 'Available_Seats_3A',
    '2A': 'Available_Seats_2A',
    '1A': 'Available_Seats_1A',
    'CC': 'Available_Seats_CC',
    'EC': 'Available_Seats_EC',
    '2S': 'Available_Seats_2S'
}

# Coach capacity by class
COACH_CAPACITY = {
    'SL': 72,
    '3A': 64,
    '2A': 46,
    '1A': 18,
    'CC': 78,
    'EC': 56,
    '2S': 100
}

# Minimum cancellation deduction by class
CANCEL_MIN_DEDUCTION = {
    'SL': 50,
    '2S': 30,
    '3A': 100,
    '2A': 150,
    '1A': 200,
    'CC': 80,
    'EC': 100
}

# Booking advance days
BOOKING_ADVANCE_DAYS = 120

# Tatkal opening hour
TATKAL_OPEN_HOUR = 10
```

### 8.3 Date Format

**Important:** Zoho Creator uses `dd-MMM-yyyy` format.

```python
# Python → Zoho
journey_date = "25-Apr-2026"
datetime_field = "25-Apr-2026 10:30:00"

# Criteria syntax
criteria = '(Journey_Date == "25-Apr-2026") && (Booking_Status == "confirmed")'
```

---

## 9. Storage Estimation

| Table | Records (Small) | Records (Large) | Size Est. |
|-------|-----------------|-----------------|-----------|
| Users | 10K | 1M | 50MB - 5GB |
| Stations | 1K | 10K | 1MB - 10MB |
| Trains | 1K | 50K | 5MB - 250MB |
| Train_Routes | 1K | 50K | 2MB - 100MB |
| Route_Stops | 10K | 500K | 20MB - 1GB |
| Coach_Layouts | 10 | 50 | <1MB |
| Train_Inventory | 30K | 1.5M | 60MB - 3GB |
| Fares | 50K | 2M | 100MB - 4GB |
| Quotas | 5K | 250K | 10MB - 500MB |
| Bookings | 100K | 10M | 500MB - 50GB |
| Passengers | 300K | 30M | 1GB - 100GB |
| Announcements | 100 | 10K | 1MB - 100MB |
| Admin_Logs | 10K | 1M | 50MB - 5GB |
| Settings | 50 | 500 | <1MB |
| Reset_Tokens | 1K | 100K | 1MB - 100MB |
| **TOTAL** | ~500K | ~45M | **~2GB - ~170GB** |

---

*Generated: 2026-03-25*
*Version: 2.0*
*Platform: Flask + Zoho Creator + Zoho Catalyst*

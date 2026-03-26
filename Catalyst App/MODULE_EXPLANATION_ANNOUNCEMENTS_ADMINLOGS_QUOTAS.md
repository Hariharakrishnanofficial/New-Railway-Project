# Railway Ticketing System - Module Explanation
## Announcements, Admin Logs & Quotas

---

## Table of Contents
1. [Announcements Module](#1-announcements-module)
2. [Admin Logs Module](#2-admin-logs-module)
3. [Quotas Module](#3-quotas-module)
4. [Summary](#4-summary)

---

## 1. Announcements Module

**File**: `routes/announcements.py`
**Purpose**: System-wide and entity-specific notifications for passengers and staff

### 1.1 What It Does

| Feature | Description |
|---------|-------------|
| **System Alerts** | Platform-wide notices (maintenance, policy changes) |
| **Train-Specific** | Delays, cancellations, platform changes for specific trains |
| **Station-Specific** | Notices for specific stations (closures, construction) |
| **Time-Bound** | Start_Date/End_Date controls visibility period |

### 1.2 Data Model

```
Announcements Table
├── Title           (required) - Short headline
├── Message         (required) - Full announcement text
├── Priority        (Normal/High/Urgent)
├── Is_Active       (boolean) - Manual on/off toggle
├── Train_ID        (optional) - Link to specific train
├── Station_ID      (optional) - Link to specific station
├── Start_Date      - When announcement becomes visible
├── End_Date        - When announcement expires
└── Created_By      - Admin who created it
```

### 1.3 API Endpoints

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/announcements` | Public | List all announcements |
| GET | `/api/announcements/active` | Public | Only current valid announcements |
| GET | `/api/announcements/{id}` | Public | Single announcement details |
| POST | `/api/announcements` | Admin | Create new announcement |
| PUT | `/api/announcements/{id}` | Admin | Update announcement |
| DELETE | `/api/announcements/{id}` | Admin | Delete announcement |

### 1.4 Business Flow

```
┌────────────────────────────────────────────────────────────────┐
│                    ANNOUNCEMENT FLOW                           │
├────────────────────────────────────────────────────────────────┤
│  1. Admin creates announcement via POST /api/announcements     │
│  2. Set scope: system-wide OR train-specific OR station-bound  │
│  3. Set validity period (Start_Date → End_Date)               │
│                                                                │
│  FRONTEND CONSUMPTION:                                         │
│  • GET /api/announcements/active → Only current, valid ones   │
│  • Filters by: today >= Start_Date AND today <= End_Date       │
│  • Displayed on user dashboard/booking screens                 │
└────────────────────────────────────────────────────────────────┘
```

### 1.5 Example Use Cases

| Scenario | Title | Scope |
|----------|-------|-------|
| Train delay | "Train 12345 delayed by 2 hours due to fog" | Train-specific |
| Platform maintenance | "Platform 4 at MAS station under maintenance" | Station-specific |
| Policy reminder | "Tatkal booking opens at 10:00 AM daily" | System-wide |
| Festival rush | "Extra coaches added for Diwali rush" | System-wide |
| Route diversion | "Trains via XYZ diverted due to track work" | Train-specific |

### 1.6 Sample Request/Response

**Create Announcement**
```http
POST /api/announcements
Content-Type: application/json
Authorization: Bearer <admin_token>

{
  "Title": "Train 12657 Delayed",
  "Message": "Chennai Mail delayed by 3 hours due to signal failure at Vijayawada",
  "Priority": "High",
  "Train_ID": "1234567890123456789",
  "Start_Date": "25-Mar-2026",
  "End_Date": "26-Mar-2026",
  "Is_Active": true
}
```

**Get Active Announcements**
```http
GET /api/announcements/active

Response:
{
  "success": true,
  "data": [
    {
      "ID": "...",
      "Title": "Train 12657 Delayed",
      "Message": "Chennai Mail delayed by 3 hours...",
      "Priority": "High",
      "Train_ID": { "ID": "...", "display_value": "12657 - Chennai Mail" }
    }
  ]
}
```

---

## 2. Admin Logs Module

**Files**: `routes/admin_logs.py` + `utils/admin_logger.py`
**Purpose**: Audit trail for all administrative actions in the system

### 2.1 What It Does

| Feature | Description |
|---------|-------------|
| **Action Tracking** | Records WHO did WHAT and WHEN |
| **Change History** | Stores old/new values for modifications |
| **IP Logging** | Captures request IP for security auditing |
| **Fire-and-Forget** | Non-blocking writes (won't fail main operation) |

### 2.2 Data Model

```
Admin_Logs Table
├── Admin_User      - Email of admin who performed action
├── Action          - Action type (CREATE, UPDATE, DELETE, etc.)
├── Resource_Type   - What was affected (Train, Station, Quota, etc.)
├── Resource_ID     - ID of affected record
├── Old_Value       - Previous state (JSON, max 2000 chars)
├── New_Value       - New state (JSON, max 2000 chars)
├── Timestamp       - When action occurred
└── IP_Address      - Request source IP
```

### 2.3 API Endpoints

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/admin-logs` | Admin | List all logs (with filters) |
| GET | `/api/admin-logs?user_id=X` | Admin | Filter by specific admin |
| GET | `/api/admin-logs?action=DELETE` | Admin | Filter by action type |
| GET | `/api/admin-logs?record_id=Y` | Admin | Filter by affected record |

### 2.4 Logging Utility Usage

**Code Location**: `utils/admin_logger.py`

```python
from utils.admin_logger import log_admin_action

# Called from various admin routes:
log_admin_action(
    admin_email="admin@railway.com",
    action="UPDATE",
    resource_type="Train",
    resource_id="12345",
    old_value='{"Is_Active": "false"}',
    new_value='{"Is_Active": "true"}'
)
```

### 2.5 Actions Logged Throughout System

| Module | Logged Actions |
|--------|----------------|
| **Trains** | CREATE_TRAIN, UPDATE_TRAIN, DELETE_TRAIN |
| **Stations** | CREATE_STATION, UPDATE_STATION, DELETE_STATION |
| **Routes** | CREATE_TRAIN_ROUTE, UPDATE_TRAIN_ROUTE, DELETE_TRAIN_ROUTE |
| **Route Stops** | add_route_stop, update_route_stop, delete_route_stop |
| **Quotas** | CREATE_QUOTA, UPDATE_QUOTA, DELETE_QUOTA |
| **Fares** | CREATE_FARE, UPDATE_FARE, DELETE_FARE |
| **Settings** | UPDATE_SETTING |
| **Announcements** | CREATE_ANNOUNCEMENT, UPDATE_ANNOUNCEMENT, DELETE_ANNOUNCEMENT |
| **Coach Layouts** | CREATE_COACH_LAYOUT, UPDATE_COACH_LAYOUT, DELETE_COACH_LAYOUT |

### 2.6 Business Purpose

```
┌────────────────────────────────────────────────────────────────┐
│                 WHY ADMIN LOGS MATTER                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  COMPLIANCE:                                                   │
│  • Regulatory audit requirements (data change trail)           │
│  • PCI-DSS, SOC2 compliance evidence                          │
│                                                                │
│  SECURITY:                                                     │
│  • Detect unauthorized or suspicious changes                   │
│  • Track bulk deletions or modifications                       │
│  • IP-based anomaly detection                                  │
│                                                                │
│  DEBUGGING:                                                    │
│  • "Who changed the train schedule yesterday?"                │
│  • "When was this fare updated?"                              │
│  • "What was the old value before this broke?"                │
│                                                                │
│  ACCOUNTABILITY:                                               │
│  • Admin responsibility tracking                               │
│  • Performance review (action counts)                         │
│  • Dispute resolution                                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 2.7 Sample Log Entry

```json
{
  "ID": "9876543210987654321",
  "Admin_User": "superadmin@railway.com",
  "Action": "UPDATE",
  "Resource_Type": "Train",
  "Resource_ID": "1234567890123456789",
  "Old_Value": "{\"Fare_SL\": 450, \"Is_Active\": true}",
  "New_Value": "{\"Fare_SL\": 500, \"Is_Active\": true}",
  "Timestamp": "25-Mar-2026 14:30:45",
  "IP_Address": "192.168.1.100"
}
```

---

## 3. Quotas Module

**File**: `routes/quotas.py`
**Purpose**: Manages seat allocation categories (General, Tatkal, Ladies, etc.)

### 3.1 What It Does

| Feature | Description |
|---------|-------------|
| **Seat Pools** | Divides train capacity into quota buckets |
| **Booking Windows** | Controls when specific quotas open (e.g., Tatkal at 10 AM) |
| **Surcharge Tracking** | Links to fare calculation for Tatkal premium |
| **Availability Control** | Separate available seat counts per quota |

### 3.2 Data Model

```
Quotas Table
├── Train_ID              - Which train this quota applies to
├── Class                 - Seat class (SL, 3A, 2A, 1A, CC, EC)
├── Quota_Type            - Human-readable name
├── Quota_Code            - Standard code (GN, TQ, PT, LD, SS, etc.)
├── Total_Seats           - Max seats in this quota pool
├── Available_Seats       - Current availability
├── Booking_Opens         - Time when booking opens (e.g., "10:00")
├── Surcharge_Percentage  - Added fee % (used for Tatkal)
└── Is_Active             - Enable/disable quota
```

### 3.3 Standard Quota Types (IRCTC-Style)

| Code | Type | Description | Booking Opens |
|------|------|-------------|---------------|
| **GN** | General | Standard booking | Any time (ARP 120 days) |
| **TQ** | Tatkal | Last-minute premium | 10:00 AM (day before journey) |
| **PT** | Premium Tatkal | Premium surge pricing | 10:00 AM (day before journey) |
| **LD** | Ladies | Reserved for women | Any time |
| **SS** | Senior Citizen | Reserved for seniors (60+) | Any time |
| **HP** | Physically Handicapped | Reserved quota | Any time |
| **DF** | Defence | Military personnel | Any time |
| **FT** | Foreign Tourist | Foreign nationals | Any time |
| **YU** | Yuva | Youth (18-45) discounted | Any time |
| **DP** | Duty Pass | Railway staff | Any time |

### 3.4 API Endpoints

| Method | Endpoint | Access | Description |
|--------|----------|--------|-------------|
| GET | `/api/quotas` | Public | List all quotas |
| GET | `/api/quotas?train_id=X` | Public | Quotas for specific train |
| GET | `/api/quotas?class=3A` | Public | Quotas for specific class |
| GET | `/api/quotas/{id}` | Public | Single quota details |
| POST | `/api/quotas` | Admin | Create new quota |
| PUT | `/api/quotas/{id}` | Admin | Update quota |
| DELETE | `/api/quotas/{id}` | Admin | Delete quota |

### 3.5 Business Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     QUOTA USAGE IN BOOKING                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  STEP 1: User selects quota during search                          │
│  ─────────────────────────────────────────                         │
│  Frontend provides dropdown: General, Tatkal, Ladies, etc.         │
│  Default selection: "General" (GN)                                 │
│                                                                     │
│  STEP 2: System validates quota constraints                        │
│  ───────────────────────────────────────────                       │
│  ├─ Is quota active for this train+class?                          │
│  ├─ Is it within booking window?                                   │
│  │   └─ Tatkal: Only after 10:00 AM (day before journey)           │
│  └─ Are seats available in this quota pool?                        │
│                                                                     │
│  STEP 3: Fare calculation applies quota surcharge                  │
│  ────────────────────────────────────────────────                  │
│  if quota in ('TQ', 'PT'):                                         │
│      surcharge = base_fare × Surcharge_Percentage / 100            │
│      # Typically 30% for Tatkal, 50% for Premium Tatkal            │
│                                                                     │
│  STEP 4: Seat allocated from specific quota pool                   │
│  ───────────────────────────────────────────────                   │
│  Seats come from quota's Available_Seats, not general inventory    │
│                                                                     │
│  STEP 5: Cancellation rules differ by quota                        │
│  ──────────────────────────────────────────                        │
│  • General: Refund based on hours before departure                 │
│  • Tatkal (TQ/PT): NO REFUND under any condition                   │
│  • Ladies/Senior: Standard refund rules apply                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.6 Quota Influence on Other Modules

```
                    ┌──────────────────┐
                    │      QUOTAS      │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ FARE CALCULATION│ │ SEAT ALLOCATION │ │  CANCELLATION   │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ Reads:          │ │ Reads:          │ │ Reads:          │
│ Surcharge_%     │ │ Available_Seats │ │ Quota_Code      │
│                 │ │ Total_Seats     │ │                 │
│ Applies:        │ │                 │ │ Applies:        │
│ Tatkal premium  │ │ Decrements:     │ │ TQ/PT = No      │
│ to base fare    │ │ Available_Seats │ │ refund policy   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 3.7 Tatkal Surcharge Calculation

**Code Reference**: `utils/fare_helper.py`

```python
def _get_tatkal_surcharge(quota):
    """
    Fetches Tatkal surcharge percentage from Quotas table.
    Falls back to 30% if not found.
    """
    if quota.upper() not in ('TQ', 'PT', 'TATKAL', 'PREMIUM TATKAL'):
        return 0.0

    criteria = f'(Quota_Code == "{quota.upper()}")'
    result = zoho.get_all_records(TABLES['quotas'], criteria=criteria, limit=1)

    if result.get('success'):
        records = result.get('data', {}).get('data', [])
        if records:
            return float(records[0].get('Surcharge_Percentage', 30))

    return 30.0  # Default 30% if not configured
```

### 3.8 Tatkal Fare Caps (IRCTC Rules)

| Class | Min Charge | Max Charge |
|-------|------------|------------|
| SL | ₹100 | ₹200 |
| 3A | ₹300 | ₹400 |
| 2A | ₹400 | ₹500 |
| 1A | ₹400 | ₹500 |
| CC | ₹100 | ₹150 |
| EC | ₹400 | ₹500 |

### 3.9 Sample Quota Configuration

```json
{
  "Train_ID": "1234567890123456789",
  "Class": "3A",
  "Quota_Type": "Tatkal",
  "Quota_Code": "TQ",
  "Total_Seats": 50,
  "Available_Seats": 45,
  "Booking_Opens": "10:00",
  "Surcharge_Percentage": 30,
  "Is_Active": true
}
```

---

## 4. Summary

| Module | Primary Purpose | Key Users | Data Impact |
|--------|-----------------|-----------|-------------|
| **Announcements** | User-facing notifications | All users (read), Admins (write) | Informational only |
| **Admin Logs** | Audit trail & compliance | Admins only | Read-only historical data |
| **Quotas** | Seat pool & pricing control | All users (read), Admins (write) | Affects booking flow & fares |

### Module Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SYSTEM ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   USER DASHBOARD                           ADMIN PANEL                      │
│   ─────────────                            ───────────                      │
│        │                                        │                           │
│        ▼                                        ▼                           │
│   ┌──────────────┐                      ┌──────────────┐                   │
│   │ Announcements│◄─────────────────────│ Create/Edit  │                   │
│   │ (Read Only)  │                      │ Announcements│                   │
│   └──────────────┘                      └──────┬───────┘                   │
│                                                │                           │
│   ┌──────────────┐                             │ logs action               │
│   │   Quotas     │◄───── availability ─────────┤                           │
│   │ (for search) │                             ▼                           │
│   └──────┬───────┘                      ┌──────────────┐                   │
│          │                              │  Admin Logs  │                   │
│          │ affects fare                 │ (Audit Trail)│                   │
│          ▼                              └──────────────┘                   │
│   ┌──────────────┐                             ▲                           │
│   │   BOOKING    │                             │                           │
│   │   ENGINE     │─────── logs booking ────────┘                           │
│   └──────────────┘                                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

*Document Version: 1.0*
*Generated: 2026-03-25*
*Based on actual codebase analysis*

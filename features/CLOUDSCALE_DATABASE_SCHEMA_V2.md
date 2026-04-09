# Zoho Catalyst CloudScale Database Schema v2.0
## Railway Ticketing System - Based on Catalyst Function & Client

---

## TABLE OVERVIEW

| # | Table Name | Zoho Form | Zoho Report | Description |
|---|------------|-----------|-------------|-------------|
| 1 | Users | Users | All_Users | User accounts & authentication |
| 2 | Stations | Stations | All_Stations | Railway station master data |
| 3 | Trains | Trains | All_Trains | Train master data |
| 4 | Train_Routes | Train_Routes | All_Train_Routes | Route parent records |
| 5 | Route_Stops | Route_Stops | All_Route_Stops | Route stop details (subform) |
| 6 | Coach_Layouts | Coach_Layouts | All_Coach_Layouts | Coach configuration by class |
| 7 | Train_Inventory | Train_Inventory | All_Inventory | Coach allocation per train |
| 8 | Fares | Fares | All_Fares | Fare rules by route/class |
| 9 | Quotas | Quotas | All_Quotas | Seat quota distribution |
| 10 | Bookings | Bookings | All_Bookings | Main booking records |
| 11 | Passengers | Passengers | All_Passengers | Passenger details per booking |
| 12 | Announcements | Announcements | All_Announcements | System announcements |
| 13 | Admin_Logs | Admin_Logs | All_Admin_Logs | Admin audit trail |
| 14 | Settings | Settings | All_Setting | System configuration |
| 15 | Password_Reset_Tokens | Password_Reset_Tokens | All_Reset_Tokens | Password reset OTP |
| 16 | Sessions | Sessions | All_Sessions | Server-side session management |
| 17 | Session_Audit_Log | Session_Audit_Log | All_Session_Audit | Session security audit trail |
| 18 | OTP_Tokens | OTP_Tokens | All_OTP_Tokens | Multi-purpose OTP verification |

---

## TABLE DEFINITIONS

### 1. USERS
User accounts and authentication

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Full_Name | VARCHAR(255) | Yes | - | User's full name |
| Email | VARCHAR(255) | Yes | Yes | Login email (lowercase) |
| Password | VARCHAR(512) | Yes | - | SHA-256 hashed password |
| Phone_Number | VARCHAR(20) | - | - | Contact phone |
| Role | ENUM | - | - | 'Admin' \| 'User' (default: User) |
| Account_Status | ENUM | - | - | 'Active' \| 'Blocked' \| 'Suspended' |
| Aadhar_Verified | VARCHAR(10) | - | - | 'true' \| 'false' (stored as string) |
| Date_of_Birth | DATE | - | - | User DOB (dd-MMM-yyyy) |
| ID_Proof_Type | VARCHAR(50) | - | - | Aadhaar, PAN, Passport, etc. |
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

### 2. STATIONS
Railway station master data

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Station_Code | VARCHAR(10) | Yes | Yes | 3-5 char code (MAS, NDLS, SBC) |
| Station_Name | VARCHAR(255) | Yes | - | Full station name |
| City | VARCHAR(100) | Yes | - | City name |
| State | VARCHAR(100) | Yes | - | State/Province |
| Zone | VARCHAR(50) | - | - | Railway zone (SR, NR, etc.) |
| Division | VARCHAR(100) | - | - | Railway division |
| Station_Type | VARCHAR(50) | - | - | Junction, Terminal, etc. |
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

### 3. TRAINS
Train master data with fare and seat information

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train_Number | VARCHAR(10) | Yes | Yes | Unique train number (12028) |
| Train_Name | VARCHAR(255) | Yes | - | Train name |
| Train_Type | VARCHAR(50) | - | - | EXPRESS, SUPERFAST, RAJDHANI, SHATABDI |
| From_Station | LOOKUP | Yes | - | Source station (→ Stations) |
| To_Station | LOOKUP | Yes | - | Destination station (→ Stations) |
| Departure_Time | TIME | Yes | - | Departure from source (HH:MM) |
| Arrival_Time | TIME | Yes | - | Arrival at destination (HH:MM) |
| Duration | VARCHAR(20) | - | - | Journey duration string |
| Distance | DECIMAL(10,2) | - | - | Total distance in km |
| Run_Days | VARCHAR(100) | - | - | Comma-separated: Mon,Wed,Fri |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Pantry_Car_Available | VARCHAR(10) | - | - | 'true' \| 'false' |
| **Fares by Class** | | | | |
| Fare_SL | DECIMAL(10,2) | - | - | Sleeper class fare |
| Fare_3A | DECIMAL(10,2) | - | - | 3rd AC fare |
| Fare_2A | DECIMAL(10,2) | - | - | 2nd AC fare |
| Fare_1A | DECIMAL(10,2) | - | - | 1st AC fare |
| Fare_CC | DECIMAL(10,2) | - | - | Chair Car fare |
| Fare_EC | DECIMAL(10,2) | - | - | Executive Chair fare |
| Fare_2S | DECIMAL(10,2) | - | - | Second Sitting fare |
| **Seats by Class** | | | | |
| Total_Seats_SL | INT | - | - | Total Sleeper seats |
| Total_Seats_3A | INT | - | - | Total 3AC seats |
| Total_Seats_2A | INT | - | - | Total 2AC seats |
| Total_Seats_1A | INT | - | - | Total 1AC seats |
| Total_Seats_CC | INT | - | - | Total Chair Car seats |
| Available_Seats_SL | INT | - | - | Available Sleeper seats |
| Available_Seats_3A | INT | - | - | Available 3AC seats |
| Available_Seats_2A | INT | - | - | Available 2AC seats |
| Available_Seats_1A | INT | - | - | Available 1AC seats |
| Available_Seats_CC | INT | - | - | Available Chair Car seats |
| **Running Status** | | | | |
| Running_Status | VARCHAR(50) | - | - | 'On Time' \| 'Delayed' |
| Delay_Minutes | INT | - | - | Delay in minutes |
| Expected_Departure | DATETIME | - | - | Expected departure time |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_trains_number` UNIQUE (Train_Number)
- `idx_trains_route` (From_Station, To_Station)
- `idx_trains_active` (Is_Active)

---

### 4. TRAIN_ROUTES
Parent route record for each train

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | Yes | - | Train reference (→ Trains) |
| Notes | TEXT | - | - | Route notes |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_routes_train` (Train)

---

### 5. ROUTE_STOPS
Intermediate stops for each train route (subform of Train_Routes)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train_Routes | LOOKUP | Yes | - | Parent route (→ Train_Routes) |
| Sequence | INT | Yes | - | Stop order (1=origin, n=destination) |
| Station_Name | VARCHAR(255) | Yes | - | Station name |
| Station_Code | VARCHAR(10) | - | - | IRCTC station code |
| Stations | LOOKUP | - | - | Station reference (→ Stations) |
| Arrival_Time | TIME | - | - | Arrival time at stop |
| Departure_Time | TIME | - | - | Departure time from stop |
| Halt_Minutes | INT | - | - | Halt duration in minutes |
| Distance_KM | DECIMAL(10,2) | - | - | Distance from source |
| Day_Count | INT | - | - | Day number (1=same day, 2=next day) |
| Platform | INT | - | - | Platform number |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_stops_route_seq` (Train_Routes, Sequence)
- `idx_stops_station` (Station_Code)

---

### 6. COACH_LAYOUTS
Coach configuration by class type

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Class_Code | VARCHAR(10) | Yes | Yes | SL, 3A, 2A, 1A, CC, EC, 2S |
| Class_Name | VARCHAR(100) | Yes | - | Sleeper, 3rd AC, etc. |
| Coach_Prefix | VARCHAR(5) | - | - | S, B, A, H, C |
| Total_Berths | INT | Yes | - | Berths per coach |
| Berth_Cycle | INT | - | - | Berth numbering cycle |
| Layout_Pattern | JSON | - | - | Berth layout configuration |
| Is_AC | VARCHAR(10) | - | - | 'true' for AC classes |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Standard Configurations:**
| Class | Prefix | Berths/Coach | Berth Order |
|-------|--------|--------------|-------------|
| SL | S | 72 | Lower, Middle, Upper, Side Lower, Side Upper |
| 2S | D | 100 | Window, Middle, Aisle |
| 3A/3AC | B | 64 | Lower, Middle, Upper, Side Lower, Side Upper |
| 2A/2AC | A | 46 | Lower, Upper, Side Lower, Side Upper |
| 1A/1AC | H | 18 | Lower, Upper |
| CC | C | 78 | Window, Aisle, Middle |
| EC | E | 56 | Window, Aisle |

---

### 7. TRAIN_INVENTORY
Daily seat inventory per train/class

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | Yes | - | Train reference (→ Trains) |
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

### 8. FARES
Fare rules between stations

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | - | - | Train reference (→ Trains) |
| From_Station | LOOKUP | Yes | - | Source station (→ Stations) |
| To_Station | LOOKUP | Yes | - | Destination station (→ Stations) |
| Class | VARCHAR(10) | Yes | - | SL, 3A, 2A, 1A, CC, EC |
| Base_Fare | DECIMAL(10,2) | Yes | - | Base fare amount |
| Dynamic_Fare | DECIMAL(10,2) | - | - | Dynamic pricing fare |
| Distance_KM | DECIMAL(10,2) | - | - | Distance between stations |
| Concession_Type | VARCHAR(50) | - | - | General, Senior, Student, etc. |
| Concession_Percent | DECIMAL(5,2) | - | - | Discount percentage |
| Effective_From | DATE | - | - | Fare start date |
| Effective_To | DATE | - | - | Fare end date |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

**IRCTC Fare Calculation:**
```
1. Base Fare (from Fares table or Train.Fare_{class})
2. + Reservation Charge (2S:₹15, SL:₹20, CC/3AC:₹40, 2AC:₹50, 1AC:₹60)
3. + Superfast Surcharge (if applicable: SL:₹30, CC/3AC:₹45, 2AC:₹45, 1AC:₹75)
4. + Tatkal Premium (30% of base, capped by class)
5. - Concession Discount (Senior:40%, Student/Disabled:50%)
6. + GST 5% (AC classes only)
7. + Catering (optional: CC/3AC:₹185, 2AC:₹250, 1AC:₹350)
8. + Convenience Fee (AC:₹35.40, Non-AC:₹17.70 per ticket)
```

---

### 9. QUOTAS
Seat quota distribution per train/class

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Train | LOOKUP | Yes | - | Train reference (→ Trains) |
| Class | VARCHAR(10) | Yes | - | SL, 3A, 2A, 1A, CC |
| Quota_Type | VARCHAR(50) | Yes | - | General, TQ (Tatkal), PT (Premium Tatkal) |
| Quota_Code | VARCHAR(10) | - | - | GN, TQ, PT, SS, LD |
| Total_Seats | INT | Yes | - | Total seats in this quota |
| Available_Seats | INT | - | - | Currently available |
| Booking_Opens | TIME | - | - | Booking opens at (10:00 for Tatkal) |
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
| HP | Physically Handicapped | 120 days before |

---

### 10. BOOKINGS
Main booking records

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| PNR | VARCHAR(20) | Yes | Yes | 10-char alphanumeric (PNRXXXXXXXX) |
| Users | LOOKUP | Yes | - | User reference (→ Users) |
| Trains | LOOKUP | Yes | - | Train reference (→ Trains) |
| Journey_Date | DATE | Yes | - | Date of journey (dd-MMM-yyyy) |
| Class | VARCHAR(10) | Yes | - | SL, 2S, 3A, 2A, 1A, CC, EC |
| Quota | VARCHAR(50) | - | - | General, TQ, PT |
| Num_Passengers | INT | Yes | - | Number of passengers (1-6) |
| Passengers | JSON | Yes | - | Passenger array (JSON string) |
| Total_Fare | DECIMAL(10,2) | Yes | - | Total booking amount |
| Booking_Status | ENUM | - | - | 'confirmed' \| 'waitlisted' \| 'cancelled' |
| Payment_Status | ENUM | - | - | 'pending' \| 'paid' |
| Payment_Method | VARCHAR(50) | - | - | UPI, Card, NetBanking |
| Boarding_Station | LOOKUP | - | - | Boarding station (→ Stations) |
| Deboarding_Station | LOOKUP | - | - | Deboarding station (→ Stations) |
| Booking_Time | DATETIME | Auto | - | When booking was made |
| Cancellation_Time | DATETIME | - | - | When cancelled |
| Refund_Amount | DECIMAL(10,2) | - | - | Refund on cancellation |
| Created_Time | DATETIME | Auto | - | Record creation time |
| Modified_Time | DATETIME | Auto | - | Last modification time |

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

**Cancellation Policy:**
| Hours Before | Deduction |
|--------------|-----------|
| > 48 hours | max(min_deduction, 25%) |
| 48-12 hours | 25% |
| 12-4 hours | 50% |
| < 4 hours | 100% (no refund) |
| Tatkal | No refund |

---

### 11. PASSENGERS
Individual passenger records (alternative to JSON storage)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Booking | LOOKUP | Yes | - | Booking reference (→ Bookings) |
| Passenger_Name | VARCHAR(255) | Yes | - | Full name |
| Age | INT | Yes | - | Age in years |
| Gender | VARCHAR(10) | Yes | - | Male, Female, Other |
| Is_Child | VARCHAR(10) | - | - | 'true' if age < 5 |
| Berth_Preference | VARCHAR(50) | - | - | Lower, Upper, No Preference |
| Coach | VARCHAR(10) | - | - | Allocated coach (S1, B2) |
| Seat_Number | INT | - | - | Allocated seat/berth number |
| Berth_Type | VARCHAR(20) | - | - | Lower, Middle, Upper, etc. |
| Current_Status | VARCHAR(50) | - | - | CNF/S1/14, WL/5, RAC/12 |
| Cancelled | VARCHAR(10) | - | - | 'true' if passenger cancelled |
| Created_Time | DATETIME | Auto | - | Record creation time |

---

### 12. ANNOUNCEMENTS
System announcements and alerts

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Title | VARCHAR(500) | Yes | - | Announcement title |
| Message | TEXT | Yes | - | Full message content |
| Priority | VARCHAR(20) | - | - | Low, Medium, High, Critical |
| Trains | LOOKUP | - | - | Related train (→ Trains) |
| Stations | LOOKUP | - | - | Related station (→ Stations) |
| Start_Date | DATETIME | - | - | Announcement start |
| End_Date | DATETIME | - | - | Announcement end |
| Is_Active | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_By | LOOKUP | - | - | Admin user (→ Users) |
| Created_Time | DATETIME | Auto | - | Record creation time |

---

### 13. ADMIN_LOGS
Admin activity audit trail

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Admin_User | LOOKUP | Yes | - | Admin reference (→ Users) |
| Action | VARCHAR(100) | Yes | - | Action performed |
| Resource_Type | VARCHAR(50) | Yes | - | Train, Booking, User, etc. |
| Resource_ID | VARCHAR(50) | - | - | ID of affected resource |
| Old_Value | JSON | - | - | Previous value |
| New_Value | JSON | - | - | New value |
| IP_Address | VARCHAR(50) | - | - | Client IP |
| User_Agent | VARCHAR(500) | - | - | Browser/client info |
| Status | VARCHAR(20) | - | - | success, failure |
| Created_Time | DATETIME | Auto | - | Record creation time |

---

### 14. SETTINGS
System configuration key-value store

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Setting_Key | VARCHAR(100) | Yes | Yes | Configuration key |
| Setting_Value | TEXT | Yes | - | Configuration value |
| Setting_Type | VARCHAR(20) | - | - | string, int, bool, json |
| Description | VARCHAR(500) | - | - | Setting description |
| Is_System | VARCHAR(10) | - | - | 'true' for system settings |
| Updated_By | LOOKUP | - | - | User who updated (→ Users) |
| Created_Time | DATETIME | Auto | - | Record creation time |
| Modified_Time | DATETIME | Auto | - | Last modification time |

**Common Settings:**
| Key | Default | Description |
|-----|---------|-------------|
| booking_advance_days | 120 | Days in advance booking allowed |
| max_passengers_per_booking | 6 | Max passengers per booking |
| tatkal_open_hour | 10 | Hour when Tatkal opens |
| maintenance_start | 23:45 | Maintenance window start |
| maintenance_end | 00:15 | Maintenance window end |

---

### 15. PASSWORD_RESET_TOKENS
Temporary OTP tokens for password reset

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| User_Email | VARCHAR(255) | Yes | - | User email |
| OTP | VARCHAR(10) | Yes | - | 6-digit OTP |
| Expires_At | DATETIME | Yes | - | OTP expiration (15 min) |
| Is_Used | VARCHAR(10) | - | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

---

### 16. SESSIONS
Server-side session management with HttpOnly cookies (replaces JWT tokens)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID (ROWID) |
| Session_ID | VARCHAR(64) | Yes | Yes | Secure 43-char session token |
| User_ID | VARCHAR(20) | Yes | - | Reference to Users.ID (ROWID) |
| User_Email | VARCHAR(255) | Yes | - | User email (denormalized) |
| User_Role | VARCHAR(20) | Yes | - | 'Admin' \| 'User' |
| IP_Address | VARCHAR(45) | - | - | Client IPv4/IPv6 address |
| User_Agent | VARCHAR(500) | - | - | Browser/device User-Agent |
| Device_Fingerprint | VARCHAR(64) | - | - | SHA-256 hash of device info |
| CSRF_Token | VARCHAR(64) | Yes | - | CSRF protection token |
| Created_At | DATETIME | Yes | - | Session creation timestamp |
| Last_Accessed_At | DATETIME | Yes | - | Last activity timestamp |
| Expires_At | DATETIME | Yes | - | Session expiration timestamp |
| Is_Active | VARCHAR(10) | Yes | - | 'true' \| 'false' |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Indexes:**
- `idx_sessions_session_id` UNIQUE (Session_ID)
- `idx_sessions_user_id` (User_ID)
- `idx_sessions_active` (Is_Active)
- `idx_sessions_expires` (Expires_At)

**Usage Notes:**
- Session_ID: Generated with `secrets.token_urlsafe(32)` - 256-bit entropy
- Max 3 concurrent sessions per user (oldest auto-revoked)
- 24-hour session timeout with sliding window
- Idle timeout: 6 hours of inactivity
- CSRF token required for POST/PUT/DELETE/PATCH requests

---

### 17. SESSION_AUDIT_LOG
Security audit trail for session-related events

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID (ROWID) |
| Event_Type | VARCHAR(50) | Yes | - | Type of security event |
| Session_ID | VARCHAR(64) | - | - | Related session (may be partial) |
| User_ID | VARCHAR(20) | - | - | Related user's ROWID |
| User_Email | VARCHAR(255) | - | - | User email at time of event |
| IP_Address | VARCHAR(45) | - | - | Client IP address |
| Event_Timestamp | DATETIME | Yes | - | When event occurred |
| Details | TEXT | - | - | JSON with additional data |
| Severity | VARCHAR(20) | - | - | INFO, WARNING, ERROR, CRITICAL |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Event Types:**
| Event_Type | Severity | Description |
|------------|----------|-------------|
| SESSION_CREATED | INFO | New session on login/register |
| SESSION_VALIDATED | INFO | Session successfully validated |
| SESSION_EXPIRED | INFO | Session timed out |
| SESSION_REVOKED | INFO | User logged out |
| SESSION_REVOKED_ADMIN | WARNING | Admin terminated session |
| SESSION_LIMIT_ENFORCED | INFO | Oldest session auto-revoked |
| CSRF_VALIDATION_FAILED | WARNING | CSRF token mismatch |
| SESSION_INVALID | WARNING | Invalid session ID presented |
| PASSWORD_CHANGED | INFO | All sessions revoked |
| SUSPICIOUS_ACTIVITY | CRITICAL | Potential security threat |

**Indexes:**
- `idx_audit_user_id` (User_ID)
- `idx_audit_event_type` (Event_Type)
- `idx_audit_timestamp` (Event_Timestamp)

---

### 18. OTP_TOKENS
Multi-purpose OTP verification tokens (registration, password reset, email change)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID (ROWID) |
| User_Email | VARCHAR(255) | Yes | - | Email address for OTP |
| OTP | VARCHAR(10) | Yes | - | 6-digit OTP code |
| Purpose | VARCHAR(30) | Yes | - | 'registration' \| 'password_reset' \| 'email_change' |
| Expires_At | DATETIME | Yes | - | OTP expiration (15 min default) |
| Is_Used | VARCHAR(10) | Yes | - | 'true' \| 'false' |
| Attempts | INT | Yes | - | Verification attempt count (max 3) |
| Created_At | DATETIME | Yes | - | Token creation timestamp |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Notes:**
- OTPs expire after 15 minutes
- Maximum 3 verification attempts before lockout
- Only one active OTP per email+purpose combination
- Cleanup old unused OTPs before creating new ones

**Indexes:**
- `idx_otp_email_purpose` (User_Email, Purpose)
- `idx_otp_expires` (Expires_At)

---

## RELATIONSHIPS DIAGRAM

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   USERS     │────<│   BOOKINGS   │>────│   TRAINS    │
└─────────────┘     └──────────────┘     └─────────────┘
      │                    │                    │
      │                    │                    │
      ▼                    ▼                    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ ADMIN_LOGS  │     │  PASSENGERS  │     │TRAIN_ROUTES │
└─────────────┘     └──────────────┘     └─────────────┘
      │                                        │
      │                                        ▼
      │                                  ┌─────────────┐
      │                                  │ ROUTE_STOPS │
      │                                  └─────────────┘
      │
      ▼
┌─────────────────┐     ┌─────────────────────┐
│    SESSIONS     │────>│  SESSION_AUDIT_LOG  │
└─────────────────┘     └─────────────────────┘
      │
      │ (User_ID FK)
      ▼
┌─────────────┐
│    USERS    │
└─────────────┘

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  STATIONS   │<────│    FARES     │────>│   TRAINS    │
└─────────────┘     └──────────────┘     └─────────────┘
      │
      │
      ▼
┌───────────────────┐
│   TRAIN_ROUTES    │
│   BOOKINGS        │
│   ANNOUNCEMENTS   │
└───────────────────┘
```

---

## ZOHO CREATOR DATE FORMAT

**Important:** Zoho Creator uses `dd-MMM-yyyy` format for dates.

```python
# Python → Zoho
journey_date = "25-Apr-2026"
datetime_field = "25-Apr-2026 10:30:00"

# Criteria syntax
criteria = '(Journey_Date == "25-Apr-2026") && (Booking_Status == "confirmed")'
```

---

## API ENDPOINT MAPPING

| Endpoint | Method | Form/Report | Description |
|----------|--------|-------------|-------------|
| /api/auth/register | POST | Users | Create user |
| /api/auth/login | POST | All_Users | Authenticate |
| /api/stations | GET | All_Stations | List stations |
| /api/stations | POST | Stations | Create station |
| /api/trains | GET | All_Trains | Search trains |
| /api/trains | POST | Trains | Create train |
| /api/bookings | GET | All_Bookings | List bookings |
| /api/bookings | POST | Bookings | Create booking |
| /api/bookings/pnr/{pnr} | GET | All_Bookings | PNR lookup |
| /api/users | GET | All_Users | List users (admin) |
| /api/fares/calculate | POST | All_Fares, All_Trains | Calculate fare |
| /api/train-routes | GET | All_Train_Routes | List routes |
| /api/train-routes/{id}/stops | GET | All_Route_Stops | List stops |
| /api/quotas | GET | All_Quotas | List quotas |
| /api/announcements | GET | All_Announcements | List announcements |
| /api/admin/logs | GET | All_Admin_Logs | Audit logs |
| /api/settings | GET | All_Setting | System settings |

---

## STORAGE ESTIMATION

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

## MIGRATION CHECKLIST

- [ ] Create all 15 tables in Catalyst CloudScale
- [ ] Configure primary keys (auto-increment BIGINT)
- [ ] Add unique constraints (Email, PNR, Station_Code, Train_Number)
- [ ] Set up foreign key relationships
- [ ] Create indexes for common queries
- [ ] Insert initial reference data (Stations, Coach_Layouts)
- [ ] Insert sample data (Trains, Fares, Quotas)
- [ ] Test CRUD operations via API
- [ ] Verify date format handling (dd-MMM-yyyy)
- [ ] Test search/filter queries with criteria
- [ ] Performance test with 10K+ records
- [ ] Set up backup strategy
- [ ] Document row-level security rules

---

*Generated from Catalyst App function and client code analysis*
*Version: 2.0 | Date: 2026-03-21*

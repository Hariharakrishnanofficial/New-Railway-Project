# Zoho Catalyst CloudScale Database Schema v2.0
## Railway Ticketing System - Based on Catalyst Function & Client

---

## ⚠️ IMPORTANT MIGRATION NOTES

### Sessions Table Foreign Key Constraint (Updated: 2026-04-08)

**Issue**: The Sessions table may have been created with a Foreign Key constraint on `User_ID` pointing to `Users.ROWID`. This prevents employee/admin logins from working.

**Symptom**: 
```
ERROR: Invalid Foreign key value for column User_ID. 
       ROWID of table Users is expected
```

**Required Fix**:
1. Open **Zoho Catalyst Console** (https://console.catalyst.zoho.com)
2. Navigate to **DataStore → Tables → Sessions**
3. Click on **User_ID** column
4. **Remove Foreign Key constraint** (if present)
5. Save changes

**Why**: The `User_ID` field needs to be a **polymorphic reference** that can store ROWIDs from either:
- `Users.ROWID` (for passenger sessions, when `User_Type='user'`)
- `Employees.ROWID` (for staff/admin sessions, when `User_Type='employee'`)

Database-level FK constraints cannot handle polymorphic references. Validation is enforced at the application level using the `User_Type` field.

**Verification**:
After removing FK constraint, test employee login:
```bash
curl -X POST "http://localhost:3000/server/smart_railway_app_function/session/employee/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@railway.com", "password": "Admin@123"}'
```

Expected: `200 OK` with session created
Before fix: `500 Internal Server Error` with FK violation

---

## TABLE OVERVIEW

| # | Table Name | Zoho Form | Zoho Report | Description |
|---|------------|-----------|-------------|-------------|
| 1 | Users | Users | All_Users | Passenger accounts (ticket buyers) |
| 2 | Employees | Employees | All_Employees | Staff accounts (Admin, Employee roles) |
| 3 | Stations | Stations | All_Stations | Railway station master data |
| 4 | Trains | Trains | All_Trains | Train master data |
| 5 | Train_Routes | Train_Routes | All_Train_Routes | Route parent records |
| 6 | Route_Stops | Route_Stops | All_Route_Stops | Route stop details (subform) |
| 7 | Coach_Layouts | Coach_Layouts | All_Coach_Layouts | Coach configuration by class |
| 8 | Train_Inventory | Train_Inventory | All_Inventory | Coach allocation per train |
| 9 | Fares | Fares | All_Fares | Fare rules by route/class |
| 10 | Quotas | Quotas | All_Quotas | Seat quota distribution |
| 11 | Bookings | Bookings | All_Bookings | Main booking records |
| 12 | Passengers | Passengers | All_Passengers | Passenger details per booking |
| 13 | Announcements | Announcements | All_Announcements | System announcements |
| 14 | Admin_Logs | Admin_Logs | All_Admin_Logs | Admin audit trail |
| 15 | Settings | Settings | All_Setting | System configuration |
| 16 | Password_Reset_Tokens | Password_Reset_Tokens | All_Reset_Tokens | Password reset OTP |
| 17 | Sessions | Sessions | All_Sessions | Server-side session management |
| 18 | Session_Audit_Log | Session_Audit_Log | All_Session_Audit | Session security audit trail |
| 19 | OTP_Tokens | OTP_Tokens | All_OTP_Tokens | Multi-purpose OTP verification |
| 20 | Employee_Invitations | Employee_Invitations | All_Employee_Invitations | Employee onboarding invitations |

---

## TABLE DEFINITIONS

### 1. USERS
Passenger accounts (ticket buyers only - NOT for employees/admin)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID |
| Full_Name | VARCHAR(255) | Yes | - | User's full name |
| Email | VARCHAR(255) | Yes | Yes | Login email (lowercase) |
| Password | VARCHAR(512) | Yes | - | Bcrypt hashed password |
| Phone_Number | VARCHAR(20) | - | - | Contact phone |
| Account_Status | ENUM | - | - | 'Active' \| 'Blocked' \| 'Suspended' |
| Aadhar_Verified | VARCHAR(10) | - | - | 'true' \| 'false' (stored as string) |
| Date_of_Birth | DATE | - | - | User DOB (dd-MMM-yyyy) |
| ID_Proof_Type | VARCHAR(50) | - | - | Aadhaar, PAN, Passport, etc. |
| ID_Proof_Number | VARCHAR(50) | - | - | ID document number |
| Address | TEXT | - | - | User address |
| Last_Login | DATETIME | - | - | Last login timestamp |
| Created_Time | DATETIME | Auto | - | Record creation time |
| Modified_Time | DATETIME | Auto | - | Last modification time |

**Notes:**
- This table is ONLY for passengers (ticket buyers)
- Employees and Admins use the separate `Employees` table
- Role column removed - all Users are passengers

**Indexes:**
- `idx_users_email` UNIQUE (Email)
- `idx_users_status` (Account_Status)

---

### 2. EMPLOYEES
Staff accounts (Admin and Employee roles)

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID (ROWID) |
| Employee_ID | VARCHAR(20) | Yes | Yes | Staff ID (e.g., "EMP001", "ADM001") |
| Full_Name | VARCHAR(255) | Yes | - | Employee's full name |
| Email | VARCHAR(255) | Yes | Yes | Login email (lowercase) |
| Password | VARCHAR(512) | Yes | - | Bcrypt hashed password |
| Phone_Number | VARCHAR(20) | - | - | Contact phone |
| Role | ENUM | Yes | - | 'Admin' \| 'Employee' |
| Department | VARCHAR(50) | - | - | 'Operations', 'Customer Service', 'IT', etc. |
| Designation | VARCHAR(50) | - | - | 'Station Master', 'Ticket Clerk', etc. |
| Permissions | TEXT | - | - | JSON permission object |
| Invited_By | BIGINT | Yes | - | ID of admin who invited |
| Invitation_Id | BIGINT | - | - | Link to Employee_Invitations |
| Joined_At | DATETIME | Yes | - | When employee registered |
| Account_Status | ENUM | Yes | - | 'Active' \| 'Inactive' \| 'Suspended' |
| Last_Login | DATETIME | - | - | Last login timestamp |
| Created_At | DATETIME | Yes | - | Record creation time |
| Updated_At | DATETIME | - | - | Last modification time |

**Notes:**
- Separate from Users table for clear role separation
- Employee_ID is auto-generated (EMP001, ADM001 format)
- Permissions is a JSON object for granular access control
- Invited_By tracks which admin added the employee

**Permissions JSON Structure:**
```json
{
  "modules": {
    "bookings": ["view", "create", "cancel"],
    "trains": ["view"],
    "stations": ["view"],
    "users": ["view"],
    "employees": ["view", "invite"],
    "reports": ["view", "export"],
    "announcements": ["view", "create", "edit"]
  },
  "admin_access": false,
  "can_invite_employees": false
}
```

**Indexes:**
- `idx_employees_email` UNIQUE (Email)
- `idx_employees_id` UNIQUE (Employee_ID)
- `idx_employees_role` (Role)
- `idx_employees_status` (Account_Status)
- `idx_employees_department` (Department)

---

### 3. STATIONS
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

### 4. TRAINS
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
| User_ID | VARCHAR(20) | Yes | - | **Polymorphic reference** to Users.ROWID or Employees.ROWID |
| User_Type | VARCHAR(20) | Yes | - | 'user' (passenger) \| 'employee' (staff/admin) |
| User_Email | VARCHAR(255) | Yes | - | User email (denormalized) |
| User_Role | VARCHAR(20) | Yes | - | 'Passenger' \| 'Employee' \| 'Admin' |
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
- `idx_sessions_user_type` (User_Type)
- `idx_sessions_active` (Is_Active)
- `idx_sessions_expires` (Expires_At)

**User_Type Values:**
- **'user'**: Session belongs to a passenger (User_ID references Users.ROWID)
- **'employee'**: Session belongs to staff/admin (User_ID references Employees.ROWID)

**CRITICAL CONSTRAINTS:**

⚠️ **DO NOT ADD FOREIGN KEY CONSTRAINT ON User_ID**
- User_ID is a **polymorphic reference** that can point to either Users.ROWID or Employees.ROWID
- Adding FK constraint to Users table will break employee/admin logins
- Use User_Type field to determine which table User_ID references
- Validation MUST be enforced at application level, not database level

**Migration Note (2026-04-08)**:
If Sessions table already exists with FK constraint on User_ID → Users.ROWID:
1. Open Catalyst CloudScale Console
2. Navigate to Tables → Sessions
3. Click on User_ID column settings
4. Remove Foreign Key reference to Users table
5. Save changes

**Usage Notes:**
- Session_ID: Generated with `secrets.token_urlsafe(32)` - 256-bit entropy
- User_ID can reference either Users.ROWID (if User_Type='user') or Employees.ROWID (if User_Type='employee')
- Max 3 concurrent sessions per user (oldest auto-revoked)
- 24-hour session timeout with sliding window
- Idle timeout: 6 hours of inactivity
- CSRF token required for POST/PUT/DELETE/PATCH requests
- **CRITICAL**: User_Type column MUST be added before deploying Phase 1 code

**Application-Level Validation:**
```python
# In session_service.py - validate User_ID references before session creation
def validate_user_reference(user_id: str, user_type: str) -> bool:
    if user_type == 'user':
        user = cloudscale_repo.get_user_by_id(user_id)
        return user is not None
    elif user_type == 'employee':
        employee = cloudscale_repo.get_employee_by_id(user_id)
        return employee is not None
    return False
```

---

### 17. SESSION_AUDIT_LOG
Security audit trail for session-related events

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID (ROWID) |
| Event_Type | VARCHAR(50) | Yes | - | Type of security event |
| Session_ID | FOREIGN KEY | - | - | FK to Sessions.ID (optional) |
| User_ID | VARCHAR(20) | - | - | **Polymorphic reference** to Users.ROWID or Employees.ROWID |
| User_Email | VARCHAR(255) | - | - | User email at time of event |
| IP_Address | VARCHAR(45) | - | - | Client IP address |
| Event_Timestamp | DATETIME | Yes | - | When event occurred |
| Details | TEXT | - | - | JSON with additional data |
| Severity | VARCHAR(20) | - | - | INFO, WARNING, ERROR, CRITICAL |
| Created_Time | DATETIME | Auto | - | Record creation time |

**Constraints:**
- **Session_ID**: References Sessions.ROWID
  - Can be NULL/omitted if session doesn't exist
  - CANNOT be empty string or invalid value
- **User_ID**: **NO FOREIGN KEY** - polymorphic reference to Users.ROWID or Employees.ROWID
  - Can be NULL/omitted if user doesn't exist (e.g., failed login)
  - CANNOT be empty string, zero, or negative value
  - Code automatically omits if no valid reference
  - **DO NOT add FK constraint** - same reason as Sessions.User_ID (polymorphic reference)

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
| EMPLOYEE_LOGIN_SUCCESS | INFO | Employee/Admin login succeeded |
| EMPLOYEE_LOGIN_FAILED | WARNING | Employee/Admin login failed |
| USER_LOGIN_SUCCESS | INFO | Passenger login succeeded |
| USER_LOGIN_FAILED | WARNING | Passenger login failed |

**Indexes:**
- `idx_audit_user_id` (User_ID)
- `idx_audit_event_type` (Event_Type)
- `idx_audit_timestamp` (Event_Timestamp)

**Important Notes:**
- Session_ID can be NULL if session doesn't exist yet
- User_ID has NO foreign key constraint (polymorphic reference)
- Details field stores user_type to distinguish Users vs Employees table reference
- When user doesn't exist (failed login), User_ID is omitted from record
- Session token stored in Details.session_ref when Sessions.ROWID unavailable

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

### 20. EMPLOYEE_INVITATIONS
Employee invitation tracking for admin-initiated onboarding

| Field | Type | Required | Unique | Description |
|-------|------|----------|--------|-------------|
| ID | BIGINT | PK | Yes | Auto-generated record ID (ROWID) |
| Invitation_Token | VARCHAR(255) | Yes | Yes | Secure invitation token (URL-safe) |
| Email | VARCHAR(255) | Yes | - | Invitee email (lowercase) |
| Role | ENUM | Yes | - | 'Admin' \| 'Employee' - role to assign |
| Department | VARCHAR(50) | - | - | Pre-fill for registration |
| Designation | VARCHAR(50) | - | - | Pre-fill for registration |
| Invited_By | BIGINT | Yes | - | Admin ID (→ Employees.ROWID) |
| Invited_At | DATETIME | Yes | - | Invitation creation time |
| Expires_At | DATETIME | Yes | - | Expiration timestamp (7 days default) |
| Is_Used | VARCHAR(10) | Yes | - | 'true' \| 'false' |
| Used_At | DATETIME | - | - | When invitation was used |
| Registered_Employee_Id | BIGINT | - | - | New employee record (→ Employees.ROWID) |
| Created_At | DATETIME | Yes | - | Timestamp used for sorting |

**Notes:**
- Tokens are generated using `secrets.token_urlsafe(32)` (256-bit entropy)
- Tokens are single-use and expire after 7 days (configurable)
- Email must exactly match the invitation during registration
- Role determines what role the new employee will have
- Department/Designation pre-fill the registration form

**Indexes:**
- `idx_invites_token` UNIQUE (Invitation_Token)
- `idx_invites_email_status` (Email, Is_Used, Expires_At)
- `idx_invites_invited_by` (Invited_By)

---

## RELATIONSHIPS DIAGRAM

```
┌─────────────────┐                              ┌─────────────────┐
│     USERS       │                              │   EMPLOYEES     │
│  (Passengers)   │                              │  (Staff/Admin)  │
├─────────────────┤                              ├─────────────────┤
│ ROWID (PK)      │                              │ ROWID (PK)      │
│ Email           │                              │ Employee_ID     │
│ Password        │                              │ Email           │
│ Full_Name       │                              │ Password        │
│ Account_Status  │                              │ Role            │
└────────┬────────┘                              │ Department      │
         │                                       │ Permissions     │
         │ Books tickets                         │ Invited_By ─────┼──┐
         ▼                                       └────────┬────────┘  │
┌─────────────────┐     ┌──────────────┐     ┌───────────┴───────┐   │
│   BOOKINGS      │>────│   TRAINS     │     │    SESSIONS       │   │
├─────────────────┤     └──────────────┘     ├───────────────────┤   │
│ User_ID (FK)    │            │             │ User_ID (FK)      │   │
│ Train_ID (FK)   │            │             │ User_Type         │   │
│ PNR             │            ▼             │ (user/employee)   │   │
└─────────────────┘     ┌──────────────┐     └───────────────────┘   │
         │              │ TRAIN_ROUTES │                             │
         ▼              └──────────────┘                             │
┌─────────────────┐            │                                     │
│   PASSENGERS    │            ▼             ┌───────────────────┐   │
└─────────────────┘     ┌──────────────┐     │EMPLOYEE_INVITATIONS│   │
                        │ ROUTE_STOPS  │     ├───────────────────┤   │
                        └──────────────┘     │ Email             │   │
                                             │ Role              │   │
┌─────────────────┐     ┌──────────────┐     │ Invited_By (FK) ──┼───┘
│   ADMIN_LOGS    │     │    FARES     │     │ Registered_Emp_Id │
├─────────────────┤     └──────────────┘     └───────────────────┘
│ User_ID (FK)    │            │
│ (→ Employees)   │            │
└─────────────────┘     ┌──────────────┐
                        │   STATIONS   │
                        └──────────────┘
```

**Key Relationships:**
- `Users` → `Bookings` (1:N) - Passengers book tickets
- `Employees` → `Sessions` (1:N) - Staff login sessions
- `Employees` → `Employee_Invitations` (1:N) - Admin invites employees
- `Employee_Invitations` → `Employees` (1:1) - Invitation creates employee
- `Employees` → `Admin_Logs` (1:N) - Admin actions audit trail
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

### Authentication & User Endpoints
| Endpoint | Method | Table | Description |
|----------|--------|-------|-------------|
| /session/register/initiate | POST | Users, OTP_Tokens | Start passenger registration |
| /session/register/verify | POST | Users | Complete registration with OTP |
| /session/login | POST | Users | Passenger login |
| /session/employee/login | POST | Employees | Employee/Admin login |
| /session/logout | POST | Sessions | Logout (invalidate session) |
| /session/validate | GET | Sessions | Validate current session |

### Employee Management Endpoints (Admin only)
| Endpoint | Method | Table | Description |
|----------|--------|-------|-------------|
| /admin/employees/invite | POST | Employee_Invitations | Send employee invitation |
| /admin/employees/invitations | GET | Employee_Invitations | List sent invitations |
| /admin/employees | GET | Employees | List all employees |
| /admin/employees/{id} | GET | Employees | Get employee details |
| /admin/employees/{id} | PUT | Employees | Update employee |
| /admin/employees/{id}/permissions | PUT | Employees | Update permissions |

### Core Business Endpoints
| Endpoint | Method | Table | Description |
|----------|--------|-------|-------------|
| /stations | GET | Stations | List stations |
| /stations | POST | Stations | Create station (admin) |
| /trains | GET | Trains | Search trains |
| /trains | POST | Trains | Create train (admin) |
| /bookings | GET | Bookings | List user bookings |
| /bookings | POST | Bookings | Create booking |
| /bookings/pnr/{pnr} | GET | Bookings | PNR lookup |
| /users | GET | Users | List passengers (admin) |
| /fares/calculate | POST | Fares | Calculate fare |
| /train-routes | GET | Train_Routes | List routes |
| /announcements | GET | Announcements | List announcements |
| /admin/logs | GET | Admin_Logs | Audit logs (admin) |

---

## STORAGE ESTIMATION

| Table | Records (Small) | Records (Large) | Size Est. |
|-------|-----------------|-----------------|-----------|
| Users (Passengers) | 10K | 1M | 50MB - 5GB |
| Employees | 50 | 1K | 1MB - 10MB |
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
| Sessions | 1K | 50K | 5MB - 250MB |
| Employee_Invitations | 100 | 5K | 1MB - 50MB |
| OTP_Tokens | 1K | 100K | 1MB - 100MB |
| **TOTAL** | ~500K | ~45M | **~2GB - ~175GB** |

---

## MIGRATION CHECKLIST

- [ ] Create all 20 tables in Catalyst CloudScale
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

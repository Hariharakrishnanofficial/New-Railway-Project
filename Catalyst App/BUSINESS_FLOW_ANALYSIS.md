# Railway Ticketing System - Business Flow Analysis
## Code-Driven Implementation Analysis v1.0

---

## Table of Contents
1. [User to PNR Generation Flow](#1-user-to-pnr-generation-flow)
2. [Master Data Handling Flow](#2-master-data-handling-flow)
3. [Cancellation & Refund Flow](#3-cancellation--refund-flow)
4. [Key Code References](#4-key-code-references)

---

## 1. User to PNR Generation Flow

### 1.1 Flow Overview

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Client    │───>│ routes/      │───>│ services/       │───>│ Zoho Creator │
│   (POST)    │    │ bookings.py  │    │ booking_service │    │ CloudScale   │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                          │                    │
                          │                    ├─── utils/fare_helper.py
                          │                    └─── utils/seat_allocation.py
                          ▼
                   PNR + Booking Record
```

### 1.2 Step-by-Step Business Flow

#### STEP 1: API Request Reception
**Code**: `routes/bookings.py:24-36`

```
POST /api/bookings
Content-Type: application/json

{
  "train_id": "1234567890123456789",
  "user_id": "9876543210987654321",
  "Journey_Date": "2026-04-15",
  "Class": "3A",
  "Quota": "General",
  "Passengers": [
    { "name": "John Doe", "age": 30, "gender": "Male", "berthPref": "Lower" }
  ]
}
```

**Business Action**: Route handler validates JSON payload existence, delegates to `BookingService.create()`.

---

#### STEP 2: Input Validation & Normalization
**Code**: `services/booking_service.py:61-94`

| Validation Check | Rule | Exception |
|------------------|------|-----------|
| train_id | Required | `ValidationError` |
| user_id | Required | `ValidationError` |
| Journey_Date | Required | `ValidationError` |
| Passengers | Min 1, Max 6 | `ValidationError` |

**Passenger Normalization Logic**:
```python
normalized_passengers = []
for p in passengers:
    np = {
        "Name": p.get("name") or p.get("Name", ""),
        "Age": p.get("age") or p.get("Age", ""),
        "Gender": p.get("gender") or p.get("Gender", "Male"),
        "Berth_Preference": p.get("berthPref") or p.get("Berth_Preference", "No Preference")
    }
    normalized_passengers.append(np)
```

---

#### STEP 3: Date Validation
**Code**: `services/booking_service.py:96-109`

| Check | Condition | Error |
|-------|-----------|-------|
| Past Date | `Journey_Date < today` | `InvalidDateError` |
| Advance Limit | `Journey_Date > today + 120 days` | `InvalidDateError` |
| Format | Must be `YYYY-MM-DD` or `dd-MMM-yyyy` | `InvalidDateError` |

---

#### STEP 4: Train Existence Check
**Code**: `services/booking_service.py:111-114`

```python
train = zoho_repo.get_train_cached(train_id)
if not train:
    raise TrainNotFoundError(train_id)
```

**Business Logic**: Uses cached train data (1-hour TTL) to reduce API calls.

---

#### STEP 5: User Validation & Booking Limit Check
**Code**: `services/booking_service.py:116-128`

| User Status | Monthly Booking Limit |
|-------------|----------------------|
| Aadhaar Verified | 12 bookings/month |
| Not Verified | 6 bookings/month |

```python
is_verified = str(user.get("Is_Aadhar_Verified", "false")).lower() == "true"
max_limit = 12 if is_verified else 6
monthly_count = zoho_repo.count_monthly_bookings(user_id, start_month)
if monthly_count >= max_limit:
    raise BookingLimitError(max_limit)
```

---

#### STEP 6: Duplicate Booking Check
**Code**: `services/booking_service.py:130-142`

```python
dup_criteria = (
    CriteriaBuilder()
    .id_eq("User_ID", user_id)
    .id_eq("Train_ID", train_id)
    .eq("Journey_Date", zoho_date)
    .ne("Booking_Status", "Cancelled")
    .build()
)
```

**Business Logic**: Prevents same user from booking same train on same date twice (unless previous is cancelled).

---

#### STEP 7: Fare Calculation
**Code**: `utils/fare_helper.py:18-120`

**Fare Resolution Priority**:
1. **Dynamic Fare** from `Fares` table (if `Dynamic_Fare > 0`)
2. **Base Fare** from `Fares` table (if record exists)
3. **Train Default Fare** from `Trains.Fare_{class}` field (fallback)

**Tatkal Surcharge Logic**:
```python
if quota in ('tatkal', 'premium tatkal', 'tq', 'pt'):
    if tatkal_fare_from_record > 0:
        total_fare += tatkal_fare_from_record
    else:
        surcharge_pct = _get_tatkal_surcharge(quota)  # From Quotas table
        if surcharge_pct > 0:
            total_fare += base_fare * (surcharge_pct / 100.0)
        else:
            total_fare += base_fare * 0.30  # Default 30% fallback
```

**Full IRCTC-Style Calculation** (routes/fares.py:147-272):
```
Final Fare = Base Fare
           + Reservation Charge (₹15-60 by class)
           + Superfast Surcharge (₹15-75 if applicable)
           + Tatkal Premium (30% capped)
           - Concession Discount (0-50%)
           + GST 5% (AC classes only)
           + Catering (optional: ₹150-350)
           + Convenience Fee (₹17.70 non-AC / ₹35.40 AC)
```

---

#### STEP 8: Seat Allocation (CNF/RAC/WL)
**Code**: `utils/seat_allocation.py:206-311`

**Allocation Algorithm**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    SEAT ALLOCATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Fetch/Create Train_Inventory record (train + date + class)  │
│  2. Load Coach Layout JSON from Coach_Layouts table             │
│  3. Parse Confirmed_Seats_JSON to get occupied set              │
│  4. For each passenger:                                         │
│     ├─ IF seats available: Allocate CNF (try preference first)  │
│     ├─ ELSE IF RAC slots available: Allocate RAC               │
│     └─ ELSE: Allocate WL (Waitlist)                            │
│  5. Update Train_Inventory with new counts                      │
│  6. Invalidate cache                                            │
└─────────────────────────────────────────────────────────────────┘
```

**Seat Finding Logic** (`find_available_seat`):
```python
# First pass: Match berth preference (LOWER, MIDDLE, UPPER)
for row in layout_data:
    for seat in row:
        if seat.get('is_seat') and seat_id not in occupied_seats:
            if seat.get('berth_type') == preference:
                return seat_info

# Second pass: Any available seat
for row in layout_data:
    for seat in row:
        if seat.get('is_seat') and seat_id not in occupied_seats:
            return seat_info
```

**Status Assignment**:
| Condition | Status Format | Example |
|-----------|---------------|---------|
| Confirmed | `CNF/{coach}/{seat}` | `CNF/S1/14` |
| RAC | `RAC/{number}` | `RAC/5` |
| Waitlist | `WL/{number}` | `WL/12` |

---

#### STEP 9: PNR Generation
**Code**: `services/booking_service.py:26-48`

**Format**: `PNR` + 8 alphanumeric chars = 11 total characters
**Example**: `PNRX7K2P9W1`

**Uniqueness Check**:
```python
for _ in range(10):  # Max 10 attempts
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    pnr = f"PNR{suffix}"
    criteria = CriteriaBuilder().eq("PNR", pnr).build()
    existing = zoho_repo.get_records(TABLES['bookings'], criteria=criteria, limit=1)
    if not existing:
        return pnr
```

---

#### STEP 10: Record Creation in Zoho
**Code**: `services/booking_service.py:159-217`

**Payload Structure**:
```python
payload = {
    "PNR":             pnr,
    "User_ID":         user_id,
    "Train_ID":        train_id,
    "Journey_Date":    zoho_date,        # Format: "25-Apr-2026"
    "Class":           cls,
    "Quota":           quota,
    "Num_Passengers":  len(passengers),
    "Total_Fare":      total_fare,
    "Booking_Status":  booking_status,   # "confirmed" | "rac" | "waitlisted"
    "Payment_Status":  "pending",
    "Payment_Method":  "online",
    "Passengers":      passengers,       # JSON array stored as string
    "Booking_Time":    "25-Mar-2026 14:30:00"
}
```

---

#### STEP 11: Passenger Form Sync
**Code**: `services/booking_service.py:219-250`

After main booking record is created, individual passenger records are created in the `Passengers` form:

```python
for p in passengers:
    pax_payload = {
        "Passenger_Name":  p.get("Name"),
        "Age":             p.get("Age"),
        "Gender":          p.get("Gender"),
        "Booking_ID":      booking_id,  # Link to parent booking
        "Current_Status":  p.get("Current_Status"),
        "Coach":           p.get("Coach"),
        "Seat_Number":     p.get("Seat_Number"),
        "Berth_Type":      p.get("Berth"),
    }
    zoho_repo.create_record(passengers_table, pax_payload)
```

---

#### STEP 12: Cache Invalidation & Response
**Code**: `services/booking_service.py:208-217`

```python
zoho_repo.invalidate_inventory_cache(train_id, zoho_date, cls)

return {
    "PNR":            pnr,
    "Booking_Status": booking_status,
    "Total_Fare":     total_fare,
    "passengers":     passengers,
    "record":         result.get("data", {}),
}
```

---

### 1.3 Complete Booking Flow Diagram

```
User Request
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           VALIDATION PHASE                                  │
├────────────────────────────────────────────────────────────────────────────┤
│  1. Required fields check (train_id, user_id, Journey_Date, passengers)    │
│  2. Passenger count validation (1-6)                                       │
│  3. Date range validation (not past, within 120 days)                      │
│  4. Train existence check (cached lookup)                                  │
│  5. User existence + Aadhaar verification status                           │
│  6. Monthly booking limit check (6 or 12)                                  │
│  7. Duplicate booking prevention                                           │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           CALCULATION PHASE                                 │
├────────────────────────────────────────────────────────────────────────────┤
│  1. Resolve base fare (Fares table → Train record fallback)                │
│  2. Apply Tatkal surcharge if quota = TQ/PT                                │
│  3. Calculate total = fare_per_person × chargeable_count                   │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           ALLOCATION PHASE                                  │
├────────────────────────────────────────────────────────────────────────────┤
│  1. Get/Create Train_Inventory for train+date+class                        │
│  2. Load coach Layout_JSON                                                 │
│  3. For each passenger:                                                    │
│     - Try CNF allocation (berth preference → any available)               │
│     - Fallback to RAC if CNF full                                         │
│     - Fallback to WL if RAC full                                          │
│  4. Update inventory counts (Confirmed_Seats_JSON, RAC_Count, WL_Count)    │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           PERSISTENCE PHASE                                 │
├────────────────────────────────────────────────────────────────────────────┤
│  1. Generate unique PNR (PNR + 8 alphanumeric)                             │
│  2. Create Bookings record with all payload data                           │
│  3. Create individual Passengers records linked to booking                 │
│  4. Invalidate inventory cache                                             │
└────────────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                              RESPONSE                                       │
├────────────────────────────────────────────────────────────────────────────┤
│  { PNR, Booking_Status, Total_Fare, passengers[], record }                 │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Master Data Handling Flow

### 2.1 Stations Master
**Code**: `routes/stations.py`

#### Creation Flow
```
POST /api/stations (Admin Only)
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Validate Required Fields:                          │
│  - Station_Code (3-5 chars, UPPERCASE)             │
│  - Station_Name                                     │
│  - City                                             │
│  - State                                            │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Build Payload:                                     │
│  - Station_Code, Station_Name, City, State          │
│  - Zone, Division (optional)                        │
│  - Station_Type (default: "Way Station")            │
│  - Number_of_Platforms, Lat/Long (optional)         │
│  - Is_Active (default: true)                        │
└─────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  zoho.create_record(TABLES['stations'], payload)    │
│  cache.delete('stations:all')                       │
└─────────────────────────────────────────────────────┘
```

#### Read Flow (Cached)
```python
# Uses 24-hour cache for station list
records = zoho_repo.get_all_stations_cached()

# Python-side filtering for search/city queries
if search:
    records = [r for r in records
               if search.lower() in r.get('Station_Code', '').lower()
               or search.lower() in r.get('Station_Name', '').lower()]
```

**Usage in Booking**: Station IDs are used for `Boarding_Station` and `Deboarding_Station` in bookings.

---

### 2.2 Trains Master
**Code**: `routes/trains.py`

#### Creation Flow
```
POST /api/trains (Admin Only)
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Build Payload with Full Train Configuration:                        │
├─────────────────────────────────────────────────────────────────────┤
│  Identity:     Train_Number, Train_Name, Train_Type                  │
│  Route:        From_Station (lookup), To_Station (lookup)            │
│  Schedule:     Departure_Time, Arrival_Time, Duration, Run_Days      │
│  Fares:        Fare_SL, Fare_3A, Fare_2A, Fare_1A, Fare_CC, Fare_EC │
│  Capacity:     Total_Seats_SL, Total_Seats_3A, etc.                 │
│  Availability: Available_Seats_SL = Total_Seats_SL (initial)        │
│  Status:       Is_Active, Running_Status, Delay_Minutes             │
└─────────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  zoho_repo.create_record(TABLES['trains'], payload) │
│  zoho_repo.invalidate_train_cache()                 │
│  log_admin_action('CREATE_TRAIN', details)          │
└─────────────────────────────────────────────────────┘
```

#### Search/Filter Flow
**Code**: `routes/trains.py:77-121`

```python
GET /api/trains?source=MAS&destination=SBC&journey_date=2026-04-15

# 1. Get cached train list (1-hour TTL)
records = zoho_repo.get_all_trains_cached()

# 2. Python-side filtering
if source:
    records = [r for r in records if get_code(r.get('From_Station')) == source]
if destination:
    records = [r for r in records if get_code(r.get('To_Station')) == destination]

# 3. Journey date filter (checks Run_Days field)
if journey_date:
    day_name = DAY_ABBR[datetime.strptime(journey_date, '%Y-%m-%d').weekday()]
    records = [r for r in records if day_name in r.get('Run_Days', '').split(',')]
```

#### Vacancy Check Flow
**Code**: `routes/trains.py:315-394`

```
GET /api/trains/{train_id}/vacancy?date=2026-04-15
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. Check inventory cache: inventory:{train_id}:{date}              │
│  2. If not cached: Query Train_Inventory table                      │
│  3. Aggregate by class: total, confirmed, rac, waitlist             │
│  4. Calculate: available = total - confirmed                        │
│  5. Set status: "AVAILABLE-{n}" | "RAC {n}" | "WL {n}"             │
│  6. Cache result (5 min TTL)                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2.3 Train Routes & Stops
**Code**: `routes/train_routes.py`

#### Data Model
```
Train_Routes (Parent)
    │
    └── Route_Stops (Child Records)
            ├── Sequence: 1
            ├── Station_Code: MAS
            ├── Station_Name: Chennai Central
            ├── Arrival_Time: null
            ├── Departure_Time: 06:00
            ├── Halt_Minutes: 0
            ├── Distance_KM: 0
            └── Day_Count: 1
```

#### Route Creation Flow
```
POST /api/train-routes (Admin Only)
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. Extract train_id from request                                   │
│  2. Check for existing route (prevent duplicates)                   │
│  3. Build Route_Stops array from nested data                        │
│  4. Create Train_Routes record with embedded stops                  │
└─────────────────────────────────────────────────────────────────────┘
```

#### Usage in Booking/Search

**Train Schedule** (`/api/trains/{id}/schedule`):
```python
# 1. Find Train_Routes record for the train
route_result = zoho_repo.get_all_records(TABLES['train_routes'],
                                         criteria=f'Trains = {train_id}')

# 2. Fetch Route_Stops for that route
stops_result = zoho_repo.get_all_records(TABLES['route_stops'],
                                         criteria=f'Train_Routes = {route_id}')

# 3. Sort by Sequence and return
stops.sort(key=lambda r: int(r.get('Sequence') or 0))
```

**Connecting Trains Search** (`/api/trains/connecting?from=MAS&to=SBC`):
```python
# 1. Fetch all routes with stops in 2 API calls
all_routes = _fetch_all_routes_full()

# 2. Index stops by train_id
for route in all_routes:
    train_stops[train_id] = sorted(stops, key=lambda s: s.get('Sequence'))

# 3. Find direct trains (from_idx < to_idx in same route)
for train_id, stops in train_stops.items():
    from_idx = find_stop_index(stops, from_station)
    to_idx = find_stop_index(stops, to_station)
    if from_idx != -1 and to_idx != -1 and from_idx < to_idx:
        direct_trains.append(train_info)
```

---

### 2.4 Fares Master
**Code**: `routes/fares.py`

#### Fare Record Structure
```
Fares Table
├── Train_ID (foreign key)
├── From_Station_ID (foreign key)
├── To_Station_ID (foreign key)
├── Class (SL, 3A, 2A, 1A, CC, EC)
├── Base_Fare (decimal)
├── Dynamic_Fare (decimal, optional)
├── Tatkal_Fare (decimal, optional)
├── Concession_Type (General, Senior, Student, etc.)
├── Concession_Percent (0-50%)
├── Distance_KM (optional)
├── Effective_From / Effective_To (date range)
└── Is_Active (boolean)
```

#### Fare Lookup Priority (in booking)
**Code**: `utils/fare_helper.py:48-97`

```
┌──────────────────────────────────────────────────────────────────┐
│  PRIORITY 1: Dynamic Fare from Fares Table                       │
│  ─────────────────────────────────────────                       │
│  Query: Train + From_Station + To_Station + Class + Is_Active    │
│  Use: Dynamic_Fare if > 0, else Base_Fare                        │
├──────────────────────────────────────────────────────────────────┤
│  PRIORITY 2: Train Default Fare (Fallback)                       │
│  ─────────────────────────────────────────                       │
│  Use: Trains.Fare_{class} field                                  │
│  Example: Trains.Fare_SL, Trains.Fare_3A                         │
└──────────────────────────────────────────────────────────────────┘
```

#### Full Fare Calculation Endpoint
**Code**: `routes/fares.py:147-272`

```
POST /api/fares/calculate
{
  "train_id": "...",
  "class": "3AC",
  "passenger_count": 2,
  "concession_type": "Senior",
  "journey_date": "2026-04-15",
  "quota": "GN",
  "opt_catering": false
}
```

**Calculation Breakdown**:
| Component | Logic | Example |
|-----------|-------|---------|
| Base Fare | From Fares/Train record | ₹1500 |
| Reservation Charge | Class-based (₹15-60) | ₹40 (3AC) |
| Superfast Surcharge | If train_type=SUPERFAST | ₹45 (3AC) |
| Tatkal Premium | 30% capped (min/max by class) | ₹300 |
| Concession | Senior=40%, Student=50% | -₹600 |
| GST | 5% on AC classes | ₹65 |
| Catering | Optional (₹150-350) | ₹0 |
| Convenience Fee | ₹17.70 (non-AC) / ₹35.40 (AC) | ₹35.40 |
| **Total** | Sum all | **₹1385.40** |

---

### 2.5 Master Data Influence on Booking

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    HOW MASTER DATA AFFECTS BOOKING                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STATIONS ─────────────────────────────────────────────────────────────────│
│  ├─ Validate Boarding_Station exists                                        │
│  ├─ Validate Deboarding_Station exists                                      │
│  └─ Used in fare lookup (From_Station, To_Station in Fares table)          │
│                                                                             │
│  TRAINS ───────────────────────────────────────────────────────────────────│
│  ├─ Validate train exists and is active                                     │
│  ├─ Get total seat capacity (Total_Seats_{class})                          │
│  ├─ Get default fare fallback (Fare_{class})                               │
│  ├─ Check Run_Days for journey_date validity                               │
│  └─ Get Train_Type for superfast surcharge                                 │
│                                                                             │
│  TRAIN_ROUTES ─────────────────────────────────────────────────────────────│
│  ├─ Validate intermediate stations for boarding/deboarding                  │
│  ├─ Calculate distance for fare computation                                 │
│  └─ Provide schedule information on ticket                                  │
│                                                                             │
│  FARES ────────────────────────────────────────────────────────────────────│
│  ├─ Get Base_Fare for specific route+class                                 │
│  ├─ Get Dynamic_Fare if dynamic pricing enabled                            │
│  ├─ Get Tatkal_Fare for tatkal quota                                       │
│  └─ Apply concession percentage                                            │
│                                                                             │
│  COACH_LAYOUTS ────────────────────────────────────────────────────────────│
│  ├─ Get Layout_JSON for seat allocation                                    │
│  ├─ Define berth types (LOWER, MIDDLE, UPPER, etc.)                        │
│  └─ Define coach capacity and seat numbering                               │
│                                                                             │
│  TRAIN_INVENTORY ──────────────────────────────────────────────────────────│
│  ├─ Track daily seat availability per train+class                          │
│  ├─ Store Confirmed_Seats_JSON (occupied seats)                            │
│  └─ Track RAC_Count and Waitlist_Count                                     │
│                                                                             │
│  QUOTAS ───────────────────────────────────────────────────────────────────│
│  ├─ Define quota-specific seat limits                                       │
│  ├─ Provide Surcharge_Percentage for Tatkal                                │
│  └─ Control booking window (opens at 10:00 for Tatkal)                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Cancellation & Refund Flow

### 3.1 Full Cancellation
**Code**: `services/booking_service.py:256-322`

```
POST /api/bookings/{booking_id}/cancel
     │
     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. Fetch booking record by ID                                      │
│  2. Validate not already cancelled                                  │
│  3. Calculate refund based on cancellation policy                   │
│  4. Update booking: Booking_Status='cancelled', Refund_Amount       │
│  5. Free confirmed seats from inventory                            │
│  6. Promote RAC/WL passengers to fill freed seats                  │
│  7. Invalidate inventory cache                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Refund Calculation
**Code**: `utils/seat_allocation.py:459-540`

| Hours Before Departure | AC Class | Non-AC (SL/2S) |
|------------------------|----------|----------------|
| > 48 hours | 25% deduction (min ₹90) | ₹60 flat deduction |
| 12-48 hours | 50% deduction | 25% deduction (min ₹60) |
| < 12 hours | 100% (no refund) | 100% (no refund) |
| Tatkal (TQ/PT) | No refund | No refund |

### 3.3 Waitlist Promotion
**Code**: `utils/seat_allocation.py:543-628`

```python
def promote_waitlist(train_id, cls, journey_date, num_seats_to_fill):
    # 1. Fetch RAC and WL bookings, sorted by Booking_Time
    rac_bookings = sorted([...], key=lambda b: b.get('Booking_Time'))
    wl_bookings = sorted([...], key=lambda b: b.get('Booking_Time'))

    # 2. Re-run allocation for eligible bookings
    for booking in promotable_bookings:
        updated_passengers, new_status = process_booking_allocation(...)
        zoho.update_record(TABLES['bookings'], booking['ID'], {
            'Passengers': json.dumps(updated_passengers),
            'Booking_Status': new_status
        })
```

---

## 4. Key Code References

| Flow Component | File | Key Functions/Methods |
|----------------|------|----------------------|
| Booking API | `routes/bookings.py` | `create_booking()`, `cancel_booking()`, `get_booking_by_pnr()` |
| Booking Logic | `services/booking_service.py` | `BookingService.create()`, `.cancel()`, `.partial_cancel()` |
| Seat Allocation | `utils/seat_allocation.py` | `process_booking_allocation()`, `find_available_seat()`, `get_train_inventory()` |
| Fare Calculation | `utils/fare_helper.py` | `get_fare_for_journey()`, `_get_tatkal_surcharge()` |
| IRCTC Fare | `routes/fares.py` | `calculate_fare()` |
| Refund Logic | `utils/seat_allocation.py` | `calculate_refund()`, `process_booking_cancellation()` |
| Waitlist Promotion | `utils/seat_allocation.py` | `promote_waitlist()` |
| Train CRUD | `routes/trains.py` | `create_train()`, `get_trains()`, `get_train_vacancy()` |
| Station CRUD | `routes/stations.py` | `create_station()`, `get_stations()` |
| Route CRUD | `routes/train_routes.py` | `create_train_route()`, `get_train_routes()`, `_fetch_all_routes_full()` |
| Fare CRUD | `routes/fares.py` | `create_fare()`, `get_fares()` |
| Data Repository | `repositories/cloudscale_repository.py` | `zoho_repo`, `CriteriaBuilder` |
| Cache Manager | `repositories/cache_manager.py` | `cache.get()`, `cache.set()`, `cache.delete()` |

---

*Document generated from actual codebase analysis*
*Version: 1.0 | Date: 2026-03-25*

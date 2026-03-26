# Zoho Catalyst CloudScale Database - Quick Reference

## 📊 14 Tables Overview

| # | Table | Records | Purpose |
|----|-------|---------|---------|
| 1 | **Users** | ~100K | Authentication & profiles |
| 2 | **Stations** | ~1K | Railway stations |
| 3 | **Trains** | ~10K | Train master data |
| 4 | **Train_Routes** | ~100K | Train stop sequences |
| 5 | **Coach_Layouts** | ~6 | Coach type configs (1A, 2A, 3A, SL, UR, FC) |
| 6 | **Train_Inventory** | ~60K | Coaches per train |
| 7 | **Fares** | ~500K | Route + class fare rules |
| 8 | **Bookings** | ~5M | Passenger bookings |
| 9 | **Passengers** | ~25M | Passenger details in bookings |
| 10 | **Quotas** | ~50K | Seat quotas (General, Tatkal, SC, etc.) |
| 11 | **Announcements** | ~1K | Train alerts/updates |
| 12 | **Admin_Logs** | ~500K | Audit trail |
| 13 | **Settings** | ~50 | System configuration |
| 14 | **Password_Reset_Tokens** | ~10K | Temporary reset tokens |

---

## 💾 Storage Estimation

```
Small Deployment (100K Users):
├─ Users:      ~50 MB
├─ Bookings:   ~500 MB (5M bookings × 100 bytes)
├─ Passengers: ~2.5 GB (25M records × 100 bytes)
├─ Fares:      ~200 MB
├─ Logs:       ~250 MB
└─ Total:      ~3.5 GB

Large Deployment (1M Users):
└─ Total:      ~35 GB (scale linearly)
```

**Catalyst CloudScale Limits:**
- Max table size: Unlimited (auto-scale)
- Auto-backup: Daily
- Recommended: Monitor with `SELECT COUNT(*) FROM table` quarterly

---

## 🔑 Key Relationships

```
Users (1) ──────→ (M) Bookings
                  ↓
              Passengers (M)

Trains (1) ──────→ (M) Bookings
     ↓              ↓
     ├─ (M) Train_Routes
     ├─ (M) Train_Inventory ──→ Coach_Layouts
     ├─ (M) Quotas
     └─ (M) Fares

Stations (1) ──────→ (M) Train_Routes

Bookings (1) ──────→ (M) Passengers
```

---

## 🚀 Setup Instructions

### Step 1: Deploy Setup Script
```bash
# Upload database_setup.py to Catalyst Functions
# Call the endpoint: POST /setup-database

curl -X POST https://your-catalyst-domain/setup-database \
  -H "Authorization: Bearer <token>"
```

### Step 2: Verify Tables Created
```python
from zcatalyst_sdk import initialize

catalyst = initialize()
datastore = catalyst.data_store

# List all tables
tables = datastore.get_tables()
print(f"Created {len(tables)} tables")
```

### Step 3: Insert Initial Data
```python
# Insert sample stations
stations = datastore.get_table('Stations')
stations.insert([
    {'station_code': 'MAS', 'station_name': 'Chennai Central', 'city': 'Chennai'},
    {'station_code': 'DEL', 'station_name': 'New Delhi', 'city': 'Delhi'},
    {'station_code': 'BOM', 'station_name': 'Mumbai Central', 'city': 'Mumbai'},
])
```

---

## 📝 Common Queries (ZCQL)

### Search Trains
```zcql
-- Find trains between two cities
SELECT t.*, s1.station_name as source, s2.station_name as destination
FROM Trains t
JOIN Stations s1 ON t.source_station_id = s1.station_id
JOIN Stations s2 ON t.destination_station_id = s2.station_id
WHERE s1.city = 'Chennai' AND s2.city = 'Delhi'
ORDER BY t.departure_time;
```

### Check Availability
```zcql
-- Check available seats for a route/class
SELECT q.quota_type, q.available_seats, q.booked_seats
FROM Quotas q
WHERE q.train_id = ?
  AND q.class_code = '2A'
  AND q.available_seats > 0
LIMIT 10;
```

### Booking Status
```zcql
-- Get booking with passengers
SELECT b.pnr_number, b.booking_status, COUNT(p.passenger_id) as passenger_count
FROM Bookings b
LEFT JOIN Passengers p ON b.booking_id = p.booking_id
WHERE b.user_id = ?
GROUP BY b.booking_id
ORDER BY b.booking_date DESC;
```

### Revenue Report
```zcql
-- Daily revenue by train
SELECT t.train_name,
       COUNT(b.booking_id) as bookings,
       SUM(b.total_fare) as revenue,
       DATE(b.booking_date) as date
FROM Bookings b
JOIN Trains t ON b.train_id = t.train_id
WHERE DATE(b.booking_date) = CURRENT_DATE
  AND b.payment_status = 'confirmed'
GROUP BY t.train_id, DATE(b.booking_date)
ORDER BY revenue DESC;
```

### Audit Trail
```zcql
-- Admin actions in last 24 hours
SELECT admin_id, action, entity_type, status, created_at
FROM Admin_Logs
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY)
  AND status = 'success'
ORDER BY created_at DESC
LIMIT 100;
```

---

## 🔒 Security & Access Control

### Row-Level Security (RLS) Rules

```python
# Example: Users can only see their own bookings
RULES = {
    'Bookings': {
        'read': 'user_id = CURRENT_USER_ID',
        'update': 'user_id = CURRENT_USER_ID AND status NOT IN ("cancelled", "confirmed")',
        'delete': 'FALSE'  # Bookings never deleted, just cancelled
    },
    'Passengers': {
        'read': 'booking_id IN (SELECT booking_id FROM Bookings WHERE user_id = CURRENT_USER_ID)',
    },
    'Quotas': {
        'read': 'TRUE',  # Public read
        'update': 'ROLE = "admin"',  # Admin only
    },
    'Admin_Logs': {
        'read': 'ROLE = "admin"',  # Admin only
        'write': 'FALSE',  # System-only writes
    }
}
```

---

## 📈 Performance Tuning

### Index Strategy
```sql
-- Frequently searched columns
CREATE INDEX idx_bookings_user_date ON Bookings(user_id, booking_date DESC);
CREATE INDEX idx_passengers_booking_status ON Passengers(booking_id, status);
CREATE INDEX idx_trains_route ON Trains(source_station_id, destination_station_id);

-- Analytical queries
CREATE INDEX idx_bookings_date ON Bookings(booking_date DESC);
CREATE INDEX idx_logs_admin_time ON Admin_Logs(admin_id, created_at DESC);
```

### Partitioning Strategy (optional)
```yaml
Bookings:
  - Partition by: booking_date (monthly)
  - Reason: Range queries common, old data archived

Passengers:
  - Partition by: booking_id (hash)
  - Reason: Always filtered by booking

Admin_Logs:
  - Partition by: created_at (daily)
  - Reason: Time-series data, quick pruning
```

---

## 🔄 Data Flow Diagrams

### Booking Flow
```
1. User searches trains (Trains table)
2. Checks availability (Quotas table)
3. Selects fare (Fares table)
4. Creates booking (Bookings table) → PNR generated
5. Adds passengers (Passengers table)
6. Payment process
7. Seat allocation (coach_number, berth_number updated)
8. Status moves: pending → confirmed
9. eTicket generated
```

### Cancellation Flow
```
1. User requests cancellation (Bookings table)
2. Calculate refund (using CANCEL_MIN_DEDUCTION settings)
3. Update status → "cancelled"
4. Passengers → "cancelled"
5. Update quotas: booked_seats --
6. Log action (Admin_Logs table)
7. Process refund (external payment service)
```

---

## 🧪 Sample Data Inserts

### Create Test Station
```python
stations = datastore.get_table('Stations')
stations.insert({
    'station_code': 'TEST',
    'station_name': 'Test City',
    'city': 'Test City',
    'state': 'Test State',
    'latitude': 13.0827,
    'longitude': 80.2707,
    'timezone': 'Asia/Kolkata',
    'platform_count': 6,
    'is_major_station': True
})
```

### Create Test Train
```python
trains = datastore.get_table('Trains')
trains.insert({
    'train_number': 12621,
    'train_name': 'Tamil Nadu Express',
    'train_type': 'Express',
    'source_station_id': 1,  # MAS
    'destination_station_id': 2,  # DEL
    'departure_time': '09:45',
    'arrival_time': '08:15',  # Next day
    'duration_minutes': 1470,  # 24.5 hours
    'total_coaches': 16,
    'status': 'active'
})
```

### Create Coach Layout
```python
layouts = datastore.get_table('Coach_Layouts')
layouts.insert({
    'car_type_code': '2A',
    'car_type_name': '2nd AC (Two Tier)',
    'total_berths': 48,
    'layout_pattern': {
        'berth_cycle': 8,
        'side_berths': ['1', '2', '3', '4', '7', '8'],
        'mid_berths': ['5', '6'],
        'lower': ['2', '4', '6', '8'],
        'upper': ['1', '3', '5', '7']
    },
    'amenities': {'charging': True, 'reading_light': True}
})
```

---

## ⚠️ Important Constraints

### Booking Rules
- Min booking age: 5 years
- Max passengers per booking: 6
- Advance booking: 90 days
- Tatkal booking: 4 hours before departure
- Cancellation refund window: varies by class

### Seat Allocation Rules
- Prefer lower berths for females with children
- Adjacent seats for family groups
- No consecutive upper berths allocated
- Wheelchairbound: ground floor (lower) berths only

### Data Retention
- User profiles: Indefinite (anonymize after account delete)
- Bookings: 2 years (compliance)
- Admin logs: 1 year (audit requirement)
- Password reset tokens: 24 hours (auto-delete expired)

---

## 🔍 Debugging Queries

### Find Bottlenecks
```zcql
-- Tables with most records
SELECT table_name, record_count FROM INFORMATION_SCHEMA.TABLES
ORDER BY record_count DESC LIMIT 5;

-- Index usage stats
SELECT * FROM INFORMATION_SCHEMA.STATISTICS
WHERE table_schema = 'railway' ORDER BY seq_in_index;
```

### Verify Referential Integrity
```zcql
-- Missing train references
SELECT * FROM Bookings b
LEFT JOIN Trains t ON b.train_id = t.train_id
WHERE t.train_id IS NULL;

-- Orphaned passengers (no matching booking)
SELECT * FROM Passengers p
LEFT JOIN Bookings b ON p.booking_id = b.booking_id
WHERE b.booking_id IS NULL;
```

---

## 📚 Related Files

- `CLOUDSCALE_DATABASE_SCHEMA.md` - Full schema details (14 tables)
- `database_setup.py` - Setup script for table creation
- `app.py` - Flask handler for API requests
- `services/zoho_repository.py` - Data access layer
- `repositories/cache_manager.py` - Query caching

---

## 🎯 Next Steps

1. ✅ Schema designed (14 tables)
2. ⏳ Run `database_setup.py` in Catalyst
3. ⏳ Insert initial data (stations, trains, coaches)
4. ⏳ Configure row-level security (RLS)
5. ⏳ Load historical data (migration)
6. ⏳ Set up monitoring & alerts
7. ⏳ Performance tuning & optimization

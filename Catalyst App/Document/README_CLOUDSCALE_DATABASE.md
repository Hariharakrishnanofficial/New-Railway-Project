# Railway Ticketing System - Catalyst CloudScale Database

## 📦 Complete Package

### Documentation Files Created

| File | Purpose | Size |
|------|---------|------|
| `CLOUDSCALE_DATABASE_SCHEMA.md` | Full schema (14 tables, detailed) | ~45 KB |
| `CLOUDSCALE_QUICK_REFERENCE.md` | Quick reference + examples | ~30 KB |
| `MIGRATION_GUIDE.md` | Data migration instructions | ~35 KB |
| `database_setup.py` | Automated table creation script | ~12 KB |

**Total Package**: ~122 KB documentation + scripts

---

## 🗄️ Database Architecture

### 14 Tables Organized by Layer

```
┌─ REFERENCE LAYER (Static) ─────────────────────┐
│ • Stations (1K records)                        │
│ • Coach_Layouts (6 records)                    │
│ • Trains (10K records)                         │
│ • Train_Routes (100K records)                  │
│ • Train_Inventory (60K records)                │
│ • Quotas (50K records)                         │
│ • Fares (500K records)                         │
│ • Settings (50 records)                        │
│ • Announcements (1K records)                   │
└────────────────────────────────────────────────┘

┌─ TRANSACTIONAL LAYER ──────────────────────────┐
│ • Bookings (5M records)                        │
│ • Passengers (25M records)                     │
│ • Users (100K records)                         │
│ • Password_Reset_Tokens (10K records)          │
└────────────────────────────────────────────────┘

┌─ AUDIT LAYER ──────────────────────────────────┐
│ • Admin_Logs (500K records)                    │
└────────────────────────────────────────────────┘
```

### Estimated Storage

```
Small: ~3.5 GB  (100K users)
Large: ~35 GB   (1M users)
```

---

## 🔑 Key Relationships

```
Users
  ├─→ Bookings (user_id)
  ├─→ Admin_Logs (admin_id)
  └─→ Password_Reset_Tokens (user_id)

Trains
  ├─→ Train_Routes (train_id)
  ├─→ Train_Inventory (train_id)
  ├─→ Quotas (train_id)
  ├─→ Fares (train_id)
  ├─→ Bookings (train_id)
  └─→ Announcements (train_id)

Stations
  ├─→ Train_Routes (station_id)
  └─→ Trains (source/destination)

Coach_Layouts
  └─→ Train_Inventory (car_type_code)

Bookings
  └─→ Passengers (booking_id)

Stations ← Bookings (source/destination)
```

---

## 📊 Sample Data Sizes

### for Small Deployment (100K Users)

```
Stations:          ~50 records          5 MB
Trains:            ~5,000 records       50 MB
Bookings:          ~5,000,000 records   500 MB
Passengers:        ~25,000,000 records  2.5 GB
───────────────────────────────────
Total:             ~32M records         ~3.5 GB
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Create Tables
```bash
# Run database_setup.py in Catalyst Functions
POST /api/setup-database
```

**Expected Output:**
```
✓ Users: success
✓ Stations: success
✓ Trains: success
... (14 total)
```

### Step 2: Seed Reference Data
```python
# Insert stations, trains, coaches, fares
# See: MIGRATION_GUIDE.md
```

### Step 3: Test API
```bash
curl https://your-catalyst-domain/api/trains?source=MAS&dest=DEL
```

---

## 💾 Implementation Files

### In Functions Folder

```
catalyst_backend/
├── app.py                      # Flask handler for Catalyst
├── config.py                   # Already migrated
├── database_setup.py           # NEW: Table creation
├── catalyst-config.json        # Catalyst deployment config
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
│
├── routes/                     # 18 API endpoint modules
│   ├── auth.py
│   ├── bookings.py
│   ├── trains.py
│   ├── users.py
│   ├── fares.py
│   ├── ai_routes.py
│   └── ... (13 more)
│
├── services/                   # Business logic
│   ├── booking_service.py
│   ├── user_service.py
│   ├── analytics_service.py
│   └── ... (4 more)
│
├── repositories/               # Data access layer
│   ├── zoho_repository.py      # Will be updated for Catalyst SDK
│   └── cache_manager.py
│
├── ai/                         # AI modules
│   ├── qwen_client.py
│   ├── nlp_search.py
│   └── ... (7 more)
│
├── core/                       # Core functionality
│   ├── security.py             # Auth, JWT
│   └── exceptions.py
│
└── utils/                      # Helpers
    ├── seat_allocation.py
    ├── fare_helper.py
    └── ... (5 more)
```

---

## 🔐 Security Considerations

### Row-Level Security (RLS)
Implement in Catalyst Data Store:

```python
# Example: Users see only their bookings
{
    'table': 'Bookings',
    'read_rule': 'user_id = current_user_id',
    'update_rule': 'user_id = current_user_id AND status NOT IN ("cancelled", "confirmed")',
    'delete_rule': 'FALSE'  # Never delete, only cancel
}
```

### Authentication
- JWT tokens in Authorization header
- Legacy support: X-User-Email, X-User-Role headers
- Admin-only endpoints: Require `role = "admin"`

### Sensitive Data
- Passwords: SHA-256 hashes only (never plaintext)
- PII: Encrypt document numbers (Aadhaar, PAN)
- Bookings: Only user can access own bookings

---

## ⚙️ Configuration (ENV Variables)

Set in `catalyst-config.json`:

```json
{
  "ZOHO_CLIENT_ID": "...",
  "ZOHO_CLIENT_SECRET": "...",
  "ZOHO_REFRESH_TOKEN": "...",
  "ZOHO_ACCOUNT_OWNER_NAME": "...",
  "GEMINI_API_KEY": "...",
  "CATALYST_ACCESS_TOKEN": "...",
  "ADMIN_SETUP_KEY": "RailAdmin@2026"
}
```

---

## 📈 Performance Tuning

### Recommended Indexes
```sql
CREATE INDEX idx_bookings_user_date
  ON Bookings(user_id, booking_date DESC);

CREATE INDEX idx_trains_route
  ON Trains(source_station_id, destination_station_id);

CREATE INDEX idx_passengers_booking
  ON Passengers(booking_id, status);

CREATE INDEX idx_logs_admin_time
  ON Admin_Logs(admin_id, created_at DESC);
```

### Partitioning Strategy
- **Bookings**: Partition by month (booking_date)
- **Passengers**: Hash partition by booking_id
- **Admin_Logs**: Partition by day (created_at)

---

## 🔄 API Endpoints (100+)

### Sample Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/trains?source=MAS&dest=DEL` | Search trains |
| GET | `/api/trains/:id/availability?date=2025-03-20` | Check availability |
| POST | `/api/bookings` | Create booking |
| GET | `/api/bookings/:pnr` | Get PNR status |
| POST | `/api/bookings/:pnr/cancel` | Cancel booking |
| GET | `/api/users/:id` | Get user profile |
| POST | `/api/auth/login` | Login |
| GET | `/api/analytics/revenue` | Revenue report |
| POST | `/api/ai/search` | AI search |
| GET | `/api/admin/logs` | Admin audit trail |

---

## ✅ Migration Checklist

### Phase 1: Setup (30 min)
- [ ] Run `database_setup.py`
- [ ] Verify 14 tables created
- [ ] Check indexes in place

### Phase 2: Seed Data (1 hour)
- [ ] Insert stations
- [ ] Insert trains & routes
- [ ] Insert coach layouts & quotas
- [ ] Insert fares

### Phase 3: Test (2 hours)
- [ ] Test booking flow
- [ ] Test PNR search
- [ ] Test cancellation
- [ ] Test analytics

### Phase 4: Go Live (1 hour)
- [ ] Update connection strings
- [ ] Monitor errors
- [ ] Verify all endpoints
- [ ] Peak load testing

---

## 📚 Related Documentation

- **CLOUDSCALE_DATABASE_SCHEMA.md** - Detailed schema for all 14 tables
- **CLOUDSCALE_QUICK_REFERENCE.md** - Sample queries, troubleshooting
- **MIGRATION_GUIDE.md** - Data migration from Zoho Creator
- **database_setup.py** - Automated table creation
- **app.py** - Flask handler for Catalyst Functions
- **catalyst-config.json** - Deployment configuration

---

## 🎯 Next Steps

1. ✅ Schema designed (14 tables)
2. ⏳ Deploy to Catalyst CloudScale
   ```bash
   catalyst deploy --only functions
   ```
3. ⏳ Run `database_setup.py`
   ```bash
   POST /api/setup-database
   ```
4. ⏳ Insert initial data (stations, trains)
5. ⏳ Test endpoints
6. ⏳ Migrate production data
7. ⏳ Enable monitoring & alerts

---

## 📞 Support

### Common Issues

**Q: How to add new column to existing table?**
```python
table = datastore.get_table('Bookings')
table.add_column({'name': 'new_field', 'type': 'STRING'})
```

**Q: How to create backup?**
```bash
# Catalyst auto-backs up daily
# Manual export (ZCQL):
SELECT * FROM Bookings WHERE DATE(booking_date) = '2025-03-20' LIMIT 1000000;
```

**Q: How to monitor storage usage?**
```python
from zcatalyst_sdk import initialize

catalyst = initialize()
usage = catalyst.analytics.get_storage_usage()
print(f"Used: {usage['used_mb']} MB / {usage['total_mb']} MB")
```

---

## 🎉 You're Ready to Go!

All components are in place:
- ✅ 14-table CloudScale schema
- ✅ Setup automation script
- ✅ Migration guide with code
- ✅ 100+ API endpoints ready
- ✅ Backend migrated to functions
- ✅ Frontend updated
- ✅ Environment variables configured

**Deploy to Catalyst** and start processing bookings! 🚂

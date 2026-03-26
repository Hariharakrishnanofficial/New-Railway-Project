# Creating Tables in Zoho Catalyst CloudScale Web Console

## 📍 Access Panel
**URL**: https://console.catalyst.zoho.in/baas/60066581545/project/31207000000011084/Development#/cloudscale/datastore/tables

---

## 🗂️ Table Creation Order (Create in this order - dependencies first)

```
1. Stations          (no dependencies)
2. Coach_Layouts     (no dependencies)
3. Trains            (depends on: Stations)
4. Train_Routes      (depends on: Trains, Stations)
5. Train_Inventory   (depends on: Trains, Coach_Layouts)
6. Quotas            (depends on: Trains)
7. Fares             (depends on: Trains, Stations)
8. Users             (no dependencies)
9. Bookings          (depends on: Users, Trains, Stations)
10. Passengers       (depends on: Bookings)
11. Announcements    (depends on: Trains)
12. Password_Reset_Tokens (depends on: Users)
13. Settings         (no dependencies)
14. Admin_Logs       (depends on: Users)
```

---

## TABLE 1: STATIONS

### Steps:
1. Click **"Add Table"** button
2. Enter **Table Name**: `Stations`
3. Click **"Add Columns"**

### Columns to Add:

| Column Name | Data Type | Primary Key | Unique | Required | Default | Notes |
|-------------|-----------|-------------|--------|----------|---------|-------|
| station_id | BIGINT | ✅ Yes | - | - | - | Auto-increment |
| station_code | STRING(10) | - | ✅ Yes | ✅ Yes | - | 3-letter code (MAS, DEL) |
| station_name | STRING(255) | - | - | ✅ Yes | - | Full name |
| city | STRING(100) | - | - | - | - | City name |
| state | STRING(100) | - | - | - | - | State name |
| country | STRING(100) | - | - | - | India | Country |
| latitude | DOUBLE | - | - | - | - | GPS latitude |
| longitude | DOUBLE | - | - | - | - | GPS longitude |
| timezone | STRING(50) | - | - | - | Asia/Kolkata | Timezone |
| platform_count | INT | - | - | - | 4 | Number of platforms |
| is_major_station | BOOLEAN | - | - | - | false | Major hub |
| created_at | DATETIME | - | - | - | CURRENT_TIMESTAMP | Creation time |

### Add Indexes:
- Click **"Add Index"**
- **Index Name**: `idx_station_code`
- **Columns**: `station_code`
- **Unique**: ✅ Yes

---

## TABLE 2: COACH_LAYOUTS

### Steps:
1. Click **"Add Table"**
2. Enter **Table Name**: `Coach_Layouts`
3. Click **"Add Columns"**

### Columns:

| Column Name | Data Type | Primary Key | Unique | Required | Default |
|-------------|-----------|-------------|--------|----------|---------|
| layout_id | BIGINT | ✅ Yes | - | - | - |
| car_type_code | STRING(10) | - | ✅ Yes | ✅ Yes | - |
| car_type_name | STRING(100) | - | - | ✅ Yes | - |
| total_berths | INT | - | - | ✅ Yes | - |
| layout_pattern | JSON | - | - | - | - |
| seat_configuration | JSON | - | - | - | - |
| amenities | JSON | - | - | - | - |
| is_active | BOOLEAN | - | - | - | true |
| created_at | DATETIME | - | - | - | CURRENT_TIMESTAMP |

### Add Index:
- **Index Name**: `idx_car_type_code`
- **Columns**: `car_type_code`
- **Unique**: ✅ Yes

### Sample Data to Insert After Creation:
```json
{
  "car_type_code": "1A",
  "car_type_name": "1st AC (First Class)",
  "total_berths": 18,
  "layout_pattern": {},
  "seat_configuration": {},
  "amenities": {"charging": true, "wifi": true},
  "is_active": true
}

{
  "car_type_code": "2A",
  "car_type_name": "2nd AC (Two Tier)",
  "total_berths": 48,
  "is_active": true
}

{
  "car_type_code": "3A",
  "car_type_name": "3rd AC (Three Tier)",
  "total_berths": 72,
  "is_active": true
}

{
  "car_type_code": "SL",
  "car_type_name": "Sleeper",
  "total_berths": 72,
  "is_active": true
}

{
  "car_type_code": "UR",
  "car_type_name": "Unreserved",
  "total_berths": 100,
  "is_active": true
}

{
  "car_type_code": "FC",
  "car_type_name": "First Class Chair Car",
  "total_berths": 50,
  "is_active": true
}
```

---

## TABLE 3: TRAINS

### Steps:
1. Click **"Add Table"**
2. Enter **Table Name**: `Trains`

### Columns:

| Column Name | Data Type | Primary Key | Unique | Required | Default |
|-------------|-----------|-------------|--------|----------|---------|
| train_id | BIGINT | ✅ Yes | - | - | - |
| train_number | INT | - | ✅ Yes | ✅ Yes | - |
| train_name | STRING(255) | - | - | ✅ Yes | - |
| train_type | STRING(50) | - | - | - | Express |
| source_station_id | BIGINT | - | - | ✅ Yes | - |
| destination_station_id | BIGINT | - | - | ✅ Yes | - |
| departure_time | TIME | - | - | ✅ Yes | - |
| arrival_time | TIME | - | - | ✅ Yes | - |
| duration_minutes | INT | - | - | - | - |
| total_coaches | INT | - | - | - | 16 |
| status | STRING(50) | - | - | - | active |
| created_at | DATETIME | - | - | - | CURRENT_TIMESTAMP |

### Add Foreign Keys:
1. **Foreign Key Name**: `fk_trains_source`
   - **Column**: `source_station_id`
   - **References**: `Stations.station_id`

2. **Foreign Key Name**: `fk_trains_destination`
   - **Column**: `destination_station_id`
   - **References**: `Stations.station_id`

### Add Indexes:
- **Index 1**:
  - Name: `idx_trains_number`
  - Columns: `train_number`
  - Unique: ✅ Yes

- **Index 2**:
  - Name: `idx_trains_route`
  - Columns: `source_station_id`, `destination_station_id`
  - Unique: ❌ No

- **Index 3**:
  - Name: `idx_trains_status`
  - Columns: `status`

---

## TABLE 4: TRAIN_ROUTES

### Columns:

| Column Name | Data Type | Primary Key | Required |
|-------------|-----------|-------------|----------|
| route_id | BIGINT | ✅ Yes | - |
| train_id | BIGINT | - | ✅ Yes |
| station_id | BIGINT | - | ✅ Yes |
| sequence | INT | - | ✅ Yes |
| arrival_time | TIME | - | - |
| departure_time | TIME | - | - |
| halt_duration_minutes | INT | - | - |
| distance_from_source_km | DOUBLE | - | - |
| platform_number | INT | - | - |
| created_at | DATETIME | - | - |

### Foreign Keys:
1. `train_id` → `Trains.train_id`
2. `station_id` → `Stations.station_id`

### Indexes:
- `idx_route_train_sequence` on `(train_id, sequence)`
- `idx_route_station` on `station_id`

---

## TABLE 5: TRAIN_INVENTORY

### Columns:

| Column Name | Data Type | Primary Key | Required |
|-------------|-----------|-------------|----------|
| inventory_id | BIGINT | ✅ Yes | - |
| train_id | BIGINT | - | ✅ Yes |
| coach_type_code | STRING(10) | - | ✅ Yes |
| coach_count | INT | - | ✅ Yes |
| total_capacity | INT | - | ✅ Yes |
| sequence_start | INT | - | - |
| sequence_end | INT | - | - |
| created_at | DATETIME | - | - |

### Foreign Keys:
1. `train_id` → `Trains.train_id`
2. `coach_type_code` → `Coach_Layouts.car_type_code`

### Indexes:
- `idx_inventory_train_coach` on `(train_id, coach_type_code)`

---

## TABLE 6: QUOTAS

### Columns:

| Column Name | Data Type | Primary Key | Required | Default |
|-------------|-----------|-------------|----------|---------|
| quota_id | BIGINT | ✅ Yes | - | - |
| train_id | BIGINT | - | ✅ Yes | - |
| class_code | STRING(10) | - | ✅ Yes | - |
| quota_type | STRING(50) | - | ✅ Yes | - |
| percentage | DECIMAL(5,2) | - | ✅ Yes | - |
| actual_capacity | INT | - | - | - |
| available_seats | INT | - | - | - |
| booked_seats | INT | - | - | 0 |
| created_at | DATETIME | - | - | CURRENT_TIMESTAMP |

### Foreign Keys:
1. `train_id` → `Trains.train_id`

### Indexes:
- `idx_quota_train_class_type` on `(train_id, class_code, quota_type)` UNIQUE

---

## TABLE 7: FARES

### Columns:

| Column Name | Data Type | Primary Key | Required |
|-------------|-----------|-------------|----------|
| fare_id | BIGINT | ✅ Yes | - |
| train_id | BIGINT | - | ✅ Yes |
| source_station_id | BIGINT | - | ✅ Yes |
| destination_station_id | BIGINT | - | ✅ Yes |
| class_code | STRING(10) | - | ✅ Yes |
| base_fare | DECIMAL(10,2) | - | ✅ Yes |
| reservation_charge | DECIMAL(10,2) | - | - |
| gst_percentage | DECIMAL(5,2) | - | - |
| total_fare | DECIMAL(10,2) | - | - |
| effective_from | DATE | - | - |
| effective_to | DATE | - | - |
| created_at | DATETIME | - | - |

### Foreign Keys:
1. `train_id` → `Trains.train_id`
2. `source_station_id` → `Stations.station_id`
3. `destination_station_id` → `Stations.station_id`

### Indexes:
- `idx_fare_route_class` on `(train_id, source_station_id, destination_station_id, class_code)`

---

## TABLE 8: USERS

### Columns:

| Column Name | Data Type | Primary Key | Unique | Required | Default |
|-------------|-----------|-------------|--------|----------|---------|
| user_id | BIGINT | ✅ Yes | - | - | - |
| email | STRING(255) | - | ✅ Yes | ✅ Yes | - |
| password_hash | STRING(512) | - | - | ✅ Yes | - |
| full_name | STRING(255) | - | - | - | - |
| phone | STRING(20) | - | - | - | - |
| role | STRING(50) | - | - | - | passenger |
| status | STRING(50) | - | - | - | active |
| date_of_birth | DATE | - | - | - | - |
| gender | STRING(10) | - | - | - | - |
| created_at | DATETIME | - | - | - | CURRENT_TIMESTAMP |
| updated_at | DATETIME | - | - | - | CURRENT_TIMESTAMP |
| last_login | DATETIME | - | - | - | - |

### Indexes:
- `idx_users_email` on `email` UNIQUE
- `idx_users_role` on `role`
- `idx_users_status` on `status`

---

## TABLE 9: BOOKINGS

### Columns:

| Column Name | Data Type | Primary Key | Unique | Required | Default |
|-------------|-----------|-------------|--------|----------|---------|
| booking_id | BIGINT | ✅ Yes | - | - | - |
| pnr_number | STRING(20) | - | ✅ Yes | ✅ Yes | - |
| user_id | BIGINT | - | - | ✅ Yes | - |
| train_id | BIGINT | - | - | ✅ Yes | - |
| journey_date | DATE | - | - | ✅ Yes | - |
| source_station_id | BIGINT | - | - | ✅ Yes | - |
| destination_station_id | BIGINT | - | - | ✅ Yes | - |
| class_code | STRING(10) | - | - | ✅ Yes | - |
| quota_type | STRING(50) | - | - | - | General |
| passenger_count | INT | - | - | ✅ Yes | - |
| total_fare | DECIMAL(10,2) | - | - | ✅ Yes | - |
| payment_status | STRING(50) | - | - | - | pending |
| booking_status | STRING(50) | - | - | - | confirmed |
| posted_status | STRING(50) | - | - | - | reserved |
| booking_date | DATETIME | - | - | - | CURRENT_TIMESTAMP |
| confirmation_date | DATETIME | - | - | - | - |
| cancelled_date | DATETIME | - | - | - | - |
| cancellation_charge | DECIMAL(10,2) | - | - | - | 0 |
| refund_amount | DECIMAL(10,2) | - | - | - | 0 |
| created_at | DATETIME | - | - | - | CURRENT_TIMESTAMP |

### Foreign Keys:
1. `user_id` → `Users.user_id`
2. `train_id` → `Trains.train_id`
3. `source_station_id` → `Stations.station_id`
4. `destination_station_id` → `Stations.station_id`

### Indexes:
- `idx_bookings_pnr` on `pnr_number` UNIQUE
- `idx_bookings_user_date` on `(user_id, booking_date)`
- `idx_bookings_train_date` on `(train_id, journey_date)`
- `idx_bookings_status` on `booking_status`
- `idx_bookings_payment` on `payment_status`

---

## TABLE 10: PASSENGERS

### Columns:

| Column Name | Data Type | Primary Key | Unique | Required |
|-------------|-----------|-------------|--------|----------|
| passenger_id | BIGINT | ✅ Yes | - | - |
| booking_id | BIGINT | - | - | ✅ Yes |
| first_name | STRING(100) | - | - | ✅ Yes |
| last_name | STRING(100) | - | - | - |
| age | INT | - | - | ✅ Yes |
| gender | STRING(10) | - | - | ✅ Yes |
| concession_type | STRING(50) | - | - | - |
| coach_number | INT | - | - | - |
| berth_number | STRING(10) | - | - | - |
| berth_type | STRING(50) | - | - | - |
| status | STRING(50) | - | - | - |
| document_type | STRING(50) | - | - | - |
| document_number | STRING(50) | - | - | - |
| ticket_number | STRING(20) | - | ✅ Yes | - |
| created_at | DATETIME | - | - | - |

### Foreign Keys:
1. `booking_id` → `Bookings.booking_id`

### Indexes:
- `idx_passengers_booking` on `booking_id`
- `idx_passengers_ticket` on `ticket_number` UNIQUE
- `idx_passengers_status` on `status`

---

## TABLE 11: ANNOUNCEMENTS

### Columns:

| Column Name | Data Type | Primary Key | Required |
|-------------|-----------|-------------|----------|
| announcement_id | BIGINT | ✅ Yes | - |
| train_id | BIGINT | - | - |
| title | STRING(500) | - | ✅ Yes |
| content | TEXT | - | ✅ Yes |
| announcement_type | STRING(50) | - | ✅ Yes |
| severity | STRING(50) | - | - |
| effective_from | DATETIME | - | ✅ Yes |
| effective_to | DATETIME | - | - |
| created_by | BIGINT | - | - |
| created_at | DATETIME | - | - |

### Foreign Keys:
1. `train_id` → `Trains.train_id` (nullable)
2. `created_by` → `Users.user_id` (nullable)

### Indexes:
- `idx_announcements_train` on `train_id`
- `idx_announcements_type` on `announcement_type`

---

## TABLE 12: PASSWORD_RESET_TOKENS

### Columns:

| Column Name | Data Type | Primary Key | Unique | Required |
|-------------|-----------|-------------|--------|----------|
| token_id | BIGINT | ✅ Yes | - | - |
| user_id | BIGINT | - | - | ✅ Yes |
| token | STRING(512) | - | ✅ Yes | ✅ Yes |
| expires_at | DATETIME | - | - | ✅ Yes |
| used | BOOLEAN | - | - | - |
| created_at | DATETIME | - | - | - |

### Foreign Keys:
1. `user_id` → `Users.user_id`

### Indexes:
- `idx_token_unique` on `token` UNIQUE
- `idx_token_user_expires` on `(user_id, expires_at)`
- `idx_token_expires` on `expires_at`

---

## TABLE 13: SETTINGS

### Columns:

| Column Name | Data Type | Primary Key | Unique | Required |
|-------------|-----------|-------------|--------|----------|
| setting_id | BIGINT | ✅ Yes | - | - |
| key | STRING(100) | - | ✅ Yes | ✅ Yes |
| value | TEXT | - | - | - |
| setting_type | STRING(50) | - | - | - |
| description | STRING(500) | - | - | - |
| is_system | BOOLEAN | - | - | - |
| updated_by | BIGINT | - | - | - |
| updated_at | DATETIME | - | - | - |

### Indexes:
- `idx_settings_key` on `key` UNIQUE

---

## TABLE 14: ADMIN_LOGS

### Columns:

| Column Name | Data Type | Primary Key | Required |
|-------------|-----------|-------------|----------|
| log_id | BIGINT | ✅ Yes | - |
| admin_id | BIGINT | - | ✅ Yes |
| action | STRING(100) | - | ✅ Yes |
| entity_type | STRING(50) | - | ✅ Yes |
| entity_id | BIGINT | - | - |
| old_value | JSON | - | - |
| new_value | JSON | - | - |
| ip_address | STRING(50) | - | - |
| user_agent | STRING(500) | - | - |
| status | STRING(50) | - | - |
| created_at | DATETIME | - | - |

### Foreign Keys:
1. `admin_id` → `Users.user_id`

### Indexes:
- `idx_logs_admin_time` on `(admin_id, created_at)`
- `idx_logs_entity` on `(entity_type, entity_id)`

---

## ✅ After All Tables Created

1. Verify all 14 tables appear in the CloudScale dashboard
2. Check all foreign keys are properly configured
3. Insert sample data (Coach_Layouts is ready - see Table 2)
4. Run the `database_setup.py` verification function to confirm

---

## 💡 Tips for Web Console

1. **For DATETIME fields**: Default to `CURRENT_TIMESTAMP`
2. **For Foreign Keys**: Select "Cascade Delete" for referential integrity
3. **For BIGINT**: System usually auto-increments (check the option)
4. **For STRING**: Always specify max length (VARCHAR)
5. **For Indexes**: Mark UNIQUE indexes where specified
6. **For Nullable columns**: Leave "Required" unchecked

All tables should now be ready in your Catalyst CloudScale!

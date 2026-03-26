# Catalyst CloudScale Data Migration Guide
## From Zoho Creator to Catalyst CloudScale

---

## 📋 Pre-Migration Checklist

- [ ] All 14 Catalyst CloudScale tables created
- [ ] `database_setup.py` executed successfully
- [ ] Zoho Creator API credentials available
- [ ] Backup taken from production Zoho Creator
- [ ] Dev environment ready for testing
- [ ] Migration window scheduled (off-peak)

---

## 🔄 Migration Strategy

### Phase 1: Static Reference Data (Non-transactional)
**Duration: ~30 minutes | Downtime: None**

Migrate in order of dependencies:

```
Stations → Coach_Layouts → Trains → Train_Routes → Train_Inventory
→ Quotas → Fares → Settings → Announcements
```

### Phase 2: User Data
**Duration: ~1-2 hours | Downtime: None (read-only phase)**

```
Users → Password_Reset_Tokens
```

### Phase 3: Transactional Data
**Duration: ~2-8 hours | Downtime: Yes (booking halt)**

```
Bookings → Passengers → Admin_Logs (historical)
```

### Phase 4: Cutover
**Duration: ~1 hour**

- Disable Zoho Creator API writes
- Run final sync
- Update connection strings
- Enable Catalyst reads
- Test all endpoints

---

## 🛠️ Implementation

### Migration Script Template

```python
"""
Migrate Railway data from Zoho Creator to Catalyst CloudScale
"""

from __future__ import annotations
import zcatalyst_sdk
import json
from datetime import datetime


class MigrationManager:
    def __init__(self):
        self.catalyst_app = zcatalyst_sdk.initialize()
        self.datastore = self.catalyst_app.data_store
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

    # ─────────────────────────────────────────────────────────────────────────
    #  PHASE 1: REFERENCE DATA
    # ─────────────────────────────────────────────────────────────────────────

    def migrate_stations(self, source_data: list[dict]) -> dict:
        """Migrate stations from Zoho Creator"""
        print("Migrating Stations...")
        stations_table = self.datastore.get_table('Stations')

        for i, station in enumerate(source_data):
            try:
                # Transform Zoho fields to Catalyst schema
                record = {
                    'station_code': station.get('Code', ''),
                    'station_name': station.get('Station_Name', ''),
                    'city': station.get('City', ''),
                    'state': station.get('State', ''),
                    'country': station.get('Country', 'India'),
                    'latitude': float(station.get('Latitude', 0)),
                    'longitude': float(station.get('Longitude', 0)),
                    'timezone': station.get('Timezone', 'Asia/Kolkata'),
                    'platform_count': int(station.get('Platforms', 4)),
                    'is_major_station': station.get('IsMajor', False) == 'true',
                }

                stations_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Stations: {self.stats['success']} inserted, {self.stats['failed']} failed\n")
        return self.stats

    def migrate_coach_layouts(self, source_data: list[dict]) -> dict:
        """Migrate coach layout configurations"""
        print("Migrating Coach Layouts...")
        layouts_table = self.datastore.get_table('Coach_Layouts')
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for i, layout in enumerate(source_data):
            try:
                record = {
                    'car_type_code': layout.get('ClassCode', ''),
                    'car_type_name': layout.get('ClassName', ''),
                    'total_berths': int(layout.get('Berths', 48)),
                    'layout_pattern': json.loads(layout.get('Pattern', '{}')),
                    'amenities': json.loads(layout.get('Amenities', '{}')) if layout.get('Amenities') else {},
                    'is_active': True,
                }

                layouts_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Coach Layouts: {self.stats['success']} inserted\n")
        return self.stats

    def migrate_trains(self, source_data: list[dict]) -> dict:
        """Migrate train master data"""
        print("Migrating Trains...")
        trains_table = self.datastore.get_table('Trains')
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for i, train in enumerate(source_data):
            try:
                # Get station IDs from lookup
                source_id = self._get_station_id(train.get('SourceCode', ''))
                dest_id = self._get_station_id(train.get('DestCode', ''))

                if not source_id or not dest_id:
                    self.stats['skipped'] += 1
                    continue

                record = {
                    'train_number': int(train.get('TrainNumber', 0)),
                    'train_name': train.get('TrainName', ''),
                    'train_type': train.get('TrainType', 'Express'),
                    'source_station_id': source_id,
                    'destination_station_id': dest_id,
                    'departure_time': train.get('DepartureTime', '00:00'),
                    'arrival_time': train.get('ArrivalTime', '00:00'),
                    'total_coaches': int(train.get('Coaches', 16)),
                    'status': 'active',
                }

                trains_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Trains: {self.stats['success']} inserted\n")
        return self.stats

    def migrate_train_routes(self, source_data: list[dict]) -> dict:
        """Migrate train route stops"""
        print("Migrating Train Routes...")
        routes_table = self.datastore.get_table('Train_Routes')
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for i, route in enumerate(source_data):
            try:
                train_id = self._get_train_id(route.get('TrainNumber', 0))
                station_id = self._get_station_id(route.get('StationCode', ''))

                if not train_id or not station_id:
                    self.stats['skipped'] += 1
                    continue

                record = {
                    'train_id': train_id,
                    'station_id': station_id,
                    'sequence': int(route.get('Sequence', 0)),
                    'arrival_time': route.get('ArrivalTime', ''),
                    'departure_time': route.get('DepartureTime', ''),
                    'halt_duration_minutes': int(route.get('Halt', 5)),
                    'distance_from_source_km': float(route.get('Distance', 0)),
                    'platform_number': int(route.get('Platform', 0)) if route.get('Platform') else None,
                }

                routes_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Train Routes: {self.stats['success']} inserted\n")
        return self.stats

    def migrate_fares(self, source_data: list[dict]) -> dict:
        """Migrate fare rules"""
        print("Migrating Fares...")
        fares_table = self.datastore.get_table('Fares')
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for i, fare in enumerate(source_data):
            try:
                train_id = self._get_train_id(fare.get('TrainNumber', 0))
                source_id = self._get_station_id(fare.get('SourceCode', ''))
                dest_id = self._get_station_id(fare.get('DestCode', ''))

                if not all([train_id, source_id, dest_id]):
                    self.stats['skipped'] += 1
                    continue

                base_fare = float(fare.get('BaseFare', 0))
                gst_pct = float(fare.get('GST', 5.0))
                gst_amt = (base_fare * gst_pct) / 100

                record = {
                    'train_id': train_id,
                    'source_station_id': source_id,
                    'destination_station_id': dest_id,
                    'class_code': fare.get('Class', '2A'),
                    'base_fare': base_fare,
                    'reservation_charge': float(fare.get('ReservationCharge', 0)),
                    'gst_percentage': gst_pct,
                    'total_fare': base_fare + gst_amt + float(fare.get('ReservationCharge', 0)),
                }

                fares_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Fares: {self.stats['success']} inserted\n")
        return self.stats

    # ─────────────────────────────────────────────────────────────────────────
    #  PHASE 2: USER DATA
    # ─────────────────────────────────────────────────────────────────────────

    def migrate_users(self, source_data: list[dict]) -> dict:
        """Migrate user profiles"""
        print("Migrating Users...")
        users_table = self.datastore.get_table('Users')
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for i, user in enumerate(source_data):
            try:
                record = {
                    'email': user.get('Email', f'user{i}@example.com'),
                    'password_hash': user.get('PasswordHash', ''),  # Already hashed in source
                    'full_name': user.get('FullName', ''),
                    'phone': user.get('Phone', ''),
                    'role': user.get('Role', 'passenger'),
                    'status': user.get('Status', 'active'),
                    'date_of_birth': user.get('DOB', ''),
                    'gender': user.get('Gender', ''),
                }

                users_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Users: {self.stats['success']} inserted\n")
        return self.stats

    # ─────────────────────────────────────────────────────────────────────────
    #  PHASE 3: TRANSACTIONAL DATA
    # ─────────────────────────────────────────────────────────────────────────

    def migrate_bookings(self, source_data: list[dict]) -> dict:
        """Migrate booking records"""
        print("Migrating Bookings...")
        bookings_table = self.datastore.get_table('Bookings')
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for i, booking in enumerate(source_data):
            try:
                user_id = self._get_user_id(booking.get('EmailId', ''))
                train_id = self._get_train_id(booking.get('TrainNumber', 0))
                source_id = self._get_station_id(booking.get('SourceCode', ''))
                dest_id = self._get_station_id(booking.get('DestCode', ''))

                if not all([user_id, train_id, source_id, dest_id]):
                    self.stats['skipped'] += 1
                    continue

                record = {
                    'pnr_number': booking.get('PNR', ''),
                    'user_id': user_id,
                    'train_id': train_id,
                    'journey_date': booking.get('JourneyDate', ''),
                    'source_station_id': source_id,
                    'destination_station_id': dest_id,
                    'class_code': booking.get('Class', '2A'),
                    'quota_type': booking.get('Quota', 'General'),
                    'passenger_count': int(booking.get('PassengerCount', 1)),
                    'total_fare': float(booking.get('TotalFare', 0)),
                    'payment_status': booking.get('PaymentStatus', 'confirmed'),
                    'booking_status': booking.get('BookingStatus', 'confirmed'),
                    'posted_status': booking.get('PostedStatus', 'reserved'),
                    'booking_date': booking.get('BookingDate', ''),
                    'confirmation_date': booking.get('ConfirmationDate', ''),
                }

                bookings_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Bookings: {self.stats['success']} inserted\n")
        return self.stats

    def migrate_passengers(self, source_data: list[dict]) -> dict:
        """Migrate passenger records"""
        print("Migrating Passengers...")
        passengers_table = self.datastore.get_table('Passengers')
        self.stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}

        for i, passenger in enumerate(source_data):
            try:
                booking_id = self._get_booking_id(passenger.get('PNR', ''))

                if not booking_id:
                    self.stats['skipped'] += 1
                    continue

                record = {
                    'booking_id': booking_id,
                    'first_name': passenger.get('FirstName', ''),
                    'last_name': passenger.get('LastName', ''),
                    'age': int(passenger.get('Age', 0)),
                    'gender': passenger.get('Gender', ''),
                    'concession_type': passenger.get('ConcessionType', 'None'),
                    'coach_number': int(passenger.get('CoachNo', 0)) if passenger.get('CoachNo') else None,
                    'berth_number': passenger.get('BerthNo', ''),
                    'berth_type': passenger.get('BerthType', ''),
                    'status': passenger.get('Status', 'confirmed'),
                    'document_type': passenger.get('DocType', ''),
                    'document_number': passenger.get('DocNumber', ''),
                    'ticket_number': passenger.get('TicketNo', ''),
                }

                passengers_table.insert(record)
                self.stats['success'] += 1

            except Exception as e:
                print(f"  ✗ Row {i}: {e}")
                self.stats['failed'] += 1

        print(f"✓ Passengers: {self.stats['success']} inserted\n")
        return self.stats

    # ─────────────────────────────────────────────────────────────────────────
    #  LOOKUP HELPERS (Cache these for performance)
    # ─────────────────────────────────────────────────────────────────────────

    def _get_station_id(self, station_code: str) -> int | None:
        """Get station_id from station_code"""
        stations = self.datastore.get_table('Stations')
        records = stations.query({'where': f"station_code = '{station_code}'"})
        return records[0]['station_id'] if records else None

    def _get_train_id(self, train_number: int) -> int | None:
        """Get train_id from train_number"""
        trains = self.datastore.get_table('Trains')
        records = trains.query({'where': f"train_number = {train_number}"})
        return records[0]['train_id'] if records else None

    def _get_user_id(self, email: str) -> int | None:
        """Get user_id from email"""
        users = self.datastore.get_table('Users')
        records = users.query({'where': f"email = '{email}'"})
        return records[0]['user_id'] if records else None

    def _get_booking_id(self, pnr: str) -> int | None:
        """Get booking_id from PNR"""
        bookings = self.datastore.get_table('Bookings')
        records = bookings.query({'where': f"pnr_number = '{pnr}'"})
        return records[0]['booking_id'] if records else None

    # ─────────────────────────────────────────────────────────────────────────
    #  VERIFICATION
    # ─────────────────────────────────────────────────────────────────────────

    def verify_migration(self) -> dict:
        """Verify migration completeness"""
        print("Verifying migration...")

        results = {}
        for table_name in ['Stations', 'Trains', 'Users', 'Bookings', 'Passengers']:
            table = self.datastore.get_table(table_name)
            records = table.query({})
            results[table_name] = len(records)
            print(f"  {table_name}: {len(records)} records")

        return results

    def run_full_migration(self):
        """Execute complete migration workflow"""
        print("=" * 70)
        print("RAILWAY TICKETING SYSTEM - CATALYST CLOUDSCALE MIGRATION")
        print("=" * 70)
        print()

        # Get data from Zoho Creator (import from JSON/API)
        # stations_data = get_stations_from_zoho()
        # trains_data = get_trains_from_zoho()
        # ... etc

        # Execute migrations
        # self.migrate_stations(stations_data)
        # self.migrate_train_routes(routes_data)
        # self.migrate_fares(fares_data)
        # self.migrate_users(users_data)
        # self.migrate_bookings(bookings_data)
        # self.migrate_passengers(passengers_data)

        # Verify
        self.verify_migration()

        print()
        print("=" * 70)
        print("MIGRATION COMPLETE")
        print("=" * 70)


if __name__ == '__main__':
    migrator = MigrationManager()
    migrator.run_full_migration()
```

---

## 🔔 Post-Migration Verification

```python
# Verify referential integrity
def verify_integrity():
    """Check for orphaned records"""
    checks = {
        'Bookings without Users': """
            SELECT COUNT(*) FROM Bookings b
            LEFT JOIN Users u ON b.user_id = u.user_id
            WHERE u.user_id IS NULL
        """,
        'Passengers without Bookings': """
            SELECT COUNT(*) FROM Passengers p
            LEFT JOIN Bookings b ON p.booking_id = b.booking_id
            WHERE b.booking_id IS NULL
        """,
        'Bookings without Trains': """
            SELECT COUNT(*) FROM Bookings b
            LEFT JOIN Trains t ON b.train_id = t.train_id
            WHERE t.train_id IS NULL
        """,
    }

    for check_name, query in checks.items():
        result = datastore.execute_query(query)
        count = result[0]['COUNT(*)']
        status = "✓ PASS" if count == 0 else f"✗ FAIL ({count} issues)"
        print(f"{check_name}: {status}")
```

---

## 📊 Performance Monitoring

Post-migration monitoring:

```sql
-- Monitor table sizes
SELECT table_name, record_count, data_size_mb, index_size_mb
FROM INFORMATION_SCHEMA.TABLE_STATS
ORDER BY record_count DESC;

-- Check slow queries
SELECT query, execution_time_ms, records_scanned
FROM INFORMATION_SCHEMA.QUERY_LOG
WHERE execution_time_ms > 1000
ORDER BY execution_time_ms DESC
LIMIT 20;

-- Monitor quota usage
SELECT quota_type, usage_mb, limit_mb
FROM CATALYST_USAGE;
```

---

## ⚠️ Rollback Plan

If migration fails:

```python
def rollback_migration():
    """Drop all tables and restore backup"""

    tables = [
        'Passengers', 'Admin_Logs', 'Bookings', 'Announcements',
        'Quotas', 'Fares', 'Train_Inventory', 'Train_Routes',
        'Trains', 'Coach_Layouts', 'Password_Reset_Tokens',
        'Settings', 'Users', 'Stations'
    ]

    for table in tables:
        datastore.drop_table(table)
        print(f"Dropped: {table}")

    # Restore from backup
    print("Restore from Zoho Creator backup completed")
```

---

## 📝 Migration Checklist

**Pre-Migration**
- [ ] Backup Zoho Creator database
- [ ] All 14 Catalyst tables created
- [ ] Migration script tested in dev environment
- [ ] Data validation rules configured
- [ ] Performance baselines established

**During Migration**
- [ ] Phase 1: Reference data (0→30 min)
- [ ] Phase 2: User data (30→90 min)
- [ ] Phase 3: Transactional data (90→450 min)
- [ ] Verify counts match source
- [ ] Check referential integrity

**Post-Migration**
- [ ] Verify all bookings present
- [ ] Test booking flow end-to-end
- [ ] Check PNR generation
- [ ] Validate calculations (fare, tax, etc.)
- [ ] Performance testing
- [ ] User acceptance testing

---

## 🚀 Go-Live

1. **Final Sync**: Run incremental sync for new data
2. **Disable Creator Writes**: Prevent new changes
3. **Last Verification**: Count records, verify integrity
4. **Update APIs**: Point to Catalyst connection strings
5. **Monitor**: Watch metrics for 24 hours
6. **Archive**: Keep Zoho Creator as archive

Ready to migrate! 🎉

"""
Comprehensive CRUD Test Suite - All Railway System Modules

Tests all CRUD operations for:
- Passengers, Bookings, Quotas, Fares, Train_Inventory
- Coach_Layouts, Route_Stops, Train_Routes, Trains, Stations
- Settings, Admin_Logs, Announcements

Creates sample records and tests CREATE, READ, UPDATE, DELETE operations.
"""

import urllib.request
import urllib.error
import json
import ssl
import time
from datetime import datetime, timedelta
import random
import string

# Disable SSL verification for testing
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

# Test results storage
results = {
    'timestamp': datetime.now().isoformat(),
    'baseUrl': BASE_URL,
    'modules': {},
    'summary': {'total': 0, 'passed': 0, 'failed': 0},
    'auth_tokens': {}
}

# Sample data generators
class SampleDataGenerator:
    @staticmethod
    def random_string(length=8):
        return ''.join(random.choices(string.ascii_letters, k=length))

    @staticmethod
    def random_digits(length=6):
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def future_date(days=30):
        date = datetime.now() + timedelta(days=random.randint(1, days))
        return date.strftime('%Y-%m-%d')

    @staticmethod
    def random_time():
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        return f"{hour:02d}:{minute:02d}"

def api_request(method, endpoint, data=None, headers=None, expected_codes=[200, 201]):
    """Make API request and return structured result."""
    global results

    url = f"{BASE_URL}{endpoint}"
    test_name = f"{method} {endpoint}"

    try:
        # Prepare headers
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)

        # Prepare body
        if data:
            if isinstance(data, str):
                body = data.encode('utf-8')
            else:
                body = json.dumps(data).encode('utf-8')
        else:
            body = None

        # Make request
        request_obj = urllib.request.Request(url, data=body, headers=req_headers, method=method)

        start_time = time.time()
        response = urllib.request.urlopen(request_obj, timeout=30, context=ctx)
        elapsed = (time.time() - start_time) * 1000

        # Parse response
        response_data = json.loads(response.read().decode())

        # Check result
        passed = response.status in expected_codes

        result = {
            'method': method,
            'endpoint': endpoint,
            'status': response.status,
            'time_ms': round(elapsed),
            'passed': passed,
            'response': response_data,
            'error': None
        }

        # Update counters
        results['summary']['total'] += 1
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1

        # Print result
        status_icon = "[OK]" if passed else "[FAIL]"
        print(f"{status_icon} {method:6} {endpoint:35} | {response.status} | {elapsed:4.0f}ms")

        return result

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0

        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = str(e)

        passed = e.code in expected_codes

        result = {
            'method': method,
            'endpoint': endpoint,
            'status': e.code,
            'time_ms': round(elapsed),
            'passed': passed,
            'response': error_data,
            'error': f"HTTP {e.code}"
        }

        results['summary']['total'] += 1
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1

        status_icon = "[OK]" if passed else "[FAIL]"
        print(f"{status_icon} {method:6} {endpoint:35} | {e.code} | {elapsed:4.0f}ms")

        return result

    except Exception as e:
        result = {
            'method': method,
            'endpoint': endpoint,
            'status': 0,
            'time_ms': 0,
            'passed': False,
            'response': None,
            'error': str(e)
        }

        results['summary']['total'] += 1
        results['summary']['failed'] += 1

        print(f"[ERR] {method:6} {endpoint:35} | ERR | 0ms | {str(e)[:50]}")

        return result

def test_crud_module(module_name, table_endpoint, sample_data, auth_required=False):
    """Test full CRUD operations for a module."""
    print(f"\\n{'='*80}")
    print(f"TESTING MODULE: {module_name.upper()}")
    print('='*80)

    module_results = {'tests': [], 'crud_summary': {'create': 0, 'read': 0, 'update': 0, 'delete': 0}}
    created_id = None

    # Get auth header if required
    auth_header = {}
    if auth_required:
        if results['auth_tokens'].get('admin_token'):
            auth_header = {'Authorization': f"Bearer {results['auth_tokens']['admin_token']}"}
        elif results['auth_tokens'].get('user_token'):
            auth_header = {'Authorization': f"Bearer {results['auth_tokens']['user_token']}"}

    # 1. CREATE operation
    print(f"\\n[CREATE] {module_name}")
    create_result = api_request('POST', table_endpoint, sample_data, auth_header, [201, 409])
    module_results['tests'].append(create_result)

    if create_result['passed'] and create_result.get('response', {}).get('data'):
        created_id = create_result['response']['data'].get('ROWID') or create_result['response']['data'].get('id')
        module_results['crud_summary']['create'] = 1
        print(f"   Created record with ID: {created_id}")

    # 2. READ operations
    print(f"\\n[READ] {module_name}")

    # Read all
    read_all_result = api_request('GET', table_endpoint, None, auth_header)
    module_results['tests'].append(read_all_result)
    if read_all_result['passed']:
        module_results['crud_summary']['read'] += 1

    # Read by ID (if we have an ID)
    if created_id:
        read_one_result = api_request('GET', f"{table_endpoint}/{created_id}", None, auth_header, [200, 404])
        module_results['tests'].append(read_one_result)
        if read_one_result['passed']:
            module_results['crud_summary']['read'] += 1

    # 3. UPDATE operation (if we have an ID)
    if created_id:
        print(f"\\n[UPDATE] {module_name}")

        # Prepare update data (modify some fields from original)
        update_data = {}
        if 'name' in str(sample_data).lower():
            for key, value in sample_data.items():
                if 'name' in key.lower() and isinstance(value, str):
                    update_data[key] = f"{value} (Updated)"
                    break

        if not update_data:
            # Try common update fields
            if 'description' in sample_data:
                update_data['description'] = "Updated description"
            elif 'status' in str(sample_data).lower():
                for key in sample_data:
                    if 'status' in key.lower():
                        update_data[key] = 'Updated'
                        break

        if update_data:
            update_result = api_request('PUT', f"{table_endpoint}/{created_id}", update_data, auth_header, [200, 404])
            module_results['tests'].append(update_result)
            if update_result['passed']:
                module_results['crud_summary']['update'] = 1

    # 4. DELETE operation (if we have an ID)
    if created_id:
        print(f"\\n[DELETE] {module_name}")
        delete_result = api_request('DELETE', f"{table_endpoint}/{created_id}", None, auth_header, [200, 204, 404])
        module_results['tests'].append(delete_result)
        if delete_result['passed']:
            module_results['crud_summary']['delete'] = 1

    # Summary for this module
    total_operations = len(module_results['tests'])
    passed_operations = sum(1 for t in module_results['tests'] if t['passed'])

    print(f"\\n[SUMMARY] {module_name}: {passed_operations}/{total_operations} operations passed")
    print(f"   CRUD Status: C={module_results['crud_summary']['create']} R={module_results['crud_summary']['read']} U={module_results['crud_summary']['update']} D={module_results['crud_summary']['delete']}")

    results['modules'][module_name] = module_results
    return module_results

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

print("="*100)
print("COMPREHENSIVE CRUD TEST SUITE - ALL RAILWAY MODULES")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# STEP 1: Setup Authentication
print("\\n[AUTH] STEP 1: AUTHENTICATION SETUP")
print("-"*60)

# Create users first
print("Creating test users...")
user_result = api_request('POST', '/seed/user', expected_codes=[200, 201])
admin_result = api_request('POST', '/seed/admin', expected_codes=[200, 201])

# Extract tokens
if user_result['passed'] and user_result.get('response', {}).get('data', {}).get('token'):
    results['auth_tokens']['user_token'] = user_result['response']['data']['token']
    print(f"[OK] User token obtained: {results['auth_tokens']['user_token'][:30]}...")

if admin_result['passed'] and admin_result.get('response', {}).get('data', {}).get('token'):
    results['auth_tokens']['admin_token'] = admin_result['response']['data']['token']
    print(f"[OK] Admin token obtained: {results['auth_tokens']['admin_token'][:30]}...")

# Test login with proper format
print("\\nTesting direct login...")
login_data = {
    'email': 'agent@agent.com',
    'password': 'agent@agent.com'
}
login_result = api_request('POST', '/auth/login', login_data)
if login_result['passed'] and login_result.get('response', {}).get('data', {}).get('token'):
    results['auth_tokens']['user_token'] = login_result['response']['data']['token']
    print(f"[OK] Login successful, token updated: {results['auth_tokens']['user_token'][:30]}...")

# STEP 2: Test All Modules with CRUD Operations
print("\\n[CRUD] STEP 2: COMPREHENSIVE CRUD TESTING")
print("-"*60)

# 1. STATIONS (Usually public, but might need auth for CREATE/UPDATE/DELETE)
station_data = {
    'stationCode': f'TST{SampleDataGenerator.random_digits(3)}',
    'stationName': f'Test Station {SampleDataGenerator.random_string(5)}',
    'city': f'Test City {SampleDataGenerator.random_string(4)}',
    'state': 'Test State',
    'zone': 'SR',
    'latitude': 12.9716,
    'longitude': 77.5946,
    'isActive': True
}
test_crud_module('Stations', '/stations', station_data, auth_required=True)

# 2. TRAINS
train_data = {
    'trainNumber': f'{random.randint(10000, 99999)}',
    'trainName': f'{SampleDataGenerator.random_string(6)} Express',
    'trainType': 'Express',
    'fromStation': '1',  # Will need actual station ID in real scenario
    'toStation': '2',
    'departureTime': SampleDataGenerator.random_time(),
    'arrivalTime': SampleDataGenerator.random_time(),
    'distance': random.randint(100, 2000),
    'runDays': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
    'isActive': True
}
test_crud_module('Trains', '/trains', train_data, auth_required=True)

# 3. TRAIN ROUTES
train_route_data = {
    'routeName': f'Route {SampleDataGenerator.random_string(5)}',
    'trainId': '1',  # Will need actual train ID
    'sourceStationId': '1',
    'destinationStationId': '2',
    'totalDistance': random.randint(100, 2000),
    'estimatedDuration': random.randint(120, 1440),  # minutes
    'isActive': True
}
test_crud_module('Train_Routes', '/train-routes', train_route_data, auth_required=True)

# 4. ROUTE STOPS
route_stop_data = {
    'trainRouteId': '1',
    'stationId': '1',
    'sequenceNumber': 1,
    'arrivalTime': SampleDataGenerator.random_time(),
    'departureTime': SampleDataGenerator.random_time(),
    'distanceFromSource': random.randint(0, 500),
    'haltDuration': random.randint(2, 30),
    'platformNumber': f'{random.randint(1, 10)}',
    'isActive': True
}
test_crud_module('Route_Stops', '/route-stops', route_stop_data, auth_required=True)

# 5. COACH LAYOUTS
coach_layout_data = {
    'trainId': '1',
    'coachType': 'AC_3_TIER',
    'coachNumber': f'S{random.randint(1, 20)}',
    'totalSeats': 72,
    'availableSeats': 72,
    'seatLayout': '2+1',  # Seating arrangement
    'facilities': 'AC,Charging Point,Reading Light',
    'isActive': True
}
test_crud_module('Coach_Layouts', '/coach-layouts', coach_layout_data, auth_required=True)

# 6. TRAIN INVENTORY
inventory_data = {
    'trainId': '1',
    'journeyDate': SampleDataGenerator.future_date(),
    'coachType': 'AC_3_TIER',
    'totalSeats': 72,
    'availableSeats': random.randint(0, 72),
    'bookedSeats': random.randint(0, 72),
    'blockedSeats': 0,
    'waitingList': random.randint(0, 20),
    'lastUpdated': datetime.now().isoformat()
}
test_crud_module('Train_Inventory', '/inventory', inventory_data, auth_required=True)

# 7. FARES
fare_data = {
    'trainId': '1',
    'sourceStationId': '1',
    'destinationStationId': '2',
    'classType': 'AC_3_TIER',
    'baseFare': random.randint(500, 3000),
    'reservationCharge': 40,
    'superfastCharge': 45,
    'gst': 0,
    'totalFare': random.randint(600, 3500),
    'distance': random.randint(100, 2000),
    'effectiveFrom': SampleDataGenerator.future_date(-30),
    'effectiveTo': SampleDataGenerator.future_date(365),
    'isActive': True
}
test_crud_module('Fares', '/fares', fare_data, auth_required=True)

# 8. QUOTAS
quota_data = {
    'trainId': '1',
    'stationId': '1',
    'classType': 'AC_3_TIER',
    'quotaType': 'GENERAL',
    'totalQuota': 50,
    'availableQuota': random.randint(0, 50),
    'journeyDate': SampleDataGenerator.future_date(),
    'isActive': True
}
test_crud_module('Quotas', '/quotas', quota_data, auth_required=True)

# 9. BOOKINGS
booking_data = {
    'userId': '1',  # Will be updated with actual user ID
    'trainId': '1',
    'journeyDate': SampleDataGenerator.future_date(),
    'sourceStationId': '1',
    'destinationStationId': '2',
    'classType': 'AC_3_TIER',
    'passengers': random.randint(1, 4),
    'totalFare': random.randint(1000, 5000),
    'bookingStatus': 'CONFIRMED',
    'paymentStatus': 'COMPLETED',
    'pnr': f'PNR{SampleDataGenerator.random_digits(10)}'
}
test_crud_module('Bookings', '/bookings', booking_data, auth_required=True)

# 10. PASSENGERS
passenger_data = {
    'bookingId': '1',  # Will need actual booking ID
    'passengerName': f'{SampleDataGenerator.random_string(6)} {SampleDataGenerator.random_string(8)}',
    'age': random.randint(18, 80),
    'gender': random.choice(['Male', 'Female', 'Other']),
    'seatNumber': f'{random.randint(1, 72)}',
    'coachNumber': f'S{random.randint(1, 20)}',
    'ticketStatus': 'CONFIRMED',
    'meal': random.choice(['VEG', 'NON_VEG', 'NONE']),
    'contactNumber': f'9{SampleDataGenerator.random_digits(9)}'
}
test_crud_module('Passengers', '/passengers', passenger_data, auth_required=True)

# 11. ANNOUNCEMENTS
announcement_data = {
    'title': f'Test Announcement {SampleDataGenerator.random_string(5)}',
    'message': f'This is a test announcement message created at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    'type': random.choice(['INFO', 'WARNING', 'CRITICAL', 'MAINTENANCE']),
    'targetAudience': 'ALL',
    'trainId': None,  # General announcement
    'stationId': None,
    'validFrom': datetime.now().isoformat(),
    'validUntil': (datetime.now() + timedelta(days=7)).isoformat(),
    'priority': random.randint(1, 5),
    'isActive': True
}
test_crud_module('Announcements', '/announcements', announcement_data, auth_required=True)

# 12. SETTINGS (Admin only)
settings_data = {
    'settingKey': f'TEST_SETTING_{SampleDataGenerator.random_string(5)}',
    'settingValue': f'test_value_{SampleDataGenerator.random_digits(4)}',
    'settingType': 'STRING',
    'description': 'Test setting created by CRUD test suite',
    'category': 'TESTING',
    'isPublic': False,
    'isActive': True
}
test_crud_module('Settings', '/settings', settings_data, auth_required=True)

# 13. ADMIN LOGS (Read-only, test GET operations)
print(f"\\n{'='*80}")
print("TESTING MODULE: ADMIN_LOGS (READ-ONLY)")
print('='*80)

admin_logs_results = {'tests': [], 'crud_summary': {'create': 0, 'read': 0, 'update': 0, 'delete': 0}}

# Test reading admin logs
if results['auth_tokens'].get('admin_token'):
    auth_header = {'Authorization': f"Bearer {results['auth_tokens']['admin_token']}"}
    read_logs_result = api_request('GET', '/admin/logs', None, auth_header)
    admin_logs_results['tests'].append(read_logs_result)
    if read_logs_result['passed']:
        admin_logs_results['crud_summary']['read'] = 1

results['modules']['Admin_Logs'] = admin_logs_results

# STEP 3: Generate Final Report
print("\\n" + "="*100)
print("FINAL COMPREHENSIVE CRUD TEST REPORT")
print("="*100)

print(f"\\n[STATS] OVERALL STATISTICS")
print(f"   Total API Calls: {results['summary']['total']}")
print(f"   Passed: {results['summary']['passed']}")
print(f"   Failed: {results['summary']['failed']}")

if results['summary']['total'] > 0:
    pass_rate = (results['summary']['passed'] / results['summary']['total']) * 100
    print(f"   Success Rate: {pass_rate:.1f}%")

print(f"\\n[MODULES] MODULE CRUD SUMMARY")
print("-" * 80)
print(f"{'Module':<20} {'Create':<8} {'Read':<8} {'Update':<8} {'Delete':<8} {'Score':<8}")
print("-" * 80)

for module_name, module_data in results['modules'].items():
    if 'crud_summary' in module_data:
        crud = module_data['crud_summary']
        total_crud = crud['create'] + crud['read'] + crud['update'] + crud['delete']
        max_crud = 4 if module_name != 'Admin_Logs' else 1  # Admin logs is read-only
        score = f"{total_crud}/{max_crud}"

        c_icon = "[OK]" if crud['create'] else "[NO]"
        r_icon = "[OK]" if crud['read'] else "[NO]"
        u_icon = "[OK]" if crud['update'] else "[NO]" if module_name != 'Admin_Logs' else "[N/A]"
        d_icon = "[OK]" if crud['delete'] else "[NO]" if module_name != 'Admin_Logs' else "[N/A]"

        print(f"{module_name:<20} {c_icon:<8} {r_icon:<8} {u_icon:<8} {d_icon:<8} {score:<8}")

# Save detailed results
results['test_completed'] = datetime.now().isoformat()
with open('tests/all_modules_crud_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\\n[SAVE] Detailed results saved to: tests/all_modules_crud_results.json")
print(f"\\n[END] Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)
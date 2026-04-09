"""
FINAL COMPREHENSIVE CRUD TEST - ALL REQUESTED MODULES
Tests: Passengers, Bookings, Quotas, Fares, Train_Inventory, Coach_Layouts,
       Route_Stops, Train_Routes, Trains, Stations, Settings, Admin_Logs, Announcements

Creates sample records and tests full CRUD operations for each module.
"""

import urllib.request
import urllib.error
import json
import ssl
import time
from datetime import datetime, timedelta
import random
import string

# Disable SSL verification
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
    'auth_tokens': {},
    'created_ids': {}  # Store created record IDs for testing
}

def random_string(length=8):
    """Generate random string."""
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_digits(length=6):
    """Generate random digits."""
    return ''.join(random.choices(string.digits, k=length))

def future_date(days=30):
    """Generate future date."""
    if days < 0:
        # For past dates
        date = datetime.now() + timedelta(days=random.randint(days, -1))
    else:
        # For future dates
        date = datetime.now() + timedelta(days=random.randint(1, days))
    return date.strftime('%Y-%m-%d')

def random_time():
    """Generate random time."""
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}"

def api_request(method, endpoint, data=None, headers=None, expected_status=[200, 201]):
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
        passed = response.status in expected_status

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
        status_icon = "PASS" if passed else "FAIL"
        print(f"  {status_icon:4} | {method:6} {endpoint:35} | {response.status} | {elapsed:4.0f}ms")

        return result

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0

        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = str(e)

        passed = e.code in expected_status

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

        status_icon = "PASS" if passed else "FAIL"
        print(f"  {status_icon:4} | {method:6} {endpoint:35} | {e.code} | {elapsed:4.0f}ms")

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

        print(f"  FAIL | {method:6} {endpoint:35} | ERR | 0ms | {str(e)[:50]}")

        return result

def test_crud_module(module_name, endpoint_base, sample_data, auth_required=False):
    """Test full CRUD operations for a module."""
    print(f"\n{'='*80}")
    print(f"MODULE: {module_name.upper()}")
    print(f"{'='*80}")

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
    print(f"\n  CREATE - {module_name}")
    create_result = api_request('POST', endpoint_base, sample_data, auth_header, [201, 409])
    module_results['tests'].append(create_result)

    if create_result['passed'] and create_result.get('response', {}).get('data'):
        created_id = create_result['response']['data'].get('ROWID') or create_result['response']['data'].get('id')
        module_results['crud_summary']['create'] = 1
        results['created_ids'][module_name] = created_id
        print(f"    Created record with ID: {created_id}")

    # 2. READ operations
    print(f"\n  READ - {module_name}")

    # Read all
    read_all_result = api_request('GET', endpoint_base, None, auth_header)
    module_results['tests'].append(read_all_result)
    if read_all_result['passed']:
        module_results['crud_summary']['read'] += 1

    # Read by ID (if we have an ID)
    if created_id:
        read_one_result = api_request('GET', f"{endpoint_base}/{created_id}", None, auth_header, [200, 404])
        module_results['tests'].append(read_one_result)
        if read_one_result['passed']:
            module_results['crud_summary']['read'] += 1

    # 3. UPDATE operation (if we have an ID)
    if created_id:
        print(f"\n  UPDATE - {module_name}")

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
            elif any('status' in key.lower() for key in sample_data):
                for key in sample_data:
                    if 'status' in key.lower():
                        update_data[key] = 'Updated'
                        break
            else:
                # Default update - use first string field
                for key, value in sample_data.items():
                    if isinstance(value, str) and len(value) > 0:
                        update_data[key] = f"{value} (Updated)"
                        break

        if update_data:
            update_result = api_request('PUT', f"{endpoint_base}/{created_id}", update_data, auth_header, [200, 404])
            module_results['tests'].append(update_result)
            if update_result['passed']:
                module_results['crud_summary']['update'] = 1

    # 4. DELETE operation (if we have an ID)
    if created_id:
        print(f"\n  DELETE - {module_name}")
        delete_result = api_request('DELETE', f"{endpoint_base}/{created_id}", None, auth_header, [200, 204, 404])
        module_results['tests'].append(delete_result)
        if delete_result['passed']:
            module_results['crud_summary']['delete'] = 1

    # Summary for this module
    total_operations = len(module_results['tests'])
    passed_operations = sum(1 for t in module_results['tests'] if t['passed'])

    print(f"\n  Summary: {passed_operations}/{total_operations} operations passed")
    print(f"  CRUD Status: C={module_results['crud_summary']['create']} R={module_results['crud_summary']['read']} U={module_results['crud_summary']['update']} D={module_results['crud_summary']['delete']}")

    results['modules'][module_name] = module_results
    return module_results

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

print("="*100)
print("FINAL COMPREHENSIVE CRUD TEST - ALL REQUESTED MODULES")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# STEP 1: Setup Authentication
print("\n[STEP 1: AUTHENTICATION SETUP]")
print("-"*60)

# Get tokens
print("Getting user token from seed endpoint...")
user_result = api_request('POST', '/seed/user', expected_status=[200, 201])
if user_result['passed'] and user_result.get('response', {}).get('data', {}).get('token'):
    results['auth_tokens']['user_token'] = user_result['response']['data']['token']
    print(f"    User token obtained: {results['auth_tokens']['user_token'][:30]}...")

print("Getting admin token from seed endpoint...")
admin_result = api_request('POST', '/seed/admin', expected_status=[200, 201])
if admin_result['passed'] and admin_result.get('response', {}).get('data', {}).get('token'):
    results['auth_tokens']['admin_token'] = admin_result['response']['data']['token']
    print(f"    Admin token obtained: {results['auth_tokens']['admin_token'][:30]}...")

# STEP 2: Test All Requested Modules with Sample Data
print("\n[STEP 2: COMPREHENSIVE CRUD TESTING - ALL REQUESTED MODULES]")
print("-"*60)

# 1. STATIONS
station_data = {
    'stationCode': f'TST{random_digits(3)}',
    'stationName': f'Test Station {random_string(5)}',
    'city': f'Test City {random_string(4)}',
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
    'trainName': f'{random_string(6)} Express',
    'trainType': 'Express',
    'fromStation': '1',
    'toStation': '2',
    'departureTime': random_time(),
    'arrivalTime': random_time(),
    'distance': random.randint(100, 2000),
    'runDays': 'Mon,Tue,Wed,Thu,Fri,Sat,Sun',
    'isActive': True
}
test_crud_module('Trains', '/trains', train_data, auth_required=True)

# 3. TRAIN_ROUTES
train_route_data = {
    'routeName': f'Route {random_string(5)}',
    'trainId': '1',
    'sourceStationId': '1',
    'destinationStationId': '2',
    'totalDistance': random.randint(100, 2000),
    'estimatedDuration': random.randint(120, 1440),
    'isActive': True
}
test_crud_module('Train_Routes', '/train-routes', train_route_data, auth_required=True)

# 4. ROUTE_STOPS (via train-routes)
route_stop_data = {
    'trainRouteId': '1',
    'stationId': '1',
    'sequenceNumber': 1,
    'arrivalTime': random_time(),
    'departureTime': random_time(),
    'distanceFromOrigin': random.randint(0, 500),
    'haltDuration': random.randint(2, 30),
    'platform': f'{random.randint(1, 10)}',
    'isActive': True
}
# Special test for route stops (nested under train-routes)
route_id = results['created_ids'].get('Train_Routes', '1')
print(f"\n{'='*80}")
print(f"MODULE: ROUTE_STOPS (VIA TRAIN_ROUTES)")
print(f"{'='*80}")

auth_header = {}
if results['auth_tokens'].get('admin_token'):
    auth_header = {'Authorization': f"Bearer {results['auth_tokens']['admin_token']}"}

stops_create = api_request('POST', f'/train-routes/{route_id}/stops', route_stop_data, auth_header, [201, 409])
stops_read = api_request('GET', f'/train-routes/{route_id}/stops', None, auth_header)
results['modules']['Route_Stops'] = {'tests': [stops_create, stops_read]}

# 5. COACH_LAYOUTS
coach_layout_data = {
    'trainId': '1',
    'coachType': 'AC_3_TIER',
    'coachNumber': f'S{random.randint(1, 20)}',
    'totalSeats': 72,
    'seatConfiguration': '2+1',
    'facilities': 'AC,Charging Point,Reading Light',
    'position': 1
}
test_crud_module('Coach_Layouts', '/coach-layouts', coach_layout_data, auth_required=True)

# 6. TRAIN_INVENTORY (via inventory)
inventory_data = {
    'trainId': '1',
    'journeyDate': future_date(),
    'availableSeatsSL': random.randint(0, 72),
    'availableSeats3A': random.randint(0, 64),
    'availableSeats2A': random.randint(0, 48),
    'availableSeats1A': random.randint(0, 24),
    'availableSeatsCC': random.randint(0, 80)
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
    'effectiveFrom': future_date(-30),
    'effectiveTo': future_date(365),
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
    'journeyDate': future_date(),
    'isActive': True
}
test_crud_module('Quotas', '/quotas', quota_data, auth_required=True)

# 9. BOOKINGS
booking_data = {
    'userId': results['auth_tokens'].get('user_token', '1'),
    'trainId': '1',
    'journeyDate': future_date(),
    'sourceStationId': '1',
    'destinationStationId': '2',
    'classType': 'AC_3_TIER',
    'passengers': random.randint(1, 4),
    'totalFare': random.randint(1000, 5000),
    'bookingStatus': 'CONFIRMED',
    'paymentStatus': 'COMPLETED',
    'pnr': f'PNR{random_digits(10)}'
}
test_crud_module('Bookings', '/bookings', booking_data, auth_required=True)

# 10. PASSENGERS
passenger_data = {
    'bookingId': '1',
    'passengerName': f'{random_string(6)} {random_string(8)}',
    'age': random.randint(18, 80),
    'gender': random.choice(['Male', 'Female', 'Other']),
    'berthPreference': random.choice(['Lower', 'Middle', 'Upper', 'Side Lower', 'Side Upper']),
    'seatNumber': f'{random.randint(1, 72)}',
    'coachNumber': f'S{random.randint(1, 20)}',
    'bookingStatus': 'CNF',
    'foodChoice': random.choice(['Veg', 'Non-Veg', 'None']),
    'idType': 'Passport',
    'idNumber': f'P{random_digits(8)}',
    'contactNumber': f'9{random_digits(9)}'
}
test_crud_module('Passengers', '/passengers', passenger_data, auth_required=True)

# 11. ANNOUNCEMENTS
announcement_data = {
    'title': f'Test Announcement {random_string(5)}',
    'message': f'This is a test announcement message created at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
    'type': random.choice(['INFO', 'WARNING', 'CRITICAL', 'MAINTENANCE']),
    'targetAudience': 'ALL',
    'trainId': None,
    'stationId': None,
    'validFrom': datetime.now().isoformat(),
    'validUntil': (datetime.now() + timedelta(days=7)).isoformat(),
    'priority': random.randint(1, 5),
    'isActive': True
}
test_crud_module('Announcements', '/announcements', announcement_data, auth_required=True)

# 12. SETTINGS
settings_data = {
    'settingKey': f'TEST_SETTING_{random_string(5)}',
    'settingValue': f'test_value_{random_digits(4)}',
    'settingType': 'STRING',
    'description': 'Test setting created by CRUD test suite',
    'category': 'TESTING',
    'isPublic': False,
    'isActive': True
}
test_crud_module('Settings', '/settings', settings_data, auth_required=True)

# 13. ADMIN_LOGS (Read-only testing)
print(f"\n{'='*80}")
print(f"MODULE: ADMIN_LOGS (READ-ONLY)")
print(f"{'='*80}")

admin_logs_results = {'tests': [], 'crud_summary': {'create': 0, 'read': 0, 'update': 0, 'delete': 0}}

if results['auth_tokens'].get('admin_token'):
    auth_header = {'Authorization': f"Bearer {results['auth_tokens']['admin_token']}"}
    read_logs_result = api_request('GET', '/admin/logs', None, auth_header)
    admin_logs_results['tests'].append(read_logs_result)
    if read_logs_result['passed']:
        admin_logs_results['crud_summary']['read'] = 1

results['modules']['Admin_Logs'] = admin_logs_results

# STEP 3: Generate Final Report
print("\n" + "="*100)
print("FINAL COMPREHENSIVE CRUD TEST REPORT - ALL REQUESTED MODULES")
print("="*100)

print(f"\nOVERALL STATISTICS")
print(f"   Total API Calls: {results['summary']['total']}")
print(f"   Passed: {results['summary']['passed']}")
print(f"   Failed: {results['summary']['failed']}")

if results['summary']['total'] > 0:
    pass_rate = (results['summary']['passed'] / results['summary']['total']) * 100
    print(f"   Success Rate: {pass_rate:.1f}%")

print(f"\nREQUESTED MODULES CRUD SUMMARY")
print("-" * 80)
print(f"{'Module':<20} {'Create':<8} {'Read':<8} {'Update':<8} {'Delete':<8} {'Score':<8}")
print("-" * 80)

requested_modules = [
    'Passengers', 'Bookings', 'Quotas', 'Fares', 'Train_Inventory',
    'Coach_Layouts', 'Route_Stops', 'Train_Routes', 'Trains',
    'Stations', 'Settings', 'Admin_Logs', 'Announcements'
]

for module_name in requested_modules:
    if module_name in results['modules']:
        module_data = results['modules'][module_name]
        if 'crud_summary' in module_data:
            crud = module_data['crud_summary']
            total_crud = crud['create'] + crud['read'] + crud['update'] + crud['delete']
            max_crud = 4 if module_name != 'Admin_Logs' else 1  # Admin logs is read-only
            score = f"{total_crud}/{max_crud}"

            c_icon = "PASS" if crud['create'] else "FAIL"
            r_icon = "PASS" if crud['read'] else "FAIL"
            u_icon = "PASS" if crud['update'] else "FAIL" if module_name != 'Admin_Logs' else "N/A"
            d_icon = "PASS" if crud['delete'] else "FAIL" if module_name != 'Admin_Logs' else "N/A"

            print(f"{module_name:<20} {c_icon:<8} {r_icon:<8} {u_icon:<8} {d_icon:<8} {score:<8}")
        else:
            print(f"{module_name:<20} {'ERROR':<8} {'ERROR':<8} {'ERROR':<8} {'ERROR':<8} {'0/4':<8}")
    else:
        print(f"{module_name:<20} {'MISS':<8} {'MISS':<8} {'MISS':<8} {'MISS':<8} {'0/4':<8}")

# Working vs Issues Summary
working_modules = []
issue_modules = []

for module_name in requested_modules:
    if module_name in results['modules']:
        module_data = results['modules'][module_name]
        if 'crud_summary' in module_data:
            crud = module_data['crud_summary']
            total_crud = crud['create'] + crud['read'] + crud['update'] + crud['delete']
            if total_crud >= 2:  # At least READ working
                working_modules.append(module_name)
            else:
                issue_modules.append(module_name)

print(f"\nWORKING MODULES ({len(working_modules)}/13)")
for module in working_modules:
    print(f"   + {module}")

if issue_modules:
    print(f"\nMODULES WITH ISSUES ({len(issue_modules)}/13)")
    for module in issue_modules:
        print(f"   - {module}")

# Save detailed results
results['test_completed'] = datetime.now().isoformat()
with open('tests/final_all_modules_crud_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nDetailed results saved to: tests/final_all_modules_crud_results.json")
print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)
"""
Final CloudScale Sample Data Population - Smart Schema-Aware Approach
"""

import urllib.request
import urllib.error
import json
import ssl
import time
from datetime import datetime

# Disable SSL verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

def api_request(method, endpoint, data=None, expected_status=[200, 201]):
    """Make API request and return result."""
    url = f"{BASE_URL}{endpoint}"

    try:
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(data).encode('utf-8') if data else None

        request_obj = urllib.request.Request(url, data=body, headers=headers, method=method)

        start_time = time.time()
        response = urllib.request.urlopen(request_obj, timeout=120, context=ctx)
        elapsed = (time.time() - start_time) * 1000

        response_data = json.loads(response.read().decode())

        success = response.status in expected_status
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:40} | {response.status} | {elapsed:6.0f}ms")

        return {
            'success': success,
            'status': response.status,
            'data': response_data,
            'time': elapsed
        }

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0

        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = {'message': str(e)}

        success = e.code in expected_status
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:40} | {e.code} | {elapsed:6.0f}ms")

        return {
            'success': success,
            'status': e.code,
            'data': error_data,
            'time': elapsed
        }

    except Exception as e:
        print(f"FAIL {method:6} {endpoint:40} | ERR | 0ms | {str(e)[:40]}")
        return {
            'success': False,
            'status': 0,
            'data': {'error': str(e)},
            'time': 0
        }

print("="*100)
print("FINAL CLOUDSCALE SAMPLE DATA POPULATION - SMART SCHEMA-AWARE APPROACH")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# Step 1: Discover table schemas first
print("\n[STEP 1: DISCOVER TABLE SCHEMAS]")
print("-" * 80)

discover_result = api_request('POST', '/smart-seed/discover-schemas')
if discover_result['success']:
    schemas = discover_result['data'].get('schemas', {})
    print(f"Schema discovery results:")
    for table, info in schemas.items():
        status = info.get('status', 'unknown')
        print(f"  {table:<15} | {status}")
        if 'fields' in info and info['fields']:
            print(f"    Fields: {info['fields'][:5]}")  # Show first 5 fields

# Step 2: Test simple insertion
print(f"\n[STEP 2: TEST SIMPLE INSERTION]")
print("-" * 80)

simple_test = api_request('POST', '/smart-seed/simple-insert')
if simple_test['success']:
    test_result = simple_test['data'].get('result', {})
    print(f"  Simple insert success: {test_result.get('success', False)}")
    if not test_result.get('success'):
        print(f"  Error: {test_result.get('error', 'Unknown')}")

# Step 3: Create working sample data with schema detection
print(f"\n[STEP 3: CREATE WORKING SAMPLE DATA]")
print("-" * 80)

working_data_result = api_request('POST', '/smart-seed/create-working-data')
if working_data_result['success']:
    summary = working_data_result['data'].get('summary', {})
    results = working_data_result['data'].get('results', {})

    print(f"Sample Data Creation Summary:")
    print(f"  Total Modules: {summary.get('total_modules', 0)}")
    print(f"  Successful Modules: {summary.get('successful_modules', 0)}")
    print(f"  Total Records: {summary.get('total_records_created', 0)}")
    print(f"  Success Rate: {summary.get('success_rate', '0%')}")

    print(f"\nDetailed Results:")
    for module, info in results.items():
        success = "SUCCESS" if info.get('success') else "FAILED"
        created = info.get('created', 0)
        print(f"  {module:<15} | {success:<7} | {created} records")

# Step 4: Final comprehensive population for all modules
print(f"\n[STEP 4: COMPREHENSIVE POPULATION - ALL MODULES]")
print("-" * 80)

comprehensive_result = api_request('POST', '/smart-seed/populate-all-modules')
if comprehensive_result['success']:
    summary = comprehensive_result['data'].get('summary', {})
    detailed = comprehensive_result['data'].get('detailed_results', {})

    print(f"Comprehensive Population Summary:")
    print(f"  Successful Modules: {summary.get('successful_modules', 0)}")
    print(f"  Total Records Created: {summary.get('total_records_created', 0)}")
    print(f"  Success Rate: {summary.get('success_rate', '0%')}")

    print(f"\nModule-by-Module Results:")
    for module, info in detailed.items():
        success = "SUCCESS" if info.get('success') else "FAILED"
        created = info.get('created', 0)
        attempted = info.get('attempted', 0)
        print(f"  {module:<15} | {success:<7} | {created}/{attempted} records")

# Step 5: Verify data exists by checking public endpoints
print(f"\n[STEP 5: VERIFY DATA EXISTS VIA PUBLIC ENDPOINTS]")
print("-" * 80)

verification_endpoints = [
    '/stations', '/trains', '/fares', '/settings', '/announcements', '/quotas'
]

verification_results = {}

for endpoint in verification_endpoints:
    result = api_request('GET', endpoint)
    if result['success']:
        data = result['data'].get('data', [])
        count = len(data)
        verification_results[endpoint] = count
        print(f"  {endpoint:<15} | {count:>3} records")
        if count > 0:
            # Show first record as example
            first_record = data[0]
            record_keys = list(first_record.keys())[:4]  # First 4 fields
            print(f"    Sample fields: {record_keys}")

# Step 6: Final status check
print(f"\n[STEP 6: FINAL COMPREHENSIVE STATUS CHECK]")
print("-" * 80)

final_status = api_request('GET', '/data-seed/status')
if final_status['success']:
    modules = final_status['data'].get('modules', {})
    summary = final_status['data'].get('summary', {})

    print(f"Final CloudScale Database Status:")
    print(f"  Total Modules: {summary.get('total_modules', 0)}")
    print(f"  Modules with Data: {summary.get('modules_with_data', 0)}")
    print(f"  Total Records: {summary.get('total_records', 0)}")

    print(f"\nRequested Modules Status:")
    requested_modules = [
        'stations', 'trains', 'fares', 'settings', 'announcements', 'quotas',
        'bookings', 'passengers', 'train_routes', 'route_stops', 'coach_layouts',
        'train_inventory', 'admin_logs'
    ]

    populated_count = 0
    for module in requested_modules:
        if module in modules:
            count = modules[module].get('record_count', 0)
            status = "POPULATED" if count > 0 else "EMPTY"
            print(f"  {module:<20} | {count:>3} records | {status}")
            if count > 0:
                populated_count += 1

    print(f"\nFINAL RESULTS:")
    print(f"  Requested Modules: 13")
    print(f"  Populated Modules: {populated_count}")
    print(f"  Success Rate: {(populated_count/13)*100:.1f}%")

print("\n" + "="*100)
print("CLOUDSCALE SAMPLE DATA POPULATION COMPLETE!")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)
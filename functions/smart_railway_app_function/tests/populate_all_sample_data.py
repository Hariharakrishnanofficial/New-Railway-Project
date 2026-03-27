"""
Comprehensive Sample Data Population Test

This script will populate ALL 13 requested modules with sample data in CloudScale:
1. Stations 2. Trains 3. Train_Routes 4. Route_Stops 5. Coach_Layouts
6. Train_Inventory 7. Fares 8. Quotas 9. Bookings 10. Passengers
11. Settings 12. Announcements 13. Admin_Logs
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
        # Prepare request
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(data).encode('utf-8') if data else None

        request_obj = urllib.request.Request(url, data=body, headers=headers, method=method)

        start_time = time.time()
        response = urllib.request.urlopen(request_obj, timeout=300, context=ctx)  # 5 minute timeout for large operations
        elapsed = (time.time() - start_time) * 1000

        # Parse response
        response_data = json.loads(response.read().decode())

        success = response.status in expected_status
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:35} | {response.status} | {elapsed:6.0f}ms")

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
        print(f"{status_icon} {method:6} {endpoint:35} | {e.code} | {elapsed:6.0f}ms")

        return {
            'success': success,
            'status': e.code,
            'data': error_data,
            'time': elapsed
        }

    except Exception as e:
        print(f"FAIL {method:6} {endpoint:35} | ERR | 0ms | {str(e)[:50]}")
        return {
            'success': False,
            'status': 0,
            'data': {'error': str(e)},
            'time': 0
        }

print("="*100)
print("COMPREHENSIVE SAMPLE DATA POPULATION - ALL 13 RAILWAY MODULES")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# Step 1: Check current data status
print("\n[STEP 1: CHECK CURRENT DATA STATUS]")
print("-" * 60)

status_result = api_request('GET', '/data-seed/status')
if status_result['success']:
    modules = status_result['data'].get('modules', {})
    summary = status_result['data'].get('summary', {})

    print(f"Current Status:")
    print(f"  Total Modules: {summary.get('total_modules', 0)}")
    print(f"  Modules with Data: {summary.get('modules_with_data', 0)}")
    print(f"  Total Records: {summary.get('total_records', 0)}")

    print(f"\nModule Details:")
    for module, info in modules.items():
        count = info.get('record_count', 0)
        status = "HAS DATA" if info.get('has_data') else "EMPTY"
        print(f"  {module:<20} | {count:>6} records | {status}")
else:
    print("Failed to get current status")

# Step 2: Run comprehensive sample data creation
print(f"\n[STEP 2: CREATE COMPREHENSIVE SAMPLE DATA FOR ALL MODULES]")
print("-" * 60)
print("Creating sample data for all 13 modules... This may take a few minutes.")

create_result = api_request('POST', '/data-seed/all')

if create_result['success']:
    results = create_result['data'].get('results', {})
    summary = create_result['data'].get('summary', {})

    print(f"\nSample Data Creation Results:")
    print(f"  Total Modules: {summary.get('total_modules', 0)}")
    print(f"  Successful: {summary.get('successful', 0)}")
    print(f"  Failed: {summary.get('failed', 0)}")

    print(f"\nDetailed Results by Module:")
    print(f"{'Module':<20} {'Status':<10} {'Created':<8} {'Sample Data'}")
    print("-" * 80)

    for module, result in results.items():
        if result.get('success'):
            created = result.get('created_count', 0)
            sample_shown = len(result.get('sample_data', []))
            print(f"{module:<20} {'SUCCESS':<10} {created:>6} {f'(showing {sample_shown})':<15}")
        else:
            error = result.get('error', 'Unknown error')[:30]
            print(f"{module:<20} {'FAILED':<10} {0:>6} {error:<15}")

    print(f"\nOverall Result: {create_result['data'].get('message', 'Completed')}")

else:
    print("Failed to create sample data")
    error_msg = create_result['data'].get('message', 'Unknown error')
    print(f"Error: {error_msg}")

# Step 3: Verify final data status
print(f"\n[STEP 3: VERIFY FINAL DATA STATUS]")
print("-" * 60)

final_status_result = api_request('GET', '/data-seed/status')
if final_status_result['success']:
    modules = final_status_result['data'].get('modules', {})
    summary = final_status_result['data'].get('summary', {})

    print(f"Final Status:")
    print(f"  Total Modules: {summary.get('total_modules', 0)}")
    print(f"  Modules with Data: {summary.get('modules_with_data', 0)}")
    print(f"  Total Records: {summary.get('total_records', 0)}")

    print(f"\nFinal Module Status:")
    print(f"{'Module':<20} {'Records':<8} {'Status':<12} {'Table'}")
    print("-" * 80)

    populated_modules = 0
    total_records = 0

    for module, info in modules.items():
        count = info.get('record_count', 0)
        status = "POPULATED" if info.get('has_data') else "EMPTY"
        table = info.get('table', '')

        if info.get('has_data'):
            populated_modules += 1

        total_records += count

        print(f"{module:<20} {count:>6} {status:<12} {table}")

    print(f"\nSUMMARY:")
    print(f"  Populated Modules: {populated_modules}/13 ({(populated_modules/13)*100:.1f}%)")
    print(f"  Total Records Created: {total_records}")

    # Check for ALL 13 requested modules
    requested_modules = [
        'stations', 'trains', 'train_routes', 'route_stops', 'coach_layouts',
        'train_inventory', 'fares', 'quotas', 'bookings', 'passengers',
        'settings', 'announcements', 'admin_logs'
    ]

    missing_modules = []
    populated_requested = []

    for req_module in requested_modules:
        # Map to table names that might be different
        module_mapping = {
            'train_inventory': 'inventory',
            'route_stops': 'route_stops',
            'coach_layouts': 'coach_layouts'
        }

        actual_module = module_mapping.get(req_module, req_module)

        if actual_module in modules and modules[actual_module].get('has_data'):
            populated_requested.append(req_module)
        else:
            missing_modules.append(req_module)

    print(f"\nREQUESTED MODULES STATUS:")
    print(f"  Populated: {len(populated_requested)}/13")
    for mod in populated_requested:
        print(f"    ✓ {mod}")

    if missing_modules:
        print(f"  Missing Data: {len(missing_modules)}")
        for mod in missing_modules:
            print(f"    ✗ {mod}")

else:
    print("Failed to get final status")

print("\n" + "="*100)
print("COMPREHENSIVE SAMPLE DATA POPULATION COMPLETE")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)
"""
Populate CloudScale with Sample Data - Public Endpoints Test
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
        response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
        elapsed = (time.time() - start_time) * 1000

        response_data = json.loads(response.read().decode())

        success = response.status in expected_status
        status_icon = "PASS" if success else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:35} | {response.status} | {elapsed:6.0f}ms")

        if success and response_data.get('data'):
            sample_data = response_data['data']
            if isinstance(sample_data, list) and len(sample_data) > 0:
                print(f"    Created {len(sample_data)} records")
            elif isinstance(sample_data, dict) and 'message' in response_data:
                print(f"    {response_data['message']}")

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
print("POPULATE CLOUDSCALE WITH SAMPLE DATA - PUBLIC ENDPOINTS")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)

# Step 1: Check initial status
print("\n[STEP 1: CHECK INITIAL STATUS]")
print("-" * 60)

status_result = api_request('GET', '/public-seed/status')

# Step 2: Create all basic sample data
print(f"\n[STEP 2: CREATE ALL BASIC SAMPLE DATA]")
print("-" * 60)

all_basic_result = api_request('POST', '/public-seed/all-basic')

if all_basic_result['success']:
    results = all_basic_result['data'].get('results', {})
    print(f"\nDetailed Results:")
    for module, result in results.items():
        status = "SUCCESS" if result.get('success') else "FAILED"
        message = result.get('message', '')
        print(f"  {module:<15} | {status:<7} | {message}")
else:
    print("Failed to create basic sample data")
    print(f"Error: {all_basic_result['data']}")

# Step 3: Create individual modules for testing
print(f"\n[STEP 3: TEST INDIVIDUAL MODULE CREATION]")
print("-" * 60)

individual_tests = [
    ('POST', '/public-seed/stations'),
    ('POST', '/public-seed/trains'),
    ('POST', '/public-seed/fares'),
    ('POST', '/public-seed/settings'),
    ('POST', '/public-seed/announcements'),
    ('POST', '/public-seed/quotas')
]

for method, endpoint in individual_tests:
    result = api_request(method, endpoint)

# Step 4: Check final status
print(f"\n[STEP 4: CHECK FINAL STATUS]")
print("-" * 60)

final_status_result = api_request('GET', '/public-seed/status')
if final_status_result['success']:
    modules = final_status_result['data'].get('modules', {})
    summary = final_status_result['data'].get('summary', {})

    print(f"\nFinal Status Summary:")
    print(f"  Total Modules Checked: {summary.get('total_modules_checked', 0)}")
    print(f"  Modules with Data: {summary.get('modules_with_data', 0)}")
    print(f"  Total Records Created: {summary.get('total_records', 0)}")

    print(f"\nModule Details:")
    for module, info in modules.items():
        count = info.get('record_count', 0)
        status = "POPULATED" if info.get('has_data') else "EMPTY"
        print(f"  {module:<15} | {count:>6} records | {status}")

# Step 5: Test public GET endpoints to verify data is accessible
print(f"\n[STEP 5: VERIFY DATA IS ACCESSIBLE VIA GET ENDPOINTS]")
print("-" * 60)

public_get_tests = [
    ('GET', '/stations'),
    ('GET', '/trains'),
    ('GET', '/fares'),
    ('GET', '/settings'),
    ('GET', '/announcements'),
    ('GET', '/quotas')
]

for method, endpoint in public_get_tests:
    result = api_request(method, endpoint)
    if result['success'] and result['data'].get('data'):
        data_count = len(result['data']['data'])
        print(f"    Retrieved {data_count} records from {endpoint}")

print("\n" + "="*100)
print("CLOUDSCALE SAMPLE DATA POPULATION COMPLETE")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*100)
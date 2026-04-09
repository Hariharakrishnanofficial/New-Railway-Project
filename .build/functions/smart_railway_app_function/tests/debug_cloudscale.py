"""
Debug CloudScale Record Creation - Direct Repository Test
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

        # Print response details for debugging
        if 'data' in response_data:
            data_info = response_data['data']
            if isinstance(data_info, list):
                print(f"    Response contains {len(data_info)} items")
                if len(data_info) > 0:
                    print(f"    First item: {data_info[0]}")
            elif isinstance(data_info, dict) and data_info:
                print(f"    Response data keys: {list(data_info.keys())}")

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
            print(f"    Error details: {error_data}")
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

print("="*80)
print("DEBUG CLOUDSCALE RECORD CREATION")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Step 1: Create a single station and see detailed response
print("\n[STEP 1: CREATE SINGLE STATION WITH DETAILED RESPONSE]")
print("-" * 60)

station_result = api_request('POST', '/public-seed/stations')
print(f"Station creation response: {station_result['data']}")

# Step 2: Check if the station was actually created
print(f"\n[STEP 2: CHECK IF STATIONS EXIST]")
print("-" * 60)

stations_result = api_request('GET', '/stations')
if stations_result['success']:
    stations_data = stations_result['data'].get('data', [])
    print(f"Found {len(stations_data)} stations in database")
    if len(stations_data) > 0:
        print(f"First station: {stations_data[0]}")

# Step 3: Try different CloudScale operations
print(f"\n[STEP 3: TEST CLOUDSCALE DATA SEED STATUS]")
print("-" * 60)

data_seed_status = api_request('GET', '/data-seed/status')
if data_seed_status['success']:
    modules = data_seed_status['data'].get('modules', {})
    print(f"CloudScale table status:")
    for module, info in modules.items():
        count = info.get('record_count', 0)
        table = info.get('table', 'Unknown')
        print(f"  {module:<15} | {table:<20} | {count} records")

# Step 4: Check individual module endpoints
print(f"\n[STEP 4: CHECK INDIVIDUAL MODULE ENDPOINTS]")
print("-" * 60)

modules_to_check = [
    'stations', 'trains', 'fares', 'settings', 'announcements', 'quotas'
]

for module in modules_to_check:
    result = api_request('GET', f'/{module}')
    if result['success']:
        data = result['data'].get('data', [])
        print(f"  {module:<15} | {len(data)} records retrieved")

# Step 5: Try creating settings (simpler data structure)
print(f"\n[STEP 5: CREATE SIMPLE SETTINGS RECORD]")
print("-" * 60)

settings_result = api_request('POST', '/public-seed/settings')
print(f"Settings creation response: {settings_result['data']}")

# Check settings after creation
settings_check = api_request('GET', '/settings')
if settings_check['success']:
    settings_data = settings_check['data'].get('data', [])
    print(f"Found {len(settings_data)} settings after creation")

print("\n" + "="*80)
print("CLOUDSCALE DEBUG COMPLETE")
print("="*80)
"""
Step-by-Step Sample Data Creation with Debugging
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
            print(f"Error details: {error_data}")
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
print("STEP-BY-STEP SAMPLE DATA CREATION WITH DEBUGGING")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Step 1: Test individual station creation first
print("\n[TEST 1: CREATE SINGLE STATION MANUALLY]")
print("-" * 50)

station_data = {
    'stationCode': 'TST01',
    'stationName': 'Test Station Alpha',
    'city': 'Mumbai',
    'state': 'Maharashtra',
    'zone': 'CR',
    'platformCount': 4,
    'isActive': True
}

station_result = api_request('POST', '/stations', station_data)
print(f"Station creation result: {station_result['success']}")
if not station_result['success']:
    print(f"Station creation error: {station_result['data']}")

# Step 2: Test getting admin token first (needed for station creation)
print("\n[TEST 2: GET ADMIN TOKEN FOR STATION CREATION]")
print("-" * 50)

admin_result = api_request('POST', '/seed/admin')
admin_token = None
if admin_result['success'] and admin_result.get('data', {}).get('data', {}).get('token'):
    admin_token = admin_result['data']['data']['token']
    print(f"Admin token obtained: {admin_token[:30]}...")

    # Try station creation with auth header
    print("\n[TEST 3: CREATE STATION WITH ADMIN TOKEN]")
    print("-" * 50)

    def api_request_with_auth(method, endpoint, data=None, token=None, expected_status=[200, 201]):
        url = f"{BASE_URL}{endpoint}"

        try:
            headers = {'Content-Type': 'application/json'}
            if token:
                headers['Authorization'] = f'Bearer {token}'

            body = json.dumps(data).encode('utf-8') if data else None

            request_obj = urllib.request.Request(url, data=body, headers=headers, method=method)

            start_time = time.time()
            response = urllib.request.urlopen(request_obj, timeout=60, context=ctx)
            elapsed = (time.time() - start_time) * 1000

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
                print(f"Error details: {error_data}")
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

    auth_station_result = api_request_with_auth('POST', '/stations', station_data, admin_token)
    print(f"Station creation with auth result: {auth_station_result['success']}")
    if not auth_station_result['success']:
        print(f"Station creation with auth error: {auth_station_result['data']}")
    else:
        print(f"SUCCESS! Station created: {auth_station_result['data']}")

    # Step 4: Test public endpoints that should work
    print("\n[TEST 4: VERIFY PUBLIC ENDPOINTS WORK]")
    print("-" * 50)

    public_tests = [
        ('GET', '/stations'),
        ('GET', '/fares'),
        ('GET', '/quotas'),
        ('GET', '/announcements'),
        ('GET', '/settings'),
        ('GET', '/train-routes')
    ]

    for method, endpoint in public_tests:
        result = api_request(method, endpoint)

else:
    print("Failed to get admin token")

# Step 5: Try direct data insertion using CloudScale without auth
print("\n[TEST 5: TRY SEED ENDPOINTS FOR BASIC DATA]")
print("-" * 50)

# Create settings via data seeder
settings_data = [
    {
        'Setting_Key': 'TEST_SETTING_1',
        'Setting_Value': 'test_value_1',
        'Setting_Type': 'STRING',
        'Description': 'Test setting for debugging',
        'Category': 'TESTING',
        'Is_Public': 'true',
        'Is_Active': 'true',
    }
]

for setting in settings_data:
    # Try direct creation using the seed method
    result = api_request('POST', '/settings', setting)
    print(f"Settings creation: {result['success']}")

# Check final status
print("\n[FINAL STATUS CHECK]")
print("-" * 50)

status_result = api_request('GET', '/data-seed/status')
if status_result['success']:
    summary = status_result['data'].get('summary', {})
    print(f"Total Records: {summary.get('total_records', 0)}")
    print(f"Modules with Data: {summary.get('modules_with_data', 0)}")

print("\n" + "="*80)
print("DEBUGGING COMPLETE")
print("="*80)
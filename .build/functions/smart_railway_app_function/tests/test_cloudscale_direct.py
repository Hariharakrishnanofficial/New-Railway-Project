"""
Test CloudScale Diagnostic Endpoints
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
print("CLOUDSCALE DIAGNOSTIC TESTS")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Test 1: CloudScale Status Check
print("\n[TEST 1: CLOUDSCALE STATUS CHECK]")
print("-" * 60)

status_result = api_request('GET', '/cloudscale-test/status')
if status_result['success']:
    status_data = status_result['data']
    print(f"  Catalyst Initialized: {status_data.get('catalyst_initialized')}")
    print(f"  ZCQL Test: {status_data.get('zcql_test')}")
    print(f"  Datastore Test: {status_data.get('datastore_test')}")
    print(f"  Tables Configured: {len(status_data.get('tables_configured', []))}")

# Test 2: Direct Insert Test
print(f"\n[TEST 2: DIRECT INSERT TEST]")
print("-" * 60)

insert_result = api_request('POST', '/cloudscale-test/insert')
if insert_result['success']:
    print("  Direct insert succeeded!")
    creation_result = insert_result['data'].get('creation_result', {})
    print(f"  Creation Success: {creation_result.get('success')}")
    if not creation_result.get('success'):
        print(f"  Creation Error: {creation_result.get('error')}")
else:
    print("  Direct insert failed!")
    print(f"  Error: {insert_result['data']}")

# Test 3: Manual Settings Creation
print(f"\n[TEST 3: MANUAL SETTINGS CREATION]")
print("-" * 60)

manual_result = api_request('POST', '/cloudscale-test/manual-settings')
if manual_result['success']:
    print("  Manual settings creation succeeded!")
    insert_result_data = manual_result['data'].get('insert_result', {})
    verify_result_data = manual_result['data'].get('verify_result', [])
    print(f"  Insert Result Type: {type(insert_result_data)}")
    print(f"  Insert Result: {insert_result_data}")
    print(f"  Verify Result Count: {len(verify_result_data) if isinstance(verify_result_data, list) else 'Not a list'}")
else:
    print("  Manual settings creation failed!")
    print(f"  Error: {manual_result['data']}")

# Test 4: Check if any data exists now
print(f"\n[TEST 4: CHECK FOR EXISTING DATA]")
print("-" * 60)

modules_to_check = ['settings', 'stations', 'announcements']

for module in modules_to_check:
    result = api_request('GET', f'/{module}')
    if result['success']:
        data = result['data'].get('data', [])
        print(f"  {module:<15} | {len(data)} records")
        if len(data) > 0:
            print(f"    First record: {data[0]}")

print("\n" + "="*80)
print("CLOUDSCALE DIAGNOSTIC COMPLETE")
print("="*80)
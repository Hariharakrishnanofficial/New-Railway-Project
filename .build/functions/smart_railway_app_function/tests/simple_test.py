"""
Simple Test - Railway Data Creation (ASCII only)
Tests the updated reliable railway data endpoint with exact CloudScale schema field names.
"""

import urllib.request
import urllib.error
import json
import ssl
from datetime import datetime

# Disable SSL verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = 'https://smart-railway-app-60066581545.development.catalystserverless.in/server/smart_railway_app_function'

def api_request(method, endpoint, data=None):
    """Make API request and return result."""
    url = f"{BASE_URL}{endpoint}"

    try:
        headers = {'Content-Type': 'application/json'}
        body = json.dumps(data).encode('utf-8') if data else None

        request_obj = urllib.request.Request(url, data=body, headers=headers, method=method)
        response = urllib.request.urlopen(request_obj, timeout=180, context=ctx)
        response_data = json.loads(response.read().decode())

        success = response.status in [200, 201]
        status = "SUCCESS" if success else "FAILED"
        print(f"{status} - {method} {endpoint} (HTTP {response.status})")

        return {
            'success': success,
            'status_code': response.status,
            'data': response_data
        }

    except urllib.error.HTTPError as e:
        # Read the error response body
        try:
            error_body = e.read().decode('utf-8')
            error_data = json.loads(error_body)
            print(f"HTTP {e.code} ERROR - {method} {endpoint}")
            print(f"Error: {error_data.get('message', 'Unknown error')}")
            return {
                'success': False,
                'status_code': e.code,
                'data': error_data
            }
        except:
            print(f"HTTP {e.code} ERROR - {method} {endpoint}: {str(e)}")
            return {
                'success': False,
                'status_code': e.code,
                'data': {'error': str(e)}
            }
    except Exception as e:
        print(f"ERROR - {method} {endpoint}: {str(e)}")
        return {
            'success': False,
            'data': {'error': str(e)}
        }

print("=" * 60)
print("SIMPLE TEST - CORRECTED CLOUDSCALE FIELDS")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Test 1: Create railway records
print(f"\nSTEP 1: CREATE RAILWAY RECORDS")
print("-" * 40)

create_result = api_request('POST', '/reliable-railway-data/create-persistent-records')

if create_result['success']:
    data = create_result['data']
    results = data.get('results', {})
    summary = results.get('summary', {})

    print(f"Status: {data.get('status', 'unknown').upper()}")
    print(f"Created: {summary.get('total_created', 0)}")
    print(f"Verified: {summary.get('total_verified', 0)}")
    print(f"Success Rate: {summary.get('success_rate', '0%')}")

    creation_successful = summary.get('total_created', 0) > 0
else:
    error_data = create_result['data']
    print(f"CREATION FAILED (HTTP {create_result.get('status_code', '?')})")
    print(f"Error: {error_data.get('message', error_data.get('error', 'Unknown'))}")
    creation_successful = False

# Test 2: Verify persistence
print(f"\nSTEP 2: VERIFY PERSISTENCE")
print("-" * 40)

verify_result = api_request('GET', '/reliable-railway-data/verify-persistence')

if verify_result['success']:
    data = verify_result['data']
    summary = data.get('summary', {})

    total_records = summary.get('total_railway_records', 0)
    successful_modules = summary.get('successful_modules', 0)

    print(f"Total Records: {total_records}")
    print(f"Successful Modules: {successful_modules}/4")

    if total_records > 0:
        print(f"SUCCESS: Found {total_records} railway records!")
        modules_with_data = summary.get('modules_with_data', [])
        print(f"Modules: {modules_with_data}")
    else:
        print("No records found in CloudScale")

    verification_successful = total_records > 0
else:
    print(f"Verification failed: {verify_result['data'].get('error', 'Unknown error')}")
    verification_successful = False

# Final result
print(f"\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)

if creation_successful and verification_successful:
    print("SUCCESS: Railway data created and verified!")
elif creation_successful:
    print("PARTIAL: Data created but verification issues")
elif verification_successful:
    print("EXISTING: Found existing data")
else:
    print("FAILED: No data created or verified")

print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
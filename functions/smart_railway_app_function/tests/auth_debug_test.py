"""
Quick Authentication Debug Test
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

def api_request(method, endpoint, data=None, headers=None, expected_status=[200, 201]):
    """Make API request and return structured result."""
    url = f"{BASE_URL}{endpoint}"

    try:
        # Prepare headers
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)

        # Prepare body
        if data:
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

        # Print result
        passed = response.status in expected_status
        status_icon = "PASS" if passed else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:35} | {response.status} | {elapsed:4.0f}ms")

        return {
            'success': True,
            'status': response.status,
            'data': response_data,
            'time': elapsed
        }

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start_time) * 1000 if 'start_time' in locals() else 0

        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = str(e)

        passed = e.code in expected_status
        status_icon = "PASS" if passed else "FAIL"
        print(f"{status_icon} {method:6} {endpoint:35} | {e.code} | {elapsed:4.0f}ms")

        return {
            'success': False,
            'status': e.code,
            'data': error_data,
            'time': elapsed
        }

    except Exception as e:
        print(f"FAIL {method:6} {endpoint:35} | ERR | 0ms | {str(e)[:50]}")
        return {
            'success': False,
            'status': 0,
            'data': str(e),
            'time': 0
        }

print("="*80)
print("AUTHENTICATION DEBUG TEST")
print(f"API: {BASE_URL}")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Step 1: Get tokens from seed endpoints
print("\n1. GET TOKENS FROM SEED ENDPOINTS")
print("-" * 50)

user_result = api_request('POST', '/seed/user')
user_token = None
if user_result['success'] and user_result.get('data', {}).get('data', {}).get('token'):
    user_token = user_result['data']['data']['token']
    print(f"  User token: {user_token[:50]}...")

admin_result = api_request('POST', '/seed/admin')
admin_token = None
if admin_result['success'] and admin_result.get('data', {}).get('data', {}).get('token'):
    admin_token = admin_result['data']['data']['token']
    print(f"  Admin token: {admin_token[:50]}...")

# Step 2: Test endpoints that were previously working (public endpoints)
print("\n2. TEST PUBLIC ENDPOINTS (NO AUTH REQUIRED)")
print("-" * 50)

api_request('GET', '/stations')
api_request('GET', '/fares')
api_request('GET', '/quotas')
api_request('GET', '/announcements')
api_request('GET', '/settings')
api_request('GET', '/train-routes')

# Step 3: Test same endpoints with auth token to see if they changed to require auth
print("\n3. TEST PUBLIC ENDPOINTS WITH AUTH HEADERS")
print("-" * 50)

if user_token:
    auth_header = {'Authorization': f'Bearer {user_token}'}
    api_request('GET', '/stations', None, auth_header)
    api_request('GET', '/fares', None, auth_header)
    api_request('GET', '/quotas', None, auth_header)

# Step 4: Test protected endpoints with tokens
print("\n4. TEST PROTECTED ENDPOINTS WITH AUTH")
print("-" * 50)

if user_token:
    auth_header = {'Authorization': f'Bearer {user_token}'}
    api_request('GET', '/auth/validate', None, auth_header)
    api_request('GET', '/bookings', None, auth_header)

if admin_token:
    admin_auth_header = {'Authorization': f'Bearer {admin_token}'}
    api_request('GET', '/users', None, admin_auth_header)
    api_request('GET', '/admin/logs', None, admin_auth_header)

# Step 5: Test direct login
print("\n5. TEST DIRECT LOGIN")
print("-" * 50)

login_result = api_request('POST', '/auth/login', {
    'email': 'agent@agent.com',
    'password': 'agent@agent.com'
})

if login_result['success'] and login_result.get('data', {}).get('data', {}).get('token'):
    login_token = login_result['data']['data']['token']
    print(f"  Login token: {login_token[:50]}...")

    # Test with login token
    login_auth_header = {'Authorization': f'Bearer {login_token}'}
    api_request('GET', '/auth/validate', None, login_auth_header)

print("\n" + "="*80)
print("AUTHENTICATION DEBUG COMPLETE")
print("="*80)
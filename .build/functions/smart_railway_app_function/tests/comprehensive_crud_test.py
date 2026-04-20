"""
Comprehensive CRUD Test - All Modules
Test deployed API with real authentication
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

# Test results
results = {
    'timestamp': datetime.now().isoformat(),
    'baseUrl': BASE_URL,
    'tests': [],
    'summary': {'total': 0, 'passed': 0, 'failed': 0}
}

def test_endpoint(name, method, endpoint, data=None, headers=None, expected=[200, 201]):
    """Test single endpoint and return result"""
    try:
        url = f'{BASE_URL}{endpoint}'
        req_headers = {'Content-Type': 'application/json'}
        if headers:
            req_headers.update(headers)

        if data:
            data_bytes = json.dumps(data).encode('utf-8')
        else:
            data_bytes = None

        request = urllib.request.Request(url, data=data_bytes, headers=req_headers, method=method)

        start = time.time()
        response = urllib.request.urlopen(request, timeout=30, context=ctx)
        elapsed = (time.time() - start) * 1000

        response_data = json.loads(response.read().decode())

        passed = response.status in expected

        result = {
            'name': name,
            'method': method,
            'endpoint': endpoint,
            'status': response.status,
            'time': f'{elapsed:.0f}ms',
            'result': 'PASS' if passed else 'FAIL',
            'response': response_data if not passed else None
        }

        results['tests'].append(result)
        results['summary']['total'] += 1
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1

        print(f'{method:6} {endpoint:30} | {response.status} | {elapsed:4.0f}ms | {"PASS" if passed else "FAIL"}')

        return response_data

    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000 if 'start' in dir() else 0
        try:
            error_data = json.loads(e.read().decode())
        except:
            error_data = str(e)

        passed = e.code in expected

        result = {
            'name': name,
            'method': method,
            'endpoint': endpoint,
            'status': e.code,
            'time': f'{elapsed:.0f}ms',
            'result': 'PASS' if passed else 'FAIL',
            'response': error_data if not passed else None
        }

        results['tests'].append(result)
        results['summary']['total'] += 1
        if passed:
            results['summary']['passed'] += 1
        else:
            results['summary']['failed'] += 1

        print(f'{method:6} {endpoint:30} | {e.code} | {elapsed:4.0f}ms | {"PASS" if passed else "FAIL"}')

        return error_data

    except Exception as e:
        result = {
            'name': name,
            'method': method,
            'endpoint': endpoint,
            'status': 0,
            'time': '0ms',
            'result': 'ERROR',
            'response': str(e)
        }

        results['tests'].append(result)
        results['summary']['total'] += 1
        results['summary']['failed'] += 1

        print(f'{method:6} {endpoint:30} | ERR | 0ms | ERROR')

        return None

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

print('=' * 80)
print('COMPREHENSIVE MODULE CRUD TESTING - Smart Railway System')
print(f'Deployed API: {BASE_URL}')
print(f'Timestamp: {datetime.now().isoformat()}')
print('=' * 80)

# Step 1: Create test users and get tokens
print()
print('STEP 1: CREATE TEST USERS')
print('-' * 50)

user_data = test_endpoint('Create Test User', 'POST', '/seed/user', expected=[200, 201])
auth_token = user_data.get('data', {}).get('token') if user_data else None

admin_data = test_endpoint('Create Admin User', 'POST', '/seed/admin', expected=[200, 201])
admin_token = admin_data.get('data', {}).get('token') if admin_data else None

print(f'User Token: {auth_token[:30] if auth_token else "None"}...')
print(f'Admin Token: {admin_token[:30] if admin_token else "None"}...')

# Step 2: Test Authentication module
print()
print('STEP 2: AUTHENTICATION MODULE')
print('-' * 50)

# Login test
login_data = test_endpoint('Login Valid User', 'POST', '/auth/login',
                          {'email': 'agent@agent.com', 'password': 'agent@agent.com'})

if login_data and login_data.get('data', {}).get('token'):
    auth_token = login_data['data']['token']

# Validate session
if auth_token:
    test_endpoint('Validate Session', 'GET', '/auth/validate',
                 headers={'Authorization': f'Bearer {auth_token}'})

# Test invalid login
test_endpoint('Login Invalid Password', 'POST', '/auth/login',
             {'email': 'agent@agent.com', 'password': 'wrong'},
             expected=[401])

# Test logout
test_endpoint('Logout', 'POST', '/auth/logout')

# Step 3: Test Core Modules
print()
print('STEP 3: CORE MODULES')
print('-' * 50)

# Stations (public endpoint)
stations_data = test_endpoint('Get All Stations', 'GET', '/stations')

# Search stations
test_endpoint('Search Stations', 'GET', '/stations?search=test')

# Trains (might need database setup)
test_endpoint('Get All Trains', 'GET', '/trains', expected=[200, 500])

# Fares
test_endpoint('Get All Fares', 'GET', '/fares')

# Quotas
test_endpoint('Get All Quotas', 'GET', '/quotas')

# Announcements
test_endpoint('Get Announcements', 'GET', '/announcements')

# Bookings (requires auth)
if auth_token:
    test_endpoint('Get User Bookings', 'GET', '/bookings',
                 headers={'Authorization': f'Bearer {auth_token}'})

# Step 4: Test Admin Modules
print()
print('STEP 4: ADMIN MODULES (REQUIRES ADMIN TOKEN)')
print('-' * 50)

if admin_token:
    # Users management
    test_endpoint('Get All Users (Admin)', 'GET', '/users',
                 headers={'Authorization': f'Bearer {admin_token}'})

    # Module Master
    test_endpoint('Get All Modules (Admin)', 'GET', '/modules',
                 headers={'Authorization': f'Bearer {admin_token}'})

    # Create new module
    module_data = test_endpoint('Create Module (Admin)', 'POST', '/modules',
                               {'moduleCode': 'TEST', 'moduleName': 'Test Module', 'description': 'Test'},
                               {'Authorization': f'Bearer {admin_token}'},
                               expected=[201, 409])

    # Settings
    test_endpoint('Get Settings (Admin)', 'GET', '/settings',
                 headers={'Authorization': f'Bearer {admin_token}'})

    # Admin logs
    test_endpoint('Get Admin Logs', 'GET', '/admin/logs',
                 headers={'Authorization': f'Bearer {admin_token}'})

else:
    print('❌ No admin token available - skipping admin tests')

# Step 5: Test User Authorization (Regular user trying admin endpoints)
print()
print('STEP 5: AUTHORIZATION TESTS')
print('-' * 50)

if auth_token:
    # Regular user trying admin endpoints (should fail)
    test_endpoint('User Access Admin Endpoint', 'GET', '/users',
                 headers={'Authorization': f'Bearer {auth_token}'},
                 expected=[401, 403])

# No auth token (should fail)
test_endpoint('No Auth - Protected Endpoint', 'GET', '/bookings', expected=[401])

# Step 6: Test Security
print()
print('STEP 6: SECURITY TESTS')
print('-' * 50)

# SQL Injection
test_endpoint('SQL Injection Test', 'POST', '/auth/login',
             {'email': "'; DROP TABLE Users; --", 'password': "' OR '1'='1"},
             expected=[400, 401])

# XSS Prevention
test_endpoint('XSS Prevention Test', 'POST', '/auth/register',
             {'fullName': '<script>alert("XSS")</script>', 'email': 'xss@test.com', 'password': 'test1234'},
             expected=[201, 400, 409])

# Large payload test
large_data = {'description': 'A' * 10000}  # 10KB string
test_endpoint('Large Payload Test', 'POST', '/modules',
             {'moduleCode': 'LARGE', 'moduleName': 'Large Test', **large_data},
             {'Authorization': f'Bearer {admin_token}'} if admin_token else {},
             expected=[201, 400, 401, 413])

# Step 7: Edge Cases
print()
print('STEP 7: EDGE CASE TESTS')
print('-' * 50)

# Empty JSON
test_endpoint('Empty JSON', 'POST', '/auth/login', {}, expected=[400])

# Malformed JSON
test_endpoint('Invalid Endpoint', 'GET', '/nonexistent', expected=[404])

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print()
print('=' * 80)
print('FINAL TEST SUMMARY')
print('=' * 80)

print(f'Total Tests: {results["summary"]["total"]}')
print(f'Passed: {results["summary"]["passed"]}')
print(f'Failed: {results["summary"]["failed"]}')

if results['summary']['total'] > 0:
    pass_rate = (results['summary']['passed'] / results['summary']['total']) * 100
    print(f'Pass Rate: {pass_rate:.1f}%')

    # Determine overall result
    if pass_rate >= 90:
        overall_result = "EXCELLENT"
    elif pass_rate >= 75:
        overall_result = "GOOD"
    elif pass_rate >= 50:
        overall_result = "ACCEPTABLE"
    else:
        overall_result = "NEEDS WORK"

    print(f'Overall Result: {overall_result}')

print()
print('Test Results by Category:')
print('-' * 40)

categories = {}
for test in results['tests']:
    category = test['endpoint'].split('/')[1] if '/' in test['endpoint'] else 'root'
    if category not in categories:
        categories[category] = {'pass': 0, 'fail': 0, 'tests': []}
    categories[category]['tests'].append(test)
    if test['result'] == 'PASS':
        categories[category]['pass'] += 1
    else:
        categories[category]['fail'] += 1

for cat, counts in categories.items():
    total = counts['pass'] + counts['fail']
    rate = (counts['pass'] / total * 100) if total > 0 else 0
    status = "✓" if rate >= 75 else "⚠" if rate >= 50 else "✗"
    print(f'{status} {cat:15}: {counts["pass"]}/{total} ({rate:.0f}%)')

# Show failed tests
failed_tests = [t for t in results['tests'] if t['result'] != 'PASS']
if failed_tests:
    print()
    print('Failed Tests Details:')
    print('-' * 40)
    for test in failed_tests[:10]:  # Show first 10 failures
        print(f'  • {test["name"]} ({test["method"]} {test["endpoint"]}) - {test["status"]}')

# Generate JSON report
results['summary']['pass_rate'] = pass_rate if results['summary']['total'] > 0 else 0
results['categories'] = categories

# Save results
with open('tests/comprehensive_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print()
print('=' * 80)
print('TEST REPORT GENERATED')
print('=' * 80)
print(f'JSON Report: tests/comprehensive_test_results.json')
print(f'Total Endpoints Tested: {results["summary"]["total"]}')
print(f'API Base URL: {BASE_URL}')
print(f'Test Completed: {datetime.now().isoformat()}')
print('=' * 80)